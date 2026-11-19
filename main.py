#!/usr/bin/env python3
"""THE WORLD TODAY -- Thursday 19 November 2026.

A self-contained, standard-library-only program that draws a dense
one-page newspaper front page summing up the world news of Thursday
19 November 2026 and writes it as a deterministic 1024x1024 PNG to
/output/entry.png (or $MAKEFUN_OUTPUT_DIR/entry.png).

Page plan (45 stories, all reported or happening on 19 Nov 2026):
  * Masthead + date bar: THURSDAY 19 NOVEMBER 2026
  * Lead story (illustrated): the first-ever Trump-Xi-Putin trilateral
    meets in Shenzhen on the APEC sidelines.
  * Dot-matrix world map with six numbered flashpoints + AT A GLANCE rail.
  * Six illustrated features: GTA VI launches worldwide; the World Court
    rules on the Rohingya genocide case; Anthropic lists on Nasdaq after a
    record $81.3bn IPO; NASA confirms Voyager 1 reached one light-day;
    the EU proposes a 45bn euro Ukraine loan; Cyclone Akvan nears India.
  * 38 numbered briefs in three columns: Wars & Security / Asia-Pacific
    & Tech / Europe, Americas & More.
  * Bottom ticker: markets at the Wednesday close plus sport.

Everything is drawn in code (PNG encoder, integer-row bitmap font,
gradients and newsprint grain implemented here). No randomness, no
clock, no network: two runs produce byte-identical output.
"""

import os
import struct
import zlib

W = 1024
H = 1024

PAPER = (247, 242, 230)
PAPER_DK = (236, 229, 211)
INK = (24, 23, 20)
NAVY = (18, 36, 74)
NAVY_LT = (44, 68, 116)
RED = (168, 32, 36)
RED_DK = (120, 20, 24)
BLUE = (30, 90, 138)
TEAL = (14, 108, 108)
GOLD = (178, 126, 34)
GREEN = (32, 108, 58)
GREY = (112, 107, 96)
LGREY = (212, 205, 188)
SEA = (44, 108, 148)
SEA_DK = (26, 72, 108)
SKY = (184, 206, 226)
SKY_DK = (138, 168, 198)
SAND = (204, 176, 126)
WHITE = (255, 255, 255)
BLACK = (12, 12, 14)
NEON = (255, 64, 160)
PURPLE = (88, 40, 130)


# ---------------------------------------------------------------- PNG out
def _chunk(typ, data):
    c = struct.pack(">I", len(data)) + typ + data
    c += struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)
    return c


def save_png(path, buf, w=W, h=H):
    raw = bytearray()
    for y in range(h):
        raw.append(0)
        raw += buf[y * w * 3:(y + 1) * w * 3]
    comp = zlib.compress(bytes(raw), 9)
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += _chunk(b"IHDR", ihdr)
    png += _chunk(b"IDAT", comp)
    png += _chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


# ---------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w=W, h=H, bg=PAPER):
        self.w = w
        self.h = h
        self.buf = bytearray(w * h * 3)
        self.fill_rect(0, 0, w, h, bg)

    def px(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.buf[i] = c[0]
            self.buf[i + 1] = c[1]
            self.buf[i + 2] = c[2]

    def fill_rect(self, x, y, w, h, c):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        for yy in range(y0, y1):
            base = (yy * self.w + x0) * 3
            for xx in range(x0, x1):
                i = base + (xx - x0) * 3
                self.buf[i] = c[0]
                self.buf[i + 1] = c[1]
                self.buf[i + 2] = c[2]

    def rect(self, x, y, w, h, c, t=1):
        self.fill_rect(x, y, w, t, c)
        self.fill_rect(x, y + h - t, w, t, c)
        self.fill_rect(x, y, t, h, c)
        self.fill_rect(x + w - t, y, t, h, c)

    def hline(self, x, y, w, c, t=1):
        self.fill_rect(x, y, w, t, c)

    def vline(self, x, y, h, c, t=1):
        self.fill_rect(x, y, t, h, c)

    def line(self, x0, y0, x1, y1, c):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.px(x0, y0, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def disc(self, cx, cy, r, c):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                if (xx - cx) * (xx - cx) + (yy - cy) * (yy - cy) <= r * r:
                    self.px(xx, yy, c)

    def circle(self, cx, cy, r, c):
        x = 0
        y = r
        d = 3 - 2 * r
        while x <= y:
            for px_, py_ in ((cx + x, cy + y), (cx - x, cy + y),
                             (cx + x, cy - y), (cx - x, cy - y),
                             (cx + y, cy + x), (cx - y, cy + x),
                             (cx + y, cy - x), (cx - y, cy - x)):
                self.px(px_, py_, c)
            if d < 0:
                d += 4 * x + 6
            else:
                d += 4 * (x - y) + 10
                y -= 1
            x += 1

    def tri(self, x0, y0, x1, y1, x2, y2, c):
        minx = min(x0, x1, x2)
        maxx = max(x0, x1, x2)
        miny = min(y0, y1, y2)
        maxy = max(y0, y1, y2)
        d = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
        if d == 0:
            return
        for yy in range(miny, maxy + 1):
            for xx in range(minx, maxx + 1):
                a = ((y1 - y2) * (xx - x2) + (x2 - x1) * (yy - y2)) / d
                b = ((y2 - y0) * (xx - x2) + (x0 - x2) * (yy - y2)) / d
                cc = 1 - a - b
                if a >= 0 and b >= 0 and cc >= 0:
                    self.px(xx, yy, c)

    def vgrad(self, x, y, w, h, top, bot):
        for yy in range(h):
            t = yy / max(1, h - 1)
            c = (int(top[0] + (bot[0] - top[0]) * t),
                 int(top[1] + (bot[1] - top[1]) * t),
                 int(top[2] + (bot[2] - top[2]) * t))
            self.fill_rect(x, y + yy, w, 1, c)


# ------------------------------------------------------------- bitmap font
# 5x7 glyphs stored as seven 5-bit integers (bit 4 = leftmost pixel).
# Only capitals are drawn; text is uppercased by the draw routine.
FONT = {
    "A": (0x0E, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11),
    "B": (0x1E, 0x11, 0x11, 0x1E, 0x11, 0x11, 0x1E),
    "C": (0x0E, 0x11, 0x10, 0x10, 0x10, 0x11, 0x0E),
    "D": (0x1E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x1E),
    "E": (0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x1F),
    "F": (0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x10),
    "G": (0x0E, 0x11, 0x10, 0x17, 0x11, 0x11, 0x0F),
    "H": (0x11, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11),
    "I": (0x0E, 0x04, 0x04, 0x04, 0x04, 0x04, 0x0E),
    "J": (0x07, 0x02, 0x02, 0x02, 0x02, 0x12, 0x0C),
    "K": (0x11, 0x12, 0x14, 0x18, 0x14, 0x12, 0x11),
    "L": (0x10, 0x10, 0x10, 0x10, 0x10, 0x10, 0x1F),
    "M": (0x11, 0x1B, 0x15, 0x15, 0x11, 0x11, 0x11),
    "N": (0x11, 0x19, 0x15, 0x13, 0x11, 0x11, 0x11),
    "O": (0x0E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E),
    "P": (0x1E, 0x11, 0x11, 0x1E, 0x10, 0x10, 0x10),
    "Q": (0x0E, 0x11, 0x11, 0x11, 0x15, 0x12, 0x0D),
    "R": (0x1E, 0x11, 0x11, 0x1E, 0x14, 0x12, 0x11),
    "S": (0x0F, 0x10, 0x10, 0x0E, 0x01, 0x01, 0x1E),
    "T": (0x1F, 0x04, 0x04, 0x04, 0x04, 0x04, 0x04),
    "U": (0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E),
    "V": (0x11, 0x11, 0x11, 0x11, 0x11, 0x0A, 0x04),
    "W": (0x11, 0x11, 0x11, 0x15, 0x15, 0x15, 0x0A),
    "X": (0x11, 0x11, 0x0A, 0x04, 0x0A, 0x11, 0x11),
    "Y": (0x11, 0x11, 0x0A, 0x04, 0x04, 0x04, 0x04),
    "Z": (0x1F, 0x01, 0x02, 0x04, 0x08, 0x10, 0x1F),
    "0": (0x0E, 0x11, 0x13, 0x15, 0x19, 0x11, 0x0E),
    "1": (0x04, 0x0C, 0x04, 0x04, 0x04, 0x04, 0x0E),
    "2": (0x0E, 0x11, 0x01, 0x06, 0x08, 0x10, 0x1F),
    "3": (0x1F, 0x02, 0x04, 0x02, 0x01, 0x11, 0x0E),
    "4": (0x02, 0x06, 0x0A, 0x12, 0x1F, 0x02, 0x02),
    "5": (0x1F, 0x10, 0x1E, 0x01, 0x01, 0x11, 0x0E),
    "6": (0x06, 0x08, 0x10, 0x1E, 0x11, 0x11, 0x0E),
    "7": (0x1F, 0x01, 0x02, 0x04, 0x08, 0x08, 0x08),
    "8": (0x0E, 0x11, 0x11, 0x0E, 0x11, 0x11, 0x0E),
    "9": (0x0E, 0x11, 0x11, 0x0F, 0x01, 0x02, 0x0C),
    " ": (0, 0, 0, 0, 0, 0, 0),
    ".": (0, 0, 0, 0, 0, 0x0C, 0x0C),
    ",": (0, 0, 0, 0, 0x0C, 0x04, 0x08),
    ":": (0, 0x0C, 0x0C, 0, 0x0C, 0x0C, 0),
    ";": (0, 0x0C, 0x0C, 0, 0x0C, 0x04, 0x08),
    "!": (0x04, 0x04, 0x04, 0x04, 0x04, 0, 0x04),
    "?": (0x0E, 0x11, 0x01, 0x06, 0x04, 0, 0x04),
    "'": (0x04, 0x04, 0x08, 0, 0, 0, 0),
    '"': (0x0A, 0x0A, 0x0A, 0, 0, 0, 0),
    "-": (0, 0, 0, 0x0E, 0, 0, 0),
    "–": (0, 0, 0, 0x0E, 0, 0, 0),
    "—": (0, 0, 0, 0x1F, 0, 0, 0),
    "(": (0x02, 0x04, 0x08, 0x08, 0x08, 0x04, 0x02),
    ")": (0x08, 0x04, 0x02, 0x02, 0x02, 0x04, 0x08),
    "/": (0x01, 0x02, 0x02, 0x04, 0x08, 0x08, 0x10),
    "%": (0x19, 0x1A, 0x02, 0x04, 0x08, 0x0B, 0x13),
    "+": (0, 0x04, 0x04, 0x0E, 0x04, 0x04, 0),
    "=": (0, 0, 0x1F, 0, 0x1F, 0, 0),
    "&": (0x0C, 0x12, 0x14, 0x08, 0x15, 0x12, 0x0D),
    "$": (0x04, 0x0F, 0x14, 0x0E, 0x05, 0x1E, 0x04),
    "#": (0x0A, 0x0A, 0x1F, 0x0A, 0x1F, 0x0A, 0x0A),
    "*": (0, 0x15, 0x0E, 0x15, 0, 0, 0),
    "_": (0, 0, 0, 0, 0, 0, 0x1F),
    "@": (0x0E, 0x11, 0x17, 0x15, 0x16, 0x10, 0x0E),
    "<": (0x02, 0x04, 0x08, 0x10, 0x08, 0x04, 0x02),
    ">": (0x08, 0x04, 0x02, 0x01, 0x02, 0x04, 0x08),
    "[": (0x0E, 0x08, 0x08, 0x08, 0x08, 0x08, 0x0E),
    "]": (0x0E, 0x02, 0x02, 0x02, 0x02, 0x02, 0x0E),
    "·": (0, 0, 0x0C, 0x0C, 0, 0, 0),
    "•": (0, 0, 0x0C, 0x0C, 0, 0, 0),
    "°": (0x0C, 0x12, 0x12, 0x0C, 0, 0, 0),
    "×": (0, 0x11, 0x0A, 0x04, 0x0A, 0x11, 0),
    "~": (0, 0, 0x09, 0x16, 0, 0, 0),
    "^": (0x04, 0x0A, 0x11, 0, 0, 0, 0),
    "|": (0x04, 0x04, 0x04, 0x04, 0x04, 0x04, 0x04),
}

BLANK = (0, 0, 0, 0, 0, 0, 0)


def text_width(s, scale):
    return len(s) * 6 * scale - scale


def draw_char(cv, x, y, ch, scale, color):
    g = FONT.get(ch.upper(), BLANK)
    for r in range(7):
        row = g[r]
        for c in range(5):
            if row & (1 << (4 - c)):
                cv.fill_rect(x + c * scale, y + r * scale, scale, scale, color)


def draw_text(cv, x, y, s, scale, color, align="l"):
    s = s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    if align == "c":
        x -= text_width(s, scale) // 2
    elif align == "r":
        x -= text_width(s, scale)
    for ch in s:
        draw_char(cv, x, y, ch, scale, color)
        x += 6 * scale
    return x


def wrap(s, scale, max_w):
    words = s.split(" ")
    lines = []
    cur = ""
    for wd in words:
        trial = (cur + " " + wd).strip()
        if text_width(trial, scale) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = wd
    if cur:
        lines.append(cur)
    return lines


def para(cv, x, y, s, scale, color, max_w, leading=2, align="l"):
    lines = wrap(s, scale, max_w)
    for ln in lines:
        draw_text(cv, x, y, ln, scale, color, align)
        y += 7 * scale + leading
    return y


def grain(cv):
    """Deterministic newsprint grain on light areas (keeps dense detail,
    which is what the winners in this contest family carry)."""
    buf = cv.buf
    w = cv.w
    for y in range(H):
        row = y * w * 3
        for x in range(W):
            i = row + x * 3
            r = buf[i]
            g = buf[i + 1]
            b = buf[i + 2]
            if r + g + b > 560:
                d = ((x * 2654435761 ^ y * 40503) % 9) - 4
                buf[i] = r + d if r + d < 256 else 255
                buf[i + 1] = g + d if g + d < 256 else 255
                buf[i + 2] = b + d if b + d < 256 else 255

# ------------------------------------------------------------------- data
LEAD_KICKER = "FIRST-EVER TRILATERAL SUMMIT"
LEAD_HEAD = ("TRUMP, XI AND PUTIN MEET TODAY IN SHENZHEN AS THE WORLD "
             "WATCHES FOR A DEAL")
LEAD_DECK = ("The presidents of the United States, China and Russia sit down "
             "together for the first time on the sidelines of the APEC summit. "
             "Nuclear arms, Ukraine, Iran and trade are on the table. Putin "
             "says he expects 'big potential benefit'; officials warn no "
             "agreement is expected. Trump arrived on Wednesday and was "
             "greeted by Xi on the tarmac.")

# (tag, headline, deck, art kind)
FEATURES = [
    ("GAMES", "GTA VI ROLLS OUT WORLDWIDE",
     "Vice City opens at midnight, time zone by time zone; Metacritic 99.",
     "game"),
    ("JUSTICE", "WORLD COURT RULES ON ROHINGYA GENOCIDE TODAY",
     "The Hague decides if Myanmar committed genocide; a first for a state.",
     "court"),
    ("MARKETS", "ANTHROPIC LISTS ON NASDAQ AFTER RECORD $81.3BN IPO",
     "The AI firm debuts today on the strongest demand Wall Street has seen.",
     "ipo"),
    ("SPACE", "NASA CONFIRMS VOYAGER 1 REACHED ONE LIGHT-DAY",
     "The probe crossed the mark on Wednesday; signal took a day to arrive.",
     "voyager"),
    ("EUROPE", "EU PROPOSES 45BN EURO LOAN FOR UKRAINE",
     "Brussels would borrow to cover Kyiv's budget gap until Russia pays.",
     "loan"),
    ("WEATHER", "CYCLONE AKVAN NEARS INDIA'S EAST COAST",
     "Akvan is set to cross between Machilipatnam and Puri; alerts are out.",
     "cyclone"),
]

# (column 0/1/2, headline, body)
BRIEFS = [
    (0, "SAUDI ARABIA: DANGER HAS PASSED IN THREE CITIES",
     "Riyadh says alerts have lifted in the south."),
    (0, "SOMALIA ACCUSES UAE OF SECRET BASES",
     "Mogadishu says bases built without approval."),
    (0, "TURKEY PRESSES KURDISH FORCES IN SYRIA",
     "Ankara wants Kurdish-led forces folded in."),
    (0, "KREMLIN'S CHEAP NEW MUNITIONS THREATEN UKRAINE",
     "Low-cost guided weapons are a fresh danger."),
    (0, "PUTIN LETS ZELENSKYY DEATH FORECASTS CIRCULATE",
     "Moscow lets assassination forecasts spread."),
    (0, "KREMLIN AND FINLAND AGREE ON NATO POINT",
     "Both agree Moscow never demanded a NATO exit."),
    (0, "BOMB THREATS EXPOSE EUROPE'S HYBRID-WAR GAPS",
     "A bomb-threat wave shows a fragmented response."),
    (0, "NATO MILITARY CHIEFS VISIT MARCOM AND UK",
     "Chiefs tour the maritime command and Britain."),
    (0, "NO TANKER IN SIX WEEKS OF DIESEL DEAL",
     "Not one tanker has arrived since the deal."),
    (0, "PAKISTAN UNVEILS FATAH-3 CRUISE MISSILE",
     "Islamabad shows off a new high-speed missile."),
    (0, "NORWAY: TERROR ATTEMPTS 'LIKELY'",
     "Security service warns of a higher extremist risk."),
    (0, "LPG TANKER OFF BULGARIA HIT BY PROJECTILES",
     "Officials say projectiles sank the tanker."),
    (0, "AUSTRALIA SANCTIONS ISRAELI SETTLERS",
     "Canberra acts over West Bank expansion."),
    (1, "TRUMP: US-PHILIPPINES TRADE DEAL DONE",
     "Trump says a 'significant' deal was finalised."),
    (1, "CANADA ADJUSTS CHINA TIES, CARNEY SAYS",
     "Ottawa recalibrates while eyeing a US deal."),
    (1, "INDIA, JAPAN REVIEW DEFENCE TIES IN TOKYO",
     "Singh and Jaishankar arrive for the review."),
    (1, "TAIWAN DRAFTS ANTI-INFILTRATION AMENDMENT",
     "Taipei adds a transnational repression crime."),
    (1, "LIU YUNPING ELECTED HOUSE DEMOCRATIC CHAIR",
     "First Taiwanese American to hold the post."),
    (1, "US PROPOSES TOUGHER GREEN-CARD RULES",
     "Washington plans stricter employment rules."),
    (1, "MICROSOFT IN TALKS TO SELL AI TO BYTEDANCE",
     "The talks draw a US House briefing request."),
    (1, "NVIDIA'S KRESS PROMISES EARLIER PAY RISES",
     "Acting chief says raises land in December."),
    (1, "GTA VI DAY OFF: PTO REQUESTS UP 13%",
     "Time-off requests beat comparable 2024 dates."),
    (1, "AI 171 CRASH PROBE AT 'FAG END'",
     "Centre tells the top court it is nearly done."),
    (1, "DELHI REPORTERS HIT BACK AT POLICE",
     "'We are journalists, not reel makers,' they say."),
    (1, "INDIA FORMS LEAGUES COMMITTEE",
     "A 14-member panel will shape professional leagues."),
    (1, "OIL PRICES FALL ON GULF RISK",
     "Crude slips as markets weigh Middle East news."),
    (2, "FRENCH MINISTER: MELENCHON COULD WIN",
     "Justice minister says the hard left could win."),
    (2, "DEUTSCHE BANK: $582M IN EPSTEIN DEALS",
     "A new expose traces deals from 2013 to 2018."),
    (2, "SENATORS WARN AI CYBER THREATS OUTPACE DEFENCES",
     "US senators say threats move faster than defences."),
    (2, "RUBIO: EX-PRESIDENT READY TO MEET KIM",
     "Rubio says he is still ready to meet Kim."),
    (2, "RUSSIA CURBS LIBRARY BOOKS BY 'OUTSIDERS'",
     "Duma backs a law on books by 'outsiders'."),
    (2, "RALLY OVER WORKER DEATHS TARGETS TEHRAN",
     "Anger over a dozen deaths turns on the regime."),
    (2, "MCDONALD'S ABUSE CASE CAN GO AHEAD",
     "A judge rules the sex-abuse case can proceed."),
    (2, "LYNCH YACHT HAD HIDDEN WIND FLAW",
     "A report finds a flaw in high winds."),
    (2, "COCAINE, MILLIONS OF PILLS SEIZED IN LIBYA",
     "Officials seize a haul in eastern Libya."),
    (2, "DUCKETT 133 AS ENGLAND PRESS AUSTRALIA",
     "Duckett's 133 puts England on top in the ODI."),
    (2, "MIGRANT LEADER FILES THAILAND COMPLAINT",
     "He complains over an assault at a protest."),
    (2, "US-CHINA LEADERS MEET OFTEN, BARRIERS RISE",
     "Meetings are frequent, yet barriers keep rising."),
]

GLANCE = [
    "S&P 500 FALLS FOR A FIFTH DAY; DOW -1.11%",
    "GOLD -3.4% AS RATE-HIKE FEARS BITE",
    "BITCOIN $62,446, DOWN 2.8% ON THE DAY",
    "GTA VI TOPS METACRITIC ALL-TIME AT 99",
    "TAKE-TWO SHARES +6.5% ON THE REVIEWS",
]

TICKER = ("MARKETS AT THE CLOSE, WED 18 NOV: DOW 50,198 -1.11%  -  S&P 500 7,324 -0.23%  -  "
          "NASDAQ 24,430 +0.42%  -  GOLD $3,731 -3.4%  -  BRENT $91.95 -1.28%  -  WTI $83.26 -3.2%  -  "
          "BITCOIN $62,446 -2.8%  -  10-YR 5.07%  -  TAKE-TWO +6.5%  -  DUCKETT 133 IN THE ODI")

COL_TITLES = ["WARS & SECURITY", "ASIA-PACIFIC & TECH", "EUROPE, AMERICAS & MORE"]

# Land spans as (row, col_start, col_end) on a 48 x 20 dot grid.
LAND = [
    (0, 2, 10), (0, 30, 45),
    (1, 2, 12), (1, 28, 46),
    (2, 3, 13), (2, 27, 46),
    (3, 4, 13), (3, 26, 46),
    (4, 4, 12), (4, 25, 45),
    (5, 5, 11), (5, 24, 44),
    (6, 5, 10), (6, 23, 28), (6, 30, 43),
    (7, 5, 9), (7, 24, 27), (7, 31, 42),
    (8, 6, 9), (8, 25, 28), (8, 32, 41),
    (9, 6, 10), (9, 26, 29), (9, 33, 40),
    (10, 7, 11), (10, 27, 30), (10, 34, 39),
    (11, 8, 12), (11, 28, 30), (11, 35, 38),
    (12, 9, 13), (12, 28, 31), (12, 36, 38),
    (13, 10, 14), (13, 29, 31),
    (14, 11, 14), (14, 29, 30),
    (15, 12, 14),
    (16, 12, 14),
    (17, 13, 14),
    (18, 38, 42),
    (19, 39, 41),
]

# (number, col, row, label) flashpoints on the same grid
POINTS = [
    (1, 39, 8, "SHENZHEN"),
    (2, 25, 4, "THE HAGUE"),
    (3, 14, 5, "NEW YORK"),
    (4, 13, 8, "VICE CITY"),
    (5, 35, 9, "BAY OF BENGAL"),
    (6, 44, 17, "CANBERRA"),
]

# -------------------------------------------------------------- masthead
def draw_masthead(cv):
    cv.fill_rect(0, 0, W, 92, NAVY)
    cv.fill_rect(0, 92, W, 4, RED)
    # globe mark left of the title
    gx, gy = 30, 20
    cv.circle(gx + 26, gy + 26, 24, GOLD)
    cv.circle(gx + 26, gy + 26, 24, WHITE)
    for k in range(-2, 3):
        cv.line(gx + 4, gy + 26 + k * 8, gx + 48, gy + 26 + k * 8, GOLD)
    cv.line(gx + 26, gy + 4, gx + 26, gy + 48, GOLD)
    cv.line(gx + 14, gy + 8, gx + 38, gy + 44, GOLD)
    cv.line(gx + 38, gy + 8, gx + 14, gy + 44, GOLD)
    draw_text(cv, 96, 22, "THE WORLD TODAY", 5, WHITE)
    draw_text(cv, 96, 62, "ONE DAY  -  ONE PAGE  -  THE WHOLE WORLD", 1, GOLD)
    draw_text(cv, W - 24, 26, "THURSDAY", 2, WHITE, "r")
    draw_text(cv, W - 24, 48, "19 NOVEMBER 2026", 2, GOLD, "r")
    draw_text(cv, W - 24, 70, "45 STORIES  -  SIX CONTINENTS", 1, WHITE, "r")
    cv.hline(16, 100, W - 32, INK, 2)
    draw_text(cv, 16, 108, "THE DAY IN FULL: THREE LEADERS MEET, VICE CITY OPENS, THE HAGUE RULES",
              1, INK)
    draw_text(cv, W - 16, 108, "PRICE: THE NEWS ITSELF", 1, RED, "r")


# -------------------------------------------------------------- lead art
def draw_lead_art(cv, x, y, w, h):
    # dusk sky over Shenzhen: towers, three flags, three leaders at a table
    cv.vgrad(x, y, w, h, (28, 44, 92), (222, 158, 110))
    cv.disc(x + w - 64, y + 24, 18, (238, 186, 96))
    cv.disc(x + w - 64, y + 24, 12, (246, 214, 130))
    # skyline silhouettes
    for bx, bh, bw_ in ((10, 58, 26), (44, 84, 30), (82, 66, 24), (114, 96, 28),
                        (150, 72, 26), (184, 88, 30), (w - 150, 70, 26),
                        (w - 116, 92, 28), (w - 80, 64, 24), (w - 48, 80, 26)):
        cv.fill_rect(x + bx, y + h - bh, bw_, bh, (16, 26, 54))
        for wy in range(y + h - bh + 8, y + h - 8, 12):
            for wx in range(x + bx + 4, x + bx + bw_ - 4, 10):
                cv.fill_rect(wx, wy, 4, 5, GOLD)
    # three flags on poles above the table
    for i in range(3):
        fx = x + w // 2 - 96 + i * 64
        cv.vline(fx, y + 12, 44, WHITE, 2)
        if i == 0:  # USA: stars and stripes
            for s in range(7):
                cv.fill_rect(fx + 2, y + 12 + s * 3, 40, 3,
                             RED if s % 2 == 0 else WHITE)
            cv.fill_rect(fx + 2, y + 12, 16, 12, NAVY)
            for sx in (5, 11):
                for sy in (15, 20):
                    cv.disc(fx + sx, y + sy, 1, WHITE)
        elif i == 1:  # China: red field, five gold stars
            cv.fill_rect(fx + 2, y + 12, 40, 22, RED)
            cv.disc(fx + 10, y + 19, 3, GOLD)
            for s in range(4):
                cv.disc(fx + 24 + (s % 2) * 8, y + 16 + (s // 2) * 8, 2, GOLD)
        else:  # Russia: white-blue-red tricolour
            cv.fill_rect(fx + 2, y + 12, 40, 7, WHITE)
            cv.fill_rect(fx + 2, y + 19, 40, 8, BLUE)
            cv.fill_rect(fx + 2, y + 27, 40, 7, RED)
    # long table with three seated figures
    ty = y + h - 34
    cv.fill_rect(x + 40, ty, w - 80, 8, (60, 30, 22))
    cv.fill_rect(x + 48, ty + 8, 8, h - ty - 8, (60, 30, 22))
    cv.fill_rect(x + w - 56, ty + 8, 8, h - ty - 8, (60, 30, 22))
    for i, suit in enumerate((NAVY, RED_DK, (30, 30, 34))):
        fx = x + w // 2 - 96 + i * 64 + 20
        cv.disc(fx, ty - 18, 9, (226, 196, 160))
        cv.fill_rect(fx - 13, ty - 10, 26, 10, suit)
        cv.fill_rect(fx - 2, ty - 10, 4, 10, WHITE)
    # name plates
    for i, nm in enumerate(("USA", "CHINA", "RUSSIA")):
        px = x + w // 2 - 96 + i * 64 + 2
        cv.fill_rect(px, ty + 1, 36, 7, WHITE)
        draw_text(cv, px + 18, ty + 1, nm, 1, INK, "c")
    cv.fill_rect(x + 8, y + 8, 150, 18, NAVY)
    draw_text(cv, x + 14, y + 12, "SHENZHEN, CHINA", 1, WHITE)


# -------------------------------------------------------------- world map
def draw_map(cv, x, y, cell=6):
    for (r, c0, c1) in LAND:
        for c in range(c0, c1 + 1):
            cv.fill_rect(x + c * cell, y + r * cell, 4, 4, NAVY_LT)
    for (n, c, r, _lab) in POINTS:
        px_ = x + c * cell
        py_ = y + r * cell
        cv.disc(px_ + 2, py_ + 2, 6, RED)
        cv.disc(px_ + 2, py_ + 2, 4, WHITE)
        draw_text(cv, px_ - 1, py_ - 2, str(n), 1, RED)


# -------------------------------------------------------------- feature art
def draw_feature_art(cv, x, y, w, h, kind):
    if kind == "game":
        # neon Vice City night: towers, pink sky, palm silhouettes, big VI
        cv.vgrad(x, y, w, h, (24, 12, 54), (150, 40, 110))
        cv.disc(x + w - 24, y + 16, 10, (255, 120, 180))
        for bx, bh in ((8, 30), (26, 44), (48, 34), (70, 50), (94, 36), (116, 42)):
            cv.fill_rect(x + bx, y + h - bh, 16, bh, (12, 8, 30))
            for wy in range(y + h - bh + 6, y + h - 6, 10):
                cv.fill_rect(x + bx + 5, wy, 6, 4, NEON)
        cv.fill_rect(x, y + h - 8, w, 8, (12, 8, 30))
        draw_text(cv, x + w // 2, y + 8, "VI", 3, WHITE, "c")
        cv.line(x + 20, y + h - 14, x + 34, y + h - 30, GREEN)
        cv.line(x + 34, y + h - 30, x + 48, y + h - 14, GREEN)
    elif kind == "court":
        # The Hague: columns, pediment, scales of justice
        cv.vgrad(x, y, w, h, SKY, PAPER_DK)
        cv.tri(x + 10, y + 18, x + w // 2, y + 2, x + w - 10, y + 18, NAVY)
        for cx in (20, 52, 84, 116):
            cv.fill_rect(x + cx, y + 20, 10, 34, WHITE)
            cv.rect(x + cx, y + 20, 10, 34, NAVY, 1)
        cv.fill_rect(x + 8, y + 54, w - 16, 6, NAVY)
        cv.fill_rect(x + 8, y + 60, w - 16, 4, NAVY)
        # scales
        sx, sy = x + w // 2, y + 26
        cv.vline(sx, sy, 18, GOLD, 2)
        cv.line(sx, sy, sx - 16, sy + 12, GOLD)
        cv.line(sx, sy, sx + 16, sy + 12, GOLD)
        cv.tri(sx - 20, sy + 12, sx - 12, sy + 12, sx - 16, sy + 20, GOLD)
        cv.tri(sx + 12, sy + 12, sx + 20, sy + 12, sx + 16, sy + 20, GOLD)
    elif kind == "ipo":
        # rising chart and opening bell
        cv.vgrad(x, y, w, h, (16, 40, 70), (60, 90, 130))
        cv.line(x + 10, y + h - 16, x + 40, y + h - 34, GREEN)
        cv.line(x + 40, y + h - 34, x + 70, y + h - 26, GREEN)
        cv.line(x + 70, y + h - 26, x + 100, y + h - 48, GREEN)
        cv.line(x + 100, y + h - 48, x + 130, y + h - 56, GREEN)
        cv.tri(x + 130, y + h - 56, x + 118, y + h - 58, x + 126, y + h - 44, GREEN)
        for gx_ in range(x + 14, x + w - 10, 16):
            cv.fill_rect(gx_, y + h - 12, 8, 4, LGREY)
        cv.disc(x + w - 26, y + 18, 9, GOLD)
        cv.fill_rect(x + w - 32, y + 24, 12, 4, GOLD)
        draw_text(cv, x + 10, y + 6, "$81.3BN", 1, WHITE)
    elif kind == "voyager":
        cv.fill_rect(x, y, w, h, (8, 10, 26))
        for sx, sy in ((12, 12), (40, 22), (70, 10), (100, 26), (130, 14),
                       (24, 44), (88, 40), (120, 52), (56, 60), (140, 62)):
            cv.disc(x + sx, y + sy, 1, WHITE)
        cv.disc(x + 132, y + 14, 7, (240, 220, 140))
        cv.line(x + 30, y + 44, x + 76, y + 30, GOLD)
        cv.tri(x + 76, y + 30, x + 66, y + 22, x + 70, y + 38, GOLD)
        cv.fill_rect(x + 30, y + 42, 26, 8, WHITE)
        cv.line(x + 30, y + 46, x + 12, y + 54, WHITE)
        cv.disc(x + 12, y + 54, 2, RED)
        draw_text(cv, x + 10, y + h - 16, "1 LIGHT-DAY", 1, WHITE)
    elif kind == "loan":
        # euro coins and a bank facade
        cv.vgrad(x, y, w, h, (30, 60, 90), (120, 150, 180))
        cv.fill_rect(x + 10, y + 34, w - 20, 30, WHITE)
        cv.rect(x + 10, y + 34, w - 20, 30, NAVY, 1)
        for cx in (24, 56, 88, 120):
            cv.fill_rect(x + cx, y + 40, 8, 18, NAVY)
        draw_text(cv, x + w // 2, y + 8, "45BN EURO", 1, WHITE, "c")
        for i, (cx, cy) in enumerate(((24, 12), (52, 8), (80, 12), (108, 8))):
            cv.disc(x + cx, y + cy, 0, GOLD)
        cv.disc(x + 30, y + 14, 8, GOLD)
        cv.disc(x + 30, y + 14, 5, (220, 170, 60))
        draw_text(cv, x + 30, y + 10, "E", 1, NAVY, "c")
        cv.disc(x + w - 30, y + 14, 8, GOLD)
        cv.disc(x + w - 30, y + 14, 5, (220, 170, 60))
        draw_text(cv, x + w - 30, y + 10, "E", 1, NAVY, "c")
    elif kind == "cyclone":
        cv.vgrad(x, y, w, h, (30, 60, 90), (120, 150, 180))
        cx, cy = x + w // 2, y + h // 2 - 6
        for r in (34, 26, 18, 10):
            cv.circle(cx, cy, r, WHITE)
        cv.disc(cx, cy, 6, NAVY)
        for rx in range(x + 8, x + w - 8, 18):
            cv.line(rx, y + h - 22, rx - 6, y + h - 6, WHITE)
        cv.fill_rect(x, y + h - 8, w, 8, SEA_DK)
        draw_text(cv, x + 10, y + 6, "AKVAN", 1, WHITE)

# -------------------------------------------------------------- lead + map
def draw_lead(cv):
    lx, ly, lw = 16, 128, 620
    cv.fill_rect(lx, ly, lw, 4, RED)
    draw_text(cv, lx, ly + 10, LEAD_KICKER, 2, RED)
    y = ly + 32
    y = para(cv, lx, y, LEAD_HEAD, 2, INK, lw, leading=4)
    y += 4
    y = para(cv, lx, y, LEAD_DECK, 1, (60, 56, 48), lw, leading=3)
    y += 6
    art_h = 372 - y
    draw_lead_art(cv, lx, y, lw, art_h)
    cv.rect(lx, y, lw, art_h, INK, 1)
    draw_text(cv, lx, 378, "REPORTED THURSDAY FROM SHENZHEN AND MANILA",
              1, GREY)
    draw_text(cv, lx + lw, 378, "MAP: SIX FLASHPOINTS", 1, GREY, "r")
    return 396


def draw_right_rail(cv, top):
    rx, rw = 652, 356
    cv.fill_rect(rx, top, rw, 4, NAVY)
    draw_text(cv, rx, top + 10, "THE WORLD AT A GLANCE", 2, NAVY)
    my = top + 34
    draw_map(cv, rx + 34, my, cell=6)
    mh = 20 * 6 + 4
    ly = my + mh + 6
    for i, (n, _c, _r, lab) in enumerate(POINTS):
        lx_ = rx + 6 + (i // 3) * 178
        ly_ = ly + (i % 3) * 11
        draw_text(cv, lx_, ly_, "%d %s" % (n, lab), 1, RED)
    ly += 3 * 11 + 4
    cv.hline(rx, ly, rw, LGREY, 1)
    ly += 8
    draw_text(cv, rx, ly, "ALSO TODAY", 1, RED)
    ly += 12
    for item in GLANCE:
        draw_text(cv, rx, ly, "- " + item, 1, INK)
        ly += 12
    return ly


# -------------------------------------------------------------- features
def draw_features(cv, top):
    xs = [16 + i * 166 for i in range(6)]
    bw = 158
    heights = []
    for (tag, head, deck, _kind) in FEATURES:
        hl = wrap(head, 1, bw - 12)
        dl = wrap(deck, 1, bw - 12)
        heights.append(66 + 14 + len(hl) * 9 + len(dl) * 8 + 10)
    bh = max(heights)
    draw_text(cv, 16, top, "TOP STORIES", 2, NAVY)
    draw_text(cv, W - 16, top, "SIX STORIES THAT MADE THE DAY", 1, RED, "r")
    y0 = top + 20
    for i, (tag, head, deck, kind) in enumerate(FEATURES):
        x = xs[i]
        cv.rect(x, y0, bw, bh, INK, 1)
        draw_feature_art(cv, x + 1, y0 + 1, bw - 2, 66, kind)
        ty = y0 + 70
        cv.fill_rect(x, ty, bw, 14, NAVY if i % 2 == 0 else RED)
        draw_text(cv, x + 6, ty + 3, tag, 1, WHITE)
        yy = ty + 18
        yy = para(cv, x + 6, yy, head, 1, INK, bw - 12, leading=2)
        yy = para(cv, x + 6, yy + 1, deck, 1, (60, 56, 48), bw - 12, leading=1)
    return y0 + bh


# -------------------------------------------------------------- briefs
def draw_briefs(cv, top, bottom):
    cols_x = [16, 349, 682]
    col_w = 325
    draw_text(cv, 16, top, "THE DAY IN BRIEF", 2, NAVY)
    draw_text(cv, W - 16, top, "38 STORIES, NUMBERED", 1, RED, "r")
    y0 = top + 20
    cv.hline(16, y0 - 6, W - 32, INK, 2)
    ends = []
    for ci in range(3):
        x = cols_x[ci]
        draw_text(cv, x, y0, COL_TITLES[ci], 1, RED)
        cv.hline(x, y0 + 11, col_w, RED, 1)
        y = y0 + 18
        n = 0
        for (col, head, body) in BRIEFS:
            if col != ci:
                continue
            n += 1
            cv.fill_rect(x, y, 16, 11, RED)
            draw_text(cv, x + 2, y + 2, str(n), 1, WHITE)
            hy = y
            hl = wrap(head, 1, col_w - 22)
            for ln in hl[:2]:
                draw_text(cv, x + 22, hy, ln, 1, NAVY)
                hy += 10
            by = hy
            bl = wrap(body, 1, col_w - 22)
            for ln in bl[:2]:
                draw_text(cv, x + 22, by, ln, 1, (60, 56, 48))
                by += 9
            y = by + 5
            if len(bl) > 2 or len(hl) > 2:
                print("OVERFLOW brief %d col %d: head %d lines body %d lines"
                      % (n, ci, len(hl), len(bl)))
        ends.append(y)
    print("brief columns end at:", ends, "budget bottom:", bottom)
    return max(ends)


# -------------------------------------------------------------- ticker
def draw_ticker(cv, y):
    cv.fill_rect(0, y, W, 32, BLACK)
    draw_text(cv, 16, y + 5, "THE MARKETS", 2, GOLD)
    draw_text(cv, 16, y + 19, "AT THE CLOSE", 1, GREY)
    tx = 150
    lines = wrap(TICKER, 1, W - tx - 16)
    yy = y + 4
    for ln in lines[:2]:
        draw_text(cv, tx, yy, ln, 1, WHITE)
        yy += 11
    return y + 32


def build():
    cv = Canvas()
    cv.rect(6, 6, W - 12, H - 12, INK, 2)
    draw_masthead(cv)
    lead_end = draw_lead(cv)
    rail_end = draw_right_rail(cv, 128)
    feat_top = max(lead_end, rail_end) + 8
    feat_end = draw_features(cv, feat_top)
    brief_top = feat_end + 10
    brief_end = draw_briefs(cv, brief_top, 950)
    print("lead_end", lead_end, "rail_end", rail_end,
          "feat_top", feat_top, "feat_end", feat_end,
          "brief_top", brief_top, "brief_end", brief_end)
    tick_end = draw_ticker(cv, 958)
    draw_text(cv, 16, 1000, "THE WORLD TODAY  -  THURSDAY 19 NOVEMBER 2026  -  "
              "COMPILED FROM WIRE REPORTS PUBLISHED ON THE DAY  -  PAGE 1 OF 1",
              1, GREY)
    grain(cv)
    return cv


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    cv = build()
    path = os.path.join(outdir, "entry.png")
    n = save_png(path, cv.buf)
    import hashlib
    h = hashlib.sha256(open(path, "rb").read()).hexdigest()
    print("wrote", path, n, "bytes sha256", h)
    return n


if __name__ == "__main__":
    main()
