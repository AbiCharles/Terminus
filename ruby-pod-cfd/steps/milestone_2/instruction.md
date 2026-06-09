Extend `/app/pod_cli.rb` to compute the proper orthogonal decomposition (POD) of each fixture's snapshot matrix by covariance eigenanalysis — implemented from scratch (no linear-algebra libraries).

For each fixture's matrix `X` (`m × n`): subtract the per-DOF mean across the `n` frames to get `Xc`; form the method-of-snapshots covariance `C = (1/(n − 1)) · Xcᵀ · Xc` (an `n × n` symmetric matrix); and compute its eigenvalues with your own symmetric eigensolver (for example cyclic Jacobi rotations). Sort the eigenvalues in descending order and clip any tiny negative round-off up to `0`. The modal **energy fraction** of mode `i` is `λ_i / Σ λ`; the **cumulative variance** is the running sum of energy fractions.

Write `/app/output/<experiment_id>/modal_energy.json`:

```json
{ "experiment_id": "<string>",
  "modes": [ { "mode_index": <int>, "eigenvalue": <float>, "energy_fraction": <float>, "cumulative_fraction": <float> }, ... ] }
```

and `/app/output/<experiment_id>/modal_energy.csv` with the exact header `mode_index,eigenvalue,energy_fraction,cumulative_fraction`. `mode_index` is 0-based in descending-energy order. The milestone 1 output must still be produced.
