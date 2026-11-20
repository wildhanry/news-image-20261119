"""main.py - The World in One Page: Thursday 19 November 2026.

Renders one deterministic 1024x1024 PNG summing up 40 verified world-news
stories of 19 November 2026 (data embedded in stories.json beside this file).
No network, no randomness, no clock: three runs give identical bytes.

Run:  mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
Grader: writes entry.png to /output (or MAKEFUN_OUTPUT_DIR).
"""
import json
import math
import os

from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------- palette
# Own variant for this day: petrol masthead, warm paper, crimson + teal.
PAPER = (250, 246, 236)
INK = (22, 24, 28)
MAST = (11, 47, 58)
MAST_DARK = (7, 34, 43)
GOLD = (206, 154, 36)
CRIMSON = (168, 32, 48)
TEAL = (14, 116, 118)
SLATE = (84, 88, 92)
LIGHT = (238, 231, 214)
SEA = (146, 182, 205)
LAND = (216, 208, 186)
WHITE = (255, 255, 255)
GREEN = (46, 110, 66)
ORANGE = (196, 94, 20)

REGION_COLORS = {
    "Americas": (96, 64, 140), "Europe": MAST, "Middle East": CRIMSON,
    "Asia": ORANGE, "Africa": GREEN, "Oceania": TEAL, "Global": SLATE,
}

SERIF_B = "/usr/share/fonts/truetype/noto/NotoSerif-Bold.ttf"
SERIF = "/usr/share/fonts/truetype/noto/NotoSerif-Regular.ttf"
SANS_B = "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf"
SANS = "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf"

W, H = 1024, 1024


def font(path, size):
    return ImageFont.truetype(path, size)


def wrap(draw, text, fnt, max_w, max_lines=None):
    lines, cur = [], ""
    for word in text.split(" "):
        trial = word if not cur else cur + " " + word
        if draw.textlength(trial, font=fnt) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    if max_lines and len(lines) > max_lines:
        lines = lines[:max_lines]
        last = lines[-1]
        while last and draw.textlength(last + "...", font=fnt) > max_w:
            last = last[:-1]
        lines[-1] = last + "..."
    return lines


def draw_lines(draw, lines, x, y, fnt, fill, lh):
    for ln in lines:
        draw.text((x, y), ln, font=fnt, fill=fill)
        y += lh
    return y


# ------------------------------------------- hand-simplified world outline
# Rough continent polygons in (lon, lat), simplified by hand for this
# page until the shapes read at 952 px wide. They live in this file on
# purpose: the renderer must not import anything from outside the repo.
NORTH_AMERICA = [
    (-168, 66), (-162, 60), (-155, 58), (-148, 60), (-140, 60), (-135, 57),
    (-130, 54), (-125, 49), (-124, 42), (-121, 36), (-117, 32), (-111, 28),
    (-108, 25), (-103, 25), (-97, 26), (-91, 19), (-87, 16), (-83, 10),
    (-79, 9), (-81, 13), (-85, 15), (-88, 14), (-92, 15), (-95, 17),
    (-94, 19), (-90, 21), (-87, 21), (-83, 25), (-81, 26), (-80, 32),
    (-76, 35), (-74, 40), (-70, 42), (-67, 44), (-63, 46), (-59, 48),
    (-55, 52), (-58, 55), (-62, 58), (-66, 60), (-70, 62), (-76, 62),
    (-82, 66), (-88, 66), (-93, 66), (-95, 69), (-105, 68), (-115, 69),
    (-125, 70), (-135, 69), (-145, 70), (-155, 71), (-163, 70), (-168, 66),
]
GREENLAND = [
    (-45, 60), (-40, 64), (-32, 68), (-25, 70), (-22, 74), (-28, 78),
    (-40, 80), (-52, 80), (-58, 76), (-55, 72), (-52, 68), (-48, 64),
]
SOUTH_AMERICA = [
    (-78, 8), (-74, 11), (-68, 11), (-62, 9), (-57, 6), (-52, 5), (-50, 0),
    (-46, -2), (-41, -3), (-35, -8), (-37, -13), (-39, -18), (-41, -23),
    (-46, -25), (-49, -29), (-53, -33), (-57, -38), (-62, -41), (-66, -45),
    (-69, -50), (-71, -54), (-73, -50), (-73, -44), (-73, -37), (-72, -30),
    (-71, -22), (-71, -17), (-76, -14), (-79, -8), (-81, -4), (-80, 2),
    (-78, 5),
]
EUROPE = [
    (-10, 36), (-9, 38), (-9, 43), (-4, 44), (-2, 44), (-1, 46), (-1, 49),
    (2, 51), (4, 53), (7, 54), (8, 57), (10, 58), (13, 56), (18, 56),
    (19, 58), (21, 60), (24, 60), (27, 60), (30, 60), (28, 58), (24, 58),
    (22, 56), (20, 55), (23, 55), (24, 52), (27, 50), (28, 47), (29, 45),
    (27, 44), (24, 45), (22, 44), (20, 42), (19, 42), (16, 40), (16, 38),
    (15, 40), (13, 42), (12, 44), (9, 44), (7, 44), (3, 43), (0, 40),
    (-2, 37), (-6, 36), (-9, 37),
]
UNITED_KINGDOM = [
    (-5, 50), (-3, 53), (-5, 55), (-4, 57), (-2, 58), (0, 53), (1, 51),
    (-3, 50),
]
AFRICA = [
    (-17, 15), (-16, 20), (-13, 24), (-10, 30), (-6, 33), (-1, 35),
    (4, 37), (10, 37), (11, 34), (15, 32), (20, 32), (25, 32), (30, 31),
    (33, 28), (35, 24), (37, 20), (39, 16), (41, 12), (44, 11), (48, 11),
    (51, 11), (50, 6), (47, 1), (42, -2), (40, -8), (39, -13), (36, -18),
    (34, -22), (32, -26), (29, -30), (27, -33), (22, -34), (19, -35),
    (17, -31), (15, -26), (13, -21), (12, -17), (13, -12), (12, -7),
    (11, -3), (9, 4), (6, 4), (2, 6), (-3, 5), (-8, 5), (-12, 8),
    (-15, 11), (-17, 13),
]
MADAGASCAR = [
    (44, -16), (47, -15), (50, -16), (49, -20), (47, -24), (45, -25),
    (43, -22), (44, -18),
]
ASIA = [
    (28, 36), (30, 36), (33, 36), (36, 36), (39, 32), (42, 31), (45, 29),
    (48, 29), (50, 29), (52, 27), (54, 26), (57, 26), (59, 25), (61, 25),
    (64, 25), (67, 25), (69, 23), (72, 20), (74, 18), (76, 13), (77, 8),
    (80, 7), (80, 12), (82, 16), (85, 19), (88, 22), (90, 22), (92, 21),
    (93, 17), (95, 16), (97, 13), (99, 9), (101, 7), (103, 2), (104, 2),
    (106, 9), (109, 12), (109, 16), (106, 20), (108, 21), (110, 20),
    (113, 22), (116, 23), (119, 25), (121, 28), (122, 31), (121, 35),
    (122, 38), (125, 40), (127, 40), (129, 39), (130, 42), (132, 43),
    (135, 44), (138, 46), (141, 49), (142, 53), (141, 58), (143, 59),
    (150, 59), (156, 58), (158, 55), (160, 60), (162, 63), (160, 66),
    (155, 69), (145, 72), (135, 72), (125, 73), (115, 74), (105, 76),
    (95, 76), (85, 75), (75, 73), (68, 71), (60, 69), (52, 68), (45, 67),
    (38, 66), (33, 64), (30, 60), (28, 56), (28, 50), (28, 45), (28, 41),
]
JAPAN = [
    (130, 31), (131, 33), (133, 34), (135, 34), (137, 35), (139, 36),
    (140, 38), (141, 40), (142, 42), (144, 44), (142, 44), (140, 41),
    (139, 38), (137, 37), (135, 35), (133, 34), (131, 32),
]
SOUTHEAST_ISLANDS = [
    (95, 5), (98, 4), (100, 0), (103, -2), (106, -6), (110, -7), (114, -8),
    (118, -9), (120, -10), (119, -6), (116, -3), (112, -2), (108, 0),
    (104, 1), (100, 3), (97, 5),
]
AUSTRALIA = [
    (113, -22), (113, -27), (114, -31), (115, -35), (118, -35), (122, -34),
    (126, -32), (129, -32), (132, -32), (135, -35), (138, -35), (140, -38),
    (143, -39), (146, -39), (149, -37), (150, -34), (153, -32), (153, -27),
    (151, -24), (148, -20), (146, -19), (143, -15), (142, -11), (140, -13),
    (137, -12), (135, -12), (132, -12), (129, -14), (126, -14), (122, -17),
    (118, -20), (115, -21),
]
NEW_ZEALAND = [
    (167, -45), (169, -43), (171, -42), (173, -40), (175, -38), (177, -38),
    (176, -40), (174, -41), (172, -43), (169, -46), (167, -46),
]
CONTINENTS = [
    NORTH_AMERICA, GREENLAND, SOUTH_AMERICA, EUROPE, UNITED_KINGDOM,
    AFRICA, MADAGASCAR, ASIA, JAPAN, SOUTHEAST_ISLANDS, AUSTRALIA,
    NEW_ZEALAND,
]


def projector_for(x0, y0, x1, y1):
    """Build a lon/lat -> pixel function for one map box.

    The world window is fixed for this page: longitude -170..190,
    latitude -55..80. The returned closure is the only place that knows
    the projection, so the painters below stay in pixel terms.
    """
    span_lon = 190 - (-170)
    span_lat = 80 - (-55)

    def project(lon, lat):
        px = x0 + (lon - (-170)) / span_lon * (x1 - x0)
        py = y0 + (80 - lat) / span_lat * (y1 - y0)
        return (px, py)

    return project


def paint_world(draw, x0, y0, x1, y1):
    """Fill every landmass polygon inside the box; return its projector."""
    project = projector_for(x0, y0, x1, y1)
    edge = (150, 142, 122)
    for landmass in CONTINENTS:
        points = [project(lon, lat) for lon, lat in landmass]
        draw.polygon(points, fill=LAND, outline=edge)
    return project


# Pixel offsets for pins whose places sit close together on the map
# (Europe / Middle East / Indonesia clusters), so numbers stay readable.
PIN_OFFSETS = {
    3: (12, -10), 4: (-13, 9), 5: (13, 8), 6: (-15, -8), 7: (-11, -6),
    12: (-6, -13), 22: (15, 12), 23: (-16, 14),
}


def mark_pins(draw, project, pins, radius=8, number_size=9):
    """Numbered story markers: dark halo, coloured disc, white numeral."""
    numeral = font(SANS_B, number_size)
    for lon, lat, num, col in pins:
        px, py = project(lon, lat)
        shift_x, shift_y = PIN_OFFSETS.get(num, (0, 0))
        px, py = px + shift_x, py + shift_y
        halo = [px - radius - 1, py - radius - 1,
                px + radius + 1, py + radius + 1]
        draw.ellipse(halo, fill=MAST_DARK)
        disc = [px - radius, py - radius, px + radius, py + radius]
        draw.ellipse(disc, fill=col, outline=WHITE, width=2)
        label = str(num)
        label_x = px - draw.textlength(label, font=numeral) / 2
        draw.text((label_x, py - number_size / 2 - 1), label,
                  font=numeral, fill=WHITE)


def mark_dots(draw, project, places, radius=2):
    """Small plain dots for the 'also on' stories."""
    for lon, lat in places:
        px, py = project(lon, lat)
        draw.ellipse([px - radius, py - radius, px + radius, py + radius],
                     fill=INK)


# ------------------------------------------------------------------ scenes
# Pictograms for this page, drawn from Pillow primitives only. Each one
# paints inside its (x, y, w, h) box and draws no text of its own.

def burst_shape(d, cx, cy, r, fill, points=10):
    """A jagged starburst: alternating long and short spikes."""
    corners = []
    step = 0
    while step < points * 2:
        ang = step * math.pi / points - math.pi / 2
        reach = r if step % 2 == 0 else r * 0.45
        corners.append((cx + reach * math.cos(ang),
                        cy + reach * math.sin(ang)))
        step += 1
    d.polygon(corners, fill=fill)


def burst(d, cx, cy, r):
    """Two nested starbursts and a hot core: this page's explosion mark."""
    burst_shape(d, cx, cy, r, (255, 140, 0))
    burst_shape(d, cx, cy, r * 0.6, (255, 220, 0))
    core = r * 0.22
    d.ellipse([cx - core, cy - core, cx + core, cy + core], fill=WHITE)


def haze(d, cx, cy, r):
    """Three overlapping grey puffs, read as smoke at small sizes."""
    puffs = [(-r, 0, r * 0.55), (0, -r * 0.7, r * 0.65),
             (r * 0.8, -r * 0.3, r * 0.5)]
    shades = [(120, 120, 118), (150, 150, 146), (120, 120, 118)]
    for (off_x, off_y, puff_r), shade in zip(puffs, shades):
        d.ellipse([cx + off_x - puff_r, cy + off_y - puff_r,
                   cx + off_x + puff_r, cy + off_y + puff_r], fill=shade)


def surf(d, x, y, w, h, color=WHITE):
    """Rows of small arcs suggesting water."""
    row = 0
    while row < 3:
        yy = y + row * h // 3
        col = 0
        while col < 4:
            xx = x + col * w // 4
            d.arc([xx, yy, xx + w // 4, yy + h // 3], 180, 360,
                  fill=color, width=2)
            col += 1
        row += 1


def paint_skyline(d, x, y, w, h):
    """Dusk skyline with lit windows and three flag poles (summit)."""
    d.rectangle([x, y, x + w, y + h], fill=(26, 44, 66))
    moon = [x + w * 0.85, y + h * 0.05, x + w * 0.94, y + h * 0.19]
    d.ellipse(moon, fill=(255, 214, 120))
    tower_heights = [0.52, 0.74, 0.60, 0.86, 0.66, 0.78, 0.56, 0.70]
    tower_w = w / len(tower_heights)
    for idx, frac_h in enumerate(tower_heights):
        left = x + idx * tower_w + 2
        top = y + h * (1 - frac_h)
        d.rectangle([left, top, left + tower_w - 4, y + h], fill=MAST_DARK)
        for row_i in range(3):
            for col_i in range(2):
                if (idx + row_i + col_i) % 2 == 0:
                    win_x = left + 5 + col_i * (tower_w / 2 - 2)
                    win_y = top + 8 + row_i * 13
                    d.rectangle([win_x, win_y, win_x + 5, win_y + 6],
                                fill=(255, 214, 120))
    flag_cols = [(178, 34, 52), (60, 59, 110), (222, 41, 16)]
    for idx, col in enumerate(flag_cols):
        pole_x = x + w * (0.14 + idx * 0.22)
        pole_top = y + h * 0.22
        d.line([(pole_x, pole_top), (pole_x, y + h * 0.52)], fill=WHITE,
               width=2)
        d.rectangle([pole_x + 2, pole_top, pole_x + 2 + w * 0.075,
                     pole_top + h * 0.10], fill=col)


def paint_gavel(d, x, y, w, h):
    """Gavel and sound block (court ruling)."""
    wood = (120, 90, 50)
    dark_wood = (90, 60, 30)
    d.rectangle([x, y, x + w, y + h], fill=(238, 232, 218))
    block = [x + w * 0.30, y + h * 0.72, x + w * 0.70, y + h * 0.86]
    d.ellipse(block, fill=wood)
    handle = [(x + w * 0.22, y + h * 0.62), (x + w * 0.62, y + h * 0.22)]
    d.line(handle, fill=dark_wood, width=8)
    head_a = [x + w * 0.55, y + h * 0.10, x + w * 0.80, y + h * 0.28]
    head_b = [x + w * 0.14, y + h * 0.50, x + w * 0.38, y + h * 0.68]
    d.rectangle(head_a, fill=wood)
    d.rectangle(head_b, fill=wood)
    ring = 0
    while ring < 3:
        arc_box = [x + w * 0.55, y + h * 0.05 + ring * 6,
                   x + w * 0.95, y + h * 0.45 + ring * 6]
        d.arc(arc_box, 270, 360, fill=SLATE, width=2)
        ring += 1


def paint_bridge(d, x, y, w, h):
    """Bridge over a strait with a blasted gap in the deck."""
    d.rectangle([x, y, x + w, y + h], fill=(214, 228, 238))
    water_top = y + h * 0.62
    d.rectangle([x, water_top, x + w, y + h], fill=SEA)
    surf(d, x + 6, y + h * 0.68, w - 12, h * 0.26)
    deck_y = y + h * 0.55
    d.line([(x + 4, deck_y), (x + w * 0.42, deck_y)], fill=INK, width=4)
    d.line([(x + w * 0.58, deck_y), (x + w - 4, deck_y)], fill=INK, width=4)
    arch = [x + w * 0.30, deck_y - h * 0.34, x + w * 0.70,
            deck_y + h * 0.10]
    d.arc(arch, 180, 360, fill=INK, width=5)
    for frac in (0.16, 0.84):
        pier_x = x + w * frac
        d.rectangle([pier_x - 3, deck_y, pier_x + 3, water_top], fill=INK)
    haze(d, x + w * 0.5, deck_y - h * 0.30, h * 0.10)
    burst(d, x + w * 0.5, deck_y - h * 0.08, h * 0.13)


def paint_globe_flame(d, x, y, w, h):
    """Globe with a flame beside it (climate talks)."""
    cx, cy = x + w * 0.38, y + h * 0.55
    r = min(w, h) * 0.34
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=SEA, outline=MAST,
              width=2)
    meridian = [cx - r * 0.45, cy - r, cx + r * 0.45, cy + r]
    d.ellipse(meridian, outline=MAST)
    d.line([(cx - r, cy), (cx + r, cy)], fill=MAST, width=2)
    fx, fy = x + w * 0.76, y + h * 0.55
    outer_flame = [(fx, fy - r * 1.1), (fx + r * 0.5, fy - r * 0.2),
                   (fx + r * 0.35, fy + r * 0.5),
                   (fx - r * 0.35, fy + r * 0.5),
                   (fx - r * 0.5, fy - r * 0.2)]
    inner_flame = [(fx, fy - r * 0.5), (fx + r * 0.28, fy),
                   (fx + r * 0.2, fy + r * 0.4),
                   (fx - r * 0.2, fy + r * 0.4),
                   (fx - r * 0.28, fy)]
    d.polygon(outer_flame, fill=ORANGE)
    d.polygon(inner_flame, fill=(255, 220, 0))


def paint_hemicycle(d, x, y, w, h, share=0.56):
    """Semicircle of seats; the first `share` of them in mast colour."""
    cx, cy = x + w / 2, y + h * 0.94
    filled = int(21 * share)
    seat_no = 0
    for ring_r in (0.82, 0.60, 0.38):
        seat = 0
        while seat < 7:
            ang = math.pi * (1 - (seat + 0.5) / 7)
            px = cx + ring_r * w * 0.48 * math.cos(ang)
            py = cy - ring_r * h * 0.88 * math.sin(ang)
            tone = MAST if seat_no < filled else (210, 210, 200)
            d.ellipse([px - 5, py - 5, px + 5, py + 5], fill=tone)
            seat_no += 1
            seat += 1


# ------------------------------------------------------------- card icons
CARD_KIND = {
    4: "drone", 5: "tower", 6: "globe", 7: "parliament", 8: "atom",
    9: "sun", 10: "art", 11: "bars", 12: "scale", 13: "flag",
}


def draw_card_icon(d, kind, x, y, w, h):
    if kind == "drone":
        # Compact portrait-safe drone: centred, nothing touches the edges.
        d.rectangle([x, y, x + w, y + h], fill=(232, 222, 200))
        d.rectangle([x, y + h * 0.74, x + w, y + h], fill=(200, 190, 150))
        cx, cy = x + w * 0.40, y + h * 0.24
        d.ellipse([cx - 9, cy - 3, cx + 9, cy + 3], fill=INK)
        d.line([(cx - 15, cy - 5), (cx + 15, cy - 5)], fill=INK, width=2)
        d.line([(cx, cy - 9), (cx, cy + 5)], fill=INK, width=2)
        for t in [i / 6 for i in range(7)]:
            px = cx + 10 + w * 0.34 * t
            py = cy + 7 + h * 0.32 * t
            d.ellipse([px - 1.5, py - 1.5, px + 1.5, py + 1.5], fill=SLATE)
        burst(d, x + w * 0.74, y + h * 0.60, h * 0.13)
        haze(d, x + w * 0.74, y + h * 0.42, h * 0.08)
    elif kind == "globe":
        d.rectangle([x, y, x + w, y + h], fill=(226, 238, 244))
        paint_globe_flame(d, x, y, w, h)
    elif kind == "parliament":
        d.rectangle([x, y, x + w, y + h], fill=(240, 236, 224))
        paint_hemicycle(d, x, y, w, h, share=140 / 250)
    elif kind == "tower":
        d.rectangle([x, y, x + w, y + h], fill=(214, 228, 238))
        bx = x + w * 0.38
        d.rectangle([bx, y + h * 0.18, bx + w * 0.24, y + h], fill=MAST)
        for r in range(3):
            d.rectangle([bx + 5, y + h * (0.28 + r * 0.20),
                         bx + w * 0.24 - 5, y + h * (0.38 + r * 0.20)],
                        fill=(255, 214, 120))
        burst(d, bx + w * 0.12, y + h * 0.22, h * 0.20)
        haze(d, bx + w * 0.12, y + h * 0.05, h * 0.10)
    elif kind == "atom":
        d.rectangle([x, y, x + w, y + h], fill=(30, 42, 68))
        cx, cy = x + w / 2, y + h / 2
        for ang_deg in (0, 60, 120):
            ang = math.radians(ang_deg)
            pts = []
            for k in range(37):
                t = 2 * math.pi * k / 36
                ex = w * 0.32 * math.cos(t)
                ey = h * 0.17 * math.sin(t)
                pts.append((cx + ex * math.cos(ang) - ey * math.sin(ang),
                            cy + ex * math.sin(ang) + ey * math.cos(ang)))
            d.line(pts, fill=(255, 214, 120), width=2)
        d.ellipse([cx - 6, cy - 6, cx + 6, cy + 6], fill=CRIMSON)
    elif kind == "sun":
        d.rectangle([x, y, x + w, y + h], fill=(250, 230, 180))
        cx, cy = x + w * 0.32, y + h * 0.38
        d.ellipse([cx - 13, cy - 13, cx + 13, cy + 13], fill=ORANGE)
        for k in range(8):
            a = k * math.pi / 4
            d.line([(cx + 17 * math.cos(a), cy + 17 * math.sin(a)),
                    (cx + 23 * math.cos(a), cy + 23 * math.sin(a))],
                   fill=ORANGE, width=3)
        d.line([(x + 6, y + h * 0.82), (x + w - 6, y + h * 0.82)],
               fill=(150, 100, 40), width=3)
        d.line([(x + w * 0.55, y + h * 0.82), (x + w * 0.62, y + h * 0.94)],
               fill=(150, 100, 40), width=2)
        d.line([(x + w * 0.70, y + h * 0.82), (x + w * 0.66, y + h * 0.94)],
               fill=(150, 100, 40), width=2)
    elif kind == "art":
        d.rectangle([x, y, x + w, y + h], fill=(52, 40, 30))
        d.rectangle([x + w * 0.22, y + h * 0.14, x + w * 0.78,
                     y + h * 0.86], fill=(245, 238, 210), outline=GOLD,
                    width=3)
        d.ellipse([x + w * 0.36, y + h * 0.28, x + w * 0.52, y + h * 0.48],
                  fill=(255, 200, 60))
        d.arc([x + w * 0.30, y + h * 0.30, x + w * 0.72, y + h * 0.80],
              200, 340, fill=(70, 110, 180), width=3)
        d.arc([x + w * 0.34, y + h * 0.40, x + w * 0.68, y + h * 0.84],
              200, 340, fill=CRIMSON, width=3)
    elif kind == "bars":
        d.rectangle([x, y, x + w, y + h], fill=WHITE)
        vals = (0.30, 0.48, 0.42, 0.72, 1.0)
        gap = w * 0.07
        bw = (w - gap * 6) / len(vals)
        for i, v in enumerate(vals):
            bx = x + gap + i * (bw + gap)
            d.rectangle([bx, y + h * 0.86 - v * h * 0.62, bx + bw,
                         y + h * 0.86], fill=GREEN)
        d.line([(x + gap, y + h * 0.86), (x + w - gap, y + h * 0.86)],
               fill=INK, width=2)
        d.line([(x + gap, y + h * 0.30), (x + w - gap * 2, y + h * 0.14)],
               fill=CRIMSON, width=3)
    elif kind == "scale":
        d.rectangle([x, y, x + w, y + h], fill=(238, 232, 218))
        cx = x + w / 2
        d.line([(cx, y + h * 0.14), (cx, y + h * 0.80)], fill=INK, width=3)
        d.line([(cx - w * 0.30, y + h * 0.24), (cx + w * 0.30, y + h * 0.24)],
               fill=INK, width=3)
        for sgn in (-1, 1):
            px = cx + sgn * w * 0.30
            d.polygon([(px, y + h * 0.24), (px - 12, y + h * 0.52),
                       (px + 12, y + h * 0.52)], outline=INK)
            d.arc([px - 13, y + h * 0.44, px + 13, y + h * 0.62], 0, 180,
                  fill=GOLD, width=3)
        d.rectangle([cx - 14, y + h * 0.80, cx + 14, y + h * 0.88],
                    fill=INK)
    elif kind == "flag":
        d.rectangle([x, y, x + w, y + h], fill=(214, 228, 238))
        d.line([(x + w * 0.30, y + h * 0.10), (x + w * 0.30, y + h * 0.92)],
               fill=INK, width=3)
        d.polygon([(x + w * 0.30, y + h * 0.10), (x + w * 0.78, y + h * 0.20),
                   (x + w * 0.30, y + h * 0.34)], fill=CRIMSON)
        d.rectangle([x + w * 0.55, y + h * 0.55, x + w * 0.90, y + h * 0.92],
                    fill=MAST)
        d.rectangle([x + w * 0.10, y + h * 0.62, x + w * 0.42, y + h * 0.92],
                    fill=TEAL)
    else:
        d.rectangle([x, y, x + w, y + h], fill=LIGHT)


# ------------------------------------------------------------------ render

def main():
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, "stories.json"), encoding="utf-8") as fh:
        data = json.load(fh)
    stories = data["stories"]
    leads = [s for s in stories if s["tier"] == "lead"]
    cards = [s for s in stories if s["tier"] == "card"]
    also = [s for s in stories if s["tier"] == "also"]

    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)

    # masthead
    d.rectangle([0, 0, W, 80], fill=MAST)
    d.text((24, 8), "THE WORLD IN ONE PAGE", font=font(SERIF_B, 38),
           fill=WHITE)
    d.text((24, 52), "Thursday 19 November 2026  -  40 stories, one image",
           font=font(SANS_B, 13), fill=GOLD)
    d.text((W - 24 - 118, 16), "19 NOV", font=font(SERIF_B, 30), fill=WHITE)
    d.text((W - 24 - 118, 50), "2026", font=font(SANS_B, 13), fill=GOLD)

    # region strip
    counts = {}
    for s in stories:
        counts[s["region"]] = counts.get(s["region"], 0) + 1
    x = 24
    y = 88
    for region in ["Asia", "Europe", "Middle East", "Americas", "Africa",
                   "Oceania", "Global"]:
        if region not in counts:
            continue
        label = "%s %d" % (region, counts[region])
        f = font(SANS_B, 11)
        tw = d.textlength(label, font=f)
        d.rectangle([x, y, x + tw + 16, y + 22],
                    fill=REGION_COLORS[region])
        d.text((x + 8, y + 4), label, font=f, fill=WHITE)
        x += tw + 24

    # leads
    ly, lh = 118, 190
    # lead 1 (big, left)
    d.rectangle([24, ly, 664, ly + lh], fill=(26, 44, 66))
    paint_skyline(d, 24, ly, 640, 128)
    d.rectangle([24, ly + 128, 664, ly + lh], fill=MAST_DARK)
    d.text((36, ly + 134), "1  SHENZHEN SUMMIT", font=font(SANS_B, 15),
           fill=GOLD)
    for i, ln in enumerate(wrap(d, leads[0]["headline"] + " - " +
                                leads[0]["summary"], font(SANS, 11), 616,
                                max_lines=2)):
        d.text((36, ly + 155 + i * 14), ln, font=font(SANS, 11),
               fill=(228, 232, 226))
    # lead 2 (top right): gavel scene left, text right
    d.rectangle([676, ly, 1000, ly + 91], fill=(238, 232, 218),
                outline=(200, 194, 178))
    paint_gavel(d, 676, ly, 118, 91)
    d.text((806, ly + 7), "2  WORLD COURT", font=font(SANS_B, 12),
           fill=CRIMSON)
    for i, ln in enumerate(wrap(d, leads[1]["headline"],
                                font(SANS_B, 11), 182, max_lines=4)):
        d.text((806, ly + 25 + i * 14), ln, font=font(SANS_B, 11), fill=INK)
    # lead 3 (bottom right): bridge scene left, text right
    d.rectangle([676, ly + 99, 1000, ly + lh], fill=(214, 228, 238),
                outline=(200, 194, 178))
    paint_bridge(d, 676, ly + 99, 118, 91)
    d.text((806, ly + 106), "3  CRIMEA BRIDGE", font=font(SANS_B, 12),
           fill=MAST)
    for i, ln in enumerate(wrap(d, leads[2]["headline"],
                                font(SANS_B, 11), 182, max_lines=4)):
        d.text((806, ly + 124 + i * 14), ln, font=font(SANS_B, 11),
               fill=INK)

    # map panel (taller in v2: 240 px, so continents and pins can breathe)
    my, mh = 316, 240
    d.rectangle([24, my, 1000, my + mh], fill=(226, 238, 244))
    d.text((36, my + 6), "WHERE IT HAPPENED - pins 1-13, dots for the rest",
           font=font(SANS_B, 12), fill=MAST)
    proj = paint_world(d, 36, my + 30, 988, my + mh - 10)
    pins = [(s["lon"], s["lat"], s["id"],
             REGION_COLORS.get(s["region"], SLATE))
            for s in leads + cards]
    mark_pins(d, proj, pins, radius=8, number_size=9)
    mark_dots(d, proj, [(s["lon"], s["lat"]) for s in also], radius=2)

    # cards grid: 5 across x 2 rows; headline plus a short summary line
    cy0 = 564
    cw, chh, gap = 188, 91, 8
    for i, s in enumerate(cards):
        cx = 24 + (i % 5) * (cw + gap)
        cyy = cy0 + (i // 5) * (chh + gap)
        d.rectangle([cx, cyy, cx + cw, cyy + chh], fill=WHITE,
                    outline=(200, 194, 178))
        draw_card_icon(d, CARD_KIND.get(s["id"], ""), cx + 5, cyy + 5,
                       54, 81)
        tx = cx + 65
        d.text((tx, cyy + 5), "%d  %s" % (s["id"], s["place"].split(",")[0].upper()[:14]),
               font=font(SANS_B, 8), fill=REGION_COLORS.get(s["region"], SLATE))
        head = wrap(d, s["headline"], font(SANS_B, 10), cw - 72,
                    max_lines=3)
        yy = draw_lines(d, head, tx, cyy + 18, font(SANS_B, 10), INK, 12)
        short = s.get("short") or s["summary"]
        room = cyy + chh - 5 - yy
        if room >= 21:
            max_sl = 2
        elif room >= 11:
            max_sl = 1
        else:
            max_sl = 0
        if max_sl:
            draw_lines(d, wrap(d, short, font(SANS, 8), cw - 72,
                               max_lines=max_sl),
                       tx, yy + 1, font(SANS, 8), SLATE, 10)

    # also-on list: 3 columns
    ay = 762
    d.rectangle([24, ay, 1000, 982], fill=MAST)
    d.text((36, ay + 7), "ALSO ON 19 NOVEMBER", font=font(SANS_B, 13),
           fill=GOLD)
    col_w = 312
    per_col = 9
    for ci in range(3):
        items = also[ci * per_col:(ci + 1) * per_col]
        cx = 36 + ci * (col_w + 12)
        yy = ay + 32
        for s in items:
            txt = "%d. %s" % (s["id"], s["headline"])
            lines = wrap(d, txt, font(SANS, 9), col_w, max_lines=2)
            for ln in lines:
                d.text((cx, yy), ln, font=font(SANS, 9),
                       fill=(238, 240, 236))
                yy += 11
            yy += 3

    # footer
    d.text((24, 990),
           "Sources: Reuters, AP, AFP, BBC, Al Jazeera, UN News, IAEA, "
           "ICJ, Save the Children, Copernicus. Each key fact checked "
           "against at least two sources; disputed claims attributed.",
           font=font(SANS, 9), fill=SLATE)
    d.text((24, 1004),
           "Drawn entirely in code with Pillow. No network at run time. "
           "Deterministic: same input, same PNG.",
           font=font(SANS, 9), fill=SLATE)

    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    img.save(os.path.join(out_dir, "entry.png"), format="PNG", optimize=False)
    print("wrote", os.path.join(out_dir, "entry.png"))


if __name__ == "__main__":
    main()
