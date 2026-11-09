"""Runs the unmodified CHROMAS 0.1.1 CLI on a Mac. Not part of the lab's code.

CHROMAS segmentation calls .cuda() unconditionally (segmentation_neuralnet.py lines 110, 176, 345) and builds a half-precision model.
This wrapper redirects .cuda() to the device in CHROMAS_DEVICE (mps by default, cpu as fallback; on cpu .half() becomes float32),
then hands over to the normal click CLI. No file of the lab's package is edited.

Second patch: slicing.py lines 137-139 call np.cross on 2-D vectors, which NumPy 2.0 removed (the lab's pyproject asks for numpy ^2.2.2, so
`chromas slice` raises "Both input arrays must be (arrays of) 3-dimensional vectors" on the pinned stack). For 2-D input the old result is the
scalar a0*b1 - a1*b0, which is what the wrapper restores.
"""
import os
import sys

import torch

dev = os.environ.get("CHROMAS_DEVICE", "mps")
torch.Tensor.cuda = lambda self, *a, **k: self.to(dev)
torch.nn.Module.cuda = lambda self, *a, **k: self.to(dev)
if dev == "cpu":
    torch.Tensor.half = lambda self, *a, **k: self.float()
    torch.nn.Module.half = lambda self, *a, **k: self.float()

import numpy as np

_np_cross = np.cross


def _cross2d(a, b, *args, **kwargs):
    a, b = np.asarray(a), np.asarray(b)
    if a.shape[-1] == 2 and b.shape[-1] == 2:
        return a[..., 0] * b[..., 1] - a[..., 1] * b[..., 0]
    return _np_cross(a, b, *args, **kwargs)


np.cross = _cross2d

from chromas.chromas import cli

if __name__ == "__main__":
    sys.argv[0] = "chromas"
    cli()
