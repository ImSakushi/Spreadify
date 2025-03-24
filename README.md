# 📚 Automatic Mangas CBZ Spread Fuser

**A Python script to automatically detect and merge double-page spreads in `.cbz` manga files, enhancing the reading experience.**

---

## 🚀 Features

- 📂 **Automatic Extraction**: Unzips `.cbz` files into a temporary folder.
- 🧠 **Smart Spread Detection**: Analyzes the left and right borders of images to detect spreads.
  - Skips merging if either edge is completely black (commonly used for flashbacks or transitions).
- 🖼️ **Image Merging**: Combines two consecutive pages side by side if they qualify as a spread.
- 📦 **CBZ Repackaging**: Generates a new `.cbz` file with the suffix `_fused` containing the merged pages.

---

## 🔧 Requirements

- **Python 3.x**
- [Pillow (PIL fork)](https://pillow.readthedocs.io/en/stable/)

### Install Dependencies
```bash
pip install pillow
```

---

## 🛠️ Usage

### 1. Process a single `.cbz` file:
```bash
python spread_fuse.py /path/to/file.cbz
```

### 2. Process a folder containing multiple `.cbz` files:
```bash
python spread_fuse.py /path/to/folder
```

The script automatically detects whether the input is a file or a folder. All `.cbz` files in the folder will be processed.

---

## 📁 Output Structure

For each `.cbz` file:
- Pages are extracted into a temporary folder.
- Consecutive images forming a spread are merged.
- A new `.cbz` file is created: `original_name_fused.cbz`.

---

## 🧪 How It Works

1. Images are extracted and sorted alphabetically.
2. Each image is analyzed:
   - If both current and next image have visible (non-white) borders and are not mostly black → they are merged.
3. Merged images replace the original pair, and a new `.cbz` file is created with the updated content.

---

## ⚙️ Technical Notes

- Spread detection is based on:
  - The percentage of black pixels on each border (default threshold: 45%).
  - Presence of at least one non-white pixel on both edges.
- Border size and thresholds can be adjusted directly in the script.

---

## 🧼 Temporary File Cleanup

> Temporary folders are **not** automatically deleted by default.  
You can uncomment the `shutil.rmtree(...)` lines in the script to enable cleanup after processing.

---

## 🧩 Potential Future Features

- GUI support for drag-and-drop usage.
- Command-line arguments to adjust thresholds.
- Support for `.cbr` and `.rar` files.

---

## 📜 License

This script is open source. Feel free to use or modify it for personal projects, scanlation teams, or manga reading tools.
