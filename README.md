# Mangas CBZ Spread Fuser

A Python script that processes CBZ (Comic Book ZIP) files by:
1. Extracting images.
2. Detecting double-page spreads using border pixel analysis.
3. Merging consecutive images if they form a spread (except when the border is fully black).
4. Repackaging everything into a new CBZ file.

## Features

- **Automatic Extraction:** Unzip `.cbz` files into a temporary folder.
- **Spread Detection:** Analyze both left and right borders for non-white pixels. Skip merging if the edge is entirely black (useful for flashback pages, etc.).
- **Image Merging:** Combine two consecutive images side by side if they qualify as a spread.
- **CBZ Repack:** Create a new `.cbz` file (with `_fused` suffix) containing the merged pages.

## Requirements

- Python 3.x
- [Pillow](https://pillow.readthedocs.io/en/stable/) (PIL fork)
- (Optional) `zipfile` is part of the Python standard library

Install Pillow:
```bash
pip install pillow
