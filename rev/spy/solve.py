from Crypto.Cipher import DES3
from hashlib import md5

test = b'ThisIsAVerySecretKey123--'

with open('flag.enc', 'rb') as f:
	flag = f.read()

cipher = DES3.new(md5(test).digest(), DES3.MODE_ECB)
flag = cipher.decrypt(flag)
print(flag)

# INS{d0tn3t_w3ak_3ncrypti0n!!!}
