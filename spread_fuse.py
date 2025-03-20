import os
import sys
import zipfile
from PIL import Image

def extract_cbz(cbz_path, extract_folder):
    """
    Extrait le contenu d'un fichier .cbz (format zip) dans un dossier spécifié.
    Retourne la liste des fichiers images extraits (chemins complets).
    """
    with zipfile.ZipFile(cbz_path, 'r') as zip_ref:
        zip_ref.extractall(extract_folder)

    extracted_files = []
    for root, dirs, files in os.walk(extract_folder):
        for file in files:
            if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                extracted_files.append(os.path.join(root, file))

    extracted_files.sort()
    return extracted_files

def is_spread_candidate(image_path, border_size=5, white_threshold=250, black_threshold=20, black_border_ratio_threshold=0.45):
    """
    Détermine si une image est candidate à la fusion en vérifiant ses bords.
    Pour chaque bord (gauche et droit) :
      - On vérifie qu'il existe au moins un pixel non blanc.
      - Si plus de 'black_border_ratio_threshold' des pixels du bord sont noirs (i.e. avg <= black_threshold),
        le bord est considéré comme majoritairement noir et l'image n'est pas candidate.
    """
    img = Image.open(image_path).convert('RGB')
    width, height = img.size

    # Bord gauche
    left_border_has_nonwhite = False
    left_black_count = 0
    left_total = border_size * height
    for x in range(border_size):
        for y in range(height):
            r, g, b = img.getpixel((x, y))
            avg = (r + g + b) / 3
            if avg < white_threshold:
                left_border_has_nonwhite = True
            if avg <= black_threshold:
                left_black_count += 1
    left_black_ratio = left_black_count / left_total
    left_border_mostly_black = left_black_ratio > black_border_ratio_threshold

    # Bord droit
    right_border_has_nonwhite = False
    right_black_count = 0
    right_total = border_size * height
    for x in range(width - border_size, width):
        for y in range(height):
            r, g, b = img.getpixel((x, y))
            avg = (r + g + b) / 3
            if avg < white_threshold:
                right_border_has_nonwhite = True
            if avg <= black_threshold:
                right_black_count += 1
    right_black_ratio = right_black_count / right_total
    right_border_mostly_black = right_black_ratio > black_border_ratio_threshold

    if left_border_mostly_black or right_border_mostly_black:
        return False

    return left_border_has_nonwhite and right_border_has_nonwhite

def merge_images_horizontally(image_path1, image_path2, output_path):
    """
    Fusionne deux images côte à côte en alignant leur haut et leur bas selon l'image la plus grande.
    Si l'une des images est plus petite, elle est redimensionnée proportionnellement.
    L'image issue de image_path2 sera à gauche et celle de image_path1 à droite.
    """
    img1 = Image.open(image_path1).convert('RGB')
    img2 = Image.open(image_path2).convert('RGB')
    
    width1, height1 = img1.size
    width2, height2 = img2.size
    new_height = max(height1, height2)

    if height1 != new_height:
        new_width1 = int(width1 * new_height / height1)
        img1 = img1.resize((new_width1, new_height), Image.Resampling.LANCZOS)
    else:
        new_width1 = width1

    if height2 != new_height:
        new_width2 = int(width2 * new_height / height2)
        img2 = img2.resize((new_width2, new_height), Image.Resampling.LANCZOS)
    else:
        new_width2 = width2

    new_width = new_width1 + new_width2
    new_img = Image.new('RGB', (new_width, new_height), color=(255, 255, 255))
    new_img.paste(img2, (0, 0))
    new_img.paste(img1, (new_width2, 0))
    new_img.save(output_path)

def process_folder_of_images(image_files, output_folder):
    """
    Traite la liste des images et fusionne les pages consécutives identifiées comme spreads.
    - Les images fusionnées conservent le nom de la première image du couple.
    - Les pages fusionnées ne sont pas retraitées.
    - Le résultat est sauvegardé dans output_folder.
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
            next_image = image_files[i+1]
            current_is_spread = is_spread_candidate(current_image)
            next_is_spread = is_spread_candidate(next_image)
            
            if current_is_spread and next_is_spread:
                merged_filename = f"{base_name}.jpg"
                merged_path = os.path.join(output_folder, merged_filename)
                print(f"[INFO] => Spread detected between {os.path.basename(current_image)} and {os.path.basename(next_image)}. Merging...")
                merge_images_horizontally(current_image, next_image, merged_path)
                print(f"[INFO] => Merge complete: {merged_path}")
                output_files.append(merged_path)
                i += 2
                continue
            else:
                output_path = os.path.join(output_folder, os.path.basename(current_image))
                Image.open(current_image).save(output_path)
                output_files.append(output_path)
                i += 1
        else:
            output_path = os.path.join(output_folder, os.path.basename(current_image))
            Image.open(current_image).save(output_path)
            output_files.append(output_path)
            i += 1

    return output_files

def create_cbz_from_folder(folder_path, cbz_output_path):
    """
    Crée un fichier ZIP (renommé en .cbz) à partir de toutes les images dans folder_path.
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
    Traite un fichier CBZ :
    - Extraction dans un dossier temporaire.
    - Détection et fusion des spreads.
    - Recréation d'un CBZ (suffixé _fused) dans le même répertoire que le CBZ d'origine.
    """
    base_name = os.path.splitext(os.path.basename(cbz_path))[0]
    parent_dir = os.path.dirname(cbz_path)
    extract_folder = os.path.join(temp_folder, base_name + "_extract")
    output_folder = os.path.join(temp_folder, base_name + "_fused_images")

    print(f"\n[INFO] Extracting CBZ: {cbz_path}")
    os.makedirs(extract_folder, exist_ok=True)
    image_files = extract_cbz(cbz_path, extract_folder)
    print(f"[INFO] {len(image_files)} images extracted.")

    print("[INFO] Starting detection/fusion of spreads...")
    fused_files = process_folder_of_images(image_files, output_folder)
    print("[INFO] Fusion complete.")

    fused_cbz_name = base_name + "_fused.cbz"
    fused_cbz_path = os.path.join(parent_dir, fused_cbz_name)
    print(f"[INFO] Creating new CBZ: {fused_cbz_path}")
    create_cbz_from_folder(output_folder, fused_cbz_path)
    print("[INFO] New CBZ created successfully.")

    # Optionnel : nettoyage des dossiers temporaires
    # import shutil
    # shutil.rmtree(extract_folder)
    # shutil.rmtree(output_folder)

def main():
    """
    Utilisation :
      - Pour traiter un dossier : python spread_fuse.py /chemin/vers/dossier
      - Pour traiter un fichier CBZ unique : python spread_fuse.py /chemin/vers/fichier.cbz

    Le script scanne l'entrée et si c'est un dossier, il traite tous les .cbz qu'il contient.
    """
    if len(sys.argv) < 2:
        print("Usage: python spread_fuse.py /chemin/vers/dossier_ou_fichier.cbz")
        sys.exit(1)
    
    input_path = sys.argv[1]

    # Création d'un dossier temporaire dans le même répertoire que l'entrée
    if os.path.isfile(input_path) and input_path.lower().endswith(".cbz"):
        temp_folder = os.path.join(os.path.dirname(input_path), "temp_spread_fuse")
        os.makedirs(temp_folder, exist_ok=True)
        process_one_cbz(input_path, temp_folder)
    elif os.path.isdir(input_path):
        temp_folder = os.path.join(input_path, "temp_spread_fuse")
        os.makedirs(temp_folder, exist_ok=True)
        cbz_files = [f for f in os.listdir(input_path) if f.lower().endswith(".cbz")]
        if not cbz_files:
            print("[INFO] Aucun fichier .cbz trouvé dans le dossier.")
            sys.exit(0)
        for cbz_file in cbz_files:
            cbz_path = os.path.join(input_path, cbz_file)
            process_one_cbz(cbz_path, temp_folder)
    else:
        print("[ERROR] L'argument doit être un dossier ou un fichier .cbz")
        sys.exit(1)

    print("\n[INFO] Traitement terminé.")

if __name__ == "__main__":
    main()
