require 'sinatra'
require 'openssl'
require 'json'
require 'base64'
require 'logger'
require 'pg'

logger = Logger.new(STDOUT)

PREDEFINED_APK_SIGNATURE = ENV['APK_SIGN']

RSA_KEY = OpenSSL::PKey::RSA.new(2048)

DB_CONNECTION = PG.connect(
  dbname: ENV['DB_NAME'],
  user: ENV['DB_USER'],
  password: ENV['DB_PWD'],
  host: ENV['DB_HOST'],
  port: ENV['DB_PORT'] 
)

get '/pubkey' do
  content_type :text
  RSA_KEY.public_key.to_pem
end

post '/data' do
  begin
    request.body.rewind
    request_payload = JSON.parse(request.body.read)
    required_params = %w[aesKey data iv signature]
    missing_params = required_params.select { |param| !request_payload.key?(param) || request_payload[param].nil? || request_payload[param].strip.empty? }
    unless missing_params.empty?
      halt 400, { error: "Missing or null parameters" }.to_json
    end


    b64_encoded_aes_key = request_payload['aesKey']
    b64_encoded_data = request_payload['data']
    b64_encoded_iv = request_payload['iv']
    b64_encoded_sign = request_payload['signature']
    apk_signature = request.env['HTTP_X_SIGNATURE']

    if apk_signature == PREDEFINED_APK_SIGNATURE
      encrypted_aes_key = Base64.decode64(b64_encoded_aes_key)
      encrypted_data = Base64.decode64(b64_encoded_data)
      iv = Base64.decode64(b64_encoded_iv)
      signature = Base64.decode64(b64_encoded_sign)

      aes_key = RSA_KEY.private_decrypt(encrypted_aes_key, OpenSSL::PKey::RSA::PKCS1_PADDING)

      aes_cipher = OpenSSL::Cipher.new('AES-256-CBC')
      aes_cipher.decrypt
      aes_cipher.key = aes_key
      aes_cipher.iv = iv
      decrypted_data = aes_cipher.update(encrypted_data) + aes_cipher.final

      data_object = JSON.parse(decrypted_data)

      attestation_b64 = data_object['attestation']
      decoded_data = Base64.decode64(attestation_b64)
      certificate = OpenSSL::X509::Certificate.new(decoded_data)
      client_public_key = certificate.public_key

      attestation_ext = certificate.extensions.find { |ext| ext.oid == ENV['STR1'] }
      if attestation_ext

        digest = OpenSSL::Digest::SHA256.new
        is_verified = client_public_key.verify(digest, signature, b64_encoded_data)

        if is_verified
          key_alias_pattern = /keyAlias_\h{8}-\h{4}-\h{4}-\h{4}-\h{12}/
          key_alias = certificate.extensions.map(&:value).find { |value| value.match?(key_alias_pattern) }
          key_alias_match = key_alias&.match(key_alias_pattern).to_s

          code = SecureRandom.alphanumeric(32)
          aes_cipher_1 = OpenSSL::Cipher.new('AES-256-CBC')
          aes_cipher_1.encrypt
          key1 = aes_cipher_1.random_key
          iv_1 = aes_cipher_1.random_iv
          b64_encoded_key1 = Base64.strict_encode64(key1)
          b64_encoded_iv_1 = Base64.strict_encode64(iv_1)

          android_id = data_object['androidId']
          client_public_key_pem = client_public_key.to_pem
          DB_CONNECTION.exec_params(
            "INSERT INTO android_keys (android_id, public_key, key_alias, phone, code, key1, iv_1)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            ON CONFLICT (android_id)
            DO UPDATE SET public_key = $2, key_alias = $3, phone = $4, code = $5, key1 = $6, iv_1 = $7",
            [android_id, client_public_key_pem, key_alias_match, data_object['phoneNumber'], code, b64_encoded_key1, b64_encoded_iv_1]
          )
        else
          status 400
          return { error: "Signature verification failed." }.to_json
        end

      else
        status 400
        return { error: "The data does not contain any key attestation" }.to_json
      end

      file_path = './file.txt'
      file_content = File.binread(file_path)

      aes_cipher_1.key = key1
      aes_cipher_1.iv = iv_1
      aes_cipher_1.padding = 1
      encrypted_file_content = aes_cipher_1.update(file_content) + aes_cipher_1.final
      b64_encoded_encrypted_file_content = Base64.strict_encode64(encrypted_file_content)

      encrypted_code = client_public_key.public_encrypt(code, OpenSSL::PKey::RSA::PKCS1_PADDING)
      b64_encoded_encrypted_code = Base64.strict_encode64(encrypted_code)

      status 200
      {
        encrypted_file: b64_encoded_encrypted_file_content,
        encrypted_code: b64_encoded_encrypted_code
      }.to_json  

    else
      status 401
      return { error: "Invalid APK Signature" }.to_json
    end 

  rescue OpenSSL::PKey::RSAError => e
    status 500
    { error: "Error during decryption" }.to_json
  rescue PG::Error => e
    status 500
    { error: "Database error" }.to_json
  rescue JSON::ParserError => e
    status 400
    { error: "Invalid JSON" }.to_json
  rescue => e
    logger.error(e.backtrace.join("\n"))
    status 500
    { error: "Unexpected error" }.to_json
  end
end

post '/getkey' do
  begin
    request.body.rewind
    request_payload = JSON.parse(request.body.read)

    required_params = %w[code signature]

    missing_params = required_params.select { |param| !request_payload.key?(param) || request_payload[param].nil? || request_payload[param].strip.empty? }
    unless missing_params.empty?
      halt 400, { error: "Missing or null parameters" }.to_json
    end

    code = request_payload['code']
    signature_b64 = request_payload['signature']

    apk_signature = request.env['HTTP_X_SIGNATURE']

    if apk_signature == PREDEFINED_APK_SIGNATURE
      signature = Base64.decode64(signature_b64)

      result = DB_CONNECTION.exec_params("SELECT public_key, iv_1, key1 FROM android_keys WHERE code = $1", [code])

      if result.ntuples == 1
        public_key_pem = result[0]['public_key']
        iv_1 = result[0]['iv_1']
        b64_key1 = result[0]['key1']
        public_key = OpenSSL::PKey::RSA.new(public_key_pem)

        digest = OpenSSL::Digest::SHA256.new
        is_verified = public_key.verify(digest, signature, code)

        if is_verified
          timestamp = Time.now.to_i

          signed_timestamp = RSA_KEY.sign(digest, timestamp.to_s)
          b64_encoded_signed_timestamp = Base64.strict_encode64(signed_timestamp)

          status 200
          {
            iv_1: iv_1,
            key1: b64_key1,
            timestamp: timestamp,
            signed_timestamp: b64_encoded_signed_timestamp
          }.to_json

        else
          status 400
          { error: "Invalid signature." }.to_json
        end
      else
        status 404
        { error: "Code not found." }.to_json
      end

    else
      status 401
      return { error: "Invalid APK Signature" }.to_json
    end

  rescue PG::Error => e
    status 500
    { error: "Database error" }.to_json
  rescue JSON::ParserError => e
    status 400
    { error: "Invalid JSON" }.to_json
  rescue => e
    status 500
    { error: "Unexpected error" }.to_json
  end
end

