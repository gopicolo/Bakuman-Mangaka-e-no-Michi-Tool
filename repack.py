import os
import json
import re

# --- Configuration ---
INPUT_DIR = 'input/Story'
JSON_DIR = 'output/Story'
MODIFIED_DIR = 'modified/Story'
TEXT_ENCODING = 'shift-jis'

def encode_with_placeholders(text_string, encoding='shift-jis'):
    """Converts a string with {HEX:XX} placeholders back into bytes."""
    parts = re.split(r'({HEX:[0-9A-Fa-f]{2}})', text_string)
    final_bytes = bytearray()
    for part in parts:
        if part.startswith('{HEX:'):
            hex_val = part[5:7]
            final_bytes.append(int(hex_val, 16))
        elif part:
            try:
                final_bytes.extend(part.encode(encoding))
            except UnicodeEncodeError as e:
                print(f"\n  WARNING: Character '{e.object[e.start:e.end]}' could not be encoded. It will be skipped.")
    return final_bytes

def repack_with_pointers(json_path, original_scr_path, output_scr_path):
    print(f"Processing: {os.path.basename(json_path)}")
    with open(original_scr_path, 'rb') as f:
        original_content = f.read()
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    magic_number = data.get('magic_number')
    pointers = data.get('pointers', [])
    strings = data.get('strings', [])
    
    if not strings:
        print("  -> No strings to process. Copying original file.")
        os.makedirs(os.path.dirname(output_scr_path), exist_ok=True)
        with open(output_scr_path, 'wb') as f:
            f.write(original_content)
        return

    # 1. Calculate length changes for each string
    size_diffs = {}
    for entry in strings:
        text_to_insert = entry.get('translated_text') or entry.get('original_text')
        new_bytes = encode_with_placeholders(text_to_insert)
        new_len = len(new_bytes)
        original_len = entry['original_length']
        size_diffs[entry['length_offset']] = (1 + new_len) - (1 + original_len)

    # 2. Rebuild the script body
    header_size = int.from_bytes(original_content[0:4], 'little')
    new_body = bytearray()
    last_pos = header_size
    
    for entry in strings:
        offset = entry['length_offset']
        original_len = entry['original_length']
        chunk = original_content[last_pos:offset]
        new_body.extend(chunk)
        text_to_insert = entry.get('translated_text') or entry.get('original_text')
        new_bytes = encode_with_placeholders(text_to_insert)
        new_len = len(new_bytes)
        new_body.append(new_len)
        new_body.extend(new_bytes)
        last_pos = offset + 1 + original_len

    new_body.extend(original_content[last_pos:])
    
    # 3. Rebuild the header with updated pointers
    new_header = bytearray(original_content[:header_size])
    sorted_string_offsets = sorted(size_diffs.keys())

    if magic_number is not None:
        for ptr in pointers:
            if 'original_target' not in ptr:
                continue
            
            original_target = int(ptr['original_target'], 16)
            if original_target == 0:
                continue
            
            total_shift = 0
            for offset in sorted_string_offsets:
                if offset < original_target:
                    total_shift += size_diffs.get(offset, 0)
            
            new_target_real = original_target + total_shift
            new_target_base = new_target_real - magic_number
            
            new_pointer_bytes = new_target_base.to_bytes(4, 'little', signed=False)
            header_write_pos = ptr['offset_in_header']
            new_header[header_write_pos+1:header_write_pos+5] = new_pointer_bytes

    # 4. Join new header and body and save
    final_content = new_header + new_body
    os.makedirs(os.path.dirname(output_scr_path), exist_ok=True)
    with open(output_scr_path, 'wb') as f:
        f.write(final_content)
        
    print(f"  -> Rebuild with corrected pointers completed.")

def main():
    if not os.path.exists(INPUT_DIR) or not os.path.exists(JSON_DIR):
        print(f"Error: Make sure the folders '{INPUT_DIR}' and '{JSON_DIR}' exist.")
        return
    print("--- Starting Final Repack of .scr Scripts (with Pointers) ---")
    
    json_files = [f for f in os.listdir(JSON_DIR) if f.lower().endswith('.json')]
    for filename in json_files:
        print(f"\nProcessing {filename}...")
        base_name = os.path.splitext(filename)[0]
        json_path = os.path.join(JSON_DIR, filename)
        original_scr_path = os.path.join(INPUT_DIR, base_name + '.scr')
        output_scr_path = os.path.join(MODIFIED_DIR, base_name + '.scr')
        if not os.path.exists(original_scr_path):
            print(f"  WARNING: Original file '{original_scr_path}' not found. Skipping.")
            continue
        repack_with_pointers(json_path, original_scr_path, output_scr_path)
        
    print("\n--- Repack Completed ---")

if __name__ == '__main__':
    main()
