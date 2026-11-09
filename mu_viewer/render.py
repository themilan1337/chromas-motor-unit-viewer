"""Turns a plain payload dict into one self-contained HTML file (no network, no CDN)."""
import base64
import json
from pathlib import Path

import cv2
import numpy as np

NOTE = (
    "Each row is one cluster of independent components (ICs) found by CHROMAS: the lab's putative motor unit. "
    "<b>|r|</b> is the absolute Pearson correlation between the time courses of two ICs, the matrix CHROMAS clusters on "
    "(<code>ica_slice_clustering.py</code>, <code>np.abs(np.corrcoef(...))</code>). The mean, min and max per unit are this viewer's own "
    "summary of that matrix; the lab defines no single per-unit number. A high value is a sign of shared drive, not proof "
    "(a motor unit means the muscles share a motor neuron, shown by single-neuron stimulation)."
)


def png_data_uri(img_rgb: np.ndarray) -> str:
    ok, buf = cv2.imencode(".jpg", cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 85])
    assert ok
    return "data:image/jpeg;base64," + base64.b64encode(buf.tobytes()).decode()


def render(payload: dict, out: str | Path) -> Path:
    payload["meta"]["note"] = NOTE + "<br>" + payload["meta"].get("source", "")
    html = (Path(__file__).parent / "template.html").read_text().replace("__DATA__", json.dumps(payload, allow_nan=False))
    out = Path(out)
    out.write_text(html)
    return out
