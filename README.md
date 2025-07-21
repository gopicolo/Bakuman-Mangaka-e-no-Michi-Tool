# `.scr` Script Extractor & Repacker with Pointer Fixes

This repository contains two Python tools for **extracting** and **repacking** `.scr` script files from games that use Shift-JIS encoding and a specific internal pointer system.

---

## Overview

- The first script extracts strings from `.scr` files, detecting dialogues, choice blocks, and pointers, saving everything in organized JSON files for editing and translation.
- The second script rebuilds `.scr` files from these JSONs, updating header pointers to reflect changes in translated text lengths.

These tools were developed to streamline the translation and modification process of games using this script format, ensuring the game runs correctly after text edits.

---

## Features

- **Robust extraction** of Shift-JIS encoded strings, including placeholders for special bytes (e.g. `{HEX:XX}`).
- **Detection and extraction of choice blocks**, handling multiple options and specific tags.
- **Automatic reading and adjustment of header pointers**, with a fixed offset (magic number `0x2D`) applied for proper alignment.
- **Faithful reconstruction** of `.scr` files with updated text, maintaining original format integrity.
- Warnings for characters that cannot be encoded in Shift-JIS.

---

## Script Structure

### Extractor (`extract.py`)

- Reads `.scr` files from `input/Story`.
- Identifies and extracts dialogue and choice strings.
- Saves extracted data as JSON in `output/Story`.
- Adjusts pointers based on file structure and the fixed offset.

### Repacker (`repack.py`)

- Reads JSON files and original `.scr` files.
- Converts edited strings (including `{HEX:XX}` placeholders) back into bytes.
- Rebuilds `.scr` files with updated texts.
- Recalculates and fixes header pointers.
- Saves rebuilt files in `modified/Story`.

---

## Usage

### Extraction

1. Place `.scr` files in the `input/Story` folder.
2. Run the extractor script:

   ```bash
   python extract.py
   ```

3. The extracted JSON files will be saved in `output/Story`.

### Repacking

1. Edit the JSON files in `output/Story` (translate or modify the text).
2. Run the repacker script:

   ```bash
   python repack.py
   ```

3. The rebuilt `.scr` files will be saved in `modified/Story`.

---

## Requirements

- Python 3.x
- Shift-JIS support (usually included in standard Python)

---

## Notes

- The pointer adjustment value (`0x2D`) is based on reverse-engineering the target game's format.
- The scripts handle non-printable and special bytes by encoding them as `{HEX:XX}` placeholders during extraction and decoding them back during repacking.
- Make sure the folder structure exists before running the scripts.

---

## License

Feel free to use and modify these tools for your projects. Attribution is appreciated.

---

## Author

[gopicolo](https://github.com/gopicolo)

---

If you have any questions or suggestions, feel free to open an issue!
