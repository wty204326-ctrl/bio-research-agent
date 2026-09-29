#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""论文/汇报图像裁切·拼接·标注工具箱（PIL，输出一律纯白背景）
子命令:
  info IMG                                        尺寸/模式
  autocrop IMG OUT [--pad 20] [--thr 245]         去白边
  crop IMG OUT --box x0,y0,x1,y1                  坐标裁切
  stitch OUT --imgs a.png b.png ... [--cols 2] [--gap 12] [--pad 12]
      [--labels A,B,C] [--label-size 48] [--uniform-height] 网格拼接+面板字母
  scalebar IMG OUT --px 100 --um 50 [--pos br] [--color white] [--th 6]  比例尺
  whitebg IMG OUT                                 透明→纯白铺平
  annotate IMG OUT [--box x,y,w,h] [--box-color red] [--arrow x1,y1,x2,y2]
      [--text x,y,STR] [--circle x,y,r]          方框/箭头/文字/圆圈标注
坐标一律像素（左上原点）。--box-color 可选 red/green/blue/black/white/#RRGGBB。
"""
import argparse, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

def load_rgb(p):
    im = Image.open(p)
    if im.mode in ("RGBA", "LA", "P"):
        bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
        im = Image.alpha_composite(bg, im.convert("RGBA")).convert("RGB")
    else:
        im = im.convert("RGB")
    return im

def font(size, bold=True):
    for f in (r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf",
              r"C:\Windows\Fonts\msyhbd.ttc" if bold else r"C:\Windows\Fonts\msyh.ttc"):
        try:
            return ImageFont.truetype(f, size)
        except Exception:
            pass
    return ImageFont.load_default(size)

def color(s):
    named = {"red": (220, 30, 30), "green": (30, 160, 60), "blue": (30, 60, 220),
             "black": (0, 0, 0), "white": (255, 255, 255), "yellow": (240, 200, 0)}
    if s in named:
        return named[s]
    s = s.lstrip("#")
    return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))

def parse_xy(s, n):
    v = [int(x) for x in s.split(",")]
    assert len(v) == n, f"需要 {n} 个数: {s}"
    return v

def cmd_info(a):
    im = Image.open(a.img)
    print(f"{a.img}: {im.size[0]}x{im.size[1]} mode={im.mode}")

def cmd_autocrop(a):
    im = load_rgb(a.img)
    g = np.asarray(im.convert("L"))
    mask = g < a.thr
    if not mask.any():
        sys.exit("整图都接近白色，无内容可留")
    ys, xs = np.where(mask)
    x0, x1 = max(xs.min() - a.pad, 0), min(xs.max() + 1 + a.pad, im.size[0])
    y0, y1 = max(ys.min() - a.pad, 0), min(ys.max() + 1 + a.pad, im.size[1])
    out = Image.new("RGB", (x1 - x0, y1 - y0), (255, 255, 255))
    out.paste(im.crop((x0, y0, x1, y1)), (0, 0))
    out.save(a.out, quality=95)
    print(f"[ok] {im.size} -> {out.size} (bbox {x0},{y0},{x1},{y1})")

def cmd_crop(a):
    x0, y0, x1, y1 = parse_xy(a.box, 4)
    im = load_rgb(a.img)
    out = Image.new("RGB", (x1 - x0, y1 - y0), (255, 255, 255))
    out.paste(im.crop((x0, y0, x1, y1)), (0, 0))
    out.save(a.out, quality=95)
    print(f"[ok] {im.size} -> {out.size}")

def cmd_stitch(a):
    imgs = [load_rgb(p) for p in a.imgs]
    if a.uniform_height:
        h = min(im.size[1] for im in imgs)
        imgs = [im.resize((int(im.size[0] * h / im.size[1]), h)) for im in imgs]
    cols = min(a.cols, len(imgs))
    rows = (len(imgs) + cols - 1) // cols
    cw = [max(im.size[0] for im in imgs[c::cols]) for c in range(cols)]
    ch = [max(im.size[1] for im in imgs[r * cols:(r + 1) * cols]) for r in range(rows)]
    W = sum(cw) + a.gap * (cols - 1) + a.pad * 2
    H = sum(ch) + a.gap * (rows - 1) + a.pad * 2
    canvas = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(canvas)
    labels = a.labels.split(",") if a.labels else []
    f = font(a.label_size)
    for i, im in enumerate(imgs):
        r, c = divmod(i, cols)
        ox = a.pad + sum(cw[:c]) + a.gap * c + (cw[c] - im.size[0]) // 2
        oy = a.pad + sum(ch[:r]) + a.gap * r
        canvas.paste(im, (ox, oy))
        if i < len(labels):
            d.text((a.pad + sum(cw[:c]) + a.gap * c + 4, oy + 2), labels[i].strip(),
                   fill=(0, 0, 0), font=f)
    canvas.save(a.out, quality=95)
    print(f"[ok] {len(imgs)} 图 -> {canvas.size} ({rows}x{cols}) -> {a.out}")

def cmd_scalebar(a):
    im = load_rgb(a.img)
    W, H = im.size
    d = ImageDraw.Draw(im)
    m = a.margin
    x1 = W - m
    x0 = W - m - a.px
    y = H - m
    c = color(a.color_)
    d.rectangle([x0, y - a.th, x1, y], fill=c)
    txt = f"{a.um} μm"
    f = font(max(16, a.th * 4))
    tw = d.textlength(txt, font=f)
    d.text((x0 + (a.px - tw) / 2, y - a.th - f.size - 6), txt, fill=c, font=f)
    im.save(a.out, quality=95)
    print(f"[ok] 比例尺 {a.px}px={a.um}μm -> {a.out}")

def cmd_whitebg(a):
    load_rgb(a.img).save(a.out, quality=95)
    print(f"[ok] 白底铺平 -> {a.out}")

def cmd_annotate(a):
    im = load_rgb(a.img)
    d = ImageDraw.Draw(im)
    if a.box:
        x, y, w, h = parse_xy(a.box, 4)
        d.rectangle([x, y, x + w, y + h], outline=color(a.box_color), width=a.box_width)
    if a.circle:
        x, y, r = parse_xy(a.circle, 3)
        d.ellipse([x - r, y - r, x + r, y + r], outline=color(a.box_color), width=a.box_width)
    if a.arrow:
        x1, y1, x2, y2 = parse_xy(a.arrow, 4)
        c = color(a.box_color)
        d.line([x1, y1, x2, y2], fill=c, width=a.box_width)
        ang = np.arctan2(y2 - y1, x2 - x1)
        L = max(10, a.box_width * 5)
        for s in (2.6, -2.6):
            d.line([x2, y2, x2 - L * np.cos(ang + s), y2 - L * np.sin(ang + s)], fill=c, width=a.box_width)
    if a.text:
        for spec in a.text:
            parts = spec.split(",", 2)
            if len(parts) == 3:
                d.text((int(parts[0]), int(parts[1])), parts[2], fill=color(a.box_color), font=font(a.label_size))
    im.save(a.out, quality=95)
    print(f"[ok] 标注 -> {a.out}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("info"); s.add_argument("img"); s.set_defaults(f=cmd_info)
    s = sub.add_parser("autocrop"); s.add_argument("img"); s.add_argument("out")
    s.add_argument("--pad", type=int, default=20); s.add_argument("--thr", type=int, default=245)
    s.set_defaults(f=cmd_autocrop)
    s = sub.add_parser("crop"); s.add_argument("img"); s.add_argument("out")
    s.add_argument("--box", required=True); s.set_defaults(f=cmd_crop)
    s = sub.add_parser("stitch"); s.add_argument("out")
    s.add_argument("--imgs", nargs="+", required=True)
    s.add_argument("--cols", type=int, default=2); s.add_argument("--gap", type=int, default=12)
    s.add_argument("--pad", type=int, default=12); s.add_argument("--labels", default=None)
    s.add_argument("--label-size", type=int, default=48)
    s.add_argument("--uniform-height", action="store_true")
    s.set_defaults(f=cmd_stitch)
    s = sub.add_parser("scalebar"); s.add_argument("img"); s.add_argument("out")
    s.add_argument("--px", type=int, required=True); s.add_argument("--um", type=float, required=True)
    s.add_argument("--pos", default="br"); s.add_argument("--color", dest="color_", default="white")
    s.add_argument("--th", type=int, default=6); s.add_argument("--margin", type=int, default=30)
    s.set_defaults(f=cmd_scalebar)
    s = sub.add_parser("whitebg"); s.add_argument("img"); s.add_argument("out"); s.set_defaults(f=cmd_whitebg)
    s = sub.add_parser("annotate"); s.add_argument("img"); s.add_argument("out")
    s.add_argument("--box"); s.add_argument("--circle"); s.add_argument("--arrow")
    s.add_argument("--text", action="append"); s.add_argument("--box-color", default="red")
    s.add_argument("--box-width", type=int, default=4)
    s.add_argument("--label-size", type=int, default=36)
    s.set_defaults(f=cmd_annotate)
    a = ap.parse_args()
    a.f(a)
