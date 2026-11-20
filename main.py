"""One page of world news for Thursday 19 November 2026, drawn in code.

Revision two of the entry: the page keeps the round-one selection of
forty stories and the same newspaper grid, but the Shenzhen lead panel
is rebuilt with a brighter dusk sky, a denser two-row skyline and many
more lit windows, and every text panel was re-checked for contrast at
the final 1024 by 1024 size.

The renderer reads stories.json from its own folder, draws everything
with Pillow primitives and writes entry.png to the folder named by
MAKEFUN_OUTPUT_DIR (falling back to /output). It touches no network,
no clock and no randomness, so repeated runs emit identical bytes.
"""

import json
import math
import os

from PIL import Image, ImageDraw, ImageFont

# --- the page palette, fixed by the design brief for this revision ---
NAVY = (14, 30, 58)          # #0E1E3A, masthead and panel ink-blue
NAVY_DEEP = (9, 20, 40)      # darker shade of the navy for caption bands
PAPER = (247, 243, 234)      # #F7F3EA, the sheet the page is printed on
INK = (17, 17, 17)           # #111111, body text
GOLD = (201, 162, 39)        # #C9A227, rules, kickers and dates
RED = (155, 27, 27)          # #9B1B1B, accent for court and conflict
CARD_LINE = (164, 152, 128)  # panel and card borders, darkened in rev2
# Every framed panel on the page is stroked with this border width, so
# pale panels still read as boxes against the pale paper around them.
BORDER_W = 2
PALE_CARD = (240, 234, 219)  # warm fill behind the court lead
SKY_WATER = (188, 214, 230)  # sea colour for the map and bridge panels
LAND_TONE = (233, 223, 193)  # landmass fill on the locator map
LAND_EDGE = (138, 128, 102)  # landmass outline, dark enough to read
MIST = (235, 238, 233)       # near-white text sitting on navy
SLATE_DARK = (56, 60, 64)    # card summaries and footer, darkened in rev2
WHITE = (255, 255, 255)

# One colour per region, used for the strip chips, the map pins and the
# card kickers, so a reader can follow a story across the whole page.
REGION_TINT = {
    "Asia": (190, 92, 22),
    "Europe": (24, 52, 96),
    "Middle East": RED,
    "Americas": (94, 62, 138),
    "Africa": (42, 106, 62),
    "Oceania": (12, 112, 114),
    "Global": (66, 70, 76),
}

SERIF_FILE = "/usr/share/fonts/truetype/noto/NotoSerif-Bold.ttf"
SERIF_TEXT = "/usr/share/fonts/truetype/noto/NotoSerif-Regular.ttf"
SANS_FILE = "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf"
SANS_TEXT = "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf"

PAGE_W = 1024
PAGE_H = 1024
MARGIN = 24

_font_cache = {}


def get_font(kind, size):
    """Return a cached TrueType font; kind is serif/sans, bold or plain."""
    key = (kind, size)
    if key not in _font_cache:
        if kind == "serif-bold":
            path = SERIF_FILE
        elif kind == "serif":
            path = SERIF_TEXT
        elif kind == "sans-bold":
            path = SANS_FILE
        else:
            path = SANS_TEXT
        _font_cache[key] = ImageFont.truetype(path, size)
    return _font_cache[key]


def fold_text(draw, text, font, width, limit=None):
    """Split text into lines that fit width; trim the tail with dots.

    Words are packed greedily. When a limit is set and the text still
    overflows, the last kept line is shortened until it fits together
    with a trailing ellipsis made of three plain dots.
    """
    words = text.split()
    lines = []
    current = ""
    for word in words:
        trial = word if current == "" else current + " " + word
        if draw.textlength(trial, font=font) <= width:
            current = trial
            continue
        if current != "":
            lines.append(current)
        current = word
    if current != "":
        lines.append(current)
    if limit is not None and len(lines) > limit:
        lines = lines[:limit]
        tail = lines[-1]
        while tail != "" and draw.textlength(tail + "...", font=font) > width:
            tail = tail[:-1]
        lines[-1] = tail + "..."
    return lines


def stack_lines(draw, lines, left, top, font, colour, leading):
    """Draw each line in order, advancing by leading; return next y."""
    y = top
    for line in lines:
        draw.text((left, y), line, font=font, fill=colour)
        y += leading
    return y


# --- locator map -----------------------------------------------------
# Coastlines sketched by hand for this page as rough (lon, lat) rings.
# They only need to read as the world at 950 px wide and to place the
# story pins honestly; no ring is traced from any other file.

RING_NORTH_AMERICA = [
    (-168, 66), (-160, 58), (-148, 59), (-140, 60), (-134, 56),
    (-128, 51), (-124, 46), (-124, 38), (-120, 34), (-114, 29),
    (-109, 23), (-105, 20), (-97, 16), (-92, 15), (-87, 14),
    (-83, 9), (-79, 9), (-81, 13), (-85, 15), (-88, 16),
    (-91, 14), (-94, 17), (-94, 19), (-90, 21), (-87, 21),
    (-84, 23), (-81, 25), (-80, 28), (-81, 32), (-78, 34),
    (-76, 36), (-74, 40), (-70, 42), (-67, 44), (-63, 45),
    (-60, 46), (-65, 49), (-56, 50), (-59, 53), (-63, 58),
    (-68, 61), (-76, 62), (-82, 66), (-85, 60), (-88, 56),
    (-92, 57), (-94, 62), (-93, 66), (-96, 69), (-108, 68),
    (-120, 71), (-135, 69), (-150, 70), (-162, 70),
]
RING_GREENLAND = [
    (-46, 60), (-38, 66), (-30, 68), (-22, 70), (-25, 76),
    (-35, 80), (-50, 79), (-56, 74), (-53, 66),
]
RING_SOUTH_AMERICA = [
    (-77, 7), (-72, 12), (-64, 10), (-55, 6), (-51, 4), (-44, 0),
    (-35, -5), (-35, -9), (-39, -15), (-40, -21), (-48, -26),
    (-52, -32), (-57, -38), (-62, -41), (-65, -45), (-67, -50),
    (-68, -54), (-71, -54), (-73, -46), (-73, -37), (-71, -27),
    (-70, -18), (-75, -15), (-79, -7), (-80, -1), (-77, 4),
]
RING_EUROPE = [
    (-9, 37), (-9, 43), (-5, 44), (-2, 47), (-1, 50), (3, 52),
    (7, 54), (8, 57), (12, 56), (18, 56), (21, 59), (24, 61),
    (30, 61), (28, 57), (24, 55), (21, 55), (24, 52), (28, 50),
    (29, 46), (27, 44), (23, 44), (20, 42), (19, 42), (16, 40),
    (15, 38), (12, 41), (10, 44), (7, 44), (3, 43), (3, 39),
    (0, 38), (-2, 37), (-6, 36),
]
RING_BRITAIN = [
    (-3, 50), (-5, 53), (-3, 56), (-5, 58), (-2, 58), (0, 54),
    (1, 52), (-1, 50),
]
RING_AFRICA = [
    (-6, 35), (0, 36), (10, 37), (11, 34), (20, 32), (30, 31),
    (33, 27), (35, 24), (38, 21), (40, 15), (43, 12), (48, 11),
    (51, 12), (46, 5), (41, 0), (40, -6), (39, -13), (37, -19),
    (35, -24), (32, -29), (27, -34), (20, -35), (17, -32),
    (15, -27), (13, -18), (12, -12), (13, -6), (9, -1), (9, 4),
    (4, 6), (-2, 5), (-8, 5), (-13, 8), (-17, 15), (-16, 21),
    (-13, 27), (-9, 31),
]
RING_MADAGASCAR = [
    (44, -13), (49, -14), (50, -19), (47, -24), (45, -25),
    (43, -21), (44, -16),
]
RING_ASIA = [
    (28, 36), (44, 29), (51, 27), (57, 26), (66, 25), (72, 21),
    (74, 15), (77, 8), (80, 10), (82, 14), (84, 18), (88, 21),
    (92, 21), (93, 16), (95, 15), (97, 10), (99, 6), (101, 2),
    (104, 1), (106, 4), (108, 10), (110, 13), (107, 17),
    (109, 19), (110, 21), (114, 23), (118, 25), (121, 28),
    (122, 32), (120, 35), (122, 38), (126, 38), (129, 36),
    (130, 39), (128, 41), (130, 42), (132, 43), (135, 45),
    (140, 48), (142, 54), (141, 59), (150, 60), (156, 53),
    (159, 56), (162, 60), (158, 63), (152, 64), (160, 66),
    (170, 66), (178, 68), (170, 70), (150, 70), (130, 72),
    (110, 74), (95, 76), (80, 73), (66, 69), (54, 68), (44, 67),
    (36, 65), (32, 62), (28, 56), (28, 48), (28, 41),
]
RING_ARABIA = [
    (35, 28), (39, 21), (43, 13), (48, 14), (55, 17), (59, 22),
    (56, 26), (51, 27), (48, 30), (42, 37), (36, 36),
]
RING_JAPAN = [
    (130, 31), (132, 33), (135, 34), (138, 35), (140, 36),
    (141, 40), (142, 44), (144, 44), (141, 42), (140, 38),
    (137, 35), (133, 34), (131, 32),
]
RING_MARITIME_ASIA = [
    (95, 5), (99, 3), (102, 0), (106, -3), (110, -6), (115, -8),
    (120, -10), (119, -5), (114, -2), (108, 0), (102, 2), (97, 5),
]
RING_PHILIPPINES = [
    (117, 10), (120, 13), (121, 16), (122, 18), (121, 14),
    (119, 11),
]
RING_AUSTRALIA = [
    (114, -22), (113, -28), (115, -34), (118, -35), (124, -33),
    (130, -32), (135, -35), (138, -35), (140, -38), (145, -38),
    (149, -37), (150, -33), (153, -28), (153, -24), (150, -20),
    (146, -19), (143, -15), (142, -11), (140, -14), (136, -12),
    (132, -11), (127, -14), (122, -17), (117, -20),
]
RING_NEW_ZEALAND = [
    (167, -45), (170, -43), (172, -41), (174, -39), (176, -37),
    (178, -37), (175, -40), (173, -42), (170, -44), (167, -46),
]

ALL_RINGS = [
    RING_NORTH_AMERICA, RING_GREENLAND, RING_SOUTH_AMERICA,
    RING_EUROPE, RING_BRITAIN, RING_AFRICA, RING_MADAGASCAR,
    RING_ASIA, RING_ARABIA, RING_JAPAN, RING_MARITIME_ASIA,
    RING_PHILIPPINES, RING_AUSTRALIA, RING_NEW_ZEALAND,
]

# The map window: longitude -170 to 190, latitude -55 to 80.
MAP_LON_MIN, MAP_LON_SPAN = -170.0, 360.0
MAP_LAT_TOP, MAP_LAT_SPAN = 80.0, 135.0


def make_projector(box):
    """Build the lon/lat to pixel conversion for one map box."""
    left, top, right, bottom = box

    def project(lon, lat):
        fx = (lon - MAP_LON_MIN) / MAP_LON_SPAN
        fy = (MAP_LAT_TOP - lat) / MAP_LAT_SPAN
        return (left + fx * (right - left), top + fy * (bottom - top))

    return project


def paint_landmasses(draw, box):
    """Fill all coastline rings inside box; return the projector."""
    project = make_projector(box)
    for ring in ALL_RINGS:
        pixels = [project(lon, lat) for lon, lat in ring]
        draw.polygon(pixels, fill=LAND_TONE, outline=LAND_EDGE)
    return project


# Nudges for pins in crowded clusters, keyed by story id, so the
# numbered discs stay apart around Europe, the Middle East and Java.
PIN_NUDGE = {
    3: (13, -9), 4: (-14, 10), 5: (14, 9), 6: (-16, -9),
    7: (-12, -7), 12: (-7, -14), 22: (16, 13), 23: (-17, 15),
}


def paint_pins(draw, project, marked, plain):
    """Numbered discs for leads and cards; plain dots for the rest.

    The plain dots go down first: several also-stories share a city
    with a numbered story (Shenzhen, Seoul, Washington), and a dot
    painted after its disc would hide the disc's numeral.
    """
    for story in plain:
        px, py = project(story["lon"], story["lat"])
        draw.ellipse([px - 2.5, py - 2.5, px + 2.5, py + 2.5], fill=INK)
    numeral_font = get_font("sans-bold", 9)
    for story in marked:
        px, py = project(story["lon"], story["lat"])
        dx, dy = PIN_NUDGE.get(story["id"], (0, 0))
        px, py = px + dx, py + dy
        tint = REGION_TINT.get(story["region"], SLATE_DARK)
        draw.ellipse([px - 9, py - 9, px + 9, py + 9], fill=NAVY_DEEP)
        draw.ellipse([px - 8, py - 8, px + 8, py + 8], fill=tint,
                     outline=WHITE, width=2)
        label = str(story["id"])
        half = draw.textlength(label, font=numeral_font) / 2
        draw.text((px - half, py - 5), label, font=numeral_font,
                  fill=WHITE)


# --- shared pictogram helpers ----------------------------------------

def starburst(draw, cx, cy, radius, spikes=9):
    """Jagged explosion mark: two nested stars and a bright core."""
    for scale, tone in ((1.0, (255, 138, 0)), (0.58, (255, 216, 0))):
        corners = []
        for step in range(spikes * 2):
            angle = step * math.pi / spikes - math.pi / 2
            reach = radius * scale if step % 2 == 0 else radius * scale * 0.46
            corners.append((cx + reach * math.cos(angle),
                            cy + reach * math.sin(angle)))
        draw.polygon(corners, fill=tone)
    core = radius * 0.2
    draw.ellipse([cx - core, cy - core, cx + core, cy + core], fill=WHITE)


def smoke_puffs(draw, cx, cy, radius):
    """Three overlapping grey ellipses that read as a smoke cloud."""
    layout = [(-1.0, 0.0, 0.55), (0.0, -0.7, 0.66), (0.85, -0.3, 0.5)]
    for off_x, off_y, puff_r in layout:
        r = radius * puff_r
        draw.ellipse([cx + off_x * radius - r, cy + off_y * radius - r,
                      cx + off_x * radius + r, cy + off_y * radius + r],
                     fill=(138, 138, 134))


def wave_rows(draw, x, y, w, h, tone=WHITE):
    """Short arcs in rows, the page shorthand for open water."""
    for row in range(3):
        for col in range(4):
            ax = x + col * w // 4
            ay = y + row * h // 3
            draw.arc([ax, ay, ax + w // 4, ay + h // 3], 180, 360,
                     fill=tone, width=2)


def blend(first, second, share):
    """Mix two RGB tuples; share is the weight of the second colour."""
    return tuple(int(a + (b - a) * share) for a, b in zip(first, second))


# --- lead scenes ------------------------------------------------------

def scene_shenzhen_skyline(draw, x, y, w, h):
    """Dusk skyline for the summit lead, rebuilt for this revision.

    Round one left this panel dark and empty. The sky is now a graded
    wash that lightens towards the horizon, a pale back row of towers
    stands behind the main row, and the main towers carry a dense grid
    of lit windows in two warm tones. The lighting pattern is pure
    arithmetic on the window position, so it never changes between
    runs. Three flag poles close the scene at the front.
    """
    sky_top = (26, 48, 84)
    sky_low = (112, 134, 160)
    for band in range(h):
        share = band / max(h - 1, 1)
        tone = blend(sky_top, sky_low, share)
        if share > 0.82:
            tone = blend(tone, (168, 148, 116), (share - 0.82) * 2.2)
        draw.line([(x, y + band), (x + w, y + band)], fill=tone)
    moon_x, moon_y, moon_r = x + w * 0.87, y + h * 0.16, h * 0.075
    draw.ellipse([moon_x - moon_r - 4, moon_y - moon_r - 4,
                  moon_x + moon_r + 4, moon_y + moon_r + 4],
                 outline=(240, 220, 160))
    draw.ellipse([moon_x - moon_r, moon_y - moon_r,
                  moon_x + moon_r, moon_y + moon_r], fill=(246, 224, 150))

    back_heights = [0.44, 0.58, 0.50, 0.66, 0.54, 0.62, 0.47, 0.60,
                    0.52, 0.68, 0.56, 0.48, 0.63, 0.51]
    slot = w / len(back_heights)
    for idx, frac in enumerate(back_heights):
        left = x + idx * slot + 1
        top = y + h * (1 - frac)
        draw.rectangle([left, top, left + slot - 2, y + h],
                       fill=(58, 80, 110))
        for row_i in range(4):
            for col_i in range(2):
                if (idx * 3 + row_i * 2 + col_i) % 3 == 0:
                    wx = left + 3 + col_i * (slot / 2)
                    wy = top + 6 + row_i * 12
                    draw.rectangle([wx, wy, wx + 3, wy + 4],
                                   fill=(214, 200, 150))

    front_heights = [0.62, 0.82, 0.70, 0.92, 0.76, 0.86, 0.66, 0.78, 0.58]
    tower_w = w / len(front_heights)
    lit_tones = [(255, 205, 110), (255, 236, 180)]
    for idx, frac in enumerate(front_heights):
        left = x + idx * tower_w + 2
        top = y + h * (1 - frac)
        draw.rectangle([left, top, left + tower_w - 4, y + h],
                       fill=(13, 26, 48))
        draw.line([(left, top), (left + tower_w - 4, top)],
                  fill=(90, 110, 140), width=1)
        cols = 3 if tower_w > 60 else 2
        rows = int((h - (top - y) - 14) // 11)
        for row_i in range(rows):
            for col_i in range(cols):
                if (idx * 5 + row_i * 3 + col_i * 7) % 3 == 0:
                    continue
                wx = left + 5 + col_i * ((tower_w - 12) / max(cols - 1, 1))
                wy = top + 7 + row_i * 11
                tone = lit_tones[(idx + row_i + col_i) % 2]
                draw.rectangle([wx, wy, wx + 5, wy + 6], fill=tone)

    flag_tones = [(190, 36, 44), (44, 62, 120), (206, 52, 32)]
    for idx, tone in enumerate(flag_tones):
        pole_x = x + w * (0.16 + idx * 0.2)
        pole_top = y + h * 0.3
        draw.line([(pole_x, pole_top), (pole_x, y + h * 0.58)],
                  fill=WHITE, width=2)
        draw.rectangle([pole_x + 2, pole_top, pole_x + 2 + w * 0.07,
                        pole_top + h * 0.09], fill=tone)
    draw.rectangle([x, y + h - 3, x + w, y + h], fill=NAVY_DEEP)


def scene_court_gavel(draw, x, y, w, h):
    """A gavel resting over its sound block, for the World Court lead."""
    draw.rectangle([x, y, x + w, y + h], fill=PALE_CARD)
    wood = (122, 92, 52)
    wood_dark = (88, 60, 30)
    block = [x + w * 0.3, y + h * 0.74, x + w * 0.72, y + h * 0.88]
    draw.ellipse(block, fill=wood)
    draw.line([(x + w * 0.24, y + h * 0.64), (x + w * 0.62, y + h * 0.24)],
              fill=wood_dark, width=8)
    draw.rectangle([x + w * 0.56, y + h * 0.1, x + w * 0.82, y + h * 0.28],
                   fill=wood)
    draw.rectangle([x + w * 0.13, y + h * 0.5, x + w * 0.38, y + h * 0.68],
                   fill=wood)
    for ring in range(3):
        arc_box = [x + w * 0.56, y + h * 0.04 + ring * 6,
                   x + w * 0.96, y + h * 0.44 + ring * 6]
        draw.arc(arc_box, 270, 360, fill=SLATE_DARK, width=2)


def scene_kerch_bridge(draw, x, y, w, h):
    """The strait bridge with a broken deck span, for the Crimea lead."""
    draw.rectangle([x, y, x + w, y + h], fill=SKY_WATER)
    water_top = y + h * 0.62
    draw.rectangle([x, water_top, x + w, y + h], fill=(126, 168, 198))
    wave_rows(draw, x + 6, y + h * 0.68, w - 12, h * 0.26)
    deck_y = y + h * 0.55
    draw.line([(x + 4, deck_y), (x + w * 0.42, deck_y)], fill=INK, width=4)
    draw.line([(x + w * 0.58, deck_y), (x + w - 4, deck_y)], fill=INK,
              width=4)
    draw.arc([x + w * 0.3, deck_y - h * 0.34, x + w * 0.7,
              deck_y + h * 0.1], 180, 360, fill=INK, width=5)
    for frac in (0.16, 0.84):
        pier_x = x + w * frac
        draw.rectangle([pier_x - 3, deck_y, pier_x + 3, water_top], fill=INK)
    smoke_puffs(draw, x + w * 0.5, deck_y - h * 0.3, h * 0.1)
    starburst(draw, x + w * 0.5, deck_y - h * 0.08, h * 0.13)


# --- card pictograms ---------------------------------------------------
# One small painter per card story, each working inside its own box and
# drawing no text. The dispatch table at the end maps story id to
# painter, which keeps the card grid code free of long branches.

def icon_drone_over_blast(draw, x, y, w, h):
    draw.rectangle([x, y, x + w, y + h], fill=(233, 223, 201))
    draw.rectangle([x, y + h * 0.74, x + w, y + h], fill=(198, 188, 148))
    cx, cy = x + w * 0.38, y + h * 0.24
    draw.ellipse([cx - 9, cy - 3, cx + 9, cy + 3], fill=INK)
    draw.line([(cx - 15, cy - 5), (cx + 15, cy - 5)], fill=INK, width=2)
    draw.line([(cx, cy - 9), (cx, cy + 5)], fill=INK, width=2)
    for step in range(7):
        t = step / 6
        px = cx + 10 + w * 0.34 * t
        py = cy + 7 + h * 0.32 * t
        draw.ellipse([px - 1.5, py - 1.5, px + 1.5, py + 1.5],
                     fill=SLATE_DARK)
    starburst(draw, x + w * 0.74, y + h * 0.6, h * 0.13)
    smoke_puffs(draw, x + w * 0.74, y + h * 0.42, h * 0.08)


def icon_struck_tower(draw, x, y, w, h):
    draw.rectangle([x, y, x + w, y + h], fill=SKY_WATER)
    base_x = x + w * 0.36
    draw.rectangle([base_x, y + h * 0.18, base_x + w * 0.26, y + h],
                   fill=NAVY)
    for row in range(3):
        wy = y + h * (0.28 + row * 0.2)
        draw.rectangle([base_x + 5, wy, base_x + w * 0.26 - 5,
                        wy + h * 0.1], fill=(255, 214, 120))
    starburst(draw, base_x + w * 0.13, y + h * 0.22, h * 0.2)
    smoke_puffs(draw, base_x + w * 0.13, y + h * 0.05, h * 0.1)


def icon_globe_and_flame(draw, x, y, w, h):
    draw.rectangle([x, y, x + w, y + h], fill=(228, 240, 246))
    cx, cy = x + w * 0.36, y + h * 0.55
    r = min(w, h) * 0.33
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(126, 168, 198),
                 outline=NAVY, width=2)
    draw.ellipse([cx - r * 0.45, cy - r, cx + r * 0.45, cy + r],
                 outline=NAVY)
    draw.line([(cx - r, cy), (cx + r, cy)], fill=NAVY, width=2)
    fx, fy = x + w * 0.76, y + h * 0.55
    outer = [(fx, fy - r * 1.1), (fx + r * 0.5, fy - r * 0.2),
             (fx + r * 0.35, fy + r * 0.5), (fx - r * 0.35, fy + r * 0.5),
             (fx - r * 0.5, fy - r * 0.2)]
    inner = [(fx, fy - r * 0.5), (fx + r * 0.28, fy),
             (fx + r * 0.2, fy + r * 0.4), (fx - r * 0.2, fy + r * 0.4),
             (fx - r * 0.28, fy)]
    draw.polygon(outer, fill=(214, 102, 22))
    draw.polygon(inner, fill=(255, 220, 0))


def icon_parliament_seats(draw, x, y, w, h):
    draw.rectangle([x, y, x + w, y + h], fill=(242, 238, 226))
    cx, cy = x + w / 2, y + h * 0.94
    winning = int(21 * (140 / 237))
    seat_no = 0
    for ring_share in (0.82, 0.6, 0.38):
        for seat in range(7):
            angle = math.pi * (1 - (seat + 0.5) / 7)
            px = cx + ring_share * w * 0.48 * math.cos(angle)
            py = cy - ring_share * h * 0.88 * math.sin(angle)
            tone = NAVY if seat_no < winning else (208, 208, 198)
            draw.ellipse([px - 5, py - 5, px + 5, py + 5], fill=tone)
            seat_no += 1


def icon_atom_orbits(draw, x, y, w, h):
    draw.rectangle([x, y, x + w, y + h], fill=(26, 40, 66))
    cx, cy = x + w / 2, y + h / 2
    for degrees in (0, 60, 120):
        angle = math.radians(degrees)
        orbit = []
        for k in range(37):
            t = 2 * math.pi * k / 36
            ex = w * 0.32 * math.cos(t)
            ey = h * 0.17 * math.sin(t)
            orbit.append((cx + ex * math.cos(angle) - ey * math.sin(angle),
                          cy + ex * math.sin(angle) + ey * math.cos(angle)))
        draw.line(orbit, fill=(255, 214, 120), width=2)
    draw.ellipse([cx - 6, cy - 6, cx + 6, cy + 6], fill=RED)


def icon_drought_sun(draw, x, y, w, h):
    draw.rectangle([x, y, x + w, y + h], fill=(250, 231, 182))
    cx, cy = x + w * 0.32, y + h * 0.38
    draw.ellipse([cx - 13, cy - 13, cx + 13, cy + 13], fill=(206, 104, 18))
    for k in range(8):
        a = k * math.pi / 4
        draw.line([(cx + 17 * math.cos(a), cy + 17 * math.sin(a)),
                   (cx + 23 * math.cos(a), cy + 23 * math.sin(a))],
                  fill=(206, 104, 18), width=3)
    ground_y = y + h * 0.82
    draw.line([(x + 6, ground_y), (x + w - 6, ground_y)],
              fill=(150, 100, 40), width=3)
    draw.line([(x + w * 0.55, ground_y), (x + w * 0.62, y + h * 0.94)],
              fill=(150, 100, 40), width=2)
    draw.line([(x + w * 0.7, ground_y), (x + w * 0.66, y + h * 0.94)],
              fill=(150, 100, 40), width=2)


def icon_framed_canvas(draw, x, y, w, h):
    draw.rectangle([x, y, x + w, y + h], fill=(54, 42, 32))
    draw.rectangle([x + w * 0.22, y + h * 0.14, x + w * 0.78, y + h * 0.86],
                   fill=(246, 239, 212), outline=GOLD, width=3)
    draw.ellipse([x + w * 0.36, y + h * 0.28, x + w * 0.52, y + h * 0.48],
                 fill=(255, 200, 60))
    draw.arc([x + w * 0.3, y + h * 0.3, x + w * 0.72, y + h * 0.8],
             200, 340, fill=(70, 110, 180), width=3)
    draw.arc([x + w * 0.34, y + h * 0.4, x + w * 0.68, y + h * 0.84],
             200, 340, fill=RED, width=3)


def icon_rising_bars(draw, x, y, w, h):
    draw.rectangle([x, y, x + w, y + h], fill=WHITE)
    heights = (0.3, 0.48, 0.42, 0.72, 1.0)
    gap = w * 0.07
    bar_w = (w - gap * 6) / len(heights)
    base = y + h * 0.86
    for idx, share in enumerate(heights):
        bx = x + gap + idx * (bar_w + gap)
        draw.rectangle([bx, base - share * h * 0.62, bx + bar_w, base],
                       fill=(44, 108, 64))
    draw.line([(x + gap, base), (x + w - gap, base)], fill=INK, width=2)
    draw.line([(x + gap, y + h * 0.3), (x + w - gap * 2, y + h * 0.14)],
              fill=RED, width=3)


def icon_balance_scales(draw, x, y, w, h):
    draw.rectangle([x, y, x + w, y + h], fill=PALE_CARD)
    cx = x + w / 2
    draw.line([(cx, y + h * 0.14), (cx, y + h * 0.8)], fill=INK, width=3)
    draw.line([(cx - w * 0.3, y + h * 0.24), (cx + w * 0.3, y + h * 0.24)],
              fill=INK, width=3)
    for sign in (-1, 1):
        px = cx + sign * w * 0.3
        draw.polygon([(px, y + h * 0.24), (px - 12, y + h * 0.52),
                      (px + 12, y + h * 0.52)], outline=INK)
        draw.arc([px - 13, y + h * 0.44, px + 13, y + h * 0.62], 0, 180,
                 fill=GOLD, width=3)
    draw.rectangle([cx - 14, y + h * 0.8, cx + 14, y + h * 0.88], fill=INK)


def icon_flag_and_blocks(draw, x, y, w, h):
    draw.rectangle([x, y, x + w, y + h], fill=SKY_WATER)
    pole_x = x + w * 0.3
    draw.line([(pole_x, y + h * 0.1), (pole_x, y + h * 0.92)], fill=INK,
              width=3)
    draw.polygon([(pole_x, y + h * 0.1), (x + w * 0.78, y + h * 0.2),
                  (pole_x, y + h * 0.34)], fill=RED)
    draw.rectangle([x + w * 0.55, y + h * 0.55, x + w * 0.9, y + h * 0.92],
                   fill=NAVY)
    draw.rectangle([x + w * 0.1, y + h * 0.62, x + w * 0.42, y + h * 0.92],
                   fill=(12, 112, 114))


CARD_ICONS = {
    4: icon_drone_over_blast,
    5: icon_struck_tower,
    6: icon_globe_and_flame,
    7: icon_parliament_seats,
    8: icon_atom_orbits,
    9: icon_drought_sun,
    10: icon_framed_canvas,
    11: icon_rising_bars,
    12: icon_balance_scales,
    13: icon_flag_and_blocks,
}


# --- page assembly -----------------------------------------------------

def paint_masthead(draw, data):
    draw.rectangle([0, 0, PAGE_W, 80], fill=NAVY)
    draw.rectangle([0, 80, PAGE_W, 83], fill=GOLD)
    draw.text((MARGIN, 9), "The World in One Page",
              font=get_font("serif-bold", 38), fill=WHITE)
    subtitle = data["date_label"] + " - 40 stories, one image"
    draw.text((MARGIN, 54), subtitle, font=get_font("sans-bold", 13),
              fill=GOLD)
    draw.text((PAGE_W - MARGIN - 118, 14), "19 Nov",
              font=get_font("serif-bold", 30), fill=WHITE)
    draw.text((PAGE_W - MARGIN - 118, 50), "2026",
              font=get_font("sans-bold", 13), fill=GOLD)


def paint_region_strip(draw, stories):
    tally = {}
    for story in stories:
        tally[story["region"]] = tally.get(story["region"], 0) + 1
    chip_font = get_font("sans-bold", 11)
    x = MARGIN
    y = 88
    order = ["Asia", "Europe", "Middle East", "Americas", "Africa",
             "Oceania", "Global"]
    for region in order:
        if region not in tally:
            continue
        label = region + " " + str(tally[region])
        width = draw.textlength(label, font=chip_font)
        draw.rectangle([x, y, x + width + 16, y + 22],
                       fill=REGION_TINT[region])
        draw.text((x + 8, y + 4), label, font=chip_font, fill=WHITE)
        x += width + 24


def paint_leads(draw, leads):
    top, height = 118, 190
    first, second, third = leads[0], leads[1], leads[2]

    scene_box = (MARGIN, top, 640, 128)
    draw.rectangle([MARGIN, top, 664, top + height], fill=NAVY_DEEP)
    scene_shenzhen_skyline(draw, *scene_box)
    draw.text((36, top + 134), "1 Shenzhen summit",
              font=get_font("sans-bold", 15), fill=GOLD)
    caption = first["headline"] + " - " + first["summary"]
    caption_lines = fold_text(draw, caption, get_font("sans", 11), 616,
                              limit=2)
    stack_lines(draw, caption_lines, 36, top + 156, get_font("sans", 11),
                MIST, 14)

    draw.rectangle([676, top, 1000, top + 91], fill=PALE_CARD,
                   outline=CARD_LINE, width=BORDER_W)
    scene_court_gavel(draw, 676, top, 118, 91)
    draw.text((806, top + 7), "2 World Court",
              font=get_font("sans-bold", 12), fill=RED)
    court_lines = fold_text(draw, second["headline"],
                            get_font("sans-bold", 11), 182, limit=4)
    stack_lines(draw, court_lines, 806, top + 25,
                get_font("sans-bold", 11), INK, 14)

    draw.rectangle([676, top + 99, 1000, top + height], fill=SKY_WATER,
                   outline=CARD_LINE, width=BORDER_W)
    scene_kerch_bridge(draw, 676, top + 99, 118, 91)
    draw.text((806, top + 106), "3 Crimea Bridge",
              font=get_font("sans-bold", 12), fill=NAVY)
    bridge_lines = fold_text(draw, third["headline"],
                             get_font("sans-bold", 11), 182, limit=4)
    stack_lines(draw, bridge_lines, 806, top + 124,
                get_font("sans-bold", 11), INK, 14)


def paint_map(draw, leads, cards, also):
    top, height = 316, 240
    draw.rectangle([MARGIN, top, 1000, top + height], fill=SKY_WATER,
                   outline=NAVY, width=BORDER_W)
    draw.text((36, top + 6), "Where it happened - pins 1-13, dots for the rest",
              font=get_font("sans-bold", 12), fill=NAVY)
    project = paint_landmasses(draw, (36, top + 30, 988, top + height - 10))
    paint_pins(draw, project, leads + cards, also)


def paint_cards(draw, cards):
    grid_top = 564
    card_w, card_h, gap = 188, 91, 8
    headline_font = get_font("sans-bold", 10)
    short_font = get_font("sans", 8)
    for idx, story in enumerate(cards):
        left = MARGIN + (idx % 5) * (card_w + gap)
        top = grid_top + (idx // 5) * (card_h + gap)
        draw.rectangle([left, top, left + card_w, top + card_h], fill=WHITE,
                       outline=CARD_LINE, width=BORDER_W)
        painter = CARD_ICONS.get(story["id"])
        if painter is not None:
            painter(draw, left + 5, top + 5, 54, 81)
        text_x = left + 65
        place_name = story["place"].split(",")[0]
        kicker = str(story["id"]) + " " + place_name
        draw.text((text_x, top + 5), kicker, font=get_font("sans-bold", 8),
                  fill=REGION_TINT.get(story["region"], SLATE_DARK))
        head_lines = fold_text(draw, story["headline"], headline_font,
                               card_w - 72, limit=3)
        y = stack_lines(draw, head_lines, text_x, top + 18, headline_font,
                        INK, 12)
        room = top + card_h - 5 - y
        allowed = 2 if room >= 21 else 1 if room >= 11 else 0
        if allowed:
            short_text = story.get("short") or story["summary"]
            short_lines = fold_text(draw, short_text, short_font,
                                    card_w - 72, limit=allowed)
            stack_lines(draw, short_lines, text_x, y + 1, short_font,
                        SLATE_DARK, 10)


def paint_also_list(draw, also):
    top = 762
    draw.rectangle([MARGIN, top, 1000, 982], fill=NAVY)
    draw.rectangle([MARGIN + 4, top + 4, 996, 978], outline=GOLD,
                   width=1)
    draw.text((36, top + 8), "Also on 19 November",
              font=get_font("sans-bold", 13), fill=GOLD)
    body_font = get_font("sans", 9)
    column_w = 312
    per_column = 9
    leading = 12
    item_gap = 5
    # Measure every column before painting anything: with the wider
    # leading the three columns nearly fill the box, and whatever
    # slack remains is split evenly above and below the tallest
    # column, so the whole block sits centred in the box instead of
    # hugging its top edge and leaving an empty band at the bottom.
    columns = []
    for column in range(3):
        batch = also[column * per_column:(column + 1) * per_column]
        wrapped = []
        height = 0
        for story in batch:
            entry = str(story["id"]) + ". " + story["headline"]
            lines = fold_text(draw, entry, body_font, column_w, limit=2)
            wrapped.append(lines)
            height += len(lines) * leading + item_gap
        columns.append((wrapped, height - item_gap))
    tallest = max(height for _, height in columns)
    area_top = top + 34
    area_bottom = 982 - 10
    slack = max(0, (area_bottom - area_top) - tallest)
    for column, (wrapped, _) in enumerate(columns):
        x = 36 + column * (column_w + 12)
        y = area_top + slack // 2
        for lines in wrapped:
            for line in lines:
                draw.text((x, y), line, font=body_font, fill=MIST)
                y += leading
            y += item_gap


def paint_footer(draw):
    note_font = get_font("sans", 9)
    sources_line = (
        "Sources: Reuters, AP, AFP, BBC, Al Jazeera, UN News, IAEA, ICJ, "
        "Save the Children, Copernicus. Each key fact checked against at "
        "least two sources; disputed claims attributed."
    )
    draw.text((MARGIN, 990), sources_line, font=note_font, fill=SLATE_DARK)
    method_line = (
        "Drawn entirely in code with Pillow. No network at run time. "
        "Deterministic: same input, same PNG."
    )
    draw.text((MARGIN, 1004), method_line, font=note_font, fill=SLATE_DARK)


def build_page(data):
    """Assemble the full page image from the loaded story data."""
    stories = data["stories"]
    by_tier = {"lead": [], "card": [], "also": []}
    for story in stories:
        by_tier[story["tier"]].append(story)
    page = Image.new("RGB", (PAGE_W, PAGE_H), PAPER)
    draw = ImageDraw.Draw(page)
    paint_masthead(draw, data)
    paint_region_strip(draw, stories)
    paint_leads(draw, by_tier["lead"])
    paint_map(draw, by_tier["lead"], by_tier["card"], by_tier["also"])
    paint_cards(draw, by_tier["card"])
    paint_also_list(draw, by_tier["also"])
    paint_footer(draw)
    return page


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(here, "stories.json")
    with open(data_path, encoding="utf-8") as handle:
        data = json.load(handle)
    page = build_page(data)
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    target = os.path.join(out_dir, "entry.png")
    page.save(target, format="PNG", optimize=False)
    print("wrote", target)


if __name__ == "__main__":
    main()
