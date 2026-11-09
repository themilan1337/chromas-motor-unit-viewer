"""Minimal decord stand-in on OpenCV, only because decord has no wheel for macOS arm64.

Not part of the lab's code. Covers the calls CHROMAS 0.1.1 makes: VideoReader(path), len(),
vr[i].asnumpy(), vr.get_batch([i,..]).asnumpy(), vr.next(), vr.get_avg_fps(), bridge.set_bridge().
Frames are returned as RGB uint8, like decord.
"""
import cv2
import numpy as np


class _Arr:
    def __init__(self, a):
        self._a = a

    def asnumpy(self):
        return self._a

    @property
    def shape(self):
        return self._a.shape


class VideoReader:
    def __init__(self, path, *args, **kwargs):
        self._cap = cv2.VideoCapture(str(path))
        if not self._cap.isOpened():
            raise RuntimeError(f"cannot open {path}")
        self._n = int(self._cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self._fps = float(self._cap.get(cv2.CAP_PROP_FPS))
        self._pos = 0

    def __len__(self):
        return self._n

    def _read(self, i):
        i = int(i) % self._n if i < 0 else int(i)
        if i != self._pos:
            self._cap.set(cv2.CAP_PROP_POS_FRAMES, i)
        ok, f = self._cap.read()
        if not ok:
            raise IndexError(i)
        self._pos = i + 1
        return cv2.cvtColor(f, cv2.COLOR_BGR2RGB)

    def __getitem__(self, i):
        return _Arr(self._read(i))

    def get_batch(self, idx):
        return _Arr(np.stack([self._read(i) for i in idx]))

    def next(self):
        return _Arr(self._read(self._pos))

    def get_avg_fps(self):
        return self._fps

    def seek(self, i):
        self._pos = -1
        self._read(i)
        self._pos = i


class bridge:
    @staticmethod
    def set_bridge(name):
        pass
