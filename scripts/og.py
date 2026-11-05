"""Open Graph preview images (1200x630) for link previews on social media and chat apps.

Called by build_site.py with the same numbers the pages show, so a preview never disagrees with its page.
One image for the overview (also used by the other non-agency pages) and one per agency.
Fonts: Newsreader and IBM Plex Sans (SIL Open Font License), the fonts maxmautner.com uses.
"""
import hashlib
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FONTS = Path(__file__).resolve().parent.parent / "site" / "og" / "fonts"
W, H, PAD = 1200, 630, 72

# maxmautner.com dark tokens
BG, SURFACE, SUNKEN = "#211e1b", "#2c2925", "#1a1714"
TEXT, TEXT2, TEXT3, ACCENT, ACCENT_INK = "#f1efe9", "#aaa39a", "#8a847b", "#c79045", "#332416"


def _mix(a, b, t):
    """Blend hex color a into b; t is the share of a (same as CSS color-mix)."""
    pa = [int(a[i:i + 2], 16) for i in (1, 3, 5)]
    pb = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x * t + y * (1 - t)):02x}" for x, y in zip(pa, pb))


# Same scheme as the status bars on the site (rtm.css)
SEG = {
    "implemented": ACCENT, "in_progress": _mix(ACCENT, SUNKEN, .8), "adopted": _mix(ACCENT, SUNKEN, .55),
    "not_started": _mix(TEXT2, SUNKEN, .4), "missed": TEXT, "not_adopted": _mix(TEXT3, SUNKEN, .7),
    "superseded": _mix(TEXT3, SUNKEN, .35), "unverified": _mix(TEXT3, SUNKEN, .5),
}


def font(name, size, weight):
    f = ImageFont.truetype(str(FONTS / name), size)
    # axes: Newsreader [wght, opsz]; IBM Plex Sans [wght, wdth]
    f.set_variation_by_axes([weight, min(72, size) if "Newsreader" in name else 100])
    return f


def serif(size, weight=600):
    return font("Newsreader.ttf", size, weight)


def sans(size, weight=400):
    return font("IBMPlexSans.ttf", size, weight)


def wrap(d, text, f, width):
    lines, cur = [], ""
    for w in text.split():
        t = f"{cur} {w}".strip()
        if d.textlength(t, font=f) <= width or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
    return lines + [cur]


def _base(eyebrow):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.rectangle([0, H - 10, W, H], fill=ACCENT)
    d.text((PAD, PAD - 6), eyebrow.upper(), font=sans(22, 600), fill=TEXT3)
    return img, d


def _footer(d, site):
    d.text((PAD, H - PAD + 10), site, font=sans(24), fill=TEXT3, anchor="ls")
    note = "Every status linked to a primary source"
    f = sans(24)
    d.text((W - PAD, H - PAD + 10), note, font=f, fill=TEXT3, anchor="rs")


def _bar(d, x, y, w, h, segments):
    """segments: list of (status_key, count). Drawn left to right, 3px gaps, like the site's bar."""
    d.rounded_rectangle([x, y, x + w, y + h], radius=h // 2, fill=SUNKEN)
    total = sum(n for _, n in segments) or 1
    gap = 3
    usable = w - gap * (len(segments) - 1)
    cx = x
    for i, (k, n) in enumerate(segments):
        sw = max(6, round(usable * n / total))
        if i == len(segments) - 1:
            sw = x + w - cx
        d.rectangle([cx, y, cx + sw, y + h], fill=SEG[k])
        cx += sw + gap
    # round the ends by masking corners with the background
    mask = Image.new("L", (w + 1, h + 1), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, w, h], radius=h // 2, fill=255)
    return mask


def _paste_bar(img, x, y, w, h, segments):
    tile = Image.new("RGB", (w + 1, h + 1), BG)
    td = ImageDraw.Draw(tile)
    mask = _bar(td, 0, 0, w, h, segments)
    img.paste(tile, (x, y), mask)


def _save(img, path):
    img.quantize(colors=96, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).save(path, optimize=True)
    return hashlib.sha256(path.read_bytes()).hexdigest()[:10]


def overview(path, agencies, site, eyebrow):
    img, d = _base(eyebrow)
    y = 150
    for line in wrap(d, "Cost-saving commitments of Muni, BART, AC Transit, and Caltrain", serif(54), W - 2 * PAD):
        d.text((PAD, y), line, font=serif(54), fill=TEXT, anchor="ls")
        y += 62
    y += 34
    name_f, num_f = sans(28, 600), sans(26, 400)
    row_h, bar_x, bar_w = 64, PAD + 300, 470
    for a in agencies:
        d.rounded_rectangle([PAD, y - 30, PAD + 7, y + 8], radius=3, fill=a["color"])
        d.text((PAD + 24, y), a["display"], font=name_f, fill=TEXT, anchor="ls")
        _paste_bar(img, bar_x, y - 22, bar_w, 18, [(s["key"], s["n"]) for s in a["bar"]])
        adopted = a["counts"]["adopted"] + a["counts"]["in_progress"] + a["counts"]["implemented"]
        d.text((W - PAD, y), f"{adopted} of {a['total']} adopted", font=num_f, fill=TEXT2, anchor="rs")
        y += row_h
    _footer(d, site)
    return _save(img, path)


def agency(path, a, site, eyebrow, target_text, labels):
    img, d = _base(eyebrow)
    d.rounded_rectangle([PAD, 108, PAD + 64, 116], radius=4, fill=a["color"])
    d.text((PAD, 196), a["display"], font=serif(76), fill=TEXT, anchor="ls")
    sub = f"{a['total']} SB 63 cost-saving recommendations tracked"
    if a["actions"] and a["actions"][0][0]:
        dt = a["actions"][0][0]
        sub += f" · board action {dt:%B} {dt.day}, {dt.year}"
    d.text((PAD, 242), sub, font=sans(28), fill=TEXT2, anchor="ls")

    c = a["counts"]
    tiles = [("Adopted", c["adopted"], ""), ("In progress", c["in_progress"], ""),
             ("Implemented", c["implemented"], target_text), ("Missed", c["missed"], "")]
    gap, top, th = 18, 276, 166
    tw = (W - 2 * PAD - 3 * gap) // 4
    for i, (label, v, note) in enumerate(tiles):
        x = PAD + i * (tw + gap)
        d.rounded_rectangle([x, top, x + tw, top + th], radius=16, fill=SURFACE)
        d.text((x + 22, top + 40), label, font=sans(26, 500), fill=TEXT2, anchor="ls")
        if note:
            d.text((x + 22, top + 68), note, font=sans(19), fill=TEXT3, anchor="ls")
        d.text((x + 22, top + th - 22), str(v), font=serif(84), fill=TEXT, anchor="ls")
    by = top + th + 22
    _paste_bar(img, PAD, by, W - 2 * PAD, 16, [(s["key"], s["n"]) for s in a["bar"]])
    # every non-zero status in words, so nothing in the bar is unlabeled
    words = " · ".join(f"{s['n']} {labels[s['key']].lower()}" for s in a["bar"])
    d.text((PAD, by + 56), words, font=sans(26), fill=TEXT2, anchor="ls")
    _footer(d, site)
    return _save(img, path)


def render(out_dir, agencies, site, eyebrow, target_text, labels):
    """Write og/index.png and og/<slug>.png; return {name: content hash} for cache-busting URLs."""
    out_dir.mkdir(parents=True, exist_ok=True)
    versions = {"index": overview(out_dir / "index.png", agencies, site, eyebrow)}
    for a in agencies:
        versions[a["slug"]] = agency(out_dir / f"{a['slug']}.png", a, site, eyebrow, target_text, labels)
    return versions
