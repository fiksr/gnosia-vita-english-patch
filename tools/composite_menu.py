import os
from PIL import Image

VITA_MENU = r"c:\Users\Nikola\Desktop\AI PROJECTS\Gnosia\extracted_vita_psarc\image\menu.png"
PC_MENU = r"c:\Users\Nikola\Desktop\AI PROJECTS\Gnosia\pc_ui_raw\menu.png"
OUT_MENU = r"c:\Users\Nikola\Desktop\AI PROJECTS\Gnosia\patched_ui_safe\menu.png"


def copy_region(dst_im, dst_box, src_im, src_box):
    # Trim transparent borders on src_box, resize to exact dst_box size, and paste over cleared dst_box
    src_crop = src_im.crop(src_box)
    sb = src_crop.getbbox()
    if sb:
        src_crop = src_crop.crop(sb)
    dw = dst_box[2] - dst_box[0]
    dh = dst_box[3] - dst_box[1]
    resized = src_crop.resize((dw, dh), Image.Resampling.LANCZOS)
    # Clear destination box first
    dst_im.paste((0, 0, 0, 0), dst_box)
    dst_im.paste(resized, (dst_box[0], dst_box[1]))


def tight_box(im, box):
    sub = im.crop(box)
    b = sub.getbbox()
    if not b:
        return box
    return (box[0] + b[0], box[1] + b[1], box[0] + b[2], box[1] + b[3])


def main():
    vita = Image.open(VITA_MENU).convert("RGBA")
    pc = Image.open(PC_MENU).convert("RGBA")

    # 1. Status badge (top-left)
    copy_region(vita, tight_box(vita, (25, 25, 210, 90)), pc, tight_box(pc, (25, 25, 290, 115)))

    # 2. Stat block (Charisma..Stealth)
    copy_region(vita, tight_box(vita, (0, 520, 415, 780)), pc, tight_box(pc, (1055, 45, 1615, 405)))

    # 3. Buttons: (vita_search_box, pc_search_box)
    mappings = [
        # Left col
        ((0, 790, 225, 858), (600, 648, 902, 738)),      # Return To Title (yellow)
        ((0, 858, 225, 925), (0, 738, 300, 826)),        # How To Play (grey)
        ((0, 925, 225, 992), (300, 648, 600, 738)),      # Return To Title (grey)
        # Mid col
        ((415, 580, 642, 648), (600, 738, 902, 826)),    # Load (grey)
        ((415, 648, 642, 715), (1058, 520, 1362, 609)),  # Command List (yellow)
        ((415, 715, 642, 782), (1058, 609, 1362, 696)),  # Command List (grey)
        ((415, 782, 642, 849), (0, 648, 300, 738)),      # Load (yellow)
        ((415, 849, 642, 916), (300, 738, 600, 826)),    # How To Play (yellow)
        ((415, 916, 642, 984), (1362, 696, 1665, 783)),  # Options (yellow)
        # Right col
        ((642, 580, 870, 648), (1362, 520, 1665, 609)),  # Options (grey)
        ((642, 848, 870, 916), (1058, 696, 1362, 783)),  # Return To Setup (yellow)
        ((642, 916, 870, 984), (1362, 609, 1665, 696)),  # Return To Setup (grey)
    ]

    for vb, pb in mappings:
        copy_region(vita, tight_box(vita, vb), pc, tight_box(pc, pb))

    os.makedirs(os.path.dirname(OUT_MENU), exist_ok=True)
    vita.save(OUT_MENU, "PNG")
    print(f"Composited English menu.png -> {OUT_MENU}")


if __name__ == "__main__":
    main()
