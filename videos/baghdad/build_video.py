#!/usr/bin/env python3
"""Render the "Mongols and the fall of Baghdad" short (1080x1920, 30fps).

  python3 build_video.py                      # draft: estimated timing, no voice
  python3 build_video.py --voice take.wav     # final: timed to your recording

Needs ffmpeg and Pillow. Fonts are DejaVu (no network needed).
Record the six script.json lines with a pause of 1.5s or more between each; the
pauses are how the scenes are timed. If the pauses are not found, timing is
spread by word count and a warning is printed.
"""
import argparse, json, math, os, re, subprocess, sys
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1080, 1920, 30
HERE = os.path.dirname(os.path.abspath(__file__))
BG, INK, MUTED = (14, 21, 19), (225, 233, 229), (152, 169, 161)
ACC, GOLD, WARN = (95, 198, 172), (217, 174, 90), (240, 160, 112)
FD = "/usr/share/fonts/truetype/dejavu/"
_fc = {}


def font(name, size):
    k = (name, size)
    if k not in _fc:
        _fc[k] = ImageFont.truetype(FD + name, size)
    return _fc[k]


SERIF, SANS, SANSB = "DejaVuSerif-Bold.ttf", "DejaVuSans.ttf", "DejaVuSans-Bold.ttf"


def ease(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def seg(t, a, b):
    return ease((t - a) / (b - a)) if b > a else 1.0


# ---------- drawing helpers ----------
def put(frame, text, x, y, f, fill, alpha=1.0, anchor="mm", spacing=0):
    if alpha <= 0.01:
        return
    d0 = ImageDraw.Draw(frame)
    l, t, r, b = d0.textbbox((x, y), text, font=f, anchor=anchor)
    l, t, r, b = int(math.floor(l)), int(math.floor(t)), int(math.ceil(r)), int(math.ceil(b))
    pad = 6
    layer = Image.new("RGBA", (r - l + 2 * pad, b - t + 2 * pad), (0, 0, 0, 0))
    ImageDraw.Draw(layer).text((x - l + pad, y - t + pad), text, font=f,
                               fill=fill + (int(255 * min(1, alpha)),), anchor=anchor)
    frame.alpha_composite(layer, (max(0, l - pad), max(0, t - pad)))


def box(frame, x0, y0, x1, y1, fill, alpha=1.0, outline=None, radius=22):
    if alpha <= 0.01:
        return
    layer = Image.new("RGBA", (x1 - x0, y1 - y0), (0, 0, 0, 0))
    ImageDraw.Draw(layer).rounded_rectangle(
        (0, 0, x1 - x0 - 1, y1 - y0 - 1), radius, fill=fill + (int(255 * alpha),),
        outline=None if outline is None else outline + (int(255 * alpha),), width=3)
    frame.alpha_composite(layer, (x0, y0))


def wrap(text, f, maxw):
    d = ImageDraw.Draw(Image.new("RGB", (4, 4)))
    lines, cur = [], ""
    for w in text.split():
        trial = (cur + " " + w).strip()
        if d.textlength(trial, font=f) <= maxw:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    return lines


def star_tile(n=180):
    tile = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(tile)
    c, r = n / 2, n * 0.34
    for rot in (0, 45):
        pts = [(c + r * math.cos(math.radians(rot + a + 45)),
                c + r * math.sin(math.radians(rot + a + 45))) for a in (0, 90, 180, 270)]
        d.polygon(pts, outline=(95, 198, 172, 26))
    d.ellipse((c - 5, c - 5, c + 5, c + 5), outline=(217, 174, 90, 30))
    return tile


def make_background():
    base = Image.new("RGBA", (W, H), BG + (255,))
    px = ImageDraw.Draw(base)
    for y in range(0, H, 4):  # soft vertical glow
        g = 1 - abs(y - H * 0.42) / (H * 0.6)
        g = max(0, g)
        px.rectangle((0, y, W, y + 4), fill=(14 + int(10 * g), 21 + int(18 * g), 19 + int(14 * g), 255))
    n = 180
    pat = Image.new("RGBA", (W + n, H + n), (0, 0, 0, 0))
    t = star_tile(n)
    for yy in range(0, H + n, n):
        for xx in range(0, W + n, n):
            pat.alpha_composite(t, (xx, yy))
    return base, pat, n


# ---------- scenes ----------
HEAD = font(SANSB, 38)


def header(f, text, color, t, d):
    put(f, text, W // 2, 300, HEAD, color, seg(t, 0.0, 0.5))


def source(f, text, sub, t, a=0.6, y=1235):
    al = seg(t, a, a + 0.5)
    put(f, text, W // 2, y, font(SANSB, 34), GOLD, al)
    if sub:
        put(f, sub, W // 2, y + 55, font(SANS, 30), MUTED, al)


def scene_hook(f, t, d):
    header(f, "THE PROPHET'S DEATH", GOLD, t, d)
    k = seg(t, 0.4, max(1.2, d * 0.72))
    year = int(632 + (1258 - 632) * k)
    put(f, str(year), W // 2, 640, font(SERIF, 250), INK if k < 1 else GOLD)
    put(f, "YEARS LATER" if k >= 1 else "", W // 2, 840, font(SANSB, 40), MUTED, seg(t, d * 0.72, d * 0.72 + 0.4))
    put(f, "632 → 1258", W // 2, 840, font(SANSB, 40), MUTED, 1 - seg(t, d * 0.7, d * 0.72 + 0.1))
    put(f, "A people arrived at Baghdad", W // 2, 1010, font(SERIF, 62), INK, seg(t, d * 0.55, d * 0.55 + 0.6))
    put(f, "who fit his description", W // 2, 1090, font(SERIF, 62), ACC, seg(t, d * 0.65, d * 0.65 + 0.6))


def scene_description(f, t, d):
    header(f, "WHAT HE DESCRIBED", GOLD, t, d)
    rows = ["Small eyes", "Red faces", "Flat noses", "Faces like shields covered in leather", "Shoes made of hair"]
    for i, r in enumerate(rows):
        a = 0.45 + i * (d - 1.2) / (len(rows) + 0.5)
        al = seg(t, a, a + 0.45)
        y = 420 + i * 150 + int((1 - al) * 24)
        box(f, 100, y, W - 100, y + 118, (21, 30, 27), al, outline=(39, 52, 47))
        put(f, str(i + 1), 170, y + 59, font(SERIF, 52), GOLD, al)
        lines = wrap(r, font(SERIF, 46), 640)
        for j, ln in enumerate(lines):
            put(f, ln, 270, y + 59 + (j - (len(lines) - 1) / 2) * 52, font(SERIF, 46), INK, al, anchor="lm")
    put(f, "(same hadith)", W - 130, 420 + 4 * 150 + 59 + 56, font(SANS, 26), MUTED,
        seg(t, d * 0.8, d * 0.8 + 0.4), anchor="rm")
    source(f, "Sahih al-Bukhari 2928", "the hadith names the Turks", t, 0.8)


def timeline(f, t_prog, show1258, t1258=0.0, y=820, brace=True):
    x0, x1 = 140, 940
    sx = lambda yr: x0 + (yr - 600) * (x1 - x0) / 700
    end = sx(1258) if show1258 else sx(790)
    xe = x0 + (end - x0) * t_prog
    ImageDraw.Draw(f).line((x0, y, xe, y), fill=MUTED + (255,), width=6)
    # 632 and 1258 label above the line, 762 below, so close dates never collide
    a = seg(t_prog, 0.15, 0.4)
    x = sx(632)
    ImageDraw.Draw(f).ellipse((x - 16, y - 16, x + 16, y + 16), fill=INK + (int(255 * a),))
    put(f, "632", x + 40, y - 70, font(SERIF, 56), INK, a)
    for j, ln in enumerate(["The Prophet", "(peace be upon him)", "passes away"]):
        put(f, ln, x - 30, y - 150 - (2 - j) * 40, font(SANS, 31), INK if j == 1 else MUTED, a, anchor="lm")
    a = seg(t_prog, 0.5, 0.75)
    x = sx(762)
    ImageDraw.Draw(f).ellipse((x - 16, y - 16, x + 16, y + 16), fill=ACC + (int(255 * a),))
    put(f, "762", x, y + 70, font(SERIF, 56), ACC, a)
    for j, ln in enumerate(["Baghdad", "is founded"]):
        put(f, ln, x, y + 135 + j * 38, font(SANS, 30), MUTED, a)
    if show1258:
        a = seg(t1258, 0.0, 0.4)
        x = sx(1258)
        r = 16 + int(10 * math.sin(t1258 * 6) * a)
        ImageDraw.Draw(f).ellipse((x - r, y - r, x + r, y + r), fill=WARN + (int(255 * a),))
        put(f, "1258", x, y - 70, font(SERIF, 56), WARN, a)
        for j, ln in enumerate(["Mongols", "enter Baghdad"]):
            put(f, ln, x, y - 150 - (1 - j) * 38, font(SANS, 30), MUTED, a)
    a = seg(t_prog, 0.62, 0.9) if brace else 0
    if a > 0:
        bx0, bx1 = sx(632), sx(762)
        ImageDraw.Draw(f).line((bx0, y + 250, bx1, y + 250), fill=GOLD + (int(255 * a),), width=4)
        put(f, "130 years", (bx0 + bx1) / 2, y + 295, font(SANSB, 32), GOLD, a)


def scene_city(f, t, d):
    header(f, "THE CITY IN THE REPORT", GOLD, t, d)
    put(f, "A great city on the Tigris,", W // 2, 470, font(SERIF, 58), INK, seg(t, 0.4, 1.0))
    put(f, "with a bridge", W // 2, 545, font(SERIF, 58), INK, seg(t, 0.7, 1.3))
    timeline(f, seg(t, 0.8, d * 0.8), False, y=900)
    source(f, "Sunan Abu Dawud 4306 · hasan (al-Albani)",
           "the text names the city Basra; some scholars read it as Baghdad", t, d * 0.55, y=1285)


def scene_history(f, t, d):
    header(f, "WHAT HISTORY RECORDS", GOLD, t, d)
    put(f, "1258", W // 2, 470, font(SERIF, 200), WARN, seg(t, 0.2, 0.8))
    put(f, "Hulagu and the Mongol army", W // 2, 640, font(SERIF, 52), INK, seg(t, 0.7, 1.3))
    put(f, "enter Baghdad", W // 2, 710, font(SERIF, 52), INK, seg(t, 0.9, 1.5))
    timeline(f, 1.0, True, max(0.0, t - 0.3), y=1030, brace=False)
    put(f, "End of Abbasid rule in Baghdad", W // 2, 1300, font(SANSB, 36), GOLD, seg(t, d * 0.55, d * 0.55 + 0.5))


def scene_objection(f, t, d):
    mid = d * 0.4
    header(f, "THE OBJECTION", WARN, t, d)
    a = seg(t, 0.3, 0.9)
    box(f, 100, 400, W - 100, 640, (30, 22, 18), a, outline=WARN)
    for j, ln in enumerate(["“The Arabs already", "knew the Turks.”"]):
        put(f, ln, W // 2, 485 + j * 70, font(SERIF, 56), INK, a)
    b = seg(t, mid, mid + 0.5)
    put(f, "THE WHOLE PICTURE", W // 2, 760, font(SANSB, 38), ACC, b)
    for i, r in enumerate(["The appearance", "The attack", "A city not yet built"]):
        s = mid + 0.4 + i * (d - mid - 1.2) / 3
        al = seg(t, s, s + 0.4)
        y = 850 + i * 130 + int((1 - al) * 20)
        box(f, 160, y, W - 160, y + 100, (17, 48, 42), al, outline=ACC)
        put(f, "✓", 230, y + 50, font(SANSB, 48), ACC, al)
        put(f, r, 310, y + 50, font(SERIF, 50), INK, al, anchor="lm")


def scene_close(f, t, d):
    header(f, "IN ONE BREATH", GOLD, t, d)
    lines = ["Small-eyed, flat-nosed", "invaders in shoes of hair,", "a great city on the Tigris:", "Baghdad, 1258."]
    for i, ln in enumerate(lines):
        s = 0.4 + i * 0.6
        put(f, ln, W // 2, 520 + i * 110, font(SERIF, 62), GOLD if i == 3 else INK, seg(t, s, s + 0.5))
    put(f, "Check every source before you cite it.", W // 2, 1140, font(SANS, 34), MUTED, seg(t, d * 0.5, d * 0.5 + 0.6))


SCENES = [scene_hook, scene_description, scene_city, scene_history, scene_objection, scene_close]


# ---------- timing ----------
def ffprobe_dur(p):
    out = subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                   "-of", "default=nw=1:nk=1", p], text=True)
    return float(out.strip())


def speech_segments(path, total):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", path, "-af", "silencedetect=noise=-35dB:d=0.7",
                        "-f", "null", "-"], capture_output=True, text=True)
    starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", r.stderr)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", r.stderr)]
    segs, cur = [], 0.0
    for s, e in zip(starts, ends):
        if s - cur > 0.25:
            segs.append((cur, s))
        cur = e
    if total - cur > 0.25:
        segs.append((cur, total))
    return segs


def plan_timing(script, voice):
    n = len(script)
    words = [len(s["text"].split()) for s in script]
    if voice:
        total = ffprobe_dur(voice)
        segs = speech_segments(voice, total)
        if len(segs) == n:
            spans = [(max(0, s - 0.15), e) for s, e in segs]
            starts = [sp[0] for sp in spans] + [spans[-1][1] + 0.9]
            return [(starts[i], starts[i + 1], segs[i][0], segs[i][1]) for i in range(n)], total + 0.9
        print(f"WARNING: found {len(segs)} spoken sections, expected {n}; timing by word count.", file=sys.stderr)
        lead = segs[0][0] if segs else 0.0
        tail = segs[-1][1] if segs else total
        span = tail - lead
        out, t = [], lead
        for w in words:
            dur = span * w / sum(words)
            out.append((t, t + dur, t, t + dur))
            t += dur
        out[0] = (0.0,) + out[0][1:]
        return out, total + 0.9
    out, t = [], 0.0
    for w in words:
        dur = w / 2.4 + 0.9
        out.append((t, t + dur, t + 0.2, t + dur - 0.7))
        t += dur
    return out, t + 0.9


def caption_chunks(text, vs, ve):
    ws = text.split()
    chunks = [ws[i:i + 4] for i in range(0, len(ws), 4)]
    weights = [max(1, len(w)) for w in ws]
    tot, pos, res = sum(weights), vs, []
    idx = 0
    span = ve - vs
    for ch in chunks:
        cw = weights[idx: idx + len(ch)]
        words = []
        for w, wt in zip(ch, cw):
            dur = span * wt / tot
            words.append((w, pos, pos + dur))
            pos += dur
        res.append(words)
        idx += len(ch)
    return res


def draw_caption(f, chunks, t):
    for words in chunks:
        if words[0][1] - 0.05 <= t < words[-1][2] + 0.25:
            fnt = font(SANSB, 62)
            d = ImageDraw.Draw(f)
            widths = [d.textlength(w + " ", font=fnt) for w, _, _ in words]
            x = W / 2 - sum(widths) / 2
            box(f, int(x) - 30, 1390, int(x + sum(widths)) + 30, 1500, (8, 12, 11), 0.7, radius=26)
            for (w, s, e), wd in zip(words, widths):
                put(f, w, x, 1445, fnt, GOLD if s <= t < e else INK, anchor="lm")
                x += wd
            return


# ---------- audio ----------
def make_audio(out, total, voice, music):
    if music:
        bed = ["-i", music]
        bedf = f"[1:a]aloop=loop=-1:size=2e9,atrim=0:{total:.2f},volume=0.35,afade=t=in:d=1,afade=t=out:st={total-1.5:.2f}:d=1.5[bed]"
    else:  # quiet generated drone, placeholder only
        bed = ["-f", "lavfi", "-i", f"sine=f=98:d={total:.2f}"]
        bedf = (f"[1:a]volume=0.05,lowpass=f=400,tremolo=f=0.15:d=0.5,"
                f"afade=t=in:d=1.5,afade=t=out:st={total-1.5:.2f}:d=1.5[bed]")
    if voice:
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", voice] + bed + [
            "-filter_complex", f"[0:a]apad=whole_dur={total:.2f},loudnorm=I=-16:TP=-1.5[v];{bedf};[bed]volume=0.5[b];[v][b]amix=inputs=2:duration=first:normalize=0[a]",
            "-map", "[a]", "-t", f"{total:.2f}", out]
    else:
        cmd = ["ffmpeg", "-y", "-loglevel", "error"] + ["-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo"] + bed + [
            "-filter_complex", bedf, "-map", "[bed]", "-t", f"{total:.2f}", out]
    subprocess.run(cmd, check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--voice")
    ap.add_argument("--music", help="optional licensed music file")
    ap.add_argument("--out")
    ap.add_argument("--max-seconds", type=float, help="render only the first N seconds (test)")
    a = ap.parse_args()
    script = json.load(open(os.path.join(HERE, "script.json")))
    plan, total = plan_timing(script, a.voice)
    if a.max_seconds:
        total = min(total, a.max_seconds)
    out = a.out or os.path.join(HERE, "baghdad_final.mp4" if a.voice else "baghdad_draft.mp4")
    audio = os.path.join(HERE, ".audio.m4a")
    make_audio(audio, total, a.voice, a.music)
    bg, pat, n = make_background()
    caps = [caption_chunks(s["text"], p[2], p[3]) for s, p in zip(script, plan)]
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", audio, "-c:v", "libx264",
                           "-pix_fmt", "yuv420p", "-crf", "20", "-preset", "medium", "-c:a", "aac",
                           "-b:a", "192k", "-movflags", "+faststart", "-t", f"{total:.2f}", out],
                          stdin=subprocess.PIPE)
    frames = int(total * FPS)
    for i in range(frames):
        t = i / FPS
        si = next((k for k, p in enumerate(plan) if p[0] <= t < p[1]), len(plan) - 1)
        s0, s1 = plan[si][0], plan[si][1]
        ox, oy = int(t * 6) % n, int(t * 4) % n
        f = bg.copy()
        f.alpha_composite(pat.crop((ox, oy, ox + W, oy + H)))
        SCENES[si](f, t - s0, s1 - s0)
        put(f, "DAWAH STUDY LIBRARY · FULFILLED PROPHECIES", W // 2, 170, font(SANSB, 24), MUTED, 0.8)
        draw_caption(f, caps[si], t)
        if not a.voice:
            put(f, "DRAFT · PLACEHOLDER TIMING · NO VOICE", W // 2, 1700, font(SANSB, 26), WARN, 0.9)
        ff.stdin.write(f.convert("RGB").tobytes())
    ff.stdin.close()
    ff.wait()
    os.remove(audio)
    print("wrote", out, f"({total:.1f}s)")


if __name__ == "__main__":
    main()
