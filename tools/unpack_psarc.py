import hashlib
import os
import struct
import zlib

PSARC_PATH = r"C:\Users\Nikola\AppData\Roaming\Vita3K\Vita3K\ux0\app\PCSG01277\game_data\game_data.psarc"
OUT_DIR = r"c:\Users\Nikola\Desktop\AI PROJECTS\Gnosia\extracted_vita_psarc"


def unpack_psarc(psarc_path, out_dir):
    with open(psarc_path, "rb") as f:
        hdr = f.read(32)
        magic, v1, v2, comp, toc_len, toc_es, num_entries, block_size, flags = struct.unpack(
            ">4sHH4sIIIII", hdr
        )
        assert magic == b"PSAR" and comp == b"zlib", f"Unexpected PSAR: {magic} {comp}"

        toc_raw = f.read(toc_len - 32)
        entries = []
        for i in range(num_entries):
            e = toc_raw[i * toc_es : (i + 1) * toc_es]
            md5 = e[:16]
            zidx = struct.unpack(">I", e[16:20])[0]
            usz = int.from_bytes(e[20:25], "big")
            off = int.from_bytes(e[25:30], "big")
            entries.append((md5, zidx, usz, off))

        bsizes_raw = toc_raw[num_entries * toc_es :]
        bsizes = struct.unpack(">" + "H" * (len(bsizes_raw) // 2), bsizes_raw)

        def read_entry(idx):
            _, zidx, usz, off = entries[idx]
            if usz == 0:
                return b""
            f.seek(off)
            out = bytearray()
            zi = zidx
            while len(out) < usz:
                bz = bsizes[zi]
                comp_size = block_size if bz == 0 else bz
                chunk = f.read(comp_size)
                if bz == 0 or comp_size == min(block_size, usz - len(out)):
                    try:
                        out.extend(zlib.decompress(chunk))
                    except zlib.error:
                        out.extend(chunk)
                else:
                    try:
                        out.extend(zlib.decompress(chunk))
                    except zlib.error:
                        out.extend(chunk)
                zi += 1
            return bytes(out[:usz])

        manifest = read_entry(0).decode("utf-8").splitlines()
        assert len(manifest) == num_entries - 1, f"{len(manifest)} vs {num_entries - 1}"

        os.makedirs(out_dir, exist_ok=True)
        for i, name in enumerate(manifest, start=1):
            clean_name = name.lstrip("/")
            dest = os.path.join(out_dir, clean_name)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            data = read_entry(i)
            with open(dest, "wb") as out_f:
                out_f.write(data)
        print(f"Unpacked {len(manifest)} files -> {out_dir}")


if __name__ == "__main__":
    unpack_psarc(PSARC_PATH, OUT_DIR)
