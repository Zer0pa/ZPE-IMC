from __future__ import annotations

import math
import os
import re
import tempfile
import xml.etree.ElementTree as ET
from typing import Iterable, List, Sequence, Tuple

from .quantize import PolylineShape

try:
    from svgpathtools import svg2paths2 as _SVG2PATHS2  # type: ignore
except ImportError:  # pragma: no cover - exercised when dependency missing
    _SVG2PATHS2 = None


def _require_svgpathtools():
    if _SVG2PATHS2 is None:  # pragma: no cover - exercised when dependency missing
        raise ImportError(
            "svgpathtools is required for diagram SVG ingestion. "
            "Install via `pip install zpe-multimodal[diagram]`."
        )
    return _SVG2PATHS2


def _sample_path(path, max_seg: float) -> List[Tuple[float, float]]:
    """Sample an svgpathtools Path into a list of complex points."""
    length = path.length(error=1e-4)
    if length == 0:
        return []
    # number of samples such that max segment length <= max_seg
    n_samples = max(int(math.ceil(length / max_seg)), 2)
    pts = [path.point(t) for t in [i / (n_samples - 1) for i in range(n_samples)]]
    out: List[Tuple[float, float]] = []
    for p in pts:
        out.append((p.real, p.imag))
    return out


def _parse_transform(transform_str: str | None) -> Tuple[float, float, float, float, float, float]:
    """
    Parse a limited SVG transform string into an affine matrix (a, b, c, d, e, f):
    [a c e]
    [b d f]
    [0 0 1]
    Supports translate(tx, ty?), scale(sx, sy?), rotate(angle) about origin.
    """
    if not transform_str:
        return (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)
    a = 1.0
    b = 0.0
    c = 0.0
    d = 1.0
    e = 0.0
    f = 0.0
    for cmd, args_str in re.findall(r"([a-zA-Z]+)\(([^)]+)\)", transform_str):
        args = [float(x) for x in re.split(r"[ ,]+", args_str.strip()) if x]
        if cmd == "translate":
            tx = args[0]
            ty = args[1] if len(args) > 1 else 0.0
            e += tx
            f += ty
        elif cmd == "scale":
            sx = args[0]
            sy = args[1] if len(args) > 1 else sx
            a *= sx
            d *= sy
        elif cmd == "rotate":
            ang = math.radians(args[0])
            cos_a = math.cos(ang)
            sin_a = math.sin(ang)
            # multiply current matrix by rotation
            na = a * cos_a + c * -sin_a
            nb = b * cos_a + d * -sin_a
            nc = a * sin_a + c * cos_a
            nd = b * sin_a + d * cos_a
            a, b, c, d = na, nb, nc, nd
        elif cmd == "matrix" and len(args) == 6:
            ma, mb, mc, md, me, mf = args
            na = a * ma + c * mb
            nb = b * ma + d * mb
            nc = a * mc + c * md
            nd = b * mc + d * md
            ne = a * me + c * mf + e
            nf = b * me + d * mf + f
            a, b, c, d, e, f = na, nb, nc, nd, ne, nf
        # other transforms ignored in spike
    return (a, b, c, d, e, f)


def _apply_affine(pt: Tuple[float, float], m: Tuple[float, float, float, float, float, float]) -> Tuple[float, float]:
    x, y = pt
    a, b, c, d, e, f = m
    return (a * x + c * y + e, b * x + d * y + f)


def _parse_style(attr: dict) -> Tuple[str | None, float | None, str | None]:
    stroke = attr.get("stroke")
    stroke_width = attr.get("stroke-width")
    fill = attr.get("fill")
    style = attr.get("style", "")
    if style:
        # simple style parser: key:value; pairs
        for kv in style.split(";"):
            if ":" not in kv:
                continue
            k, v = kv.split(":", 1)
            k = k.strip()
            v = v.strip()
            if k == "stroke":
                stroke = v
            elif k == "stroke-width":
                stroke_width = v
            elif k == "fill":
                fill = v
    sw = None
    if stroke_width is not None:
        try:
            sw = float(stroke_width)
        except Exception:
            sw = None
    return stroke, sw, fill


def _parse_style_string(style: str) -> dict:
    out = {}
    for kv in style.split(";"):
        if ":" not in kv:
            continue
        k, v = kv.split(":", 1)
        out[k.strip()] = v.strip()
    return out


def _collect_inherited_styles(svg_text: str) -> List[dict]:
    """
    Traverse SVG XML and collect cascaded stroke/fill/stroke-width/transform per drawable element.
    Order aligns with svgpathtools output (document order of shapes/paths).
    """
    try:
        root = ET.fromstring(svg_text)
    except ET.ParseError:
        return []

    supported = {"path", "line", "rect", "polyline", "polygon", "circle", "ellipse"}
    styles: List[dict] = []

    def walk(elem, inherited: dict):
        current = dict(inherited)
        style_attr = elem.attrib.get("style")
        if style_attr:
            current.update(_parse_style_string(style_attr))
        for key in ("stroke", "fill", "stroke-width", "transform"):
            if key in elem.attrib:
                current[key] = elem.attrib[key]
        if elem.tag.split("}")[-1] in supported:
            styles.append(current)
        for child in list(elem):
            walk(child, current)

    walk(root, {})
    return styles


def svg_to_polylines(svg_text: str, max_seg: float = 2.0, canvas_size: int = 256, padding: int = 4) -> List[PolylineShape]:
    """
    Parse an SVG string into normalized polylines.

    - Flattens supported shapes/paths into point lists.
    - Normalizes to fit within [0, canvas_size) with padding.
    """
    tmp = tempfile.NamedTemporaryFile("w+", suffix=".svg", delete=False, encoding="utf-8")
    svg2paths2 = _require_svgpathtools()
    try:
        tmp.write(svg_text)
        tmp.flush()
        paths, attrs, svg_attr = svg2paths2(tmp.name)
    finally:
        tmp.close()
        try:
            os.remove(tmp.name)
        except OSError:
            pass
    inherited_styles = _collect_inherited_styles(svg_text)
    polylines: List[PolylineShape] = []
    for idx, (path, attr) in enumerate(zip(paths, attrs)):
        pts = _sample_path(path, max_seg=max_seg)
        if not pts:
            continue
        inherited = inherited_styles[idx] if idx < len(inherited_styles) else {}
        stroke, stroke_width, fill = _parse_style(attr)
        if stroke is None:
            stroke = inherited.get("stroke")
        if stroke_width is None and inherited.get("stroke-width") is not None:
            try:
                stroke_width = float(inherited.get("stroke-width"))
            except Exception:
                stroke_width = None
        if fill is None:
            fill = inherited.get("fill")
        transform_str = attr.get("transform")
        inherited_transform = inherited.get("transform")
        if inherited_transform and transform_str:
            transform_str = f"{inherited_transform} {transform_str}"
        elif inherited_transform:
            transform_str = inherited_transform

        transform = _parse_transform(transform_str)
        pts = [_apply_affine(p, transform) for p in pts]
        polylines.append(
            PolylineShape(
                points=pts,
                stroke=stroke,
                stroke_width=stroke_width,
                fill=fill,
            )
        )

    if not polylines:
        return []

    # Normalize to canvas with padding
    all_x = [p[0] for poly in polylines for p in poly.points]
    all_y = [p[1] for poly in polylines for p in poly.points]
    min_x, max_x = min(all_x), max(all_x)
    min_y, max_y = min(all_y), max(all_y)
    width = max_x - min_x if max_x > min_x else 1.0
    height = max_y - min_y if max_y > min_y else 1.0
    scale = (canvas_size - 2 * padding) / max(width, height)

    normed: List[PolylineShape] = []
    for poly in polylines:
        normed_poly: List[Tuple[float, float]] = []
        for x, y in poly.points:
            nx = (x - min_x) * scale + padding
            ny = (y - min_y) * scale + padding
            normed_poly.append((nx, ny))
        normed.append(
            PolylineShape(
                points=normed_poly,
                stroke=poly.stroke,
                stroke_width=(poly.stroke_width * scale) if poly.stroke_width else None,
                fill=poly.fill,
            )
        )
    return normed


def polylines_to_svg(polylines: Sequence[PolylineShape], canvas_size: int = 256) -> str:
    """Emit a minimal SVG with one <polyline> per path, preserving stroke/fill width when present."""
    poly_elems: List[str] = []
    for poly in polylines:
        if len(poly.points) < 2:
            continue
        pts = " ".join(f"{x},{y}" for x, y in poly.points)
        stroke = poly.stroke or "black"
        fill = poly.fill or "none"
        width = poly.stroke_width if poly.stroke_width is not None else 1
        poly_elems.append(
            f'<polyline points="{pts}" fill="{fill}" stroke="{stroke}" stroke-width="{width}"/>'
        )
    body = "\n  ".join(poly_elems)
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {canvas_size} {canvas_size}" width="{canvas_size}" height="{canvas_size}">\n  {body}\n</svg>'
