#!/usr/bin/env python3
"""Arabic version of the Baghdad short (1080x1920, 30fps), timed to script_ar.json.

  python3 build_video_ar.py                    # draft: estimated timing, no voice
  python3 build_video_ar.py --voice take.m4a   # final: timed to your recording

Reuses the helpers in build_video.py. Needs ffmpeg and Pillow with raqm (Arabic shaping).
Pause 2 seconds between the six sections when recording; see RECORDING_AR.md.
"""
import argparse, json, math, os, subprocess
from PIL import Image, ImageDraw
import build_video as B
from build_video import (W, H, FPS, HERE, INK, MUTED, ACC, GOLD, WARN, SERIF, SANS, SANSB,
                         font, put, box, seg, wrap, make_background, plan_timing, make_audio)


def tx(frame, text, x, y, f, fill, alpha=1.0, anchor="mm"):
    put(frame, text, x, y, f, fill, alpha, anchor)


def header(f, text, color, t, d):
    tx(f, text, W // 2, 300, font(SANSB, 46), color, seg(t, 0.0, 0.5))


def source(f, text, sub, t, a=0.6, y=1235):
    al = seg(t, a, a + 0.5)
    tx(f, text, W // 2, y, font(SANSB, 38), GOLD, al)
    if sub:
        tx(f, sub, W // 2, y + 58, font(SANS, 32), MUTED, al)


def scene_hook(f, t, d):
    header(f, "هل هو مجرد صدفة؟", GOLD, t, d)
    k = seg(t, 0.4, max(1.2, d * 0.72))
    tx(f, str(int(632 + (1258 - 632) * k)).translate(str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩")), W // 2, 640, font(SANSB, 230), INK if k < 1 else GOLD)
    tx(f, "أكثر من ستمئة سنة", W // 2, 860, font(SANSB, 52), MUTED, seg(t, d * 0.72, d * 0.72 + 0.4))
    tx(f, "من وفاة النبي إلى سقوط بغداد", W // 2, 1040,
       font(SANSB, 50), INK, seg(t, d * 0.55, d * 0.55 + 0.6))


def scene_description(f, t, d):
    header(f, "ماذا وصف؟", GOLD, t, d)
    rows = ["صغار الأعين", "حمر الوجوه", "ذلف الأنوف", "كأن وجوههم المجانّ المطرقة", "نعالهم الشعر"]
    for i, r in enumerate(rows):
        a = 0.45 + i * (d - 1.2) / (len(rows) + 0.5)
        al = seg(t, a, a + 0.45)
        y = 420 + i * 150 + int((1 - al) * 24)
        box(f, 100, y, W - 100, y + 118, (21, 30, 27), al, outline=(39, 52, 47))
        tx(f, str(i + 1), W - 170, y + 59, font(SANSB, 52), GOLD, al)
        tx(f, r, W - 270, y + 59, font(SANSB, 50), INK, al, anchor="rm")
    tx(f, "(في الحديث نفسه)", 130, 420 + 4 * 150 + 115, font(SANS, 28), MUTED, seg(t, d * 0.8, d * 0.8 + 0.4), anchor="lm")
    source(f, "صحيح البخاري ٢٩٢٨", "الحديث يذكر الترك", t, 0.8)


def timeline(f, prog, show1258, t1258=0.0, y=820, brace=True):
    x0, x1 = 140, 940
    sx = lambda yr: x1 - (yr - 600) * (x1 - x0) / 700  # right to left
    end = sx(1258) if show1258 else sx(790)
    xe = x1 + (end - x1) * prog
    ImageDraw.Draw(f).line((xe, y, x1, y), fill=MUTED + (255,), width=6)
    a = seg(prog, 0.15, 0.4)
    x = sx(632)
    ImageDraw.Draw(f).ellipse((x - 16, y - 16, x + 16, y + 16), fill=INK + (int(255 * a),))
    tx(f, "٦٣٢", x, y - 70, font(SANSB, 56), INK, a)
    tx(f, "وفاة النبي صلى الله عليه وسلم", x, y - 135, font(SANS, 30), MUTED, a, anchor="rm")
    a = seg(prog, 0.5, 0.75)
    x = sx(762)
    ImageDraw.Draw(f).ellipse((x - 16, y - 16, x + 16, y + 16), fill=ACC + (int(255 * a),))
    tx(f, "٧٦٢", x, y + 70, font(SANSB, 56), ACC, a)
    tx(f, "بناء بغداد", x, y + 130, font(SANS, 32), MUTED, a)
    if show1258:
        a = seg(t1258, 0.0, 0.4)
        x = sx(1258)
        r = 16 + int(10 * math.sin(t1258 * 6) * a)
        ImageDraw.Draw(f).ellipse((x - r, y - r, x + r, y + r), fill=WARN + (int(255 * a),))
        tx(f, "١٢٥٨", x, y - 70, font(SANSB, 56), WARN, a)
        tx(f, "دخول المغول بغداد", x, y - 135, font(SANS, 32), MUTED, a)
    a = seg(prog, 0.62, 0.9) if brace else 0
    if a > 0:
        bx0, bx1 = sx(762), sx(632)
        ImageDraw.Draw(f).line((bx0, y + 250, bx1, y + 250), fill=GOLD + (int(255 * a),), width=4)
        tx(f, "نحو ١٣٠ سنة", (bx0 + bx1) / 2, y + 295, font(SANSB, 34), GOLD, a)


def scene_city(f, t, d):
    header(f, "المدينة في الرواية", GOLD, t, d)
    tx(f, "مدينة على دجلة", W // 2, 470, font(SANSB, 62), INK, seg(t, 0.4, 1.0))
    tx(f, "يأتيها بنو قنطوراء", W // 2, 550, font(SANSB, 62), INK, seg(t, 0.7, 1.3))
    timeline(f, seg(t, 0.8, d * 0.8), False, y=900)
    source(f, "سنن أبي داود ٤٣٠٦", "النص يقول «البصرة»، وبعض العلماء فهموها بغداد", t, d * 0.55, y=1285)


def scene_history(f, t, d):
    header(f, "ماذا يسجل التاريخ؟", GOLD, t, d)
    tx(f, "١٢٥٨", W // 2, 470, font(SANSB, 200), WARN, seg(t, 0.2, 0.8))
    tx(f, "هولاكو يدخل بغداد", W // 2, 650, font(SANSB, 56), INK, seg(t, 0.7, 1.3))
    timeline(f, 1.0, True, max(0.0, t - 0.3), y=1050, brace=False)
    tx(f, "نهاية حكم العباسيين في بغداد", W // 2, 1320, font(SANSB, 40), GOLD, seg(t, d * 0.55, d * 0.55 + 0.5))


def scene_objection(f, t, d):
    mid = d * 0.4
    header(f, "الاعتراض", WARN, t, d)
    a = seg(t, 0.3, 0.9)
    box(f, 100, 400, W - 100, 640, (30, 22, 18), a, outline=WARN)
    tx(f, "«العرب كانوا يعرفون الترك»", W // 2, 520, font(SANSB, 58), INK, a)
    b = seg(t, mid, mid + 0.5)
    tx(f, "لكن انظر إلى الصورة كلها", W // 2, 760, font(SANSB, 42), ACC, b)
    for i, r in enumerate(["الوجوه", "الهجوم", "المدينة على النهر"]):
        s = mid + 0.4 + i * (d - mid - 1.2) / 3
        al = seg(t, s, s + 0.4)
        y = 850 + i * 130 + int((1 - al) * 20)
        box(f, 160, y, W - 160, y + 100, (17, 48, 42), al, outline=ACC)
        tx(f, "✓", W - 230, y + 50, font(SANSB, 48), ACC, al)
        tx(f, r, W - 310, y + 50, font(SANSB, 52), INK, al, anchor="rm")


def scene_close(f, t, d):
    header(f, "احكم بنفسك", GOLD, t, d)
    for i, ln in enumerate(["اقرأ الحديث", "اقرأ التاريخ", "ثم احكم"]):
        s = 0.4 + i * 0.7
        tx(f, ln, W // 2, 560 + i * 130, font(SANSB, 72), GOLD if i == 2 else INK, seg(t, s, s + 0.5))
    tx(f, "تحقق من كل مصدر قبل أن تنقل", W // 2, 1140, font(SANS, 38), MUTED, seg(t, d * 0.5, d * 0.5 + 0.6))


SCENES = [scene_hook, scene_description, scene_city, scene_history, scene_objection, scene_close]


def caption_chunks(text, vs, ve):
    ws = text.split()
    chunks = [ws[i:i + 4] for i in range(0, len(ws), 4)]
    tot = sum(max(1, len(w)) for w in ws)
    pos, res = vs, []
    for ch in chunks:
        words = []
        for w in ch:
            dur = (ve - vs) * max(1, len(w)) / tot
            words.append((w, pos, pos + dur))
            pos += dur
        res.append(words)
    return res


def draw_caption(f, chunks, t):
    for words in chunks:
        if words[0][1] - 0.05 <= t < words[-1][2] + 0.25:
            fnt = font(SANSB, 62)
            d = ImageDraw.Draw(f)
            widths = [d.textlength(w + " ", font=fnt) for w, _, _ in words]
            total = sum(widths)
            box(f, int(W / 2 - total / 2) - 30, 1390, int(W / 2 + total / 2) + 30, 1500, (8, 12, 11), 0.7, radius=26)
            x = W / 2 + total / 2  # first word at the right edge
            for (w, s, e), wd in zip(words, widths):
                tx(f, w, x, 1445, fnt, GOLD if s <= t < e else INK, anchor="rm")
                x -= wd
            return


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--voice")
    ap.add_argument("--music")
    ap.add_argument("--out")
    ap.add_argument("--max-seconds", type=float)
    ap.add_argument("--speed", type=float, default=1.0, help="draft only: playback speed multiplier")
    a = ap.parse_args()
    script = json.load(open(os.path.join(HERE, "script_ar.json")))
    plan, total = plan_timing(script, a.voice)
    if a.speed != 1.0 and not a.voice:
        plan = [tuple(x / a.speed for x in p) for p in plan]
        total /= a.speed
    if a.max_seconds:
        total = min(total, a.max_seconds)
    out = a.out or os.path.join(HERE, "baghdad_ar_final.mp4" if a.voice else "baghdad_ar_draft.mp4")
    audio = os.path.join(HERE, ".audio_ar.m4a")
    make_audio(audio, total, a.voice, a.music)
    bg, pat, n = make_background()
    caps = [caption_chunks(s["text"], p[2], p[3]) for s, p in zip(script, plan)]
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", audio, "-c:v", "libx264",
                           "-pix_fmt", "yuv420p", "-crf", "20", "-preset", "medium", "-c:a", "aac",
                           "-b:a", "192k", "-movflags", "+faststart", "-t", f"{total:.2f}", out],
                          stdin=subprocess.PIPE)
    for i in range(int(total * FPS)):
        t = i / FPS
        si = next((k for k, p in enumerate(plan) if p[0] <= t < p[1]), len(plan) - 1)
        s0, s1 = plan[si][0], plan[si][1]
        ox, oy = int(t * 6) % n, int(t * 4) % n
        f = bg.copy()
        f.alpha_composite(pat.crop((ox, oy, ox + W, oy + H)))
        sp = a.speed if not a.voice else 1.0
        SCENES[si](f, (t - s0) * sp, (s1 - s0) * sp)
        draw_caption(f, caps[si], t)
        if not a.voice:
            tx(f, "مسودة · توقيت تقديري · بلا صوت", W // 2, 1700, font(SANSB, 30), WARN, 0.9)
        ff.stdin.write(f.convert("RGB").tobytes())
    ff.stdin.close()
    ff.wait()
    os.remove(audio)
    print("wrote", out, f"({total:.1f}s)")


if __name__ == "__main__":
    main()
