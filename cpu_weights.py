"""The published weights were saved from CUDA tensors; chromas does torch.load(weights) without map_location, so it fails on a CPU/Mac.
This rewrites the same state dict with CPU tensors (values unchanged). Usage: python cpu_weights.py in.pth out.pth"""
import sys

import torch

sd = torch.load(sys.argv[1], map_location="cpu")
torch.save(sd, sys.argv[2])
print(len(sd), "tensors,", sum(v.numel() for v in sd.values() if hasattr(v, "numel")), "values ->", sys.argv[2])
