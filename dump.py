import os
import json
import re

# --- Configuration ---
INPUT_DIR = 'input/Story'
OUTPUT_DIR = 'output/Story'
TEXT_ENCODING = 'shift-jis'

# Dialogue and Choice Signatures
DIALOGUE_SIGNATURES = [
    b'\x86\x66\x01\x1e\x00\x1f', b'\x86\x28\x01\x1e\x00\x1f', b'\x86\x65\x00\x1e\x00\x1f',
    b'\x86\x8e\x01\x1e\x00\x1f', b'\xea\x02\x03\xff\x1e\x00\x1f', b'\x86\x74\x01\x1e\x00\x1f',
    b'\x86\x74\x00\x1e\x00\x1f', b'\x86\x19\x01\x1e\x00\x1f', b'\x86\x16\x00\x1e\x00\x1f',
    b'\x86\x18\x00\x1e\x00\x1f', b'\x86\x14\x01\x1e\x00\x1f', b'\x7f\x00\x1e\x00\x1f',
    b'\x02\x01\x1e\x00\x1f', b'\x28\x01\xef\xfa\xff\x1e\x00\x1f', b'\x86\x0a\x00\x1e\x00\x1f',
    b'\x86\x16\x01\x1e\x00\x1f', b'\x86\x65\x01\x1e\x00\x1f', b'\x86\x66\x00\x1e\x00\x1f', b'\x25\x06\x01',
    b'\x32\x1e\x00\x1f', b'\x1e\x00\x1f', b'\x25\x02\x01', b'\x25\x03\x01', b'\x25\x05\x01', b'\x25\x0A\x01',
    b'\x86\x28\x01\xea\x02\x03\xff\x1e\x00\x1f', b'\x25\x04\x01', b'\x25\x07\x01', b'\x25\x08\x01', b'\x25\x09\x01',
    b'\x25\x01\x01'
]
CHOICE_BLOCK_START_SIGS = [b'\x24\x03\x03', b'\x24\x02\x02', b'\x24\x01\x01']
CHOICE_BLOCK_END_CMD = b'\x01'
ALL_SIGNATURES = DIALOGUE_SIGNATURES + CHOICE_BLOCK_START_SIGS

def robust_decode(payload_bytes, encoding='shift-jis'):
    result = []
    i = 0
    while i < len(payload_bytes):
        byte = payload_bytes[i]
        if byte < 0x20:
            result.append(f"{{HEX:{byte:02X}}}")
            i += 1
            continue
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
            result.append(f"{{HEX:{byte:02X}}}")
            i += 1
    return "".join(result)

def extract_from_file(filepath):
    print(f"Processing file: {os.path.basename(filepath)}...")
    with open(filepath, 'rb') as f:
        content = f.read()

    pointers = []
    strings = []
    try:
        header_size = int.from_bytes(content[0:4], 'little')
        for i in range(4, header_size, 5):
            if i + 5 > header_size:
                break
            tag = content[i]
            pointer_base = int.from_bytes(content[i+1:i+5], 'little')
            pointers.append({"offset_in_header": i, "tag": f"{tag:02X}", "pointer_base": pointer_base})
    except (IndexError, ValueError):
        header_size = 0

    current_pos = header_size
    while current_pos < len(content):
        next_pos, found_sig, is_choice_block = -1, None, False
        for sig in ALL_SIGNATURES:
            pos = content.find(sig, current_pos)
            if pos != -1 and (next_pos == -1 or pos < next_pos):
                if sig in CHOICE_BLOCK_START_SIGS and pos > 0 and content[pos - 1] == 0x20:
                    next_pos, found_sig, is_choice_block = pos, sig, True
                elif sig in DIALOGUE_SIGNATURES:
                    next_pos, found_sig = pos, sig

        if next_pos == -1:
            break

        if not is_choice_block:
            chain_pos = next_pos + len(found_sig)
            while True:
                len_offset = chain_pos
                if len_offset >= len(content):
                    break
                length = content[len_offset]
                payload_start, payload_end = len_offset + 1, len_offset + 1 + length
                if length > 0 and payload_end <= len(content):
                    strings.append({
                        "type": "dialogue",
                        "length_offset": len_offset,
                        "original_length": length,
                        "original_text": robust_decode(content[payload_start:payload_end])
                    })
                chain_pos = payload_end
                if not (chain_pos + 1 < len(content) and content[chain_pos] == 0x1F):
                    break
                chain_pos += 1
            current_pos = chain_pos
        else:
            choice_pos = next_pos + len(found_sig)
            if choice_pos < len(content) and content[choice_pos] < 0x10:
                choice_pos += 1
            num_options = int(found_sig[1:2].hex())
            for i in range(num_options):
                if choice_pos + 2 > len(content):
                    break
                tag_val = content[choice_pos] if i > 0 else content[next_pos + 3]
                if i > 0:
                    choice_pos += 1
                len_byte_offset = choice_pos
                length = content[len_byte_offset]
                payload_start, payload_end = len_byte_offset + 1, len_byte_offset + 1 + length
                if length > 0 and payload_end <= len(content):
                    strings.append({
                        "type": "choice",
                        "tag": f"{tag_val:02X}",
                        "length_offset": len_byte_offset,
                        "original_length": length,
                        "original_text": robust_decode(content[payload_start:payload_end])
                    })
                choice_pos = payload_end
            end_pos = content.find(CHOICE_BLOCK_END_CMD, choice_pos)
            current_pos = end_pos + 1 if end_pos != -1 else choice_pos

    strings.sort(key=lambda x: x['length_offset'])

    # === New magic number logic ===
    magic_number = None
    if pointers:
        print("  -> Calculating magic number...")

        first_choice = next((s for s in strings if s["type"] == "choice"), None)

        if first_choice:
            tag = first_choice.get("tag")
            pointer = next((p for p in pointers if p["tag"] == tag), None)

            if pointer:
                pointer_base = pointer["pointer_base"]
                # Now find the first dialogue after that offset
                next_dialogue = next((s for s in strings if s["type"] == "dialogue" and s["length_offset"] > pointer_base), None)

                if next_dialogue:
                    magic_number = next_dialogue["length_offset"] - pointer_base
                    print(f"     Magic number found: {magic_number} (0x{magic_number:X})")

    if magic_number is not None:
        for ptr in pointers:
            ptr['original_target'] = f"0x{ptr['pointer_base'] + magic_number:X}"

    final_data = []
    for i, entry in enumerate(strings):
        ordered_entry = {
            "id": i,
            "type": entry.get("type"),
            "tag": entry.get("tag"),
            "length_offset": entry['length_offset'],
            "original_length": entry['original_length'],
            "original_text": entry['original_text'],
            "translated_text": ""
        }
        final_data.append(ordered_entry)

    return {"magic_number": magic_number, "pointers": pointers, "strings": final_data}

def main():
    if not os.path.exists(INPUT_DIR):
        print(f"Error: Input folder '{INPUT_DIR}' not found.")
        return
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    unextracted_files = []
    print(f"--- Starting Definitive .scr Script Extractor ---")

    scr_files = [f for f in os.listdir(INPUT_DIR) if f.lower().endswith('.scr')]
    for filename in scr_files:
        print(f"\nProcessing: {filename}")
        input_filepath = os.path.join(INPUT_DIR, filename)
        data = extract_from_file(input_filepath)
        if data and (data.get('strings') or data.get('pointers')):
            output_filename = os.path.splitext(filename)[0] + '.json'
            output_filepath = os.path.join(OUTPUT_DIR, output_filename)
            with open(output_filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            print(f"  -> Saved to: {output_filepath}")
        else:
            unextracted_files.append(filename)

    print("\n\n--- Extraction Finished ---")
    if unextracted_files:
        print(f"\n--- {len(unextracted_files)} .scr files with no extracted data ---")
        for filename in sorted(unextracted_files):
            print(f"- {filename}")
    else:
        print("\n--- Final Report ---")
        print("All .scr files with data were successfully extracted!")

if __name__ == '__main__':
    main()
