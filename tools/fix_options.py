import os
from PIL import Image

VITA_OPT = r"c:\Users\Nikola\Desktop\AI PROJECTS\Gnosia\extracted_vita_psarc\image\menu_option.png"
PC_OPT = r"c:\Users\Nikola\Desktop\AI PROJECTS\Gnosia\pc_ui_raw\menu_option.png"
OUT_OPT = r"c:\Users\Nikola\Desktop\AI PROJECTS\Gnosia\patched_ui_safe\menu_option.png"


def copy_prop(dst_im, dst_pbox, src_im, src_pbox):
    vw, vh = dst_im.size
    pw, ph = src_im.size
    db = (int(vw * dst_pbox[0]), int(vh * dst_pbox[1]), int(vw * dst_pbox[2]), int(vh * dst_pbox[3]))
    sb = (int(pw * src_pbox[0]), int(ph * src_pbox[1]), int(pw * src_pbox[2]), int(ph * src_pbox[3]))
    crop = src_im.crop(sb).resize((db[2] - db[0], db[3] - db[1]), Image.Resampling.LANCZOS)
    dst_im.paste(crop, (db[0], db[1]))


def main():
    vita = Image.open(VITA_OPT).convert("RGBA")
    pc = Image.open(PC_OPT).convert("RGBA")

    # 1. Left half (Options badge + Volume/BGM/SFX/Message Speed) aligns 1:1
    copy_prop(vita, (0.0, 0.0, 0.555, 1.0), pc, (0.0, 0.0, 0.555, 1.0))
    # 2. Top-right: Prevent Skipping + During Events (aligned to Vita's slightly lower y)
    copy_prop(vita, (0.575, 0.21, 0.955, 0.44), pc, (0.575, 0.13, 0.955, 0.36))
    # 3. During Debate label (over Vita's 議論時 above the second ON/OFF row)
    copy_prop(vita, (0.615, 0.57, 0.80, 0.64), pc, (0.595, 0.43, 0.79, 0.50))

    os.makedirs(os.path.dirname(OUT_OPT), exist_ok=True)
    vita.save(OUT_OPT, "PNG")
    print(f"Composited clean menu_option.png -> {OUT_OPT}")


if __name__ == "__main__":
    main()
