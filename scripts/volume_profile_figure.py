#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["matplotlib", "pyarrow", "numpy"]
# ///
"""Render the wiki's volume-profile figure from real bars.

    ./scripts/volume_profile_figure.py --parquet SPY_massive_15m.parquet \
        --symbol SPY --timeframe 15m --length 400 --end 840

The profile is a line-by-line port of `crates/pine-builtins/src/vp/mod.rs` — the
absolute snapped price ladder, the overlap-proportional spread, the heavier-neighbour
value-area expansion and the local-minimum LVN — so every number annotated on the
figure is the one `vp.*` returns for the same window. It is not an illustration.
"""

from __future__ import annotations

import argparse
import math
from collections import OrderedDict

import numpy as np
import pyarrow.parquet as pq
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

# ── the ladder (port of vp/mod.rs) ─────────────────────────────────────────────────

DEFAULT_BINS = 50
DEFAULT_VA = 0.70


def snap_width(raw: float, scale: float) -> float:
    """Snap to a 1/2/5 x 10^n grid so rung edges are round prices."""
    if not (raw > 0.0 and math.isfinite(raw)):
        raw = abs(scale) * 1e-4 if math.isfinite(scale) and abs(scale) > 0 else 1e-8
    base = 10.0 ** math.floor(math.log10(raw))
    m = raw / base
    mult = 1.0 if m <= 1.0 else 2.0 if m <= 2.0 else 5.0 if m <= 5.0 else 10.0
    return base * mult


def spread(high: float, low: float, volume: float, w: float) -> list[tuple[int, float]]:
    """Spread one bar's volume across the rungs its range overlaps, proportional to overlap."""
    if volume <= 0.0:
        return []
    k_lo = math.floor(low / w)
    k_hi = math.floor(high / w)
    if k_lo == k_hi or high <= low:
        return [(k_lo, volume)]
    span = high - low
    out = []
    for k in range(k_lo, k_hi + 1):
        rung_lo = k * w
        overlap = min(high, rung_lo + w) - max(low, rung_lo)
        if overlap > 0.0:
            out.append((k, volume * overlap / span))
    return out


def build_profile(high, low, volume, length: int, bins: int = DEFAULT_BINS):
    """The profile of the window ENDING at the last bar. Width re-derived from the window."""
    h, l, v = high[-length:], low[-length:], volume[-length:]
    w = snap_width((h.max() - l.min()) / bins, h.max())
    hist: dict[int, float] = {}
    for i in range(len(h)):
        for k, vol in spread(float(h[i]), float(l[i]), float(v[i]), w):
            hist[k] = hist.get(k, 0.0) + vol
    return w, OrderedDict(sorted(hist.items())), sum(hist.values())


def levels(hist, total, w, va: float = DEFAULT_VA):
    """POC and value area: expand outward from the POC, always taking the heavier neighbour."""
    rungs = list(hist.items())
    poc_ix = max(range(len(rungs)), key=lambda i: rungs[i][1])
    target = total * va
    lo_ix = hi_ix = poc_ix
    acc = rungs[poc_ix][1]
    while acc < target and (lo_ix > 0 or hi_ix + 1 < len(rungs)):
        below = rungs[lo_ix - 1][1] if lo_ix > 0 else -1.0
        above = rungs[hi_ix + 1][1] if hi_ix + 1 < len(rungs) else -1.0
        if above >= below:
            hi_ix += 1
            acc += above
        else:
            lo_ix -= 1
            acc += below
    return {
        "poc": (rungs[poc_ix][0] + 0.5) * w,
        "vah": (rungs[hi_ix][0] + 1) * w,
        "val": rungs[lo_ix][0] * w,
        "poc_ix": poc_ix,
        "lo_ix": lo_ix,
        "hi_ix": hi_ix,
    }


def lvn(hist, w, price: float, downward: bool):
    """Nearest low-volume node: a dip the profile comes back UP from, over the DENSE rung range."""
    if w <= 0.0 or len(hist) < 2:
        return None
    keys = list(hist.keys())
    min_k, max_k = keys[0], keys[-1]
    vol = lambda k: hist.get(k, 0.0)
    here = min(max(math.floor(price / w), min_k), max_k)
    ks = list(range(min_k, here + 1))[::-1] if downward else list(range(here, max_k + 1))
    if len(ks) < 3:
        return None
    prev = vol(ks[0])
    run = None
    for i in range(1, len(ks)):
        val_i = vol(ks[i])
        if run is not None and val_i == run[2]:
            run = (run[0], i, run[2])
        elif run is not None and val_i > run[2]:
            centre = (ks[run[0]] + ks[run[1]]) / 2.0
            return (centre + 0.5) * w
        elif val_i < prev:
            run = (i, i, val_i)
        prev = val_i
    return None


# ── palette (dataviz skill, dark mode; validated all-pairs) ────────────────────────

SURFACE = "#1a1a19"
INK = "#ffffff"
INK_2 = "#c3c2b7"
INK_3 = "#8a8a80"
GRID = "#2f2f2d"
BLUE = "#3987e5"   # slot 1 — the profile and its value area
ORANGE = "#d95926"  # slot 2 — the point of control
AQUA = "#199e70"   # slot 3 — low-volume nodes
BLUE_MUTE = "#2b4c72"  # bins outside the value area: same hue, receded


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--parquet", required=True,
                    help="OHLCV parquet: ts_event, open, high, low, close, volume")
    ap.add_argument("--symbol", default="SPY")
    ap.add_argument("--timeframe", default="1D")
    ap.add_argument("--length", type=int, default=500)
    ap.add_argument("--bins", type=int, default=DEFAULT_BINS)
    ap.add_argument("--va", type=float, default=DEFAULT_VA)
    ap.add_argument("--end", type=int, default=0, help="bars to drop off the end")
    ap.add_argument("--out", default="images/volume-profile.png")
    args = ap.parse_args()

    t = pq.read_table(args.parquet).to_pydict()
    n = len(t["close"]) - args.end
    ts = np.array(t["ts_event"][:n])
    high = np.array(t["high"][:n], dtype=float)
    low = np.array(t["low"][:n], dtype=float)
    close = np.array(t["close"][:n], dtype=float)
    volume = np.array(t["volume"][:n], dtype=float)

    L = args.length
    w, hist, total = build_profile(high, low, volume, L, args.bins)
    lv = levels(hist, total, w, args.va)
    poc, vah, val = lv["poc"], lv["vah"], lv["val"]
    px = float(close[-1])
    lvn_lo = lvn(hist, w, px, True)
    lvn_hi = lvn(hist, w, px, False)
    va_pos = (px - val) / (vah - val)
    va_width = 100.0 * (vah - val) / poc

    print(f"window {L} bars  bins {args.bins}  va {args.va}  rung width {w}")
    print(f"poc {poc:.2f}  vah {vah:.2f}  val {val:.2f}")
    print(f"lvn_below {lvn_lo}  lvn_above {lvn_hi}")
    print(f"va_pos {va_pos:.4f}  va_width {va_width:.4f}  close {px:.2f}")

    # ── figure ────────────────────────────────────────────────────────────────────
    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "figure.facecolor": SURFACE,
        "axes.facecolor": SURFACE,
        "text.color": INK_2,
        "axes.labelcolor": INK_3,
        "xtick.color": INK_3,
        "ytick.color": INK_3,
    })

    fig = plt.figure(figsize=(13.6, 7.2), dpi=140)
    fig.subplots_adjust(left=0.045, right=0.795, top=0.855, bottom=0.095, wspace=0.03)
    gs = fig.add_gridspec(1, 2, width_ratios=[2.35, 1.0], wspace=0.03)
    axp = fig.add_subplot(gs[0, 0])   # price
    axh = fig.add_subplot(gs[0, 1], sharey=axp)  # histogram

    hp, lp = high[-L:], low[-L:]
    cp = close[-L:]
    x = np.arange(L)

    # price panel — the high/low envelope is what actually gets binned, so show it
    axp.fill_between(x, lp, hp, color=INK_2, alpha=0.13, linewidth=0)
    axp.plot(x, cp, color=INK_2, linewidth=1.0, alpha=0.85)

    # value area band
    axp.axhspan(val, vah, color=BLUE, alpha=0.10, linewidth=0, zorder=0)
    axh.axhspan(val, vah, color=BLUE, alpha=0.10, linewidth=0, zorder=0)

    for ax in (axp, axh):
        ax.axhline(vah, color=BLUE, linewidth=1.4, linestyle=(0, (6, 3)), zorder=3)
        ax.axhline(val, color=BLUE, linewidth=1.4, linestyle=(0, (6, 3)), zorder=3)
        ax.axhline(poc, color=ORANGE, linewidth=2.0, zorder=4)
        for y in (lvn_lo, lvn_hi):
            if y is not None:
                ax.axhline(y, color=AQUA, linewidth=1.4, linestyle=(0, (2, 2.5)), zorder=3)

    # the close, and where it sits inside the value area
    axp.plot([L - 1], [px], marker="o", markersize=7, color=INK,
             markeredgecolor=SURFACE, markeredgewidth=1.6, zorder=6)

    # histogram — the rungs, lowest price first
    ks = list(hist.keys())
    vols = np.array([hist[k] for k in ks])
    ys = np.array([k * w for k in ks])
    inside = np.array([lv["lo_ix"] <= i <= lv["hi_ix"] for i in range(len(ks))])
    colors = [BLUE if ins else BLUE_MUTE for ins in inside]
    colors[lv["poc_ix"]] = ORANGE
    axh.barh(ys + w / 2.0, vols, height=w * 0.80, color=colors,
             edgecolor=SURFACE, linewidth=0.6, zorder=2)

    # ── labels ────────────────────────────────────────────────────────────────────
    lo_y, hi_y = float(lp.min()), float(hp.max())
    pad = (hi_y - lo_y) * 0.045
    axp.set_ylim(lo_y - pad, hi_y + pad)
    axp.set_xlim(-L * 0.015, L * 1.015)
    axh.set_xlim(0, vols.max() * 1.06)

    for ax in (axp, axh):
        ax.grid(axis="y", color=GRID, linewidth=0.7, alpha=0.55, zorder=0)
        for s in ax.spines.values():
            s.set_visible(False)
        ax.tick_params(length=0, labelsize=10.5)
    axh.tick_params(labelleft=False)
    axh.set_xticks([])
    axp.set_xticks([0, L - 1])
    axp.set_xticklabels([str(ts[-L])[:10], str(ts[-1])[:10]], fontsize=10.5)
    for lbl, ha in zip(axp.get_xticklabels(), ("left", "right")):
        lbl.set_horizontalalignment(ha)

    xr = axh.get_xlim()[1]

    def level_label(y, text, color, weight="normal"):
        axh.annotate(text, xy=(xr, y), xytext=(xr * 1.045, y), va="center", ha="left",
                     fontsize=12.5, color=color, weight=weight,
                     annotation_clip=False, zorder=8)

    level_label(vah, f"vp.vah  {vah:,.2f}", BLUE)
    level_label(poc, f"vp.poc  {poc:,.2f}", ORANGE, "bold")
    level_label(val, f"vp.val  {val:,.2f}", BLUE)
    if lvn_hi is not None:
        level_label(lvn_hi, f"vp.lvn_above  {lvn_hi:,.2f}", AQUA)
    if lvn_lo is not None:
        level_label(lvn_lo, f"vp.lvn_below  {lvn_lo:,.2f}", AQUA)

    # va_width: a bracket spanning the value area
    bx = xr * 1.55
    axh.annotate("", xy=(bx, val), xytext=(bx, vah),
                 arrowprops=dict(arrowstyle="<->", color=INK_3, linewidth=1.1),
                 annotation_clip=False, zorder=8)
    axh.annotate(f"vp.va_width\n{va_width:.2f}% of POC", xy=(bx * 1.012, (val + vah) / 2),
                 va="center", ha="left", fontsize=11.5, color=INK_2,
                 annotation_clip=False, zorder=8)

    # va_pos: the close's height inside the value area, 0 at VAL and 1 at VAH
    axp.annotate(f"close {px:,.2f}\nvp.va_pos = {va_pos:.2f}",
                 xy=(L - 1, px), xytext=(L * 0.700, px + (hi_y - lo_y) * 0.075),
                 fontsize=11.5, color=INK, ha="right", va="bottom",
                 arrowprops=dict(arrowstyle="-", color=INK_3, linewidth=1.0,
                                 connectionstyle="arc3,rad=-0.15"), zorder=8)
    for y, lab in ((val, "va_pos 0"), (vah, "va_pos 1")):
        axp.annotate(lab, xy=(L * 0.012, y), fontsize=10.5, color=BLUE, va="center", ha="left",
                     bbox=dict(boxstyle="round,pad=0.22", fc=SURFACE, ec="none", alpha=0.85),
                     zorder=7)

    # one rung, named: vp.histogram()[i] is its length, vp.bin_low(i) is its price floor.
    # Annotated low in the profile, where the rungs are short and the panel has room.
    i_ann = max(0, lv["lo_ix"] - 8)
    y_ann, v_ann = ys[i_ann], vols[i_ann]
    # Both callouts sit BELOW the rung and their leaders run parallel — the shorter reach to
    # the bar tip above the longer one to the rung floor, so they never cross.
    tx = vols.max() * 0.46
    axh.annotate(f"vp.histogram(...)[{i_ann}]  =  {v_ann / 1e6:,.2f}M",
                 xy=(v_ann, y_ann + w / 2), xytext=(tx, y_ann - w * 3.6),
                 fontsize=11, color=INK_2, ha="left", va="center",
                 arrowprops=dict(arrowstyle="->", color=INK_3, linewidth=0.9,
                                 shrinkA=4, shrinkB=3), zorder=8)
    axh.plot([0, v_ann * 1.10], [y_ann, y_ann], color=INK_3, linewidth=0.9,
             linestyle=(0, (3, 2)), zorder=7)
    axh.annotate(f"vp.bin_low(..., {i_ann})  =  {y_ann:,.2f}",
                 xy=(v_ann * 1.10, y_ann), xytext=(tx, y_ann - w * 7.2),
                 fontsize=11, color=INK_2, ha="left", va="center",
                 arrowprops=dict(arrowstyle="->", color=INK_3, linewidth=0.9,
                                 shrinkA=4, shrinkB=2), zorder=8)

    # titles
    fig.text(0.045, 0.955, f"[poc, vah, val] = vp.rolling({L}, {args.bins})",
             fontsize=17, color=INK, weight="bold", family="DejaVu Sans Mono"
             if "DejaVu Sans Mono" in {f.name for f in matplotlib.font_manager.fontManager.ttflist}
             else "DejaVu Sans")
    fig.text(0.045, 0.912,
             f"{args.symbol} {args.timeframe}: {L} bars binned onto a {w:g}-wide price ladder, "
             f"{int(args.va * 100)}% value area",
             fontsize=12, color=INK_3)
    fig.text(0.640, 0.912, "volume traded at price  →", fontsize=11, color=INK_3)
    for i, (c, lab) in enumerate(((BLUE, "rungs inside the value area"),
                                  (BLUE_MUTE, "rungs outside it"))):
        yy = 0.862 - i * 0.030
        fig.patches.append(Rectangle((0.640, yy), 0.011, 0.018, transform=fig.transFigure,
                                     facecolor=c, edgecolor="none", zorder=9))
        fig.text(0.657, yy + 0.004, lab, fontsize=10.5, color=INK_3)
    axp.set_ylabel("price", fontsize=11.5, color=INK_3, labelpad=6)

    fig.savefig(args.out, facecolor=SURFACE, bbox_inches="tight", pad_inches=0.22)
    print("wrote", args.out)


if __name__ == "__main__":
    main()
