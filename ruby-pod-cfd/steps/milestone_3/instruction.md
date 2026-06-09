Extend `/app/pod_cli.rb` to select modes for an energy threshold and report the reconstruction error.

Given the energy threshold `θ` (the `--threshold` argument; graded at `0.99`), select the smallest number of leading modes `k` whose cumulative energy fraction is `≥ θ`. The relative **reconstruction error** of keeping `k` modes is

```
reconstruction_error = sqrt( ( Σ_{i ≥ k} λ_i ) / ( Σ_i λ_i ) )
```

with eigenvalues in descending order and `i` 0-based (so the kept modes are `0 … k−1`).

Write `/app/output/<experiment_id>/report.json`:

```json
{
  "experiment_id": "<string>",
  "energy_threshold": <float>,
  "n_selected_modes": <int k>,
  "selected_mode_indices": [0, 1, ..., k-1],
  "cumulative_at_selected": <float>,
  "reconstruction_error": <float>
}
```

and `/app/output/<experiment_id>/report.csv` with the exact header `experiment_id,energy_threshold,n_selected_modes,reconstruction_error`. Your CLI must honour the `--threshold` argument (the verifier runs it at more than one threshold). The milestone 1 and 2 outputs must still be produced.
