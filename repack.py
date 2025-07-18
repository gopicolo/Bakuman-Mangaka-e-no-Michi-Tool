import os
import json
import re

# --- Configuration ---
INPUT_DIR = 'input/Story'
JSON_DIR = 'output/Story'
MODIFIED_DIR = 'modified/Story'
TEXT_ENCODING = 'shift-jis'

def encode_with_placeholders(text_string, encoding='shift-jis'):
    """Convert string with {HEX:XX} placeholders back to bytes."""
    parts = re.split(r'({HEX:[0-9A-Fa-f]{2}})', text_string)
    final_bytes = bytearray()
    for part in parts:
        if part.startswith('{HEX:'):
            hex_val = part[5:7]
            final_bytes.append(int(hex_val, 16))
        elif part:
            final_bytes.extend(part.encode(encoding))
    return final_bytes

def intelligent_repack(json_path, original_scr_path, output_scr_path):
    print(f"Processing: {os.path.basename(json_path)}")
    with open(original_scr_path, 'rb') as f:
        original_content = f.read()
    with open(json_path, 'r', encoding='utf-8') as f:
        translations = json.load(f)

    new_file_data = bytearray()
    last_pos = 0

    for entry in translations:
        text_to_insert = entry.get('texto_traduzido') or entry.get('texto_original')
        offset = entry['offset_tamanho']
        original_len = entry['tamanho_original']

        try:
            new_bytes = encode_with_placeholders(text_to_insert)
            new_len = len(new_bytes)
        except Exception as e:
            print(f"  ERROR processing string ID {entry['id']}: {e}. Keeping original.")
            chunk_to_keep = original_content[last_pos:offset + 1 + original_len]
            new_file_data.extend(chunk_to_keep)
            last_pos = offset + 1 + original_len
            continue

        chunk = original_content[last_pos:offset]
        new_file_data.extend(chunk)

        # Write length byte and data
        new_file_data.append(new_len)
        new_file_data.extend(new_bytes)

        last_pos = offset + 1 + original_len

    final_chunk = original_content[last_pos:]
    new_file_data.extend(final_chunk)

    with open(output_scr_path, 'wb') as f:
        f.write(new_file_data)

    print(f"  -> Repack complete.")

def main():
    if not os.path.exists(INPUT_DIR) or not os.path.exists(JSON_DIR):
        print(f"Error: Make sure '{INPUT_DIR}' and '{JSON_DIR}' folders exist.")
        return
    os.makedirs(MODIFIED_DIR, exist_ok=True)
    print("--- Starting Intelligent Script Repack ---")
    json_files = [f for f in os.listdir(JSON_DIR) if f.lower().endswith('.json')]
    for filename in json_files:
        base_name = os.path.splitext(filename)[0]
        json_path = os.path.join(JSON_DIR, filename)
        original_scr_path = os.path.join(INPUT_DIR, base_name + '.scr')
        output_scr_path = os.path.join(MODIFIED_DIR, base_name + '.scr')

        if not os.path.exists(original_scr_path):
            print(f"\nWARNING: Original file '{original_scr_path}' not found. Skipping.")
            continue

        intelligent_repack(json_path, original_scr_path, output_scr_path)
    print("\n--- Repack Complete ---")

if __name__ == '__main__':
    main()
