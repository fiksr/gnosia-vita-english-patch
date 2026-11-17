import glob
import os
from PIL import Image
import UnityPy

VITA_DIR = r"c:\Users\Nikola\Desktop\AI PROJECTS\Gnosia\extracted_vita_psarc"
PC_AA = r"C:\Program Files (x86)\Steam\steamapps\common\GNOSIA\Gnosia_Data\StreamingAssets\aa\StandaloneWindows64"
OUT_IMG_DIR = r"c:\Users\Nikola\Desktop\AI PROJECTS\Gnosia\patched_ui_safe"


def main():
    os.makedirs(OUT_IMG_DIR, exist_ok=True)

    # 1. Load PC EN textures
    pc_tex = {}
    for b in sorted(glob.glob(os.path.join(PC_AA, "*_en_*.bundle"))):
        env = UnityPy.load(b)
        for obj in env.objects:
            if obj.type.name == "Texture2D":
                d = obj.read()
                pc_tex[d.m_Name] = d

    # 2. Match against Vita PNGs
    vita_pngs = glob.glob(os.path.join(VITA_DIR, "image", "**", "*.png"), recursive=True)
    matched = []
    unmatched_pc = set(pc_tex.keys())

    for vp in vita_pngs:
        stem = os.path.splitext(os.path.basename(vp))[0]
        if stem in ("cIndex", "vote", "entry") or stem.startswith(("charaIndex", "charaTelling", "title")):
            continue
        cand = None
        for key in (stem, f"{stem}_GP", f"{stem}_KB"):
            if key in pc_tex:
                cand = key
                break
        if cand:
            unmatched_pc.discard(cand)
            unmatched_pc.discard(f"{stem}_KB")
            unmatched_pc.discard(f"{stem}_GP")
            with Image.open(vp) as vim:
                vw, vh = vim.size
            d = pc_tex[cand]
            pw, ph = d.m_Width, d.m_Height
            ar_diff = abs((pw / ph) - (vw / vh)) / (vw / vh)
            matched.append((vp, cand, (vw, vh), (pw, ph), ar_diff))
            if ar_diff <= 0.08:
                rel = os.path.relpath(vp, os.path.join(VITA_DIR, "image"))
                out_p = os.path.join(OUT_IMG_DIR, rel)
                os.makedirs(os.path.dirname(out_p), exist_ok=True)
                im = d.image.resize((vw, vh), Image.Resampling.LANCZOS)
                im.save(out_p, "PNG")

    print(f"Matched & resized {len(matched)} / {len(vita_pngs)} Vita PNGs")
    big_ar = [m for m in matched if m[4] > 0.08]
    print(f"Aspect ratio diff > 8%: {len(big_ar)}")
    for vp, cand, vsz, psz, ar in big_ar[:15]:
        print(f"  {os.path.basename(vp)} ({cand}): Vita={vsz} PC={psz} diff={ar*100:.1f}%")
    print(f"Remaining unmatched PC EN textures ({len(unmatched_pc)}): {sorted(unmatched_pc)[:20]}")


if __name__ == "__main__":
    main()
