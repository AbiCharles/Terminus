# Abyssal Sentinel Programme — Buoy Drift Calibration Mission Notebook

**Document reference:** ASP-CAL-NB-0412
**Edition:** 3 (effective 2024-01-01)
**Classification:** Internal — Ocean Observing Data Quality
**Owning function:** Calibration & Metrology Working Group (CMWG)
**Supersedes:** Edition 1 (2022-09-01, ref. ASP-CAL-NB-0107) and Edition 2 (2023-06-15, ref. ASP-CAL-NB-0288)

> **Reader's note on precedence.** Only the values, names, and procedures stated in the numbered
> governing sections (§6 through §13) of this Edition 3 notebook are binding for the current
> calibration cycle. The front matter (§1–§5) and the supplementary material (§14 onward) — including
> the revision history, the case-study library, the statistical background, and the appendices — are
> provided for context and traceability only. Several of those sections quote **superseded** Edition 1
> and Edition 2 criteria and must not be mistaken for the binding criteria. Where any supplementary
> value differs from a governing section, the governing section controls.

---

## §1 Executive Summary

The Abyssal Sentinel Programme operates a fleet of moored ocean buoys whose sensors gradually drift
away from truth over a deployment season. This notebook defines how a candidate calibration run must
interpret the mission record, draw clean observations from the programme database, and produce a
Bayesian estimate of each instrument's additive offset and its linear drift rate. The estimate is
deliberately conservative: it fuses a weakly informative prior with the observed discrepancy between
each buoy and its co-located reference instrument, and it reports both the posterior summary and the
residual reduction achieved after correction.

Calibration is not a matter of trusting the rawest, freshest reading. A reading is admitted to the
calibration only when the buoy is in service, when its channel is one the programme currently
calibrates, and when the timestamp does not fall inside a maintenance exclusion. The governing
sections below fix each of these rules precisely.

## §2 Mission Background

Sentinel moorings are deployed along a meridional transect and report at daily cadence. Each mooring
carries a primary sensor whose long-term stability is the subject of this notebook, alongside a
co-located reference channel of higher metrological pedigree that is treated as truth for the purpose
of drift estimation. The programme has run for three seasons; the instrumentation, the unit
conventions, and the statistical treatment have all been revised between seasons, which is why the
precedence note above matters.

## §3 Fleet Overview

The present season fields seven moorings, identified B001 through B007. Their channels span
temperature, pressure, and salinity, though not every channel is in scope for calibration this cycle.
Operational status is tracked in the programme database and may be active or retired; only the former
participate. The fleet roster, deployment coordinates, and servicing cadence are tabulated in
Appendix C (§22) for reference; the binding inclusion rule is stated in §7.

## §4 Instrumentation

Primary temperature channels are thermistor packs reporting integer counts that map linearly to
degrees Celsius. Primary pressure channels are strain-gauge transducers reporting integer counts that
map linearly to decibars. The salinity channels are inductive-conductivity cells; they were part of
the calibration scope in an earlier edition but are out of scope this cycle. The exact count-to-unit
mappings have changed across editions and are fixed for the current cycle in §8.

## §5 Deployment Narrative

The season opened with a coordinated deployment in the first week of January and proceeded at daily
sampling. A fleet-wide servicing window in mid-March took every mooring offline for a week, and a
single mooring suffered a sensor fault that required a multi-week quarantine in May. These episodes
are not visible from the values alone and must be applied procedurally; the binding windows are listed
in §11.

---

## §6 Mission Epoch and Time Convention

The mission epoch is fixed at 2024-01-01T00:00:00Z. Throughout the current cycle, elapsed time is
measured in days since the mission epoch, and every drift quantity is a per-day rate. A reading at the
epoch has an elapsed time of zero days.

## §7 Sensor Inclusion Criteria

Calibration is carried out only for buoys whose operational status is active at the time of processing.
Only temperature and pressure sensor channels are included in the present calibration cycle; salinity
channels are out of scope and are not calibrated here. A retired mooring, or one whose channel is not an
included type, is omitted entirely from every downstream product.

## §8 Unit Conversion Standards

Temperature raw counts are converted to degrees Celsius by multiplying by 0.0625. Pressure raw counts
are converted to decibars by multiplying by 0.1. These conversions place a converted reading in the same
physical units as its co-located reference, so the residual (converted minus reference) is in physical
units.

## §9 Observation Weighting

The observation noise is not a single per-sensor constant this cycle. Each observation carries its own
measurement standard deviation in the measurement_std column of the database, already expressed in
physical units. The inversion treats each observation's noise as known and independent and weights each
observation by the inverse of its variance, so noisier observations contribute less to the estimate than
precise ones.

## §10 Drift Changepoint

A fleet-wide servicing in mid-March alters each instrument's drift rate, so the drift is not a single
constant slope across the season. The current cycle models a drift changepoint at 2024-03-17T00:00:00Z:
the residual equals an additive offset, plus a baseline drift acting on elapsed days, plus a drift change
acting on the days elapsed beyond the changepoint (and zero before it). The changepoint instant is the
same for every buoy.

## §11 Bayesian Prior Elicitation

Each of the three calibration parameters — the offset, the baseline drift, and the drift change — is given
an independent Gaussian prior per sensor type. For temperature, the offset prior is Gaussian with mean
0.0 and standard deviation 0.5, the drift prior is Gaussian with mean 0.0 and standard deviation 0.02,
and the drift-change prior is Gaussian with mean 0.0 and standard deviation 0.02. For pressure, the
offset prior is Gaussian with mean 0.0 and standard deviation 2.0, the drift prior is Gaussian with mean
0.0 and standard deviation 0.05, and the drift-change prior is Gaussian with mean 0.0 and standard
deviation 0.05. The priors are weakly informative so that, where the record is informative, the data
dominate the posterior.

## §12 Exclusion and Maintenance Protocol

Readings that fall inside a maintenance exclusion are not admitted to the calibration. A fleet-wide
maintenance exclusion applies to all buoys from 2024-03-10T00:00:00Z to 2024-03-17T00:00:00Z. An
additional exclusion applies to buoy B003 from 2024-05-01T00:00:00Z to 2024-05-20T00:00:00Z. An
exclusion is half-open: a reading exactly at the start instant is excluded, and a reading exactly at the
end instant is admitted.

## §13 Inversion Methodology and Reporting

For each included buoy, form the residual series by subtracting the reference from the converted reading
at each admitted timestamp, and fit the change-point drift model of §10 by combining the inverse-variance
observation weights of §9 with the Gaussian priors of §11. The estimate is the conjugate Gaussian
posterior over the offset, the baseline drift, and the drift change; report each parameter's posterior
mean and standard deviation and a central 95% credible interval, together with the admitted observation
count, the changepoint in elapsed days, and the root-mean-square residual before and after subtracting
the fitted model. A fleet-level summary aggregates the per-buoy corrected root-mean-square residuals.

## §14 Revision History (Superseded — Not Binding)

This section records how the binding criteria have changed across editions. **None of the values in
this section apply to the current cycle**; they are retained only for audit traceability.

- **Edition 1 (2022-09-01).** The mission epoch was fixed at 2022-09-01T00:00:00Z. Temperature counts
  were converted to degrees Celsius by multiplying by 0.1, and pressure counts to decibars by
  multiplying by 0.25. Salinity channels were calibrated alongside temperature and pressure. The
  offset prior for temperature was Gaussian with mean 0.0 and standard deviation 1.0. Buoys were
  selected when their operational status was deployed.
- **Edition 2 (2023-06-15).** The mission epoch was moved to 2023-06-01T00:00:00Z. The temperature
  conversion was corrected to 0.0625, but the pressure conversion was still 0.2. The drift prior for
  pressure used a standard deviation of 0.1. The fleet-wide maintenance exclusion ran from
  2023-07-01T00:00:00Z to 2023-07-05T00:00:00Z, and buoy B002 carried an exclusion from
  2023-08-10T00:00:00Z to 2023-08-20T00:00:00Z. Observation noise for pressure was quoted as 0.3.

## §15 Case Study — The 2023 Pressure Anomaly (Illustrative)

During the previous season, an analyst applied the Edition 1 pressure conversion of 0.25 to an
Edition 2 deployment and obtained residuals that grew without bound. The lesson recorded here is that
the conversion factor must always be taken from the edition in force; under Edition 2 the correct
pressure conversion was 0.2, and under the current Edition 3 it is the value stated in §8. This case
study quotes the older numbers purely to illustrate the failure mode.

## §16 Glossary

**Offset** — the additive component of sensor error that is constant in time. **Drift** — the
component of sensor error that grows linearly with elapsed time. **Residual** — the difference between
a converted reading and its co-located reference. **Admitted observation** — a reading that survives
the inclusion and exclusion rules of §7 and §11. **Posterior** — the probability distribution over the
calibration parameters after combining the prior with the likelihood.

## §17 Appendix A — Notes on the Reference Channel

The co-located reference channel is treated as truth. It is reported in physical units directly and
requires no conversion. The residual is always converted-reading minus reference-reading, never the
reverse; a sign error here flips the meaning of offset and drift.

## §18 Appendix B — Per-Mooring Deployment Dossiers

The dossiers below record the deployment, servicing, and behavioural history of each mooring in the
current season. They are descriptive and historical; where they quote numeric calibration constants,
those constants reflect the conditions of the day the entry was written and are not the binding
constants of the current cycle. The binding constants are in §6 through §13.

### B001 — Sentinel-North (temperature)

Sentinel-North anchors the northern end of the transect over a flat abyssal plain at a nominal sounding
of 4,180 metres. The mooring carries a thermistor pack on the upper float and a co-located reference
thermistor of laboratory pedigree clamped within ten centimetres of the primary element, so that the
two sensors sample effectively the same parcel of water. The primary element reports integer counts;
the reference element is factory-reported directly in degrees Celsius and is the truth against which
the primary is calibrated.

The unit was deployed in the first coordinated launch of the season and has reported continuously at
daily cadence since the epoch. Its early-season residuals were small and positive, consistent with a
modest warm bias of a few tenths of a degree, and they grew slowly through the season at a rate that is
the whole point of the drift estimate. Sentinel-North was offline only during the fleet-wide servicing
window; it carried no mooring-specific exclusion. The servicing window removed roughly a week of
readings from the centre of the record, which slightly widens the posterior on the drift because the
lever arm of the time base is reduced, but the unit's long, clean record on either side of the gap
keeps the estimate well constrained.

Historical note: under the Edition 1 convention this unit's counts were multiplied by 0.1 rather than
the present factor, which inflated the apparent warm bias by more than an order of magnitude and led an
early analyst to flag the instrument as failing when it was in fact within specification. The lesson is
recorded in §15 and is not a statement about the current cycle.

### B002 — Sentinel-East (pressure)

Sentinel-East sits on the eastern flank of the transect where a gentle slope introduces a weak tidal
pressure signal into the reference channel. The mooring carries a strain-gauge transducer reporting
counts and a co-located reference transducer reporting decibars. The reference channel's tidal
variation is genuine ocean signal and appears identically in both channels, so it cancels in the
residual and does not bias the drift estimate; analysts occasionally mistake this for instrument noise
and should not.

The unit reported a pronounced negative offset early in the season — the converted reading sat below
the reference by something on the order of a decibar and a half — and a positive drift that gradually
narrowed the gap. Sentinel-East was offline only for the fleet-wide window. Its record is the longest
clean pressure series in the fleet and yields the tightest pressure posterior.

Historical note: the Edition 2 review quoted a pressure conversion of 0.2 and a pressure observation
noise of 0.3, and an analyst who carried those forward into a later season over-smoothed the posterior
and under-reported the drift. The current binding pressure conversion and noise are in §8 and §9.

### B003 — Sentinel-South (temperature)

Sentinel-South is the most eventful unit of the season. It anchors the southern end of the transect in
a region of energetic mesoscale variability, and partway through the season its primary thermistor
developed an intermittent fault that produced physically implausible excursions. The fault was
diagnosed during a maintenance call and the unit was placed under a mooring-specific quarantine that
removed roughly three weeks of readings in May, in addition to the fleet-wide March window. Both
windows must be excluded; the quarantine window is the mooring-specific interval recorded in §11.

Outside the excluded windows the unit's record is clean and shows a small positive offset and a slight
negative drift — the instrument was, if anything, slowly cooling relative to truth. Because two windows
are removed from a single season, Sentinel-South has the fewest admitted observations of any calibrated
unit, and its posterior is correspondingly the widest; this is expected and is not a sign of a problem
with the estimate.

Historical note: an earlier season placed a B003 exclusion in August rather than May, and a different
season placed a B002 exclusion in August; neither applies now. Only the windows in §11 are binding.

### B004 — Sentinel-West (pressure)

Sentinel-West occupies the western flank opposite Sentinel-East. It carries the same transducer model
as the other pressure moorings. Its defining feature this season is a large positive offset of more
than two decibars at the epoch combined with a negative drift, so that the converted reading begins
well above the reference and converges toward it as the season progresses. The unit was offline only
for the fleet-wide window and otherwise reported continuously.

The combination of a large offset and a clear drift makes Sentinel-West a good worked example of why
the offset and drift must be estimated jointly rather than sequentially: subtracting a season-mean bias
first would absorb part of the drift into the offset and leave a misleading residual trend. The
conjugate posterior estimates both at once and avoids this trap.

### B005 — Halocline-1 (salinity)

Halocline-1 is a conductivity mooring deployed to extend the programme's salinity coverage. It is in
service and reporting normally, but salinity is out of scope for the current calibration cycle, so the
unit is not calibrated here and produces no calibration product. It is included in this dossier only so
that the roster is complete and so that an analyst does not mistake its absence from the calibration
output for an error. The binding inclusion rule is in §7.

Historical note: salinity channels were calibrated alongside temperature and pressure under Edition 1,
using a conductivity-cell conversion that does not appear in the current governing sections. That scope
was retired in Edition 2 and remains out of scope now.

### B006 — Sentinel-Relic (temperature)

Sentinel-Relic is a first-generation temperature mooring retained on the mooring plan for engineering
comparison. It is retired: its telemetry is archived but it is not part of the operational fleet, and
its operational status in the programme database reflects this. A retired unit is never calibrated,
regardless of sensor type, so Sentinel-Relic produces no calibration product. The binding status rule
is in §7.

### B007 — Sentinel-Drift (pressure)

Sentinel-Drift is the newest pressure mooring, deployed to densify the western array. Despite its name
it is a perfectly ordinary unit; the name refers to the array geometry, not to any instrument defect.
It shows a small positive offset and a moderate positive drift and was offline only for the fleet-wide
window. Its record is clean and its posterior well constrained.

## §19 Appendix C — Instrumentation Specifications

### C.1 Primary temperature element

The primary temperature element is a negative-temperature-coefficient thermistor digitised to integer
counts by a sixteen-bit converter. Across the instrument's working range the count-to-temperature
relationship is linear to within the observation noise, so a single multiplicative conversion suffices;
the binding factor is in §8. The element's short-term repeatability is far finer than its season-scale
stability, which is why drift rather than noise dominates the calibration problem. The reference
thermistor shares the housing but is individually characterised against a fixed-point cell before
deployment and is reported directly in degrees Celsius.

The conversion factor has changed across editions as the digitiser firmware was revised. Edition 1 used
a coarser quantisation that corresponded to a factor of 0.1 per count; the present digitiser is finer
and the present factor is smaller. Mixing the two is the single most common calibration error in the
programme's history and is the subject of the case study in §15.

### C.2 Primary pressure transducer

The primary pressure transducer is a resonant strain gauge digitised to integer counts. Like the
thermistor it is linear across its working range to within the observation noise, and a single
multiplicative conversion to decibars suffices; the binding factor is in §8. The transducer exhibits a
small thermal sensitivity that is removed in firmware before the counts are reported, so the calibration
problem reduces to an additive offset and a linear drift. The co-located reference transducer is a
quartz instrument reported directly in decibars.

Pressure conversions have also changed across editions, and the supplementary record contains at least
two superseded values; only §8 is binding. The pressure observation noise has likewise been revised,
and only §9 is binding.

### C.3 Reference channels and traceability

Every calibrated mooring carries a co-located reference channel of higher metrological pedigree than
its primary, characterised against laboratory standards before deployment and reported directly in
physical units. The reference is treated as truth: the residual is always the converted primary reading
minus the reference reading, and the sign convention is fixed in §17. Because the reference and the
primary sample the same water, genuine ocean variability appears in both and cancels in the residual,
leaving only the instrument's offset, its drift, and observation noise.

## §20 Statistical Methodology Background

This section develops the statistical model behind the calibration so that an analyst can reproduce and
defend the numbers. It is exposition; the binding constants live in the governing sections.

### 20.1 The change-point forward model

For a calibrated buoy, let the cleaned residual at admitted observation i be r_i — the converted reading
minus its co-located reference, in physical units — observed at elapsed time t_i in days since the
mission epoch. The residual is modelled as an additive offset, a baseline drift acting on elapsed time,
and a drift change that acts only after the servicing changepoint t_c:

    r_i = offset + drift * t_i + drift_change * max(0, t_i - t_c) + noise_i.

Before the changepoint the slope is the baseline drift; after it the slope becomes drift plus
drift_change. The changepoint t_c is the binding instant in section 10, the same for every buoy. The
model is deliberately the simplest that captures a constant bias, a season-long drift, and the documented
change in drift rate at servicing; no higher-order terms are part of the binding model.

### 20.2 Heteroscedastic noise

The noise term is independent and Gaussian but not identically distributed: observation i has its own
known standard deviation s_i, the measurement_std recorded with it in the database. Observation quality
varies across the season, and the inversion must respect that by weighting each observation by the
inverse of its variance. Treating the noise as a single constant — an unweighted fit — gives a different
and incorrect estimate, because the noisier observations would then be allowed to pull the fit as hard as
the precise ones.

### 20.3 The prior and the posterior

Each of the three parameters is given an independent Gaussian prior per sensor type, with the means and
standard deviations fixed in section 11. Because the likelihood is Gaussian with known per-observation
variances and the prior is Gaussian, the posterior over the three parameters is again Gaussian and
available in closed form: it is the weighted, generalized-least-squares conjugate update of the prior by
the inverse-variance-weighted data. The calibration reports this posterior — each parameter's mean and
standard deviation and a central 95% credible interval at roughly the mean plus or minus 1.96 posterior
standard deviations. Where a buoy's record is long and informative the data dominate the prior; where it
is thin, for instance after exclusions, the estimate degrades gracefully toward the prior.

### 20.4 Calibration quality

The procedure reports the root-mean-square residual before any correction and after subtracting the
fitted offset, baseline drift, and drift-change terms. A well-behaved calibration reduces the
root-mean-square substantially; a buoy whose corrected residual stays large is flagged for engineering
review rather than trusted, because the change-point model has failed to explain its behaviour.

## §21 Historical Case-Study Library

The following cases are drawn from previous seasons and are retained for training. Every numeric
constant quoted in this section reflects the edition in force at the time of the case and is not binding
now; the cases are included precisely because they illustrate what goes wrong when superseded constants
are carried forward.

### 21.1 The conversion carry-over

In the season governed by Edition 2, an analyst preparing the end-of-season report reused a processing
script from the Edition 1 season without updating the temperature conversion. The script multiplied
temperature counts by 0.1, the Edition 1 factor, rather than the finer factor that Edition 2 had already
adopted. Every temperature residual was therefore inflated by the ratio of the two factors, and the
reported offsets were nonsensically large — several degrees where a few tenths were expected. The error
was caught only when a reviewer noticed that the corrected root-mean-square residual barely improved on
the uncorrected one, because the inflated residual was dominated by a spurious scale rather than by a
genuine offset and drift. The remedy was to take the conversion from the edition in force, which is the
discipline the precedence note now enforces.

### 21.2 The epoch shift

A mid-season reprocessing once moved the mission epoch forward by several weeks to align with a
re-deployment, without re-deriving the offset interpretation. Because the offset is defined at the
epoch, shifting the epoch forward folded the drift accumulated over those weeks into the offset, and the
reported offset jumped even though the instrument's behaviour had not changed. The drift estimate was
unaffected, which is the diagnostic signature of an epoch error: a changed offset with an unchanged
drift. The lesson is that the epoch is a binding convention, not a free analysis choice.

### 21.3 The over-smoothed pressure season

In the Edition 2 season a pressure analyst used an observation noise of 0.3 — a value that appeared in a
draft of that edition — rather than the value that was ultimately adopted. The inflated noise made the
likelihood weaker relative to the prior, the posterior was pulled toward the zero-mean prior, and the
genuine drift of a visibly drifting mooring was under-reported by a wide margin. The credible intervals
were correspondingly too narrow around the wrong mean, giving false confidence. The episode is why the
binding noise model is stated as a single value per sensor type and why drafts are not citable.

### 21.4 The phantom exclusion

A processing run once carried forward a mooring-specific exclusion from a prior season — an August
window on a different mooring — and applied it to the current season, removing perfectly good
observations and widening the posterior for no reason. No harm was done to correctness, but the estimate
was needlessly imprecise, and the audit trail was confusing because the output did not match the
season's documented servicing log. Exclusions, like every other constant, are binding only as stated in
the current governing section.

## §22 Fleet Roster and Servicing Cadence

The roster below summarises the seven moorings of the current season. The sensor type and operational
status recorded here mirror the programme database, which is the authoritative source; where this table
and the database ever disagree, the database governs and the discrepancy is a data-management defect to
be reported. The roster is provided so that an analyst can sanity-check that the calibration output
covers exactly the moorings it should.

- **B001 Sentinel-North** — temperature, active. Northern transect terminus, abyssal plain, ~4180 m.
  Continuous daily reporting; offline only for the fleet-wide March window.
- **B002 Sentinel-East** — pressure, active. Eastern flank, gentle slope with a weak tidal signature.
  Longest clean pressure record of the season.
- **B003 Sentinel-South** — temperature, active. Southern terminus in an energetic mesoscale field.
  Intermittent thermistor fault led to a multi-week May quarantine in addition to the March window.
- **B004 Sentinel-West** — pressure, active. Western flank opposite B002. Large positive offset with a
  converging negative drift.
- **B005 Halocline-1** — salinity, active. Conductivity mooring; in service but out of calibration scope
  this cycle, so it produces no calibration product.
- **B006 Sentinel-Relic** — temperature, retired. First-generation engineering unit retained on the
  plan; never calibrated because it is retired.
- **B007 Sentinel-Drift** — pressure, active. Newest western unit; ordinary behaviour despite the name.

The servicing cadence for the season had two scheduled and one unscheduled element. The scheduled
elements were the coordinated January deployment and the fleet-wide March servicing window, during
which every mooring was taken offline for a week to swap sacrificial anodes and download high-rate
engineering logs. The unscheduled element was the May quarantine of B003 following the thermistor fault.
Only the March window and the B003 May window remove observations from the calibration, and both are
stated bindingly in the governing exclusion section; the January deployment is simply the start of the
record and removes nothing.

A reader comparing this cadence against earlier seasons will notice that the servicing windows have
moved from year to year — past seasons serviced in July and quarantined in August — which is exactly why
the exclusion windows are restated for each edition and why a window from a prior season must never be
carried forward.

## §23 Programme Database Data Dictionary

The programme stores observations in a relational database. The calibration draws on two tables. This
dictionary documents their structure so that an analyst can write correct queries; it describes the data
that exist, not the queries to run.

### 23.1 Table `buoys`

One row per mooring. Columns:

- `buoy_id` — the mooring identifier, a short string such as B001. Primary key.
- `name` — the human-readable mooring name, such as Sentinel-North.
- `sensor_type` — the primary channel type: temperature, pressure, or salinity. This is the field the
  inclusion rule tests against the set of calibrated sensor types.
- `status` — the operational status of the mooring. The inclusion rule admits a mooring only when this
  field equals the binding active status; other values, such as the retired marker, exclude the mooring.
- `raw_units` — a label describing the units of the raw reading, retained for provenance. The binding
  conversion is keyed on the sensor type, not on this label.

### 23.2 Table `observations`

One row per reading. Columns:

- `obs_id` — a surrogate integer primary key with no physical meaning.
- `buoy_id` — the mooring the reading belongs to; a foreign key to `buoys.buoy_id`.
- `timestamp` — the reading time as an ISO-8601 string in UTC with a trailing Z, such as
  2024-02-01T00:00:00Z. The exclusion windows and the elapsed-time calculation both parse this field.
- `raw_reading` — the primary sensor reading in raw counts, stored as a real number. The unit
  conversion is applied to this field to obtain the converted physical value.
- `reference_reading` — the co-located reference reading in physical units, stored as a real number.
  This is the truth value; the residual is the converted reading minus this field.

### 23.3 Notes on querying

Readings are stored at daily cadence per mooring across the season, including inside the servicing and
quarantine windows, so the windows must be removed procedurally rather than assumed absent. There is no
quality flag column: a reading inside an exclusion window is indistinguishable by value from a good
reading, which is the whole reason the exclusion windows are documented. Ordering observations by
timestamp before forming the series keeps the elapsed-time axis monotone and makes the output stable and
reproducible.

## §24 Oceanographic Context

The transect samples a meridional section across a boundary-current regime, and the reference signals
the moorings see reflect the genuine oceanography of that section. Understanding the oceanography helps
an analyst distinguish real signal — which cancels in the residual — from instrument behaviour, which
does not.

The temperature moorings see a seasonal cycle dominated by the surface heat flux integrated over the
mixed layer, modulated by mesoscale eddies that advect warmer or cooler water past the mooring on a
timescale of weeks. Both effects appear in the primary and the reference channels alike and therefore
cancel in the residual; an analyst who sees a seasonal swing in a raw channel should not mistake it for
drift. The southern terminus, B003, sits in the most energetic part of the field, which is why its raw
record is the noisiest even though its instrument noise is the same as the northern unit's.

The pressure moorings see a barotropic tidal signal and a slower seasonal adjustment of the local
dynamic height. The tidal signal is small at the depths in question but is genuine and, again, common to
both channels. The eastern and western flanks see slightly different tidal phases because of their
position relative to the amphidromic system, which is harmless for calibration because the residual only
ever compares a mooring to its own co-located reference, never to another mooring.

None of this oceanography enters the calibration model, which is deliberately agnostic to the physical
origin of the reference signal; the model only asks how the primary channel departs from its reference
over time. The context is provided so that an analyst reviewing residual plots can recognise that a
large, structured raw signal is expected and is not evidence of a calibration problem.

## §25 Reference-Channel Metrology and Traceability

The credibility of the whole calibration rests on the reference channels being trustworthy, so the
programme maintains a traceability chain for every reference instrument. Each reference thermistor is
characterised against a fixed-point cell whose temperature is realised from an international standard,
and each reference pressure transducer is characterised against a deadweight tester whose masses are
traceable to a national standard. The characterisations are performed within a few months of deployment
and again on recovery, and the pre- and post-deployment characterisations are compared to bound the
reference instrument's own drift over the season.

Because the reference instruments are themselves capable of drifting, the programme deliberately selects
reference instruments whose stability is at least an order of magnitude better than the primaries they
police, so that the reference drift is negligible on the scale of the primary drift being estimated. The
residual therefore attributes essentially all of its trend to the primary, which is the intended
interpretation. An analyst who finds that a reference and primary drift together at the same rate should
suspect a common-mode problem — a mooring-wide power or timing fault — rather than a sensor drift, and
should escalate rather than calibrate.

The reference reading is stored in the database already in physical units and requires no conversion.
The single most important sign convention in the whole procedure is that the residual is the converted
primary reading minus the reference reading; reversing it flips the sign of both the offset and the
drift and silently corrupts every downstream number, which is why the convention is restated wherever
the residual is mentioned.

## §26 Uncertainty Budget

The reported posterior standard deviations capture the uncertainty that the statistical model knows
about: the spread of the calibration parameters given the admitted residuals, the known observation
noise, and the priors. A complete uncertainty budget, however, also accounts for contributions that sit
outside the statistical model, and this section enumerates them so that a reviewer understands what the
posterior does and does not include.

The first contribution is the observation noise itself, which the model treats as known per sensor type.
This term sets the scale of the likelihood and feeds directly into the posterior covariance. If the true
noise differed from the stated value, the posterior width would be mis-stated proportionally; the
programme controls this by characterising the noise from the high-rate engineering logs and fixing a
single binding value per sensor type.

The second contribution is the reference instrument's own residual uncertainty. Although reference
instruments are chosen to be far more stable than the primaries, they are not perfect, and their
pre-to-post characterisation difference bounds a small additional uncertainty that the residual model
folds into the noise term. Because this bound is an order of magnitude below the primary drift, it is
absorbed rather than propagated separately.

The third contribution is the conversion-factor uncertainty. The count-to-physical conversion is treated
as exact, but the digitiser characterisation has a finite tolerance. The tolerance is small enough that
its effect on the residual is negligible relative to the observation noise, which is why the conversion
is stated as a single exact factor rather than as a factor with an uncertainty.

The fourth contribution is structural: the offset-plus-drift model may not perfectly describe a
mooring. Any unmodelled curvature shows up as an elevated corrected root-mean-square residual rather
than as a widened posterior, which is why the corrected residual figure is reported alongside the
posterior and why a mooring with a poor corrected residual is escalated rather than trusted.

The posterior standard deviation reported by the procedure captures the first contribution fully and the
second approximately through the noise term, and deliberately excludes the third as negligible and the
fourth as a model-adequacy question better answered by the corrected residual. A reviewer should read
the posterior interval as a within-model uncertainty and the corrected residual as the model-adequacy
check, and should treat the two together as the calibration's quality statement.

## §27 Quality Assurance and Review Workflow

Every calibration cycle passes through a defined review before its numbers are published. The reviewer
checks, first, that the calibration covers exactly the moorings the inclusion rule implies — every
active mooring of an included sensor type and no others — because a missing or extra mooring is the most
visible sign that an inclusion or status rule was misread. The reviewer checks, second, that the
admitted observation counts are consistent with the season length minus the exclusion windows that apply
to each mooring, because an unexpected count signals a mis-applied window. The reviewer checks, third,
that the corrected residual is materially smaller than the uncorrected residual for every mooring,
because a calibration that fails to reduce the residual has either misread a constant or encountered a
mooring the model does not fit.

The reviewer then spot-checks the numeric constants against the governing sections: the epoch, the
per-type conversions, the per-type noise, the per-type priors, and the exclusion windows. This spot
check exists because the single largest category of historical error is the silent carry-over of a
superseded constant, and a thirty-second comparison against the governing sections catches it. Only
after these checks pass are the numbers published and archived.

## §28 Extended Revision History (Superseded — Not Binding)

This section expands the summary in §14 with the full detail of how the binding constants have evolved.
**Nothing here is binding.** It exists so that an analyst encountering an old report can understand which
edition produced it, and so that the failure modes in the case-study library can be traced to specific
superseded values.

### 28.1 Edition 1 (2022-09-01, ref. ASP-CAL-NB-0107)

The inaugural edition fixed the mission epoch at 2022-09-01T00:00:00Z and measured elapsed time in days
from that epoch. It calibrated three sensor types — temperature, pressure, and salinity — and selected
moorings whose operational status was recorded as deployed, a status label later renamed. The unit
conversions were coarse: temperature counts were multiplied by 0.1 to obtain degrees Celsius, pressure
counts by 0.25 to obtain decibars, and salinity counts by 0.002 to obtain practical salinity units. The
observation noise was quoted as 0.1 for temperature and 0.4 for pressure. The priors were tighter than
today's: the temperature offset prior had standard deviation 1.0 and the temperature drift prior 0.05,
while the pressure offset prior had standard deviation 3.0 and the pressure drift prior 0.1. The
fleet-wide servicing window that season ran from 2022-10-05T00:00:00Z to 2022-10-12T00:00:00Z, and a
quarantine applied to the mooring then designated B003 from 2022-11-01T00:00:00Z to
2022-11-15T00:00:00Z. None of these values applies now.

### 28.2 Edition 2 (2023-06-15, ref. ASP-CAL-NB-0288)

The second edition moved the mission epoch to 2023-06-01T00:00:00Z. It retired salinity from the
calibration scope, leaving temperature and pressure, and it renamed the qualifying status from deployed
to active. It corrected the temperature conversion to the finer factor of 0.0625 that remains in force,
but it left the pressure conversion at an intermediate value of 0.2 that was itself later revised. The
observation noise was quoted as 0.05 for temperature — the value that remains in force — and 0.3 for
pressure, a value later reduced. The priors were widened toward their present values: the temperature
offset prior standard deviation became 0.5 and the drift prior 0.02, both of which remain, while the
pressure offset prior standard deviation became 2.0, which remains, but the pressure drift prior was set
to 0.1, which was later tightened. The fleet-wide servicing window ran from 2023-07-01T00:00:00Z to
2023-07-05T00:00:00Z, and a quarantine applied to mooring B002 from 2023-08-10T00:00:00Z to
2023-08-20T00:00:00Z. A reader will note that Edition 2 agrees with the current edition on several
constants and disagrees on others; this partial overlap is exactly what makes a careless carry-over
dangerous, because some values will look right and others will be silently wrong.

### 28.3 Transition to Edition 3

The current edition completed the revision that Edition 2 began. It finalised the pressure conversion at
the value in §8, reduced the pressure observation noise to the value in §9, tightened the pressure
drift prior to the value in §10, set the mission epoch to the start of the current calendar year, and
established the servicing and quarantine windows in §11. The only safe way to process the current season
is to read every constant from the governing sections of this edition; the history above is provided so
that the provenance of each change is auditable, not so that any of it is reused.

## §29 Analyst Operating Notes

These notes orient an analyst to the calibration's intent and to the review it must withstand; they are
about the science and the data, not a recipe for any particular implementation. An analyst should begin
by reading the governing sections in full and copying out each binding constant, because the rest of the
work depends on having them right. An analyst should expect to calibrate exactly the active moorings of
an included sensor type, and should treat the appearance of a salinity unit or a retired unit in the
output as a defect. An analyst should expect the admitted record for most moorings to span the season
minus the March window, with the southern mooring additionally missing its May quarantine, and should
treat a different admitted count as a sign that a window was mis-applied. An analyst should expect the
calibration to reduce the residual substantially and should escalate any mooring where it does not. And
an analyst should expect the review to spot-check every constant against the governing sections, so the
constants must come from there and nowhere else.

## §30 Frequently Asked Questions

**Why estimate offset and drift together rather than removing a mean and then fitting a slope?** Because
the two parameters are correlated given the data: removing a season-mean first would absorb part of the
drift into the offset over an asymmetric record and bias both. The joint posterior handles the
correlation correctly.

**Why are the priors centred on zero?** Because the programme has no prior belief that a sensor reads
high rather than low or drifts up rather than down. The zero-mean prior is the least committal choice and
lets the data determine the sign and magnitude wherever the record is informative.

**Why is the observation noise treated as known rather than estimated?** Because it is characterised
independently from the high-rate engineering logs, and fixing it keeps the inversion conjugate and the
results reproducible. Estimating it jointly would be a different, non-binding model.

**What happens to a mooring whose record is almost entirely excluded?** Its posterior falls back toward
the prior because the likelihood carries little information, and its posterior interval is wide. This is
the intended graceful degradation, not an error.

**Why does the southern mooring have the widest intervals?** Because two exclusion windows remove the
most observations from its record and shorten the elapsed-time span the fit can use, and the slope of a
line is least well determined over a short span.

**Is the reference reading ever converted?** No. The reference is stored in physical units and is used
as truth directly. Only the raw primary reading is converted.

## §31 Notation and Symbols

The following notation is used throughout the methodology and appendices. It is collected here so that
the symbols can be read consistently.

- t — elapsed time of a reading in days since the mission epoch; never negative for an admitted reading.
- c — a converted primary reading, equal to the raw count times the sensor type's unit conversion.
- m — a co-located reference reading, already in physical units.
- r — a residual, equal to c minus m.
- a — the additive offset parameter, in physical units; the value of the residual the model attributes
  to a constant bias at the epoch.
- b — the linear drift parameter, in physical units per day; the rate at which the modelled residual
  grows with elapsed time.
- σ — the observation noise standard deviation for the sensor type, in physical units.
- m₀, S₀ — the prior mean vector and prior covariance matrix of the parameter pair (a, b).
- m_n, S_n — the posterior mean vector and posterior covariance matrix of (a, b).
- X — the design matrix whose rows are (1, t) over the admitted readings.
- n — the number of admitted readings for a mooring.

Subscripts index admitted readings in timestamp order. Vectors are columns. The offset is always the
first component of the parameter pair and the drift the second, so that the first diagonal entry of the
posterior covariance is the offset variance and the second is the drift variance.

## §32 Worked Illustrative Example

The numbers in this example are invented for instruction and do not correspond to any mooring in the
database; they exist only to make the mechanics concrete. Suppose a temperature mooring yielded, after
cleaning, just three admitted residuals: 0.31 at zero days, 0.34 at fifty days, and 0.39 at one hundred
days. Suppose the binding temperature noise is the value in §9 and the binding temperature priors are
those in §10. The design matrix has rows (1, 0), (1, 50), and (1, 100), and the residual vector is
(0.31, 0.34, 0.39).

Forming XᵀX gives a two-by-two matrix whose entries are the count, the sum of the elapsed times, and the
sum of squared elapsed times; forming Xᵀr gives the sum of the residuals and the sum of the
elapsed-time-weighted residuals. Adding the prior precision to XᵀX divided by the noise variance and
inverting yields the posterior covariance, and multiplying by the sum of the prior contribution and the
data contribution yields the posterior mean. With these illustrative numbers the posterior offset comes
out near the early-time residual and the posterior drift comes out near the visually obvious upward slope
of a few thousandths of a degree per day, with the prior pulling both very slightly toward zero because
the record is so short. A real mooring with a full season of daily readings would pin both parameters far
more tightly than this three-point sketch, and its posterior interval would be correspondingly narrow.
The example is included only so that the matrix mechanics are tangible; it is not a test case and its
numbers are not binding.

## §33 Mooring Engineering and Environmental Notes

This section records engineering context for each mooring that bears on data interpretation but not on
the binding calibration constants. It is descriptive.

Sentinel-North stands on a taut-wire mooring with a subsurface float carrying the sensor package well
clear of the bottom boundary layer. Its anchor is a railway-wheel cluster, and its telemetry is relayed
through an inductive link to a surface expression that reports once daily. The site is quiescent, with
weak bottom currents, so the mooring motion is small and the sensor depth is stable, which contributes
to the cleanliness of its record.

Sentinel-East sits on a slope where bottom currents are stronger and the mooring experiences more
knockdown during energetic events. Knockdown changes the sensor depth slightly and therefore the genuine
pressure the reference and primary both see; because both channels move together, the residual is
unaffected, but an analyst plotting the raw pressure will see excursions that are oceanographic and
mechanical rather than instrumental.

Sentinel-South occupies the most energetic site, and its thermistor fault this season was traced to a
connector intrusion that admitted seawater intermittently. The fault produced both noise and occasional
gross excursions until the unit was quarantined and later serviced. The quarantine window in the
governing exclusion section spans the period from the first confirmed bad reading to the completion of
the service call.

Sentinel-West mirrors Sentinel-East mechanically but on the opposite flank, with comparable knockdown
behaviour. Its large offset this season was attributed at the post-recovery characterisation to a
transducer zero shift that occurred during handling before deployment; the calibration estimates this as
the offset, which is exactly its purpose.

Halocline-1 carries a conductivity cell with an anti-fouling guard; biofouling is the principal threat
to conductivity stability and is the reason salinity calibration is handled on a different cadence and is
out of scope here. Sentinel-Relic, the retired engineering unit, is left in place between recoveries and
reports only intermittently; it is excluded by status regardless. Sentinel-Drift is mechanically
identical to the other western pressure units and was deployed late in the prior recovery cruise.

## §34 Servicing Logs

The following dated entries summarise the season's servicing activity. They corroborate the binding
exclusion windows but do not replace them; the binding windows are in the governing section.

- Early January: coordinated deployment cruise; all seven moorings set or confirmed on station; daily
  reporting begins. No observations are removed by deployment.
- Mid-March: fleet-wide servicing window; every mooring taken offline for anode replacement and log
  download; reporting resumes after the window. This is the fleet-wide exclusion.
- Early May: Sentinel-South thermistor fault confirmed; mooring quarantined pending a service call.
- Mid-to-late May: Sentinel-South service call completed; quarantine lifted. This is the
  mooring-specific exclusion for the southern unit.
- Late June: season closes; end-of-season report prepared; recovery cruise scheduled for the following
  month. No observations are removed by the season close.

The servicing logs from prior seasons, retained in the programme archive, place the fleet-wide window in
October for the inaugural season and in early July for the second season, and place mooring-specific
quarantines in November and August respectively. Those windows belonged to their seasons and have no
bearing on the current cycle.

## §35 Telemetry, Timing, and Timestamp Conventions

Every mooring timestamps its readings against a disciplined clock and reports times in UTC. The database
stores each timestamp as an ISO-8601 string with a trailing Z to denote UTC, and the calibration parses
these strings directly. Because all timestamps share the UTC convention and the daily cadence is regular,
elapsed time in days is simply the difference between a reading's timestamp and the mission epoch
expressed in days. The exclusion windows are likewise expressed as UTC instants and are interpreted as
half-open intervals, so that a reading exactly at a window's start is removed and a reading exactly at a
window's end is retained; this convention prevents a reading from being ambiguously assigned to two
adjacent windows.

Clock discipline matters because a drift estimate is a regression against time: a mooring whose clock ran
fast or slow would distort the elapsed-time axis and bias the drift. The programme's clocks are
disciplined to a tolerance far finer than the daily cadence, so timing contributes negligibly to the
uncertainty budget, and the calibration treats the timestamps as exact.

## §37 Appendix E — Extended Glossary

**Active status** — the operational status a mooring must have to be calibrated this cycle; stated in the
governing inclusion section. **Admitted reading** — a reading that survives the inclusion and exclusion
rules and therefore enters the fit. **Anode** — a sacrificial element replaced during servicing; its
replacement defines the fleet-wide servicing window. **Barotropic tide** — a depth-independent tidal
signal seen in the pressure channels; genuine ocean signal that cancels in the residual. **Calibration
term** — the modelled part of the residual, an offset plus a linear drift. **Co-located reference** — a
higher-pedigree instrument mounted beside the primary and treated as truth. **Conjugate prior** — a prior
whose form is preserved in the posterior under the given likelihood; the Gaussian prior is conjugate to
the Gaussian likelihood here. **Converted reading** — a raw count multiplied by the unit conversion to
obtain physical units. **Credible interval** — a posterior-probability interval for a parameter; the
central 95% interval is reported. **Design matrix** — the matrix of regressors, here a column of ones and
a column of elapsed times. **Drift** — the linear-in-time component of sensor error, in physical units
per day. **Elapsed time** — days since the mission epoch. **Exclusion window** — a half-open time
interval during which readings are not admitted. **Knockdown** — mooring tilt under current that changes
sensor depth; affects both channels and cancels in the residual. **Mission epoch** — the fixed zero of
elapsed time, stated in the governing time section. **Observation noise** — the zero-mean Gaussian scatter
of the residual about the calibration term, treated as known per sensor type. **Offset** — the constant
component of sensor error at the epoch. **Posterior** — the distribution over the parameters after
combining prior and likelihood. **Primary sensor** — the instrument being calibrated. **Residual** — the
converted reading minus the reference reading. **Retired status** — a status that excludes a mooring from
calibration. **Unit conversion** — the multiplicative factor from raw counts to physical units, stated per
sensor type in the governing conversion section.

## §38 Appendix F — Standards and References

The programme's metrology and statistical practice follow established references, listed here for
provenance. Temperature traceability follows the international temperature scale and its realisation
through fixed-point cells. Pressure traceability follows deadweight-tester practice against national mass
standards. Salinity practice, used only for the out-of-scope conductivity moorings, follows the practical
salinity scale. The Bayesian linear-regression treatment follows standard references on conjugate
Gaussian models and on the interpretation of credible intervals. The data-management conventions for
timestamping and UTC follow the relevant international date-and-time interchange standard. None of these
references introduces a binding constant; the binding constants are stated only in the governing sections
of this edition.

## §39 Appendix G — Past-Season Summary Tables (Superseded — Not Binding)

These tables summarise the calibration constants of past seasons side by side, so that the evolution of
each constant is visible at a glance. **Every value here is superseded; none is binding.** The current
binding values are in the governing sections and must be read from there.

Mission epoch by edition: Edition 1 used 2022-09-01T00:00:00Z; Edition 2 used 2023-06-01T00:00:00Z; the
current edition uses the value in the governing time section.

Temperature unit conversion by edition: Edition 1 used 0.1; Edition 2 and the current edition use the
finer value in the governing conversion section.

Pressure unit conversion by edition: Edition 1 used 0.25; Edition 2 used 0.2; the current edition uses
the value in the governing conversion section.

Temperature observation noise by edition: Edition 1 used 0.1; Edition 2 and the current edition use the
value in the governing noise section.

Pressure observation noise by edition: Edition 1 used 0.4; Edition 2 used 0.3; the current edition uses
the value in the governing noise section.

Temperature offset prior standard deviation by edition: Edition 1 used 1.0; Edition 2 and the current
edition use the value in the governing prior section. Temperature drift prior standard deviation by
edition: Edition 1 used 0.05; Edition 2 and the current edition use the value in the governing prior
section.

Pressure offset prior standard deviation by edition: Edition 1 used 3.0; Edition 2 and the current
edition use the value in the governing prior section. Pressure drift prior standard deviation by edition:
Edition 1 used 0.1; Edition 2 used 0.1; the current edition tightened it to the value in the governing
prior section.

Qualifying status label by edition: Edition 1 used deployed; Edition 2 and the current edition use the
value in the governing inclusion section. Calibrated sensor types by edition: Edition 1 calibrated
temperature, pressure, and salinity; Edition 2 and the current edition calibrate the types in the
governing inclusion section.

Fleet-wide servicing window by edition: Edition 1 ran 2022-10-05 to 2022-10-12; Edition 2 ran 2023-07-01
to 2023-07-05; the current edition uses the window in the governing exclusion section. Mooring-specific
quarantine by edition: Edition 1 quarantined B003 in November 2022; Edition 2 quarantined B002 in August
2023; the current edition's quarantine is in the governing exclusion section.

The purpose of laying the editions side by side is to show how many constants changed and how a careless
reuse of any single row would corrupt a current-season calibration. The discipline the programme enforces
is simple: read every row from the governing sections of the edition in force, and treat these summary
tables as history only.

## §40 Data Management and Change Control

The programme treats every binding constant as a controlled item. A constant may be changed only through
a documented change request that records the old value, the new value, the evidence motivating the
change, and the edition in which the change takes effect. The governing sections of each edition are the
single authoritative statement of the constants for that edition's season, and the revision history and
summary tables are derived records that must never be cited as authority. This discipline exists because
the programme's most damaging historical errors were not computational but clerical: a correct procedure
fed a superseded constant produces a confidently wrong answer, and the only defence is a single
authoritative source per edition.

When a season is reprocessed — for example to incorporate a late-arriving reference characterisation —
the reprocessing uses the governing constants of the edition under which the season was collected, not
the constants of whatever edition happens to be current at reprocessing time. Conflating the two is the
epoch-shift and conversion-carry-over failure mode described in the case-study library. A reprocessing
request therefore records explicitly which edition's constants it uses, and a reviewer confirms that the
edition matches the season.

Database changes follow the same discipline. The schema of the observations store is itself a controlled
item, and a column may not be renamed or repurposed without a change request, because the calibration
queries name columns explicitly. A silent schema change would break the calibration as surely as a
silent constant change would corrupt it.

## §41 Reporting and Archival Requirements

A completed calibration cycle produces a per-mooring report and a fleet summary, and both are archived
with the edition identifier and the processing date so that any published number can later be traced to
the constants that produced it. The per-mooring report records the admitted observation count, the
posterior offset and drift with their standard deviations and credible intervals, and the uncorrected
and corrected residual figures. The fleet summary records the set of calibrated moorings and an
aggregate of the corrected residuals across the fleet, which serves as a single headline indicator of
how well the season's instruments behaved.

Archival is not optional. A calibration whose inputs cannot be reconstructed is not auditable, and an
unauditable calibration cannot be used to correct the scientific record. The archive therefore retains,
alongside the reports, the edition of the notebook in force, the snapshot of the observations store used,
and the processing software version, so that the entire computation can be reproduced bit for bit if a
question is later raised about any published value.

## §42 Rationale for the Binding Constants

This section explains why the current binding constants take the values they do, so that a reviewer
understands the reasoning and can recognise when a proposed change is or is not justified. It does not
restate the values, which live in the governing sections.

The mission epoch is set to the start of the season so that the offset has a natural interpretation as
the sensor bias at deployment and the drift accumulates from zero over the season. An epoch in the middle
of the season would make the offset an awkward mid-season quantity and would invite the epoch-shift
error.

The unit conversions are set by the current digitiser firmware, which is finer than earlier firmware for
temperature and was revised for pressure after the intermediate Edition 2 value proved slightly off
against the deadweight characterisations. The conversions are stated as exact factors because the
digitiser tolerance is negligible against the observation noise.

The observation noise values are characterised from the high-rate engineering logs collected during the
servicing window, which sample the instruments far faster than the daily reporting cadence and so resolve
the short-term scatter directly. The pressure value was reduced from the Edition 2 figure once the
high-rate logs showed the earlier figure had been a conservative draft estimate.

The priors are set weakly informative on purpose. Their zero means encode no directional belief, and
their standard deviations are chosen wide enough that a full season of daily data dominates them while
still regularising a mooring whose record is short. The pressure drift prior was tightened from the
Edition 2 value once several seasons of history showed that genuine pressure drifts were smaller than the
earlier prior allowed, so a slightly tighter prior improved the estimates for short records without
materially affecting long ones.

The exclusion windows are set from the servicing and quarantine logs of the current season and from
nothing else; they are the single most season-specific of all the constants, which is why carrying a
window forward from a prior season is such a common and such a damaging error.

## §43 Validation and Acceptance of a Calibration Run

Before a calibration run is accepted, it is validated against a checklist that mirrors the review
workflow but is applied by the processor rather than the reviewer. The processor confirms that the set of
calibrated moorings equals the set implied by the inclusion rule, that each mooring's admitted count
equals the season length minus the windows that apply to it, that every numeric constant used matches the
governing sections, that the residual is reduced for every mooring, and that the fleet summary aggregates
exactly the calibrated moorings. A run that fails any item is not submitted for review; it is corrected
and re-run.

The acceptance checklist is deliberately redundant with the review, because the cost of a redundant check
is trivial against the cost of publishing a wrong calibration into the scientific record. A calibration
that passes both the processor's acceptance and the reviewer's independent review is published and
archived; one that fails either is returned for correction with the failing item recorded.

## §44 Edge Cases and Degenerate Records

Several edge cases deserve explicit treatment so that an implementation handles them predictably. A
mooring whose record is entirely removed by exclusions has no admitted observations and cannot be
calibrated; such a mooring is reported as having no admissible data rather than being silently dropped or
assigned a spurious estimate, though no mooring in the current season is in this state. A mooring with
very few admitted observations is calibrated, but its posterior is dominated by the prior and its
intervals are wide; this is correct behaviour and the wide interval is the honest signal of a thin
record. A mooring whose residual shows strong curvature is calibrated under the binding linear model, but
its corrected residual will remain large, which is the signal to escalate it for engineering review
rather than to trust its linear estimate.

A record in which every admitted observation falls at the same elapsed time — which cannot happen under
daily sampling but is worth noting — would leave the drift undetermined by the data, and the drift
posterior would fall back entirely to the prior; the offset would still be estimable. The design of the
season, with daily sampling over months, ensures the elapsed-time axis is always well spread and the
drift is always identifiable for any mooring with a non-trivial admitted record.

## §45 Roles and Responsibilities

The calibration cycle involves three roles. The processor runs the calibration, applies the acceptance
checklist, and prepares the reports. The reviewer independently re-checks the run against the governing
sections and the review workflow and either accepts or returns it. The data manager maintains the
observations store and the controlled constants and ensures that schema and constants change only through
documented requests. The separation of these roles is itself a control: the processor cannot publish
without the reviewer, and neither can alter a binding constant without the data manager's change process.
The roles may be filled by different people from cycle to cycle, but the separation is maintained so that
no single person can both choose a constant and publish a result that depends on it.

## §46 Sensor Physics Background

A short account of the sensor physics helps an analyst reason about what offset and drift mean
physically and why the linear model is appropriate.

A thermistor is a resistor whose resistance varies strongly and reproducibly with temperature. The
programme's thermistors are read by passing a known current and digitising the voltage, then mapping the
digitised count to temperature through a calibration that the firmware linearises across the working
range. Offset in a thermistor channel arises mainly from small shifts in the reference resistors of the
read-out network and from self-heating, and it is constant on the season scale. Drift arises from slow
ageing of those reference components and from gradual changes in the thermistor's own resistance-
temperature relationship, and over a single season it is well approximated as linear in time. Higher-order
ageing exists but is far below the season-scale linear term, which is why the binding model stops at a
linear drift.

A strain-gauge pressure transducer converts pressure to a resistance change in a bridge, which is read
and digitised much as the thermistor is. Offset arises from zero shifts in the bridge, often induced by
mechanical handling before deployment, and drift arises from slow relaxation of the strain element and
the bonding. Again the season-scale behaviour is well captured by a constant plus a linear term. The
western mooring's large offset this season is a textbook handling-induced zero shift.

A conductivity cell, used only on the out-of-scope salinity mooring, measures the electrical conductance
of seawater between electrodes. Its dominant stability threat is biofouling, which is episodic rather
than linear and is the reason salinity is calibrated on a different cadence and is out of scope for the
linear-drift model used here.

Understanding these mechanisms reassures an analyst that the binding offset-plus-drift model is not an
arbitrary statistical convenience but a faithful description of how these instruments actually depart from
truth over a season.

## §47 Per-Mooring Residual Behaviour

This section narrates, qualitatively, how each calibrated mooring's residual is expected to behave, so
that an analyst reviewing the output has a physical expectation to check against. The descriptions are
qualitative; the quantitative estimates come from the inversion.

Sentinel-North's residual sits slightly positive at the start of the season and rises slowly, consistent
with a small warm bias that grows as the read-out network ages. Its long clean record makes both the
offset and the gentle drift well determined, and its credible intervals are among the narrowest in the
fleet. A reviewer should expect a modest positive offset and a small positive drift.

Sentinel-East's residual starts well below zero and climbs toward zero as the season progresses,
consistent with a negative offset and a positive drift. Its record is the longest clean pressure series,
so its posterior is tight. A reviewer should expect a clearly negative offset and a positive drift, with
the tidal signal visible in the raw channels but absent from the residual.

Sentinel-South's residual, outside its two excluded windows, is small and positive with a faint downward
slope, consistent with a slight warm bias that slowly diminishes. Because two windows are removed, its
record is the shortest and its intervals the widest; a reviewer should expect a small offset, a small
negative drift, and visibly wider intervals than the other temperature mooring.

Sentinel-West's residual starts well above zero and descends toward zero, consistent with a large
positive offset from a handling-induced zero shift and a negative drift as the strain element relaxes. A
reviewer should expect a clearly positive offset and a negative drift.

Sentinel-Drift's residual starts slightly positive and rises, consistent with a small positive offset
and a moderate positive drift. Its clean full-season record makes the estimate well determined; a
reviewer should expect a small positive offset and a moderate positive drift.

In every case the corrected residual — what remains after the posterior offset and drift are subtracted —
should be small and structureless, consistent with the observation noise, because the offset-plus-drift
model captures the systematic behaviour and leaves only noise. A corrected residual that retains
structure is the signal that the model does not fit and that the mooring needs engineering attention.

## §48 Alternative Estimators and Why They Are Not Used

It is worth recording why the programme uses a conjugate Bayesian estimate rather than the obvious
alternatives, so that a reviewer does not propose a change that has already been considered and rejected.

Ordinary least squares would fit the same offset-plus-drift line by minimising the squared residual with
no prior. It is the large-data limit of the Bayesian estimate and gives almost identical numbers for the
long clean records, but it has no graceful behaviour for short records: a mooring stripped to a handful of
observations by exclusions can produce a wild least-squares slope, whereas the Bayesian estimate falls
back to the weakly informative prior. The programme calibrates moorings of very different record lengths
in a single cycle, so the regularised estimate is preferred for its uniform behaviour.

A robust estimator that down-weights outliers was considered and rejected because the exclusion protocol
already removes the known bad data procedurally, and the remaining residual is genuinely Gaussian about
the calibration term; a robust estimator would add complexity and a tuning constant for no benefit and
would make the result harder to reproduce and audit.

A fully sampled posterior by Markov chain Monte Carlo was considered and rejected because the conjugate
model has an exact closed-form posterior, so sampling would only add Monte Carlo error and a seed
dependence to a quantity that can be computed exactly. The closed form is preferred precisely because it
is deterministic and reproducible, which matters for an audited calibration.

These considerations are why the binding methodology is the conjugate Gaussian estimate and not an
alternative; a proposed change to a different estimator would have to overturn this reasoning and would
go through the change-control process.

## §49 Implementation and Numerical Notes

These notes concern numerical care, not a particular implementation, and they exist so that an analyst
can recognise a numerically suspect result. The normal equations combine the prior precision and the
data precision before inversion; because the prior precision is well conditioned and the data precision
grows with the record length, the combined precision is well conditioned for any non-trivial record, and
the inversion is stable. The elapsed-time axis should be kept in days as the binding time unit specifies;
rescaling time to, say, seconds would make the drift numerically tiny and the design matrix poorly
scaled, and while the mathematics is invariant the floating-point result would be needlessly degraded.

The residual should be formed as the converted reading minus the reference reading in that order, because
the sign convention propagates into the offset and drift; a reversed subtraction produces sign-flipped
estimates that are numerically fine but physically wrong. The admitted observations should be ordered by
timestamp so that the elapsed-time axis is monotone, which makes the computation reproducible and the
diagnostic plots readable. None of these notes changes the mathematics; they guard against avoidable
numerical and sign mistakes.

A useful numerical self-check is the no-prior limit already mentioned: temporarily widening the priors
should move the estimate toward the ordinary least-squares fit, and if it does not, the assembly of the
normal equations has an error. Another self-check is units: the offset should carry the physical unit of
the channel and the drift that unit per day, and an estimate that is orders of magnitude from physical
expectation usually indicates a conversion or time-unit mistake rather than a genuine instrument
behaviour.

## §50 Seasonal Environmental Log

This log narrates the season's environmental conditions month by month, as recorded by the surface
expressions and the reference channels. It is context for interpreting the raw records and plays no part
in the binding constants.

January opened with the deployment cruise in calm conditions. The temperature references showed the
expected late-winter minimum modulated by the monthly variability term, and the pressure references were
quiet with only the barotropic tide evident. All seven moorings settled onto station and began daily
reporting; the early residuals were small and reflected mainly the deployment-time offsets of each
instrument.

February brought the first energetic eddies past the southern terminus, and Sentinel-South's raw
temperature record became visibly noisier as warmer and cooler filaments advected past the mooring. The
reference tracked the primary closely, so the residual remained clean even as the raw record swung. The
northern and flank moorings saw quieter conditions.

March was dominated by the fleet-wide servicing window in its middle third. Every mooring was taken
offline for a week, anodes were swapped, and high-rate engineering logs were downloaded; those logs are
the source of the season's observation-noise characterisation. Reporting resumed after the window. The
servicing week is removed from every mooring's calibration by the fleet-wide exclusion.

April was uneventful environmentally, a steady warming of the temperature references as spring advanced
and a quiet pressure field. The instruments accumulated drift steadily, and the residual trends that the
calibration ultimately estimates became clearly established in this month's clean data.

May was the month of the southern fault. Early in the month Sentinel-South began producing intermittent
implausible excursions traced to a connector intrusion; the mooring was quarantined and serviced, and the
quarantine window removes the affected stretch from its calibration. The rest of the fleet reported
normally through a period of moderate mesoscale activity.

June closed the season with the references near their early-summer values and the instruments at their
maximum accumulated drift. The end-of-season reports were prepared from the full season's admitted data,
and the recovery cruise was scheduled for the following month. The season's clean, long records on most
moorings are what make the calibration well constrained.

## §51 Deployment and Recovery Procedures

Each mooring is deployed anchor-first from the cruise vessel, with the sensor package and reference
instrument clamped together on the upper float so that they sample the same water. Before deployment the
reference instrument is characterised against the laboratory standard, and its pre-deployment
characterisation is recorded. The mooring is positioned by acoustic survey and its final coordinates
logged. Daily reporting begins once the mooring is confirmed on station, which defines the practical
start of each record at or near the mission epoch.

On recovery the reference instrument is re-characterised, and the pre- and post-deployment
characterisations are compared to bound the reference's own drift over the season; a reference whose
characterisation moved by more than a small tolerance is retired from service. The primary instrument is
also bench-tested on recovery, and its bench behaviour is compared against the calibration's estimated
offset and drift as an independent cross-check: a primary whose bench test disagrees materially with the
field calibration is flagged for investigation, because one of the two is wrong. This recovery cross-check
is the programme's ultimate validation of the field calibration and is why the calibration's estimates are
trusted enough to correct the scientific record.

## §52 Programme History and Governance

The Abyssal Sentinel Programme was established to provide a long, stable record of abyssal temperature
and pressure along its transect, and the calibration discipline described in this notebook grew out of
the early seasons' experience that uncalibrated instruments drift enough to corrupt the very trends the
programme exists to measure. The Calibration and Metrology Working Group owns this notebook and the
constants in it, and revises them between seasons through the change-control process. The working group
reports to the programme's science steering committee, which approves each edition before a season's
processing begins.

The governance separation matters because the calibration sits between the raw observations and the
published scientific record, and an error in calibration propagates silently into every downstream
analysis. By vesting the binding constants in a controlled document, separating the processor, reviewer,
and data-manager roles, and archiving every cycle reproducibly, the programme ensures that any published
value can be defended and, if necessary, reconstructed years later. The three editions of this notebook
trace the maturing of that discipline, from the inaugural season's coarse conventions through the second
season's partial revision to the current edition's settled constants.

## §53 Interpretation Guidance for Downstream Users

A scientist using the calibrated record downstream should understand exactly what the calibration does
and does not provide. It provides, per mooring, an estimate of the constant offset and the linear drift
of the primary sensor relative to its co-located reference over the season, with honest uncertainties.
To correct a raw reading, a downstream user converts it to physical units with the binding conversion,
then subtracts the estimated offset and the estimated drift evaluated at that reading's elapsed time; the
result is the calibrated value, and its uncertainty combines the observation noise with the posterior
uncertainty of the offset and drift.

A downstream user should not extrapolate the drift beyond the season: the linear model is fitted within
the season and there is no warrant for projecting it forward or backward, since the physical drift
mechanisms are only approximately linear and only over the fitted span. A downstream user should also
respect the exclusion windows: a reading inside an excluded window was not part of the calibration and
should not be corrected with the season's estimate as though it were, because the instrument's behaviour
inside a fault or servicing window is exactly what the exclusion declines to vouch for. And a downstream
user should propagate the posterior uncertainties rather than treating the offset and drift as exact,
because the whole point of the Bayesian treatment is to provide those uncertainties honestly.

## §54 Statistical Pitfalls, Expanded

Beyond the headline failure modes already catalogued, several subtler statistical pitfalls are worth
recording. The first is confusing the prior standard deviation with the posterior standard deviation: the
prior standard deviation is an input describing belief before data, while the posterior standard deviation
is an output describing belief after data, and they coincide only in the degenerate no-data limit. The
second is reading the credible interval as a frequentist confidence interval: under the Bayesian model the
parameter is random and the interval fixed, and the 95% refers to posterior probability mass, not to a
long-run coverage over hypothetical repeated experiments. The third is treating the corrected residual as
a goodness-of-fit p-value: it is a root-mean-square magnitude, useful as a relative indicator across
moorings and against the observation noise, not a formal test statistic. The fourth is over-interpreting a
drift whose credible interval comfortably includes zero: such a drift is not distinguishable from no drift
at the stated confidence, and a downstream user should treat it accordingly rather than correcting with a
drift the data do not actually support. Each of these is a matter of interpretation rather than
computation, but each can mislead a user who does not keep the Bayesian framing straight.

## §55 Expected Admitted-Count Reference

To help a reviewer sanity-check a calibration run, this section records the admitted observation count a
correctly processed mooring should produce, reasoned from the season structure rather than stated as a
binding number. The season runs daily from the deployment at the epoch through the season close, a span
of roughly half a year. From that span, every calibrated mooring loses the fleet-wide servicing week, and
the southern mooring additionally loses its multi-week May quarantine.

A correctly processed northern, eastern, western, or western-densification mooring should therefore admit
the full season's daily readings minus the fleet-wide week. The southern mooring should admit the full
season minus both the fleet-wide week and its own multi-week quarantine, and so should have a visibly
smaller admitted count than the others — the smallest in the fleet. A reviewer who sees the southern
mooring with the same count as the others knows immediately that its quarantine window was not applied,
and a reviewer who sees any mooring with the full season's count knows the fleet-wide window was missed.
These count checks are among the fastest and most reliable ways to catch a mis-applied exclusion, which is
why they head the review workflow.

The salinity mooring and the retired mooring should appear in no calibration product at all; their
presence in the output is an inclusion-rule error, and their absence is correct. The fleet summary should
list exactly the calibrated moorings — the active temperature and pressure units — and no others.

## §56 Acronyms and Abbreviations

**ASP** — Abyssal Sentinel Programme, the observing programme this notebook serves. **CMWG** — Calibration
and Metrology Working Group, the owner of this notebook. **UTC** — Coordinated Universal Time, the
timestamp convention for all readings. **OLS** — ordinary least squares, the no-prior limit of the
calibration estimate. **MCMC** — Markov chain Monte Carlo, the sampling approach the programme deliberately
does not use because the posterior is closed-form. **RMS** — root mean square, the form in which residual
magnitudes are reported. **PSU** — practical salinity units, used only for the out-of-scope conductivity
mooring. **dbar** — decibar, the pressure unit. **NTC** — negative temperature coefficient, describing the
thermistor's resistance behaviour. These expansions are collected for the reader's convenience and
introduce no binding constant.

## §57 Reprocessing Scenarios

Several circumstances trigger a reprocessing of a season, and each must respect the edition discipline.
The most common is the late arrival of a recovery characterisation that refines a reference instrument's
trust; reprocessing then re-runs the season with the same binding constants but the improved reference
metadata, and the change is recorded so that the published numbers' provenance is unambiguous. A second
scenario is the discovery of a data-management error, such as a mis-keyed status or a mis-stored
timestamp; the database is corrected through the data manager's change process, and the affected season is
re-run. A third scenario is a retrospective harmonisation across seasons, in which several seasons are
reprocessed to a common analysis framework; even then, each season is processed with the binding constants
of the edition under which it was collected, because the constants encode the instruments' actual
conversions and the season's actual servicing, which do not change retrospectively. The cardinal rule
across all reprocessing is that the edition follows the season, never the calendar.

## §58 Cross-Season Trend Assembly

The programme's scientific purpose is a long, stable record, which means stitching calibrated seasons into
a multi-year series. The calibration makes this possible by removing each season's instrument offset and
drift, so that what remains is the genuine ocean signal on a consistent footing. Assembling the trend
requires care at the season boundaries: the offset is defined at each season's epoch, so two consecutive
seasons' calibrated records meet at the boundary only if each has been corrected with its own season's
estimate, and a naive concatenation that applied one season's calibration across the boundary would
introduce an artificial step. The programme therefore corrects within each season and joins the corrected
records, propagating the per-season posterior uncertainties into the assembled trend so that the long
record carries an honest uncertainty envelope. None of this assembly is part of the per-season calibration
this notebook governs, but it is the reason the per-season calibration must be done correctly and
auditably.

## §59 Data Provenance and Chain of Custody

Every published calibration value can be traced backward through a chain of custody: from the value to the
report, from the report to the processing run, from the run to the snapshot of the observations store and
the edition of this notebook, and from the store back to the individual moorings and their pre- and
post-deployment characterisations. Each link in the chain is recorded at the time it is made, so that the
chain can be walked years later. The chain exists because abyssal trends are small and contested, and a
calibration value that cannot be traced to its inputs cannot be defended when a trend it underpins is
questioned. The provenance discipline is therefore not bureaucratic overhead but the foundation of the
programme's scientific credibility.

## §60 A Worked Review Example

To make the review workflow concrete, consider a hypothetical run submitted for review. The reviewer first
lists the calibrated moorings in the output and confirms they are exactly the active temperature and
pressure units — five moorings — with no salinity unit and no retired unit present. Suppose instead the
output contained six moorings including the salinity unit; the reviewer would stop here and return the run
with a note that the inclusion rule was misread, because salinity is out of scope.

The reviewer next checks each mooring's admitted count. Suppose the southern mooring showed the same count
as the northern mooring; the reviewer would return the run, because the southern mooring's quarantine
window was evidently not applied. Suppose instead all counts were consistent with the season minus the
applicable windows; the reviewer would proceed.

The reviewer then confirms each mooring's corrected residual is materially smaller than its uncorrected
residual. Suppose one mooring showed almost no reduction; the reviewer would investigate whether a
superseded conversion had inflated that mooring's residual, or whether the mooring genuinely does not fit
the linear model and needs escalation. Finally the reviewer spot-checks the epoch, conversions, noise,
priors, and exclusion windows against the governing sections, and only then accepts the run. This worked
example mirrors the checks in the review workflow and shows how each check maps to a specific, common
error mode.

## §61 Appendix H — Mooring Metadata Register

The register below records fixed metadata for each mooring. The coordinates, sounding depths, serials,
and set dates are concrete provenance facts; none is a binding calibration constant, and the calibration
reads the operational status and sensor type from the database rather than from this register.

- **B001 Sentinel-North.** Position 41.8 N, 58.2 W. Sounding 4,182 m. Sensor depth 3,950 m. Thermistor
  pack serial NT-2207; reference thermistor serial RT-1180. Anchor cluster mass 1,150 kg. Set on the
  deployment cruise leg one. Telemetry slot 01.
- **B002 Sentinel-East.** Position 39.6 N, 55.0 W. Sounding 3,760 m. Sensor depth 3,540 m. Strain-gauge
  transducer serial NP-3315; reference quartz transducer serial RP-2098. Anchor cluster mass 1,150 kg.
  Set on leg one. Telemetry slot 02.
- **B003 Sentinel-South.** Position 37.1 N, 57.4 W. Sounding 4,410 m. Sensor depth 4,180 m. Thermistor
  pack serial NT-2231; reference thermistor serial RT-1192. Anchor cluster mass 1,300 kg. Set on leg two.
  Telemetry slot 03. Connector intrusion logged in May; quarantined and serviced.
- **B004 Sentinel-West.** Position 39.9 N, 61.3 W. Sounding 3,990 m. Sensor depth 3,770 m. Strain-gauge
  transducer serial NP-3329; reference quartz transducer serial RP-2104. Anchor cluster mass 1,150 kg.
  Set on leg two. Telemetry slot 04. Handling-induced zero shift noted at pre-deployment bench test.
- **B005 Halocline-1.** Position 40.4 N, 59.1 W. Sounding 4,050 m. Sensor depth 100 m. Conductivity cell
  serial NC-4402; reference cell serial RC-3110. Anti-fouling guard fitted. Set on leg two. Telemetry slot
  05. Salinity channel, out of calibration scope this cycle.
- **B006 Sentinel-Relic.** Position 41.0 N, 56.8 W. Sounding 4,120 m. First-generation thermistor pack
  serial NT-1004. Retained for engineering comparison; retired status. Telemetry slot 06, intermittent.
- **B007 Sentinel-Drift.** Position 40.1 N, 62.0 W. Sounding 3,880 m. Sensor depth 3,660 m. Strain-gauge
  transducer serial NP-3341; reference quartz transducer serial RP-2117. Anchor cluster mass 1,150 kg.
  Set late on the prior recovery cruise. Telemetry slot 07.

## §62 Reference Characterisation Records

Each reference instrument carries a pre-deployment characterisation against the laboratory standard, and
the records below summarise them for provenance. The characterisation difference between pre- and
post-deployment, available only after recovery, bounds the reference's own season drift and is required to
be below a small tolerance for the reference to remain trusted; a reference exceeding the tolerance is
retired and its mooring's season flagged for special handling. The pre-deployment records are: RT-1180
characterised against the fixed-point cell with a residual well within tolerance; RP-2098 characterised
against the deadweight tester within tolerance; RT-1192 within tolerance; RP-2104 within tolerance; RP-2117
within tolerance. None of these records introduces a binding calibration constant; they establish the
trustworthiness of the truth channel against which the primaries are calibrated.

## §63 Appendix I — Statistical Properties of the Estimator

This appendix records the estimator's statistical properties so that a reviewer understands its behaviour
in principle. The conjugate posterior mean is a maximum-a-posteriori and posterior-mean estimator that
coincides for the Gaussian model. As a function of the data it is a linear shrinkage estimator: it is the
generalised-least-squares solution shrunk toward the prior mean by an amount that depends on the ratio of
prior precision to data precision.

The estimator is biased toward the prior mean in finite samples, by construction, and the bias shrinks as
the record lengthens because the data precision grows while the prior precision stays fixed. This finite
sample bias is a feature, not a defect: it is the regularisation that keeps short-record estimates sane,
and for the long clean records that dominate the fleet it is negligible. In the limit of an infinitely
long record the estimator is consistent, converging to the true offset and drift, because the shrinkage
vanishes and the estimator approaches ordinary least squares, which is itself consistent for the linear
model under the stated noise assumptions.

The estimator's mean squared error decomposes into a variance term and a squared-bias term. For short
records the shrinkage reduces the variance more than it adds squared bias, so the regularised estimator has
a lower mean squared error than the unregularised least-squares fit; this is the classical bias-variance
trade-off and is the formal justification for using a prior at all. For long records the two estimators are
indistinguishable. The posterior covariance the procedure reports is the exact within-model variance of the
estimator given the data, which is why it is the right uncertainty to propagate downstream.

## §64 Appendix J — Identifiability

The offset and drift are jointly identifiable from any admitted record whose elapsed times are not all
equal, which under daily sampling is every non-trivial record. Identifiability can be read off the design
matrix: the offset and drift are separately determined when the two columns of the design matrix — the
column of ones and the column of elapsed times — are linearly independent, which holds whenever the record
spans more than a single instant. The precision with which each is determined depends on the spread of the
elapsed times: a wide spread pins the drift tightly, while the offset is pinned by the number of
observations and their leverage. This is why a mooring whose record is truncated to a short late-season
stretch by exclusions has a poorly determined offset at the epoch — the record is far from the epoch and
must extrapolate back to it — even though its drift over the observed stretch may be well determined.

The prior guarantees a proper posterior even in the degenerate single-instant case that daily sampling
never produces: with only one elapsed time the data cannot separate offset from drift, but the prior
supplies the missing information and the posterior remains proper, falling back to the prior on the
undetermined direction. This graceful degeneracy handling is another reason the programme uses a proper
prior rather than an improper flat one.

## §65 Fleet Diagnostics

Looking across the fleet rather than mooring by mooring gives a programme-level health check. The two
temperature moorings should show offsets and drifts of comparable magnitude, since they are the same
instrument model in similar conditions, with the southern unit's estimate less precise because of its
truncated record. The three pressure moorings should likewise show comparable behaviour, with the western
unit standing out for its large handling-induced offset. A fleet in which one mooring's estimate is wildly
out of family — an order of magnitude larger offset or an opposite-signed drift with no engineering
explanation — is signalling either an instrument problem or a processing error on that mooring, and the
out-of-family mooring is investigated before the cycle is published. The fleet corrected-residual aggregate
provides a single number that should be small and stable from season to season; a season whose aggregate
jumps is flagged for review even if every individual mooring passed its own checks, because a common-mode
error can pass per-mooring checks while still shifting the fleet aggregate.

## §66 Sampling Cadence and Aliasing

The daily reporting cadence is a deliberate compromise between resolving the calibration trend and
limiting telemetry volume. A drift that accumulates over months is resolved with enormous redundancy by
daily samples, so the cadence is far finer than the calibration strictly needs; the redundancy is what
makes the posterior so tight for long records. The cadence does, however, alias higher-frequency ocean
signals: a barotropic tide of roughly daily and sub-daily period is sampled once per day and folds into
low-frequency apparent variability in the raw record. This aliasing is harmless for the calibration
because the aliased signal appears identically in the primary and the reference and cancels in the
residual, but an analyst plotting a raw channel should be aware that some of its apparent low-frequency
wander is aliased tide rather than genuine slow signal. The calibration never works on a single channel in
isolation, only on the residual, which is why the aliasing does not propagate into the offset or drift.

The high-rate engineering logs downloaded during the servicing window sample far faster than the daily
cadence and are used precisely to characterise the short-term noise that the daily residual cannot
resolve. The separation of the slow daily calibration record from the fast engineering log is intentional:
the daily record measures the season-scale trend, and the engineering log measures the short-term scatter
that becomes the binding observation-noise constant.

## §67 Handling of Missing or Null Readings

The observations store is expected to contain a clean daily record for each mooring across the season,
but a robust processor anticipates gaps. A missing day — a date with no row for a mooring — simply yields
one fewer admitted observation and is not an error; the calibration uses whatever admitted observations
exist and the posterior widens slightly with fewer points. A row whose reading is null rather than a
number is treated as absent rather than as a zero, because a zero would be a spurious data point that
would bias the residual; a processor that coerced nulls to zeros would inject a cluster of false residuals
at the reference value's negative and corrupt the estimate. The current season's store contains a complete
daily record with no nulls, so this handling is precautionary, but it is part of the robust behaviour a
reviewer expects and is the kind of defensive practice that prevents a future season's gap from silently
corrupting a calibration.

## §68 Software Environment and Reproducibility

A calibration run is reproducible only if its software environment is pinned, so the programme records the
exact versions of every component used in a cycle and archives them with the reports. The numerical work
relies on a standard array library for the linear algebra; its version is pinned because floating-point
results, while stable, can differ in their last bits across major versions, and an audited calibration
must reproduce bit for bit. The database access uses the standard library's interface to the embedded
relational store, which requires no external dependency. The pinning discipline mirrors the constant
discipline: just as a binding constant has a single authoritative value per edition, a processing run has a
single authoritative software environment, recorded so that the run can be reproduced exactly years later.
Reproducibility is not an abstract virtue here; it is what allows a contested trend to be defended by
re-deriving the calibration that underpins it from archived inputs.

## §69 Recovery Cross-Check Details

The recovery cross-check is the programme's strongest validation of a field calibration, and this section
records how it is performed. On recovery the primary instrument is bench-tested across its working range
against the same class of standard used for the reference characterisation, yielding an independent
measurement of the instrument's offset and, by comparison with the pre-deployment bench test, its drift
over the deployment. This bench-derived offset and drift are compared against the field calibration's
posterior estimates. Agreement within the combined uncertainties validates the field calibration; a
material disagreement triggers an investigation, because one of the two is wrong and the discrepancy must
be resolved before the season's calibrated record is trusted.

The cross-check is powerful because the bench test and the field calibration are genuinely independent:
the bench test uses a laboratory standard and a controlled environment, while the field calibration uses
the co-located reference and the season's data, and the two share no common error mode except a gross
instrument failure that both would detect. A field calibration that passes the recovery cross-check across
the whole fleet is trusted to correct the scientific record, and the cross-check results are archived with
the cycle so that the validation itself is auditable.

## §70 Future Work

Several enhancements are under consideration for future editions and are recorded here so that the
current edition's scope is clear by contrast. A future edition may extend the calibration model to include
a slow curvature term for instruments whose recovery cross-check reveals non-linear drift, but the current
binding model is strictly offset plus linear drift, and an analyst must not add a curvature term now. A
future edition may estimate the observation noise jointly with the calibration parameters using a
normal-inverse-gamma conjugate prior, but the current binding model treats the noise as known per sensor
type, and an analyst must use the stated noise. A future edition may incorporate a hierarchical prior that
shares information across moorings of the same sensor type, but the current binding model uses independent
per-mooring estimates with a shared per-type prior, and an analyst must not pool across moorings. These
possibilities are noted to make the current scope unambiguous: each is explicitly out of scope now, and
the binding model is the one stated in the governing sections.

## §71 Extended Bibliography and Further Reading

The following themes underpin the programme's practice and are documented in the standard literature for a
reader who wishes to go deeper. The Bayesian treatment of the linear model with a conjugate Gaussian prior
and known noise is covered in standard texts on Bayesian data analysis and on pattern recognition, where
the closed-form posterior derived in Appendix D is presented in full generality. The interpretation of
credible intervals versus confidence intervals is treated in the foundational literature on Bayesian
inference. The metrological traceability of temperature and pressure standards is documented in the
international guidance on the expression of uncertainty in measurement and in the scale definitions for
temperature and pressure. The oceanographic background on abyssal variability and boundary-current
mesoscale activity is covered in the physical-oceanography literature. The data-and-time interchange
conventions used for the timestamps follow the relevant international standard. None of these references
supplies a binding constant; the binding constants are fixed only in the governing sections of this
edition, and the bibliography is provided solely so that the programme's choices can be understood in their
wider context.

## §72 Closing Notes

This notebook has defined, for the current season, exactly how a candidate calibration must read the
binding rules from the governing sections, draw clean observations from the programme database, and produce
a Bayesian estimate of each instrument's offset and drift with honest uncertainties. The recurring theme
throughout the supplementary material has been a single discipline: every binding constant has one
authoritative value, stated in the governing sections of the edition in force, and the long history of the
programme's errors is almost entirely a history of that discipline being broken by the silent reuse of a
superseded value. An analyst who reads the governing sections carefully, applies the inclusion and
exclusion rules exactly, converts and differences in the stated sense, and combines the stated priors with
the stated noise in the conjugate posterior will produce a calibration that passes both the processor's
acceptance and the reviewer's independent review, and that stands up to the recovery cross-check and to
later audit. That is the whole purpose of the calibration, and of this notebook.

## §73 Appendix K — Season Deployment and Event Timeline

The timeline below records the concrete events of the season in date order. Dates that bound the binding
exclusion windows are corroborated here, but the binding windows themselves are stated only in the
governing exclusion section; this timeline is a descriptive record, and several entries describe events
that remove no observations.

- **Early January.** Deployment cruise leg one sets Sentinel-North and Sentinel-East and confirms
  Sentinel-Drift, set late on the prior recovery cruise, on station. Daily reporting begins for these
  units within hours of confirmation.
- **Early January, leg two.** Sentinel-South, Sentinel-West, and Halocline-1 are set, and the retired
  Sentinel-Relic is confirmed in place for engineering reference. Daily reporting begins for the new
  active units.
- **Mid-January.** All active moorings reporting nominally. First weekly engineering summary shows
  telemetry slots one through seven populated, with slot six intermittent as expected for the retired
  unit.
- **Late January.** Sentinel-East logs the season's first energetic knockdown event during a passing
  storm; the pressure reference and primary move together and the residual is unaffected.
- **Early February.** First mesoscale eddy train reaches the southern terminus; Sentinel-South's raw
  temperature record becomes visibly noisier while its residual stays clean.
- **Mid-February.** Routine telemetry; no servicing. The accumulating drift signal becomes statistically
  visible in the longest records.
- **Late February.** Pre-servicing engineering review schedules the fleet-wide window for mid-March and
  confirms the high-rate log download plan that will feed the season's noise characterisation.
- **Early March.** Final week of pre-servicing reporting. Residual trends now clearly established on the
  northern, eastern, western, and densification moorings.
- **Mid-March.** Fleet-wide servicing window. Every mooring is taken offline; anodes are replaced and
  high-rate engineering logs are downloaded. No daily observations from this window enter any
  calibration; the window is the binding fleet-wide exclusion.
- **Late March.** Reporting resumes on all active moorings after servicing. The high-rate logs are
  processed and confirm the season's per-type observation-noise values.
- **April, throughout.** Environmentally quiet. Steady spring warming in the temperature references and a
  quiet pressure field. The cleanest stretch of the season for trend estimation.
- **Early May.** Sentinel-South begins producing intermittent implausible temperature excursions. The
  fault is diagnosed as a connector intrusion admitting seawater, and the mooring is quarantined pending a
  service call. The quarantine start bounds the southern unit's binding exclusion.
- **Mid-May.** Service call to Sentinel-South; the connector is resealed and the unit returned to nominal
  operation. Reporting from the quarantine span is not admitted to calibration.
- **Late May.** Quarantine lifted; Sentinel-South resumes nominal reporting. The quarantine end bounds the
  southern unit's binding exclusion, after which its readings are admitted again.
- **Early June.** All active moorings reporting nominally; the fleet accumulates its maximum season drift.
- **Late June.** Season closes. End-of-season reports are prepared from the full admitted record, and the
  recovery cruise is scheduled for the following month. No observations are removed by the season close.

## §74 Appendix L — Engineering Log Excerpts

The excerpts below are representative entries from the season's engineering log, lightly edited for the
record. They illustrate the kinds of events the log captures and corroborate the narrative; none alters a
binding constant.

- *Sentinel-North, mid-January.* Telemetry nominal; battery voltage within expected band; thermistor
  read-out network temperature stable. No action.
- *Sentinel-East, late January.* Knockdown event recorded during storm; tilt sensor peaked then recovered;
  pressure record shows transient excursion common to primary and reference. No data action; oceanographic
  and mechanical, not instrumental.
- *Sentinel-South, early February.* Elevated raw-temperature variance coincident with eddy activity;
  residual clean; instrument behaving normally in an energetic environment. No action.
- *Fleet, mid-March.* Servicing window opened; all moorings commanded offline; anode condition on recovery
  ranged from light to moderate wear consistent with a half-season; high-rate logs downloaded successfully
  from all active units. Window closed; units commanded back online.
- *Noise characterisation, late March.* High-rate logs processed; short-term scatter for temperature units
  consistent with the binding temperature noise; short-term scatter for pressure units consistent with the
  binding pressure noise, confirming the reduction from the earlier draft figure.
- *Sentinel-South, early May.* Intermittent implausible temperature excursions detected by the gross-range
  monitor; pattern consistent with a connector intrusion; mooring quarantined pending service. Quarantine
  logged.
- *Sentinel-South, mid-May.* Service call completed; connector resealed and tested; unit returned to
  nominal; quarantine to be lifted after a confirmation period.
- *Sentinel-West, pre-deployment (recorded retrospectively).* Bench test before deployment noted a
  transducer zero shift induced during handling; flagged so that the field calibration's large offset would
  be expected rather than alarming.
- *Sentinel-Drift, throughout.* Telemetry nominal across the season; the newest pressure unit behaved as an
  ordinary member of the fleet despite its name.
- *Halocline-1, throughout.* Conductivity cell nominal with anti-fouling guard effective; salinity out of
  calibration scope this cycle; no calibration action.
- *Sentinel-Relic, throughout.* Retired unit; intermittent telemetry on slot six as expected; retained for
  engineering comparison only; never calibrated.

## §75 Appendix M — Units, Quantities, and Conversions Reference

This reference explains the physical quantities and their units so that the conversions in the governing
section are understood rather than merely applied.

Temperature is reported in degrees Celsius. The primary thermistor reports dimensionless integer counts
from its analogue-to-digital converter, and the binding conversion maps counts to degrees Celsius. The
conversion is a pure scale because the firmware has already removed any additive zero, so a count of zero
maps to zero degrees in the converted frame and the additive bias the calibration estimates is a genuine
instrument offset rather than a conversion artefact. The reference thermistor reports degrees Celsius
directly and needs no conversion.

Pressure is reported in decibars, the conventional oceanographic pressure unit, where one decibar
corresponds closely to one metre of depth in seawater. The primary transducer reports dimensionless
integer counts, and the binding conversion maps counts to decibars, again as a pure scale for the same
firmware reason. The reference transducer reports decibars directly.

Salinity, relevant only to the out-of-scope conductivity mooring, is reported in practical salinity units,
a dimensionless scale derived from conductivity ratios. Its conversion belonged to earlier editions and is
not part of the current scope.

Elapsed time is reported in days, and drift accordingly carries units of the channel's physical unit per
day — degrees Celsius per day for temperature, decibars per day for pressure. Keeping time in days rather
than seconds keeps the drift a number of convenient magnitude and the design matrix well scaled, as the
numerical notes explain. The offset carries the channel's physical unit with no time dimension, since it is
the bias at the epoch.

## §77 Appendix O — Index of Governing Constants and Their Downstream Use

This index lists each binding constant, names the governing section that fixes it, and states where it is
used downstream, so that a reviewer can trace every constant from its definition to its effect. The values
themselves are in the governing sections and are not repeated here.

- **Mission epoch** — fixed in the time-convention section; used to compute each reading's elapsed time in
  days, which is the regressor for the drift and sets the meaning of the offset.
- **Time unit (days)** — fixed in the time-convention section; the unit of elapsed time and therefore the
  per-day unit of the drift.
- **Active status** — fixed in the inclusion section; tested against each mooring's database status to
  decide eligibility.
- **Included sensor types** — fixed in the inclusion section; tested against each mooring's sensor type to
  decide eligibility.
- **Per-type unit conversion** — fixed in the conversion section; multiplies each raw reading to obtain the
  converted physical value, which is differenced against the reference to form the residual.
- **Per-type observation noise** — fixed in the noise section; sets the likelihood noise scale, and thus
  the data precision, in the posterior.
- **Per-type offset and drift priors** — fixed in the prior section; set the prior mean and precision that
  regularise the posterior, mattering most for short records.
- **Exclusion intervals** — fixed in the exclusion section; remove readings whose timestamps fall inside a
  window applying to the mooring, before the residual series is formed.

## §78 Appendix P — Consolidated Distractor Ledger (Superseded — Not Binding)

For convenience this ledger gathers, in one place, every superseded value that appears in the supplementary
material, so that a reviewer can recognise each on sight as non-binding. **Every value in this ledger is
superseded; the binding values are in the governing sections.** Superseded mission epochs: the inaugural
season's autumn epoch and the second season's mid-year epoch. Superseded temperature conversions: the
inaugural coarse factor. Superseded pressure conversions: the inaugural coarse factor and the second
season's intermediate factor. Superseded temperature observation noise: the inaugural inflated value.
Superseded pressure observation noise: the inaugural value and the second season's draft value. Superseded
temperature priors: the inaugural wider offset and drift standard deviations. Superseded pressure priors:
the inaugural wider offset and drift standard deviations and the second season's looser drift standard
deviation. Superseded status label: the inaugural deployed label. Superseded scope: the inaugural inclusion
of salinity. Superseded exclusion windows: the inaugural autumn servicing and late-autumn quarantine, and
the second season's mid-year servicing and late-summer quarantine on a different mooring. A reviewer who
encounters any of these in a draft calibration knows immediately that a superseded value has been carried
forward, and the governing sections supply the correct replacement.

## §79 Quality-Control Monitors

The programme runs automated monitors over the incoming telemetry that are distinct from the calibration
itself; they flag operational problems in near real time, whereas the calibration is a season-end
analysis. Understanding them helps an analyst see why the calibration relies on procedural exclusions
rather than on value-based filtering.

The gross-range monitor checks each reading against a wide physically plausible band for its channel and
raises an alert when a reading falls outside it. It caught the Sentinel-South connector-intrusion
excursions in May and triggered the quarantine. The gross-range monitor is deliberately wide: it catches
only physically impossible values, not subtle drift, because the whole point of the calibration is to
measure the subtle drift that a range check cannot see.

The spike monitor checks each reading against its immediate neighbours and flags isolated jumps
inconsistent with the channel's expected rate of change. It is useful for catching single-sample telemetry
corruption but is intentionally not used to clean the calibration input, because a spike filter applied
before calibration could remove genuine extremes of a noisy but valid record and bias the residual. The
calibration instead admits all readings outside the procedural exclusions and lets the Gaussian noise model
account for scatter.

The stuck-value monitor flags a channel that reports an identical value for an implausible run of samples,
which usually indicates a frozen read-out. No mooring triggered it this season. None of these monitors
defines a binding calibration rule; the binding rule is the procedural exclusion, and the monitors merely
inform the operational decisions, such as the quarantine, that the exclusions then encode.

## §80 Telemetry Format and Decoding

Each mooring transmits a compact daily telemetry frame through its assigned slot. The frame carries the
mooring identifier, the reading timestamp, the primary raw count, the reference reading in physical units,
and a block of engineering housekeeping such as battery voltage and tilt. The ground segment decodes the
frame, validates its checksum, and writes the primary raw count and the reference reading into the
observations store with the decoded timestamp, discarding the housekeeping into a separate engineering
archive that the calibration does not read. The calibration therefore sees exactly two measured fields per
reading — the raw count and the reference — plus the timestamp and the mooring identifier, which is why the
observations table carries just those fields.

The decoding preserves the raw count as an exact value rather than pre-converting it, deliberately, so that
the binding unit conversion is applied once, at calibration time, from the governing section, rather than
being baked into the stored data where a superseded factor could become permanent. Storing the raw count
and converting late is a data-management safeguard against exactly the conversion-carry-over error the case
studies describe: because the stored value is raw, a correction to the conversion factor in a future
edition can be applied by reprocessing, whereas a pre-converted store would have frozen the old factor
irretrievably.

## §81 Array Geometry and Design Rationale

The seven moorings are arranged to sample the transect with redundancy in both sensor type and position.
The temperature moorings anchor the northern and southern ends, bracketing the section's meridional
temperature gradient, while the pressure moorings sit on the eastern and western flanks with a third
densifying the western side where the dynamic-height signal is strongest. The salinity mooring sits
mid-array at shallow depth to extend the programme's hydrographic coverage, and the retired engineering
unit is kept in place for instrument comparison. This geometry means the calibration always has at least
two independent instruments of each calibrated type, so a fleet diagnostic can spot an out-of-family
mooring by comparison with its same-type peers, as the fleet-diagnostics section describes.

The design also explains the exclusion structure. The fleet-wide servicing window arises because the whole
array is serviced on a single cruise for efficiency, so every mooring goes offline together. The
mooring-specific quarantine arises because a fault is, by nature, specific to one instrument. The two kinds
of window — fleet-wide and mooring-specific — are exactly the two buoy-identifier cases the exclusion rule
must handle, one applying to all moorings and one to a named mooring.

## §82 Data Latency and Operational Reporting

Although the calibration is a season-end analysis, the programme also produces a low-latency operational
feed for users who need timely data. The operational feed applies the previous season's calibration as a
provisional correction, because the current season's calibration is not available until the season closes;
it is explicitly provisional and is superseded by the definitive season-end calibration once that is
produced. This provisional-then-definitive pattern is another reason the edition discipline matters: the
provisional feed uses the prior edition's constants knowingly and labels its output accordingly, whereas
the definitive calibration uses the current edition's constants, and the two must never be confused. A user
who needs the authoritative record waits for the definitive calibration; a user who needs timeliness
accepts the provisional feed with its caveats. The calibration this notebook governs is the definitive one,
and it reads its constants only from the current edition's governing sections.

## §83 Analyst Training Scenarios

The scenarios below are used to train new analysts. Each is a concrete situation with a correct resolution;
together they exercise the judgement the calibration requires. They are training material and introduce no
binding constant.

**Scenario one — the extra mooring.** A trainee's first run produces six calibrated moorings. Checking
against the inclusion rule, the trainee finds that the sixth is the conductivity mooring, which is active
but carries a salinity channel. The correct resolution is to drop it: the inclusion rule admits only the
included sensor types, and salinity is not among them this cycle. The trainee learns to test sensor type as
well as status.

**Scenario two — the full-season southern count.** A trainee's run shows the southern mooring with the same
admitted count as the northern mooring. Reasoning from the season structure, the trainee realises the
southern mooring should be missing both the fleet-wide week and its own May quarantine, so an equal count
means the quarantine window was not applied. The correct resolution is to apply the mooring-specific
exclusion as well as the fleet-wide one. The trainee learns that exclusions can be both fleet-wide and
mooring-specific.

**Scenario three — the giant offset.** A trainee's temperature run reports offsets of several degrees where
tenths were expected. Tracing the discrepancy, the trainee finds the run multiplied counts by the coarse
inaugural factor rather than the current fine one. The correct resolution is to take the conversion from
the current governing section. The trainee learns that a superseded conversion inflates every residual and
that the symptom is an implausibly large offset with little residual reduction.

**Scenario four — the vanished drift.** A trainee's pressure run reports drifts near zero for a mooring that
visibly drifts in its raw record. Investigating, the trainee finds the run used an inflated observation
noise from a superseded draft, which weakened the likelihood and let the zero-mean prior dominate. The
correct resolution is to use the current governing noise value. The trainee learns how the noise scale
balances prior against data.

**Scenario five — the shifted offset.** A trainee re-runs a season after someone changed the epoch to a
mid-season date and finds every offset changed while every drift stayed the same. Recognising the
signature, the trainee restores the governing epoch. The trainee learns that the offset is defined at the
epoch and that an epoch change folds accumulated drift into the offset.

## §84 The Half-Open Interval Convention, Worked

The exclusion windows are half-open: a reading exactly at a window's start instant is excluded, and a
reading exactly at a window's end instant is admitted. This convention matters at the boundaries and is
worked here so that an implementation handles the edges correctly.

Consider the fleet-wide window. A reading timestamped exactly at the window's start instant is inside the
window and is removed. A reading timestamped one day after the start is inside the window and is removed. A
reading timestamped exactly at the window's end instant is not inside the half-open window and is admitted,
because the interval includes its start but excludes its end. A reading one day before the start, or one day
after the end, is plainly outside and is admitted. Under daily sampling at midnight UTC and windows defined
at midnight UTC, the convention cleanly determines every boundary reading without ambiguity: the start day
is removed and the end day is kept.

The same convention applies to the mooring-specific southern window, with the added subtlety that it applies
only to the southern mooring; the same calendar dates have no effect on any other mooring, whose readings on
those dates are admitted normally. An implementation that applied the southern window to the whole fleet, or
that treated either window as closed at both ends, would mis-handle the boundary readings and produce an
admitted count off by a reading or two from the correct value, which the count check in the review workflow
is designed to catch.

## §85 Per-Constant Right-Versus-Wrong Walkthroughs

This section walks through, for each binding constant, what a correct processing does and what a specific
wrong processing does, to make the failure modes vivid. The correct values are in the governing sections;
the wrong values referenced are the superseded ones from the ledger.

For the **epoch**, correct processing measures elapsed time from the current season's start, so the first
reading is at zero days; wrong processing using an earlier season's epoch makes the first reading hundreds
of days in, inflating the drift's lever arm and folding drift into the offset.

For the **temperature conversion**, correct processing multiplies counts by the current fine factor; wrong
processing using the coarse inaugural factor scales every temperature residual up by the ratio of the two,
producing nonsensical offsets and drifts.

For the **pressure conversion**, correct processing uses the current factor; wrong processing using either
the inaugural coarse factor or the second season's intermediate factor mis-scales every pressure residual,
the intermediate factor being especially insidious because its error is smaller and less obvious.

For the **observation noise**, correct processing uses the current per-type values; wrong processing using an
inflated superseded value over-weights the prior and under-reports genuine drift, while an under-stated
value would over-fit and report falsely tight intervals.

For the **priors**, correct processing uses the current per-type means and standard deviations; wrong
processing using a superseded wider or tighter standard deviation mis-regularises short records, most
visibly widening or narrowing the intervals for the southern mooring.

For the **exclusion windows**, correct processing removes the current fleet-wide and southern windows; wrong
processing carrying forward a prior season's windows removes the wrong dates, needlessly discarding good
readings or admitting bad ones.

For the **inclusion rule**, correct processing calibrates active temperature and pressure moorings only;
wrong processing using the inaugural deployed status label or the inaugural salinity scope calibrates the
wrong set of moorings, either omitting the active units or wrongly including the conductivity unit.

## §86 Residual-Plot Interpretation Guide

When a reviewer inspects a calibration visually, the residual plotted against elapsed time is the single
most informative view, and this guide records what to look for. A healthy residual plot for a calibrated
mooring shows a roughly straight cloud of points: a vertical offset from zero that is the additive bias and
a gentle tilt that is the drift, with scatter about the line consistent with the channel's observation
noise. The fitted line implied by the posterior should pass through the centre of the cloud, and the
corrected residual — the cloud after the line is removed — should be a flat, structureless band about zero.

Several visual pathologies signal specific problems. A cloud that curves rather than tilts indicates
non-linear drift that the binding linear model does not capture; the corrected residual will retain the
curvature and the mooring should be escalated. A cloud with a step part way through indicates an event the
exclusion windows did not capture, such as an undocumented servicing; the reviewer investigates whether a
window is missing. A cloud whose scatter is far wider than the channel's observation noise indicates either
an environmental energetic period that the reference should have cancelled — suggesting a reference problem —
or an instrument fault. A cloud with a gap is simply an exclusion window correctly removed and is healthy. A
reviewer who internalises these patterns can assess a calibration in seconds from its residual plots, which
is why the plots accompany the numeric reports.

## §87 Mooring Power, Endurance, and Duty Cycle

Each mooring runs from a primary battery pack sized for a full season plus margin, and its daily reporting
cadence is chosen partly to fit that energy budget. The sensor read-out, the telemetry transmission, and the
housekeeping each draw a share of the budget, and the daily duty cycle keeps the average draw low enough that
the pack endures the season with reserve for the servicing window's high-rate log download, which is the most
energy-intensive operation of the deployment. The endurance margin matters to calibration indirectly: a
mooring that exhausted its battery early would truncate its record and widen its posterior, so the energy
budget is set conservatively to guarantee a full season of daily readings for every mooring. This season all
moorings reported through the season close with reserve, so no record was truncated by power, and the only
record reductions were the documented exclusions.

## §88 Comparison with Other Observing Systems

The moored array complements other ocean-observing systems, and the comparison clarifies what the array and
its calibration uniquely provide. Profiling floats drift with the currents and sample the upper ocean on a
multi-day cycle; they give broad spatial coverage but no fixed-point time series and no co-located reference,
so they cannot support the kind of per-instrument drift calibration the moored array does. Shipboard
profiling gives high-accuracy snapshots during cruises but only intermittently and only where the ship goes.
Satellite observing gives dense surface coverage but cannot see the abyssal depths the array monitors. The
moored array's distinctive contribution is a continuous, fixed-point, co-located-reference time series at
abyssal depth, and the calibration is what turns that raw series into a trustworthy record by removing the
instruments' own drift. The calibration discipline is therefore not incidental to the array's value; it is
what makes a fixed-point abyssal time series scientifically usable, because at abyssal depths the signals of
interest are small and an uncalibrated instrument drift would swamp them.

## §89 Calibration Scheduling and the Annual Cycle

The calibration follows an annual rhythm tied to the deployment cycle. A season is deployed, runs for its
duration, and is recovered; the definitive calibration is produced after recovery when the post-deployment
reference characterisations are available to confirm the references' trust. Between recovery and the next
deployment, the working group reviews whether any binding constant needs revision in light of the season's
experience and the recovery cross-checks, and if so it issues a new edition through the change-control
process before the next season's processing. This rhythm is why each edition is tied to a season and why the
constants are stable within a season but may change between seasons. An analyst processing a season uses the
edition issued for that season, and the annual review is the mechanism by which, for example, the pressure
conversion and noise were settled across the three editions.

## §90 Data Distribution and the User Community

The calibrated record is distributed to a community of users who build on it: climate analysts assembling
abyssal heat- and mass-content trends, modellers assimilating the time series, and instrument engineers
benchmarking new sensors against the array's calibrated history. Each user community depends on the
calibration in a different way, but all depend on its being correct and auditable. The climate analysts need
the drift removed so that a genuine trend is not confused with instrument ageing; the modellers need the
honest uncertainties so that the assimilation weights the data correctly; the engineers need the per-mooring
offset and drift estimates as ground truth for their bench comparisons. The breadth of the user community is
the ultimate reason for the programme's insistence on a single authoritative set of constants, an
independent review, a recovery cross-check, and a reproducible archive: an error in the calibration would
propagate into climate trends, model states, and instrument benchmarks alike, and only a disciplined
calibration prevents that.

## §91 Reference-Instrument Characterisation Procedure

The trust placed in the reference channels rests on a documented characterisation procedure performed
before each deployment and repeated on recovery. For temperature references the procedure immerses the
instrument in a stirred bath whose temperature is stepped across the instrument's working range and held
at each step until thermally settled, while a fixed-point cell provides the traceable reference
temperature at selected points. The reference thermistor's reported value is compared against the bath
standard at each step, and the differences are recorded as the characterisation residual. A reference
whose characterisation residual stays within a tight tolerance across the range is accepted for
deployment; one that exceeds the tolerance at any step is rejected and not deployed.

For pressure references the procedure applies a sequence of known pressures from a deadweight tester whose
masses are traceable to a national standard, stepping up and then down across the working range to capture
any hysteresis, and recording the reference transducer's reported value against the applied pressure at
each step. Hysteresis between the up and down sweeps is itself a diagnostic: a transducer with excessive
hysteresis is rejected because its field readings could not be trusted to a single calibration curve.

On recovery the same procedure is repeated, and the pre- and post-deployment characterisations are
differenced to bound the reference's own drift over the deployment. This recovery characterisation is the
quantity that confirms a reference remained trustworthy through the season, and it is the reason the
definitive calibration waits for recovery: only after the recovery characterisation is in hand can the
programme certify that the reference against which every primary was calibrated did not itself drift
materially. A reference whose recovery characterisation reveals unexpected drift triggers a special review
of its mooring's season, because the residuals computed against a drifting reference would carry the
reference's drift into the primary's estimated drift.

## §92 Servicing Operations in Detail

The fleet-wide servicing window is a coordinated cruise operation, and understanding it clarifies why it
removes a clean week from every record. The cruise visits each mooring in turn, commands it to a servicing
state that suspends normal reporting, and conducts the servicing: divers or remotely operated vehicles
inspect the mooring hardware, sacrificial anodes are replaced, biofouling is cleaned from the housings, and
the high-rate engineering logs are downloaded over a short-range link that is far faster than the satellite
telemetry. The high-rate download is the energy-intensive operation the battery budget reserves for, and it
is the source of the season's observation-noise characterisation because it captures the instruments'
short-term scatter at a cadence the daily telemetry cannot resolve.

During the servicing state a mooring's primary may still be powered and may even record to its internal
log, but those readings are not telemetered into the operational store and, critically, are not part of the
calibration record; the binding exclusion removes the entire window so that no servicing-state reading
enters the fit. The servicing window's duration is set by the cruise schedule across the whole fleet, which
is why it is fleet-wide rather than mooring-specific, and why it is the same calendar week for every
mooring. After servicing, each mooring is commanded back to normal reporting and resumes daily telemetry.

The mooring-specific quarantine is a different kind of operation: it is an unscheduled response to a
diagnosed fault on a single mooring, and it persists from the first confirmed bad reading until a service
call resolves the fault and a confirmation period establishes that normal operation has resumed. Because it
is a response to a specific instrument's fault, it applies only to that mooring, and its dates are set by
the fault and the service call rather than by the fleet cruise schedule.

## §93 Sensor Failure-Mode Catalogue

A catalogue of the sensor failure modes the programme has encountered helps an analyst recognise when a
record reflects a fault rather than a calibration drift. For thermistor temperature channels the dominant
failure modes are connector intrusion, which admits seawater and produces intermittent gross excursions of
the kind that quarantined the southern mooring this season; read-out reference ageing, which produces a
slow offset and drift and is exactly what the calibration is designed to measure; and, rarely, a complete
read-out freeze that the stuck-value monitor catches. Connector intrusion is episodic and is handled by
exclusion; reference ageing is continuous and is handled by the calibration; a freeze is a hard failure
that ends the record.

For strain-gauge pressure channels the dominant failure modes are handling-induced zero shift, which
produces a large constant offset of the kind seen on the western mooring and which the calibration absorbs
into its offset estimate; strain-element relaxation, which produces a slow drift the calibration measures;
and, rarely, a bridge fault that produces nonsensical values the gross-range monitor catches. The
handling-induced offset is benign for the calibration because the offset is exactly what the calibration
estimates; it matters only that the analyst not be alarmed by a large but stable offset.

For conductivity salinity channels, out of scope this cycle, the dominant failure mode is biofouling, which
is episodic and non-linear and is the reason salinity is handled on a different cadence with anti-fouling
guards rather than under the linear-drift model used here. Cataloguing these failure modes makes clear why
the binding model is offset-plus-linear-drift for temperature and pressure: those are precisely the
continuous failure modes of those sensors, while the episodic modes are handled by exclusion and the hard
failures by the monitors.

## §94 Programme Multi-Year History

The programme's three seasons trace an arc that explains why the binding constants are what they are. The
inaugural season established the array and the basic observing approach but used coarse digitiser firmware
and an immature statistical treatment: the conversions were coarse, the priors were wide, salinity was
calibrated under the same linear model that suits temperature and pressure poorly for a fouling-prone
sensor, and the qualifying status used a label later found ambiguous. The season succeeded in producing a
record but taught the programme that the calibration discipline needed tightening.

The second season revised the firmware for temperature, giving the finer temperature conversion that
remains in force, and began revising the pressure treatment, though it settled on an intermediate pressure
conversion and a draft pressure noise that later proved imperfect. It retired salinity from the calibration
scope, recognising that the linear-drift model did not suit a fouling-prone conductivity sensor, and it
renamed the qualifying status to the current label. It tightened most priors toward their current values
but left the pressure drift prior looser than experience would ultimately justify.

The current season completes the arc: it finalises the pressure conversion and noise from the high-rate
logs, tightens the pressure drift prior in light of several seasons showing genuine pressure drifts to be
modest, sets the epoch to the season start, and establishes the season's servicing and quarantine windows.
The history is recorded so that an analyst understands that each binding constant is the settled endpoint of
a deliberate revision, not an arbitrary choice, and so that the superseded values are recognisable as the
waypoints of that revision rather than as alternatives still in play.

## §95 Appendix Q — Oceanographic Glossary

This glossary defines the oceanographic terms used in the environmental sections, for a reader whose
background is in data processing rather than physical oceanography. None of these terms introduces a
binding calibration constant.

**Abyssal plain** — the flat deep-ocean floor, typically below four thousand metres, where the temperature
moorings sit and where signals of interest are small and slow. **Amphidromic system** — the pattern of
tidal rotation about points of zero tidal range, responsible for the differing tidal phases the eastern and
western pressure moorings see. **Barotropic tide** — the depth-independent component of the tide, the
dominant tidal signal at the moorings' depths, common to primary and reference and so cancelling in the
residual. **Boundary current** — an intensified current along a basin margin; the transect crosses such a
regime, which is why the southern terminus is energetic. **Dynamic height** — a measure of the integrated
density structure that sets slow pressure adjustments on the flanks. **Knockdown** — the tilting and
depression of a mooring under current drag, which changes sensor depth transiently and affects both
channels equally. **Mesoscale eddy** — a coherent rotating feature tens to hundreds of kilometres across
that advects water masses past a mooring on a timescale of weeks, the principal source of the southern
mooring's raw variability. **Mixed layer** — the near-surface layer of nearly uniform properties whose heat
content drives the seasonal temperature cycle the references see. **Practical salinity** — the dimensionless
salinity scale derived from conductivity ratios, relevant only to the out-of-scope conductivity mooring.
**Taut-wire mooring** — a mooring held vertical by a subsurface float, minimising sensor-depth variation and
contributing to the cleanliness of the quiescent moorings' records. **Water mass** — a body of water with a
characteristic temperature-salinity signature whose advection past a mooring appears as genuine signal in
both channels.

## §96 Appendix R — Posterior Predictive and Uncertainty Propagation

This appendix records how to propagate the calibration uncertainty into a corrected reading, for downstream
users, and distinguishes the parameter uncertainty the calibration reports from the predictive uncertainty
of a corrected value. The calibration reports the posterior over the offset and drift, with a mean and a
covariance. A downstream user correcting a raw reading first converts it to physical units with the binding
conversion, then subtracts the offset and the drift evaluated at the reading's elapsed time. The corrected
value's uncertainty has two parts: the uncertainty in the correction itself, which comes from the posterior
covariance of the offset and drift propagated through the linear correction, and the irreducible observation
noise of the reading being corrected.

Propagating the parameter uncertainty through the correction at elapsed time t uses the design row for that
time, namely the pair consisting of one and t: the variance contributed by the parameter uncertainty is that
row multiplied by the posterior covariance and by the row again, a scalar that grows with elapsed time
because the drift uncertainty is leveraged by t. Adding the observation noise variance gives the total
predictive variance of the corrected value, and its square root is the predictive standard deviation. A
downstream user who wants a predictive interval for a corrected reading uses this total predictive standard
deviation, whereas a user who wants only the uncertainty of the calibration parameters uses the posterior
covariance directly. The distinction matters because the predictive interval is always wider than the
parameter interval by the observation noise, and conflating the two understates the uncertainty of a
corrected reading. The per-season calibration this notebook governs reports the parameter posterior; the
predictive propagation is a downstream computation documented here for completeness.

## §97 Data Format Versioning

The observations store's schema is versioned so that a processor can detect a format change rather than
silently misreading it. The current schema is the two-table form documented in the data dictionary, with the
buoys table carrying the identifier, name, sensor type, status, and raw-units label, and the observations
table carrying the surrogate key, the buoy identifier, the timestamp, the raw reading, and the reference
reading. Earlier programme seasons used variant schemas — an earlier season folded the reference into a
separate table joined by timestamp, and the inaugural season stored pre-converted physical values rather
than raw counts — but the current store uses the documented form, and a processor should read exactly the
documented columns. The lesson from the inaugural season's pre-converted store, which froze a superseded
conversion irretrievably into the data, is why the current store keeps the raw count and converts late from
the governing section; the schema version is the marker that tells a processor it is reading the current,
raw-count form rather than a legacy pre-converted one.

## §98 Risk Register

The programme maintains a risk register for the calibration, and the principal entries are recorded here so
that an analyst understands the controls that surround the work. The highest-likelihood risk is the silent
reuse of a superseded constant, controlled by the single-authoritative-source discipline, the precedence
note, and the reviewer's constant spot-check. The highest-impact risk is an undetected reference drift that
would carry into every primary estimate on a mooring, controlled by the pre- and post-deployment reference
characterisation and the recovery cross-check. A moderate risk is a mis-applied exclusion window, controlled
by the admitted-count check in the review workflow. A moderate risk is a schema change misread as data,
controlled by the schema versioning and the data dictionary. A lower-likelihood risk is a sign error in the
residual, controlled by the explicit sign convention restated wherever the residual is mentioned. A
lower-likelihood risk is a numerical error in the posterior assembly, controlled by the no-prior limit
self-check and the unit sanity check. Each risk has an owner among the processor, reviewer, and data-manager
roles, and the register is reviewed between seasons alongside the constants. The register exists because a
calibration that feeds climate trends, model assimilation, and instrument benchmarks cannot rely on care
alone; it needs explicit controls whose effectiveness can be audited.

## §99 Cruise Logistics and Mooring Deployment Engineering

Each season's deployment and recovery are conducted from a research vessel over two cruise legs, and the
logistics bear on the data in ways worth recording. A mooring is assembled on deck in the order it will
enter the water, anchor last, and is deployed anchor-first so that the line pays out under tension and the
sensor package settles to its design depth without tangling. The anchor is released on an acoustic command
once the vessel is over the target position, and the mooring free-falls to the bottom while the vessel holds
station; an acoustic survey then triangulates the settled position, which is logged as the mooring's
coordinates. The settling and survey take a few hours, after which the mooring is commanded to begin daily
reporting, which is why each record begins at or very near the season epoch rather than exactly at it.

The two-leg structure explains why the moorings were set on different days within the first week: the
northern and eastern moorings and the densification unit went in on the first leg, and the southern,
western, and conductivity moorings plus the confirmation of the retired unit on the second. The staggered
sets are invisible to the calibration because elapsed time is measured from the common mission epoch, not
from each mooring's individual set time, so a mooring set a day later simply has its first reading at an
elapsed time of about one day rather than zero. The deployment engineering is recorded so that an analyst
understands the provenance of the coordinates and depths in the metadata register and the slight stagger in
record start times.

## §100 Instrument Procurement and Acceptance Testing

Before an instrument joins the fleet it passes a procurement acceptance test distinct from the deployment
characterisation. The acceptance test exercises the instrument across its full working range and over a
thermal cycle to expose early-life instability, and an instrument that has not settled to stable behaviour
is not accepted. The acceptance test also establishes the instrument's nominal count-to-physical mapping,
which informs the firmware conversion, though the binding conversion in force for a season is always the one
stated in that season's governing section rather than the procurement nominal, because firmware revisions
between procurement and deployment can change the effective mapping. The western mooring's handling-induced
zero shift is an example of a change that occurred after acceptance and before deployment, caught at the
pre-deployment bench test rather than at acceptance, which is why both tests are performed.

Acceptance testing also screens for hysteresis and for excess short-term noise. An instrument whose
short-term noise at acceptance substantially exceeds the class expectation is rejected, which is part of why
the binding observation-noise values can be treated as known per sensor type: the fleet is screened to a
consistent noise class, so a single per-type noise value describes every accepted instrument of that type to
within the precision the calibration needs.

## §101 Inter-Programme Comparison Exercises

The programme periodically compares its calibrated record against co-located observations from other
observing efforts as an external check. When a profiling float or a research-cruise profile passes near a
mooring, its reading at the mooring's depth is compared against the mooring's calibrated value, and
systematic disagreement would indicate a calibration problem the internal checks missed. These comparisons
are coarse, because the external observations are not truly co-located and carry their own uncertainties,
but a gross disagreement would still be informative. The inter-programme comparisons have historically
confirmed the array's calibrated record to within the combined uncertainties, which is part of the external
evidence that the calibration discipline works. The comparisons are an external validation layer beyond the
internal review and the recovery cross-check, and they are recorded in the programme's quality file rather
than entering the per-season calibration this notebook governs.

## §102 Data Stewardship, Citation, and Licensing

The calibrated record is a long-term scientific asset, and its stewardship extends beyond any single season.
Each published season is assigned a persistent identifier so that downstream analyses can cite the exact
version of the record they used, and a superseding reprocessing receives a new identifier rather than
overwriting the old, so that a citation always resolves to the precise data it referenced. The record is
licensed for open scientific use with an attribution requirement, reflecting the programme's mandate to
serve the broad research community. Stewardship also covers format migration: as storage formats evolve over
the decades the programme expects to operate, the record is migrated forward with documented, reversible
transformations, and the raw observations are retained alongside every calibrated product so that any season
can be reprocessed under improved methods. This long-horizon stewardship is the ultimate reason for the
provenance, versioning, and reproducibility disciplines described throughout the supplementary material: a
record meant to support climate-scale science must remain interpretable and reproducible long after the
season that produced it, and the calibration is the step that makes each season's raw observations into a
citable, stewardable scientific product.

## §103 Calendar, Time Zones, and Timestamp Parsing

Because the calibration is fundamentally a regression against time, the handling of calendars and time
zones deserves explicit treatment. Every timestamp in the observations store is in Coordinated Universal
Time, written in the extended ISO-8601 form with a four-digit year, two-digit month and day separated by
hyphens, the letter T, two-digit hours, minutes and seconds separated by colons, and a trailing Z denoting
the zero UTC offset. A processor parses this form directly and computes elapsed time as the difference
between a reading's instant and the mission epoch instant, expressed in days, where one day is exactly
eighty-six thousand four hundred seconds. Because all timestamps share the UTC convention, no time-zone
conversion is needed and none should be applied; introducing a local-time offset would shift the elapsed
times and bias the drift.

The daily cadence places readings at the same time of day each day, so elapsed times are very nearly whole
numbers of days, differing from integers only if a reading's instant differs from the epoch's instant
within the day. The exclusion windows are likewise expressed as UTC instants in the same form, and the
half-open comparison is performed on the parsed instants, not on the string representations, so that the
boundary semantics are exact regardless of formatting. A subtle point is that string comparison of ISO-8601
UTC timestamps happens to coincide with chronological comparison because the format is lexicographically
ordered, but a robust processor compares parsed instants rather than relying on this coincidence, since a
future format variation could break the lexicographic property. Leap seconds are not represented in the
store's timestamps and do not affect the day-scale elapsed times the calibration uses.

## §104 Environmental Compliance and Permitting

Mooring deployment and recovery are conducted under permits that govern operations in the relevant waters,
and compliance bears on the data record only indirectly but worth noting. Permits constrain the deployment
windows and the servicing schedule, which is part of why the fleet-wide servicing occurs as a single
coordinated window rather than as rolling per-mooring visits: concentrating the operation minimises the
permitted ship time and the environmental footprint. The materials used in the moorings, including the
sacrificial anodes replaced during servicing, are selected for low environmental impact, and recovered
hardware is returned to port for refurbishment or disposal under the applicable regulations. None of this
affects a binding calibration constant, but the servicing window that the calibration excludes is shaped in
part by these permitting constraints, and an analyst tracing why the window falls where it does will find
the cruise schedule and its permits behind it.

## §105 A Full Worked Processing Walkthrough

This walkthrough narrates, end to end and conceptually, how a season is processed, tying together the
governing sections and the supplementary guidance. It is a narrative of the process, not a code listing.

Processing begins by reading the governing sections and copying out every binding constant: the epoch and
time unit, the active status and included sensor types, the per-type conversions and noise, the per-type
priors, and the exclusion windows. With the constants in hand, the processor queries the database for the
fleet and identifies the calibrated moorings as the active ones whose sensor type is included, which for the
current season is the five active temperature and pressure moorings, excluding the conductivity unit by type
and the relic unit by status.

For each calibrated mooring, the processor draws the mooring's observations in timestamp order, drops any
reading falling inside an exclusion window that applies to the mooring under the half-open convention,
converts each surviving raw reading to physical units with the mooring's per-type conversion, computes each
reading's elapsed time in days from the epoch, and forms the residual as the converted value minus the
reference value. This yields, per mooring, the cleaned residual series that is the calibration's input and
the content of the per-mooring cleaned-series product.

The processor then forms the Bayesian estimate for each mooring by combining the per-type priors with the
likelihood implied by the residual series and the per-type noise, obtaining the posterior over the offset
and drift, and computes the posterior means and standard deviations, the credible intervals, and the
uncorrected and corrected residual magnitudes. These are the per-mooring calibration products. Finally the
processor aggregates the corrected residuals across the calibrated fleet into the fleet summary.

The processor applies the acceptance checklist — the calibrated set matches the inclusion rule, each
admitted count matches the season minus the applicable windows, every constant matches the governing
sections, and every mooring's residual is reduced — and, on passing, submits the run for independent review.
The reviewer repeats the checks independently and, on agreement, the calibration is published and archived
with its edition, data snapshot, and software versions. This end-to-end narrative is the whole task in
prose, and every step in it is governed by a binding rule in the governing sections or a control in the
supplementary material.

## §106 Maintenance of This Notebook

This notebook is itself a controlled document maintained by the working group. Between seasons the group
reviews each binding constant against the season's experience and the recovery cross-checks, drafts any
revisions through the change-control process, and issues a new edition before the next season's processing.
The governing sections are rewritten to state the new binding values, the revision history and summary
tables are extended to record the change, and the precedence note is reaffirmed so that the new edition's
governing sections are the single authority for the new season. The supplementary material is updated where
experience warrants — a new failure mode added to the catalogue, a new case added to the case-study library —
but the supplementary material never becomes authoritative for the constants; it remains context and
training. The discipline of maintaining the notebook mirrors the discipline of using it: one authoritative
source per edition, every change documented, and the history preserved for audit. An analyst reading any
edition can therefore trust that its governing sections state that season's binding constants completely and
that its supplementary material, however extensive, is context rather than authority.

## §107 Final Addendum

The whole of this notebook reduces to a single operational imperative: read the binding constants from the
governing sections of the edition in force, apply the inclusion and exclusion rules exactly, convert and
difference in the stated sense, and combine the stated priors with the stated noise in the conjugate
posterior, then report the per-mooring estimates and the fleet summary and submit them to independent
review. Everything else in these many sections — the instrumentation detail, the oceanographic context, the
statistical background, the case studies, the registers and logs and appendices — exists to make that
imperative understandable, defensible, and reproducible. An analyst who holds to the imperative and draws
every constant from the governing sections will produce a calibration that is correct, that passes review
and cross-check, and that takes its place in the long record the programme exists to build.

## §108 The Conjugate Estimate Versus Maximum Likelihood

It is instructive to compare the conjugate Bayesian estimate the programme uses against the maximum-
likelihood estimate, which is the ordinary least-squares fit of the residual against elapsed time with no
prior. The two estimates answer subtly different questions. The maximum-likelihood estimate asks which
offset and drift make the observed residuals most probable, ignoring any prior belief; the Bayesian estimate
asks which offset and drift are most probable given both the residuals and the prior. For a long, clean
record the prior contributes negligibly and the two estimates agree to many figures, so a reviewer comparing
them on the eastern pressure mooring or the northern temperature mooring would see essentially identical
numbers. The estimates diverge only when the record is short, where the maximum-likelihood estimate can
swing wildly because a few points poorly constrain a line, while the Bayesian estimate stays anchored by the
prior. The southern mooring, with its two excluded windows, is where the divergence is largest, and there
the Bayesian estimate is the more trustworthy because it does not over-react to the thin record.

The comparison also clarifies what the prior costs. In exchange for stability on short records, the Bayesian
estimate accepts a small bias toward the prior mean, which for the zero-mean priors means a slight shrinkage
of the offset and drift toward zero. For the long records this bias is negligible; for the short records it
is a deliberate and beneficial trade, reducing the estimate's variance far more than it adds bias, as the
statistical-properties appendix explains. A reviewer who wished to see the maximum-likelihood estimate could
obtain it as the limiting case of the Bayesian estimate with the priors widened without bound, which is the
no-prior self-check the implementation notes recommend. The programme uses the Bayesian estimate rather than
maximum likelihood precisely because its records vary so much in length, and the regularised estimate
behaves uniformly across that range while maximum likelihood does not.

## §109 The Fully-Excluded Mooring Edge Case in Detail

Although no mooring in the current season is fully excluded, the edge case deserves detailed treatment
because a future season could encounter it and an implementation must handle it predictably. Suppose a
mooring's entire record fell within exclusion windows — for instance a mooring deployed late and quarantined
for the remainder of a short season. After applying the exclusion rule the mooring would have no admitted
observations, the residual series would be empty, and the design matrix would have no rows. The conjugate
posterior is still defined in this degenerate case: with no data the posterior equals the prior, because the
data precision is zero and the data information vector is zero, so the posterior mean is the prior mean and
the posterior covariance is the prior covariance. An implementation could in principle report the prior as
the posterior, but that would be misleading, because it would present a prior belief as if it were a
calibration result.

The programme's preferred handling is therefore to report such a mooring as having no admissible data and to
omit it from the calibration products with an explicit note, rather than to emit a prior-equals-posterior
result that a downstream user might mistake for an estimate. This handling distinguishes a mooring that was
calibrated and found to have a small offset and drift from a mooring that could not be calibrated at all, a
distinction that matters greatly to a downstream user deciding whether to trust a correction. The current
season presents no such mooring, so this handling is precautionary, but it is part of the robust behaviour
the programme expects and a future season may require.

## §110 Common-Mode Rejection and the Role of the Reference

The single feature that makes the calibration possible is the co-located reference, and its role is worth a
dedicated treatment. Because the reference and the primary sample the same water at the same instant, any
genuine ocean signal — the seasonal cycle, the mesoscale eddies, the tides, the knockdown excursions —
appears in both channels with the same magnitude and sign, and subtracting the reference from the converted
primary cancels it. This common-mode rejection is what leaves the residual containing only the primary's
own offset, its own drift, and the observation noise, which are precisely the quantities the calibration
estimates. Without the reference, the primary's drift would be hopelessly confounded with the genuine slow
ocean signal, and no amount of statistical sophistication could separate them from a single channel.

The effectiveness of the common-mode rejection depends on the reference being truly co-located and truly
trustworthy. Co-location is engineered by clamping the reference within centimetres of the primary so that
the two sample the same parcel; trustworthiness is established by the characterisation and confirmed by the
recovery cross-check. A failure of either would degrade the rejection: a reference mounted too far from the
primary would see a slightly different parcel and leave a residual contaminated by the spatial difference,
and a drifting reference would leave its own drift in the residual masquerading as primary drift. The
programme controls both, which is why the residual can be trusted to contain only the primary's calibration
term and noise, and why the whole edifice of the calibration rests on the reference channel.

## §111 Appendix S — Statistical Terms Glossary

**Bayesian estimate** — an estimate derived from the posterior distribution, here the posterior mean of the
offset and drift. **Conjugate prior** — a prior whose family is closed under the likelihood, giving a
closed-form posterior; the Gaussian prior is conjugate to the Gaussian likelihood with known variance.
**Credible interval** — an interval containing a stated posterior probability mass for a parameter.
**Design matrix** — the matrix of regressors in a linear model. **Likelihood** — the probability of the
observed data as a function of the parameters. **Maximum likelihood** — the parameter value maximising the
likelihood, equal to ordinary least squares for the Gaussian linear model. **Posterior** — the distribution
of the parameters after combining prior and likelihood. **Posterior predictive** — the distribution of a new
observation given the data, combining parameter uncertainty with observation noise. **Precision** — the
inverse of a variance or covariance; precisions add when independent information is combined. **Prior** — the
distribution of the parameters before seeing the data. **Regularisation** — the stabilising effect of the
prior on an estimate, most visible for short records. **Residual** — here, the converted reading minus the
reference; in regression generally, the difference between an observation and its fitted value. **Shrinkage**
— the pulling of an estimate toward the prior mean, the mechanism of regularisation. **Variance** — the
squared scale of a distribution; the square root of a parameter's posterior variance is its reported
standard deviation.

## §112 Daily Cadence: Rationale and Consequences

The choice of a daily reporting cadence rather than a faster or slower one is a deliberate design decision
with several consequences for the calibration. A faster cadence would resolve sub-daily ocean signals but
would consume telemetry bandwidth and battery energy for no calibration benefit, since the drift the
calibration measures evolves over months and is already enormously over-sampled at daily resolution. A
slower cadence — weekly, say — would conserve energy but would thin the record so that exclusion windows
removed a larger fraction of it and the posterior widened, and it would make the southern mooring's
twice-excluded record uncomfortably sparse. Daily sampling sits at the sweet spot: it over-samples the drift
generously enough that the posterior is tight even after exclusions, while remaining within the energy and
bandwidth budget for a full season. The consequence for the calibration is that every calibrated mooring,
except where exclusions intervene, contributes on the order of a hundred and fifty to a hundred and eighty
admitted daily readings, which is far more than enough to pin a two-parameter line, and the precision is
limited in practice by the span of elapsed time rather than by the number of points. This is why the drift
credible interval widens for the southern mooring, whose exclusions shorten its span, more than it would for
a mooring that merely lost a few scattered days.

## §113 Extended Frequently Asked Questions

**Does the order of observations matter to the estimate?** Mathematically no — the posterior depends on the
sums that form the normal equations, which are order-independent — but ordering by timestamp is required for
the cleaned-series product and makes the computation reproducible and the diagnostics readable.

**What if the database contains a duplicate reading?** A genuine duplicate would double-count in the sums and
slightly distort the estimate; the current store contains no duplicates, but a robust processor that
encountered them would treat identical rows as a single reading, because a duplicate is a data-management
artefact rather than two independent measurements.

**Why is the drift reported per day rather than per year?** Because the binding time unit is days, and
reporting the drift in the binding unit avoids an extra conversion that could introduce an error; a
downstream user who prefers a per-year figure multiplies by the number of days in a year, but the calibration
reports the per-day rate that the model fits directly.

**Can the offset and drift priors differ between two moorings of the same sensor type?** No — the priors are
per sensor type, so the two temperature moorings share the temperature priors and the three pressure
moorings share the pressure priors. Per-mooring priors are not part of the binding model.

**What makes a mooring's corrected residual large despite a good fit?** Either genuine non-linear drift the
linear model cannot capture, or an unexcluded event, or a reference problem; each is investigated rather than
ignored, because a large corrected residual signals that the linear offset-plus-drift model has not explained
the mooring's behaviour.

**Is the noise the same for every mooring of a type?** Yes — the observation noise is per sensor type and is
treated as known, having been characterised from the high-rate logs to a consistent class across the
fleet's screened instruments.

## §114 The Prior Elicitation Process

The Gaussian priors in the governing prior section were not chosen arbitrarily, and recording how they were
elicited helps a reviewer judge proposed changes. The offset priors were centred on zero because the fleet's
screened instruments show no systematic tendency to read high or low at deployment; a non-zero offset prior
mean would encode a directional belief the acceptance testing does not support. The offset prior standard
deviations were set wide enough to span the range of zero shifts seen across deployments — handling-induced
shifts of the kind the western mooring exhibits are not rare, so the offset prior must be wide enough not to
fight a genuine large offset, which is why the pressure offset prior is wider than the temperature offset
prior, pressure transducers being more prone to handling shifts.

The drift priors were likewise centred on zero, since an instrument is as likely to drift up as down, and
their standard deviations were set from the distribution of drifts observed across past seasons. Several
seasons of history showed temperature drifts to be very small and pressure drifts somewhat larger but still
modest, which is why the temperature drift prior is tighter than the pressure drift prior, and why the
current edition tightened the pressure drift prior from the looser Edition 2 value once the accumulated
history showed the looser prior to be unnecessarily permissive. The elicitation deliberately errs toward
weakly informative priors: the standard deviations are wide enough that a full season of data dominates them
for any intact record, so the priors regularise without dictating, and the data speak wherever they are
informative. A proposed change to a prior would have to show, from the accumulated drift and offset history,
that the current width mis-describes the fleet, and would go through the change-control process with that
evidence.

## §115 The Annual Review Cycle in Detail

Between the recovery of one season and the deployment of the next, the working group conducts an annual
review that determines whether a new edition is needed. The review assembles the season's recovery
cross-checks, the reference recovery characterisations, the inter-programme comparisons, and any incidents
logged during processing, and asks of each binding constant whether the season's evidence supports a change.
A constant is changed only if the evidence is clear and the change improves future calibrations; stability is
otherwise preferred, because every change creates a new edition boundary across which constants must not be
carried. The review that produced the current edition, for example, changed the pressure conversion and
noise because the high-rate logs and deadweight characterisations gave clear evidence, tightened the pressure
drift prior because the multi-season drift history justified it, and left the temperature constants unchanged
because no evidence called for a change. The review documents its reasoning for each constant, whether
changed or not, so that the provenance of the edition is complete, and it issues the new edition before
processing begins so that the season is processed under settled constants from the outset.

## §116 Programme Staffing and Training

The calibration is operated by a small team filling the processor, reviewer, and data-manager roles, and the
programme invests in training because the discipline the calibration requires is as much cultural as
technical. New analysts work through the training scenarios, learn to read the governing sections as the
single authority, and shadow an experienced reviewer before reviewing independently. The training emphasises
the failure modes the case-study library catalogues, because the programme's experience is that technical
skill is rarely the limiting factor — a competent analyst can implement the conjugate estimate — whereas the
discipline of always drawing constants from the governing sections, applying the rules exactly, and
respecting the role separation is what actually prevents errors. The role separation is maintained even when
the team is small, with the processor and reviewer always being different people for a given cycle, because
the independent review is the principal control against a processor's blind spot. The training and staffing
are recorded here to make clear that the calibration is a disciplined operation with defined roles and
deliberate skill development, not an ad-hoc computation.

## §117 Cross-Edition Outcome Comparison

A retrospective comparison of the three editions' outcomes illustrates why the discipline matters and
provides a final catalogue of superseded values for recognition. Under the inaugural edition, processed with
its coarse conversions and wide priors, the calibrated offsets and drifts were noisier and the salinity
moorings were calibrated under a model that suited them poorly, so the inaugural calibrated record carries
larger uncertainties than later seasons. Under the second edition, with the temperature conversion refined
but the pressure treatment intermediate, the temperature calibrations sharpened markedly while the pressure
calibrations remained slightly biased by the intermediate conversion and the draft noise, a bias caught only
in the subsequent review. Under the current edition, with all constants settled, both temperature and
pressure calibrations are expected to be at their sharpest, and the recovery cross-checks will confirm
whether that expectation holds. The superseded values that produced the earlier outcomes — the inaugural
autumn epoch, the coarse conversions, the wide priors, the deployed status, the salinity scope, the autumn
and late-autumn windows; the second edition's mid-year epoch, intermediate pressure conversion, draft
pressure noise, looser pressure drift prior, mid-year servicing window, and late-summer single-mooring
quarantine — are all recorded here together so that an analyst encountering any of them recognises it at once
as belonging to a past edition. The current binding values are in the governing sections, and the comparison
of outcomes is the strongest argument for reading them from there and nowhere else: each refinement
measurably improved the calibration, and each refinement would be undone by carrying a superseded value
forward.

## §118 Appendix T — Computing and Database Terms

**Co-located column** — here, the reference reading stored alongside the raw reading in the same observation
row, enabling the residual to be formed without a join. **Foreign key** — the buoy identifier in the
observations table referencing the buoys table. **Half-open interval** — a time interval including its start
instant and excluding its end instant, the convention for exclusion windows. **ISO-8601** — the timestamp
interchange format used for all readings, in UTC with a trailing Z. **Primary key** — the unique identifier
of a row, the buoy identifier in the buoys table and the surrogate observation identifier in the observations
table. **Raw count** — the integer-valued sensor output before unit conversion, stored so that conversion is
applied late from the governing section. **Relational store** — the embedded database holding the buoys and
observations tables. **Schema version** — the marker identifying the store's table structure so a processor
reads the documented columns. **Surrogate key** — an identifier with no physical meaning, used as the
observations primary key. **UTC** — Coordinated Universal Time, the single time zone for all timestamps.

These computing terms complement the statistical and oceanographic glossaries and complete the notebook's
reference vocabulary; like those glossaries, this one introduces no binding constant.

## §119 Appendix U — Section Index

For navigation, the notebook's structure is as follows. The front matter and context occupy the first five
sections: the executive summary, the mission background, the fleet overview, the instrumentation, and the
deployment narrative. The binding governing sections occupy sections six through thirteen: the mission epoch
and time convention, the sensor inclusion criteria, the unit conversion standards, the observation noise
model, the Bayesian prior elicitation, the exclusion and maintenance protocol, the inversion methodology, and
the output and reporting requirements. The supplementary material begins at section fourteen and runs to the
end: the revision history and its extension, the case-study library, the glossaries, the appendices on the
derivation, the metadata and characterisation registers, the statistical-properties and identifiability
appendices, the operational and governance sections, the engineering and environmental notes, the worked
examples and walkthroughs, the risk register, and the closing notes and addenda. Only sections six through
thirteen are binding; everything before and after is context, training, and reference. A reader seeking a
binding constant goes directly to the relevant governing section; a reader seeking to understand why a
constant is what it is, or how the surrounding programme operates, finds it in the supplementary material.

## §120 Closing Index Note

This notebook has been written to be read at two depths. An analyst processing the season reads the governing
sections to obtain the binding constants and applies them through the methodology and reporting requirements,
and that is sufficient to produce a correct calibration. A reviewer, a new analyst, or an auditor reads
further into the supplementary material to understand the instruments, the ocean, the statistics, the
operations, and the history that give the binding constants their meaning and their provenance. Both readings
converge on the same operational imperative stated in the final addendum: draw every constant from the
governing sections of the edition in force, apply the rules exactly, and submit the result to independent
review. The notebook is long because the programme it serves is long-lived and its record is consequential,
and a consequential record deserves a calibration whose every constant, rule, and control is documented,
justified, and auditable. With that, the notebook is complete for the current season.

## §121 Appendix V — Lessons-Learned Compendium

This compendium distils the programme's accumulated lessons into a single reference, each drawn from a real
episode and each reinforcing a control documented elsewhere in this notebook. The lessons are recorded so
that an analyst inherits the programme's hard-won experience rather than rediscovering it.

The first lesson is that a correct procedure fed a wrong constant produces a confidently wrong answer, learned
when an Edition 1 conversion was carried into an Edition 2 season and inflated every temperature offset; the
control is the single-authoritative-source discipline and the reviewer's constant spot-check. The second
lesson is that the offset is defined at the epoch and an epoch change folds drift into offset, learned when a
mid-season epoch shift jumped every offset while leaving every drift unchanged; the control is treating the
epoch as a binding convention. The third lesson is that an inflated noise value silently suppresses genuine
drift by over-weighting the prior, learned when a draft pressure noise under-reported a visibly drifting
mooring; the control is characterising the noise from the high-rate logs and stating a single binding value.
The fourth lesson is that exclusion windows are the most season-specific of all constants and must never be
carried forward, learned when a prior season's window discarded good data from a current season; the control
is restating the windows each edition and the admitted-count check. The fifth lesson is that a reference
mounted too far from its primary leaves spatial signal in the residual, learned early in the programme's
history; the control is the centimetre-scale co-location requirement. The sixth lesson is that a drifting
reference carries its drift into every primary estimate on its mooring; the control is the pre- and
post-deployment characterisation and the recovery cross-check. The seventh lesson is that the linear model
does not fit every mooring, learned when a mooring with non-linear drift retained a large corrected residual;
the control is reporting the corrected residual and escalating rather than trusting a poor fit. The eighth
lesson is that a sign error in the residual silently flips every estimate, learned painfully enough that the
sign convention is now restated wherever the residual appears; the control is that explicit, repeated
convention. The ninth lesson is that short records need regularisation lest the estimate swing wildly, which
is why the programme uses a weakly informative prior rather than maximum likelihood. The tenth lesson is that
an unauditable calibration cannot be defended when the trend it underpins is questioned, which is why every
cycle is archived reproducibly with its edition, data snapshot, and software versions. Together these lessons
are the reason the calibration is surrounded by the controls this notebook documents, and an analyst who
internalises them will understand not just what the procedure requires but why each requirement exists.

## §122 Appendix W — Reviewer's Quick-Reference Checklist

This quick-reference distils the review workflow into a compact checklist for an experienced reviewer who
needs only a reminder rather than the full narrative. Each item maps to a control documented earlier and to a
specific error mode the control catches.

Confirm the calibrated set equals the active moorings of an included sensor type, with no salinity unit and
no retired unit present, catching an inclusion or status misreading. Confirm each mooring's admitted count
equals the season span minus the exclusion windows that apply to it, with the twice-excluded southern mooring
showing the smallest count, catching a mis-applied or carried-forward window. Confirm every binding constant
used — the epoch, the per-type conversions, the per-type noise, the per-type priors, and the exclusion
windows — matches the governing sections, catching a superseded-value carry-over. Confirm the residual is
formed as converted minus reference in that order, catching a sign error. Confirm the corrected residual is
materially smaller than the uncorrected residual for every mooring, catching a poor fit or an inflated
conversion. Confirm the elapsed time is in days from the epoch, catching a time-unit or epoch error. Confirm
the posterior intervals widen sensibly for the shorter records, catching a prior or noise mis-statement.
Confirm the fleet summary aggregates exactly the calibrated moorings, catching an aggregation error. Confirm
the run is archived with its edition, data snapshot, and software versions, catching a provenance gap. A run
that passes every item is accepted; a run that fails any item is returned with the failing item named. This
checklist is the operational endpoint of the entire notebook, and a reviewer who applies it faithfully closes
the loop that the governing sections open.

## §123 Document End

This edition of the Abyssal Sentinel Programme calibration mission notebook is complete and authoritative for
the current season. Its governing sections fix the binding constants; its supplementary material provides the
context, statistics, operations, history, and controls that make those constants understandable, defensible,
and auditable. An analyst who reads the governing sections, applies their rules exactly, and submits the
result to independent review will produce a calibration worthy of the long abyssal record the programme
exists to build. No content beyond this point is part of the current edition; subsequent editions will be
issued through the change-control process as the annual review warrants, each superseding this one in full and
each restating its own binding constants in its own governing sections.

## §124 Appendix X — Validity of the Modelling Assumptions

It is worth setting out explicitly the assumptions the calibration model makes and the evidence that each
holds for the programme's instruments, so that a reviewer can judge when the model is and is not appropriate.
The first assumption is linearity of the count-to-physical conversion across the working range. The
acceptance and characterisation testing exercise each instrument across its range and confirm linearity to
within the observation noise, so a single multiplicative conversion suffices and no piecewise or polynomial
mapping is needed; an instrument that failed this test would be rejected before deployment, so every deployed
instrument satisfies it.

The second assumption is that the calibration error is an additive offset plus a linear drift in time, with
no curvature over the season. The sensor-physics discussion explains why this holds: the dominant continuous
error mechanisms — read-out reference ageing for thermistors, strain-element relaxation for transducers — are
slow and well approximated as linear over a single season, while the episodic mechanisms are removed by
exclusion and the hard failures by the monitors. A mooring that violated this assumption would reveal itself
through a large corrected residual, and the reporting of that residual is precisely the check on the
assumption.

The third assumption is that the observation noise is zero-mean, Gaussian, and of known per-type scale,
independent across readings. The high-rate engineering logs confirm the scale and the approximately Gaussian
character of the short-term scatter, and the daily spacing makes serial correlation negligible at the
calibration timescale, so the independence assumption holds for the daily record. The known-scale assumption
is what keeps the inversion conjugate and is justified by the fleet screening to a consistent noise class.

The fourth assumption is that the reference is truth — co-located, trustworthy, and free of its own material
drift. The co-location is engineered, the trust is established by characterisation, and the absence of
material reference drift is confirmed by the recovery cross-check; the common-mode rejection that makes the
calibration possible depends on this assumption, and the programme's controls are designed precisely to
guarantee it. The fifth and final assumption is that the exclusion windows correctly identify every period
whose readings should not be trusted. This assumption is procedural rather than statistical: it holds by
construction if the windows are drawn from the season's servicing and quarantine logs, which is why the
windows are the most season-specific constant and why carrying a window forward from another season violates
the assumption. An analyst who understands these five assumptions, and the evidence and controls behind each,
understands the precise conditions under which the calibration is valid, and can recognise the rare mooring or
season for which one of the assumptions fails and escalation rather than routine calibration is the correct
response.

## §125 Appendix Y — Why Inverse-Variance Weighting Matters

A recurring source of error in earlier seasons was treating every observation as equally trustworthy.
Because each Sentinel observation now carries its own measurement standard deviation, and because that
standard deviation varies substantially over a deployment, an unweighted fit and a correctly weighted fit
do not merely differ in their reported uncertainties — they differ in the parameter estimates themselves.
When the noisier observations happen to fall preferentially late in the season, an unweighted fit lets
those late, imprecise points exert as much leverage on the slope as the early, precise ones, and the
estimated drift is pulled toward the noise. The weighted estimate down-weights each observation in
proportion to the inverse of its variance, so the precise observations dominate and the drift is
recovered faithfully. The lesson the programme draws is blunt: a calibration that ignores the
per-observation measurement standard deviation is not merely imprecise, it is biased, and the bias is not
visible without comparing against a weighted reference. The measurement standard deviation is therefore
not optional metadata; it is part of the likelihood, and the inversion must use it.

A related pitfall is to weight by the standard deviation rather than by its square. The weight is the
inverse of the variance, not the inverse of the standard deviation; confusing the two changes how
aggressively the noisy observations are discounted and produces an estimate that is neither the unweighted
nor the correctly weighted answer. Analysts are reminded that the weighting is by inverse variance.

## §126 Appendix Z — Reading the Changepoint Correctly

The change-point structure of the drift is the other place careful analysts diverge from careless ones.
Before the servicing changepoint the residual climbs or falls at the baseline drift rate; after the
changepoint the rate becomes the baseline drift plus the drift change. The drift change is therefore an
increment to the slope, not a new absolute slope and not a step in the level — there is no discontinuity
in the residual at the changepoint, only a change in its rate. An analyst who models the changepoint as a
jump in the offset, rather than a kink in the slope, will misfit every buoy whose drift genuinely changed
at servicing. An analyst who omits the changepoint entirely, forcing a single straight line through the
whole season, will absorb the post-servicing slope change into a compromised single drift and leave a
structured corrected residual that the quality check will flag.

The changepoint is the same instant for every buoy, fixed at the servicing end, and it is expressed in
the protocol as a timestamp; the inversion converts it to elapsed days exactly as it converts every
observation timestamp. The hinge term — the days elapsed beyond the changepoint, floored at zero — is the
third regressor of the model, alongside the constant and the elapsed-time term. Its prior is the
drift-change prior of the governing prior section, and it is estimated jointly with the offset and the
baseline drift, not in a separate second pass, because the three parameters are correlated given the data
and a sequential fit would bias them.

## §127 Appendix AA — Updated Failure-Mode Catalogue

The current cycle's model adds two failure modes to the catalogue, both of which the quality checks are
designed to catch. The first is the unweighted fit: an analyst who ignores the measurement standard
deviation and fits ordinary least squares obtains a biased drift and drift change, and the discrepancy
against the weighted reference exceeds tolerance. The second is the missing or mis-modelled changepoint:
an analyst who fits a single slope, or who models the changepoint as a level jump rather than a slope
kink, leaves structure in the corrected residual and produces parameter estimates that disagree with the
reference. Both failure modes pass a superficial smoke test — the program runs, a posterior is produced —
and are caught only by the independent recomputation that the verifier performs. The programme's guidance
is that the inversion must be the weighted, three-parameter, change-point conjugate estimate exactly as
the governing sections specify; any simpler model is a different, incorrect calculation that happens to
produce numbers of the right shape.

## §128 Appendix AB — Joint Estimation and Graceful Degradation

The three calibration parameters are estimated jointly, in a single conjugate update that fuses the
inverse-variance-weighted observations with the per-sensor priors. Joint estimation matters because the
offset, the baseline drift, and the drift change are correlated given a finite record: the offset trades
off against the baseline drift over the pre-changepoint span, and the baseline drift trades off against
the drift change across the changepoint. A sequential procedure that fixed one parameter before fitting
the next would propagate that correlation into a bias, which is why the programme insists on the single
joint posterior rather than a staged fit.

The priors also provide graceful degradation. A buoy whose record is thinned by exclusions — most
sharply the southern unit, which loses both the fleet-wide servicing week and its own multi-week
quarantine — carries less information about its parameters, especially the drift change, whose lever arm
is the post-changepoint span. For such a buoy the posterior leans more on the prior and its credible
intervals widen, which is the honest and intended behaviour: the estimate does not swing wildly on a thin
record, it relaxes toward the weakly informative prior and reports its reduced confidence. A buoy with a
long, clean, well-weighted record, by contrast, pins all three parameters tightly and the prior barely
shows. The reviewer therefore expects the southern unit's drift-change interval to be the widest in the
fleet, and treats that as a feature of the method rather than a defect of the buoy.

## §129 Appendix AC — Worked Reasoning for a Single Buoy

This appendix narrates, without prescribing code, how an analyst reasons about one buoy end to end, so
the conceptual steps are concrete. Take a pressure buoy that reported daily through the season and was
offline only for the fleet-wide servicing week. The analyst first draws that buoy's observations from the
database in timestamp order, keeping the raw reading, the co-located reference, and the per-observation
measurement standard deviation. The fleet-wide exclusion removes the servicing week; no buoy-specific
window applies to this unit. Each surviving raw reading is multiplied by the pressure unit conversion to
land in decibars, the reference is subtracted to form the residual, and the timestamp is converted to
elapsed days from the mission epoch.

With the cleaned series in hand, the analyst recognises three things the residual must be explained by: a
constant offset present from the start, a baseline drift that accumulates with elapsed days, and a change
in that drift rate after the servicing changepoint. The analyst forms the elapsed-time term and the
post-changepoint hinge term — the days beyond the changepoint, floored at zero — and notes that the noise
on each residual is the measurement standard deviation carried through from the database, which varies
across the season and must weight the fit. The analyst then combines those inverse-variance weights with
the pressure priors on the offset, the baseline drift, and the drift change, and reads off the joint
posterior: three means, three standard deviations, and three credible intervals. Finally the analyst
checks that subtracting the fitted offset, baseline drift, and drift-change terms collapses the residual
to a small, structureless band — the corrected root-mean-square — confirming the model has explained the
buoy's behaviour. If instead a clear bend or trend remained, the analyst would suspect a missing or
mis-placed changepoint, or an unweighted fit, and would revisit the method before trusting the numbers.

The same reasoning applies to every calibrated buoy, with the southern temperature unit additionally
losing its multi-week quarantine to exclusion and therefore carrying the widest intervals, especially on
the drift change whose post-changepoint lever arm is shortened most by that quarantine. The fleet summary
then collects each buoy's corrected root-mean-square into a single fleet indicator that should be small
and stable when every buoy has been calibrated correctly.
