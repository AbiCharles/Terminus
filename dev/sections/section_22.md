## §22 Internal Audit (Third Line) Findings and Remediation Log

### §22.1 Purpose and Scope of this Section

This section consolidates the multi-year record of Internal Audit (IA) findings, management responses, and remediation tracking that pertain directly to the governance of the consumer-credit 12-month probability-of-default (PD) classifier and its promotion into the production model registry. It is maintained as a living workpaper extract under the third line of defense and is reproduced in the dossier so that examiners, the Model Risk Management Committee (MRMC), and external supervisory reviewers can trace how the program matured across Editions 1 through 3 of this dossier (2023, 2024, and the current 2026 edition).

The findings catalogued here are deliberately not a restatement of the binding promotion criteria. The authoritative, currently-enforced gate thresholds, fairness ceilings, reproducibility parameters, and registry alias controls live in §6 through §13 and are referenced by pointer throughout. Where this section cites numeric values, those values are historical artifacts of superseded editions and are presented solely as audit evidence of the trajectory of remediation. Readers seeking the controls in force on the publication date of this edition must consult §6–§13 directly; nothing in §22 should be read as authority for any current limit.

### §22.2 Role and Independence of the Third Line

Internal Audit operates as the third line of defense within Meridian Financial's three-lines model. The first line comprises the model development and model-owning business units within Consumer Credit; the second line is Model Risk Management, which owns independent validation, the model inventory, and the challenge function. IA provides independent, objective assurance over the design and operating effectiveness of both the first-line control environment and the second-line oversight function. Critically, IA does not own, build, validate, calibrate, or approve the PD classifier, and IA personnel are excluded from any promotion decision. This exclusion is structural: IA's reporting line runs to the Audit Committee of the Board, not to the Chief Risk Officer who oversees MRM, preserving organizational independence from the functions IA assesses.

IA's mandate over the model program is reaffirmed annually in the audit charter approved by the Audit Committee. The mandate covers (a) governance and policy adequacy, (b) the effectiveness of second-line validation challenge, (c) the integrity of the model inventory and registry controls, (d) data lineage and sourcing controls feeding the model, (e) fairness and disparate-impact monitoring, and (f) the operability of contingency controls such as rollback. IA does not opine on whether a given model is fit for purpose — that is a second-line validation judgment — but it does opine on whether the process that produced and promoted the model was designed and operating as the governance framework requires.

A standing independence safeguard worth recording: IA staff who previously rotated out of first-line modeling roles are subject to a cooling-off period before they may audit work they could have influenced. One independence exception was logged and remediated (see Finding IA-2024-07) when a contractor with prior first-line exposure was provisionally assigned to a fairness review; the assignment was reversed and the relevant testing re-performed by an unconflicted auditor.

### §22.3 Audit Methodology

Model-risk audits are conducted on a risk-based cycle. The PD classifier is rated a high-inherent-risk model given its direct influence on consumer credit decisioning and its exposure to fair-lending risk through protected attributes (age_group, gender, region) and the prohibited proxy region_risk_index. High-inherent-risk models receive a full-scope audit no less than every eighteen months, with targeted interim reviews triggered by material changes — for example, a new edition of this governance dossier, a registry platform migration, or a validation finding escalated by the second line.

The methodology follows a consistent arc across engagements:

- **Planning and risk assessment.** IA confirms the model's inventory record, inherent-risk rating, and the population of controls in scope. The engagement scope memo is shared with the auditee and the second line, but testing samples are not pre-disclosed.
- **Design assessment.** IA evaluates whether the governing controls described in §6–§13 are designed to address the risks the framework intends to mitigate. Design gaps are findings even where no control failure has yet occurred.
- **Operating-effectiveness testing.** IA re-performs or inspects evidence for a sample of promotion events, fairness evaluations, reproducibility runs, and approval workflows. Where feasible, IA independently re-executes a registered training run from the recorded parameters and seed to confirm the recorded metrics are reproducible.
- **Reporting and rating.** Findings are rated High, Medium, or Low based on a combination of likelihood and impact, with fair-lending and safety-and-soundness exposures weighted upward. Each finding carries an agreed management action, an accountable owner, and a committed remediation date.
- **Validation of closure.** No finding is closed on management's assertion alone. IA independently validates remediation evidence before moving a finding to Closed status. Closure validation is itself sampled by the Audit Committee's external co-source partner on a rotating basis.

Severity definitions used throughout this log:

| Severity | Definition |
|---|---|
| High | A control deficiency that could permit promotion of a non-compliant model, a fair-lending breach, or an unrecoverable production incident; or a systemic governance gap. Board-level reportable. |
| Medium | A deficiency that weakens a key control but is compensated by other controls, or that creates material inefficiency or evidentiary gaps without immediate prudential exposure. |
| Low | A localized or documentation-level deficiency with limited risk, typically remediable within one cycle. |

### §22.4 Findings Detail (2023–2026)

The findings below are presented chronologically. Each entry records the observation, the risk it creates, management's response, the remediation actions taken or committed, the accountable owner, and current status as of this edition's publication date.

---

#### IA-2023-01 — Inadequate documentation of proxy-variable analysis
**Date raised:** 2023-04-18 · **Severity:** High · **Status:** Closed (2023-11-30)

**Observation.** During the inaugural audit of the model program under Edition 1 of the governance dossier, IA found that the prohibition on the proxy variable region_risk_index was asserted in policy but not evidenced in practice. The first line maintained no documented proxy-screening analysis demonstrating that region_risk_index — or any near-collinear surrogate — had been tested for and excluded from the feature set. The model then in production, registered under the name meridian_risk_model_v1 with artifact path `model`, carried no workpaper showing how proxy exclusion was verified.

**Risk.** Absent documented proxy screening, a prohibited proxy could enter the feature pipeline undetected, producing disparate impact on the protected region attribute while appearing compliant on its face. This is a direct fair-lending exposure and a safety-and-soundness concern.

**Management response.** Model owners accepted the finding without exception. They acknowledged that proxy exclusion had been performed informally during development but never memorialized.

**Remediation.** A standing proxy-screening workpaper was instituted, requiring correlation and mutual-information testing of every candidate feature against region and region_risk_index prior to feature freeze, with second-line review. The screening procedure was subsequently codified into the binding control set; the current obligation and its acceptance criteria are specified in §9 (refer there for the governing requirement).

**Owner.** Head of Consumer Credit Modeling. **Closure basis.** IA inspected three subsequent development cycles and confirmed the workpaper was produced and independently reviewed in each.

---

#### IA-2023-02 — Weak reproducibility and seeding discipline
**Date raised:** 2023-05-09 · **Severity:** High · **Status:** Closed (2024-02-15)

**Observation.** Under Edition 1, the recorded train/validation/test split was 80/10/10 using random seed 7. IA attempted to re-execute a registered training run from the logged parameters and could not reproduce the recorded accuracy of 0.80 or AUC of 0.82 within tolerance. Investigation showed the data-loading step applied a non-deterministic shuffle that was not governed by the recorded seed, so the 80/10/10 partition was not actually fixed by seed 7 as the run metadata implied.

**Risk.** Non-reproducible training undermines the entire validation and promotion chain: recorded metrics cannot be independently verified, model comparisons are unsound, and an examiner cannot reconstruct the model that was promoted. This also defeats meaningful champion-challenger comparison.

**Management response.** Accepted. The first line confirmed the shuffle defect and that several historical runs were therefore not bit-reproducible.

**Remediation.** All stochastic operations were brought under a single recorded seed, and a reproducibility self-test was added to the training pipeline that re-runs the partition and asserts identity before metrics are logged. The split convention itself was later revised in Edition 2 to 70/15/15 under seed 13, and has since been superseded again; the reproducibility parameters now in force are specified in §8 and must be read there rather than inferred from this finding.

**Owner.** Lead ML Engineer, Consumer Credit. **Closure basis.** IA independently re-executed two runs post-remediation and reproduced logged metrics to the bit.

---

#### IA-2023-03 — Model inventory and registry metadata incomplete
**Date raised:** 2023-09-22 · **Severity:** Medium · **Status:** Closed (2024-01-31)

**Observation.** The registry record for meridian_risk_model_v1 used the artifact path `model` and lacked structured metadata linking the registered version to its originating training run, dataset snapshot, and validation report. IA could not, from the registry alone, establish a complete lineage from a promoted version back to the data and code that produced it.

**Risk.** Incomplete registry metadata impairs auditability, complicates incident response, and weakens the ability to demonstrate which exact artifact is serving production traffic.

**Management response.** Accepted with a partial compensating-control note: lineage existed in scattered systems but was not consolidated at the registry.

**Remediation.** Registry entries were standardized to require run ID, dataset snapshot identifier, validation report reference, and approver identity as mandatory tags. The current registry metadata and naming controls are set out in §11.

**Owner.** Model Inventory Owner (Second Line). **Closure basis.** IA sampled five new registrations and confirmed mandatory tags were populated and resolvable.

---

#### IA-2024-04 — Fairness monitoring limited to a single protected attribute
**Date raised:** 2024-03-14 · **Severity:** High · **Status:** Closed (2024-09-30)

**Observation.** Edition 2 introduced an explicit gender disparity ceiling of 0.06 on the demographic-parity-difference metric. IA found, however, that production fairness monitoring computed the disparity statistic only for gender. The other protected attributes — age_group and region — were named in policy but not instrumented in the monitoring job, so drift in their disparity profiles would not have been detected between validation cycles.

**Risk.** Disparate impact could accumulate undetected on age_group or region in production even while gender remained within its ceiling. This is a material fair-lending monitoring gap.

**Management response.** Accepted. The second line acknowledged the monitoring job had been built incrementally and had not kept pace with the policy's protected-attribute scope.

**Remediation.** The fairness monitor was extended to compute demographic-parity-difference across all three protected attributes on the production scoring population, with alerting on threshold breach. The current monitoring obligations and the governing ceilings — which differ from the superseded 0.06 gender figure — are defined in §10 and §12; this finding should not be read as endorsing any specific current limit.

**Owner.** Head of Model Monitoring (Second Line). **Closure basis.** IA inspected three monthly monitoring cycles covering all protected attributes and confirmed alerting fired correctly in a controlled test.

---

#### IA-2024-05 — Demographic-parity metric computed on stale reference population
**Date raised:** 2024-04-02 · **Severity:** Medium · **Status:** Closed (2024-08-20)

**Observation.** Even where the gender disparity statistic was computed, IA found it was benchmarked against a reference population snapshot that had not been refreshed since the Edition 1 development window. The demographic-parity-difference was therefore measured against an outdated base rate that no longer reflected the booked portfolio.

**Risk.** A stale reference can mask or exaggerate disparity, producing false comfort or false alarms and undermining confidence in the fairness control even when the metric itself is correctly implemented.

**Management response.** Accepted.

**Remediation.** The reference-population refresh cadence was formalized and tied to the validation cycle, with the snapshot identifier recorded alongside each fairness result. The governing cadence is referenced in §10.

**Owner.** Head of Model Monitoring (Second Line). **Closure basis.** IA confirmed the refreshed reference and verified snapshot identifiers were logged with results.

---

#### IA-2024-06 — Separation-of-duties exception in promotion approval
**Date raised:** 2024-06-11 · **Severity:** High · **Status:** Closed (2025-03-31)

**Observation.** IA identified two promotion events in which the same individual functioned as both the model developer and the approving authority recording the promotion. The first line and second line approval roles had collapsed onto a single person during a period of staffing constraint, defeating the four-eyes principle that the conservative-promotion posture depends upon.

**Risk.** A single actor able to both build and promote a model can bypass independent challenge, intentionally or otherwise, and can promote a model that has not cleared independent validation.

**Management response.** Accepted as a High-severity control breach. Management initiated a look-back over all promotions in the affected period.

**Remediation.** Promotion approval was reconfigured so that the developer, the validating reviewer, and the promotion approver must be three distinct, role-segregated identities, enforced technically at the registry rather than by procedure alone. The look-back identified no improperly promoted model, but the control gap itself warranted the High rating. The current separation-of-duties and approval-authority controls are specified in §13.

**Owner.** Chief Risk Officer's delegate for model governance. **Closure basis.** IA tested the enforced segregation against an attempted same-actor promotion in a non-production environment and confirmed the action was blocked.

---

#### IA-2024-07 — Auditor independence exception (self-identified)
**Date raised:** 2024-07-19 · **Severity:** Low · **Status:** Closed (2024-08-05)

**Observation.** IA self-reported that a co-source contractor with prior first-line modeling exposure had been provisionally assigned to a fairness-monitoring review without completing the required cooling-off period. No testing conclusions had yet been finalized.

**Risk.** Audit conclusions over work an auditor could previously have influenced are not independent and cannot be relied upon for assurance.

**Management response.** IA leadership accepted and acted immediately.

**Remediation.** The assignment was reversed; an unconflicted auditor re-performed all in-scope testing; and the engagement-staffing checklist was updated to require an explicit cooling-off attestation before assignment. Recorded here for transparency and completeness of the independence record.

**Owner.** Chief Audit Executive. **Closure basis.** Re-performed testing reviewed; staffing control updated and confirmed in subsequent engagements.

---

#### IA-2025-08 — Stage-based promotion control structurally weak (motivated Edition 3)
**Date raised:** 2025-02-27 · **Severity:** High · **Status:** Closed (2025-12-15)

**Observation.** IA found that production designation of the live model relied on the registry's mutable lifecycle *stage* field (e.g., transitioning a version to a "Production" stage). Stage transitions could be effected by any actor with registry write access and were not bound to the approval workflow, were reversible without an audit trail of equivalent rigor, and could be applied to more than one version in ambiguous ways. The control intended to guarantee that exactly one validated, approved version served production traffic was therefore structurally weak: the binding designation of the production model was a free-floating stage label rather than a governed, single-valued pointer.

**Risk.** This is the central control weakness that the third line escalated to the MRMC. Under a stage-based scheme, a model could be designated production without traversing the approval and validation gates, the production-serving version could be changed without a durable, attributable record, and incident reconstruction would be unreliable. The exposure spans fair-lending, safety-and-soundness, and auditability simultaneously.

**Management response.** Accepted as High and escalated. Management agreed the stage construct could not bear the governance weight placed on it and committed to a redesign — the work that ultimately produced Edition 3 of this dossier.

**Remediation.** The production designation was migrated from mutable lifecycle stages to a single governed registry **alias** that points to exactly one approved version, bound to the segregated approval workflow and to an immutable promotion record. Movement of the alias is the promotion event and is itself the controlled, attributable action. The full current alias-based promotion control — including how the production pointer is set, who may move it, and how the prior version is retained for rollback — is specified in §11 and §13. This finding is the documented origin of that control change; the operative rules are in §6–§13, not here.

**Owner.** Model Inventory Owner (Second Line), with the CRO governance delegate. **Closure basis.** IA verified that stage-based promotion paths were decommissioned, that the alias pointer was single-valued and workflow-bound, and that attempts to move the alias outside the approval workflow were rejected in test.

---

#### IA-2025-09 — Data-lineage gap between sourcing and feature store
**Date raised:** 2025-05-13 · **Severity:** Medium · **Status:** Open (target 2026-09-30)

**Observation.** IA traced a sample of model features from the serving layer back toward source systems and found a lineage break at the boundary between the upstream sourcing layer and the feature store. For two derived features, the transformation logic was documented but the specific source extract and its effective date could not be deterministically identified, because the feature-store ingestion did not persist the source extract identifier.

**Risk.** Without complete source-to-feature lineage, IA cannot fully verify that the data used in training and serving is the governed, approved data, nor can it confirm that a prohibited proxy did not enter through an upstream transformation. The exposure overlaps with the proxy-screening control (IA-2023-01) at the data layer.

**Management response.** Accepted. The first line confirmed the ingestion process discards source extract identifiers and committed to persisting them.

**Remediation (in progress).** A lineage-tagging enhancement is being implemented to carry the source extract identifier and effective date through to the feature store, closing the trace. Interim compensating control: monthly manual reconciliation of the two affected features against source, evidenced to IA. The governing data-lineage control objectives are in §7. **Open** pending engineering delivery and IA validation of end-to-end trace on a fresh extract.

**Owner.** Lead ML Engineer, Consumer Credit. **Status note.** On track; interim reconciliation evidenced for three consecutive months.

---

#### IA-2025-10 — Rollback drill performed late and partially
**Date raised:** 2025-08-08 · **Severity:** Medium · **Status:** Open (target 2026-07-31)

**Observation.** The governance framework requires periodic rollback drills demonstrating that the production alias can be reverted to the immediately prior approved version within the committed recovery window. IA found that the scheduled annual drill was performed roughly four months late and, when performed, exercised only the alias revert itself — it did not validate that downstream consumers re-resolved to the reverted version or that monitoring re-baselined correctly.

**Risk.** An untested or partially-tested rollback path may not function under real incident conditions, extending the window during which a defective or non-compliant model serves production decisions.

**Management response.** Accepted. Management acknowledged the drill scope was too narrow and the cadence had slipped.

**Remediation (in progress).** The drill procedure is being expanded to cover end-to-end re-resolution by downstream consumers and monitoring re-baselining, and the cadence is being moved to a calendar-anchored schedule with automated reminders and Audit Committee visibility on completion. The current rollback and contingency obligations are specified in §13. **Open** pending the next full-scope drill and IA observation.

**Owner.** Head of Model Operations. **Status note.** Procedure redesign drafted; full-scope drill scheduled.

---

#### IA-2026-11 — Edition 3 control adoption not yet evidenced across all live records
**Date raised:** 2026-01-22 · **Severity:** Low · **Status:** Open (target 2026-08-31)

**Observation.** Following publication of Edition 3, IA performed a readiness review of registry records and promotion workpapers and found that, while the alias-based control and refreshed gate criteria in §6–§13 are in force, a small number of legacy registry records still carried vestigial stage labels and superseded metadata tags from the Edition 2 era. These do not govern any current decision, but their presence creates potential for confusion during examination.

**Risk.** Low. Residual superseded metadata could be misread as current authority by a reviewer who does not consult §6–§13. There is no live control failure.

**Management response.** Accepted as a clean-up item.

**Remediation (in progress).** A remediation pass is removing or clearly archiving vestigial stage labels and tagging legacy records as historical. The authoritative current controls remain those in §6–§13. **Open** pending completion of the metadata clean-up and IA spot-check.

**Owner.** Model Inventory Owner (Second Line). **Status note.** Clean-up underway; majority of records already reconciled.

---

#### IA-2026-12 — Challenger-comparison evidence retention inconsistent
**Date raised:** 2026-03-05 · **Severity:** Low · **Status:** Closed (2026-05-20)

**Observation.** IA found that while champion-versus-challenger comparisons were performed at each promotion, the retained evidence package was inconsistent: some comparisons archived the full metric tables and fairness deltas, others retained only a summary. The promotion decision itself was sound in every sampled case, but the evidentiary record varied.

**Risk.** Low. Inconsistent retention weakens reconstructability of the decision rationale but did not affect any promotion outcome.

**Management response.** Accepted.

**Remediation.** A standardized challenger-comparison evidence template was adopted and made a mandatory attachment to the promotion record. The governing comparison and evidence requirements are referenced in §12 and §13.

**Owner.** Head of Model Validation (Second Line). **Closure basis.** IA confirmed the template was attached to the two promotions that occurred after adoption.

---

### §22.5 Consolidated Findings Table

| ID | Date raised | Severity | Title | Status |
|---|---|---|---|---|
| IA-2023-01 | 2023-04-18 | High | Inadequate documentation of proxy-variable analysis | Closed |
| IA-2023-02 | 2023-05-09 | High | Weak reproducibility and seeding discipline | Closed |
| IA-2023-03 | 2023-09-22 | Medium | Model inventory and registry metadata incomplete | Closed |
| IA-2024-04 | 2024-03-14 | High | Fairness monitoring limited to a single protected attribute | Closed |
| IA-2024-05 | 2024-04-02 | Medium | Demographic-parity metric on stale reference population | Closed |
| IA-2024-06 | 2024-06-11 | High | Separation-of-duties exception in promotion approval | Closed |
| IA-2024-07 | 2024-07-19 | Low | Auditor independence exception (self-identified) | Closed |
| IA-2025-08 | 2025-02-27 | High | Stage-based promotion control structurally weak | Closed |
| IA-2025-09 | 2025-05-13 | Medium | Data-lineage gap between sourcing and feature store | Open |
| IA-2025-10 | 2025-08-08 | Medium | Rollback drill performed late and partially | Open |
| IA-2026-11 | 2026-01-22 | Low | Edition 3 control adoption not yet evidenced across all records | Open |
| IA-2026-12 | 2026-03-05 | Low | Challenger-comparison evidence retention inconsistent | Closed |

### §22.6 Remediation-Status Summary

As of this edition's publication date (2026-01-01 baseline, with two findings raised in the current cycle reflected through Q2 2026 for completeness of the record), the portfolio of model-program audit findings stands as follows.

| Severity | Total | Closed | Open | % Closed |
|---|---|---|---|---|
| High | 5 | 5 | 0 | 100% |
| Medium | 4 | 2 | 2 | 50% |
| Low | 3 | 2 | 1 | 67% |
| **All** | **12** | **9** | **3** | **75%** |

**Open-finding aging.** None of the three open findings is past its committed remediation date as of publication. IA-2025-09 (data lineage) and IA-2025-10 (rollback drills) are both Medium and both supported by documented interim compensating controls; IA-2026-11 (vestigial metadata) is Low with no live control exposure. No finding is overdue, and no High-severity finding remains open.

**Trajectory observation.** The severity and subject matter of findings track the maturation of the program in a coherent way. The 2023 findings cluster around foundational hygiene — undocumented proxy screening, non-reproducible training, and thin registry lineage — which is characteristic of an early-stage program operating under Edition 1. The 2024 findings move up the maturity curve into the adequacy of fairness instrumentation and the integrity of segregation-of-duties, reflecting the tightening introduced by Edition 2. The pivotal 2025 finding, IA-2025-08, identified a structural weakness in the stage-based production designation; its escalation and remediation were the direct impetus for the alias-based promotion control and the broader recalibration embodied in Edition 3. The 2026 findings are residual clean-up and evidentiary-consistency items, consistent with a program that has substantially closed its material control gaps and is now operating under the current criteria in §6–§13.

**Standing caveat.** This log is an assurance record, not a controls register. Every numeric value reproduced in §22 belongs to a superseded edition and is retained only as audit evidence of remediation history. The controls in force — the promotion gate thresholds, the protected-attribute fairness ceilings, the reproducibility parameters, the registry naming, and the alias-based production designation — are defined exclusively in §6 through §13, and any decision must be made against those sections rather than against any figure recited here.
