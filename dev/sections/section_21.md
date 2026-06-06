## §21 Historical Case Study Library

This library preserves ten redacted post-decision memos drawn from the Meridian Financial Model Risk Management (MRM) archive, spanning the period 2019 through early 2026. Each entry records a model-promotion decision (or non-promotion) made under the governance regime in force at the time, the metrics observed during validation, the rationale of the Model Risk Committee (MRC) or its delegate, and the durable lesson carried forward into successive editions of this dossier. These cases are retained for training, calibration of reviewer judgment, and institutional memory; they are explicitly **historical**. Where a case quotes a metric, a floor, a ceiling, a split convention, an artifact name, or a promotion mechanism, that value reflects the rule **as it stood on the case date**, not the regime currently binding. The current binding criteria — the AUC and accuracy floors, the demographic-parity ceilings, the canonical split and seed, the approved hyperparameters, the registry name and alias convention, and the rollback triggers — are stated only in §6 through §13, and any reader needing the operative rule must consult those sections. The cases below intentionally include superseded Edition 1 (2023) and Edition 2 (2024) values to illustrate how the standard evolved; do not transplant them into present-day decisions.

A note on the timeline. The earliest cases (2019–2022) predate any formal edition of this dossier and were governed by ad-hoc model-validation memoranda and the bank's general Model Governance Policy. Edition 1 was ratified on 2023-01-01, Edition 2 on 2024-01-01, and the present Edition 3 on 2026-01-01. Several cases sit on edition boundaries and are useful precisely because they show a decision made under one regime being re-examined under its successor.

---

### Case 2019-03 — Geographic Proxy in the First Behavioral Scorecard

**Situation.** In the second quarter of 2019, the Retail Analytics group submitted a gradient-boosted behavioral scorecard intended to replace a legacy logistic application score for the unsecured installment portfolio. The model was developed before formal MRM edition governance and was reviewed under the bank's general Model Governance Policy. The development team had engineered a composite feature derived from ZIP-level aggregates — average charge-off rate, median tenure, and a blended delinquency index — which the team named, internally, a "neighborhood stability score."

**Decision.** Validation rejected the model and returned it to development. The rejection was not on discriminatory power; the model was, by the raw numbers, strong.

| Metric (2019 validation) | Observed | Notes |
|---|---|---|
| Test AUC | 0.847 | Strong rank-ordering |
| Test accuracy | 0.83 | Above legacy by 4 points |
| KS statistic | 0.51 | Best seen to date in the portfolio |

**Rationale.** The validation lead, supported by a Fair Lending Compliance reviewer, determined that the "neighborhood stability score" functioned as a geographic proxy: it was constructed almost entirely from area-level credit performance and correlated strongly with the racial composition of the underlying census tracts. Although the model never ingested a protected attribute directly, the engineered feature reconstructed regional risk in a manner that risked redlining-by-algorithm under ECOA/Reg B. Counsel advised that disparate-impact exposure was material and not defensible by business necessity given that comparable rank-ordering was achievable without the feature.

The development team contested the finding, arguing that the feature contained no individual-level demographic data and was "just credit performance." Compliance's rebuttal, later cited verbatim in Edition 1's drafting notes, was that a feature need not *contain* a protected attribute to *reconstruct* one; the relevant legal question is the effect on protected classes, not the intent or the literal contents of the input. A small remediation study was commissioned: when the team rebuilt the model with the area aggregate removed and replaced by individual-level bureau attributes, test AUC fell only modestly, from 0.847 to 0.829, confirming that the proxy was not necessary for competitive performance and therefore not defensible by business necessity.

**Lesson.** This case is the genesis of Meridian's standing prohibition on geographic-proxy features. The principle — that a model may be disqualified for *how* it achieves its accuracy, not merely *whether* it is accurate — became foundational and is reflected in the present-day prohibition on any area-derived risk aggregate that reconstructs regional risk. The governing rule today lives in §11; readers should not treat the 2019 numbers as any kind of threshold, and the specific feature names used internally in 2019 have no standing today. The case also seeded the practice of requiring feature provenance documentation — a written lineage for every engineered feature, tracing it to its source fields — before validation will accept a candidate, and it established that protected attributes such as `age_group`, `gender`, and `region` are not the only fairness concern: their proxies are equally in scope.

---

### Case 2020-07 — The Higher-Accuracy Challenger That Lost to a Fairer Champion

**Situation.** During the 2020 annual refresh of the consumer-credit PD model, two candidates competed. Candidate A was a deep gradient-boosted ensemble with extensive feature interactions; Candidate B was a more constrained boosted model with monotonic constraints and a reduced feature set scrubbed of borderline proxies. Both targeted the 12-month default horizon.

**Decision.** The MRC selected Candidate B as champion despite Candidate A's superior headline accuracy.

| Candidate | Test AUC | Test accuracy | Region disparity (DPD) |
|---|---|---|---|
| A (ensemble) | 0.861 | 0.84 | 0.17 |
| B (constrained) | 0.842 | 0.81 | 0.07 |

**Rationale.** Under the pre-edition regime the bank applied an informal regional-disparity tolerance of roughly 0.20 demographic-parity difference, which Candidate A technically met. But the committee, advised by Fair Lending, judged the 0.17 regional gap to be uncomfortably close to the tolerance and poorly explained — driven by interaction terms the developers could not interpret. Candidate B's 0.07 gap, achieved with monotonic constraints and an auditable feature set, was preferred. The committee recorded that "a two-point AUC premium does not justify a fairness profile we cannot explain to an examiner."

The committee's deliberation record is unusually detailed and is worth preserving. Three governors initially favored Candidate A on the strength of its AUC, reasoning that a more accurate model would, in expectation, decline fewer creditworthy applicants and approve fewer bad risks, which is itself a consumer benefit. The Fair Lending member countered that an unexplained 0.17 regional disparity could not be communicated to an examiner or defended in a fair-lending exam, and that the interaction terms producing Candidate A's lift were precisely the ones that could not be decomposed into a business-necessity narrative. A tie-break analysis showed that Candidate B, despite the lower AUC, actually produced a *more stable* approval rate across regions over a back-test, because its monotonic constraints prevented the score from lurching on small input changes. That stability argument converted two of the three holdouts.

**Lesson.** This is the canonical Meridian precedent that fairness and explainability can and should outweigh a modest accuracy advantage. The philosophy — conservative promotion where fairness or proxy concerns disqualify a higher-accuracy model — was later codified across all three editions and is the single most-cited case in subsequent reviewer training. The specific 0.20 tolerance cited here was itself superseded: Edition 1 (2023) formalized a regional-disparity ceiling of 0.20 as a written gate, and Edition 2 (2024) reframed the parity control around `gender` at a far tighter 0.06 ceiling, measured as a demographic-parity difference. None of those figures is the current binding ceiling; the operative fairness criteria are in §12.

---

### Case 2021-02 — Data Leakage Discovered During Validation

**Situation.** In early 2021, a challenger PD model arrived at validation with an unusually high reported AUC of 0.91 — far above anything the portfolio had historically supported. The development team was confident and had pre-drafted a promotion announcement.

**Decision.** Validation halted the promotion and returned the model with a finding of target leakage. No promotion occurred.

**Rationale.** The validation analyst, suspicious of the performance jump, traced the feature contributions and found a field labeled `acct_status_curr` that encoded the account's current collections status. Because the modeling window and the performance window had been misaligned during the feature build, the feature carried information from *after* the prediction date — effectively leaking the outcome. When the analyst rebuilt the dataset with a correct point-in-time cutoff and removed the contaminated field, performance collapsed to a realistic level.

| State | AUC | Interpretation |
|---|---|---|
| As submitted (leaked) | 0.91 | Implausible; contaminated |
| After point-in-time fix | 0.79 | Plausible; honest |

The post-mortem identified the mechanical cause precisely. The feature build joined a snapshot table to the label table on account identifier alone, without constraining the snapshot date to precede the performance-observation window. For a subset of accounts the snapshot was captured *after* delinquency had already begun, so `acct_status_curr` was, for those accounts, a near-perfect tell. The contaminated accounts were a minority of the population but carried disproportionate influence on the boosted model's splits. The analyst's remediation — a strict point-in-time join enforcing a snapshot-before-window constraint — is now boilerplate in the feature pipeline, and the misleading 0.91 figure is retained in training material as the archetypal "leakage signature."

**Lesson.** "If it looks too good, it is leaking." This case established Meridian's mandatory point-in-time feature-construction review and the requirement that any candidate exceeding the historical performance envelope by a wide margin trigger an automatic leakage audit before any other validation step proceeds. It also motivated the later standardization of a fixed train/validation/test split and a fixed random seed so that performance is reproducible and comparable across submissions — without a fixed split, a leakage-inflated result could not even be cleanly compared against an honest baseline. The canonical split convention has since changed across editions (Edition 1 used 80/10/10 at seed 7; Edition 2 moved to 70/15/15 at seed 13) and the current split and seed are defined in §7.

---

### Case 2021-11 — Interpretable Benchmark Beats the Complex Model

**Situation.** Late in 2021, Retail Analytics proposed replacing the incumbent scorecard with a neural-network PD model trained on a wide feature set including transaction-sequence embeddings. The pitch emphasized modernization and a richer feature representation.

**Decision.** The MRC declined to promote the neural model and retained the interpretable benchmark.

**Rationale.** Validation ran the neural candidate head-to-head against the bank's standard interpretable benchmark — a regularized logistic model with a curated, governed feature set maintained specifically as a challenger floor.

| Model | Test AUC | Test accuracy | Explainability |
|---|---|---|---|
| Neural (embeddings) | 0.838 | 0.81 | Low — embeddings opaque |
| Interpretable benchmark | 0.831 | 0.81 | High — coefficient-level |

The neural model's edge was within the noise band of the validation set (the bootstrap AUC confidence intervals overlapped substantially), while its adverse-action-reason-code generation was unreliable and its embeddings resisted attribution. The committee concluded that a sub-one-point AUC difference of uncertain statistical significance did not justify abandoning a model that produced defensible, regulator-ready reason codes.

The committee asked a pointed question that has since become a standard reviewer prompt: "If this model declines an applicant, can we tell them why, truthfully, in plain language?" For the neural candidate, the honest answer was that the decline was driven by a transaction-sequence embedding whose dimensions had no human-legible meaning; the reason codes were reverse-engineered approximations, not faithful explanations. For the interpretable benchmark, every decline mapped to specific, auditable coefficients. Given the statistically indistinguishable performance, the committee found no basis to accept opacity. A secondary concern was maintenance: the embedding model required GPU retraining and specialized monitoring, whereas the benchmark could be re-fit and re-validated by any analyst on the team within an afternoon.

**Lesson.** Complexity must earn its place. Meridian's "interpretable benchmark as challenger floor" practice dates to this case: any complex candidate must beat the interpretable benchmark by a *material and statistically defensible* margin — overlapping bootstrap confidence intervals are not a win — and must preserve adverse-action explainability sufficient to generate truthful reason codes. This reinforced the bank's conservative posture and fed directly into the explainability expectations carried into Editions 1–3.

---

### Case 2022-05 — Unstable Feature Removed by Feature Governance

**Situation.** A 2022 candidate relied heavily on a feature called `recent_inquiry_velocity_30d`, a fast-moving credit-inquiry count over a 30-day trailing window. The feature ranked among the top three contributors and meaningfully lifted discrimination.

**Decision.** The newly stood-up Feature Governance Council ordered the feature removed and the model retrained before validation would proceed.

**Rationale.** Population Stability Index monitoring of the feature across consecutive monthly vintages showed severe instability — the distribution shifted dramatically during a bureau-reporting cadence change, and the feature's PSI repeatedly breached the council's instability trigger.

| Vintage pair | Feature PSI | Status |
|---|---|---|
| Jan→Feb 2022 | 0.31 | Unstable |
| Feb→Mar 2022 | 0.28 | Unstable |
| Post-removal model | n/a | Stable inputs |

A feature that swings this much month-to-month produces a model whose scores are not comparable over time and whose calibration silently degrades. The council judged that the marginal lift was not worth the operational and calibration risk, and that the feature would have driven spurious drift alarms downstream.

The development team's objection was that the instability was transient — an artifact of the bureau-reporting cadence change that would settle once the new cadence stabilized. The council acknowledged the point but held that a model promoted during the unstable window would bake the distorted distribution into its splits and calibration, and that "wait and see whether it settles" is not a posture compatible with a production credit decision affecting consumers. The retrained model, with the velocity feature removed, lost roughly 0.6 points of test AUC — a cost the council deemed acceptable in exchange for inputs that would not silently corrupt the score's meaning over time. The council also required that, were the feature to be reconsidered later, it be re-engineered over a longer trailing window less sensitive to reporting cadence.

**Lesson.** Stability is a promotion gate, not an afterthought. This case formalized pre-promotion feature-stability screening — PSI computed on each candidate feature across consecutive vintages — as a prerequisite to validation, distinct from the post-promotion population-stability monitoring that watches the deployed model. It also clarified the division of authority: Feature Governance owns input admissibility, while the MRC owns the promotion decision. That separation of concerns recurs, in a different guise, in the separation-of-duties control of Case 2024-09.

---

### Case 2023-04 — First Promotion Under Edition 1; A Candidate Fails the AUC Floor of Its Era

**Situation.** With Edition 1 ratified on 2023-01-01, the first refresh under the new written standard arrived in Q2 2023. Edition 1 set an accuracy floor of 0.80, an AUC floor of 0.82, used ranking accuracy as the selection metric, prescribed an 80/10/10 split at seed 7, imposed a regional-disparity ceiling of 0.20, registered the model under the name `meridian_risk_model_v1` with artifact path `model`, and promoted via the MLflow **Production stage**.

**Decision.** The submitted challenger was rejected for failing the AUC floor; a subsequent retrained candidate passed and was promoted to Production.

| Candidate | AUC (floor 0.82) | Accuracy (floor 0.80) | Region DPD (ceiling 0.20) | Outcome |
|---|---|---|---|---|
| Initial | 0.815 | 0.81 | 0.11 | Rejected — AUC below floor |
| Retrained | 0.834 | 0.82 | 0.09 | Promoted to Production |

**Rationale.** The initial candidate cleared accuracy and fairness but missed the AUC floor of 0.82 by half a point. Under Edition 1 the floors were hard gates; no compensating-strength argument was permitted. The team diagnosed an under-fit caused by overly aggressive regularization, relaxed it, retrained on the seed-7 80/10/10 split, and re-submitted a candidate that cleared all three Edition 1 gates and was promoted to the Production stage under the name `meridian_risk_model_v1`.

A noteworthy procedural point: the initial candidate's developers requested an exception, arguing that the 0.005 AUC shortfall was within validation noise and that the model's superior fairness profile (a 0.11 regional disparity, comfortably under the 0.20 ceiling) should compensate. The MRC declined. Under Edition 1 the floors were not balancing factors to be traded against one another; each was an independent gate that had to be cleared on its own terms. Granting a noise-band exception, the committee reasoned, would erode the gate for every future submission and invite endless litigation over what counted as "within noise." The cleaner path was to fix the under-fit and re-submit, which the team did within two weeks.

**Lesson.** Hard floors are hard, and gates do not compensate for one another. The case demonstrated the discipline of Edition 1's gating and the value of a single reproducible split and seed for apples-to-apples comparison across the original and retrained candidates. Every value cited here — the 0.82 AUC floor, the 0.80 accuracy floor, the 0.20 regional ceiling, the 80/10/10 seed-7 split, the `meridian_risk_model_v1` registry name, the `model` artifact path, and Production-stage promotion — is **Edition 1 history and has since been superseded**. The current floors, ceilings, split, name, and promotion mechanism are in §6–§13 and must not be inferred from this case.

---

### Case 2023-09 — Post-Promotion Rollback on Drift

**Situation.** A model promoted to Production in spring 2023 under Edition 1 began, by September, to show deteriorating live performance as macroeconomic conditions tightened and the through-the-door population shifted toward thinner-file applicants.

**Decision.** The model was rolled back to the prior Production version after monitoring breached the drift and performance-decay triggers in force.

**Rationale.** Production monitoring tracked scoring-population PSI and a rolling realized-AUC proxy. Over six weeks the input PSI climbed steadily while the realized discrimination eroded.

| Week | Population PSI | Rolling AUC proxy |
|---|---|---|
| Baseline | 0.04 | 0.83 |
| Week 4 | 0.19 | 0.80 |
| Week 6 | 0.27 | 0.77 |

When the PSI and the AUC-decay measures crossed the Edition 1 monitoring triggers, the model-risk on-call invoked rollback under the change-management runbook, reverting the Production-stage pointer to the previously validated version while a replacement was developed. Because Edition 1 used the MLflow Production stage, the rollback was executed by reassigning the Production stage to the prior model version.

The incident review surfaced two operational lessons beyond the drift itself. First, the rollback, executed by reassigning the Production stage to the prior version, briefly created ambiguity in the registry: for a short window the stage history made it unclear which version was authoritative, and a downstream batch job nearly scored against the wrong version before the on-call manually confirmed the pointer. Second, the realized-AUC proxy lagged the population PSI by roughly two weeks, meaning the population shift was detectable well before performance visibly decayed — arguing for earlier, input-side triggers rather than waiting for outcome-side confirmation. Both findings were logged as inputs to the next edition's monitoring design.

**Lesson.** Promotion is not the end of the lifecycle. This case hardened Meridian's drift-monitoring and documented rollback procedure, and it showed that a stage-based rollback, while workable, was operationally clumsy and momentarily ambiguous — a finding that contributed materially to the later move toward alias-based promotion (Case 2024-12). The specific trigger values used in 2023 were Edition 1 operational settings and are not the current rollback triggers; the values in the table are this incident's observed measurements. The operative triggers are defined in §13.

---

### Case 2024-09 — Separation-of-Duties Control Catches a Conflict

**Situation.** During the first refresh under Edition 2 (ratified 2024-01-01), a model arrived for promotion with validation sign-off already attached. Edition 2 carried an accuracy floor of 0.80, an AUC floor of 0.81, a ranking macro-F1 bar of 0.75, a 70/15/15 split at seed 13, a gender-disparity ceiling of 0.06, and continued Production-stage promotion.

**Decision.** The promotion was paused by the governance gate when the access-control review found that the validator and a co-developer were the same individual.

**Rationale.** The candidate's metrics were in order:

| Metric (Edition 2) | Value | Edition 2 rule |
|---|---|---|
| AUC | 0.836 | floor 0.81 — pass |
| Accuracy | 0.82 | floor 0.80 — pass |
| Macro-F1 | 0.78 | bar 0.75 — pass |
| Gender DPD | 0.05 | ceiling 0.06 — pass |

But the MRM governance workflow enforces separation of duties: the person who develops or contributes to a model may not sign its independent validation. The audit-log review flagged that the named validator had committed feature-engineering code to the candidate's repository. The promotion was frozen, an independent validator was assigned, and the model underwent fresh validation. It ultimately passed on the merits, but only after the conflict was cured.

There was, predictably, pushback. The individual in question argued the conflict was technical rather than substantive — the committed code was a minor refactor, not core feature logic — and that re-validating would delay a needed refresh by a month. The MRM head's response is preserved in the file: separation of duties is a *bright-line* control precisely so that no one has to adjudicate, case by case, how much involvement is "too much." The moment the line requires judgment about degree, it stops being a control and becomes a negotiation. The independent re-validation cost three weeks; the candidate passed cleanly, and the episode produced an automated identity cross-check that now runs before any promotion can be queued.

**Lesson.** Controls are not satisfied by good metrics, and bright lines exist to avoid case-by-case adjudication. A clean scorecard does not excuse a broken control; separation of duties is an independent gate. This case strengthened the automated cross-check between repository commit identities and validation sign-off identities. The Edition 2 values quoted (the 0.81 AUC floor, the 0.80 accuracy floor, the 0.75 macro-F1 bar, the 0.06 `gender` demographic-parity ceiling, the 70/15/15 seed-13 split, and Production-stage promotion) are **historical and superseded**; the current criteria are in §6–§13.

---

### Case 2024-12 — Migration From Production-Stage to Alias-Based Promotion

**Situation.** By late 2024, accumulated operational pain — exemplified by the clumsy stage-based rollback in Case 2023-09 — drove a project to redesign the promotion mechanism. MLflow had deprecated model stages in favor of registry aliases and tags, and Meridian's platform team aligned with that direction.

**Decision.** The MRC approved, as a forward-looking design decision feeding into Edition 3, the migration from Production-stage promotion to **alias-based promotion**, where the live model is designated by a registry alias rather than a stage transition.

**Rationale.** Stage-based promotion conflated lifecycle state with deployment intent and made rollbacks a destructive reassignment of a shared stage label. Aliases decouple "which version is live" from "which version is in what lifecycle state," allow atomic repointing, and preserve a clean audit trail of alias moves. A migration pilot demonstrated the difference:

| Capability | Production stage (Eds. 1–2) | Alias-based (Ed. 3 design) |
|---|---|---|
| Promotion act | Stage transition | Alias assignment |
| Rollback | Reassign shared stage | Repoint alias atomically |
| Audit clarity | Stage history conflated | Discrete alias-move log |

The migration was not without cost. The platform team had to rewrite the deployment-serving lookup to resolve the live model by alias rather than by stage, update every downstream batch and real-time scoring client, and back-fill an alias-move audit log so that historical promotions remained traceable. A transition period ran both mechanisms in parallel for one refresh cycle to confirm equivalence before the stage-based path was retired. The MRC also took the opportunity to clarify governance language: under the alias regime, "promotion" is defined as the act of assigning the designated alias to a validated version, and "rollback" as repointing that alias — definitions that removed the lifecycle-versus-deployment conflation that had caused the ambiguity in Case 2023-09.

**Lesson.** This case documents the mechanism shift that distinguishes Edition 3 from its predecessors: Editions 1 and 2 promoted via the MLflow Production stage, whereas Edition 3 promotes via an MLflow alias. The case records *that* the migration happened and *why*; the specific current alias name and registry name are defined in §6–§8 and are deliberately not restated here, consistent with this section's role as historical narrative rather than as a statement of binding configuration.

---

### Case 2026-02 — Rollback Automation Works As Designed

**Situation.** In February 2026, under the newly effective Edition 3 regime, a freshly promoted PD model experienced an abrupt input-distribution shock following an upstream bureau data-feed schema change that silently null-filled a key feature.

**Decision.** No human intervention was required for the initial response: the automated rollback fired, repointed the live alias to the last-good version, and paged the on-call.

**Rationale.** Edition 3's monitoring stack watches input integrity, population stability, and a realized-performance proxy, and is wired to invoke an automatic alias repoint when configured triggers breach. When the schema change drove a sudden spike in null rates and a corresponding drop in the live performance proxy, the automation detected the breach within the monitoring interval and executed the rollback.

| Signal | Pre-incident | At trigger | Action |
|---|---|---|---|
| Feature null rate | ~0% | 41% | Integrity breach |
| Population PSI | 0.03 | 0.30 | Stability breach |
| Live AUC proxy | 0.81 | 0.73 | Performance decay |

The alias was atomically repointed to the prior validated version, scoring continuity was preserved, and the post-incident review confirmed the automation behaved exactly per runbook. Root cause was traced to the upstream feed, not the model, and the feature pipeline was hardened with a null-rate guard.

The post-incident review was notably calm precisely because the automation had done its job: time-to-containment was a single monitoring interval, no consumer was scored against the degraded model after the trigger fired, and the audit log showed a clean alias-move from the affected version back to the last-good version with a timestamp and the triggering signal recorded. The review did surface one improvement: the integrity check had caught the null-rate spike, but a tighter upstream contract test would have caught the schema change before it ever reached the feature pipeline. Accordingly, a schema-conformance gate was added on ingestion of the bureau feed, and the feature pipeline gained an explicit null-rate guard that fails closed rather than null-filling silently.

**Lesson.** Automation, well-specified and well-tested, contains incidents faster than humans can. This case is Meridian's clearest demonstration that the alias-based mechanism adopted in Case 2024-12 pays off operationally: the rollback was a clean, atomic, auditable alias repoint rather than a destructive stage reassignment, and it required no human in the critical path. The specific trigger thresholds that fired here are Edition 3 operational settings owned by §13; the values shown in the table are this incident's observed measurements, not a restatement of the governing triggers, and the binding trigger definitions remain in §13.

---

**Closing note for reviewers.** Read horizontally across these ten cases and three themes recur: (1) *how* a model earns accuracy matters as much as the accuracy itself — proxies, leakage, and instability disqualify even strong scorecards; (2) controls and separation of duties are independent gates that a clean metrics sheet cannot satisfy; and (3) the lifecycle does not end at promotion — monitoring, rollback, and the mechanism by which the live model is designated are first-class governance concerns. Every numeric floor, ceiling, split, seed, name, and trigger quoted above is anchored to its case date and edition. For any present-day decision, the only authoritative criteria are those in §6 through §13.
