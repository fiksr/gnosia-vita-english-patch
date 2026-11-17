import json
import os
import re
import struct
import textwrap
import zlib

PC_TM = r"c:\Users\Nikola\Desktop\AI PROJECTS\Gnosia\translation_memory.json"
DELTA_TM = r"c:\Users\Nikola\Desktop\AI PROJECTS\Gnosia\delta_translations.json"
DUMPED_ELF = r"C:\Users\Nikola\Desktop\Vita3K\elfdumps\PCSG01277\0x81000000-0x81AE3CC8_app0.elf"
VITA3K_ORIG = r"C:\Users\Nikola\AppData\Roaming\Vita3K\Vita3K\ux0\app\PCSG01277\eboot.bin.orig"
VITA3K_EBOOT = r"C:\Users\Nikola\AppData\Roaming\Vita3K\Vita3K\ux0\app\PCSG01277\eboot.bin"
OUT_ELF = r"c:\Users\Nikola\Desktop\AI PROJECTS\Gnosia\patched_app0.elf"
OUT_REPORT = r"c:\Users\Nikola\Desktop\AI PROJECTS\Gnosia\elf_patch_report.json"


def norm(s):
    return s.replace("\\n", "").replace("\n", "").replace("\u3000", "").replace(" ", "")


_CONTRACTIONS = [
    ("is not ", "isn't "),
    ("are not ", "aren't "),
    ("was not ", "wasn't "),
    ("were not ", "weren't "),
    ("do not ", "don't "),
    ("does not ", "doesn't "),
    ("did not ", "didn't "),
    ("have not ", "haven't "),
    ("has not ", "hasn't "),
    ("had not ", "hadn't "),
    ("will not ", "won't "),
    ("would not ", "wouldn't "),
    ("could not ", "couldn't "),
    ("should not ", "shouldn't "),
    ("cannot ", "can't "),
    ("can not ", "can't "),
    ("it is ", "it's "),
    ("It is ", "It's "),
    ("that is ", "that's "),
    ("That is ", "That's "),
    ("there is ", "there's "),
    ("There is ", "There's "),
    ("I am ", "I'm "),
    ("you are ", "you're "),
    ("You are ", "You're "),
    ("we are ", "we're "),
    ("We are ", "We're "),
    ("they are ", "they're "),
    ("They are ", "They're "),
    ("I have ", "I've "),
    ("you have ", "you've "),
    ("we have ", "we've "),
    ("I will ", "I'll "),
    ("you will ", "you'll "),
    ("... ", "..."),
    ("… ", "..."),
]


def wrap_english(text, width=56, is_dialogue=False):
    def _wrap(t, w):
        out_lines = []
        for line in t.split("\n"):
            if len(line) <= w:
                out_lines.append(line)
            else:
                out_lines.extend(textwrap.wrap(line, width=w, break_long_words=False, break_on_hyphens=False))
        return out_lines

    # Skill descriptions in Command List have "\n\n" before trigger condition and render in a 25-char box
    if "\n\n" in text and not is_dialogue:
        parts = text.split("\n\n")
        wrapped_parts = []
        for p in parts:
            p_flat = p.replace("\n", " ").strip()
            wrapped_parts.append("\n".join(_wrap(p_flat, 24)) if p_flat else "")
        return "\n\n".join(wrapped_parts)

    if is_dialogue:
        # Reflow PC's manual single newlines into one paragraph for 56-char width
        base_t = re.sub(r"(?<!\n)\n(?!\n)", " ", text)
        lines = _wrap(base_t, width)
    else:
        lines = _wrap(text, width)

    if len(lines) > 3:
        t2 = text.replace("\n", " ")
        lines2 = _wrap(t2, width)
        if len(lines2) <= 3:
            lines = lines2
        else:
            t3 = t2
            for old, new in _CONTRACTIONS:
                t3 = t3.replace(old, new)
            lines3 = _wrap(t3, width)
            if len(lines3) < len(lines):
                lines = lines3
            elif len(lines2) < len(lines):
                lines = lines2
    return "\n".join(lines)


def decode_movw(hw1, hw2):
    if (hw1 & 0xFBF0) == 0xF240 and (hw2 & 0x8000) == 0:
        rd = (hw2 >> 8) & 0xF
        imm = ((hw1 & 0xF) << 12) | (((hw1 >> 10) & 1) << 11) | (((hw2 >> 12) & 7) << 8) | (hw2 & 0xFF)
        return rd, imm
    return None


def decode_movt(hw1, hw2):
    if (hw1 & 0xFBF0) == 0xF2C0 and (hw2 & 0x8000) == 0:
        rd = (hw2 >> 8) & 0xF
        imm = ((hw1 & 0xF) << 12) | (((hw1 >> 10) & 1) << 11) | (((hw2 >> 12) & 7) << 8) | (hw2 & 0xFF)
        return rd, imm
    return None


def encode_movw(rd, imm16):
    imm4 = (imm16 >> 12) & 0xF
    i = (imm16 >> 11) & 1
    imm3 = (imm16 >> 8) & 7
    imm8 = imm16 & 0xFF
    return 0xF240 | (i << 10) | imm4, (imm3 << 12) | (rd << 8) | imm8


def encode_movt(rd, imm16):
    imm4 = (imm16 >> 12) & 0xF
    i = (imm16 >> 11) & 1
    imm3 = (imm16 >> 8) & 7
    imm8 = imm16 & 0xFF
    return 0xF2C0 | (i << 10) | imm4, (imm3 << 12) | (rd << 8) | imm8


def build_fself(orig_self, elf_bytes, out_path):
    hdr_len = struct.unpack_from("<Q", orig_self, 0x10)[0]
    out = bytearray(orig_self[:hdr_len])
    e_phnum = struct.unpack_from("<H", elf_bytes, 44)[0]
    out[0xA0 : 0xA0 + 0x34] = elf_bytes[0:0x34]
    out[0xE0 : 0xE0 + e_phnum * 0x20] = elf_bytes[0x34 : 0x34 + e_phnum * 0x20]

    cur_off = hdr_len
    for i in range(e_phnum):
        p_type, p_offset, p_vaddr, p_paddr, p_filesz, p_memsz, p_flags, p_align = struct.unpack_from(
            "<8I", elf_bytes, 0x34 + i * 32
        )
        seg_raw = bytes(elf_bytes[p_offset : p_offset + p_filesz])
        seg_z = zlib.compress(seg_raw, 6)
        pad = (16 - (cur_off % 16)) % 16
        out.extend(b"\x00" * pad)
        cur_off += pad
        seg_off = cur_off
        out.extend(seg_z)
        cur_off += len(seg_z)
        struct.pack_into("<QQIIII", out, 0x180 + i * 32, seg_off, len(seg_z), 2, 0, 2, 0)

    struct.pack_into("<Q", out, 0x18, len(elf_bytes))
    struct.pack_into("<Q", out, 0x20, len(out))
    with open(out_path, "wb") as f:
        f.write(out)
    return len(out)


def main():
    with open(PC_TM, "r", encoding="utf-8") as f:
        tm = json.load(f)
    exact = tm["exact"]
    normalized = tm["normalized"]

    delta = {}
    if os.path.exists(DELTA_TM):
        with open(DELTA_TM, "r", encoding="utf-8") as f:
            delta = json.load(f)

    with open(DUMPED_ELF, "rb") as f:
        elf = bytearray(f.read())

    # 1. Collect all .rodata JP strings
    rodata_start, rodata_end = 0x759000, 0x87B2BB
    entries = []
    for m in re.finditer(b"[^\x00]{1,}", elf[rodata_start:rodata_end]):
        raw = m.group(0)
        try:
            s = raw.decode("utf-8")
        except UnicodeDecodeError:
            continue
        if not any("\u3040" <= c <= "\u9fff" for c in s):
            continue
        off = rodata_start + m.start()
        vaddr = 0x81000000 + (off - 0xE0)

        suffix, base = "", s
        m_suf = re.search(r"\|\s*\d+$", s)
        if m_suf:
            base = s[: m_suf.start()]
            suffix = "|" + m_suf.group(0).lstrip("| ")

        en = delta.get(s) or delta.get(base) or exact.get(s) or exact.get(base) or normalized.get(norm(base))
        if en is None:
            entries.append({"off": off, "vaddr": vaddr, "jp": s, "en": None, "orig_len": len(raw)})
        else:
            if s != base and not en.endswith(suffix):
                en = wrap_english(en, is_dialogue=True) + suffix
            else:
                en = wrap_english(en, is_dialogue=(s != base))
            entries.append({"off": off, "vaddr": vaddr, "jp": s, "en": en, "orig_len": len(raw)})

    # 2. Split into in-place vs overflow
    inplace = []
    overflow_map = {}  # vaddr -> entry
    unmatched = []

    for e in entries:
        if e["en"] is None:
            unmatched.append(e)
            continue
        en_b = e["en"].encode("utf-8")
        if len(en_b) <= e["orig_len"]:
            inplace.append((e, en_b))
        else:
            overflow_map[e["vaddr"]] = (e, en_b)

    # Apply in-place patches
    for e, en_b in inplace:
        off = e["off"]
        orig_len = e["orig_len"]
        elf[off : off + orig_len] = en_b + b"\x00" * (orig_len - len(en_b))

    # Widen both real dialogue boxes: r2 (max_chars) 31 -> 58 (0x3a), r3 (max_lines) 3 -> 4, [sp] (font_size) 40 -> 25 (0x19)
    box_patches = [
        (0x0546D2, 0x221F, 0x223A, 0x0546D4, 0x2303, 0x2304, 0x0546B6, 0x2328, 0x2319),  # 0x810545f2 / f4 / d6
        (0x071032, 0x221F, 0x223A, 0x071034, 0x2303, 0x2304, 0x071026, 0x2728, 0x2719),  # 0x81070f52 / 54 / 46
        # Command List right-hand explanation box (Start Menu & Skill Setup): r2 15->25 (0x19), r3 14->18 (0x12), font 24->19 (0x13)
        (0x06C1C2, 0x220F, 0x2219, 0x06C1C6, 0x230E, 0x2312, 0x06C1B0, 0x2018, 0x2013),
        (0x09904C, 0x220F, 0x2219, 0x099050, 0x230E, 0x2312, 0x099032, 0x2018, 0x2013),
    ]
    for off_w, exp_w, new_w, off_l, exp_l, new_l, off_f, exp_f, new_f in box_patches:
        assert struct.unpack_from("<H", elf, off_w)[0] == exp_w, f"Unexpected wrap insn at 0x{off_w:x}"
        assert struct.unpack_from("<H", elf, off_l)[0] == exp_l, f"Unexpected lines insn at 0x{off_l:x}"
        assert struct.unpack_from("<H", elf, off_f)[0] == exp_f, f"Unexpected font insn at 0x{off_f:x}"
        struct.pack_into("<H", elf, off_w, new_w)
        struct.pack_into("<H", elf, off_l, new_l)
        struct.pack_into("<H", elf, off_f, new_f)

    # Widen single-row list menus (r2 max_chars only, keeping vertical row height unchanged so cursor aligns!)
    list_wrap_patches = [
        (0x0632BE, 0x220A, 0x2214),  # How to Play left categories: 10 -> 20
        (0x06338E, 0x2218, 0x2232),  # How to Play right topics: 24 -> 50
        (0x063456, 0x2218, 0x2232),  # How to Play topic header: 24 -> 50
        (0x06BEBA, 0x220A, 0x2216),  # Command List (Menu) left col: 10 -> 22
        (0x06BF82, 0x220A, 0x2216),  # Command List (Menu) mid col: 10 -> 22
        (0x06C042, 0x220A, 0x2216),  # Command List (Menu) title: 10 -> 22
        (0x06C106, 0x220A, 0x2212),  # Command List (Menu) reqs: 10 -> 18
        (0x098D44, 0x220A, 0x2216),  # Command List (Setup) left col: 10 -> 22
        (0x098E0C, 0x220A, 0x2216),  # Command List (Setup) mid col: 10 -> 22
        (0x098ECC, 0x220A, 0x2216),  # Command List (Setup) title: 10 -> 22
        (0x098F90, 0x220A, 0x2212),  # Command List (Setup) reqs: 10 -> 18
        (0x071F16, 0x220A, 0x2216),  # In-debate Speak menu: 10 -> 22
    ]
    for off_w, exp_w, new_w in list_wrap_patches:
        assert struct.unpack_from("<H", elf, off_w)[0] == exp_w, f"Unexpected list wrap at 0x{off_w:x}"
        struct.pack_into("<H", elf, off_w, new_w)

    # 3. Find all references to overflowing vaddrs
    overflow_vaddrs = set(overflow_map.keys())
    mov_refs = {v: [] for v in overflow_vaddrs}  # vaddr -> [(off_w, rw, off_t, rt)]
    u32_refs = {v: [] for v in overflow_vaddrs}  # vaddr -> [off]

    # Scan .text for Thumb-2 MOVW + (optional MOV) + MOVT
    text_end = 0x759000
    for off in range(0xE0, text_end - 4, 2):
        hw1, hw2 = struct.unpack_from("<HH", elf, off)
        mw = decode_movw(hw1, hw2)
        if mw is None:
            continue
        rs, lo16 = mw
        aliases = {rs: off}  # reg -> movw_off
        for d in range(4, 36, 2):
            if off + d + 4 > text_end:
                break
            h3, h4 = struct.unpack_from("<HH", elf, off + d)
            mt = decode_movt(h3, h4)
            if mt is not None:
                rt, hi16 = mt
                if rt in aliases:
                    val = (hi16 << 16) | lo16
                    if val in overflow_vaddrs:
                        mov_refs[val].append((aliases[rt], rs, off + d, rt))
                    del aliases[rt]
                    if not aliases:
                        break
                continue
            # Check 16-bit MOVS rd, rm (0x1C00..0x1C3F) or MOV rd, rm (0x4600..0x46FF)
            if (h3 & 0xFFC0) == 0x1C00:
                rd, rm = h3 & 7, (h3 >> 3) & 7
                if rm in aliases:
                    aliases[rd] = off
                elif rd in aliases:
                    del aliases[rd]
            elif (h3 & 0xFF00) == 0x4600:
                rd = ((h3 >> 4) & 8) | (h3 & 7)
                rm = (h3 >> 3) & 0xF
                if rm in aliases:
                    aliases[rd] = off
                elif rd in aliases:
                    del aliases[rd]

    # Scan .rodata and .data for 32-bit pointers
    for start, end in [(0x759000, 0x87B39B), (0x87B3C0, 0xAE3088)]:
        for off in range(start, end - 4, 4):
            val = struct.unpack_from("<I", elf, off)[0]
            if val in overflow_vaddrs:
                u32_refs[val].append(off)

    # 4. Build extra .rodata block appended to PHDR 1 (after .bss)
    p1_type, p1_off, p1_vaddr, p1_paddr, p1_filesz, p1_memsz, p1_flags, p1_align = struct.unpack_from(
        "<8I", elf, 0x34 + 1 * 32
    )
    bss_pad_len = p1_memsz - p1_filesz
    # Align new string block to 16 bytes
    base_new_vaddr = (p1_vaddr + p1_memsz + 15) & ~15
    pre_align = base_new_vaddr - (p1_vaddr + p1_memsz)

    extra_block = bytearray(bss_pad_len + pre_align)
    repointed_count = 0
    unrepointed = []
    addend_map = {}

    for vaddr, (e, en_b) in overflow_map.items():
        has_ref = bool(mov_refs[vaddr] or u32_refs[vaddr])
        if not has_ref:
            unrepointed.append({"vaddr": hex(vaddr), "jp": e["jp"], "en": e["en"], "orig_len": e["orig_len"]})
            continue
        new_vaddr = base_new_vaddr + (len(extra_block) - bss_pad_len - pre_align)
        addend_map[vaddr - 0x81000000] = new_vaddr - 0x81000000
        extra_block.extend(en_b + b"\x00")
        # Align each string to 4 bytes
        while len(extra_block) % 4 != 0:
            extra_block.append(0)

        new_lo = new_vaddr & 0xFFFF
        new_hi = (new_vaddr >> 16) & 0xFFFF

        for off_w, rs, off_t, rt in mov_refs[vaddr]:
            w1, w2 = encode_movw(rs, new_lo)
            t1, t2 = encode_movt(rt, new_hi)
            struct.pack_into("<HH", elf, off_w, w1, w2)
            struct.pack_into("<HH", elf, off_t, t1, t2)

        for off_u in u32_refs[vaddr]:
            struct.pack_into("<I", elf, off_u, new_vaddr)

        repointed_count += 1

    # Update PT_SCE_RELA (PHDR 2) addends properly (fmt=0 is 12 bytes, fmt=1 is 8 bytes)
    p2_off = struct.unpack_from("<I", elf, 0x34 + 2 * 32 + 4)[0]
    p2_filesz = struct.unpack_from("<I", elf, 0x34 + 2 * 32 + 16)[0]
    rela_updated = 0
    rpos = p2_off
    r_end = p2_off + p2_filesz
    while rpos < r_end:
        w0 = struct.unpack_from("<I", elf, rpos)[0]
        fmt = w0 & 0xF
        if fmt == 0:
            r_addend = struct.unpack_from("<I", elf, rpos + 4)[0]
            if r_addend in addend_map:
                struct.pack_into("<I", elf, rpos + 4, addend_map[r_addend])
                rela_updated += 1
            rpos += 12
        elif fmt == 1:
            rpos += 8
        else:
            raise ValueError(f"Unknown RELA fmt={fmt} at 0x{rpos:x}")
    print(f"Updated PT_SCE_RELA entries: {rela_updated}")

    # Splice extra_block at end of PHDR 1 (p1_off + p1_filesz)
    insert_pos = p1_off + p1_filesz
    delta = len(extra_block)
    new_elf = bytearray(elf[:insert_pos]) + extra_block + bytearray(elf[insert_pos:])

    # Update PHDR 1 filesz & memsz
    new_p1_filesz = p1_filesz + delta
    new_p1_memsz = new_p1_filesz
    struct.pack_into("<II", new_elf, 0x34 + 1 * 32 + 16, new_p1_filesz, new_p1_memsz)

    # Shift PHDR 2, 3, 4 offsets
    for i in (2, 3, 4):
        old_off = struct.unpack_from("<I", new_elf, 0x34 + i * 32 + 4)[0]
        struct.pack_into("<I", new_elf, 0x34 + i * 32 + 4, old_off + delta)

    with open(OUT_ELF, "wb") as f:
        f.write(new_elf)

    with open(VITA3K_ORIG, "rb") as f:
        orig_self = f.read()

    fself_size = build_fself(orig_self, new_elf, VITA3K_EBOOT)

    report = {
        "total_rodata_jp": len(entries),
        "inplace_patched": len(inplace),
        "overflow_total": len(overflow_map),
        "repointed": repointed_count,
        "unrepointed_count": len(unrepointed),
        "unmatched_count": len(unmatched),
        "unrepointed_samples": unrepointed[:50],
        "unmatched": [{"vaddr": hex(x["vaddr"]), "jp": x["jp"], "orig_len": x["orig_len"]} for x in unmatched],
    }
    with open(OUT_REPORT, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"Total .rodata JP strings: {len(entries)}")
    print(f"  Patched in-place:  {len(inplace)}")
    print(f"  Repointed (ext):   {repointed_count}")
    print(f"  Unrepointed (skip):{len(unrepointed)}")
    print(f"  Unmatched (JP):    {len(unmatched)}")
    print(f"Extra block size:    {delta} bytes (new PHDR1 vaddr end: 0x{p1_vaddr + new_p1_memsz:x})")
    print(f"Wrote FSELF ({fself_size} bytes) -> {VITA3K_EBOOT}")


if __name__ == "__main__":
    main()
