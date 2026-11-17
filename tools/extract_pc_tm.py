import json
import os
import struct

PC_ASSETS = r"C:\Program Files (x86)\Steam\steamapps\common\GNOSIA\Gnosia_Data\sharedassets0.assets"
OUT_TM = r"c:\Users\Nikola\Desktop\AI PROJECTS\Gnosia\translation_memory.json"


def read_unity_str(buf, pos):
    if pos + 4 > len(buf):
        return None, pos
    ln = struct.unpack_from("<I", buf, pos)[0]
    if ln == 0 or ln > 4096 or pos + 4 + ln > len(buf):
        return None, pos
    raw = buf[pos + 4 : pos + 4 + ln]
    try:
        s = raw.decode("utf-8")
    except UnicodeDecodeError:
        return None, pos
    return s, pos + 4 + ln + ((4 - (ln % 4)) % 4)


def norm(s):
    return s.replace("\\n", "").replace("\n", "").replace("\u3000", "").replace(" ", "")


def main():
    with open(PC_ASSETS, "rb") as f:
        pc = f.read()

    exact = {}
    normalized = {}
    for pos in range(0, len(pc) - 16, 4):
        if pc[pos : pos + 4] == b"\x03\x00\x00\x00":
            s0, p1 = read_unity_str(pc, pos + 4)
            if s0 and any("\u3040" <= c <= "\u9fff" for c in s0):
                s1, p2 = read_unity_str(pc, p1)
                s2, p3 = read_unity_str(pc, p2)
                if s1 is not None and s2 is not None:
                    jp_clean = s0.replace("\\n", "\n").replace('\\"', '"').replace("\\'", "'")
                    en_clean = s1.replace("\\n", "\n").replace('\\"', '"').replace("\\'", "'")
                    exact[jp_clean] = en_clean
                    normalized[norm(s0)] = en_clean

    os.makedirs(os.path.dirname(OUT_TM), exist_ok=True)
    with open(OUT_TM, "w", encoding="utf-8") as f:
        json.dump({"exact": exact, "normalized": normalized}, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(exact)} exact and {len(normalized)} normalized pairs -> {OUT_TM}")


if __name__ == "__main__":
    main()
