import os
from PIL import Image

VITA_DIR = r"c:\Users\Nikola\Desktop\AI PROJECTS\Gnosia\extracted_vita_psarc\image"
PC_DIR = r"c:\Users\Nikola\Desktop\AI PROJECTS\Gnosia\pc_ui_raw"
OUT_DIR = r"c:\Users\Nikola\Desktop\AI PROJECTS\Gnosia\patched_ui_safe"


def tight_box(im, box):
    sub = im.crop(box)
    b = sub.getbbox()
    if not b:
        return box
    return (box[0] + b[0], box[1] + b[1], box[0] + b[2], box[1] + b[3])


def copy_region(dst_im, dst_box, src_im, src_box, keep_ps_icon=False):
    src_crop = src_im.crop(src_box)
    sb = src_crop.getbbox()
    if sb:
        src_crop = src_crop.crop(sb)
    dw = dst_box[2] - dst_box[0]
    dh = dst_box[3] - dst_box[1]
    resized = src_crop.resize((dw, dh), Image.Resampling.LANCZOS)

    ps_corner = None
    if keep_ps_icon:
        # Save bottom-left PlayStation icon area (36x34 px) from original Vita button
        ps_box = (dst_box[0], dst_box[3] - 34, dst_box[0] + 36, dst_box[3])
        ps_corner = dst_im.crop(ps_box).copy()

    dst_im.paste((0, 0, 0, 0), dst_box)
    dst_im.paste(resized, (dst_box[0], dst_box[1]))

    if ps_corner is not None:
        # Restore Vita's PS button icon over the bottom-left Xbox icon
        dst_im.paste(ps_corner, (dst_box[0], dst_box[3] - 34), ps_corner)


def do_interface():
    vita = Image.open(os.path.join(VITA_DIR, "interface.png")).convert("RGBA")
    pc = Image.open(os.path.join(PC_DIR, "interface_GP.png")).convert("RGBA")

    buttons = [
        ((936, 0, 1050, 84), (1232, 816, 1384, 926)),      # No
        ((988, 145, 1102, 229), (576, 624, 728, 736)),     # Close (menu)
        ((988, 231, 1102, 315), (1895, 648, 2047, 758)),   # Data
        ((839, 423, 953, 507), (1895, 762, 2047, 872)),    # Menu
        ((955, 423, 1069, 507), (1070, 439, 1222, 551)),   # Select
        ((370, 632, 484, 716), (1707, 798, 1859, 908)),    # Delete
        ((260, 801, 374, 885), (0, 711, 152, 823)),        # Back
        ((376, 801, 490, 885), (576, 851, 728, 961)),      # Select
        ((260, 887, 374, 971), (1895, 536, 2047, 646)),    # Change
        ((376, 887, 490, 971), (971, 191, 1123, 301)),     # Wait & See
        ((777, 724, 891, 808), (1554, 799, 1706, 909)),    # Input
        ((893, 724, 1007, 808), (1895, 421, 2047, 533)),   # Back
        ((1009, 724, 1123, 808), (576, 738, 728, 848)),    # Yes
        ((777, 810, 891, 894), (576, 511, 728, 623)),      # Speak
        ((893, 810, 1007, 894), (1385, 814, 1537, 926)),   # Next
        ((1009, 810, 1123, 894), (0, 825, 152, 935)),      # Close (data)
    ]

    for vb, pb in buttons:
        copy_region(vita, tight_box(vita, vb), pc, tight_box(pc, pb), keep_ps_icon=True)

    vita.save(os.path.join(OUT_DIR, "interface.png"), "PNG")
    print("Composited interface.png (16 buttons)")


def do_vote():
    vita = Image.open(os.path.join(VITA_DIR, "vote.png")).convert("RGBA")
    pc = Image.open(os.path.join(PC_DIR, "vote.png")).convert("RGBA")
    vw, vh = vita.size
    pw, ph = pc.size

    # Banners in vote.png by proportional bands
    # Vita: Skip ~(0.48..0.59, 0.29..0.35), Finished ~(0.00..0.26, 0.74..0.82), Voting... ~(0.27..0.54, 0.74..0.82), Please Vote ~(0.54..0.81, 0.74..0.82)
    # PC:   Skip ~(0.49..0.61, 0.29..0.35), Voting... ~(0.49..0.76, 0.00..0.08), Please Vote ~(0.00..0.27, 0.36..0.44), Finished ~(0.28..0.55, 0.36..0.44)
    banners = [
        ((int(vw * 0.48), int(vh * 0.29), int(vw * 0.595), int(vh * 0.355)),
         (int(pw * 0.488), int(ph * 0.285), int(pw * 0.61), int(ph * 0.35)), True),
        ((0, int(vh * 0.74), int(vw * 0.265), int(vh * 0.82)),
         (int(pw * 0.275), int(ph * 0.36), int(pw * 0.555), int(ph * 0.44)), False),
        ((int(vw * 0.27), int(vh * 0.74), int(vw * 0.54), int(vh * 0.82)),
         (int(pw * 0.49), 0, int(pw * 0.76), int(ph * 0.08)), False),
        ((int(vw * 0.545), int(vh * 0.74), int(vw * 0.815), int(vh * 0.82)),
         (0, int(ph * 0.36), int(pw * 0.275), int(ph * 0.44)), False),
    ]

    for vb, pb, keep_x in banners:
        tb_v = tight_box(vita, vb)
        tb_p = tight_box(pc, pb)
        if keep_x:
            ps_x = vita.crop((tb_v[0], tb_v[1], tb_v[0] + 34, tb_v[3])).copy()
            copy_region(vita, tb_v, pc, tb_p, keep_ps_icon=False)
            vita.paste(ps_x, (tb_v[0], tb_v[1]), ps_x)
        else:
            copy_region(vita, tb_v, pc, tb_p, keep_ps_icon=False)

    vita.save(os.path.join(OUT_DIR, "vote.png"), "PNG")
    print("Composited vote.png (4 banners)")


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    do_interface()
    do_vote()


if __name__ == "__main__":
    main()
