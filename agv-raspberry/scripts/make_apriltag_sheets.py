import os
import time
import cv2 as cv
import numpy as np
from PIL import Image, ImageDraw, ImageFont


def mm2px(mm: float, dpi: int) -> int:
    return int(round(mm / 25.4 * dpi))


def ensure_dict():
    if not hasattr(cv, "aruco"):
        raise RuntimeError("cv2.aruco não encontrado. Instale opencv-contrib-python.")
    a = cv.aruco
    if not hasattr(a, "DICT_APRILTAG_36h11"):
        raise RuntimeError("DICT_APRILTAG_36h11 ausente. Atualize opencv-contrib-python (>=4.7).")
    return a.getPredefinedDictionary(a.DICT_APRILTAG_36h11)


def main():
    # Config página A4 (retrato), 300 DPI
    DPI = 300
    A4_W_MM, A4_H_MM = 210.0, 297.0
    A4_W_PX, A4_H_PX = mm2px(A4_W_MM, DPI), mm2px(A4_H_MM, DPI)

    # Grid 4x4 = 16 tags, cada tag 30 mm, com borda branca
    GRID_ROWS, GRID_COLS = 4, 4
    TAG_SIZE_MM = 30.0
    WHITE_BORDER_MM = 4.0
    MARGIN_MM = 10.0
    GUTTER_MM = 6.0
    LABEL_MM = 5.0

    margin_px = mm2px(MARGIN_MM, DPI)
    gutter_px = mm2px(GUTTER_MM, DPI)
    tag_px = mm2px(TAG_SIZE_MM, DPI)
    border_px = mm2px(WHITE_BORDER_MM, DPI)
    label_px = mm2px(LABEL_MM, DPI)

    cell_w = tag_px + 2 * border_px
    cell_h = tag_px + 2 * border_px + label_px
    total_w = GRID_COLS * cell_w + (GRID_COLS - 1) * gutter_px
    total_h = GRID_ROWS * cell_h + (GRID_ROWS - 1) * gutter_px

    if total_w + 2 * margin_px > A4_W_PX or total_h + 2 * margin_px > A4_H_PX:
        raise RuntimeError("Grid não cabe na A4. Reduza TAG_SIZE_MM/margens/gutters.")

    # Canvas A4
    canvas = Image.new("L", (A4_W_PX, A4_H_PX), 255)
    draw = ImageDraw.Draw(canvas)
    try:
        font = ImageFont.truetype("arial.ttf", size=mm2px(3.5, DPI))
    except Exception:
        font = ImageFont.load_default()

    x_origin = (A4_W_PX - total_w) // 2
    y_origin = (A4_H_PX - total_h) // 2

    dictionary = ensure_dict()

    # Pastas de saída
    base_dir = os.path.dirname(os.path.dirname(__file__))
    out_dir = os.path.join(base_dir, "printables")
    tags_dir = os.path.join(out_dir, "tags")
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(tags_dir, exist_ok=True)

    # IDs 0..15
    ids = list(range(GRID_ROWS * GRID_COLS))
    for idx, tag_id in enumerate(ids):
        r, c = divmod(idx, GRID_COLS)
        x0 = x_origin + c * (cell_w + gutter_px)
        y0 = y_origin + r * (cell_h + gutter_px)

        marker = cv.aruco.generateImageMarker(dictionary, tag_id, tag_px)

        # Celula com borda branca e área de label
        cell_img = Image.new("L", (cell_w, cell_h), 255)
        cell_img.paste(Image.fromarray(marker), (border_px, border_px))

        # Label centrado
        label = f"id {tag_id}"
        try:
            # Pillow >= 8: use textbbox for precise measurement
            bbox = draw.textbbox((0, 0), label, font=font)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        except Exception:
            # Fallback for older Pillow
            tw, th = font.getsize(label)
        lx = x0 + (cell_w - tw) // 2
        ly = y0 + tag_px + 2 * border_px + (label_px - th) // 2
        draw.text((lx, ly), label, font=font, fill=0)

        # Cola célula no canvas
        canvas.paste(cell_img, (x0, y0))

        # Salvar PNG individual (tag + borda)
        indiv = Image.new("L", (cell_w, cell_h - label_px), 255)
        indiv.paste(Image.fromarray(marker), (border_px, border_px))
        indiv_path = os.path.join(tags_dir, f"apriltag_36h11_id{tag_id}_{int(TAG_SIZE_MM)}mm.png")
        indiv.save(indiv_path)

    sheet_path = os.path.join(out_dir, f"apriltags_36h11_A4_{GRID_ROWS}x{GRID_COLS}_{int(TAG_SIZE_MM)}mm_{DPI}dpi.png")
    canvas.save(sheet_path)
    print(f"Saved sheet: {sheet_path}")
    print(f"Saved individual tags in: {tags_dir}")
    print("Imprima em 100% (sem ajustar à página), papel fosco.")


if __name__ == "__main__":
    main()
