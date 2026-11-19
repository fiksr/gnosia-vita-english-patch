"""Composite English paramChange.png (My Room LV-Up UI) and setup.png (Setup & Role Descriptions) for Gnosia Vita v0.3."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(r"C:\Users\Nikola\Desktop\AI PROJECTS\Gnosia")
VITA_DIR = ROOT / "extracted_vita_psarc" / "image"
PC_DIR = ROOT / "pc_ui_raw"
OUT_DIR = ROOT / "patched_ui_safe"


def copy_region(dst_im: Image.Image, dst_box: tuple[int, int, int, int], src_im: Image.Image, src_box: tuple[int, int, int, int]) -> None:
    src_crop = src_im.crop(src_box)
    sb = src_crop.getbbox()
    if sb:
        src_crop = src_crop.crop(sb)
    dw = dst_box[2] - dst_box[0]
    dh = dst_box[3] - dst_box[1]
    resized = src_crop.resize((dw, dh), Image.Resampling.LANCZOS)
    dst_im.paste((0, 0, 0, 0), dst_box)
    dst_im.paste(resized, (dst_box[0], dst_box[1]))


def build_param_change() -> None:
    vita = Image.open(VITA_DIR / "paramChange.png").convert("RGBA")
    pc = Image.open(PC_DIR / "paramChange_GP.png").convert("RGBA")

    # 1. Main Status / Abilities panel
    copy_region(vita, (0, 0, 797, 489), pc, (1, 0, 1061, 649))
    # 2. Six stacked stat description blocks (Charisma..Stealth)
    copy_region(vita, (0, 490, 325, 914), pc, (1063, 4, 1495, 555))
    # 3. 'Change Abilities' teal header
    copy_region(vita, (325, 538, 552, 605), pc, (1490, 0, 1799, 86))
    # 4. 'Command List' grey button
    copy_region(vita, (328, 610, 445, 700), pc, (1500, 90, 1655, 205))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / "paramChange.png"
    vita.save(out_path, "PNG")
    print(f"Saved {out_path}")


def draw_rich_lines(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    lines: list[list[tuple[str, tuple[int, int, int, int]]]],
    font: ImageFont.FreeTypeFont,
    line_h: int,
) -> None:
    x0, y0, _, _ = box
    y = y0
    for segs in lines:
        x = x0
        for txt, col in segs:
            draw.text((x, y), txt, font=font, fill=col)
            bbox = draw.textbbox((x, y), txt, font=font)
            x = bbox[2]
        y += line_h


def build_setup() -> None:
    vita = Image.open(VITA_DIR / "setup.png").convert("RGBA")
    draw = ImageDraw.Draw(vita)

    font_path = Path(r"C:\Windows\Fonts\segoeui.ttf")
    font_bold = Path(r"C:\Windows\Fonts\segoeuib.ttf")
    f_body = ImageFont.truetype(str(font_path), 17)
    f_btn = ImageFont.truetype(str(font_bold), 18)
    f_hdr = ImageFont.truetype(str(font_bold), 22)

    DARK = (38, 42, 48, 255)
    ORANGE = (232, 128, 12, 255)
    WHITE = (245, 248, 250, 255)

    # Clear the 7 Japanese role description boxes (transparent background)
    desc_boxes = {
        "bug": (544, 248, 845, 464),
        "gnosia": (544, 464, 845, 634),
        "angel": (544, 634, 845, 725),
        "ac": (0, 495, 264, 645),
        "guard": (264, 495, 540, 610),
        "eng": (264, 610, 540, 695),
        "doc": (264, 695, 540, 790),
    }
    for box in desc_boxes.values():
        vita.paste((0, 0, 0, 0), box)

    draw = ImageDraw.Draw(vita)

    draw_rich_lines(draw, desc_boxes["bug"], [
        [("The ", DARK), ("Bug", ORANGE), (" is an enemy to both", DARK)],
        [("Humans and Gnosia.", DARK)],
        [("Cannot be eliminated at night,", DARK)],
        [("but disappears if investigated", DARK)],
        [("by the Engineer.", DARK)],
        [("Can claim to be a fake", DARK)],
        [("Engineer", ORANGE), (" or ", DARK), ("Doctor", ORANGE), (".", DARK)],
    ], f_body, 22)

    draw_rich_lines(draw, desc_boxes["gnosia"], [
        [("Gnosia", ORANGE), (" are enemies of Humans.", DARK)],
        [("Each warp, they choose one", DARK)],
        [("person to eliminate.", DARK)],
        [("They can also claim to be a", DARK)],
        [("fake ", DARK), ("Engineer", ORANGE), (" or ", DARK), ("Doctor", ORANGE), (".", DARK)],
    ], f_body, 22)

    draw_rich_lines(draw, desc_boxes["angel"], [
        [("The ", DARK), ("Guardian Angel", ORANGE), (" can choose", DARK)],
        [("one person each warp to", DARK)],
        [("protect from the Gnosia.", DARK)],
    ], f_body, 22)

    draw_rich_lines(draw, desc_boxes["ac"], [
        [("AC Follower", ORANGE), (" is human, but", DARK)],
        [("lies to help Gnosia win.", DARK)],
        [("Can claim to be a fake", DARK)],
        [("Engineer", ORANGE), (" or ", DARK), ("Doctor", ORANGE), (".", DARK)],
    ], f_body, 22)

    draw_rich_lines(draw, desc_boxes["guard"], [
        [("Guard Duty", ORANGE), (" are two humans", DARK)],
        [("who can prove each other's", DARK)],
        [("innocence by stepping", DARK)],
        [("forward. No fakes exist.", DARK)],
    ], f_body, 22)

    draw_rich_lines(draw, desc_boxes["eng"], [
        [("The ", DARK), ("Engineer", ORANGE), (" investigates one", DARK)],
        [("person each warp to learn", DARK)],
        [("if they are Gnosia or not.", DARK)],
    ], f_body, 22)

    draw_rich_lines(draw, desc_boxes["doc"], [
        [("The ", DARK), ("Doctor", ORANGE), (" examines the", DARK)],
        [("frozen crewmate to learn if", DARK)],
        [("they were Gnosia or not.", DARK)],
    ], f_body, 22)

    # Clean up the 3 Japanese button/header overlays cleanly inside their polygon interiors:
    # 1. Top-left yellow header '初期条件設定' -> sample clean yellow-green interior band and write 'Loop Setup'
    hdr_strip = vita.crop((14, 52, 28, 98)).resize((176, 48), Image.Resampling.BILINEAR)
    vita.paste(hdr_strip, (30, 52))
    draw.text((40, 62), "Loop Setup", font=f_hdr, fill=(45, 50, 35, 255))

    # 2. Random button ('おまかせ設定') -> solid interior grey over JP text only (preserving △ icon & bevels)
    draw.rectangle((164, 654, 244, 712), fill=(138, 144, 150, 255))
    draw.text((168, 672), "Random", font=f_btn, fill=WHITE)

    # 3. Search button ('イベントサーチ') -> solid interior grey over JP text only (preserving △ icon & bevels)
    draw.rectangle((32, 732, 108, 788), fill=(138, 144, 150, 255))
    draw.text((38, 748), "Search", font=f_btn, fill=WHITE)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / "setup.png"
    vita.save(out_path, "PNG")
    print(f"Saved {out_path}")


if __name__ == "__main__":
    build_param_change()
    build_setup()
