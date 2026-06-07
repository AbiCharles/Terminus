I've got an ocean-buoy calibration mission notebook at /app/mission_notebook.md and a SQLite database of observations at /app/observations.db, and I need a small Python CLI at /app/buoy_calibrate.py that calibrates each buoy's sensor drift over three steps: pull the binding rules out of the notebook, build a clean per-buoy residual series from the database, then run a Bayesian inversion for each sensor's offset and drift. The notebook has been revised across editions and only its governing sections (§6–§13) are binding — earlier-edition numbers are quoted elsewhere as background and must not be used.

For this first step, make `python /app/buoy_calibrate.py parse` read /app/mission_notebook.md and write the binding protocol to /app/protocol.json as a single JSON object with exactly this shape:

```json
{
  "mission_epoch": "<ISO8601, e.g. 2024-01-01T00:00:00Z>",
  "time_unit": "days",
  "active_status": "<string>",
  "included_sensor_types": ["<sensor type>", ...],
  "drift_changepoint": "<ISO8601>",
  "sensors": {
    "<sensor type>": {
      "unit_conversion": <float>,
      "priors": {
        "offset": {"mean": <float>, "std": <float>},
        "drift": {"mean": <float>, "std": <float>},
        "drift_change": {"mean": <float>, "std": <float>}
      }
    }
  },
  "exclusion_intervals": [{"buoy_id": "<buoy id or ALL>", "start": "<ISO8601>", "end": "<ISO8601>"}]
}
```

Fill every field from the binding sections: the mission epoch and time unit, the operational status that makes a buoy eligible, which sensor channels are calibrated, the drift changepoint instant, and for each included sensor type the unit conversion and the Gaussian priors for the offset, the baseline drift, and the post-changepoint drift change, plus the maintenance exclusion intervals. The observation noise is not a single per-sensor number here — each observation carries its own measurement standard deviation in the database — so there is no noise field in the protocol. Be precise; superseded values from earlier editions must not appear.
