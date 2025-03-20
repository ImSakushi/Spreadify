import os
import sys
import zipfile
from PIL import Image

def extract_cbz(cbz_path, extract_folder):
    """
    Extracts the contents of a .cbz (zip format) file into a specified folder.
    Returns a list of extracted image files (full paths).
    """
    with zipfile.ZipFile(cbz_path, 'r') as zip_ref:
        zip_ref.extractall(extract_folder)

    # Retrieve all extracted files
    extracted_files = []
    for root, dirs, files in os.walk(extract_folder):
        for file in files:
            # Filter only image files
            if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                extracted_files.append(os.path.join(root, file))

    # Sort them so the page order remains correct
    extracted_files.sort()
    return extracted_files

def is_spread_candidate(image_path, border_size=5, white_threshold=250, black_threshold=20):
    """
    Checks if, within the 'border_size' pixels on both the left and right edges of the image,
    there are any NON-WHITE pixels (indicating a potential spread).

    HOWEVER, if the entire left border OR the entire right border is COMPLETELY BLACK,
    we consider it NOT a spread (e.g., flashback or stylistic black frame).

    Returns:
      - True if it potentially detects a spread.
      - False otherwise.
    """
    img = Image.open(image_path).convert('RGB')
    width, height = img.size
    
    # Flags to track pixel colors
    left_border_has_black = False       # At least one non-white pixel on the left border
    right_border_has_black = False      # At least one non-white pixel on the right border
    left_border_all_black = True        # Is the entire left border completely black?
    right_border_all_black = True       # Is the entire right border completely black?
    
    # --- Check the left border ---
    for x in range(border_size):
        for y in range(height):
            r, g, b = img.getpixel((x, y))
            avg = (r + g + b) / 3
            
            # If we find a pixel that is not white, note that the left border has black
            if avg < white_threshold:
                left_border_has_black = True
            
            # If we find a pixel that is not sufficiently black, it's not 100% black
            if avg > black_threshold:
                left_border_all_black = False
    
    # --- Check the right border ---
    for x in range(width - border_size, width):
        for y in range(height):
            r, g, b = img.getpixel((x, y))
            avg = (r + g + b) / 3
            
            if avg < white_threshold:
                right_border_has_black = True
            
            if avg > black_threshold:
                right_border_all_black = False

    # --- Final logic ---
    # 1) If the left border OR the right border is entirely black => do not merge
    if left_border_all_black or right_border_all_black:
        return False
    
    # 2) Otherwise, it's a spread only if we detected non-white pixels on both sides
    return left_border_has_black and right_border_has_black

def merge_images_horizontally(image_path1, image_path2, output_path):
    """
    Merges two images side by side, placing the second image on the left and the first image on the right.
    The function aligns the top and bottom edges en se basant sur l'image la plus grande (en hauteur).
    Si l'une des images est plus petite, elle est redimensionnée proportionnellement.
    """
    img1 = Image.open(image_path1).convert('RGB')
    img2 = Image.open(image_path2).convert('RGB')
    
    width1, height1 = img1.size
    width2, height2 = img2.size

    # Déterminer la hauteur de référence (celle de l'image la plus grande)
    new_height = max(height1, height2)

    # Redimensionner img1 si nécessaire
    if height1 != new_height:
        new_width1 = int(width1 * new_height / height1)
        img1 = img1.resize((new_width1, new_height), Image.Resampling.LANCZOS)
    else:
        new_width1 = width1

    # Redimensionner img2 si nécessaire
    if height2 != new_height:
        new_width2 = int(width2 * new_height / height2)
        img2 = img2.resize((new_width2, new_height), Image.Resampling.LANCZOS)
    else:
        new_width2 = width2

    # La nouvelle largeur est la somme des largeurs redimensionnées
    new_width = new_width1 + new_width2

    # Créer une nouvelle image avec un fond blanc
    new_img = Image.new('RGB', (new_width, new_height), color=(255, 255, 255))
    new_img.paste(img2, (0, 0))            # L'image suivante à gauche
    new_img.paste(img1, (new_width2, 0))     # L'image courante à droite

    new_img.save(output_path)

def process_folder_of_images(image_files, output_folder):
    """
    Processes images in order and merges consecutive pages identified as double-page spreads.
    - Merged images are named after the first page of the pair.
    - Skips the next page once merged.
    - Saves the result in output_folder.
    - Returns the list of processed (final) files in the new order.
    """
    os.makedirs(output_folder, exist_ok=True)
    
    i = 0
    total_images = len(image_files)
    output_files = []

    while i < total_images:
        current_image = image_files[i]
        base_name = os.path.splitext(os.path.basename(current_image))[0]
        
        print(f"[INFO] Processing page: {current_image}")
        
        if i < total_images - 1:
            # Look at the next page
            next_image = image_files[i+1]
            
            # Check both the current page and the next one
            current_is_spread = is_spread_candidate(current_image)
            next_is_spread = is_spread_candidate(next_image)
            
            if current_is_spread and next_is_spread:
                # Spread detected: merge them
                merged_filename = f"{base_name}.jpg"
                merged_path = os.path.join(output_folder, merged_filename)
                
                print(f"[INFO] => Spread detected between "
                      f"{os.path.basename(current_image)} and {os.path.basename(next_image)}. Merging...")
                
                merge_images_horizontally(current_image, next_image, merged_path)
                
                print(f"[INFO] => Merge complete: {merged_path}")

                output_files.append(merged_path)
                
                # Skip the next page
                i += 2
                continue
            else:
                # Not a spread, just copy the image
                output_path = os.path.join(output_folder, os.path.basename(current_image))
                Image.open(current_image).save(output_path)
                output_files.append(output_path)
                i += 1
        else:
            # Last image, no comparison possible
            output_path = os.path.join(output_folder, os.path.basename(current_image))
            Image.open(current_image).save(output_path)
            output_files.append(output_path)
            i += 1

    return output_files

def create_cbz_from_folder(folder_path, cbz_output_path):
    """
    Creates a ZIP file (renamed to .cbz) from all the image files in 'folder_path'.
    Compresses any images (jpg, png, etc.), preserving the same folder structure.
    """
    files_to_add = []
    for root, dirs, files in os.walk(folder_path):
        for filename in files:
            if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                full_path = os.path.join(root, filename)
                rel_path = os.path.relpath(full_path, folder_path)
                files_to_add.append((full_path, rel_path))

    with zipfile.ZipFile(cbz_output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_full, file_rel in files_to_add:
            zipf.write(file_full, arcname=file_rel)

def process_one_cbz(cbz_path, temp_folder):
    """
    Processes a single CBZ file:
    - Extracts to a temporary folder.
    - Detects/fuses double-page spreads (unless the border is fully black).
    - Recreates a CBZ (suffix '_fused') in the same directory as cbz_path.
    """
    base_name = os.path.splitext(os.path.basename(cbz_path))[0]
    parent_dir = os.path.dirname(cbz_path)

    # Extraction folder for this CBZ
    extract_folder = os.path.join(temp_folder, base_name + "_extract")
    # Folder where we save final images
    output_folder = os.path.join(temp_folder, base_name + "_fused_images")

    # 1) Extraction
    print(f"\n[INFO] Extracting CBZ: {cbz_path}")
    os.makedirs(extract_folder, exist_ok=True)
    image_files = extract_cbz(cbz_path, extract_folder)
    
    print(f"[INFO] {len(image_files)} images extracted.")

    # 2) Merging
    print("[INFO] Starting detection/fusion of spreads...")
    fused_files = process_folder_of_images(image_files, output_folder)
    print("[INFO] Fusion complete.")

    # 3) Rebuild the .cbz from the final images
    fused_cbz_name = base_name + "_fused.cbz"
    fused_cbz_path = os.path.join(parent_dir, fused_cbz_name)

    print(f"[INFO] Creating new CBZ: {fused_cbz_path}")
    create_cbz_from_folder(output_folder, fused_cbz_path)
    print("[INFO] New CBZ created successfully.")

    # 4) (Optional) Cleanup of temporary folders
    # import shutil
    # shutil.rmtree(extract_folder)
    # shutil.rmtree(output_folder)

def main():
    """
    Usage: python spread_fuse.py /path/to/folder
    - Scans all .cbz files in the folder.
    - For each file, creates <file>_fused.cbz by merging double-page spreads.
    - Does NOT merge if the left/right border is entirely black.
    """
    if len(sys.argv) < 2:
        print("Usage: python spread_fuse.py /path/to/folder")
        sys.exit(1)
    
    input_folder = sys.argv[1]
    
    # Verify that it's a valid folder
    if not os.path.isdir(input_folder):
        print(f"[ERROR] '{input_folder}' is not a valid folder.")
        sys.exit(1)

    # Create a temporary folder
    temp_folder = os.path.join(input_folder, "temp_spread_fuse")
    if not os.path.exists(temp_folder):
        os.makedirs(temp_folder)

    # List all .cbz in the folder
    cbz_files = [f for f in os.listdir(input_folder) if f.lower().endswith(".cbz")]
    
    if not cbz_files:
        print("[INFO] No .cbz files found in the folder.")
        sys.exit(0)

    for cbz_file in cbz_files:
        cbz_path = os.path.join(input_folder, cbz_file)
        process_one_cbz(cbz_path, temp_folder)

    print("\n[INFO] All .cbz files have been processed.")

if __name__ == "__main__":
    main()
