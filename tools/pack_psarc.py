import hashlib
import os
import shutil
import struct
import zlib

VITA3K_PSARC = r"C:\Users\Nikola\AppData\Roaming\Vita3K\Vita3K\ux0\app\PCSG01277\game_data\game_data.psarc"
VITA3K_PSARC_ORIG = VITA3K_PSARC + ".orig"
EXTRACTED_DIR = r"c:\Users\Nikola\Desktop\AI PROJECTS\Gnosia\extracted_vita_psarc"
SAFE_UI_DIR = r"c:\Users\Nikola\Desktop\AI PROJECTS\Gnosia\patched_ui_safe"

BLOCK_SIZE = 65536


def read_orig_manifest(psarc_path):
    with open(psarc_path, "rb") as f:
        hdr = f.read(32)
        magic, v1, v2, comp, toc_len, toc_es, num_entries, block_size, flags = struct.unpack(
            ">4sHH4sIIIII", hdr
        )
        toc_raw = f.read(toc_len - 32)
        e0 = toc_raw[:toc_es]
        usz = int.from_bytes(e0[20:25], "big")
        off = int.from_bytes(e0[25:30], "big")
        bsizes_raw = toc_raw[num_entries * toc_es :]
        bsizes = struct.unpack(">" + "H" * (len(bsizes_raw) // 2), bsizes_raw)
        f.seek(off)
        out = bytearray()
        zi = 0
        while len(out) < usz:
            bz = bsizes[zi]
            chunk = f.read(block_size if bz == 0 else bz)
            try:
                out.extend(zlib.decompress(chunk))
            except zlib.error:
                out.extend(chunk)
            zi += 1
        return bytes(out[:usz]).decode("utf-8").splitlines()


def pack_psarc(manifest, base_dir, override_img_dir, out_path):
    all_blobs = ["\n".join(manifest).encode("utf-8")]
    md5s = [b"\x00" * 16]
    replaced = 0

    for rel in manifest:
        clean = rel.lstrip("/")
        ov = None
        if clean.startswith("image/"):
            cand = os.path.join(override_img_dir, clean[len("image/") :])
            if os.path.exists(cand):
                ov = cand
        src = ov if ov else os.path.join(base_dir, clean)
        if ov:
            replaced += 1
        with open(src, "rb") as f:
            data = f.read()
        all_blobs.append(data)
        md5s.append(hashlib.md5(rel.encode("utf-8")).digest())

    num_entries = len(all_blobs)
    toc_entry_size = 30
    block_sizes = []
    compressed_chunks = []
    entry_meta = []

    for i, blob in enumerate(all_blobs):
        zidx = len(block_sizes)
        usz = len(blob)
        entry_meta.append([md5s[i], zidx, usz, 0])
        for pos in range(0, usz, BLOCK_SIZE):
            raw_blk = blob[pos : pos + BLOCK_SIZE]
            comp_blk = zlib.compress(raw_blk, 6)
            if len(comp_blk) < len(raw_blk):
                compressed_chunks.append(comp_blk)
                block_sizes.append(len(comp_blk))
            else:
                compressed_chunks.append(raw_blk)
                block_sizes.append(0 if len(raw_blk) == BLOCK_SIZE else len(raw_blk))

    toc_len = 32 + num_entries * toc_entry_size + len(block_sizes) * 2
    cur_off = toc_len
    blk_cursor = 0
    for i in range(num_entries):
        entry_meta[i][3] = cur_off
        usz = entry_meta[i][2]
        nblocks = (usz + BLOCK_SIZE - 1) // BLOCK_SIZE if usz > 0 else 0
        for _ in range(nblocks):
            cur_off += len(compressed_chunks[blk_cursor])
            blk_cursor += 1

    with open(out_path, "wb") as f:
        f.write(struct.pack(">4sHH4sIIIII", b"PSAR", 1, 4, b"zlib", toc_len, toc_entry_size, num_entries, BLOCK_SIZE, 0))
        for md5, zidx, usz, off in entry_meta:
            f.write(md5)
            f.write(struct.pack(">I", zidx))
            f.write(usz.to_bytes(5, "big"))
            f.write(off.to_bytes(5, "big"))
        for bz in block_sizes:
            f.write(struct.pack(">H", bz))
        for chunk in compressed_chunks:
            f.write(chunk)

    print(f"Packed {num_entries - 1} files ({replaced} UI PNGs replaced) -> {out_path}")


def main():
    if not os.path.exists(VITA3K_PSARC_ORIG):
        shutil.copy2(VITA3K_PSARC, VITA3K_PSARC_ORIG)
        print(f"Backed up original PSARC -> {VITA3K_PSARC_ORIG}")
    manifest = read_orig_manifest(VITA3K_PSARC_ORIG)
    pack_psarc(manifest, EXTRACTED_DIR, SAFE_UI_DIR, VITA3K_PSARC)


if __name__ == "__main__":
    main()
