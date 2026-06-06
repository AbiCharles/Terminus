## §20 Production Monitoring, Drift Surveillance, and Rollback Runbook

This section specifies the post-promotion monitoring program that governs the consumer-credit 12-month probability-of-default (PD) classifier once it has been promoted to the production champion alias in the MLflow registry. It is operational in nature: it tells the on-call model-monitoring engineer, the Model Risk Management (MRM) reviewer, and the line-of-business owner what is measured, how often, who is accountable, what conditions cause an alert, and exactly how to execute a rollback to the prior champion version when one of the three binding rollback triggers fires. The binding numeric thresholds for those triggers are not restated here; they are defined once, authoritatively, in §13, and every reference below points there. This separation is deliberate. Monitoring code and runbooks change frequently; binding criteria change only through a controlled edition revision. Keeping the numbers in one place prevents the drift between "what the dashboard checks" and "what the governance committee approved" that has historically been a root cause of monitoring incidents at peer institutions.

The program is designed under the conservative-promotion philosophy that runs through this dossier. Promotion is hard to earn and easy to lose. The monitoring layer is the second half of that bargain: a model that has cleared the §6–§13 promotion gates is not trusted indefinitely, but is held to continuous evidence that the population it scores, the way it scores, and the outcomes it produces remain consistent with the conditions under which it was approved. The moment that evidence degrades past a defined boundary, the system is engineered to revert to a known-good prior state rather than to debate in place.

### 20.1 Scope and monitoring philosophy

Production monitoring covers four surfaces, each of which corresponds to a way the model can fail silently after promotion:

1. **Discrimination and ranking performance** — does the model still separate defaulters from non-defaulters as well as it did at promotion? This is the core predictive-quality surface and is governed by the `auc_floor` trigger.
2. **Calibration** — are the predicted PDs still trustworthy as probabilities, not merely as a rank order? A model can retain rank-ordering power while its absolute probabilities drift away from realized default rates, which corrupts every downstream limit, pricing, and provisioning decision that consumes the score.
3. **Population stability** — is the population being scored in production still the population the model was trained and validated on? This is the leading indicator. Population shift almost always precedes performance degradation, and the `drift_psi` trigger exists to catch it before discrimination collapses.
4. **Fairness and approval-rate behavior** — does the model continue to treat the protected groups within the §6 fairness scope equitably, and is the aggregate approval rate stable enough that a sudden contraction is detected before it becomes a conduct or safety-and-soundness event? Approval-rate behavior is governed by the `approval_rate_floor` trigger.

A central design constraint is that monitoring must operate against **realized outcomes that arrive late**. The label here is a 12-month default flag; by construction, a fully matured outcome for a loan scored today is not observable for a year. The monitoring program therefore runs on two clocks. Leading indicators — population stability index (PSI), score-distribution shape, input feature drift, and approval rate — are computable immediately from scoring traffic and require no labels. Lagging indicators — AUC, the Brier score, calibration curves, and the fairness outcome metrics — are computed against partially and fully matured cohorts as labels arrive, using both early-performance proxies (e.g., 3- and 6-month delinquency roll rates) and the eventual 12-month label. We never wait a full year to react; we react on the leading indicators and confirm with the lagging ones.

### 20.2 Performance monitoring: discrimination and calibration

**Discrimination.** The primary discrimination metric is the area under the ROC curve (AUC) computed on each maturing production cohort. Because labels mature gradually, AUC is reported in three views: (a) a *vintage* view, where each monthly origination cohort is tracked as its label window matures, giving an unbiased but lagging read; (b) a *trailing matured* view over the most recent fully-matured 12-month window, which is the view used to evaluate the `auc_floor` trigger; and (c) an *early-proxy* view using 90-day delinquency as a surrogate label, which provides an advance warning weeks before the matured AUC can confirm a problem. The early-proxy AUC is explicitly advisory — it cannot by itself fire `auc_floor`, but a sustained early-proxy decline escalates triage priority and prompts MRM to pull the matured cohort forward for manual review. Confidence intervals on AUC are produced by stratified bootstrap (2,000 resamples) so that the on-call engineer can distinguish a genuine decline from sampling noise on a thin cohort.

**Calibration.** Calibration is monitored because the PD score feeds provisioning and pricing, and a miscalibrated-but-well-ranked model passes a naive AUC check while quietly mispricing risk. We track:

- The **Brier score** and its decomposition (reliability, resolution, uncertainty) on each matured cohort.
- A **reliability diagram** binned into deciles of predicted PD, plotting mean predicted PD against realized default rate per bin, with the 45-degree identity line overlaid.
- The **expected calibration error (ECE)** and **maximum calibration error (MCE)** as scalar summaries for dashboarding and trend lines.
- A **calibration-in-the-large** check (mean predicted PD versus overall realized default rate) to detect uniform over- or under-prediction.

Calibration degradation does not itself map to a binding rollback trigger; instead, a material and sustained calibration break is an MRM-reviewable finding that can trigger a re-fit, recalibration (e.g., refreshing an isotonic or Platt calibration layer), or, at MRM's discretion, a discretionary rollback under the authority described in §20.7. The reason calibration is not auto-wired to a numeric trigger is that calibration is routinely repairable without a full model change, and a recalibration is a less disruptive remediation than a rollback.

### 20.3 Population Stability Index methodology

The population stability index (PSI) is the workhorse drift metric and the basis of the `drift_psi` trigger. PSI quantifies how far a *current* distribution has moved from a *reference* (expected) distribution. We compute PSI in two distinct families:

**Score PSI.** This is the headline drift metric and the one wired to the `drift_psi` trigger. It is computed on the distribution of the model's output PD score.

**Feature PSI / Characteristic Stability Index.** Computed per input feature to localize *why* the score distribution moved. Feature PSI is diagnostic, not directly trigger-wired, but it is essential for triage: a score-PSI breach with a clear concentration in one or two feature PSIs points the investigator straight at the cause (e.g., a changed upstream bureau feed, a new acquisition channel, a seasonal mix shift).

#### How score PSI is computed across score bins

The procedure is fixed so that the number is reproducible and auditable:

1. **Establish the reference distribution.** At promotion time, the validation-cohort score distribution is frozen as the PSI reference and stored as an artifact alongside the registered model version. The reference is versioned with the model: a rollback to a prior champion version also restores that version's reference distribution, so PSI is always measured against the baseline the running model was actually validated on.

2. **Define bins.** The score range [0, 1] is partitioned into 10 bins by the *deciles of the reference distribution* (quantile binning), not by equal-width cuts. Quantile binning ensures each reference bin carries roughly 10% of mass, which stabilizes the index against the heavy concentration of PD scores at the low end. Bin edges are frozen with the reference. Empty or near-empty current bins are floored with a small epsilon (we use 0.0001 of total mass) before taking logs, so that a zero count cannot send PSI to infinity.

3. **Compute per-bin proportions.** For each bin *i*, let `expected_i` be the reference proportion (≈ 0.10 by construction) and `actual_i` be the proportion of current scoring traffic falling in that bin's edges.

4. **Apply the PSI formula.** PSI = Σ over bins of `(actual_i − expected_i) × ln(actual_i / expected_i)`. Each term is non-negative, so PSI is non-negative and increases monotonically with divergence between the two distributions; it is, up to the binning, a symmetrized discrete relative-entropy measure.

5. **Window and aggregate.** Score PSI is computed daily on the trailing rolling window of scoring traffic and reported as a daily value plus a 7-day smoothed trend. A single noisy day does not fire the trigger; the trigger logic (see §20.6) requires sustained breach, consistent with the threshold semantics defined in §13.

The conventional industry reading of PSI bands — below 0.10 negligible shift, 0.10 to 0.25 moderate shift warranting investigation, above 0.25 significant shift — is provided to monitoring staff as *interpretive context only*. The binding boundary for `drift_psi` lives in §13 and may differ from these conventional bands; staff must evaluate against §13, not against the textbook bands.

### 20.4 Fairness monitoring in production

Fairness is not certified once at promotion and forgotten. The protected attributes in scope are `age_group`, `gender`, and `region`, as defined in §6. The feature `region_risk_index` remains a prohibited proxy and must not appear as a model input in production; the monitoring pipeline includes a static assertion that the served feature vector schema does not contain `region_risk_index` and raises a hard alert if it ever does, because reintroduction of a prohibited proxy is a governance violation independent of any statistical metric.

The primary production fairness metric is the **demographic-parity difference** — the difference in favorable-outcome (approval) rates across the levels of each protected attribute — tracked continuously on scoring traffic. Because approval is observable immediately while default outcomes are not, demographic-parity difference is a leading fairness indicator and is reported daily per protected attribute. As labels mature, we additionally compute lagging outcome-fairness metrics (group-wise default-rate calibration and group-wise AUC) to confirm that parity in approvals has not produced disparity in realized risk.

Production fairness monitoring is evaluated against the fairness limits in the current binding criteria (§6–§13); the retired ceilings from prior editions are recorded in §20.9 for context only and are not enforced. Where a protected-group parity reading deteriorates without breaching a binding rollback trigger, the finding is escalated to MRM as a fairness watch item, which may prompt a targeted investigation, a fairness re-validation, or a discretionary rollback.

### 20.5 Approval-rate monitoring

The aggregate and segmented approval rate is monitored as both a business-health and a model-behavior signal, and underpins the `approval_rate_floor` trigger. A model that begins denying credit to a materially larger share of applicants than at promotion can be (a) responding correctly to a genuinely riskier applicant pool, (b) miscalibrated after an upstream data change, or (c) drifting in a way that has not yet shown up in PSI. Approval rate is therefore monitored at three granularities: overall portfolio, by acquisition channel, and by region segment, each on a daily cadence with a 7-day smoothed trend. A sharp approval-rate contraction is one of the fastest-moving early-warning signals available because it needs no labels at all, and it is frequently the first symptom an upstream feature outage produces.

### 20.6 The three named rollback triggers

There are exactly three binding rollback triggers. Each is described below by **name and purpose**; each maps to a numeric threshold that is defined authoritatively in **§13** and is deliberately not reproduced here.

- **`auc_floor`** — Guards discrimination. Purpose: ensure the promoted model continues to rank-order default risk at least as well as the minimum acceptable level the governance committee approved. It is evaluated on the trailing matured-cohort AUC view (§20.2). When matured AUC falls and stays below the floor defined in §13, the trigger fires. The early-proxy AUC view escalates triage but does not itself fire the trigger.

- **`drift_psi`** — Guards population stability. Purpose: detect that the production population has moved far enough from the validation reference that the model's approved performance can no longer be assumed to hold. It is evaluated on the score PSI computed per §20.3 against the boundary in §13, on a sustained (not single-day) basis.

- **`approval_rate_floor`** — Guards approval behavior and downstream conduct/safety-and-soundness exposure. Purpose: detect a material contraction in the rate at which credit is approved, which can indicate miscalibration, upstream data failure, or unmodeled population shift. It is evaluated on the smoothed approval-rate trend against the floor in §13.

Trigger evaluation is implemented in the monitoring service as pure functions that read the current metric and the §13 threshold from a single governance-controlled configuration object; the threshold values are sourced from that one configuration so there is no second copy to drift. A trigger fires only on **sustained** breach over the confirmation window specified for that metric, to suppress single-sample noise, and each firing is recorded with the metric value, the window, the threshold reference, and the model version in effect at the time.

### 20.7 Monitored-metrics table

The threshold column intentionally reads "see §13" for every trigger-bound metric; the binding numbers are not duplicated in this runbook.

| Metric | Surface | Owner | Cadence | Mapped trigger | Threshold |
|---|---|---|---|---|---|
| Trailing matured AUC | Discrimination | Model Monitoring Eng. | Monthly (on cohort maturation) | `auc_floor` | see §13 |
| Early-proxy AUC (90-day delinquency surrogate) | Discrimination (advisory) | Model Monitoring Eng. | Weekly | escalates triage for `auc_floor` | see §13 |
| Score PSI | Population stability | Model Monitoring Eng. | Daily + 7-day trend | `drift_psi` | see §13 |
| Feature PSI / CSI (per input) | Drift localization (diagnostic) | Data Platform | Daily | none (diagnostic) | interpretive bands only |
| Overall approval rate | Approval behavior | LOB Owner | Daily + 7-day trend | `approval_rate_floor` | see §13 |
| Segmented approval rate (channel, region) | Approval behavior | LOB Owner | Daily | informs `approval_rate_floor` triage | see §13 |
| Demographic-parity difference (per protected attr) | Fairness (leading) | MRM Fairness Reviewer | Daily | none (MRM watch item) | per §6–§13 |
| Group-wise matured AUC & calibration | Fairness (lagging) | MRM Fairness Reviewer | Monthly | none (MRM watch item) | per §6–§13 |
| Brier score / ECE / MCE | Calibration | Model Monitoring Eng. | Monthly | none (MRM-reviewable) | reviewable |
| Reliability diagram (decile bins) | Calibration | Model Monitoring Eng. | Monthly | none (MRM-reviewable) | reviewable |
| `region_risk_index` absence assertion | Proxy-control | Data Platform | Per deploy + daily | hard governance alert | prohibited |
| Scoring-volume / null-rate / feature-availability | Pipeline health | Data Platform | Real-time | operational alert | runbook |

### 20.8 The rollback runbook

This is the operational procedure executed when a rollback trigger fires or when MRM exercises discretionary authority. It is written to be followed under pressure by the on-call engineer.

#### Step 1 — Detection

A trigger fires when the monitoring service confirms a sustained breach over the confirmation window for `auc_floor`, `drift_psi`, or `approval_rate_floor`, evaluated against §13. Detection is automated; the service emits a structured trigger event containing the trigger name, the observed metric value and window, the §13 threshold reference, the currently-served model version and its registry alias, and a link to the diagnostic dashboard snapshot. Detection of the `region_risk_index` proxy assertion or a catastrophic pipeline-health failure also enters this runbook as an immediate hard alert.

#### Step 2 — Alert

The trigger event is dispatched simultaneously to the on-call model-monitoring engineer (primary page, via the incident pager), the MRM duty reviewer, and the line-of-business owner (notification, non-paging). The alert opens an incident ticket automatically, pre-populated with the trigger event payload, and starts the incident clock. Acknowledgement by the on-call engineer is required within the page SLA; failure to acknowledge escalates to the secondary on-call and then to the MRM manager.

#### Step 3 — Triage

The on-call engineer performs first-line triage against a fixed checklist, with the goal of distinguishing a genuine model-quality event from a data or pipeline artifact:

1. **Confirm the breach is real, not a telemetry artifact.** Check scoring volume, feature null-rates, and feature-availability for the breach window. A `drift_psi` or `approval_rate_floor` breach that coincides with an upstream feed outage or a null-rate spike is treated first as a data incident — the fix may be to restore the feed and re-evaluate, not to roll back the model.
2. **Localize.** For `drift_psi`, inspect feature PSI to find the contributing features. For `approval_rate_floor`, inspect segmented approval rate to find whether the contraction is portfolio-wide or concentrated in a channel/region. For `auc_floor`, confirm against the matured cohort and check whether early-proxy AUC corroborates.
3. **Check fairness coupling.** Pull the demographic-parity-difference panel for the breach window. A performance or approval breach that is concentrated in a protected group raises the incident severity and routes MRM into the decision path immediately.
4. **Classify.** Conclude triage with one of: *data/pipeline incident* (route to Data Platform, model stays), *transient/false* (continue heightened monitoring, no action), or *confirmed model-quality breach* (proceed to Step 4).

Triage has a hard time box. If the engineer cannot positively classify the event within the triage window, the default action is to escalate to the decision authority and prepare for rollback — the conservative-promotion posture means the system biases toward reverting to known-good rather than running unverified in production.

#### Step 4 — Decision authority

The authority to execute a production rollback is held as follows. A confirmed breach of any of the three binding triggers (`auc_floor`, `drift_psi`, `approval_rate_floor`) authorizes the on-call model-monitoring engineer to execute the alias rollback **immediately** without waiting for committee convening, because these thresholds were pre-approved by the governance committee in §13 — firing the trigger *is* the approval to roll back. The MRM duty reviewer is informed and may halt the rollback only to substitute a more conservative action (there is no authority to keep a confirmed-breached model serving). For **discretionary** rollbacks (calibration breaks, fairness watch items, suspected-but-unconfirmed degradation that does not meet a binding trigger), the decision authority is the MRM duty reviewer in consultation with the LOB owner; the on-call engineer executes on their instruction. All decisions, automatic or discretionary, are recorded in the incident ticket with the deciding authority named.

#### Step 5 — Executing the alias rollback in the registry

Rollback is performed entirely through the MLflow registry alias mechanism. The production champion is identified by a registry **alias**, not by a hard-coded version number; promotion and rollback are alias moves. This is what makes rollback fast, atomic, and auditable. The procedure:

1. **Identify the prior champion version.** The registry retains the immediately-preceding champion version. The incident ticket and the registry's alias history record which version held the champion alias before the current one; the rollback target is that prior version. Under no circumstances is rollback a re-train — it is a reversion to an already-validated, already-promoted artifact.
2. **Re-point the alias.** Move the production champion alias from the breached version back to the prior champion version. Because serving resolves the model by alias at load/refresh time, re-pointing the alias is the single authoritative action that takes the prior version live. No code deploy is required.
3. **Restore the matching PSI reference and calibration artifacts.** The prior version's frozen reference distribution and calibration layer are restored as the active monitoring baselines (they are stored with the version), so that post-rollback PSI and calibration are measured against the correct baseline for the model now serving.
4. **Confirm serving cutover.** Verify that scoring traffic is being served by the rolled-back version: confirm the served model version reported in scoring logs matches the prior champion version, and that scoring volume and latency are nominal.
5. **Quarantine the breached version.** Tag the breached version in the registry with an incident reference and a status that prevents it from being re-aliased to champion without explicit MRM sign-off. It is not deleted — it is preserved for the post-incident review and for any model-risk audit.
6. **Snapshot evidence.** Capture the alias-history record, the trigger event payload, and the dashboard state at rollback time as immutable incident artifacts.

The target time from confirmed-breach decision to completed alias cutover is short by design; because rollback is an alias move rather than a deploy, the limiting factor is human decision time in Steps 3–4, not mechanical execution in Step 5.

#### Step 6 — Post-incident review

Within five business days of a rollback, MRM convenes a post-incident review. The review establishes the root cause; confirms whether the trigger fired correctly (true positive), prematurely (false positive needing threshold or window re-tuning), or late (a near-miss indicating the threshold or leading-indicator coverage is inadequate); documents the customer and portfolio impact over the breach window; and assigns remediation owners and dates. A rollback does not close the underlying issue — the breached model remains quarantined and the review produces a remediation plan (re-fit, recalibration, feature-pipeline fix, or retirement) that must complete and re-clear the §6–§13 promotion gates before any candidate can be promoted to champion again. The review output is a standing input to the next edition revision of this dossier; recurring trigger behavior is precisely the evidence used to re-examine whether the §13 thresholds remain appropriate.

### 20.9 Alerting, dashboards, and reporting cadence

**Alerting tiers.** Alerts are tiered to prevent fatigue. *Tier 1 (page)* is reserved for confirmed binding-trigger breaches, the `region_risk_index` proxy assertion, and catastrophic pipeline failure. *Tier 2 (notify)* covers MRM watch items: calibration breaks, fairness parity deterioration short of a trigger, and approaching-threshold warnings (e.g., score PSI entering the moderate-shift interpretive band). *Tier 3 (digest)* covers routine trend movement and is rolled into the periodic report rather than dispatched in real time. Every Tier 1 and Tier 2 alert carries the trigger/metric name, the observed value, the §13 reference, the model version in effect, and a deep link to the relevant dashboard panel.

**Dashboards.** A single monitoring dashboard is the canonical operational view, organized into the four surfaces of §20.1: a discrimination panel (vintage, trailing-matured, and early-proxy AUC with bootstrap CIs), a stability panel (score PSI daily and 7-day trend, plus a feature-PSI heat map for localization), a fairness panel (per-attribute demographic-parity-difference time series with lagging group-wise outcome metrics), and an approval panel (overall and segmented approval rate). Each trigger-bound panel renders the §13 boundary as a reference line pulled from the same governance configuration the trigger logic reads, so the dashboard and the trigger can never disagree.

**Reporting cadence.** A weekly monitoring digest goes to the LOB owner and MRM summarizing all four surfaces, open watch items, and any Tier 1/Tier 2 events. A monthly model-performance report — produced as matured cohorts roll in — provides the formal AUC, calibration, and outcome-fairness read and is the artifact of record for ongoing model validation. A quarterly MRM review consolidates the monthly reports, the incident history, and any near-misses, and is the forum in which discretionary remediations and any proposed threshold changes are deliberated. The annual edition revision of this dossier draws on the full year of monthly and quarterly evidence.

### 20.10 Ongoing monitoring under SR 11-7

This program implements the ongoing-monitoring expectation of supervisory guidance SR 11-7. SR 11-7 holds that model risk is managed across the full lifecycle and that ongoing monitoring is "essential to evaluate whether changes in products, exposures, activities, clients, or market conditions necessitate adjustment, redevelopment, or replacement of the model, and to verify that any extension of the model beyond its original scope is valid." The mapping to this runbook is direct:

- **Verifying the model is performing as intended.** The discrimination and calibration monitoring of §20.2, evaluated on maturing cohorts, is the direct evidence that the model continues to perform as it did when validated and approved.
- **Detecting changes in population and conditions.** The PSI methodology of §20.3 and the approval-rate monitoring of §20.5 are the leading-indicator machinery for detecting exactly the "changes in products, exposures, activities, clients, or market conditions" SR 11-7 names.
- **Sensitivity to the limits of the model's design.** The frozen, version-matched PSI reference encodes the population on which the model was validated; a PSI breach is the explicit signal that the model is being used outside the conditions it was approved for.
- **Conservative response and effective challenge.** The pre-approved, automatic rollback authority of §20.8 operationalizes the conservative-promotion posture: confirmed degradation reverts to a known-good prior champion rather than continuing to serve, and the post-incident review supplies the documented effective challenge SR 11-7 expects.
- **Documentation and audit.** Every trigger event, decision, alias move, and review is captured as immutable incident evidence, satisfying the documentation and auditability expectations of the guidance and supporting independent review by Internal Audit.

The independence principle is preserved: the model-monitoring engineering function operates the pipeline and executes mechanical rollbacks, but MRM — independent of model development and of the line of business — owns trigger and threshold governance, fairness adjudication, and the post-incident review.

### 20.11 Retired thresholds (context, not enforced)

For historical traceability only, and explicitly **not enforced**, prior editions set different bars. Edition 1 (2023) registered the model as `meridian_risk_model_v1` with artifact path `model`, validated on an 80/10/10 split (seed 7), and held an accuracy bar of 0.80, an AUC bar of 0.82, and a regional fairness ceiling of 0.20. Edition 2 (2024) used a 70/15/15 split (seed 13), an accuracy bar of 0.80, an AUC bar of 0.81, a macro-F1 bar of 0.75, and a gender fairness ceiling of 0.06. These values are recorded so that a reviewer reading historical monitoring telemetry understands which baseline a given vintage was measured against. The current binding bars and ceilings are those in §6–§13; the current rollback boundaries are those in §13. Where this section needs a comparison point, it uses the named triggers and points to §13.

### 20.12 Illustrative incident write-ups (example telemetry)

The following two write-ups use **clearly-labeled illustrative telemetry** to show the runbook in motion. The numbers below are example observations of production behavior, not threshold definitions; thresholds remain in §13.

#### Illustrative incident A — `drift_psi` from an upstream channel shift

*Example telemetry.* Beginning around week 8 of a monitoring quarter, the stability panel showed score PSI rising off its usual low baseline. In week 9 the 7-day-smoothed score PSI was observed at 0.31, having climbed from a typical reading near 0.04 over the preceding two weeks; this sustained reading breached the `drift_psi` boundary defined in §13 and fired the trigger. Triage (Step 3) confirmed scoring volume and null-rates were nominal — not a pipeline artifact — and the feature-PSI heat map localized the movement to two acquisition-channel and income-band features. Segmented approval rate showed the shift concentrated in a newly-onboarded partner channel whose applicant mix differed materially from the validation population. The demographic-parity panel showed no protected-group concentration, so severity stayed at standard. The on-call engineer, holding pre-approved authority for a confirmed binding-trigger breach, executed the alias rollback (Step 5): the champion alias was re-pointed to the prior champion version, that version's frozen PSI reference was restored, serving cutover was confirmed against scoring logs, and the breached version was quarantined. The post-incident review (Step 6) found a true-positive trigger and a genuine population shift; remediation was to develop and re-validate a candidate against the new channel's population and re-clear the §6–§13 gates before any re-promotion. The example illustrates the core point: PSI led, performance had not yet visibly degraded, and the conservative reversion prevented serving into an unvalidated population.

#### Illustrative incident B — `approval_rate_floor` from a silent feature-feed degradation

*Example telemetry.* On an example Tuesday, the approval panel showed the overall 7-day-smoothed approval rate contracting sharply over 36 hours, and the smoothed trend crossed below the `approval_rate_floor` boundary defined in §13, firing the trigger. First-line triage (Step 3) immediately checked pipeline health and found that a bureau-sourced feature had begun returning nulls for a subset of applicants, which the scoring path was imputing conservatively and thereby depressing approvals. This was classified as a *data/pipeline incident*, not a model-quality breach: the correct first action under the runbook was to route to Data Platform to restore the feed rather than to roll back the model. Heightened monitoring was held in place; once the feed was restored, the approval-rate trend recovered above the §13 boundary within the confirmation window and the incident was closed without a model rollback. The post-incident review nonetheless produced two remediations — a feature-availability alert wired to fire *before* approval rate moves (so the data incident is caught upstream of the model symptom), and a review of the conservative imputation behavior. This example illustrates why Step 3 triage is mandatory before Step 5: the same approval-rate symptom can arise from a data fault or a model fault, and rolling back the model would not have fixed a broken feed. It also illustrates that not every trigger firing ends in a rollback — the runbook's job is to reach the correct conservative action, which is sometimes a data fix and sometimes a reversion.

Together these write-ups capture the operating doctrine of this section: lead with population and approval signals, confirm with maturing performance and calibration, triage before reverting, and when a binding trigger is genuinely breached, fall back to a known-good prior champion through a clean alias move — never debate a degraded model in place.
