import os
import random
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

games = {}

COLORS = [
    (220, 50, 50),
    (50, 100, 220),
    (50, 180, 80),
    (240, 190, 40)
]

def font(size):
    try:
        return ImageFont.truetype("DejaVuSans-Bold.ttf", size)
    except:
        return ImageFont.load_default()

def make_board(game):
    img = Image.new("RGB", (900, 900), (245, 235, 220))
    d = ImageDraw.Draw(img)

    d.text((450, 40), "DESMADRE PARCHÍS",
           fill=(50, 30, 20), font=font(40), anchor="mm")
    d.text((450, 85), "🎲 TABLERO 🎲",
           fill=(90, 50, 30), font=font(25), anchor="mm")

    x0, y0 = 70, 120
    cell = 45

    spots = []
    for row in range(4):
        cols = range(17) if row % 2 == 0 else range(16, -1, -1)
        for col in cols:
            spots.append((col, row))

    for row in range(4, 8):
        cols = range(17) if row % 2 == 0 else range(16, -1, -1)
        for col in cols:
            spots.append((col, row))

    for row in range(8, 12):
        cols = range(17) if row % 2 == 0 else range(16, -1, -1)
        for col in cols:
            spots.append((col, row))

    for row in range(12, 16):
        cols = range(17) if row % 2 == 0 else range(16, -1, -1)
        for col in cols:
            spots.append((col, row))

    for number, (col, row) in enumerate(spots[:68], 1):
        x = x0 + col * cell
        y = y0 + row * cell

        d.rectangle(
            (x, y, x + cell, y + cell),
            fill=(255, 255, 255),
            outline=(120, 100, 90),
            width=2
        )

        d.text(
            (x + cell // 2, y + cell // 2),
            str(number),
            fill=(70, 60, 50),
            font=font(14),
            anchor="mm"
        )

    for i, uid in enumerate(game["players"]):
        pos = game["positions"][uid]

        if 1 <= pos <= 68:
            col, row = spots[pos - 1]
            cx = x0 + col * cell + cell // 2
            cy = y0 + row * cell + cell // 2

            d.ellipse(
                (cx - 16, cy - 16, cx + 16, cy + 16),
                fill=COLORS[i],
                outline=(30, 30, 30),
                width=3
            )

    d.rounded_rectangle(
        (250, 850, 650, 890),
        radius=15,
        fill=(255, 215, 70),
        outline=(80, 60, 20),
        width=3
    )

    d.text(
        (450, 870),
        "🏁 META — 68",
        fill=(50, 40, 20),
        font=font(22),
        anchor="mm"
    )

    return img
