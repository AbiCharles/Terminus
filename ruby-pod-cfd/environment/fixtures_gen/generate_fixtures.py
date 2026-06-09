"""Generate deterministic CFD snapshot fixtures with a known low-rank POD structure.

Each experiment's snapshot matrix X is m x n (m spatial DOF, n frames):
    X[:, t] = mean_field + sum_k a_k[t] * phi_k   (+ small noise)
with orthonormal-ish spatial modes phi_k and decaying temporal amplitudes, so the
modal energy spectrum decays in a well-posed way for POD. Output is JSON files the
Rails API serves; the velocity values are float64 rounded to fixed precision so the
API payload is byte-identical across builds.
"""
import json
import os
import sys

import numpy as np

OUT = sys.argv[1] if len(sys.argv) > 1 else "/build/fixtures"
PAGE_SIZE = 8       # frames per snapshot page (forces pagination)
ROUND = 9           # decimal places stored in the API payload

# (id, is_fixture, m, n, n_modes, amp_decay, noise, seed, label)
EXPERIMENTS = [
    ("cfd_cylinder_re100", True, 192, 48, 6, 0.55, 0.01, 11, "vortex shedding, Re=100"),
    ("cfd_cavity_re400", True, 160, 40, 5, 0.6, 0.008, 23, "lid-driven cavity, Re=400"),
    ("cfd_channel_smoke", False, 120, 24, 4, 0.7, 0.02, 7, "non-fixture smoke test"),
]


def build_matrix(m, n, n_modes, amp_decay, noise, seed):
    rng = np.random.default_rng(seed)
    # orthonormal spatial modes via QR of a random matrix
    phi, _ = np.linalg.qr(rng.standard_normal((m, n_modes)))
    mean_field = 0.5 * rng.standard_normal(m)
    t = np.linspace(0.0, 2.0 * np.pi, n, endpoint=False)
    X = np.tile(mean_field[:, None], (1, n))
    for k in range(n_modes):
        amp = (amp_decay ** k)
        coeff = amp * np.cos((k + 1) * t + 0.3 * k)
        X += np.outer(phi[:, k], coeff)
    X += noise * rng.standard_normal((m, n))
    return np.round(X, ROUND)


def main():
    os.makedirs(OUT, exist_ok=True)
    index = []
    for (eid, is_fixture, m, n, n_modes, amp_decay, noise, seed, label) in EXPERIMENTS:
        X = build_matrix(m, n, n_modes, amp_decay, noise, seed)  # m x n
        meta = {
            "id": eid,
            "label": label,
            "is_fixture": is_fixture,
            "field": "velocity",
            "n_dofs": int(m),
            "n_frames": int(n),
            "page_size": PAGE_SIZE,
            "n_pages": int(np.ceil(n / PAGE_SIZE)),
        }
        # frames: column t is frame t (a flattened velocity field of length m)
        frames = [{"index": int(t), "values": X[:, t].tolist()} for t in range(n)]
        with open(os.path.join(OUT, f"{eid}.json"), "w") as fh:
            json.dump({"meta": meta, "frames": frames}, fh)
        index.append({k: meta[k] for k in ("id", "is_fixture", "n_dofs", "n_frames", "n_pages")})
    with open(os.path.join(OUT, "index.json"), "w") as fh:
        json.dump({"experiments": index}, fh, indent=2)
    print(f"wrote {len(EXPERIMENTS)} experiments to {OUT}")


if __name__ == "__main__":
    main()
