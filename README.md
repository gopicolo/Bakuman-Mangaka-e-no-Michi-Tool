# Bakuman. - Mangaka e no Michi (DS) Script Tools

This repository contains two Python scripts created by gopicolo for extracting and reinserting dialogue text from the game **Bakuman. - Mangaka e no Michi** for Nitendo DS.

## 🛠 Scripts

### 📝 `dump.py`

Extracts text strings from `.scr` script files found in `input/Story` and saves them as `.json` files in `output/Story`.

Each string block contains:
- `id`: Unique ID
- `offset_tamanho`: Offset of the byte that stores the string length
- `tamanho_original`: Original length in bytes
- `texto_original`: Original Shift-JIS string (decoded)
- `texto_traduzido`: Field left empty for translation

Supports various command signatures to ensure full coverage of dialogue strings, and handles multi-part (chained) blocks.

### 📦 `repack.py`

Reinserts the translated strings back into the original `.scr` files.

- Reads the `.json` files from `output/Story`
- Replaces the original strings in `input/Story` with the translated text
- Outputs the modified `.scr` files to `modified/Story`
- Automatically encodes text back to Shift-JIS and respects `{HEX:XX}` placeholders

If the translated string fails to encode, the original is kept.

## 📁 Folder Structure

```
.
├── input/
│   └── Story/              # Original .scr files from the game
├── output/
│   └── Story/              # Extracted JSONs (text to translate)
├── modified/
│   └── Story/              # Repacked .scr files with translations
```

## 💬 Text Encoding

All game text is encoded in **Shift-JIS**. The scripts handle decoding and encoding automatically. Corrupted or unreadable bytes are replaced with `{HEX:XX}` during dump and reinserted as-is during repack.

## ✅ Requirements

- Python 3.x
- No external dependencies (pure Python)

## 🔄 Usage

1. Place original `.scr` files in `input/Story`
2. Run `dump.py` to extract the text
3. Edit the `texto_traduzido` fields in the `.json` files in `output/Story`
4. Run `repack.py` to reinsert the translated strings
5. Use the files from `modified/Story` in your patched game

---
