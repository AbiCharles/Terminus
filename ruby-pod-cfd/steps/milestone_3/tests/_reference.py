"""Independent reference POD (the verifier's answer key).

Reads the canonical CFD fixtures the API serves and recomputes, with numpy, the
assembled snapshot matrix and its method-of-snapshots POD. It never reads the
agent's outputs, so a fabricated or mis-computed result is rejected.
"""
import json
import os

import numpy as np

FIX = os.environ.get("CFD_FIXTURES_DIR", "/opt/api/fixtures")
THRESHOLD = 0.99  # the energy threshold the milestone-3 reports are graded at


def index():
    return json.load(open(os.path.join(FIX, "index.json")))["experiments"]


def fixture_ids():
    return [e["id"] for e in index() if e["is_fixture"]]


def nonfixture_ids():
    return [e["id"] for e in index() if not e["is_fixture"]]


def assemble(eid):
    d = json.load(open(os.path.join(FIX, f"{eid}.json")))
    frames = sorted(d["frames"], key=lambda f: f["index"])
    X = np.array([f["values"] for f in frames], dtype=np.float64).T  # m x n
    return X, d["meta"]


def pod(X):
    n = X.shape[1]
    Xc = X - X.mean(axis=1, keepdims=True)
    C = (Xc.T @ Xc) / (n - 1)
    eig = np.clip(np.linalg.eigvalsh(C)[::-1], 0.0, None)
    total = eig.sum()
    frac = eig / total
    cum = np.cumsum(frac)
    return eig, frac, cum


def select_k(cum, theta):
    idx = int(np.searchsorted(cum, theta, side="left"))
    return min(idx + 1, len(cum))


def recon_error(eig, k):
    return float(np.sqrt(eig[k:].sum() / eig.sum()))
