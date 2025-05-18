import numpy as np
from PIL import Image
import itertools
import matplotlib.pyplot as plt
import os
import sys
from pyzbar.pyzbar import decode
import cv2

def split_image(image_path):
    """
    Split a 33x33 image into 9 blocks of 11x11 pixels each.
    Returns the blocks as a 3x3 grid of numpy arrays.
    """
    # Check if file exists
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image file not found: {image_path}")
        
    # Open the image
    img = Image.open(image_path)
    
    # Check if the image is 33x33
    if img.size != (33, 33):
        # Resize image if it's not 33x33
        print(f"Resizing image from {img.size} to (33, 33)")
        img = img.resize((33, 33), Image.LANCZOS)
    
    # Convert to numpy array
    img_array = np.array(img)
    
    # Get the number of channels
    num_channels = 1 if len(img_array.shape) == 2 else img_array.shape[2]
    print(f"Image has {num_channels} channels")
    
    # Initialize a 3x3 grid to store the blocks
    blocks = [[None for _ in range(3)] for _ in range(3)]
    
    # Split the image into 9 blocks
    for i in range(3):
        for j in range(3):
            blocks[i][j] = img_array[i*11:(i+1)*11, j*11:(j+1)*11]
    
    return blocks, num_channels

def create_combinations(blocks, num_channels):
    """
    Create combinations keeping the four corners fixed and arranging 
    the five non-corner blocks without repetition.
    """
    # Extract the non-corner blocks into a flat list
    non_corner_blocks = [
        blocks[0][1],  # Top-center
        blocks[1][0],  # Middle-left
        blocks[1][1],  # Middle-center
        blocks[1][2],  # Middle-right
        blocks[2][1],  # Bottom-center
    ]
    
    # Create shape for new images based on number of channels
    if num_channels > 1:
        shape = (33, 33, num_channels)
    else:
        shape = (33, 33)
    
    # Generate all possible permutations of the 5 non-corner blocks
    # This will give 5! = 120 combinations
    combinations = []
    
    # Generate all permutations of the non-corner blocks
    for perm in itertools.permutations(non_corner_blocks):
        # Create a new 33x33 image with the correct number of channels
        new_img = np.zeros(shape, dtype=blocks[0][0].dtype)
        
        # Keep the corners fixed from the original image
        new_img[0:11, 0:11] = blocks[0][0]    # Top-left
        new_img[0:11, 22:33] = blocks[0][2]   # Top-right
        new_img[22:33, 0:11] = blocks[2][0]   # Bottom-left
        new_img[22:33, 22:33] = blocks[2][2]  # Bottom-right
        
        # Place the permuted non-corner blocks
        new_img[0:11, 11:22] = perm[0]   # Top-center
        new_img[11:22, 0:11] = perm[1]   # Middle-left
        new_img[11:22, 11:22] = perm[2]  # Middle-center
        new_img[11:22, 22:33] = perm[3]  # Middle-right
        new_img[22:33, 11:22] = perm[4]  # Bottom-center
        
        combinations.append(new_img)
    
    print(f"Created {len(combinations)} unique combinations")
    return combinations

def scan_qr_code(image_array):
    """
    Scan a numpy array image for QR codes using pyzbar.
    Returns the decoded data if a QR code is found, None otherwise.
    """
    # Convert to Image if needed for pyzbar
    if isinstance(image_array, np.ndarray):
        # Ensure the image is in the correct format for pyzbar
        # If it's RGB or RGBA, convert to grayscale
        if len(image_array.shape) > 2 and image_array.shape[2] >= 3:
            image_array = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
        
        pil_image = Image.fromarray(image_array.astype('uint8'))
    else:
        pil_image = image_array
    
    # Resize for better scanning (QR scanners often work better with larger images)
    # Scale by a factor of 3 to get 99x99 pixels
    enlarged_image = pil_image.resize((99, 99), Image.LANCZOS)
    
    # Try to decode the QR code
    decoded_objects = decode(enlarged_image)
    
    # Return data if found
    if decoded_objects:
        return decoded_objects[0].data.decode('utf-8')
    return None

def save_and_scan_combinations(combinations, output_dir):
    """
    Save all combinations to files and scan them for QR codes.
    Returns a list of successfully decoded QR codes with their indices.
    """
    os.makedirs(output_dir, exist_ok=True)
    successful_scans = []
    
    print(f"Saving and scanning {len(combinations)} combinations...")
    
    # Process all combinations
    for idx, img_array in enumerate(combinations):
        # Save the image
        img = Image.fromarray(img_array.astype('uint8'))
        file_path = os.path.join(output_dir, f"combination_{idx}.png")
        img.save(file_path)
        
        # Scan for QR code
        qr_data = scan_qr_code(img_array)
        
        if qr_data:
            print(f"✓ Combination {idx}: QR Code found! Data: {qr_data}")
            successful_scans.append((idx, qr_data))
        else:
            # Print progress every 10 combinations if not successful
            if idx % 10 == 0:
                print(f"Processed {idx}/{len(combinations)} combinations...")
    
    print(f"\nScan complete: Found {len(successful_scans)} valid QR codes out of {len(combinations)} combinations")
    return successful_scans

def display_successful_combinations(combinations, successful_indices, output_dir):
    """
    Display and save only the combinations that yielded successful QR scans.
    """
    if not successful_indices:
        print("No successful QR code scans to display.")
        return
    
    # Save successful combinations to a separate directory
    success_dir = os.path.join(output_dir, "successful")
    os.makedirs(success_dir, exist_ok=True)
    
    # Display grid of successful combinations
    rows = min(4, len(successful_indices))
    cols = min(4, (len(successful_indices) + rows - 1) // rows)
    
    plt.figure(figsize=(15, 15))
    for i, (idx, qr_data) in enumerate(successful_indices):
        if i >= rows * cols:
            break
            
        # Get the image
        img_array = combinations[idx]
        
        # Save to successful directory
        img = Image.fromarray(img_array.astype('uint8'))
        file_path = os.path.join(success_dir, f"successful_{idx}_{qr_data}.png")
        img.save(file_path)
        
        # Display
        plt.subplot(rows, cols, i + 1)
        if len(img_array.shape) == 3:
            plt.imshow(img_array)
        else:
            plt.imshow(img_array, cmap='gray')
        plt.title(f"#{idx}: {qr_data}")
        plt.axis('off')
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "successful_grid.png"))
    plt.show()
    
    # Create a text report
    with open(os.path.join(output_dir, "qr_scan_results.txt"), 'w') as f:
        f.write(f"QR Code Scan Results\n")
        f.write(f"====================\n\n")
        f.write(f"Total combinations: {len(combinations)}\n")
        f.write(f"Successful scans: {len(successful_indices)}\n\n")
        f.write(f"Details:\n")
        for idx, qr_data in successful_indices:
            f.write(f"- Combination #{idx}: {qr_data}\n")
    
    print(f"Successful combinations saved to {success_dir}")
    print(f"Results summary saved to {os.path.join(output_dir, 'qr_scan_results.txt')}")

def main():
    """
    Main function that processes the image, creates combinations, and scans for QR codes.
    """
    # Get the image path from command line arguments or use default
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
    else:
        print("No image path provided. Please enter the path to your image:")
        image_path = 'file.png'
    
    # Check if file exists
    if not os.path.exists(image_path):
        print(f"Error: File '{image_path}' not found.")
        return
    
    # Output directory
    output_dir = "qr_combinations" if len(sys.argv) <= 2 else sys.argv[2]
    
    try:
        print(f"Processing image: {image_path}")
        
        # Split the image into blocks
        blocks, num_channels = split_image(image_path)
        
        # Create all possible combinations
        combinations = create_combinations(blocks, num_channels)
        
        # Scan all combinations for QR codes and save them
        successful_scans = save_and_scan_combinations(combinations, output_dir)
        
        # Display the successful combinations
        display_successful_combinations(combinations, successful_scans, output_dir)
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()