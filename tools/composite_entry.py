import os
from PIL import Image

VITA_ENTRY = r"c:\Users\Nikola\Desktop\AI PROJECTS\Gnosia\extracted_vita_psarc\image\entry.png"
PC_ENTRY = r"c:\Users\Nikola\Desktop\AI PROJECTS\Gnosia\pc_ui_raw\entry_GP.png"
OUT_ENTRY = r"c:\Users\Nikola\Desktop\AI PROJECTS\Gnosia\patched_ui_safe\entry.png"


def tight_box(im, box):
    sub = im.crop(box)
    b = sub.getbbox()
    if not b:
        return box
    return (box[0] + b[0], box[1] + b[1], box[0] + b[2], box[1] + b[3])


def copy_region(dst_im, dst_box, src_im, src_box):
    src_crop = src_im.crop(src_box)
    sb = src_crop.getbbox()
    if sb:
        src_crop = src_crop.crop(sb)
    dw = dst_box[2] - dst_box[0]
    dh = dst_box[3] - dst_box[1]
    resized = src_crop.resize((dw, dh), Image.Resampling.LANCZOS)
    dst_im.paste((0, 0, 0, 0), dst_box)
    dst_im.paste(resized, (dst_box[0], dst_box[1]))


def main():
    vita = Image.open(VITA_ENTRY).convert("RGBA")
    pc = Image.open(PC_ENTRY).convert("RGBA")
    vw, vh = vita.size
    pw, ph = pc.size

    # Map each panel by proportional bounding boxes
    panels = [
        # Main left panel (Player Data, Name, Sex, Abilities, Points, Color)
        ((0, 0, int(vw * 0.612), int(vh * 0.550)), (0, 0, int(pw * 0.625), int(ph * 0.515))),
        # Top-right: "Once you've input..."
        ((int(vw * 0.612), 0, int(vw * 0.870), int(vh * 0.190)), (int(pw * 0.625), 0, int(pw * 0.885), int(ph * 0.175))),
        # Mid-right: "Select your gender:"
        ((int(vw * 0.625), int(vh * 0.240), int(vw * 0.895), int(vh * 0.390)), (int(pw * 0.640), int(ph * 0.230), int(pw * 0.910), int(ph * 0.370))),
        # Bottom-left: "Select your favorite color:"
        ((int(vw * 0.160), int(vh * 0.550), int(vw * 0.430), int(vh * 0.960)), (int(pw * 0.165), int(ph * 0.520), int(pw * 0.440), int(ph * 0.910))),
        # Bottom-mid: "Assign points..."
        ((int(vw * 0.440), int(vh * 0.550), int(vw * 0.708), int(vh * 0.980)), (int(pw * 0.450), int(ph * 0.520), int(pw * 0.720), int(ph * 0.930))),
        # Bottom-right top: "Please input your Name..."
        ((int(vw * 0.710), int(vh * 0.550), int(vw * 0.965), int(vh * 0.740)), (int(pw * 0.722), int(ph * 0.520), int(pw * 0.985), int(ph * 0.700))),
        # Bottom-right: "Start" button
        ((int(vw * 0.832), int(vh * 0.835), int(vw * 0.935), int(vh * 0.925)), (int(pw * 0.855), int(ph * 0.790), int(pw * 0.950), int(ph * 0.875))),
    ]

    for vb, pb in panels:
        copy_region(vita, tight_box(vita, vb), pc, tight_box(pc, pb))

    os.makedirs(os.path.dirname(OUT_ENTRY), exist_ok=True)
    vita.save(OUT_ENTRY, "PNG")
    print(f"Composited English entry.png -> {OUT_ENTRY}")


if __name__ == "__main__":
    main()
