#!/usr/bin/env python3
"""Generate the full-length MSL-SP-118 Revision C standard.

The governing units/method/example region (§8, §9, §10) is spliced in verbatim
from /tmp/governing_region.md so the operative configuration is never altered;
all generated front matter (§1-§7) and back matter (§11 onward, appendices) sit
outside the `## §8` .. `## §10` slice the extractor reads, so the distractors
they carry never reach the parser. Output: environment/settling_standard.md.
"""
import os

GOVERNING = open("/tmp/governing_region.md", encoding="utf-8").read().rstrip() + "\n"

OUT = os.path.join(os.path.dirname(__file__), "..", "sediment-settling-flask",
                   "environment", "settling_standard.md")

EXPERIMENTS = [
    # id, label, suspension, column_cm, fluid, notes
    (1, "SC-2201", "kaolinite slurry, 12 g/L", 40.0, "deionised water at 20 °C",
     "baseline turbidity run; sensor CP-08"),
    (2, "SC-2202", "montmorillonite, 8 g/L", 38.5, "0.01 M NaCl", "swelling-clay control"),
    (3, "SC-2203", "silica flour, 25 g/L", 45.0, "deionised water at 25 °C", "coarse fraction"),
    (4, "SC-2204", "kaolinite slurry, 15 g/L", 42.0, "deionised water at 22 °C",
     "subject of the §10 worked example"),
    (5, "SC-2205", "illite, 10 g/L", 41.0, "0.05 M CaCl2", "flocculated regime"),
    (6, "SC-2206", "calcium carbonate, 30 g/L", 44.0, "tap water at 18 °C", "high-density mineral"),
    (7, "SC-2207", "kaolinite slurry, 14 g/L", 42.0, "deionised water at 21 °C",
     "**the experiment governed by this analysis**"),
    (8, "SC-2208", "bentonite, 6 g/L", 39.0, "0.10 M NaCl", "gel-forming; slow compression"),
    (9, "SC-2209", "silt mixture, 20 g/L", 43.0, "deionised water at 23 °C", "natural sediment"),
    (10, "SC-2210", "alumina, 18 g/L", 40.5, "deionised water at 20 °C", "narrow size band"),
    (11, "SC-2211", "fly ash, 22 g/L", 46.0, "0.02 M NaCl", "industrial residue"),
    (12, "SC-2212", "kaolinite/silica blend, 16 g/L", 42.5, "deionised water at 24 °C", "bimodal"),
]

SENSORS = [
    # model, raw_scale, raw_offset, range, serial
    ("ColumnProbe CP-04", 0.00500, 0.10, "0-1023", "CP04-7781"),
    ("ColumnProbe CP-06", 0.00750, 0.05, "0-2047", "CP06-3120"),
    ("ColumnProbe CP-08", 0.01000, 0.00, "0-4095", "CP08-9904"),
    ("ColumnProbe CP-08", 0.00980, 0.02, "0-4095", "CP08-9911"),
    ("ColumnProbe CP-10", 0.01250, -0.05, "0-4095", "CP10-2245"),
    ("ColumnProbe CP-10", 0.01180, 0.03, "0-4095", "CP10-2251"),
    ("ColumnProbe CP-12", 0.01500, 0.10, "0-8191", "CP12-6680"),
    ("ColumnProbe CP-12", 0.01470, 0.08, "0-8191", "CP12-6692"),
    ("ColumnProbe CP-14", 0.02000, 0.00, "0-8191", "CP14-0034"),
    ("ColumnProbe CP-14", 0.01950, 0.04, "0-8191", "CP14-0041"),
    ("ColumnProbe CP-16", 0.02500, -0.10, "0-16383", "CP16-5519"),
    ("ColumnProbe CP-16", 0.02440, 0.06, "0-16383", "CP16-5527"),
    ("ColumnProbe CP-18", 0.03000, 0.00, "0-16383", "CP18-7702"),
    ("ColumnProbe CP-18", 0.02960, 0.05, "0-16383", "CP18-7719"),
    ("ColumnProbe CP-20", 0.04000, 0.10, "0-32767", "CP20-1188"),
    ("ColumnProbe CP-20", 0.03920, 0.07, "0-32767", "CP20-1196"),
]

LABS = ["Meridian (lead)", "Northvale Geotechnical", "Coastal Sediments Inc.",
        "Université du Littoral", "Hokuriku Soil Mechanics", "Cape Survey Labs",
        "Andes Hydrology Group", "Baltic Particle Science"]


def para(*sentences):
    return " ".join(sentences) + "\n\n"


def header():
    return (
        "# Standard Practice for Settling-Column Sedimentation Analysis\n\n"
        "**Designation:** MSL-SP-118\n"
        "**Revision:** C (effective 2026-01-01)\n"
        "**Supersedes:** Revision A (2019-03-01) and Revision B (2022-06-15)\n"
        "**Issuing body:** Meridian Sedimentation Laboratory — Methods Committee\n\n"
        "> **Precedence.** Only the requirements stated in the governing sections of **this Revision C**\n"
        "> document are binding. Values appearing in the revision history (§12), the worked example (§10),\n"
        "> and the appendices are provided for context, illustration, or historical traceability and are\n"
        "> **not** the operative configuration. Several of them are **superseded** Revision A/B settings or\n"
        "> pertain to a *different* experiment; where any such value differs from the governing analysis\n"
        "> method in §9, §9 controls.\n\n"
    )


def foreword():
    s = "## Foreword\n\n"
    s += para(
        "This practice was developed by the Methods Committee of the Meridian Sedimentation Laboratory",
        "(MSL) to standardise the reduction of settling-column interface-height records into estimated",
        "settling parameters. It consolidates two decades of laboratory experience with hindered- and",
        "compression-settling measurements and replaces the procedures previously circulated as internal",
        "memoranda MSL-IM-44 through MSL-IM-71.")
    s += para(
        "The committee emphasises that this is a *practice* rather than a *test method*: it prescribes how",
        "an already-acquired interface-height series is to be analysed, not how the column experiment",
        "itself is to be run (that is covered by MSL-SP-090). Where a laboratory's local procedure differs",
        "from this practice, the differences shall be recorded in the analysis report and justified.")
    s += para(
        "Revision C introduces three substantive changes relative to Revision B: the breakpoint search",
        "now requires a larger minimum number of points on each side of a candidate transition; the",
        "optimiser iteration budget has been increased; and per-sensor calibration is now mandatory,",
        "withdrawing the former laboratory-wide calibration constant. Operators migrating analyses from",
        "Revision A or B should read §12 carefully, as several historical defaults are now superseded.")
    s += para(
        "Throughout this document, numerical values printed in the governing sections (§5-§9) are binding.",
        "Numerical values printed elsewhere — in the foreword, the worked examples, the inter-laboratory",
        "study, the uncertainty budget, or any appendix — are illustrative and must never be copied into",
        "an analysis configuration in place of the governing values.")
    return s


def section_1():
    s = "## §1 Scope\n\n"
    s += para(
        "This practice covers the reduction of settling-column interface-height time series into estimated",
        "settling parameters for a single experiment. It defines the analysis-method configuration that an",
        "operator must apply: the kinetic model, the parameter-initialisation and optimisation settings, the",
        "confidence-interval convention, the physical constants, and the reporting units. Per-experiment",
        "conditions and per-sensor calibration constants are **not** in this document; they are held in the",
        "laboratory database and are retrieved per experiment (see §5).")
    s += para(
        "The practice applies to aqueous mineral suspensions analysed in vertical settling columns",
        "instrumented with a single optical interface-level probe. It does not cover centrifugal",
        "sedimentation, pipette analysis, hydrometer analysis, or laser-diffraction sizing; those methods",
        "are addressed by separate MSL practices and are referenced here only for context.")
    s += para(
        "This practice does not purport to address all of the safety concerns, if any, associated with its",
        "use. It is the responsibility of the user of this practice to establish appropriate safety, health,",
        "and environmental practices and to determine the applicability of regulatory limitations prior to",
        "use. See §23 for a non-exhaustive summary of laboratory hazards.")
    return s


def section_2():
    s = "## §2 Referenced Documents\n\n"
    s += para("The following documents are referenced. Unless a specific revision is cited, the current",
              "revision applies. None of these referenced documents contains operative analysis values for",
              "this practice; values are taken only from §5-§9 of this document and the laboratory database.")
    refs = [
        ("MSL-SP-090", "Standard Method for Conducting Settling-Column Tests"),
        ("MSL-SP-101", "Sensor Calibration Records and Traceability"),
        ("MSL-SP-118", "this practice"),
        ("MSL-SP-204", "Column Apparatus Maintenance and Cleaning"),
        ("MSL-DB-3", "Experiment Registry Database Schema"),
        ("MSL-QA-12", "Quality Assurance for Sedimentation Analyses"),
        ("ISO 13317-1", "Determination of particle size distribution — Gravitational liquid sedimentation"),
        ("ASTM D422", "Standard Test Method for Particle-Size Analysis of Soils (withdrawn, cited for context)"),
        ("ISO/IEC Guide 98-3", "Uncertainty of measurement (GUM)"),
    ]
    for code, title in refs:
        s += f"- **{code}** — {title}.\n"
    s += "\n"
    return s


def section_3():
    s = "## §3 Terminology\n\n"
    s += para("For the purposes of this practice, the following definitions apply.")
    terms = [
        ("interface height", "the elevation of the clear-supernatant/suspension boundary above the column "
         "base, in centimetres."),
        ("free-settling phase", "the initial, approximately linear descent of the interface, during which "
         "particles settle at a hindered but roughly constant velocity."),
        ("compression phase", "the later regime in which the settled bed consolidates and the interface "
         "approaches its final height asymptotically."),
        ("breakpoint", "the transition time `t_c` separating the free-settling and compression phases."),
        ("initial settling velocity", "the magnitude `v1` of the interface descent rate during the "
         "free-settling phase, in centimetres per second."),
        ("final bed height", "the asymptotic interface height `h_inf` reached after full compression."),
        ("compression rate constant", "the first-order rate constant `k` governing the exponential approach "
         "to the final bed height, in reciprocal seconds."),
        ("effective diameter", "the Stokes-equivalent spherical particle diameter inferred from the initial "
         "settling velocity, reported in micrometres."),
        ("raw level", "the dimensionless integer reported by the optical probe prior to calibration."),
        ("calibration constants", "the per-sensor `raw_scale` and `raw_offset` that convert a raw level to "
         "an interface height in centimetres."),
        ("sequence index", "the monotonic acquisition counter `seq` attached to each sample, used to align "
         "the timing and level channels."),
        ("coverage factor", "the multiplier applied to a standard uncertainty to obtain an expanded "
         "uncertainty at a stated level of confidence."),
    ]
    for term, defn in terms:
        s += f"- *{term}* — {defn}\n"
    s += "\n"
    return s


def section_4():
    s = "## §4 Significance and Use\n\n"
    s += para(
        "Settling-column analysis provides estimates of bulk settling behaviour that are used in the design",
        "of clarifiers, thickeners, and tailings-management facilities, and in the characterisation of",
        "natural sediment transport. The parameters estimated by this practice — the initial settling",
        "velocity, the final bed height, the compression rate constant, and the derived effective diameter —",
        "feed directly into those design and characterisation workflows.")
    s += para(
        "Because downstream design decisions depend on the estimated parameters, it is essential that the",
        "analysis configuration be applied exactly as specified. Small changes to the kinetic model, the",
        "breakpoint search rule, or the confidence-interval convention can shift the reported parameters and",
        "their stated uncertainties enough to affect an engineering decision. For this reason §9 fixes every",
        "element of the analysis configuration, and operators are cautioned against substituting values from",
        "older revisions or from illustrative material elsewhere in this document.")
    return s


def section_5():
    s = "## §5 Calibration and Per-Experiment Conditions\n\n"
    s += para(
        "Per-sensor calibration constants (`raw_scale`, `raw_offset`) and per-experiment conditions (column",
        "height, fluid viscosity, fluid density, particle density, temperature, assigned sensor) are recorded",
        "in the laboratory database and must be read from it for the experiment under analysis — they are not",
        "reproduced here. Physical height is `raw_scale * raw_level + raw_offset` in centimetres. (Revision A",
        "used a single laboratory-wide calibration of `raw_scale = 0.0100`, `raw_offset = 0.0`; this global",
        "calibration is **withdrawn** — always use the per-sensor record.)")
    s += para(
        "The calibration record for each probe is established under MSL-SP-101 and is traceable to the",
        "laboratory's reference length standard. A representative (non-binding) listing of probe records is",
        "given in §17 for context; the authoritative constants for the experiment under analysis are those in",
        "the database, not the listing.")
    return s


def section_6():
    s = "## §6 Test Procedure (summary)\n\n"
    s += para(
        "A specimen is dispersed, the column is filled to its marked height, and the interface elevation is",
        "logged until the bed stabilises. The acquisition order of level samples is **not** guaranteed to be",
        "monotonic in sequence index; each level sample carries its sequence number for alignment with the",
        "timing channel. The full experimental procedure is given in MSL-SP-090; only the analysis of the",
        "resulting record is within the scope of this practice.")
    return s


def section_7():
    s = "## §7 Experiment Registry\n\n"
    s += para(
        "The current registry holds twelve experiments (labels `SC-2201` … `SC-2212`). **The analysis",
        "described by this practice is to be applied to experiment 7 (label `SC-2207`).** Other registry",
        "entries are listed for completeness and must not be analysed in its place.")
    s += "| id | label | suspension | column height | fluid | notes |\n"
    s += "|----|-------|------------|---------------|-------|-------|\n"
    for eid, label, susp, col, fluid, notes in EXPERIMENTS:
        s += f"| {eid} | {label} | {susp} | {col:.1f} cm | {fluid} | {notes} |\n"
    s += "\n"
    s += para(
        "The column heights and fluid descriptions above are contextual; the authoritative per-experiment",
        "conditions used in the analysis are read from the database (§5), not from this table. The table is",
        "provided so an operator can confirm that experiment 7 corresponds to label `SC-2207`.")
    return s


def section_11():
    s = "## §11 Reporting\n\n"
    s += para(
        "Report the breakpoint, the three fitted parameters with their 95% confidence half-widths, the derived",
        "effective diameter, and the fit residual metrics (root-mean-square error in cm, coefficient of",
        "determination, and the number of observations fitted), in the artifact formats required by the task.")
    s += para(
        "Each reported quantity shall be accompanied, in the laboratory archive copy, by the configuration",
        "values used to produce it, so that an auditor can confirm that the governing §9 configuration — and",
        "not a superseded or illustrative value — was applied. The machine-readable configuration object",
        "produced by the analysis serves this purpose.")
    return s


def section_12():
    s = "## §12 Revision History (non-binding)\n\n"
    s += ("- **Revision A (2019):** single-exponential model; breakpoint not modelled; optimiser cap 5000;\n"
          "  laboratory-wide calibration `raw_scale = 0.0100`; confidence intervals reported at a coverage\n"
          "  factor of 2.0; initial guesses `v1 = 0.5 cm/s`, `k = 0.10 1/s`.\n"
          "- **Revision B (2022):** introduced the two-phase model; breakpoint search required ≥3 points per\n"
          "  side; retained the 5000 evaluation cap; retained the coverage factor 2.0; initial guesses\n"
          "  unchanged from Revision A.\n"
          "- **Revision C (2026, current):** breakpoint search requires ≥5 points per side; optimiser cap\n"
          "  10000; per-sensor calibration mandatory; confidence half-widths at the 1.96 multiplier; initial\n"
          "  guesses `v1 = 1.0 cm/s`, `k = 0.05 1/s`. See §9 for the operative values.\n\n")
    s += para(
        "The values listed under Revisions A and B above are recorded solely for traceability. They are",
        "**superseded** and must not be used in a Revision C analysis. Where this history and §9 disagree,",
        "§9 controls.")
    return s


def section_13():
    s = "## §13 Quality Control and Acceptance Criteria\n\n"
    s += para(
        "An analysis is acceptable under this practice when the following criteria are met: the fitted model",
        "explains at least 98% of the variance in the interface-height series (coefficient of determination",
        "≥ 0.98); the root-mean-square residual does not exceed 0.5 cm; the chosen breakpoint lies strictly",
        "inside the observed time range with the required number of points on each side (§9.2); and the",
        "fitted initial settling velocity is positive.")
    s += para(
        "These acceptance thresholds (0.98 and 0.5 cm) are quality gates on the *result*; they are not part of",
        "the fitting configuration and must not be confused with the optimiser settings of §9.3. A run that",
        "fails an acceptance criterion is repeated under MSL-SP-090, not re-fitted with altered settings.")
    s += para(
        "Laboratories shall maintain control charts of the residual RMSE and the coefficient of determination",
        "across runs. A run whose RMSE exceeds the upper control limit of 0.5 cm, or whose coefficient of",
        "determination falls below 0.98, is flagged for review. Control limits are reviewed annually by the",
        "Methods Committee.")
    return s


def section_14():
    s = "## §14 Measurement Uncertainty Budget\n\n"
    s += para(
        "The combined standard uncertainty of each estimated parameter is obtained by propagating the",
        "contributions tabulated below through the fit. The dominant contributions are the level-sensor",
        "calibration uncertainty and the timing-channel quantisation. The expanded uncertainty reported to",
        "the client is the combined standard uncertainty multiplied by the coverage factor of §9.4.")
    s += "| source | type | standard uncertainty | sensitivity | notes |\n"
    s += "|--------|------|----------------------|-------------|-------|\n"
    rows = [
        ("sensor calibration (scale)", "B", "0.3% of height", "∂H/∂scale", "from MSL-SP-101 record"),
        ("sensor calibration (offset)", "B", "0.02 cm", "1", "zero-point drift"),
        ("timing quantisation", "B", "0.5 ms / √3", "∂t", "1 ms acquisition tick"),
        ("interface definition", "A", "0.05 cm", "1", "operator repeatability"),
        ("temperature (viscosity)", "B", "0.2 °C", "∂μ/∂T", "affects Stokes diameter"),
        ("column verticality", "B", "0.1%", "geometric", "alignment check"),
        ("model adequacy", "A", "residual RMSE", "—", "lack-of-fit component"),
    ]
    for src, typ, u, sens, note in rows:
        s += f"| {src} | {typ} | {u} | {sens} | {note} |\n"
    s += "\n"
    s += para(
        "The coverage factor used to expand the combined standard uncertainty to a 95% interval is fixed by",
        "§9.4 at 1.96. Some clients request a 99% interval; the corresponding factor of 2.576 is provided for",
        "reference only and is not used in the standard report. The older laboratory convention of a coverage",
        "factor of 2.0 (Revisions A and B) is superseded.")
    return s


def section_15():
    s = "## §15 Alternate and Superseded Kinetic Models (non-binding)\n\n"
    s += para(
        "For historical context and for comparison studies, three kinetic models have been used at this",
        "laboratory. Only the two-phase model of §9.1 is operative under Revision C.")
    s += para(
        "**Single-exponential model (Revision A, superseded).** `H(t) = h_inf + (H0 - h_inf) * exp(-k*t)`,",
        "with no breakpoint. This model was found to bias the initial settling velocity low for flocculated",
        "suspensions and was replaced in Revision B. It must not be used under Revision C, even though it",
        "remains available in the analysis library for reproducing historical results.")
    s += para(
        "**Power-law compression model (experimental).** `H(t) = h_inf + a * (t + t0)^(-b)`. Investigated in",
        "an inter-laboratory study (§19) but never adopted; parameters are not comparable to the two-phase",
        "model and shall not be reported under this practice.")
    s += para(
        "**Two-phase model (Revision B/C, operative).** Defined in §9.1. Revision C retains the model form",
        "introduced in Revision B but tightens the breakpoint search (§9.2) and the optimiser budget (§9.3).")
    return s


def section_16():
    s = "## §16 Optimiser Configuration Guidance (non-binding commentary)\n\n"
    s += para(
        "The nonlinear least-squares fit of §9.3 is performed with a Levenberg–Marquardt optimiser. This",
        "section provides commentary on the configuration; the binding values are those in §9.3, not those",
        "recalled here for discussion.")
    s += para(
        "Historically (Revisions A and B) the optimiser was capped at 5000 function evaluations, which",
        "occasionally produced non-convergence on long records. Revision C raises the cap to 10000; the §9.3",
        "value governs. The initial guesses were likewise changed: Revisions A and B started the optimiser",
        "from `v1 = 0.5 cm/s` and `k = 0.10 1/s`, whereas Revision C starts from `v1 = 1.0 cm/s` and",
        "`k = 0.05 1/s` (§9.3). The final-bed-height parameter is initialised at the minimum observed height",
        "in all revisions.")
    s += para(
        "Operators should not interpret the commentary in this section as configuration. If a value here",
        "differs from §9.3 — for example the superseded 5000-evaluation cap or the superseded 0.5 cm/s",
        "starting velocity — the §9.3 value is the one to use.")
    return s


def section_17():
    s = "## §17 Sensor Calibration Records (representative, non-binding)\n\n"
    s += para(
        "The following table lists representative probe calibration records maintained under MSL-SP-101. It",
        "is provided for context only; the calibration constants used in an analysis are those attached to",
        "the experiment's assigned sensor in the database (§5), not those in this table.")
    s += "| model | raw_scale | raw_offset | ADC range | serial |\n"
    s += "|-------|-----------|------------|-----------|--------|\n"
    for model, scale, offset, rng, serial in SENSORS:
        s += f"| {model} | {scale:.5f} | {offset:+.2f} | {rng} | {serial} |\n"
    s += "\n"
    s += para(
        "Each probe is recalibrated every six months or after any disassembly. The withdrawn",
        "laboratory-wide constant (`raw_scale = 0.0100`, `raw_offset = 0.0`) appears in none of these records",
        "and must not be substituted for a per-sensor value.")
    return s


def section_18():
    s = "## §18 Experiment Registry Details (non-binding)\n\n"
    s += para(
        "This section expands the registry of §7 with the conditions recorded for each experiment at",
        "acquisition time, together with the acquisition narrative and the quality-control outcome. These",
        "values are contextual; the authoritative per-experiment conditions are read from the database (§5).",
        "The analysis required by this practice applies to experiment 7 only; every other entry is included",
        "for completeness and traceability, and several quote settings that are not the governing ones.")
    for eid, label, susp, col, fluid, notes in EXPERIMENTS:
        sensor = SENSORS[(eid * 3) % len(SENSORS)]
        n_samples = 180 + (eid * 17) % 90
        dur_min = 22 + (eid * 7) % 18
        temp = 18 + (eid * 3) % 8
        s += f"### {label} (experiment {eid})\n\n"
        s += para(
            f"Suspension: {susp}. Nominal column height: {col:.1f} cm. Fluid: {fluid}. Recorded temperature",
            f"approximately {temp} °C. Assigned probe: {sensor[0]} (serial {sensor[4]}). {notes.capitalize()}.")
        s += para(
            f"Acquisition produced {n_samples} interleaved samples over roughly {dur_min} minutes. As with",
            "every record under this practice, the level channel was stored in sensor acquisition order rather",
            "than sorted by sequence index, so the timing and level channels must be realigned by sequence",
            "index before reduction. The timing channel is in milliseconds; conversion to seconds follows §8.")
        s += para(
            f"Quality control: the run met the §13 acceptance criteria, with a residual root-mean-square error",
            f"below 0.5 cm and a coefficient of determination above 0.98 under the governing configuration. The",
            "analyst confirmed that the per-sensor calibration record (not the withdrawn laboratory-wide",
            "constant) was applied when converting raw levels to heights.")
        if eid == 7:
            s += para(
                "**This is the experiment analysed under this practice.** Apply the governing configuration of",
                "§8 and §9: the two-phase model, at least five points on each side of the breakpoint, initial",
                "guesses of 1.0 cm/s and 0.05 1/s with the final-bed-height parameter started at the minimum",
                "observed height, a 10000-evaluation optimiser cap, a 1.96 coverage factor, gravity of",
                "9.81 m/s², milliseconds divided by 1000, and the effective diameter expressed in micrometres.",
                "Do not use the illustrative values from the §10 worked example (which concerns SC-2204) or any",
                "superseded value from the revision history (§12) or the deprecated-defaults appendix (B).")
        elif eid == 4:
            s += para(
                "This experiment is the subject of the §10 worked example. The numbers quoted there",
                "(breakpoint near 9 s, `v1 ≈ 0.5 cm/s`, `k ≈ 0.10 1/s`) pertain to SC-2204 and to the",
                "illustrative starting guesses used there; they are not the configuration for experiment 7.")
    return s


def _fit_row(eid, rep):
    """Deterministic, plausible per-replicate fit summary (illustrative numbers)."""
    tc = 5.0 + ((eid * 13 + rep * 7) % 60) / 10.0
    v1 = 0.30 + ((eid * 11 + rep * 5) % 90) / 100.0
    hinf = 9.0 + ((eid * 17 + rep * 3) % 80) / 10.0
    k = 0.04 + ((eid * 19 + rep * 9) % 14) / 100.0
    rmse = 0.10 + ((eid * 7 + rep) % 35) / 100.0
    r2 = 0.980 + ((eid * 3 + rep) % 19) / 1000.0
    d = 18.0 + ((eid * 23 + rep * 11) % 220) / 10.0
    return tc, v1, hinf, k, rmse, r2, d


def section_25():
    s = "## §25 Validation Dataset Catalogue (non-binding)\n\n"
    s += para(
        "During the development of Revision C the governing configuration was exercised on five replicate",
        "acquisitions of each registry experiment. The per-replicate fit summaries are catalogued here to",
        "document the reproducibility of the method. All numbers are outcomes of the analysis, not inputs to",
        "it; they are specific to the named experiment and replicate and are not configuration values.")
    for eid, label, *_ in EXPERIMENTS:
        s += f"### Catalogue — {label}\n\n"
        s += "| replicate | t_c (s) | v1 (cm/s) | h_inf (cm) | k (1/s) | rmse (cm) | r² | d (µm) |\n"
        s += "|-----------|---------|-----------|------------|---------|-----------|----|--------|\n"
        for rep in range(1, 19):
            tc, v1, hinf, k, rmse, r2, d = _fit_row(eid, rep)
            s += (f"| {rep} | {tc:.2f} | {v1:.3f} | {hinf:.2f} | {k:.3f} | "
                  f"{rmse:.3f} | {r2:.3f} | {d:.1f} |\n")
        s += "\n"
        s += para(
            f"The eighteen replicates of {label} agree to within the §13 control limits. The replicate spread in",
            "the initial settling velocity is the principal contributor to the reported confidence interval,",
            "consistent with the uncertainty budget of §14. These catalogue values illustrate reproducibility",
            "only; the configuration that produced them is the governing §9 configuration in every case.")
    return s


def section_26():
    s = "## §26 Round-Robin Detailed Results (non-binding)\n\n"
    s += para(
        "The 2024 inter-laboratory study (§19) is documented in full here. Each participating laboratory",
        "analysed the common record for every registry experiment using its then-current configuration. The",
        "tables below report each laboratory's recovered initial settling velocity; the spread across",
        "laboratories reflects their differing configurations and motivated the standardisation of Revision C.")
    for li, lab in enumerate(LABS, 1):
        s += f"### Laboratory {li}: {lab}\n\n"
        s += "| experiment | t_c (s) | v1 (cm/s) | h_inf (cm) | k (1/s) | notes |\n"
        s += "|------------|---------|-----------|------------|---------|-------|\n"
        for eid, label, *_ in EXPERIMENTS:
            tc, v1, hinf, k, rmse, r2, d = _fit_row(eid, li)
            note = "two-phase, 5/side, cap 10000, z=1.96" if li in (5, 8) else \
                   ("single-exp, z=2.0" if li == 3 else
                    ("power-law, z=2.576" if li == 6 else "two-phase, 3/side, cap 5000, z=2.0"))
            s += f"| {label} | {tc:.2f} | {v1:.3f} | {hinf:.2f} | {k:.3f} | {note} |\n"
        s += "\n"
        s += para(
            f"{lab} used the configuration noted above throughout the round. Only the rows where a laboratory",
            "used the two-phase model with five points per side, a 10000-evaluation cap, and a 1.96 coverage",
            "factor correspond to the Revision C governing configuration; the remaining configurations are",
            "recorded for traceability and are superseded.")
    return s


def section_27():
    s = "## §27 Frequently Asked Questions (non-binding)\n\n"
    qa = [
        ("Which model should I use for experiment 7?",
         "The two-phase model of §9.1. The single-exponential model is a superseded Revision A model and the "
         "power-law model was never adopted; neither is used under Revision C."),
        ("How many points must lie on each side of the breakpoint?",
         "At least five (§9.2). Revision B required only three; that requirement is superseded. The §10 worked "
         "example and the round-robin rows that used three points per side are not governing."),
        ("What initial guesses should the optimiser use?",
         "v1 = 1.0 cm/s and k = 0.05 1/s, with h_inf started at the minimum observed height (§9.3). The "
         "historical guesses of 0.5 cm/s and 0.10 1/s (Appendix B, Revisions A/B) are superseded."),
        ("What is the optimiser evaluation cap?",
         "10000 (§9.3). The older cap of 5000 is superseded."),
        ("Which coverage factor applies to the confidence intervals?",
         "1.96 (§9.4). The factor 2.0 used in Revisions A/B is superseded, and 2.576 is a 99% factor used only "
         "on explicit client request."),
        ("Which value of gravity do I use?",
         "9.81 m/s² (§8). The more precise standard-gravity value 9.80665 m/s² (Appendix A) is not used in "
         "this reduction."),
        ("How do I convert the timing channel?",
         "Divide milliseconds by 1000 to obtain seconds (§8). The minute conversion (60000 ms) in Appendix A "
         "is for reading old logbooks only."),
        ("In what unit is the effective diameter reported?",
         "Micrometres (§8 and §9.5)."),
        ("The database calibration differs from the §17 table — which do I use?",
         "The database record for the experiment's assigned sensor (§5). The §17 table is representative "
         "context, and the withdrawn laboratory-wide constant is never used."),
    ]
    for q, a in qa:
        s += f"**Q: {q}**\n\n{a}\n\n"
    return s


def section_28():
    s = "## §28 Reference Interface-Height Digests (non-binding)\n\n"
    s += para(
        "For each registry experiment, a digest of the mean interface height across the validation replicates",
        "is tabulated below at fixed elapsed times. The digests document the qualitative settling behaviour —",
        "an approximately linear free-settling descent followed by an exponential approach to the final bed",
        "height — and are provided for context and for cross-checking an analysis pipeline. They are not",
        "configuration values and they are not the data analysed by the practice (which is served per",
        "experiment through the acquisition channels, in milliseconds and raw levels).")
    for eid, label, susp, col, fluid, notes in EXPERIMENTS:
        tc, v1, hinf, k, *_ = _fit_row(eid, 1)
        s += f"### Digest — {label}\n\n"
        s += "| t (s) | mean H (cm) | sd (cm) | phase |\n"
        s += "|-------|-------------|---------|-------|\n"
        for j in range(72):
            t = j * 2.0
            if t <= tc:
                h = col - v1 * t
            else:
                h = hinf + (col - v1 * tc - hinf) * (2.718281828 ** (-k * (t - tc)))
            sd = 0.03 + ((eid + j) % 7) / 100.0
            phase = "free-settling" if t <= tc else "compression"
            s += f"| {t:.1f} | {h:.2f} | {sd:.2f} | {phase} |\n"
        s += "\n"
        s += para(
            f"The {label} digest shows the breakpoint near {tc:.1f} s separating the two regimes. The standard",
            "deviations are the replicate spread and are consistent with the §14 uncertainty budget. These",
            "tabulated heights are summary outputs, not inputs; the analysis reads the raw acquisition",
            "channels from the serving layer and converts them per §5 and §8.")
    return s


def appendix_F():
    s = "## Appendix F — Sensor Calibration Histories (non-binding)\n\n"
    s += para(
        "Each probe carries a dated calibration history under MSL-SP-101. Representative histories are",
        "reproduced here for context. The authoritative constants for an analysis are those attached to the",
        "experiment's assigned sensor in the database (§5), not these historical entries.")
    dates = ["2021-01-12", "2021-07-09", "2022-01-15", "2022-07-11", "2023-01-20", "2023-07-14",
             "2024-01-15", "2024-07-11", "2025-01-20", "2025-07-14", "2025-12-02", "2026-03-18"]
    for model, scale, offset, rng, serial in SENSORS:
        s += f"### {model} — serial {serial}\n\n"
        s += "| date | raw_scale | raw_offset | reference standard | technician |\n"
        s += "|------|-----------|------------|--------------------|------------|\n"
        for di, d in enumerate(dates):
            drift = (di - 2) * 0.00002
            sc = scale + drift
            off = offset + (di - 2) * 0.005
            tech = ["A. Okafor", "L. Bianchi", "R. Haddad", "M. Sato"][di % 4]
            s += f"| {d} | {sc:.5f} | {off:+.3f} | RL-{100 + di} | {tech} |\n"
        s += "\n"
        s += para(
            f"The current record for {serial} is the most recent entry above. The probe is recalibrated every",
            "six months; intermediate drift is within the calibration uncertainty of §14. None of these",
            "entries is the withdrawn laboratory-wide constant.")
    return s


def appendix_G():
    s = "## Appendix G — Commentary on Each Governing Parameter (non-binding)\n\n"
    s += para(
        "This appendix collects commentary on each element of the governing configuration. The binding values",
        "are stated in §8 and §9; the commentary here explains the rationale and the relationship to the",
        "superseded values, and must not itself be read as the configuration.")
    items = [
        ("Kinetic model", "The two-phase model captures both the free-settling and compression regimes with a "
         "single continuous curve. It replaced the single-exponential Revision A model, which systematically "
         "underestimated the initial settling velocity. Governing value: two-phase (§9.1)."),
        ("Breakpoint minimum points per side", "Requiring five points on each side of a candidate breakpoint "
         "stabilises the transition-time estimate against noise. Revision B used three, which admitted spurious "
         "early breakpoints. Governing value: five (§9.2)."),
        ("Initial velocity guess", "Starting the optimiser at 1.0 cm/s improves convergence for the typical "
         "hindered-settling velocities seen in the registry, relative to the 0.5 cm/s used historically. "
         "Governing value: 1.0 cm/s (§9.3)."),
        ("Initial rate-constant guess", "Starting k at 0.05 1/s reflects the slower compression observed with "
         "the current suspensions, relative to the historical 0.10 1/s. Governing value: 0.05 1/s (§9.3)."),
        ("Final-bed-height initialisation", "The final bed height is started at the minimum observed interface "
         "height in all revisions; this is unchanged."),
        ("Optimiser evaluation cap", "Ten thousand evaluations virtually eliminate the non-convergence seen "
         "with the historical 5000 cap on long records. Governing value: 10000 (§9.3)."),
        ("Coverage factor", "A factor of 1.96 yields a 95% Gaussian interval for the large samples typical of "
         "settling-column records, replacing the rounded 2.0 of earlier revisions. Governing value: 1.96 "
         "(§9.4)."),
        ("Gravitational constant", "The rounded value 9.81 m/s² is sufficient given the dominant calibration "
         "and timing uncertainties; the full 9.80665 m/s² is unnecessary here. Governing value: 9.81 m/s² "
         "(§8)."),
        ("Time conversion", "Milliseconds are divided by 1000 to obtain seconds. Governing value: divide by "
         "1000 (§8)."),
        ("Diameter unit", "The Stokes-equivalent diameter is reported in micrometres. Governing value: "
         "micrometres (§8, §9.5)."),
    ]
    for title, body in items:
        s += f"- **{title}.** {body}\n"
    s += "\n"
    return s


def section_19():
    s = "## §19 Inter-laboratory Comparison Study (non-binding)\n\n"
    s += para(
        "In 2024 the Methods Committee organised an inter-laboratory comparison to assess the reproducibility",
        "of the two-phase analysis ahead of Revision C. Eight laboratories analysed a common set of",
        "interface-height records using their then-current configurations. The study is summarised here for",
        "context; none of its tabulated numbers is an operative configuration value.")
    s += "| round | participating lab | model | min points/side | optimiser cap | coverage factor |\n"
    s += "|-------|-------------------|-------|-----------------|---------------|-----------------|\n"
    configs = [
        ("two-phase", 3, 5000, 2.0), ("two-phase", 3, 5000, 2.0), ("single-exp", 0, 2000, 2.0),
        ("two-phase", 4, 8000, 1.96), ("two-phase", 5, 10000, 1.96), ("power-law", 0, 4000, 2.576),
        ("two-phase", 3, 5000, 2.0), ("two-phase", 5, 10000, 1.96),
    ]
    for i, (lab, (model, mps, cap, cf)) in enumerate(zip(LABS, configs), 1):
        mps_s = str(mps) if mps else "n/a"
        s += f"| {i} | {lab} | {model} | {mps_s} | {cap} | {cf} |\n"
    s += "\n"
    s += para(
        "The spread of configurations in the table above motivated the standardisation in Revision C. The",
        "committee adopted the configuration that gave the most reproducible initial settling velocity across",
        "laboratories: the two-phase model with at least five points on each side of the breakpoint, a 10000",
        "evaluation cap, and a 1.96 coverage factor (§9). The other rows record what individual laboratories",
        "did at the time and are not to be emulated.")
    return s


def section_20():
    s = "## §20 Data Acquisition and File Formats\n\n"
    s += para(
        "The acquisition system records two channels per experiment. The timing channel stores, for each",
        "sequence index, the elapsed acquisition time in **milliseconds**. The level channel stores, for each",
        "sequence index, the raw integer probe reading. The two channels are exported independently and, in",
        "the laboratory's serving layer, are paginated; the level channel is not guaranteed to be ordered by",
        "sequence index.")
    s += para(
        "Times are recorded in milliseconds. Older logbooks occasionally quoted elapsed times in minutes; the",
        "conversion 1 min = 60000 ms is provided for reading those logbooks and is not the conversion used in",
        "the analysis, which converts milliseconds to seconds per §8. Heights are derived from raw readings by",
        "the per-sensor calibration of §5.")
    return s


def section_21():
    s = "## §21 Statistical Treatment of the Fit\n\n"
    s += para(
        "Parameter standard errors are obtained from the square roots of the diagonal of the covariance",
        "matrix returned by the optimiser. The 95% confidence half-width for each parameter is the standard",
        "error multiplied by the coverage factor fixed in §9.4. For large samples the Gaussian factor 1.96 is",
        "appropriate and is the value adopted by this practice.")
    s += para(
        "Several alternative conventions exist and are noted here only to forestall their accidental use. A",
        "coverage factor of 2.0 (a common rounding of 1.96) was used in Revisions A and B and is superseded.",
        "A factor of 2.576 corresponds to a 99% interval and is used only when a client explicitly requests",
        "99% coverage. For very small samples a Student-t factor would be used in place of the Gaussian",
        "factor; settling-column records are large enough that this practice uses the Gaussian 1.96 in all",
        "cases.")
    s += para(
        "The derived effective diameter inherits its uncertainty from the initial settling velocity through",
        "the Stokes relation of §9.5; its confidence interval is obtained by propagating the velocity",
        "standard error and is reported at the same 1.96 coverage factor.")
    return s


def section_22():
    s = "## §22 Troubleshooting\n\n"
    items = [
        ("Optimiser fails to converge", "Confirm the evaluation cap is set to the §9.3 value of 10000 rather "
         "than the superseded 5000; verify the initial guesses match §9.3; check that the interface series is "
         "monotonic non-increasing after realignment."),
        ("Breakpoint search returns no candidate", "The record may be too short to provide five points on "
         "each side of any interior time; acquire a longer record under MSL-SP-090. Do not relax the §9.2 "
         "minimum to the superseded value of three."),
        ("Negative fitted velocity", "Indicates a misaligned level channel; re-join the timing and level "
         "channels by sequence index rather than by position."),
        ("Effective diameter implausibly large", "Check that the gravitational constant is the §8 value of "
         "9.81 m/s² and that viscosity and densities were read from the database in SI units."),
        ("Reported interval seems wide", "Confirm the coverage factor is 1.96 (§9.4) and not 2.576 (99%) or "
         "the superseded 2.0."),
    ]
    for symptom, action in items:
        s += f"- **{symptom}.** {action}\n"
    s += "\n"
    return s


def section_23():
    s = "## §23 Safety\n\n"
    s += para(
        "Mineral suspensions may contain respirable fines; prepare and disperse specimens in accordance with",
        "the laboratory's dust-control procedures. Saline and calcium-chloride fluids are mild irritants.",
        "Settling columns are tall glass or acrylic vessels; secure them against toppling. This section is a",
        "summary and does not replace the laboratory's safety documentation.")
    return s


def section_24():
    s = "## §24 Apparatus Maintenance\n\n"
    s += para(
        "Probe windows are cleaned between runs per MSL-SP-204. Columns are inspected for verticality before",
        "filling. The acquisition system clock is checked against a reference each quarter; a drift exceeding",
        "0.1% requires recalibration of the timing channel. Maintenance records are retained for five years.")
    return s


def appendix_A():
    s = "## Appendix A — Units and Constants (non-binding)\n\n"
    s += para(
        "Standard gravity is `9.80665 m/s²`; for routine reduction the rounded value `g = 9.81 m/s²` from §8",
        "is used. 1 cm = 10 mm; 1 Pa·s = 1000 cP. Times may incidentally be quoted in minutes in older",
        "logbooks (1 min = 60000 ms); the acquisition channel used here is in milliseconds (§8). Dynamic",
        "viscosity of water near room temperature is approximately 1.0 mPa·s but the analysis uses the",
        "database value for the experiment, not this nominal figure.")
    s += "| quantity | symbol | value | note |\n|----------|--------|-------|------|\n"
    rows = [
        ("standard gravity", "g_n", "9.80665 m/s²", "rounded to 9.81 in §8 for this reduction"),
        ("reduction gravity", "g", "9.81 m/s²", "the value used (see §8)"),
        ("ms per second", "—", "1000", "time conversion used (§8)"),
        ("ms per minute", "—", "60000", "logbook context only; not used"),
        ("cP per Pa·s", "—", "1000", "viscosity unit conversion"),
        ("95% Gaussian factor", "z", "1.96", "coverage factor used (§9.4)"),
        ("99% Gaussian factor", "z", "2.576", "reference only"),
        ("legacy coverage factor", "k", "2.0", "Revisions A/B; superseded"),
    ]
    for q, sym, val, note in rows:
        s += f"| {q} | {sym} | {val} | {note} |\n"
    s += "\n"
    return s


def appendix_B():
    s = "## Appendix B — Deprecated Parameter Defaults (non-binding)\n\n"
    s += para(
        "Historical optimiser defaults retained for traceability: initial `v1 = 0.5 cm/s`, initial",
        "`k = 0.10 1/s`, evaluation cap `5000`, coverage factor `2.0`, minimum points per side `3`,",
        "single-exponential model. None of these are the Revision C operative settings; see §9.")
    return s


def appendix_C():
    s = "## Appendix C — Worked Examples for Other Experiments (illustrative)\n\n"
    s += para(
        "The following sketches illustrate the analysis on experiments other than the one governed by this",
        "practice. All numbers are illustrative and pertain to the named experiment and its own starting",
        "guesses; none is the configuration for experiment 7.")
    examples = [
        ("SC-2201", 7.2, 0.42, 12.1, 0.08),
        ("SC-2204", 9.0, 0.50, 11.0, 0.10),
        ("SC-2206", 5.5, 0.61, 16.4, 0.14),
        ("SC-2210", 8.1, 0.47, 13.0, 0.09),
        ("SC-2212", 6.8, 0.53, 12.7, 0.11),
    ]
    for label, tc, v1, hinf, k in examples:
        s += para(
            f"*{label}.* An operator obtained a breakpoint near {tc:.1f} s with `v1 ≈ {v1:.2f} cm/s`,",
            f"`h_inf ≈ {hinf:.1f} cm`, and `k ≈ {k:.2f} 1/s`. These values characterise {label} and are not",
            "transferable to another experiment.")
    return s


def appendix_D():
    s = "## Appendix D — Symbols\n\n"
    syms = [
        ("H(t)", "interface height as a function of time, cm"),
        ("H0", "initial (column) height, cm"),
        ("t_c", "breakpoint time, s"),
        ("v1", "initial settling velocity, cm/s"),
        ("h_inf", "final bed height, cm"),
        ("k", "compression rate constant, 1/s"),
        ("mu", "fluid dynamic viscosity, Pa·s"),
        ("rho_p", "particle density, kg/m³"),
        ("rho_f", "fluid density, kg/m³"),
        ("g", "gravitational acceleration, m/s²"),
        ("d", "effective (Stokes-equivalent) diameter, µm"),
        ("z", "coverage factor for confidence intervals"),
    ]
    for sym, desc in syms:
        s += f"- `{sym}` — {desc}\n"
    s += "\n"
    return s


def appendix_E():
    s = "## Appendix E — Bibliography\n\n"
    refs = [
        "Coe, H. S., and Clevenger, G. H. (1916). Methods for determining the capacities of slime-settling tanks.",
        "Kynch, G. J. (1952). A theory of sedimentation. Trans. Faraday Soc.",
        "Richardson, J. F., and Zaki, W. N. (1954). Sedimentation and fluidisation.",
        "Fitch, B. (1962). Sedimentation process fundamentals.",
        "Talmage, W. P., and Fitch, E. B. (1955). Determining thickener unit areas.",
        "Bustos, M. C., Concha, F., Bürger, R., and Tory, E. M. (1999). Sedimentation and Thickening.",
        "ISO 13317-1 (2001). Gravitational liquid sedimentation methods.",
        "ISO/IEC Guide 98-3 (2008). Uncertainty of measurement (GUM).",
        "Meridian Sedimentation Laboratory (2019). MSL-SP-118 Revision A.",
        "Meridian Sedimentation Laboratory (2022). MSL-SP-118 Revision B.",
    ]
    for i, r in enumerate(refs, 1):
        s += f"{i}. {r}\n"
    s += "\n"
    return s


def build():
    parts = [
        header(), foreword(),
        section_1(), section_2(), section_3(), section_4(), section_5(), section_6(), section_7(),
        GOVERNING,  # §8, §9, §10 verbatim
        section_11(), section_12(), section_13(), section_14(), section_15(), section_16(),
        section_17(), section_18(), section_19(), section_20(), section_21(), section_22(),
        section_23(), section_24(), section_25(), section_26(), section_27(), section_28(),
        appendix_A(), appendix_B(), appendix_C(), appendix_D(), appendix_E(),
        appendix_F(), appendix_G(),
    ]
    return "".join(parts)


if __name__ == "__main__":
    doc = build()
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(doc)
    words = len(doc.split())
    print(f"wrote {OUT}")
    print(f"chars={len(doc)} words={words} approx_tokens={int(words/0.75)}")
