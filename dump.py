import os
import json

# --- Configuration ---
INPUT_DIR = 'input/Story'
OUTPUT_DIR = 'output/Story'
TEXT_ENCODING = 'shift-jis'

# List of command signatures that precede a text block.
# This list is quite complete.
COMMAND_SIGNATURES = [
    b'\x86\x66\x01\x1e\x00\x1f', b'\x86\x28\x01\x1e\x00\x1f', b'\x86\x65\x00\x1e\x00\x1f',
    b'\x86\x8e\x01\x1e\x00\x1f', b'\xea\x02\x03\xff\x1e\x00\x1f', b'\x86\x74\x01\x1e\x00\x1f',
    b'\x86\x74\x00\x1e\x00\x1f', b'\x86\x19\x01\x1e\x00\x1f', b'\x86\x16\x00\x1e\x00\x1f',
    b'\x86\x18\x00\x1e\x00\x1f', b'\x86\x14\x01\x1e\x00\x1f', b'\x7f\x00\x1e\x00\x1f',
    b'\x02\x01\x1e\x00\x1f', b'\x28\x01\xef\xfa\xff\x1e\x00\x1f', b'\x86\x0a\x00\x1e\x00\x1f',
    b'\x86\x16\x01\x1e\x00\x1f', b'\x86\x65\x01\x1e\x00\x1f', b'\x86\x66\x00\x1e\x00\x1f',
    b'\x32\x1e\x00\x1f', b'\x1e\x00\x1f',
]

def robust_decode(payload_bytes, encoding='shift-jis'):
    """
    Decodes text and replaces invalid bytes/sequences with placeholders like {HEX:XX}.
    """
    try:
        return payload_bytes.decode(encoding)
    except UnicodeDecodeError:
        result = []
        i = 0
        while i < len(payload_bytes):
            try:
                char = payload_bytes[i:i+2].decode(encoding)
                result.append(char)
                i += 2
                continue
            except UnicodeDecodeError:
                pass
            try:
                char = payload_bytes[i:i+1].decode(encoding)
                result.append(char)
                i += 1
            except UnicodeDecodeError:
                result.append(f"{{HEX:{payload_bytes[i]:02X}}}")
                i += 1
        return "".join(result)

def extract_strings_from_file(filepath):
    print(f"Processing file: {os.path.basename(filepath)}...")
    with open(filepath, 'rb') as f:
        content = f.read()

    extracted_data = []
    string_id = 0
    current_pos = 0

    while current_pos < len(content):
        next_found_pos = -1
        found_signature = None
        for sig in COMMAND_SIGNATURES:
            pos = content.find(sig, current_pos)
            if pos != -1:
                if next_found_pos == -1 or pos < next_found_pos:
                    next_found_pos = pos
                    found_signature = sig
                elif pos == next_found_pos and len(sig) > len(found_signature):
                    found_signature = sig

        if next_found_pos == -1:
            break

        chain_pos = next_found_pos + len(found_signature)

        len_byte_offset = chain_pos
        if len_byte_offset >= len(content):
            break
        length = content[len_byte_offset]

        payload_start = len_byte_offset + 1
        payload_end = payload_start + length
        if payload_end > len(content):
            current_pos = next_found_pos + 1
            continue

        payload = content[payload_start:payload_end]
        original_text = robust_decode(payload)

        entry = {
            "id": string_id,
            "offset_tamanho": len_byte_offset,
            "tamanho_original": length,
            "texto_original": original_text,
            "texto_traduzido": ""
        }
        extracted_data.append(entry)
        string_id += 1
        chain_pos = payload_end

        # --- NEW LOGIC: Loop to detect chained continuation blocks ---
        while True:
            if chain_pos + 1 < len(content) and content[chain_pos] == 0x1F:
                len_byte_offset = chain_pos + 1
                length = content[len_byte_offset]

                if length == 0:
                    break

                payload_start = len_byte_offset + 1
                payload_end = payload_start + length
                if payload_end > len(content):
                    break

                payload = content[payload_start:payload_end]
                original_text = robust_decode(payload)

                entry = {
                    "id": string_id,
                    "offset_tamanho": len_byte_offset,
                    "tamanho_original": length,
                    "texto_original": original_text,
                    "texto_traduzido": ""
                }
                extracted_data.append(entry)
                string_id += 1
                chain_pos = payload_end
            else:
                break

        current_pos = chain_pos

    print(f"  {len(extracted_data)} strings found.")
    return extracted_data

def main():
    if not os.path.exists(INPUT_DIR):
        print(f"Error: Input folder '{INPUT_DIR}' not found.")
        return
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    unextracted_files = []
    print(f"--- Starting Script Extraction ---")
    scr_files = [f for f in os.listdir(INPUT_DIR) if f.lower().endswith('.scr')]
    total_files = len(scr_files)
    for i, filename in enumerate(scr_files):
        print(f"\n[{i+1}/{total_files}]", end=" ")
        input_filepath = os.path.join(INPUT_DIR, filename)
        data = extract_strings_from_file(input_filepath)
        if data:
            output_filename = os.path.splitext(filename)[0] + '.json'
            output_filepath = os.path.join(OUTPUT_DIR, output_filename)
            with open(output_filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            print(f"  -> Saved to: {output_filepath}")
        else:
            unextracted_files.append(filename)
    print("\n\n--- Extraction Complete ---")
    if unextracted_files:
        print(f"\n--- {len(unextracted_files)} .scr files with no text found ---")
        for filename in sorted(unextracted_files):
            print(f"- {filename}")
    else:
        print("\n--- Final Report ---")
        print("All .scr files contained text and were extracted successfully!")

if __name__ == '__main__':
    main()
