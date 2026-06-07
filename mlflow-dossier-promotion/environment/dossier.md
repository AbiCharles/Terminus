# Meridian Financial — Consumer Credit Model Promotion Governance Dossier

**Document reference:** MRM-GOV-CCD-0327
**Edition:** 3 (effective 2026-01-01)
**Classification:** Internal — Model Risk Management
**Owning function:** Second Line of Defense, Model Risk Management (MRM)
**Supersedes:** Edition 1 (2023-03-01, ref. MRM-GOV-CCD-0102) and Edition 2 (2024-06-15, ref. MRM-GOV-CCD-0219)

> **Reader's note on precedence.** Throughout this dossier, *only the thresholds, names, and
> procedures stated in the numbered governing sections (§6 through §13) of this Edition 3 document
> are binding.* The supplementary sections §14 through §24 — including the regulatory background, the
> methodology chapters, the historical case study library (§21), the glossary (§23), and the
> appendices (§24) — are provided for context, methodology, and audit traceability only. Several of
> them describe **superseded** Edition 1 and Edition 2 criteria, or quote production-monitoring
> observations, and must not be mistaken for the current cycle's binding criteria. Where a number in
> any supplementary section differs from the governing sections, **the governing section controls.**

---

## §1 Executive Summary

Meridian Financial operates a portfolio of consumer lending products supported by quantitative
models that estimate the probability that an obligor will default within a twelve-month performance
window. This dossier defines the **governance, validation, and promotion criteria** that a candidate
probability-of-default (PD) classifier must satisfy before it may be promoted to the role of
production champion within the enterprise model registry.

The promotion process is deliberately conservative. A candidate model is not promoted because it is
the most accurate option available; it is promoted because it simultaneously (a) clears the minimum
predictive-performance bar, (b) satisfies the fair-lending disparity constraints applicable to
protected and quasi-protected attributes, and (c) was constructed only from features that the
feature-governance committee has approved for use in credit decisioning. A model that is highly
accurate but violates a disparity constraint, or that achieves its accuracy by relying on a
prohibited proxy variable, is **disqualified regardless of its headline performance**.

This Edition 3 revision tightens several Edition 2 provisions and re-platforms model tracking onto an
MLflow-based registry. The substantive changes are: adoption of the alias-based promotion mechanism
(replacing the legacy stage-based mechanism), a revised holdout sampling protocol, recalibrated
performance floors, and an expanded set of monitored rollback triggers.

## §2 Regulatory and Policy Context

Meridian's model risk practices are framed by Federal Reserve Supervisory Letter **SR 11-7** and the
parallel **OCC Bulletin 2011-12** on model risk management, which together establish the
expectations for model development, validation, and ongoing monitoring under an effective-challenge
regime. Fair-lending obligations derive from the **Equal Credit Opportunity Act (ECOA)** as
implemented by **Regulation B**, and from the disparate-impact doctrine as articulated in
interagency fair-lending examination procedures. Where a model input is not itself a prohibited
basis but operates as a close proxy for one, its use is treated as presumptively impermissible
unless a documented business-necessity justification has been accepted by the Fair Lending Officer;
no such justification is in force for the current cycle.

The promotion criteria below are the operational translation of those obligations into measurable,
testable gates. They are intended to be reproducible: an independent reviewer who applies the stated
sampling protocol to the stated dataset must be able to recompute every reported metric and reach
the same promotion decision.

## §3 Governance Framework and Lifecycle

Every model progresses through five lifecycle states: *Proposed*, *In Development*, *In Validation*,
*Approved-Champion*, and *Retired*. Movement from *In Validation* to *Approved-Champion* is the
"promotion" event governed by this dossier. Promotion is gated by the Model Risk Committee acting on
a validation package assembled by the second line. The validation package must contain, at minimum,
a reproducible training record for every candidate, the computed acceptance metrics, the fairness
assessment, and a written promotion recommendation identifying the single champion.

## §4 Approval Authorities and RACI

The Head of Model Risk is **Accountable** for every promotion decision. The MRM validation lead is
**Responsible** for assembling and certifying the validation package. The Fair Lending Officer is
**Consulted** on every disparity assessment and holds an absolute veto over any candidate that
breaches a disparity ceiling. The sponsoring line-of-business executive and the Chief Data Officer
are **Informed**. No individual contributor may both develop a candidate and certify its validation
package; the separation-of-duties control is mandatory.

## §5 Model Inventory Conventions

Each governed model occupies exactly one logical slot in the enterprise registry. The slot carries a
stable registered name; individual trained artifacts are recorded as versions beneath that name, and
exactly one version at a time may carry the production alias. The conventions for the present cycle
are specified in §6.

## §6 Model Identity and Registry Conventions

For this promotion cycle the candidate models all target the same registry slot. The **registered
model name** under which the promoted champion must be recorded is
`meridian_credit_default_classifier`. (The Edition 1 inventory used the name
`meridian_risk_model_v1`; that name is retired and must not be reused.)

Promotion is expressed through an **alias**, not a lifecycle stage. The production alias for the
champion is the literal string `champion`. Edition 2 used MLflow's legacy stage transition to the
`Production` stage; Edition 3 has migrated to aliases, and the stage-based mechanism is deprecated
and must not be relied upon.

All experiment runs for this cycle are recorded under a single tracking experiment named
`credit_default_promotion`. When a candidate's fitted estimator is logged as a model artifact, it
must be logged under the artifact path `credit_default_model`. (Earlier editions logged the
serialized estimator under the artifact path `model`; that convention is superseded — the current
artifact path is `credit_default_model`.) The prediction target column in the dataset is named
`default`.

## §7 Data Sourcing, Splits, and Sampling Protocol

The development dataset for this cycle is the curated extract provided as `data.csv`, one row per
historical application with the binary outcome recorded in the `default` column.

The sampling protocol partitions the dataset into **70 percent training, 15 percent validation, and
15 percent test**, with the partition **stratified on the `default` outcome** so that the default
rate is preserved across all three folds. To guarantee reproducibility the partition is seeded with
the integer random state **42**.

The partition is constructed in two stages. First, a single stratified draw separates a **30 percent
holdout pool** from the 70 percent training fold, using random state 42. Second, that 30 percent
holdout pool is split **in half** — again by a stratified draw seeded with random state 42 — to form
the validation fold and the test fold, each representing 15 percent of the original data. All
reported acceptance metrics and all fairness statistics are computed on the **test** fold. The
validation fold is reserved for threshold tuning and is not used to compute the acceptance metrics
for the current candidate roster. (Edition 1 used an 80/10/10 split seeded with random state 7; this
is superseded by the 70/15/15 protocol above.)

To remove any ambiguity about partition order, the canonical result of this protocol is materialised
in `data.csv` as a `split` column whose value is `train`, `validation`, or `test` for each row.
Consumers must use this `split` column directly as the train/validation/test assignment rather than
re-deriving the partition; models are fit on the `train` rows and every reported metric is computed
on the `test` rows.

## §8 Candidate Model Roster

The model risk team has pre-registered the following three candidate configurations for this
evaluation cycle. Each configuration must be trained on the training fold and evaluated on the test
fold exactly as specified; the agent does not select the model families or hyperparameters, it
executes the registered roster and lets the acceptance and fairness gates determine eligibility.

1. **`logreg_baseline`** — a `LogisticRegression` classifier serving as the interpretable benchmark,
   configured with inverse-regularization strength `C` equal to 1.0, a maximum of 1000 solver
   iterations, and random state 42. It is trained on the approved feature set only (see §9).

2. **`gbm_audit`** — a `GradientBoostingClassifier` configured with 200 estimators, a maximum tree
   depth of 3, a learning rate of 0.1, and random state 42. This configuration is trained on the
   approved feature set **augmented with the `region_risk_index` field as an additional numeric
   feature** (standardized alongside the other numeric predictors). It exists so that the
   disparate-impact uplift attributable to the regional proxy can be measured explicitly; it is
   subject to exactly the same gates as every other candidate.

3. **`gbm_compliant`** — a `GradientBoostingClassifier` configured identically to `gbm_audit` (200
   estimators, maximum depth 3, learning rate 0.1, random state 42) but trained on the approved
   feature set **only**, excluding `region_risk_index`.

Every candidate uses the same preprocessing: numeric features are standardized to zero mean and unit
variance, and categorical features are one-hot encoded with unknown categories ignored at transform
time.

## §9 Feature Governance and Prohibited Proxies

The feature-governance committee has approved the following predictors for use in credit decisioning.
The approved **numeric** features are `income`, `loan_amount`, `dti_ratio`, `credit_score`,
`employment_years`, and `num_open_accounts`. The approved **categorical** features are
`home_ownership` and `loan_purpose`.

The field `region_risk_index` is **prohibited** as a model input for any model that is eligible for
promotion. Although it is numerically predictive, it is a close geographic proxy that reproduces the
regional disparity pattern the fair-lending program is obligated to suppress; its inclusion is
treated as presumptively impermissible for the current cycle. For the purpose of the policy record,
`region_risk_index` is the sole entry on the prohibited-feature list.

The protected and quasi-protected attributes `age_group`, `gender`, and `region` are likewise never
used as model inputs; they are retained in the dataset solely to compute the fairness statistics
described in §11. They are not modelling features at all — approved or prohibited — and so are
catalogued as the fairness slices in §11 rather than on the prohibited-feature list.

## §10 Performance Acceptance Criteria

To be eligible for promotion a candidate must clear every one of the following minimum thresholds on
the test fold. The minimum acceptable **accuracy** is **0.72**. The minimum acceptable
**macro-averaged F1 score** (the unweighted mean of the per-class F1 scores) is **0.70**. The
minimum acceptable **area under the ROC curve** is **0.78**. A candidate that falls below any one of
these three floors is disqualified, irrespective of how strong its other metrics may be.

Among the candidates that clear every acceptance threshold *and* satisfy every fairness constraint in
§11, the champion is the one with the highest **area under the ROC curve**. ROC-AUC is the ranking
metric for champion selection; ties, should they occur, are broken in favor of the higher
macro-averaged F1 score.

(For the historical record: Edition 1 set the accuracy floor at 0.80 and the ROC-AUC floor at 0.82,
and Edition 2 briefly used macro-F1 of 0.75 as the ranking metric. None of these earlier values
apply to the current cycle.)

## §11 Fairness and Disparate-Impact Assessment

Fairness is assessed on the test fold using the **demographic-parity difference** statistic. For a
given protected attribute, the demographic-parity difference is defined as the difference between the
highest and the lowest rate of positive predictions (predicted `default` equal to 1, at the default
0.5 decision threshold) observed across the groups of that attribute. A smaller value indicates more
uniform treatment across groups.

A candidate is disqualified if the demographic-parity difference for any monitored attribute exceeds
its ceiling. The ceiling for `age_group` is **0.12**. The ceiling for `gender` is **0.10**. The
ceiling for `region` is **0.15**. These ceilings apply independently; breaching any single ceiling
disqualifies the candidate.

## §12 Champion Selection and Promotion Workflow

The promotion procedure is as follows. Train and evaluate every candidate in the §8 roster under the
§7 protocol. Discard any candidate that fails any §10 acceptance threshold. From the survivors,
discard any candidate that breaches any §11 fairness ceiling. If no candidate survives, the cycle
fails and no promotion occurs. Otherwise, select the surviving candidate with the highest ROC-AUC as
the champion, register it in the enterprise registry under the registered model name from §6, and
assign it the `champion` alias. Non-champion candidates remain recorded as runs but receive no alias
and are not registered as the champion.

## §13 Rollback and Monitoring Conditions

After promotion, the champion is monitored continuously and is automatically rolled back to the prior
champion if any of the following triggers fires. The first trigger, identified as `auc_floor`, fires
when the monitored production ROC-AUC falls below 0.74. The second trigger, identified as
`drift_psi`, fires when the population stability index of the incoming score distribution rises above
0.25. The third trigger, identified as `approval_rate_floor`, fires when the weekly approval rate
falls below 0.35. Any single trigger is sufficient to initiate rollback.

## §14 Regulatory and Supervisory Background

This section establishes the regulatory and supervisory foundation on which the promotion controls in this dossier rest. It is explanatory and non-binding: nothing stated here creates, modifies, or substitutes for the binding acceptance criteria, fairness ceilings, sampling protocol, registry conventions, or rollback triggers that govern an actual promotion decision. Those binding values reside exclusively in the governing sections (§6 through §13). Where this section refers to a quantitative gate, it does so by pointer to the controlling section and never by restating a current threshold. The purpose here is to give a validator, an internal auditor, or a supervisory examiner the legal and prudential context necessary to read the rest of the dossier semantically — to understand *why* each gate exists, *which* statutory or supervisory expectation it discharges, and *how* the evidence trail produced by a promotion run maps back onto that expectation.

### 14.1 The Model-Risk Management Mandate

Meridian Financial, N.A. treats the 12-month probability-of-default (PD) classifier governed by this dossier as a "model" within the meaning of the interagency supervisory guidance on model risk management, issued by the Board of Governors of the Federal Reserve System as Supervisory Letter SR 11-7 and adopted contemporaneously by the Office of the Comptroller of the Currency as OCC Bulletin 2011-12. That guidance defines a model as a quantitative method, system, or approach that applies statistical, economic, financial, or mathematical theories, techniques, and assumptions to process input data into quantitative estimates. A supervised classifier that ingests applicant- and account-level features and emits a calibrated probability of default over a forward twelve-month horizon falls squarely inside that definition. Because the output of this model informs credit-granting decisions and feeds downstream into capital, pricing, and allowance estimation, it is classified by the second line as a high-materiality model, and the promotion controls in §6–§13 are calibrated to that materiality tier.

The guidance frames model risk as the potential for adverse consequences — financial loss, poor business or strategic decisions, or reputational and legal harm — arising from decisions based on incorrect or misused model outputs. Critically, SR 11-7 identifies two fundamental sources of model risk. The first is the risk that a model has fundamental errors and produces inaccurate outputs when viewed against its design objective and intended business uses. The second is the risk that a model is used incorrectly or inappropriately, or that its limitations and assumptions are not understood by those relying on it. Meridian's promotion philosophy is deliberately conservative precisely because both sources of risk are live for a consumer-credit PD model: an error in the model degrades credit decisions at scale, and misuse — for example, deploying the model on a population outside its development sample, or treating a ranking statistic as if it certified fairness — can introduce harm that no single accuracy metric would surface. The dossier therefore does not treat predictive performance as a sufficient condition for promotion. A candidate that is more accurate but that violates a fairness ceiling, or that relies on a prohibited proxy feature, is disqualified. This asymmetry is intentional and is described in detail in the governing sections; here it is sufficient to note that it is a direct operationalization of the SR 11-7 principle that model risk is not reducible to model error.

#### 14.1.1 The Three Components of an Effective Framework

SR 11-7 and OCC 2011-12 organize sound model-risk management around three mutually reinforcing components. Meridian's framework is structured to mirror them, and the artifacts produced during a promotion run are mapped to each.

The first component is **model development, implementation, and use**. The guidance expects that a model rest on sound theory, that its design and construction be documented in a manner that a knowledgeable third party could understand and evaluate, that the data used to build it be relevant and of high quality, and that developmental testing be performed to confirm the model behaves as intended. In this dossier, this component is discharged through the documented feature set — the approved predictors enumerated in the controlling sections (income, loan_amount, dti_ratio, credit_score, employment_years, num_open_accounts, home_ownership, loan_purpose) — and through the requirement that the development sample be drawn under the sampling protocol referenced in §7. Developmental testing maps onto the candidate-evaluation step that produces the metrics later compared against the acceptance thresholds in §10.

The second component is **model validation**. SR 11-7 describes validation as the set of processes and activities intended to verify that models are performing as expected, in line with their design objectives and business uses. It articulates three core elements of validation: an evaluation of conceptual soundness, including developmental evidence; ongoing monitoring, including process verification and benchmarking; and outcomes analysis, including back-testing. The guidance insists that validation be performed by parties who are independent of model development and who possess the requisite expertise and the authority to challenge. The second line of defense at Meridian — the Model Risk Management (MRM) function — owns validation, and the promotion gates in §8–§11 are the codified validation tests that a candidate must clear before the registry alias is moved.

The third component is **governance, policies, and controls**. The guidance is explicit that even a strong development and validation regime will fail without a governance structure that assigns clear roles and accountability, establishes policies and procedures, maintains inventories, and ensures that issues are escalated and remediated. This dossier is itself an instrument of that third component: it is a policy chapter that defines the registry conventions in §6, the gating logic, the documentation requirements, and the rollback triggers referenced in §13. The promotion of a champion via an MLflow registry alias, rather than through an informal or undocumented handoff, is a governance control — it creates a single, auditable point of authority over which model version is treated as production-eligible.

### 14.2 The Three Lines of Defense and Effective Challenge

Meridian implements the SR 11-7 governance expectation through a conventional three-lines-of-defense structure, and the promotion process described in this dossier is the mechanism by which the second line exercises *effective challenge* over the first.

The **first line of defense** comprises the model owners and developers within the consumer-credit business and its supporting data-science function. The first line proposes a candidate model, assembles the development sample under the §7 protocol, trains the candidate, and produces the developmental evidence and metric report. The first line owns the model in the sense that it is accountable for its design and for the business decision to seek promotion. Importantly, the first line does *not* have the authority to move the registry alias on its own; the separation of the act of building from the act of certifying is the structural expression of independence.

The **second line of defense** is the MRM function, supported by the fair-lending compliance group. The second line does not merely review the first line's self-assessment; it independently re-runs or re-derives the controlling metrics against the held-out evaluation data, confirms that no prohibited proxy feature has entered the feature set, computes the fairness statistics against the ceilings in §11, and renders the promotion decision. SR 11-7 uses the phrase *effective challenge* to describe this activity, and the guidance is precise about what makes a challenge effective: it requires the right incentives, competence, and influence. The challenger must be motivated to find problems rather than to rubber-stamp; must possess sufficient technical skill to understand the model's mechanics; and must have organizational standing such that a finding cannot simply be overridden by the sponsoring business line. The conservative disqualification rule — that a fairness violation or a prohibited proxy defeats a candidate regardless of its accuracy — is what gives the second line's challenge teeth. Without it, effective challenge would collapse into a negotiation in which superior predictive performance could be traded against fairness concerns.

The **third line of defense** is internal audit, which does not re-perform validation but periodically assesses whether the first and second lines are executing their responsibilities in accordance with this policy. Internal audit's interest is in the integrity of the process and the completeness of the audit trail: did a promotion actually clear every gate, was the evidence retained, were the registry conventions in §6 followed, and were any rollback events handled in accordance with §13. The documentation and audit-trail expectations set out later in this section exist principally to make the third line's work tractable.

#### 14.2.1 Effective Challenge as a Continuing Doctrine

It would be a misreading of SR 11-7 to treat effective challenge as a one-time event discharged at the moment of promotion. The guidance frames it as a continuing posture. A model that cleared every gate at promotion can still drift into error or into disparate outcomes as the underlying population changes, as macroeconomic conditions shift, or as the data pipeline feeding it degrades. The promotion decision is therefore not the terminus of challenge but its renewal point. Each promotion run re-subjects the incumbent's design assumptions to scrutiny, and the rollback triggers referenced in §13 are the codified expression of the principle that the second line retains the standing authority to revoke a previously granted promotion when monitoring evidence warrants. The supervisory expectation is that the institution never reaches a state in which a model is simply trusted because it was once approved.

### 14.3 Supervisory Expectations for Ongoing Monitoring

Ongoing monitoring is one of the three validation elements named in SR 11-7, and it is the element most easily neglected, because it imposes a continuing operational burden long after the excitement of a model launch has faded. The guidance expects monitoring to confirm that a model is appropriate for its stated purpose, that it continues to perform within expected bounds, and that any deterioration is detected and acted upon. Two distinct monitoring concepts apply. *Process verification* checks that the model is implemented and operating as designed — that inputs arrive correctly, that the scoring code in production matches the validated artifact, and that no silent change has been introduced. *Benchmarking and outcomes analysis* compare the model's predictions against realized outcomes and against alternative approaches, so that gradual degradation in discriminatory power or calibration is surfaced before it produces material harm.

For a PD classifier, the relevant degradation modes include population drift (the applicant mix moving away from the development sample), concept drift (the relationship between features and default changing, often during an economic inflection), and calibration drift (predicted probabilities ceasing to match observed default frequencies even when rank-ordering is preserved). The rollback triggers referenced in §13 are the institution's pre-committed thresholds at which monitoring evidence forces a return to a prior champion or a halt in reliance on the model. Pre-committing to these triggers is itself a supervisory good practice: it removes the temptation to rationalize away deterioration in the moment, and it converts monitoring from an advisory exercise into a binding control. This dossier deliberately keeps the trigger values in §13 and does not restate them here, so that there is a single authoritative source and no risk of a stale copy in a background section misleading an operator.

### 14.4 The Fair-Lending Statutory Basis

The fair-lending dimension of this dossier rests on the Equal Credit Opportunity Act (ECOA), codified at 15 U.S.C. § 1691 et seq., and its implementing regulation, Regulation B, at 12 C.F.R. Part 1002. ECOA makes it unlawful for any creditor to discriminate against an applicant, with respect to any aspect of a credit transaction, on the basis of a prohibited characteristic. The prohibited bases include race, color, religion, national origin, sex, marital status, age (provided the applicant has the capacity to contract), the fact that all or part of the applicant's income derives from a public-assistance program, and the fact that the applicant has in good faith exercised a right under the Consumer Credit Protection Act. Regulation B operationalizes these prohibitions and, among other things, restricts the information a creditor may request and the manner in which it may be used.

A credit-scoring model occupies a particular place in this scheme. Regulation B distinguishes "empirically derived, demonstrably and statistically sound" credit-scoring systems from judgmental systems, and permits the use of age in an empirically derived system under narrowly defined conditions — but it categorically forbids the assignment of a negative factor or value to the age of an elderly applicant. More broadly, the regulation reflects a design principle that a model must not become a vehicle for laundering a prohibited characteristic into a credit decision. Meridian's treatment of age_group, gender, and region as protected or quasi-protected attributes — attributes against which the model's outputs are tested but which are not themselves predictors — is the modeling-side expression of this principle. These attributes are used to *measure* disparity, not to *drive* decisions.

#### 14.4.1 Disparate Treatment and Disparate Impact

Fair-lending law recognizes two distinct theories of liability, and the interagency fair-lending examination procedures direct examiners to evaluate institutions against both. The distinction is foundational to how this dossier's gates are designed.

**Disparate treatment** occurs when a creditor treats an applicant differently on a prohibited basis. It does not require any showing of intent to harm; it is established by the differential treatment itself. In the modeling context, the clearest form of disparate treatment would be the direct inclusion of a prohibited characteristic as a predictor that moves the score. This is why the approved predictor list in the controlling sections is exhaustive and why the protected attributes are excluded from it. The model cannot treat applicants differently on the basis of gender or age_group if those attributes are not inputs to the scoring function.

**Disparate impact** is subtler and is the theory that most often implicates a statistically derived model. It arises when a facially neutral policy or practice — here, a scoring rule built only from ostensibly permissible predictors — nonetheless produces a significantly adverse effect on a protected class, and the practice is not justified by business necessity, or a less-discriminatory alternative exists that would serve the same legitimate objective. A model can satisfy the disparate-treatment test perfectly, using only approved predictors, and still fail the disparate-impact test if those predictors are correlated with protected status in a way that systematically disadvantages a group. The fairness gates in this dossier — built on the demographic-parity-difference statistic computed across age_group, gender, and region and compared against the ceilings in §11 — are the institution's principal control against disparate impact. They are screening tests: they detect the *adverse effect* prong of the analysis before a model is promoted, so that any candidate exhibiting impermissible disparity is stopped and either rejected or routed into the business-necessity and less-discriminatory-alternative analysis described below.

#### 14.4.2 The Burden-Shifting Framework

The disparate-impact analysis follows a three-stage burden-shifting structure that is well established in fair-lending supervision and that mirrors the framework recognized under analogous civil-rights statutes. First, the party challenging the practice must identify a specific practice and demonstrate that it causes a disparate impact on a protected class. Second, if such an effect is shown, the burden shifts to the creditor to demonstrate that the practice serves a legitimate business necessity — that it has a manifest relationship to a valid, nondiscriminatory business objective such as the accurate prediction of creditworthiness. Third, even where business necessity is established, the challenger may still prevail by showing that a less-discriminatory alternative exists that would serve the creditor's legitimate objective comparably.

This framework explains a structural feature of the dossier that might otherwise look like over-engineering. Clearing the fairness ceilings in §11 is necessary but is not, by itself, a complete defense; it is the institution's evidence that no impermissible adverse effect of the kind that would trigger the first stage is present. The conservative disqualification rule — that a higher-accuracy candidate which breaches a ceiling is rejected in favor of a compliant one — is the institution voluntarily performing the less-discriminatory-alternative analysis *in advance*, at the point of model selection, rather than waiting to assert business necessity defensively after the fact. By preferring the compliant model when one exists, Meridian discharges the third-stage inquiry as a matter of design. The demographic-parity-difference statistic and its ceilings thus serve double duty: they screen for adverse effect, and the selection logic built around them operationalizes the search for a less-discriminatory alternative.

### 14.5 The Proxy-Discrimination Doctrine and Geographic Proxies

The most legally hazardous failure mode for a credit model is proxy discrimination: the use of a facially neutral variable that functions as a stand-in for a prohibited characteristic. A variable need not be labeled "race" or "national origin" to carry their predictive signal; a sufficiently granular geographic indicator can encode the demographic composition of a neighborhood with enough fidelity that conditioning on it reproduces the effect of conditioning on protected status. Fair-lending examiners are specifically attentive to geographic variables because of the long and documented history of redlining — the practice of denying or pricing credit on the basis of neighborhood composition — which is precisely the harm that the fair-housing and fair-lending statutory regime was enacted to prevent.

This is why the feature engineered as region_risk_index is treated in this dossier as a prohibited proxy and is categorically excluded from the approved predictor set, irrespective of whatever predictive lift it might offer. A region-derived risk score is a textbook geographic proxy: it aggregates outcome history at a geographic level and reintroduces it as an applicant-level feature, thereby allowing the model to penalize an applicant for where they live in a manner that can track protected-class concentration. The exclusion is not a performance judgment and is not subject to a business-necessity override at the modeling stage; it is a bright-line prohibition. A candidate that includes region_risk_index is disqualified at the gate stage even if it would otherwise clear every accuracy and fairness threshold, because its very mechanism of prediction is one the institution has determined it will not use. The distinction between region as a *protected attribute against which fairness is measured* and region_risk_index as a *prohibited predictor* is therefore deliberate and must not be elided: the institution measures disparity across region but refuses to predict from a region-derived risk feature.

### 14.6 Data Aggregation and Governance Expectations

A model is only as trustworthy as the data that feed it, and supervisory expectations for data governance flow from the Basel Committee on Banking Supervision's Principles for Effective Risk Data Aggregation and Risk Reporting, commonly cited as BCBS 239. Although BCBS 239 was framed for the aggregation of risk data at large banking organizations, its principles articulate expectations that apply directly to the data underpinning a PD model. The governance principle expects that data-aggregation capabilities be subject to strong governance arrangements consistent with the institution's other governance frameworks. The accuracy and integrity principle expects that data be aggregated on a largely automated basis so as to minimize the probability of error, and that data be reconcilable to authoritative sources. The completeness principle expects that all material risk data be captured. The timeliness principle expects that data be available rapidly enough to support decisions. And the adaptability principle expects that aggregation be flexible enough to meet ad hoc and stress requests.

In the context of this dossier, the BCBS 239 principles motivate several requirements that are elaborated in the governing sections. The sampling protocol referenced in §7 exists so that the development and evaluation data are drawn reproducibly from an authoritative source rather than assembled ad hoc; reproducibility is the data-governance counterpart to the integrity principle. The lineage between the registered artifact, the experiment in which it was produced, and the data snapshot from which it was trained — formalized through the registry conventions in §6 — is what allows a validator to reconcile a promoted model back to its inputs. Completeness and accuracy at the feature level are why the approved predictor set is fixed and documented: a model whose feature pipeline silently changed would breach both the BCBS 239 integrity expectation and the SR 11-7 process-verification element of ongoing monitoring. Data governance is therefore not a separate compliance silo but a precondition for the model-risk and fair-lending controls to mean anything; a fairness statistic computed on unreconciled or incomplete data is not evidence of anything.

### 14.7 Interaction with CECL and the Allowance Process

The outputs of a PD classifier do not terminate in the credit-decision system. A forward-looking estimate of default probability is, by its nature, an input that can flow into the institution's estimation of expected credit losses under the Current Expected Credit Loss (CECL) accounting standard, ASC 326, and into the allowance for credit losses that CECL governs. This linkage raises the materiality and the supervisory stakes of the model considerably, because an error or bias in the PD estimate can propagate into financial-statement balances and into the institution's regulatory capital position.

This dossier does not govern the allowance process, and the CECL methodology, its forecasting assumptions, and its governance live in a separate framework owned by the finance and the credit-risk functions. The point of acknowledging the linkage here is twofold. First, it reinforces the high-materiality classification of the model and thereby the conservatism of the promotion gates: a model whose outputs may inform loss estimation cannot be promoted on a thin evidentiary basis. Second, it imposes a stability and explainability expectation that purely decisioning use would not. Where a model feeds an accounting estimate, unexplained volatility in its outputs becomes an audit and a control concern in its own right, and the calibration dimension of ongoing monitoring (§14.3) takes on added importance, because CECL relies on the *level* of predicted probabilities and not merely on their rank-ordering. The promotion controls in §6–§13 are designed to be compatible with this downstream reliance; they do not themselves certify the model for CECL use, which remains a determination of the allowance framework.

### 14.8 Documentation and Audit-Trail Expectations

SR 11-7 is emphatic that documentation is not an administrative afterthought but a substantive control: the guidance states that without adequate documentation, model risk management will be ineffective, and it expects documentation sufficient to allow a party unfamiliar with a model to understand how it operates, its limitations, and its key assumptions. OCC 2011-12 carries the same expectation. The interagency fair-lending examination procedures add a complementary demand: an institution must be able to demonstrate, with contemporaneous records, that it tested for and addressed disparate impact, because the burden-shifting framework presupposes that the institution can produce its own evidence of business necessity and of the search for less-discriminatory alternatives.

Operationally, this means that every promotion run governed by this dossier must leave behind a complete, immutable, and reconstructable record. That record includes the identity and version of the candidate artifact and its lineage to the producing experiment and data snapshot under the §6 conventions; the full metric report evaluated against the §10 acceptance thresholds; the fairness computations across age_group, gender, and region evaluated against the §11 ceilings; the confirmation that the feature set contained only approved predictors and excluded region_risk_index; the identity of the second-line reviewer who rendered the decision; and, where applicable, the record of any rollback event and the §13 trigger that precipitated it. The audit trail must be sufficient for the third line, or an examiner, to answer the question "should this model have been promoted under the policy in force at the time?" purely from the retained evidence, without recourse to the recollection of any individual. The decision to express champion designation through a registry alias rather than an informal status is, again, an audit-trail control: the alias movement is itself a logged, attributable event that anchors the record.

### 14.9 How This Dossier Operationalizes the Expectations into Testable Gates

The throughline of this section is that abstract supervisory expectations become meaningful only when they are reduced to controls that can pass or fail deterministically. This dossier performs that reduction, and the governing sections hold the binding specifications. The mapping is summarized below; the section pointers are authoritative and the descriptions are explanatory only.

| Supervisory expectation | Source authority | Operationalized as | Governing section |
|---|---|---|---|
| Reproducible, authoritative development data | SR 11-7 (data quality); BCBS 239 (integrity) | Sampling protocol | §7 |
| Model lineage and inventory integrity | SR 11-7 (governance); BCBS 239 (governance) | Registry conventions | §6 |
| Conceptual soundness and developmental testing | SR 11-7 (validation, element 1) | Candidate evaluation against performance bars | §8–§10 |
| Acceptable predictive performance | SR 11-7 (validation, outcomes) | Acceptance thresholds | §10 |
| No disparate impact | ECOA / Reg B; fair-lending exam procedures | Demographic-parity-difference fairness ceilings | §11 |
| No disparate treatment / no prohibited proxy | ECOA / Reg B; proxy-discrimination doctrine | Approved-predictor allowlist; region_risk_index prohibition | §6, §11 |
| Authoritative, attributable promotion act | SR 11-7 (governance); audit-trail expectations | Champion designation via registry alias | §6 |
| Ongoing monitoring and revocation authority | SR 11-7 (validation, ongoing monitoring) | Rollback triggers | §13 |

The gates are conjunctive, not compensatory. A candidate must clear every applicable gate; strength on one dimension does not purchase tolerance on another. This is the structural feature that distinguishes Meridian's conservative philosophy from a naive optimize-for-accuracy regime, and it is the feature that makes the dossier auditable: because each gate is independent and binary, the third line and an examiner can verify compliance gate by gate rather than having to second-guess a holistic judgment call. The binding values for each gate are stated once, in the governing section, and are intentionally not reproduced in this background chapter.

### 14.10 Examination History Motivating Editions 1 through 3

The current edition did not arrive fully formed; it is the product of two prior editions and the supervisory feedback that each attracted. This subsection records that history as audit context. The values cited here are *retired* and are presented solely to explain the evolution of the framework; none of them is in force, and none should be read as a current criterion.

**Edition 1 (2023, reference MRM-GOV-CCD-0102).** The institution's first formal promotion policy for the consumer-credit PD model was performance-centric. It set an accuracy floor of 0.80 and an ROC-AUC floor of 0.82, and it ranked competing candidates on accuracy alone. The development sample was partitioned 80/10/10 with a fixed random seed of 7. Fairness was addressed by a single regional disparity ceiling of 0.20, which in retrospect was both too coarse — it considered only region and ignored gender and age — and too permissive. The model was registered under the name meridian_risk_model_v1 with an artifact stored at the path model, and promotion was effected by transitioning the version into the MLflow Production stage. A supervisory examination of the consumer-credit function identified two weaknesses in this edition: the ranking-on-accuracy rule could promote a model that maximized aggregate performance while concentrating error in a protected subpopulation, and the single regional ceiling provided no protection against gender- or age-correlated disparity. Examiners also noted that promotion via a mutable stage transition left a weaker audit trail than an explicit, attributable designation would.

**Edition 2 (2024, reference MRM-GOV-CCD-0219).** The second edition responded to the first round of findings. It retained the accuracy floor at 0.80 but lowered the ROC-AUC floor marginally to 0.81 to reflect a recalibration of the development population. More significantly, it replaced accuracy with macro-F1 as the ranking metric, introducing a macro-F1 bar of 0.75 in recognition that aggregate accuracy is a poor objective when the classes are imbalanced and when error in the minority (default) class is the costly error. The data partition was revised to 70/15/15 with a fixed seed of 13, enlarging the held-out evaluation and test portions. On fairness, Edition 2 added a gender disparity ceiling of 0.06, a substantially tighter constraint than the Edition 1 regional ceiling and one that began to treat disparity as a multi-attribute concern. Promotion, however, was still effected through the MLflow Production stage. A subsequent examination credited the improvements but raised three further points: the fairness regime remained incomplete because it did not jointly constrain disparity across all of the protected and quasi-protected attributes the institution had identified; the policy did not articulate a bright-line prohibition on geographic proxy features, even though the data pipeline contained a region-derived risk index that could function as one; and the promotion mechanism continued to rely on a mutable stage rather than an immutable, attributable pointer.

**Edition 3 (this edition, 2026, reference MRM-GOV-CCD-0327).** The current edition is the institution's most conservative to date and resolves the open findings from the Edition 2 examination, though, consistent with the constraints on this background section, its governing values are stated only in §6–§13 and are not reproduced here. At the level of doctrine rather than number, Edition 3 makes four structural advances over its predecessors. First, it generalizes the fairness regime from single-attribute ceilings to a coherent set of ceilings spanning age_group, gender, and region, computed on the demographic-parity-difference statistic, so that disparity is constrained jointly rather than one attribute at a time. Second, it codifies the prohibited-proxy doctrine explicitly by naming region_risk_index as a forbidden predictor and fixing an exhaustive allowlist of approved predictors, closing the gap the Edition 2 examination flagged. Third, it abandons the mutable Production-stage promotion mechanism in favor of champion designation through a registry alias, producing the attributable, logged promotion event that examiners had sought across both prior reviews. Fourth, it elevates the conservative disqualification principle from an implicit preference to an explicit rule: a candidate that breaches a fairness ceiling or relies on a prohibited proxy is disqualified regardless of its predictive performance, thereby embedding the less-discriminatory-alternative analysis into the selection logic itself. The progression from Edition 1 through Edition 3 is, in summary, a progression from performance-first toward fairness-and-governance-first, and from informal promotion toward an auditable, gate-based regime — exactly the trajectory that the cumulative supervisory feedback was steering.

### 14.11 Reading This Dossier in Light of the NIST AI RMF

Finally, although the binding regime for this model is the prudential and fair-lending framework described above, the institution maps its controls to the National Institute of Standards and Technology AI Risk Management Framework (NIST AI RMF 1.0) as a cross-walk, because the framework's functions provide a useful vocabulary for organizing the controls. The *Govern* function corresponds to the policy and accountability structures embodied in this dossier and in the three-lines model. The *Map* function corresponds to the contextualization performed in development — identifying intended use, the population, and the protected attributes against which the model is tested. The *Measure* function corresponds to the evaluation gates: the performance metrics assessed against §10 and the fairness statistics assessed against §11. The *Manage* function corresponds to ongoing monitoring and the rollback authority in §13. The cross-walk is informational; where the NIST framework and the binding supervisory guidance might appear to diverge, the supervisory guidance and applicable law control. The value of the mapping is that it lets the institution demonstrate, to stakeholders who think in AI-governance terms, that a regime built on SR 11-7 and ECOA already satisfies the structure that the AI RMF recommends — and that the testable gates in §6–§13 are where that structure becomes real.


## §15 Model Development and Validation Methodology

This section sets out the methodological standards that govern how a consumer-credit twelve-month probability-of-default (PD) classifier is to be conceived, built, documented, and independently validated before it can be considered for promotion under this dossier. It is deliberately written as methodology rather than as a rulebook. The binding acceptance criteria, fairness ceilings, sampling protocol, candidate roster, and rollback triggers that determine whether a particular model actually clears the bar live in the governing sections (§6 through §13) and are referenced here only by pointer. Where this chapter speaks of thresholds, ranking statistics, or partition discipline, it describes the *shape* of the requirement and the reasoning behind it; the operative numbers are not restated and must be read from their authoritative homes. Nothing in §15 may be cited as the source of a binding limit, and where a developer or reviewer encounters an apparent conflict between this chapter and §6–§13, the governing sections prevail without exception.

The methodology described below reflects Meridian Financial's conservative promotion philosophy. A candidate that demonstrates superior discrimination or accuracy does not thereby earn promotion; it must additionally satisfy the fairness constraints and the prohibited-proxy prohibitions in full. A model that achieves a higher headline performance metric while violating a fairness ceiling, or while drawing predictive signal from a prohibited geographic proxy, is disqualified outright. The methodology therefore is structured so that conceptual soundness, fairness, and reproducibility are assessed as gating conditions in their own right, not as tie-breakers applied after a performance ranking has already been computed.

### 15.1 Conceptual Soundness Review

Consistent with the supervisory expectations articulated in SR 11-7 and OCC Bulletin 2011-12, the first stage of any development effort is a conceptual soundness review conducted before substantial engineering investment. Conceptual soundness asks whether the modeling approach is appropriate to the business problem, whether the chosen target and population are coherent with the credit decision the model will inform, and whether the data and methods can in principle support the inferences the model is intended to make. The review is performed jointly by the first-line development team and a second-line reviewer who has not contributed to the design, and it produces a written conceptual soundness memorandum that becomes the first artifact in the validation package.

The review interrogates the theory of the model. For a PD classifier this means establishing that the relationship between the approved predictors and twelve-month default behavior is economically plausible, that the predictors are available at the point of decision without look-ahead, and that none of the predictors functions as a surrogate for a protected attribute. The approved predictor set — income, loan_amount, dti_ratio, credit_score, employment_years, num_open_accounts, home_ownership, and loan_purpose — is examined feature by feature for both predictive rationale and proxy risk. The protected attributes age_group, gender, and region are explicitly excluded from the feature space, and the geographic proxy region_risk_index is prohibited entirely: its inclusion, in any transformed or engineered form, is treated as a conceptual-soundness failure rather than as a quantitative finding, because the harm it represents is structural and cannot be remediated by tuning. Reviewers are instructed to probe for indirect reconstruction of region_risk_index from permitted variables and to document the controls that prevent such reconstruction during feature engineering.

Conceptual soundness also encompasses the limitations register. Every model carries assumptions that hold only within a domain, and the review must enumerate those assumptions, the conditions under which they break, and the compensating controls or monitoring that mitigate the residual risk. A conceptual soundness review that returns no limitations is itself a finding; absence of identified weakness is read as insufficient scrutiny rather than as evidence of a flawless design.

### 15.2 Development Standards for the PD Classifier

#### Target definition and performance window

The modeling target is a binary indicator of default observed over a fixed twelve-month performance window measured from the observation date. The definition of "default" — the delinquency status, charge-off treatment, and cure logic that resolve borderline accounts — must be stated precisely and applied identically across every partition and every candidate. The performance window is forward-looking from the observation point, and the development data must be constructed so that no information generated during or after the window leaks into the feature vector. Because the target is realized only at the close of the window, the development sample is necessarily drawn from a vintage old enough to have matured; the methodology requires that the maturation logic be documented so that a reviewer can confirm that incomplete-performance accounts have not been silently labeled.

#### Sampling and population definition

The population from which development data is drawn must match the population on which the model will be deployed, and any exclusions — declined applications, accounts outside the product perimeter, segments governed by a separate model — must be enumerated and justified. The sampling protocol itself, including how observations are selected, how class balance is handled, and how vintages are weighted, is governed by §7 and is not restated here. Developers are directed to §7 for the operative sampling rules; this chapter establishes only the methodological expectation that the sampling design be representative, documented, and reproducible, and that any deviation from the §7 protocol be raised as an exception with second-line concurrence before development proceeds.

#### Train, validation, and test discipline

The partitioning of data into training, validation, and test sets follows the discipline specified in §7. The methodological principle, stated without restating the operative fractions or the seed, is strict separation of concerns: the training partition is used to fit candidate models, the validation partition is used for model selection and hyperparameter confirmation, and the test partition is held out untouched until a single, final evaluation. The test partition must never be consulted during development, feature selection, or tuning; a single premature look at the test set contaminates it and requires that a fresh holdout be constructed. The partition assignment must be deterministic and reproducible so that an independent reviewer regenerating the splits under the §7 protocol obtains identical membership.

It is instructive to contrast the present discipline with the superseded editions, purely as historical audit context. Edition 1 (2023) employed an 80/10/10 partition seeded with the value 7; Edition 2 (2024) moved to a 70/15/15 partition seeded with the value 13. These historical parameters are retired and are recorded here only to orient an auditor reconstructing the lineage of the methodology. The current partition fractions and seed are set in §7 and must be read from there; they are not reproduced in this chapter, and the historical values above must not be mistaken for current governing parameters.

#### Leakage controls

Leakage is treated as a first-order defect. The methodology distinguishes target leakage, in which a feature encodes information about the outcome that would not be available at decision time, from partition leakage, in which information crosses the boundary between training and evaluation sets. Controls against target leakage include the point-in-time construction of every feature, an explicit audit of each predictor's availability date relative to the observation date, and a prohibition on any feature derived from post-observation behavior. Controls against partition leakage include fitting all preprocessing transformations exclusively on the training partition and applying the fitted transformations — never refitting — to the validation and test partitions. Any statistic estimated from data (a mean, a standard deviation, an encoding table, a category vocabulary) must be learned from training data alone. Group-structured leakage, where multiple records from the same borrower span the train/test boundary, must be prevented by partitioning at the appropriate entity grain rather than at the record grain where the data structure warrants it.

#### Reproducibility and seeding philosophy

Reproducibility is a non-negotiable property of a credible model, not a convenience. Every source of pseudo-randomness in the pipeline — partition assignment, stochastic optimization, bootstrap resampling, any sampling within preprocessing — must be made deterministic by seeding from a single, recorded source of entropy so that an identical environment reproduces identical artifacts. The methodology requires that the seed be pinned and recorded in the run configuration; it does not specify the seed value here, because that value is fixed by the protocol in §7 and stating it in a non-binding chapter would invite drift. The principle is that two runs of the same code against the same data in the same environment must produce bit-identical or numerically equivalent results, and that any nondeterminism that cannot be eliminated must be quantified so that a reviewer can distinguish genuine instability from seed noise.

### 15.3 Preprocessing Standards

Preprocessing is part of the model and is validated as such. Because the most common source of subtle leakage is preprocessing that has seen the evaluation data, the cardinal rule is that every transformation is fit on the training partition and only applied elsewhere. The standards below describe the methodology; the specific transformer configurations a candidate uses are recorded in its run manifest and confirmed during validation.

#### Numeric standardization

Continuous predictors — income, loan_amount, dti_ratio, credit_score, employment_years, num_open_accounts — are standardized so that scale differences do not distort distance- or regularization-sensitive learners. The location and scale parameters used for standardization are estimated from the training partition alone and then applied unchanged to the validation and test partitions. The methodology requires that the handling of outliers and of missing numeric values be stated explicitly: whether values are winsorized, whether missingness is imputed and by what statistic, and whether a missingness indicator is retained as a separate signal. Whatever the choice, it must be fit on training data, applied consistently, and documented so that the transformation is reproducible.

#### Categorical encoding and unknown-category handling

Categorical predictors — home_ownership and loan_purpose — are encoded into a numeric representation whose vocabulary is established from the training partition. The methodology's distinctive requirement concerns categories not seen during training. Because a deployed model will inevitably encounter category values absent from its training vocabulary, the encoder must define an explicit, deterministic policy for unknown categories rather than failing or silently producing an undefined representation. The accepted approaches — mapping unknown levels to a reserved "unknown" bucket, or encoding them as an all-zero indicator vector — must be selected deliberately, fit on training data, and exercised during validation against deliberately injected novel categories so that the reviewer can confirm the model degrades gracefully rather than erroring at the decision boundary. An encoder that has no defined behavior for an unseen category is a conceptual-soundness defect, not merely an implementation gap.

The same encoding artifacts (the category vocabulary, the imputation statistics, the standardization parameters) are themselves outputs that must be persisted with the model so that scoring in production applies precisely the transformations that were validated. A mismatch between the preprocessing fit during development and the preprocessing applied at inference is a reproducibility failure that disqualifies the candidate.

### 15.4 The Candidate Roster and Pre-Registration of Hyperparameters

Meridian's methodology rejects open-ended hyperparameter exploration on the production data. Instead, development proceeds against a pre-registered candidate roster: a fixed, documented set of model families and their accompanying hyperparameter configurations, agreed before the final evaluation is run. The roster is specified in §8. This chapter does not enumerate the roster's members or their settings — the number of estimators, tree depth, learning rate, regularization strength, and iteration ceilings that distinguish the candidates are fixed in §8 and must be read there — because pre-registration loses its force the moment the configuration is reproduced in a non-binding chapter where it could be edited independently of the governing source.

The rationale for pre-registration is statistical integrity. Unbounded tuning against a held-out set is a form of multiple comparison that inflates apparent performance and corrodes the meaning of the test result. By fixing the candidate roster and its hyperparameters in advance, the methodology bounds the comparison space, makes the selection procedure auditable, and ensures that the test partition is consulted exactly once to evaluate a pre-committed set of candidates rather than repeatedly to search for a favorable outcome. Where the validation evidence suggests that the roster is inadequate — for instance, if every candidate underperforms — the remedy is to revise the roster through the §8 change process and reconstruct a fresh holdout, not to tune informally against the existing test data.

The interpretable benchmark, discussed below, is always a member of the comparison even when it is not the intended production model, because the methodology requires that a more complex learner justify its complexity against a transparent baseline.

### 15.5 Independent Validation Standards under SR 11-7

Validation is performed by a function organizationally independent of development, and its scope follows the three pillars that SR 11-7 sets out: evaluation of conceptual soundness, ongoing monitoring, and outcomes analysis. §15.1 addresses conceptual soundness; monitoring is governed elsewhere in the dossier; this subsection concentrates on the outcomes analysis and the corroborating tests that the validation package must contain.

#### Outcomes analysis

Outcomes analysis compares the model's predictions against realized outcomes. For a PD classifier this includes assessing whether predicted default probabilities correspond to observed default rates across the score distribution, and whether the classification decisions the model implies are accurate against the matured target. Outcomes analysis is conducted on the held-out test partition and, where available, on an out-of-time sample drawn from a later vintage than the development data, because temporal generalization is a sharper test of a credit model than random holdout performance alone.

#### Benchmarking

The candidate must be benchmarked against alternatives. At minimum the validation compares the candidate against the interpretable benchmark from the roster, and where a prior production model exists, against that incumbent. Benchmarking establishes whether the candidate's performance is meaningfully better than a transparent baseline and whether any improvement is large enough to justify the additional model risk that complexity introduces. A candidate that cannot beat a simple, interpretable model by a margin commensurate with its added opacity is not promotable regardless of its absolute scores.

#### Sensitivity and stability testing

Sensitivity testing perturbs inputs and assumptions to map how the model's outputs respond. Reviewers examine the model's behavior under shifts in the marginal distributions of key predictors, under plausible economic stress to variables such as income and dti_ratio, and under the deliberate injection of unknown categorical levels. Stability testing repeats the development and evaluation under controlled variation — alternative seeds within the bounds the protocol permits, resampled folds, perturbed vintages — to confirm that the reported metrics are properties of the model rather than artifacts of a single fortunate partition. A model whose performance swings materially under seed variation is judged unstable, and instability is reported as a finding even when the headline metrics on the canonical partition are acceptable.

#### The interpretable-benchmark requirement

The methodology mandates that an interpretable model accompany every candidate as a standing benchmark. The interpretable benchmark serves two purposes: it bounds the marginal value of complexity, and it provides a transparent reference whose behavior can be reasoned about directly when the primary model's predictions are challenged under ECOA/Regulation B adverse-action requirements. The benchmark must be evaluated under the identical protocol so that the comparison is fair, and its results must be reported alongside the candidate's in the validation package.

### 15.6 Calibration and Discrimination Assessment

The validation assesses both discrimination — the model's ability to rank defaulters above non-defaulters — and calibration — the agreement between predicted probabilities and observed frequencies. These are distinct properties: a model can rank well yet be poorly calibrated, and a well-calibrated model can rank poorly. Both matter for a PD classifier, because the score is used both to order applicants and, where probabilities feed downstream decisions or CECL-relevant estimates, to quantify expected outcomes.

The performance metric families the methodology relies upon are accuracy, macro-averaged F1, and ROC-AUC. Accuracy measures the overall correctness of the implied classification; macro-F1 balances precision and recall across classes and is informative when the default class is the minority; ROC-AUC summarizes ranking performance across all decision thresholds and is insensitive to a single operating point. Each family answers a different question, and the methodology requires that all three be reported so that no single statistic can mask a weakness visible in another. The governing acceptance levels for these families — the floors a candidate must clear and the statistic used to rank competing candidates — are set in §10 and are not stated here. This chapter describes only which metric families are computed and why; the numeric thresholds and the designation of the primary ranking statistic are read from §10.

Calibration is assessed through reliability analysis that compares predicted probability against observed default rate across bins of the score, supported where appropriate by a numerical calibration statistic. Where a model is well discriminating but miscalibrated, the methodology permits a documented, monotonic post-hoc calibration step provided it is fit on a calibration partition distinct from training and test, applied as part of the persisted model, and re-validated; calibration adjustment is never permitted to reach into the test partition.

It is again useful to record the historical contrast for audit lineage. Edition 1 (2023) ranked candidates on accuracy and imposed an accuracy floor of 0.80 and a ROC-AUC floor of 0.82. Edition 2 (2024) shifted the ranking statistic to macro-F1 with a selection bar of 0.75 while retaining an accuracy floor of 0.80 and adjusting the ROC-AUC floor to 0.81. These figures are superseded and are reproduced solely so that an auditor can trace how the assessment philosophy evolved across editions; they are not the current criteria, and the current criteria reside exclusively in §10.

### 15.7 Fairness and Prohibited-Proxy Assessment within the Methodology

Although the binding fairness ceilings live in §11, the methodology requires that fairness be assessed as an integral part of validation rather than as a downstream compliance check. The statistic used is the demographic-parity-difference, computed across the protected attributes age_group, gender, and region. The validation must report this statistic for each protected attribute and confirm that the model satisfies the fairness ceilings set in §11 — without restating those ceilings here. The conservative philosophy is operative throughout: a candidate with superior accuracy or discrimination that breaches a fairness ceiling, or that is found to draw signal from the prohibited proxy region_risk_index, is disqualified, and the validation report must state the disqualification as a gating outcome rather than as a deduction from a composite score.

For historical context only, Edition 1 (2023) controlled a regional disparity with a ceiling of 0.20, and Edition 2 (2024) controlled a gender disparity with a ceiling of 0.06. Those ceilings are retired. The current fairness ceilings, the attributes to which they attach, and the precise form of the parity statistic that governs promotion are specified in §11 and must be read from there; the superseded figures above are recorded purely as audit lineage and carry no current force.

The prohibited-proxy assessment is methodologically separate from the parity statistic. Even a model that satisfies every parity ceiling is disqualified if region_risk_index, or a reconstruction of it, has entered the feature space. Validation therefore includes an explicit feature-provenance audit that traces every input back to an approved predictor and confirms that no engineered feature reconstitutes the prohibited proxy from permitted variables.

### 15.8 Reproducibility and Replication of the Validation Package

The validation package is the evidentiary record on which the promotion decision rests, and it must be reproducible by a party who did not build it. The package comprises, at minimum: the conceptual soundness memorandum; the data lineage and the partition assignments derived under the §7 protocol; the persisted preprocessing artifacts; the candidate run manifests referencing the §8 roster; the computed discrimination, calibration, and fairness results; the benchmark comparisons; the sensitivity and stability findings; the feature-provenance audit; and the limitations register. Data lineage and the integrity of these records are expected to meet the principles of BCBS 239, so that the figures in the report can be traced to authoritative source data and reproduced on demand.

Reproducibility means that the environment is captured precisely enough to be reconstructed: the library versions, the random seed pinned per the §7 protocol, the data snapshot identifiers, and the exact transformation parameters. Replication is the stronger property the methodology demands of the independent reviewer: not merely re-running the developer's code, but reconstructing the result from the protocol. The methodology aligns its model lifecycle and artifact-management expectations with SR 15-18 so that the version of the model evaluated is unambiguously the version that would be promoted, and so that the registry record, including the alias used to designate the champion, refers to the exact artifact that the validation package describes.

The current model is promoted by assigning a registry alias to the validated model version rather than by moving it into a lifecycle stage. This is a deliberate departure from the superseded editions, both of which promoted by transitioning the model into a Production stage; that mechanism is retired. The current registered model name, the alias that designates the champion, the experiment under which runs are tracked, and the artifact path are all fixed in the governing sections and are not reproduced here. For historical lineage only, Edition 1 (2023) registered its model under the name meridian_risk_model_v1 with the artifact stored at path "model" and promoted via the Production stage; these identifiers are retired and must not be read as current.

### 15.9 How an Independent Reviewer Re-Derives the Reported Metrics

A central methodological requirement is that an independent reviewer, given the same protocol and the same data snapshot, can re-derive the reported metrics within numerical tolerance. The procedure is prescriptive so that re-derivation is an objective check rather than a subjective re-modeling exercise.

The reviewer begins by reconstructing the data snapshot from the lineage records, confirming the row counts and the target-maturation logic. The reviewer then regenerates the train, validation, and test partitions strictly under the §7 protocol — applying the protocol's partition fractions and pinned seed without reference to any value stated in this chapter — and confirms that the regenerated partition membership matches the membership recorded in the validation package exactly. Any discrepancy in partition membership halts the re-derivation, because divergent splits make all downstream comparisons meaningless.

With partitions confirmed, the reviewer refits the preprocessing transformations on the training partition alone and verifies that the resulting standardization parameters, imputation statistics, and categorical vocabularies match the persisted artifacts. The reviewer then instantiates each candidate from the §8 roster using the pre-registered hyperparameters, fits on the training partition, selects and confirms on the validation partition, and evaluates exactly once on the test partition. The reviewer computes the same metric families — accuracy, macro-F1, and ROC-AUC — together with the calibration analysis and the demographic-parity-difference across age_group, gender, and region, and compares each figure against the value reported by development.

Agreement is judged within a stated numerical tolerance that accommodates irreducible floating-point and platform variation; the methodology requires that the tolerance be specified in advance and that any difference exceeding it be investigated and resolved before sign-off. A re-derivation that reproduces the headline metrics but not the fairness statistics, or vice versa, is incomplete and does not satisfy the requirement. The reviewer additionally repeats the prohibited-proxy provenance audit independently, because that audit is a structural check that cannot be reduced to a metric comparison. The output of this exercise is a replication statement, signed by the reviewer, attesting either that the reported metrics were reproduced within tolerance under the governing protocol or that they were not, with the discrepancies enumerated.

### 15.10 Sign-Off and Documentation Standards

Promotion requires documented sign-off from both the first-line development owner and the independent validation function, and, where the dossier's escalation rules so require, from the model risk committee. The development owner attests that the model was built to the standards in this chapter, that the approved predictor set was respected, that the prohibited proxy was excluded, and that the run manifests faithfully describe the artifacts. The validation function attests that the independent re-derivation succeeded within tolerance, that the conceptual soundness review was satisfied, that the fairness and prohibited-proxy assessments passed against the ceilings in §11, and that the acceptance and ranking criteria in §10 were met.

Documentation standards require that the validation package be self-contained and legible to a reader who joins the process cold: a reviewer two years hence, or an examiner, must be able to reconstruct what was done and why from the record alone, without recourse to the original authors. The package must state its assumptions, its limitations, and the conditions under which the model's approval would no longer hold — connecting forward to the monitoring and rollback provisions that govern the model's life after promotion, whose triggers are fixed in the governing sections and are not reproduced here. The documentation must also align with the broader risk-management and governance expectations the institution maps to the NIST AI RMF, ensuring that the development and validation record contributes to the institution's overall account of how the model is governed, measured, and managed across its lifecycle.

Finally, the methodology requires that every sign-off be dated, attributed to a named individual with the authority to give it, and accompanied by the version identifiers of the model artifact and the validation package to which the sign-off pertains. A sign-off that does not bind to a specific, immutable artifact version is not a valid sign-off, because it cannot establish that the thing approved is the thing that will be promoted. The integrity of that binding — from validated artifact, through registry record, to the champion alias — is the methodological hinge on which the entire promotion framework turns, and it is the last thing a reviewer confirms before the record is closed.


## §16 Data Governance, Lineage, and Data Dictionary

This section establishes the data-governance regime that underpins every promotion decision rendered under this dossier. It documents the provenance of the development extract used to train and evaluate candidate consumer-credit probability-of-default (PD) classifiers, the controls that assure the integrity of that extract, the treatment of personally identifiable and protected-class information, the quarantine of the prohibited geographic proxy, and the retention, access, and reproducibility obligations that allow a promotion decision to be reconstructed years after the fact. It closes with an exhaustive data dictionary covering every column of the development extract and a conceptual treatment of the data inputs required for downstream drift monitoring. The intent throughout is that no model is promoted on the basis of data whose origin, quality, and permissibility cannot be independently re-established by Model Risk Management (MRM), Internal Audit, or an examiner.

The governing philosophy is deliberately conservative and is consistent with the institution-wide posture articulated elsewhere in this dossier: where data provenance is ambiguous, where a control is unverified, or where the fair-lending status of a field is contested, the default disposition is to exclude the field from eligible model inputs and to escalate rather than to permit. Data governance is treated here not as a precondition that is satisfied once and forgotten but as a continuous, auditable property of the modeling pipeline that must hold at training time, at the moment of promotion, and throughout the monitored life of the champion.

### 16.1 Scope and Relationship to Adjacent Sections

The data-governance controls in this section operate alongside, and do not supersede, the binding promotion criteria defined elsewhere in this dossier. Specifically, the feature-eligibility rules and the disposition of approved predictors, prohibited proxies, and protected attributes are governed by the feature governance rules in §9; the fair-lending measurement methodology, including the demographic-parity-difference statistic and the disparity ceilings applied to protected groups, is governed by §11; and the sampling, partitioning, and reproducibility protocol for constructing training, validation, and test partitions is governed by §7. This section is concerned with the lineage, quality, permissibility, and documentation of the underlying data — that is, with what the data *are* and how they came to be — and it points to the binding sections for the numeric thresholds and decision rules that act *upon* those data. Where this section describes a field as "approved as a predictor" or "excluded from model inputs," that characterization is descriptive of the field's governance classification; the operative enforcement of eligibility occurs under §9, and the operative enforcement of fairness occurs under §11.

This separation is intentional. It allows the data dictionary and lineage record to remain stable across editions even as binding thresholds are recalibrated, and it prevents the data documentation from becoming a second, possibly inconsistent, source of truth for criteria that must have exactly one authoritative location.

### 16.2 System of Record and Source Lineage

The development extract distributed with this dossier as `data.csv` is a governed, point-in-time snapshot derived from the institution's authoritative consumer-lending data estate. Its lineage is documented end-to-end so that every field can be traced from its originating system of record (SOR), through the curated feature store, to the row-and-column form in which modelers consume it.

The lineage proceeds through four logical stages:

1. **Originating systems of record.** Application and account attributes (for example, requested loan amount, stated loan purpose, declared income, and home-ownership status) originate in the loan-origination platform at the point of application. Bureau-derived attributes (credit score and the count of open trade lines) originate from consumer-reporting-agency feeds ingested under the institution's permissible-purpose controls. Performance outcomes — the realized 12-month default indicator that becomes the target — originate in the servicing and collections systems and are observed only after the performance window has fully elapsed.

2. **Ingestion and conformance layer.** Raw source records are landed in a governed ingestion zone where schema conformance, type coercion, and referential checks are applied. At this stage, source-system identifiers are preserved to support lineage but are not propagated downstream into modeling artifacts. Records that fail conformance are routed to an exception queue rather than silently dropped, so that completeness can be reconciled against the source population.

3. **Curated feature store.** Conformed records are materialized into the curated consumer-credit feature store, where business-meaningful features are computed, documented, and versioned. The feature store is the single authoritative interface between the data estate and the modeling pipeline: modelers do not query the systems of record directly. Each feature in the store carries metadata describing its source lineage, its computation logic, its refresh cadence, its owning data steward, and its governance classification (approved predictor, protected attribute, or prohibited proxy). This metadata is the substantive basis for the data dictionary in §16.9.

4. **Development extract (`data.csv`).** The development extract is produced by selecting a governed cohort from the feature store as of a defined snapshot timestamp, joining the realized target, and persisting the result as an immutable, versioned file. The extract intentionally carries the protected attributes and the prohibited geographic proxy as columns — not because they are eligible inputs, but because their presence is required for fair-lending measurement and for proxy-leakage testing, as discussed in §16.5 and §16.6.

The performance-window dependency in stage 1 is material to timeliness and to the prevention of target leakage: because the default indicator can only be known after the full observation window has matured, the snapshot logic must ensure that all feature values reflect information available at or before origination and that no post-origination information bleeds into the predictors. Lineage documentation records the as-of logic for every feature precisely so that this temporal boundary can be audited.

### 16.3 Lineage Documentation and BCBS 239 Alignment

The lineage record is maintained to satisfy the principles articulated in BCBS 239 (*Principles for effective risk data aggregation and risk reporting*), which the institution applies to model-development data even where a given extract falls below the threshold of a formal regulatory report. Three BCBS 239 principles are especially load-bearing here:

- **Accuracy and Integrity (Principle 3).** Feature computations in the curated store are reconciled against their systems of record on a defined cadence, and the development extract is checksummed and version-pinned so that the exact bytes consumed in training can be re-identified.
- **Completeness (Principle 4).** The extract's cohort selection is reconcilable to the source population, and exception-queue volumes are reported so that systematic exclusions cannot masquerade as a clean population.
- **Adaptability (Principle 6).** The feature store supports ad hoc extraction for stress testing and fair-lending deep dives without requiring changes to source systems.

The institution treats the lineage record as a governance artifact in its own right: a promotion package that cannot demonstrate an unbroken, documented chain from system of record to `data.csv` is not eligible for promotion regardless of model performance, because the absence of lineage defeats the reproducibility and challenge obligations of SR 11-7.

### 16.4 Data-Quality Controls

Data-quality controls are applied at ingestion, at feature materialization, and again at extract construction, and the results are recorded as a data-quality profile that accompanies the snapshot. The controls are organized along the conventional dimensions, each mapped to the BCBS 239 expectations and to the consequences a failure carries within this dossier.

### Completeness

Completeness controls verify that the cohort drawn into the extract reconciles to the eligible source population and that mandatory fields are populated. Null rates are computed per column and compared against documented tolerances; the disposition of nulls (imputation, exclusion, or treatment as an informative category) is recorded so that downstream behavior is reproducible. Critically, completeness is assessed not only at the cell level but at the cohort level: a systematic absence of records from a particular origination channel or time window is a completeness failure even if every retained row is fully populated, because such gaps can silently bias both performance and fairness estimates. Completeness deficiencies that bear on protected-group representation are escalated under §11 because they directly threaten the validity of the demographic-parity-difference measurement.

### Validity

Validity controls confirm that each field conforms to its declared type, domain, and business rules: numeric fields fall within plausible ranges, categorical fields take only enumerated values, and cross-field invariants hold (for example, a debt-to-income ratio is consistent with the reported income and obligations, and employment tenure is non-negative and bounded by plausible working life). Records violating hard invariants are routed to exception handling rather than coerced. Validity rules and their enumerated domains are the authoritative basis for the permissible-range column of the data dictionary.

### Timeliness

Timeliness controls confirm that the snapshot reflects an internally consistent as-of position and that no feature incorporates information dated after the modeling reference point. Because the target requires a fully matured performance window, timeliness here has a forward and a backward aspect: features must not look forward past origination, and the target must not be observed before the window closes. The snapshot timestamp and the performance-window definition are recorded in the lineage so that the temporal boundary is auditable and so that a re-run produces an identical population.

### Uniqueness

Uniqueness controls confirm that each modeling unit appears once and that there is no duplication arising from join fan-out across source systems. De-duplication logic is documented; where a single borrower could in principle contribute multiple records, the grain of the modeling unit is stated explicitly so that independence assumptions in evaluation are not silently violated. Duplicate-driven leakage between training and evaluation partitions is treated as a reproducibility defect and is incompatible with the partitioning protocol in §7.

### Data-Quality Profile and Disposition

| Dimension | Question answered | BCBS 239 principle | Failure consequence in this dossier |
|---|---|---|---|
| Completeness | Are all eligible records and mandatory fields present, and does the cohort reconcile to source? | Completeness (P4) | Escalation; potential ineligibility where protected-group coverage is compromised (see §11) |
| Validity | Does every value conform to its type, domain, and cross-field rules? | Accuracy & Integrity (P3) | Exception routing; extract not certified until resolved |
| Timeliness | Is the snapshot internally consistent and free of look-ahead? | Timeliness (P5) | Extract rejected; re-snapshot required |
| Uniqueness | Is each modeling unit represented exactly once? | Accuracy & Integrity (P3) | Reproducibility defect; incompatible with §7 partitioning |

The data-quality profile is versioned alongside the extract and is referenced by the promotion package. A model trained on an extract whose profile shows unresolved hard failures cannot be advanced; the conservative default is to fix the data and re-snapshot rather than to model around a known defect.

### 16.5 Governance of PII and Protected-Class Information

The development extract contains information that is sensitive under several overlapping regimes, and its handling is governed accordingly. Application and bureau attributes are subject to the Gramm-Leach-Bliley Act (GLBA) safeguarding and confidentiality obligations and to the permissible-purpose and accuracy expectations of the Fair Credit Reporting Act (FCRA). The protected attributes carried in the extract are subject to the anti-discrimination requirements of the Equal Credit Opportunity Act (ECOA) and its implementing Regulation B, and their handling also reflects prevailing data-privacy norms regarding data minimization and purpose limitation.

The institution applies a clear separation between **measurement use** and **input use** of protected-class information. Protected attributes — age group, gender, and region — are retained in the extract for the express and limited purpose of fair-lending measurement: they are necessary to compute the demographic-parity-difference statistic and any related disparity diagnostics across protected groups. They are *not* eligible as model inputs. This is the deliberate design: a candidate model must never consume a protected attribute as a feature, yet the institution must be able to measure the model's behavior *across* those attributes. Retaining the attributes for measurement while excluding them from inputs is the only way to satisfy both obligations simultaneously, and it is consistent with the well-established fair-lending practice of measuring outcomes by protected class without using protected class as a basis for decisioning.

The operative enforcement of this separation lives in the binding sections, not here. The rule that protected attributes are ineligible as predictors is enforced under the feature governance rules in §9; the methodology and ceilings for the fairness measurement that consumes those attributes are defined under §11. This section's role is to ensure that the data are present, correctly classified, and access-controlled so that the §9 and §11 controls can operate on trustworthy inputs.

Access to the protected attributes is governed under least-privilege principles. Personally identifiable source identifiers are stripped before the extract is materialized; the protected attributes that remain are coarsened (for example, age is represented as banded groups rather than exact date of birth) to satisfy data-minimization expectations while preserving the granularity required for meaningful disparity measurement. Access to the columns used for fair-lending measurement is restricted to MRM and the fair-lending analytics function, and access is logged. Modelers constructing candidate models operate against the approved-predictor projection of the extract, structurally reducing the opportunity for inadvertent inclusion of an ineligible field.

A point of historical contrast is informative. Earlier editions of this governance framework reflected a less mature posture on protected-attribute handling and a coarser fair-lending measurement regime: Edition 1 (2023) relied on a regional disparity ceiling that has since been retired, and Edition 2 (2024) introduced a gender-specific ceiling that was likewise superseded. Those superseded thresholds are noted here only as historical context to show the trajectory toward the present, more conservative regime; they are not operative, and the binding ceilings live exclusively in §11.

### 16.6 The Prohibited Geographic Proxy: `region_risk_index`

The extract includes a field, `region_risk_index`, that warrants specific and emphatic treatment. This field is a geographically derived risk score. Because it is constructed from location, it functions as a proxy for protected geography and, by extension, risks encoding the very disparities that fair-lending law is designed to prevent — it can act as a conduit for redlining-type effects even when no protected attribute is used directly as an input. For that reason it is classified as a **prohibited proxy** and is quarantined from all eligible models.

Quarantine, in this context, has a precise operational meaning. The field is *retained in lineage and in the extract* so that it can be subjected to proxy-leakage testing — that is, so the institution can affirmatively verify that approved predictors do not reconstruct the prohibited signal and that the field's relationship to protected attributes and to the target can be characterized. But the field is *excluded from the approved-predictor projection* that modelers consume, it must never appear as a model input, and its presence in a candidate's feature set is a disqualifying condition. The distinction mirrors the treatment of protected attributes: retention for measurement and testing is permitted and indeed required; use as an input is prohibited.

The reason the field is kept rather than simply deleted is that deletion would destroy the institution's ability to *test for* proxy leakage. If `region_risk_index` were absent, MRM could not check whether a combination of permitted features inadvertently reconstructs the geographic risk signal. By keeping the field quarantined and instrumented, the institution can run leakage diagnostics that compare model behavior against the prohibited signal and flag any approved-predictor combination that correlates with it beyond tolerance. The eligibility rule that bars this field as an input is enforced under §9; this section documents the field's lineage role, its rationale for retention, and its quarantine status. Any change to the field's classification would itself be a governance event requiring re-approval and would not be effected through data documentation alone.

### 16.7 Retention, Access Control, and Reproducibility

Reproducibility is a first-class obligation under SR 11-7 and is operationalized through three commitments: immutability of the snapshot, controlled access, and durable retention.

**Immutability and versioning.** The development extract is persisted as an immutable, version-pinned artifact identified by a content checksum. Once certified, the bytes do not change; a correction produces a new versioned snapshot rather than an in-place edit. The exact snapshot version, its checksum, the snapshot timestamp, the performance-window definition, and the accompanying data-quality profile are recorded in the promotion package so that the data underlying any promotion decision can be re-identified and reconstructed. This is what makes the partitioning protocol in §7 meaningful: a fixed, reproducible split is only fixed if the underlying data it partitions are themselves fixed.

**Access control.** Access follows least-privilege and is segregated by role. The approved-predictor projection is available to modelers; the protected attributes and the quarantined proxy are restricted to MRM and fair-lending analytics for measurement and leakage testing; raw source identifiers are not propagated into the modeling estate at all. All access to sensitive columns is logged, and the logs are retained as part of the audit trail.

**Retention.** The snapshot, its lineage record, its data-quality profile, and the associated access logs are retained for the full governance retention period applicable to model-risk records, so that a promotion decision remains reconstructible across editions and through examination cycles. Retention is aligned to the institution's records schedule and to the expectation that a superseded champion's full development context remains available for as long as the model's decisions continue to carry regulatory or litigation relevance.

For historical orientation, earlier editions persisted development data with weaker reproducibility guarantees: the Edition 1 (2023) and Edition 2 (2024) practices did not uniformly checksum and version-pin the development extract, which complicated after-the-fact reconstruction. The present regime closes that gap and treats reconstructibility as a precondition of eligibility.

### 16.8 Notes on the Target and Cohort Construction

The target column, `default`, is the realized 12-month probability-of-default outcome expressed as a binary indicator. Two governance properties of the target deserve emphasis. First, the target is observed only after the performance window has matured, which is why the snapshot's timeliness controls (see §16.4) are designed to prevent both look-ahead in the features and premature observation of the outcome. Second, the prevalence of the positive class is recorded in the data-quality profile because class balance materially affects both performance metrics and fairness diagnostics; any material shift in prevalence between development and the monitored population is a drift signal (see §16.10). The cohort is defined at a stated modeling grain — one row per origination decision within the snapshot window — and the uniqueness controls guarantee that this grain is not violated by join fan-out.

### 16.9 Data Dictionary

The following data dictionary documents every column present in the development extract. The **Role** column gives each field's governance classification under this dossier: *approved predictor* (eligible as a model input, subject to §9), *prohibited proxy* (quarantined; never an input), *protected attribute* (retained for measurement only; never an input), or *target* (the outcome being modeled). The permissible-range and category specifications are the authoritative domains used by the validity controls in §16.4. Fair-lending sensitivity notes flag considerations relevant to ECOA/Regulation B and to the disparity measurement governed by §11.

#### Approved Predictors

| Column | Data type | Description | Permissible range / categories | Role | Fair-lending sensitivity notes |
|---|---|---|---|---|---|
| `income` | Numeric (continuous) | Applicant's verified or stated gross annual income at origination, used as a measure of repayment capacity. | Non-negative; bounded by documented plausibility limits; outliers routed to validity review. | Approved predictor | Income can correlate with protected characteristics; permitted as a legitimate capacity measure but its disparate-impact contribution is observable through §11 diagnostics. |
| `loan_amount` | Numeric (continuous) | Requested or approved principal of the consumer-credit loan. | Non-negative; bounded by product limits. | Approved predictor | Low direct sensitivity; monitored for interaction effects that could correlate with protected geography. |
| `dti_ratio` | Numeric (continuous) | Debt-to-income ratio capturing existing obligations relative to income; a core capacity feature. | Non-negative; cross-validated for consistency with `income` and obligations. | Approved predictor | Capacity measure with recognized business justification; included in disparate-impact review. |
| `credit_score` | Numeric (continuous/ordinal) | Bureau-derived consumer credit score reflecting prior credit behavior. | Within the standard bounded score range defined by the bureau; nulls dispositioned per §16.4. | Approved predictor | Subject to FCRA accuracy/permissible-purpose controls at source; can embed historical disparities, so its impact is measured under §11. |
| `employment_years` | Numeric (continuous) | Length of current or aggregate employment tenure, as a stability indicator. | Non-negative; bounded by plausible working life. | Approved predictor | May correlate with age; because age is protected, leakage of an age signal through tenure is monitored. |
| `num_open_accounts` | Numeric (integer count) | Count of open credit trade lines at origination, indicating credit footprint. | Non-negative integer; bounded by plausibility limits. | Approved predictor | Low direct sensitivity; reviewed for proxy interactions. |
| `home_ownership` | Categorical | Applicant's housing tenure status (e.g., own, mortgage, rent), as a stability/asset signal. | Enumerated category set defined by the feature store; unknowns handled per validity rules. | Approved predictor | Can correlate with wealth and protected geography; included in disparate-impact monitoring. |
| `loan_purpose` | Categorical | Stated purpose of the requested credit (e.g., consolidation, purchase, other). | Enumerated category set defined by the feature store. | Approved predictor | Generally low direct sensitivity; reviewed for category-level disparities. |

#### Prohibited Proxy

| Column | Data type | Description | Permissible range / categories | Role | Fair-lending sensitivity notes |
|---|---|---|---|---|---|
| `region_risk_index` | Numeric (continuous) | Geographically derived composite risk score for the applicant's location. | Bounded continuous score as computed by the feature store. | Prohibited proxy | High sensitivity. Acts as a proxy for protected geography and a potential conduit for redlining-type disparate impact. Quarantined from all eligible models; retained solely for proxy-leakage testing (see §16.6). Never a model input; enforcement under §9. |

#### Protected Attributes

| Column | Data type | Description | Permissible range / categories | Role | Fair-lending sensitivity notes |
|---|---|---|---|---|---|
| `age_group` | Categorical (banded) | Applicant age expressed as coarsened bands rather than exact age, for data minimization. | Enumerated age bands defined for fair-lending measurement. | Protected attribute | Protected under ECOA/Regulation B. Retained for measurement only; never a model input. Used to compute demographic-parity-difference under §11. |
| `gender` | Categorical | Applicant gender as recorded for fair-lending measurement. | Enumerated category set. | Protected attribute | Protected under ECOA/Regulation B. Retained for measurement only; never a model input. Edition 2 (2024) applied a now-retired gender disparity ceiling; current ceilings are governed by §11. |
| `region` | Categorical | Applicant geographic region used for fair-lending measurement (distinct from the prohibited derived risk index). | Enumerated region set. | Protected attribute | Protected/geographic-sensitivity dimension. Retained for measurement only; never a model input. Edition 1 (2023) applied a now-retired regional ceiling; current treatment is governed by §11. |

#### Target

| Column | Data type | Description | Permissible range / categories | Role | Fair-lending sensitivity notes |
|---|---|---|---|---|---|
| `default` | Binary indicator | Realized 12-month default outcome, observed after the performance window matures. | {0, 1}. | Target | Not an input. Class prevalence recorded in the data-quality profile; prevalence shifts are a drift signal (see §16.10). The target's joint distribution with protected attributes underpins fairness diagnostics in §11. |

Three classification rules are worth restating because they are the crux of this section's governance contribution. First, the approved predictors are the *only* fields eligible to be consumed as model inputs, and that eligibility is enforced under §9. Second, the protected attributes and the prohibited proxy are present in the extract for measurement and testing but are never inputs — their retention is a fair-lending and proxy-testing necessity, not a license to use them in scoring. Third, the target is the outcome, not a feature, and its temporal maturity is the reason the snapshot's timeliness controls exist.

### 16.10 Data Inputs for Drift Monitoring (Conceptual)

Once a champion is promoted via its MLflow alias, the data-governance regime does not end; it extends into ongoing monitoring. This subsection describes, at a conceptual level, the data inputs required to monitor for drift; the binding thresholds, cadences, and rollback triggers that act upon these signals are defined in the binding sections and are not restated here.

Drift monitoring consumes three conceptually distinct data inputs. **Input drift (covariate drift)** is assessed by comparing the distribution of each approved predictor in the live scoring population against its distribution in the development snapshot; a material shift in, for example, the income or credit-score distribution indicates that the population the champion is scoring no longer resembles the population it was developed on. **Prediction drift** is assessed by tracking the distribution of the model's PD outputs over time, independent of realized outcomes, which provides an early signal before the performance window for new originations has matured. **Outcome and performance drift** is assessed once realized defaults become observable, comparing live performance and the class prevalence against the development baseline recorded in the data-quality profile.

Crucially, drift monitoring also has a fair-lending dimension. Because the protected attributes are retained, the institution can monitor not only aggregate drift but also whether the relationships among predictors, predictions, and protected groups are shifting in ways that could erode the fairness properties established at promotion. A model that remains accurate in aggregate while its disparity profile deteriorates is exactly the failure mode that retaining protected attributes for measurement is designed to catch. Likewise, the quarantined proxy continues to serve a monitoring role: live data can be tested to confirm that no drift in approved predictors has begun to reconstruct the prohibited geographic signal.

For monitoring to be meaningful, the live data must traverse the same lineage and quality controls as the development extract: the same feature definitions, the same validity domains, and the same as-of discipline. A drift signal computed against inconsistently constructed live data is uninterpretable. Accordingly, the monitoring data inputs are themselves governed under the lineage and data-quality controls described in §16.2 through §16.4, closing the loop between development-time and run-time data governance. The numeric thresholds at which any of these signals trigger investigation, recalibration, or rollback are defined in the binding sections of this dossier and are intentionally not duplicated here.

### 16.11 Summary

The data underlying any promotion under this dossier is governed as a traceable, quality-controlled, access-restricted, and reproducible asset. Every field in the development extract is documented, classified, and dispositioned: approved predictors are the sole eligible inputs; protected attributes and the prohibited geographic proxy are retained for measurement and proxy-leakage testing but never used as inputs; and the target is the matured outcome whose temporal properties dictate the snapshot's timeliness controls. The lineage from system of record through the curated feature store to `data.csv` is documented to BCBS 239 expectations, and the snapshot is immutable, checksummed, and retained so that a promotion decision can be reconstructed long after it is made. This section supplies the data foundation; the binding sections — notably §7 for sampling and partitioning, §9 for feature eligibility, and §11 for fair-lending measurement and ceilings — supply the operative rules that act upon that foundation.


## §17 Feature Governance Committee Proceedings and Proxy Analysis

### 17.1 Purpose and Standing of This Section

This section records the charter, standing membership, adjudication standards, and minuted proceedings of the Feature Governance Committee (FGC) as they pertain to the consumer-credit 12-month probability-of-default classifier governed by this dossier. It is descriptive and procedural. Where a feature-level rule is binding — for example, the enumerated set of approved predictors, the explicit prohibition of geographic proxy variables, or the treatment of protected attributes — the binding statement of record lives in the feature governance rules in §9 and is not reproduced here. This section explains how the Committee reached those positions, why each approved predictor cleared the bar, and why one candidate variable was rejected as a presumptively impermissible proxy. Readers seeking the controlling values should follow the pointers to §9; readers seeking the reasoning, evidentiary basis, and deliberative history will find it below.

The FGC is one of three standing technical committees that feed the Model Risk Management Committee (MRMC). Its sister committees — the Performance & Calibration Committee (governing the metrics regime in §6–§8) and the Fair Lending Committee (governing the fairness ceilings in §11) — operate in parallel and share overlapping membership by design, so that a candidate predictor's predictive merit, its fair-lending footprint, and its governance disposition are never adjudicated in isolation.

### 17.2 Mandate

The Committee's mandate is to determine, for the consumer-credit PD model, which input variables are permissible for use in credit decisioning, on what conditions, and with what monitoring obligations. Concretely, the FGC:

1. Maintains the canonical roster of approved predictors and the canonical roster of prohibited variables, both of which are codified in §9.
2. Adjudicates each candidate predictor against the four standing criteria set out in §17.3, producing a written disposition and a recorded vote.
3. Classifies every attribute that the model could in principle ingest into one of three regulatory categories — *approved predictor*, *protected attribute* (age_group, gender, region), or *prohibited variable* — and ensures that no protected attribute is ever used as a direct model input, and that no prohibited variable is reintroduced under a renamed or re-engineered guise.
4. Conducts and documents proxy analysis: the empirical investigation of whether a candidate predictor, though facially neutral, functions as a stand-in for a protected attribute and therefore carries disparate-impact risk.
5. Reviews any business-necessity justification advanced in favor of a variable that fails the fair-lending safety criterion, together with the search for a less-discriminatory alternative, and records whether that justification was accepted or rejected.
6. Escalates unresolved disputes, and any proposal to add or remove a predictor, to the MRMC for ratification.

The FGC does not set performance thresholds, does not own the data splitting protocol, and does not approve the model for promotion. Its remit ends at the boundary of the feature set. Promotion remains a function of the alias-based registry workflow described elsewhere in this dossier.

### 17.3 Standing Adjudication Criteria

A candidate predictor is approved for credit decisioning only if it satisfies all four of the following standing criteria. The criteria are conjunctive: failure on any one is disqualifying, and no amount of strength on the other three can cure it. This conjunctive structure is deliberate and reflects the institution's conservative posture toward consumer-credit decisioning.

**Criterion 1 — Causality and business justifiability.** The predictor must bear a defensible, articulable relationship to a borrower's ability or willingness to repay. The Committee does not require proof of strict causation, which is rarely attainable in credit data, but it does require a credit-theoretic rationale that a reasonable underwriter would recognize as legitimate. Variables that predict default only through an opaque or socially suspect channel — for instance, a variable whose predictive power evaporates once a borrower's actual financial capacity is controlled for — fail this criterion even if they are statistically significant.

**Criterion 2 — Stability.** The predictor must be stable across time, across data refreshes, and across the population segments the model serves. The Committee reviews population stability metrics, the rate of missingness and its mechanism, vintage-over-vintage drift, and the degree to which the variable's distribution is sensitive to operational or seasonal artifacts. A predictor that is informative in one vintage and inverted in the next is not a sound basis for decisioning.

**Criterion 3 — Fair-lending safety.** The predictor must not function as a proxy for a protected attribute, and its inclusion must not by itself drive the model's demographic-parity-difference toward or beyond the fairness ceilings owned by the Fair Lending Committee in §11. The Committee examines the association between the candidate and each protected attribute (age_group, gender, region), the marginal change in disparate-impact metrics attributable to the candidate, and whether the variable would survive a disparate-impact challenge. This is the criterion on which the prohibited geographic proxy failed.

**Criterion 4 — Explainability.** The predictor's contribution to a given decision must be explainable to a borrower in plain language sufficient to support an adverse-action notice, and to an examiner in technical detail sufficient to support a fair-lending examination. A variable whose effect on the score cannot be rendered intelligible — whether because it is an inscrutable composite or because its directionality is unstable — fails this criterion.

A predictor that clears all four criteria is approved subject to ongoing monitoring; approval is never permanent and is revisited at each edition of this dossier and whenever a material drift event is logged.

### 17.4 Membership and Quorum

The Committee is chaired by the Head of Model Risk Management and comprises the following standing voting members. Roles are listed; named incumbents are maintained in the MRM personnel register and are not reproduced here.

| Seat | Function represented | Voting |
| --- | --- | --- |
| Chair | Head of Model Risk Management | Yes (casting vote on ties) |
| Vice-Chair | Lead Quantitative Model Validator | Yes |
| Member | Fair Lending Officer (Compliance) | Yes |
| Member | Consumer Credit Underwriting Policy Lead | Yes |
| Member | Data Governance & Lineage Lead | Yes |
| Member | Lead Data Scientist, Credit Models | Yes |
| Member | Senior Counsel, Regulatory & Fair Lending Law | Yes |
| Advisor | Model Development Manager (sponsoring line) | No (non-voting) |
| Secretary | MRM Governance Analyst | No (records minutes) |

Quorum requires five voting members present, of whom at least one must be the Fair Lending Officer or Senior Counsel, so that no feature disposition with fair-lending implications is taken without a compliance or legal voice in the room. Decisions are by simple majority of those present and voting; the Chair holds a casting vote in the event of a tie. A prohibition decision — the act of placing a variable on the prohibited roster — requires, by Committee bylaw, an affirmative vote with no more than one dissent, reflecting the gravity and the difficulty of reversing such a designation once downstream pipelines have been built to exclude the variable.

### 17.5 Feature-by-Feature Adjudication Narrative

The eight approved predictors below constitute the complete authorized input set for the consumer-credit PD model; the canonical, binding enumeration is in §9. The narratives that follow explain the Committee's reasoning against the four standing criteria. Each was approved subject to monitoring.

#### 17.5.1 income

Borrower income is the most direct available measure of repayment capacity and is the textbook example of a justifiable credit predictor (Criterion 1 satisfied on its face). The Committee examined stability across vintages and found income distributions stable after standard winsorization of the upper tail; missingness was low and, where present, traceable to a documented intake mechanism rather than a non-random pattern correlated with a protected class (Criterion 2). On fair-lending safety, the Committee noted that income does carry some association with protected attributes in the underlying population — a known feature of consumer-credit data generally — but found that the association did not rise to proxy status: income retains independent, credit-theoretic predictive power for repayment after conditioning on protected attributes, and its marginal contribution to the model's demographic-parity-difference was within tolerances owned by §11 (Criterion 3). Income is straightforwardly explainable in an adverse-action context (Criterion 4). **Disposition: approved.**

#### 17.5.2 loan_amount

The requested loan amount bears directly on the size of the repayment obligation relative to capacity and is a standard underwriting input (Criterion 1). The Committee reviewed its stability and confirmed it is an applicant-supplied, operationally clean field with negligible drift (Criterion 2). On fair-lending safety, loan_amount is most informative in conjunction with income and dti_ratio rather than in isolation; the Committee confirmed it does not act as a geographic or demographic proxy and that its standalone disparate-impact footprint is immaterial (Criterion 3). It is readily explainable (Criterion 4). The Committee noted one monitoring obligation: because loan_amount interacts with loan_purpose, the joint distribution is to be reviewed at each vintage to ensure no purpose-by-amount interaction reintroduces a protected-class association. **Disposition: approved with interaction monitoring.**

#### 17.5.3 dti_ratio

Debt-to-income ratio is among the most defensible predictors in the set, encoding repayment burden as a normalized quantity that is robust across income levels (Criterion 1). It is stable, with well-understood bounds and a clear treatment for the small number of degenerate cases (zero or undefined denominators), which are handled by a documented rule rather than silent imputation (Criterion 2). Because dti_ratio is a ratio of two financial quantities, it tends to *reduce* rather than introduce demographic skew relative to using income alone, and the Committee found its fair-lending footprint favorable (Criterion 3). It is highly explainable and maps cleanly to adverse-action reason codes (Criterion 4). **Disposition: approved.**

#### 17.5.4 credit_score

A bureau credit score is a purpose-built, externally governed measure of credit risk and is the most directly relevant single predictor of default (Criterion 1). The Committee noted that the score is itself a regulated artifact produced under its own fair-lending regime, and reviewed third-party documentation on its construction. Stability is high and the field is operationally reliable (Criterion 2). On fair-lending safety, the Committee acknowledged the well-documented industry concern that bureau scores can encode historical disparities; it reviewed the marginal disparate-impact contribution of credit_score in the current model and found it within the §11 tolerances, and recorded an explicit ongoing-monitoring obligation given the variable's sensitivity (Criterion 3). It is explainable to borrowers via standard reason-code frameworks (Criterion 4). **Disposition: approved with heightened monitoring.**

#### 17.5.5 employment_years

Length of employment is a recognized proxy for income stability and willingness/ability to sustain repayment over the loan term, and is justifiable on standard underwriting grounds (Criterion 1). The Committee scrutinized this variable more closely than the financial measures because tenure variables can, in some populations, correlate with age_group. It reviewed the association and found that employment_years, as binned and used by the model, did not exhibit a sufficiently strong or monotone relationship with age_group to constitute a proxy, and that its incremental disparate-impact contribution was within tolerance (Criterion 3); the Committee nonetheless attached an explicit monitoring obligation to track the employment_years/age_group association at each vintage. Stability is good with a documented treatment for the right-censored long-tenure cases (Criterion 2). It is explainable (Criterion 4). **Disposition: approved with age-association monitoring.**

#### 17.5.6 num_open_accounts

The number of open credit accounts is an accepted measure of credit utilization breadth and exposure, informative about a borrower's existing obligations (Criterion 1). The Committee found it stable, with a clear definition and low missingness (Criterion 2). Its fair-lending footprint was reviewed and found immaterial; it does not function as a proxy and its marginal disparate-impact contribution is small (Criterion 3). The Committee noted that the variable is moderately explainable — borrowers understand the count, though the directionality (more accounts can be favorable or unfavorable depending on context) requires care in adverse-action language — and recorded that reason-code copy must be reviewed to ensure intelligibility (Criterion 4). **Disposition: approved with reason-code-language review.**

#### 17.5.7 home_ownership

Home-ownership status is a recognized indicator of financial stability and asset position (Criterion 1). This variable received extended discussion because of its potential entanglement with both region and historical lending patterns. The Committee examined the association between home_ownership and the protected attribute region and confirmed that, while a modest association exists, it is materially weaker than the association observed for the prohibited geographic proxy (see §17.6) and does not approach proxy status; the variable carries genuine, independent credit-theoretic signal about asset backing and stability (Criterion 3). Stability is good and the categories are clean (Criterion 2). It is explainable (Criterion 4). The Committee recorded that home_ownership is to be monitored jointly with region at each vintage and that any future strengthening of that association would trigger re-adjudication. **Disposition: approved with region-association monitoring.**

#### 17.5.8 loan_purpose

The stated purpose of the loan is an accepted underwriting input because different purposes carry materially different default profiles (Criterion 1). The Committee reviewed the category taxonomy to ensure that no purpose category functions as a covert demographic or geographic signal, and confirmed the categories are defined by financial use rather than by any characteristic correlated with a protected class (Criterion 3). Stability is good, with a documented treatment for rare and "other" categories (Criterion 2). It is explainable (Criterion 4). As noted under loan_amount, the loan_purpose-by-amount interaction is subject to joint monitoring. **Disposition: approved with interaction monitoring.**

### 17.6 Extended Proxy Analysis: region_risk_index

The variable region_risk_index — a continuous index summarizing aggregate credit-risk characteristics of a borrower's geographic area — was advanced by the sponsoring development line as a candidate predictor. The Committee subjected it to its most extensive proxy analysis on record and rejected it. The binding prohibition is stated in §9; this subsection records the analysis and reasoning that produced it.

#### 17.6.1 Why a proxy analysis was triggered

region_risk_index is facially neutral: it does not name a protected class, and it is constructed from aggregate area-level credit statistics rather than from any individual's demographic attributes. But facial neutrality is precisely the condition under which proxy risk is most dangerous, because a variable that *functions* as a stand-in for a protected attribute can transmit disparate impact while appearing innocuous in a feature list. Because the index is constructed at the geographic level, and because region is itself a protected attribute under this dossier, the Committee treated geographic entanglement as the presumptive hypothesis to be disproven rather than as an objection to be raised only if evidence happened to surface.

#### 17.6.2 Correlation with the protected attribute region

The central finding is that region_risk_index is, by construction, a deterministic function of geography. Because the index is computed at the area level and every borrower in a given area receives that area's index value, the variable does not merely correlate with region — it is, in the limit, recoverable from region. The Committee reviewed the empirical association between region_risk_index and the protected attribute region and found it overwhelming: the index value was almost entirely explained by region membership, with the area-level construction meaning that knowing a borrower's region was sufficient to reconstruct the index to within rounding. This is a qualitatively different and far stronger relationship than the modest associations observed for home_ownership or employment_years, which retain substantial within-group variation and independent credit signal. region_risk_index has essentially no within-region variation by design.

#### 17.6.3 Disparate-impact risk introduced

A variable that is recoverable from a protected attribute imports the full distribution of that protected attribute's historical disparities into the model. The Committee's analysis showed that including region_risk_index materially worsened the model's demographic-parity-difference with respect to region, pushing it toward and, in the configurations tested, beyond the fairness ceilings owned by §11. Crucially, the mechanism was not incidental: the variable worsened parity *because* it encoded region, not despite it. The Committee characterized this as the variable functioning as a near-perfect geographic proxy — the model could decision on region while never naming it, which is the precise harm the protected-attribute regime exists to prevent. The Fair Lending Officer recorded that this pattern is the classic signature of redlining-by-proxy and that the variable would not survive a disparate-impact challenge.

#### 17.6.4 Statistical evidence reviewed

The Committee reviewed the following lines of evidence, each pointing in the same direction:

| Evidence reviewed | Finding |
| --- | --- |
| Association of region_risk_index with region | Near-deterministic; index recoverable from region by construction |
| Within-region variance of the index | Negligible — confirms the variable carries little information beyond geography |
| Marginal change in demographic-parity-difference (region) from adding the index | Materially adverse; moved the metric toward/over the §11 ceilings |
| Predictive lift after conditioning on the approved predictors | Minimal — the index added little incremental default-prediction once income, dti_ratio, credit_score, etc. were present |
| Reconstruction test: predict region from the index | High recoverability, confirming proxy status |
| Stability of the index's effect direction across vintages | Inconsistent, compounding the fair-lending concern |

The conditioning result in the fourth row was decisive on the predictive side: once the genuine ability-to-repay measures were in the model, region_risk_index contributed little independent default signal. In other words, the variable's apparent predictive value was largely a re-expression of geography rather than of repayment capacity — failing Criterion 1 (no defensible repayment-causal channel) at the same time it failed Criterion 3 (fair-lending safety).

#### 17.6.5 Business-necessity and less-discriminatory-alternative analysis

Under fair-lending doctrine, a facially neutral practice that produces disparate impact may nonetheless be permissible if it is justified by business necessity and there is no less-discriminatory alternative that serves the same legitimate objective. The sponsoring line advanced a business-necessity argument: that region_risk_index improved default prediction and therefore protected the safety and soundness of the lending portfolio. The Committee tested this argument on its own terms and rejected it for two independent reasons.

First, the business-necessity prong failed on the evidence. The conditioning analysis (above) showed that the index added minimal incremental predictive value once the approved ability-to-repay predictors were present. A variable that does not meaningfully improve prediction cannot be a business necessity; there is no legitimate objective that it uniquely serves.

Second, even had a predictive benefit existed, the less-discriminatory-alternative prong failed. The legitimate objective the index purported to serve — accurate assessment of individual repayment risk — is already and more appropriately served by the approved individual-level predictors (income, loan_amount, dti_ratio, credit_score, employment_years, num_open_accounts, home_ownership, loan_purpose), which measure the borrower's own circumstances rather than the aggregate characteristics of the borrower's neighbors. Individual-level repayment measures are a manifestly less-discriminatory alternative that achieves the same legitimate aim without importing geographic disparity. The existence of that alternative is, by itself, dispositive.

The Committee therefore concluded that region_risk_index is a presumptively impermissible geographic proxy, that no business-necessity justification rehabilitates it, and that a less-discriminatory alternative exists and is already in use. It was placed on the prohibited roster, and the binding prohibition — including the obligation to prevent its reintroduction under any re-engineered or renamed form — is recorded in §9.

#### 17.6.6 Historical context: the Edition 1 precedent

The Committee noted that this was not the institution's first encounter with geographic proxy risk. The Edition 1 model (retired), named meridian_risk_model_v1 and registered to the artifact path `model`, incorporated a geographic risk feature of similar construction. That model was developed under a less mature governance regime — it was evaluated under a ranking-accuracy primary metric, with retired thresholds of 0.80 accuracy and 0.82 AUC, on an 80/10/10 split at seed 7, and against a regional fairness ceiling of 0.20 that has since been superseded. The geographic feature in that model was subsequently identified as a disparate-impact vector and the model was rejected and retired. The Edition 2 regime (also retired) tightened the framework further — moving to a 70/15/15 split at seed 13, a macro-F1 ranking bar of 0.75, and a gender ceiling of 0.06 — but it was the Edition 1 episode that first crystallized the institution's position that geographic indices must be treated as presumptive proxies. The current edition codifies that lesson as a standing prohibition rather than a case-by-case finding.

### 17.7 Disposition Summary Table

The following table summarizes the Committee's disposition for every variable it adjudicated for the current edition. Approved predictors are authorized inputs; the protected attributes are listed to record that they are never used as direct inputs; the prohibited variable is listed with its proxy basis. The binding enumeration governs and is in §9.

| Variable | Regulatory category | Disposition | Primary basis / monitoring obligation |
| --- | --- | --- | --- |
| income | Approved predictor | Approved | Direct repayment capacity; independent signal after conditioning |
| loan_amount | Approved predictor | Approved (monitored) | Repayment obligation size; monitor purpose-by-amount interaction |
| dti_ratio | Approved predictor | Approved | Normalized repayment burden; reduces demographic skew |
| credit_score | Approved predictor | Approved (heightened monitoring) | Purpose-built risk measure; monitor disparate-impact contribution |
| employment_years | Approved predictor | Approved (monitored) | Income-stability proxy; monitor age_group association |
| num_open_accounts | Approved predictor | Approved (monitored) | Exposure breadth; review adverse-action reason-code language |
| home_ownership | Approved predictor | Approved (monitored) | Asset/stability signal; monitor region association |
| loan_purpose | Approved predictor | Approved (monitored) | Purpose-specific default profile; monitor amount interaction |
| age_group | Protected attribute | Not an input | Fairness-monitored only; never a direct model input |
| gender | Protected attribute | Not an input | Fairness-monitored only; never a direct model input |
| region | Protected attribute | Not an input | Fairness-monitored only; never a direct model input |
| region_risk_index | Prohibited variable | Prohibited | Geographic proxy for region; disparate impact; no business necessity (see §9) |

### 17.8 Selected Meeting Minutes

The following are extracts from the Committee's minute book covering the deliberations that produced the dispositions above. Full minutes are retained in the MRM governance archive; these extracts record the substance and the recorded votes.

#### 17.8.1 Minutes — 2025-03-12 (FGC-2025-02)

Present: Chair, Vice-Chair, Fair Lending Officer, Underwriting Policy Lead, Data Governance Lead, Lead Data Scientist, Senior Counsel (quorum satisfied; compliance and legal present).

The Chair opened the review of the candidate predictor set for the forthcoming edition. The Lead Data Scientist presented the eight financial and account-level candidates against the four standing criteria. Discussion focused on employment_years and home_ownership, both flagged by the Fair Lending Officer for potential protected-attribute entanglement (age_group and region respectively). The Committee reviewed the association statistics presented by Data Governance and was satisfied that both variables retained substantial independent credit signal and did not approach proxy status, but directed that explicit per-vintage association monitoring be attached to each.

The sponsoring line requested that region_risk_index be added to the agenda as a candidate. The Fair Lending Officer objected that any area-level geographic index must undergo full proxy analysis before the Committee could entertain it, citing the Edition 1 precedent. The Committee agreed and tabled region_risk_index pending a dedicated proxy analysis.

Resolved: income, loan_amount, dti_ratio, credit_score, num_open_accounts, and loan_purpose provisionally approved against all four criteria, subject to the monitoring obligations recorded. employment_years and home_ownership provisionally approved subject to association monitoring. region_risk_index tabled for dedicated proxy analysis. Vote: 7–0 in favor.

#### 17.8.2 Minutes — 2025-06-18 (FGC-2025-05)

Present: Chair, Vice-Chair, Fair Lending Officer, Underwriting Policy Lead, Data Governance Lead, Lead Data Scientist, Senior Counsel; Model Development Manager attending (non-voting).

The sole substantive item was the proxy analysis of region_risk_index. Data Governance presented the association evidence: the index was shown to be recoverable from region by construction, with negligible within-region variance. The Lead Data Scientist presented the conditioning analysis showing minimal incremental predictive lift once the approved ability-to-repay predictors were present, and the marginal disparate-impact analysis showing the index moved demographic-parity-difference with respect to region adversely, toward and beyond the §11 ceilings.

The Model Development Manager advanced the business-necessity argument that the index improved portfolio safety and soundness. Senior Counsel and the Fair Lending Officer responded that the business-necessity prong failed on the evidence given the minimal predictive lift, and that in any event a less-discriminatory alternative — the individual-level approved predictors already in the model — fully served the legitimate objective. The Committee deliberated at length and recorded its concern that the variable was a textbook redlining-by-proxy vector.

Resolved: region_risk_index is a presumptively impermissible geographic proxy. Business-necessity justification rejected; less-discriminatory alternative found to exist. The variable is to be placed on the prohibited roster with an obligation to prevent reintroduction under any renamed or re-engineered form. Recommendation forwarded to MRMC for ratification and codification in §9. Vote: 7–0 in favor (prohibition bylaw threshold of no more than one dissent satisfied).

#### 17.8.3 Minutes — 2025-10-09 (FGC-2025-09)

Present: Chair, Vice-Chair, Fair Lending Officer, Underwriting Policy Lead, Data Governance Lead, Lead Data Scientist (quorum satisfied; Fair Lending Officer present).

Item 1 — Reintroduction watch. Data Governance reported that an area-level "neighborhood economic indicator" had appeared in an upstream feature store under a different name. The Committee examined its construction, determined it was substantively equivalent to the prohibited geographic proxy, and directed that it be excluded from the model's feature pipeline and flagged to upstream owners. The Committee reaffirmed that the prohibition in §9 attaches to function and construction, not merely to the literal variable name.

Item 2 — Monitoring readback. The Committee reviewed the first-vintage readback of the association-monitoring obligations attached to employment_years, home_ownership, and credit_score. All three remained within the bounds that supported their approval. No re-adjudication triggered.

Resolved: the renamed neighborhood indicator is confirmed as a prohibited proxy and excluded. Monitoring obligations confirmed as operating. Vote: 6–0 in favor.

#### 17.8.4 Minutes — 2026-01-08 (FGC-2026-01)

Present: Chair, Vice-Chair, Fair Lending Officer, Underwriting Policy Lead, Data Governance Lead, Lead Data Scientist, Senior Counsel.

Edition 3 closeout. The Committee conducted its final review of the predictor set and dispositions ahead of the edition's effective date. It confirmed the eight approved predictors, their monitoring obligations, and the prohibition of region_risk_index, and ratified the disposition summary table reproduced in §17.7. The Committee noted that the binding statements of the approved roster and the prohibition are recorded in §9 and that this section is the supporting deliberative record. Senior Counsel confirmed the proxy analysis and the failed business-necessity/less-discriminatory-alternative analysis were documented to a standard adequate to support a fair-lending examination.

Resolved: the feature governance dispositions for Edition 3 are finalized as recorded. Forwarded to MRMC for edition ratification. Vote: 7–0 in favor.

### 17.9 Closing Note

The Committee's standing position, reaffirmed at each session above, is that conservative feature governance is cheaper than remediation. A predictor admitted in error propagates into every decision the model makes and into every adverse-action notice it generates; a proxy admitted in error transmits disparate impact silently and at scale. The four-criterion conjunctive test, the presumptive treatment of geographic indices as proxies, and the bylaw requiring near-unanimity for a prohibition all exist to make the admission of a harmful variable difficult and its exclusion durable. The binding consequences of these proceedings — the approved roster and the prohibition of region_risk_index — are recorded in the feature governance rules in §9.


## §18 Fair Lending and Disparate-Impact Assessment Methodology

This section sets out the methodology by which Meridian Financial, N.A. ("Meridian," "the Bank") measures and adjudicates the fair-lending posture of any consumer-credit 12-month probability-of-default (PD) classifier proposed for promotion into the production model registry. It is a methodology chapter: it describes *how* fairness is measured, *why* the chosen statistic was adopted, *who* holds adjudication authority, and *what* happens when a candidate fails. It deliberately does not restate the current binding numeric criteria. Those acceptance thresholds — including the per-attribute disparity ceilings, the standard decision threshold, and the minimum predictive-quality bars — are maintained as the single authoritative source in §6 through §13, and in particular the fairness ceilings live in §11. Wherever this section needs to invoke a binding limit, it does so by pointer to §11 rather than by repeating a number. Any numeric value that appears in the body of this section is either (a) an explicitly retired threshold from a superseded edition, presented as historical record, or (b) a value clearly labeled "illustrative" and used only to demonstrate the mechanics of a calculation. Illustrative values are not, and must never be read as, the governing ceilings.

### 18.1 Purpose and scope

The fair-lending assessment is one of the two co-equal gates that a candidate model must clear before the Model Risk Management (MRM) function will permit promotion. The first gate is predictive quality, addressed elsewhere in this dossier; the second is the fair-lending gate described here. The two gates are evaluated independently and are not fungible: a candidate cannot "buy back" a fairness deficiency with superior accuracy, nor can it offset weak discrimination with a clean fairness profile. This non-fungibility is the structural expression of the Bank's conservative promotion philosophy and is elaborated in §18.9.

The scope of this methodology covers the 12-month PD classifier used in consumer-credit underwriting and the protected and quasi-protected attributes against which its outputs are tested: `age_group`, `gender`, and `region`. It also covers the treatment of the prohibited geographic-proxy feature `region_risk_index`, which is barred from the model's feature space precisely because it operates as a latent encoding of protected geographic characteristics; the rationale for that prohibition, and its interaction with the `region` fairness dimension, is discussed in §18.6. Out of scope are the operational controls governing post-deployment monitoring, drift, and adverse-action notice generation, which are governed by their own sections; this section is concerned with the pre-promotion disparate-impact assessment.

### 18.2 Legal grounding translated into measurement

The methodology is anchored in the Equal Credit Opportunity Act (ECOA, 15 U.S.C. §1691 et seq.) and its implementing Regulation B (12 C.F.R. Part 1002). ECOA prohibits discrimination in any aspect of a credit transaction on the basis of race, color, religion, national origin, sex, marital status, age (provided the applicant has the capacity to contract), the applicant's receipt of public assistance income, or the good-faith exercise of rights under the Consumer Credit Protection Act. Regulation B operationalizes these prohibitions and constrains the information a creditor may request and act upon.

Fair-lending law recognizes more than one theory of liability. The two most relevant to an automated underwriting model are **disparate treatment** — facially or intentionally treating an applicant differently because of a protected characteristic — and **disparate impact** — a facially neutral policy or practice that produces a disproportionately adverse effect on a protected class and is not justified by business necessity, or where a less discriminatory alternative exists. A PD classifier that never ingests a protected attribute can still produce disparate impact, because lawful-looking predictors frequently correlate with protected status. Disparate-impact analysis is therefore the principal lens of this methodology, and the burden-shifting structure of the disparate-impact framework — a showing of adverse effect, a business-necessity justification, and a search for less-discriminatory alternatives — maps directly onto the Bank's promotion workflow.

Translating these legal concepts into a repeatable measurement requires three commitments:

1. **A measurable adverse-effect statistic.** The Bank reduces the legal notion of "disproportionately adverse effect" to a concrete, reproducible quantity computed from the model's predictions on a held-out evaluation population. That quantity is the demographic-parity-difference statistic defined in §18.4.

2. **A defined decision threshold.** Disparate impact is a property of *decisions*, not of raw scores. A PD model emits a continuous score; a decision arises only when that score is compared to a cutoff. The fair-lending assessment is therefore always evaluated at the standard decision threshold fixed in §6–§13, so that the measured disparity reflects the lending decisions the model would actually drive. Using an arbitrary or model-tuned threshold for the fairness test would make the result uncomparable across candidates; pinning it to the governed threshold makes the test reproducible and auditable.

3. **A documented business-necessity and less-discriminatory-alternative record.** Even where a candidate passes the numeric ceiling, the assessment file preserves the rationale linking each retained predictor to creditworthiness and records whether a less-discriminatory alternative specification was considered. This is the documentary spine that allows the Bank to defend a promoted model under examination and to demonstrate that promotion was not a mechanical pass/fail exercise.

The legal framework also explains why the Bank treats `region` with heightened sensitivity. Geographic variables are a classic vector for redlining-type effects, in which neutral-seeming locational data proxies for prohibited bases such as race or national origin. The prohibition of `region_risk_index` and the elevated scrutiny of the `region` dimension are direct methodological responses to that history.

### 18.3 Protected and quasi-protected attributes

The fair-lending assessment evaluates three attributes. `gender` and `age_group` are protected bases under ECOA in the conventional sense. `region` is treated as a quasi-protected attribute: it is not itself an enumerated protected basis, but because geography correlates strongly with protected characteristics, it is governed under the same disparate-impact discipline and, as discussed below, under the strictest scrutiny of the three.

| Attribute | Status | Primary fair-lending concern | Group structure used in measurement |
|---|---|---|---|
| `gender` | Protected (ECOA sex) | Direct sex-based disparate impact via correlated predictors | Discrete categories as defined in the evaluation schema |
| `age_group` | Protected (ECOA age) | Age-correlated effects, e.g., thin-file young applicants or fixed-income older applicants | Banded age cohorts |
| `region` | Quasi-protected (geographic proxy) | Redlining-type disparate impact; latent encoding of protected status | Defined geographic groupings |

Each attribute is assessed *independently*. The disparity statistic is computed separately within each attribute's group structure, and the candidate must clear the ceiling applicable to that attribute (per §11) on every attribute. There is no aggregate or averaged fairness score across attributes, and a pass on two attributes never compensates for a failure on the third. Independent per-attribute adjudication is deliberate: a class injured along one protected dimension is not made whole by the model's even-handedness along another.

### 18.4 Definition of the demographic-parity-difference statistic

The binding fairness statistic at Meridian is the **demographic-parity difference** (also called the statistical-parity difference). It is defined as follows.

Let an attribute *A* partition the evaluation population into mutually exclusive groups *g₁, g₂, …, g_k*. Let the model, evaluated at the standard decision threshold *t* fixed in §6–§13, produce for each applicant a binary decision. Define the **positive-prediction rate** for group *gᵢ* as the proportion of members of *gᵢ* who receive the favorable (positive) decision at threshold *t*:

  *r(gᵢ) = (number in gᵢ receiving the favorable decision at t) / (number in gᵢ)*

The **demographic-parity difference** for attribute *A* is then the spread between the most-favored and least-favored group:

  *DPD(A) = max₍ᵢ₎ r(gᵢ) − min₍ᵢ₎ r(gᵢ)*

In words: across all groups of the attribute, take the highest positive-prediction rate and subtract the lowest. The result is a number between 0 and 1. A value of 0 means every group receives the favorable decision at exactly the same rate — perfect demographic parity. Larger values indicate a wider gap between the best-treated and worst-treated groups and therefore a stronger signal of disparate impact. The candidate's *DPD(A)* for each protected attribute is compared against the ceiling for that attribute in §11; the candidate fails the fair-lending gate if any attribute's *DPD* exceeds its ceiling.

Three properties of this definition deserve emphasis:

- **It is a difference of rates, not of scores.** Because it is computed on thresholded decisions, it speaks the language of lending outcomes — who gets credit — rather than the language of model internals.
- **It is a max-minus-min spread, not a pairwise comparison against a reference group.** This makes it robust to which group is arbitrarily designated as the baseline; it always captures the widest gap present anywhere in the attribute.
- **It is symmetric and label-agnostic with respect to group identity.** Relabeling or reordering the groups never changes the value. This is important for reproducibility and for defending the statistic as non-arbitrary.

#### 18.4.1 Worked illustrative example (illustrative values only)

The following numbers are **illustrative** and exist solely to demonstrate the arithmetic. They are not thresholds, not observed results from any candidate, and emphatically not the ceilings in §11.

Suppose the attribute under test is `region`, partitioned into four groups, and that after scoring the evaluation population and applying the standard decision threshold we observe the following **illustrative** positive-prediction rates:

| Group (illustrative) | Applicants (illustrative) | Favorable decisions (illustrative) | Positive-prediction rate *r(gᵢ)* (illustrative) |
|---|---|---|---|
| Region A | 5,000 | 3,400 | 0.680 |
| Region B | 4,200 | 2,520 | 0.600 |
| Region C | 3,800 | 2,090 | 0.550 |
| Region D | 6,000 | 4,260 | 0.710 |

The most-favored group is Region D at an illustrative rate of 0.710; the least-favored is Region C at an illustrative rate of 0.550. The demographic-parity difference for `region` in this illustrative scenario is:

  *DPD(region) = 0.710 − 0.550 = 0.160* (illustrative)

To adjudicate, the assessor would compare this illustrative 0.160 against the `region` ceiling recorded in §11. If the illustrative 0.160 exceeded that ceiling, the candidate would fail the fair-lending gate on the `region` attribute regardless of its predictive quality. The same computation is then repeated independently for `gender` and `age_group`, each against its own ceiling. Again: the value 0.160 here is purely demonstrative of the subtraction; it carries no normative meaning and must not be confused with any governing limit.

A second illustrative point worth drawing out: the statistic is sensitive only to the extremes. In the table above, Region A and Region B fall between the max and the min and so do not affect *DPD* directly. This is intentional — the legal concern is the *worst* disparity any group suffers — but it is also a known limitation that the methodology compensates for through the supplementary diagnostics described in §18.7.

### 18.5 Alternative fairness metrics considered and the rationale for adoption

Fairness measurement is not settled science, and no single statistic captures every normatively relevant notion of equity. Before adopting the demographic-parity difference as the *binding* statistic, the MRM and Fair Lending functions evaluated the principal alternatives. The comparison below records why each was considered and why demographic-parity difference was chosen as the gate. The binding ceilings remain in §11; this subsection concerns only the choice of statistic, not its numeric threshold.

#### 18.5.1 Equal opportunity / true-positive-rate difference

Equal opportunity asks whether, among applicants who *would* repay (the true positives in classifier terms), each group is approved at the same rate. Formally it compares the true-positive rate (TPR) across groups and takes the spread. Its appeal is that it conditions on the outcome label and so does not penalize a model for legitimate differences in underlying creditworthiness between groups. Its drawback for a pre-promotion gate is that it requires reliable ground-truth repayment labels on the evaluation population, which for a 12-month PD model means a matured outcome window; the label is also itself a product of prior lending decisions and can encode historical bias (the "selective labels" problem). Because the gate must be computable at promotion time on the governed evaluation set, and because conditioning on a potentially biased label can launder historical discrimination, equal opportunity was retained as a *diagnostic* (§18.7) but not adopted as the binding gate.

#### 18.5.2 Predictive parity / calibration within groups

Predictive parity asks whether a given score means the same thing across groups — i.e., whether the positive predictive value (the share of predicted defaulters who actually default) is equal across groups, or equivalently whether the model is calibrated within each group. This is a desirable property and is monitored. However, it is well established that predictive parity, equalized error rates, and demographic parity cannot in general all hold simultaneously when base rates differ across groups (the impossibility results of the fairness literature). Predictive parity also tends to be satisfied "for free" by a well-calibrated model even when approval rates diverge sharply, so it is a weak guard against disparate *impact* in the lending-outcome sense. It is therefore tracked as a supporting calibration diagnostic rather than used as the disparate-impact gate.

#### 18.5.3 Disparate-impact ratio / four-fifths rule

The disparate-impact ratio expresses the least-favored group's positive rate as a fraction of the most-favored group's positive rate; under the EEOC-derived four-fifths (80%) rule of thumb, a ratio below 0.80 is treated as evidence of adverse impact. This ratio is closely related to the demographic-parity difference — both are functions of the same per-group positive rates — and the Bank computes it as a cross-check. The reason it is not the *binding* statistic is that a ratio is scale-dependent in a way that produces unstable behavior at low approval rates: when the favored group's rate is small, modest absolute differences produce alarming ratios, and when approval rates are high the same absolute gap produces a comfortable-looking ratio. An absolute difference (DPD) behaves predictably across the operating range and is easier to set a defensible, edition-stable ceiling against. The four-fifths ratio is therefore retained as a corroborating diagnostic.

#### 18.5.4 Why demographic-parity difference is the binding statistic

Demographic-parity difference was adopted as the binding gate for the following reasons:

- **It is computable at promotion time without matured labels.** It depends only on the model's thresholded decisions and group membership, both available on the governed evaluation set. The gate can therefore be applied to every candidate, every time, without waiting for an outcome window to mature.
- **It speaks directly to lending outcomes.** It measures the gap in who actually receives credit, which is the quantity disparate-impact doctrine cares about, rather than an internal model property.
- **It does not condition on a potentially biased label**, avoiding the risk of certifying as "fair" a model that merely reproduces historically discriminatory approval patterns.
- **It is robust and reproducible**: a max-minus-min spread is invariant to group relabeling and produces a stable, interpretable number that can be tied to a fixed ceiling across editions.
- **It is conservative.** Because it ignores legitimate-creditworthiness justifications, it can flag a model that a label-conditioned metric would clear. The Bank treats that conservatism as a feature: the appropriate place to argue business necessity is the documented remediation and override record (§18.8), under Fair Lending Officer scrutiny, not in the choice of a more permissive statistic.

The other metrics are not discarded. They are run as **supplementary diagnostics** on every candidate so that the assessment file contains a multi-metric picture; but only the demographic-parity difference, evaluated at the standard threshold against the §11 ceilings, determines pass or fail.

| Metric | What it equalizes | Needs matured labels? | Conditions on outcome label? | Behavior across operating range | Role at Meridian |
|---|---|---|---|---|---|
| Demographic-parity difference (max−min positive rate) | Approval rates across groups | No | No | Stable (absolute difference) | **Binding gate** (ceilings in §11) |
| Equal opportunity (TPR difference) | Approval among true repayers | Yes | Yes | Moderate | Diagnostic |
| Predictive parity / within-group calibration | Meaning of a given score | Yes | Yes | Stable | Diagnostic |
| Disparate-impact ratio (four-fifths) | Ratio of least- to most-favored rate | No | No | Unstable at low/high rates | Corroborating cross-check |

### 18.6 Independent per-attribute assessment and the heightened sensitivity of `region`

As stated in §18.3, the demographic-parity difference is computed separately for `gender`, `age_group`, and `region`, and each is held to its own ceiling per §11. The independence of these tests is methodological bedrock; there is no scenario in which strong performance on one protected attribute offsets a breach on another.

Among the three, the `region` dimension warrants the most scrutiny, for reasons rooted in the geographic-proxy problem. Geography is a dense carrier of protected-class information: where a person lives correlates with race, national origin, and other prohibited bases, which is the mechanism by which historical redlining operated. A model can therefore exhibit substantial regional disparity even when no protected attribute is in its feature set, simply because lawful-looking predictors (income volatility, utilization patterns, tenure) are spatially structured.

This is also why the feature `region_risk_index` is **prohibited** from the model's feature space. `region_risk_index` is a constructed geographic-risk score, and a constructed score of that kind is a near-perfect proxy: it concentrates the spatial — and therefore the protected-class — signal into a single high-leverage feature, giving the model an efficient pathway to encode geographic discrimination while appearing facially neutral. Excluding it is a primary control. But exclusion alone is insufficient, because the same spatial signal can be reconstructed in pieces from other permitted features. The elevated `region` scrutiny in the disparate-impact test is the backstop: even if a prohibited or proxy signal leaks back in through correlated predictors, the outcome-level `DPD(region)` test catches the disparate *effect* regardless of the pathway by which it arose. In practice this means that when a candidate is close to any ceiling, the `region` result receives the most attention in the assessment narrative, the supplementary diagnostics in §18.7 are examined most closely on the regional partition, and the feature-attribution review pays particular attention to predictors that may be acting as geographic surrogates.

### 18.7 Supplementary diagnostics

To avoid the known blind spots of any single statistic — including the demographic-parity difference's insensitivity to anything between the extreme groups — the assessment file accompanies the binding result with a panel of diagnostics computed on the same governed evaluation set at the same standard threshold:

- The full vector of per-group positive-prediction rates for each attribute (not just the max and min), so reviewers can see the whole distribution and detect a middle group that is trending toward an extreme.
- The disparate-impact ratio (four-fifths cross-check) per attribute.
- Equal-opportunity (TPR difference) and within-group calibration where a sufficiently matured label is available, flagged with the maturity caveat.
- Group sample sizes and confidence intervals on each rate, so that a disparity computed on a thin group is not over-interpreted; small-sample groups are reported with their uncertainty and may trigger additional data collection rather than a mechanical pass/fail.
- A feature-attribution review highlighting predictors with the strongest association to the `region` partition, to surface potential geographic surrogates.

These diagnostics do not change the pass/fail rule — only the demographic-parity difference against §11 governs that — but they inform the Fair Lending Officer's judgment, the remediation plan, and the documentary defense of any promotion decision.

### 18.8 Fair Lending Officer veto, escalation, and remediation

#### 18.8.1 The veto

The Fair Lending Officer (FLO) holds an independent veto over any promotion. The veto is unconditional with respect to predictive quality: the FLO may block the promotion of a candidate that clears every accuracy and discrimination bar if, in the FLO's judgment, the fair-lending record is unsatisfactory — for example, a passing-but-marginal `region` result accompanied by diagnostics suggesting an emerging geographic-proxy pathway, or a thin-group disparity that cannot be confidently bounded. Conversely — and critically — the FLO cannot *waive* a breach. A candidate whose demographic-parity difference exceeds a §11 ceiling on any protected attribute is disqualified, and the FLO has no authority to override that disqualification by appeal to the model's accuracy. The veto runs in one direction only: it can stop a promotion, never force one through a fairness failure.

#### 18.8.2 Escalation path

The escalation path proceeds as follows:

1. **Assessment.** MRM computes the demographic-parity difference for each protected attribute against the §11 ceilings, assembles the §18.7 diagnostics, and records a preliminary determination.
2. **FLO review.** The Fair Lending Officer reviews the assessment package independently of the model-development team. The FLO may concur, exercise the veto, or request additional analysis (e.g., enlarged samples for thin groups, deeper surrogate analysis on `region`).
3. **Escalation to the Model Risk Committee.** A breach, an FLO veto, or an unresolved disagreement between development and fair-lending functions is escalated to the Model Risk Committee, with Legal/Compliance participation. The Committee does not have authority to approve a model that breaches a §11 ceiling; its role on a breach is to ratify the disqualification and direct remediation. Where the matter is an FLO veto of a technically-passing candidate, the Committee adjudicates the qualitative concern.
4. **Board-level reporting.** Material fair-lending matters, including any disqualification of an otherwise high-performing candidate, are reported up through the established risk-governance reporting line.

Throughout, the independence of the fair-lending review from the development team is preserved; the function that builds the model does not adjudicate its own fairness.

#### 18.8.3 Remediation expectations

When a candidate breaches a ceiling, the candidate is not promoted, and the development team is expected to remediate rather than to re-litigate the statistic. Expected remediation activities, documented in the assessment file, include:

- **Disparity decomposition** — identifying which predictors and which population segments drive the breach, with particular attention to geographic surrogates on a `region` breach.
- **Feature remediation** — removing, transforming, or constraining predictors that act as proxies for protected status, and re-confirming that prohibited features such as `region_risk_index` have not re-entered directly or via reconstruction.
- **Less-discriminatory-alternative search** — actively seeking an alternative model specification that retains acceptable predictive quality while reducing the disparity, consistent with the disparate-impact doctrine's requirement to consider less-discriminatory alternatives. The search, and its results, are documented whether or not a satisfactory alternative is found.
- **Re-assessment** — re-running the full §18 assessment on the remediated candidate; a remediated model is a new candidate and must clear every gate afresh.

Remediation is expected to produce a model that *passes* the ceiling, not a narrative that explains the breach away. Business-necessity argumentation has its place in the documentary record but cannot substitute for bringing the demographic-parity difference within the §11 ceiling.

### 18.9 Why the most accurate model is not necessarily promoted

The defining feature of Meridian's promotion philosophy is that **a fairness breach disqualifies a candidate even when it is the most accurate model available.** This is not an incidental consequence of the workflow; it is a deliberate policy choice, and the methodology is built to enforce it.

The reasoning is threefold. First, **legal**: a model that produces disparate impact exposes the Bank to ECOA/Reg B liability that no amount of predictive lift can cure; accuracy is not a defense to discrimination. Second, **ethical and reputational**: the Bank's obligation to lend equitably is not contingent on the cost of doing so, and a more-accurate-but-discriminatory model imposes that cost on protected applicants. Third, **methodological integrity**: allowing accuracy to offset fairness would make the fairness ceiling negotiable and therefore meaningless; the only way a ceiling functions as a real constraint is if it is inviolable. For these reasons the two gates are evaluated independently (§18.1) and a fairness failure is terminal.

In operational terms this means that the model-selection procedure does not maximize accuracy subject to a fairness penalty; it first eliminates every candidate that breaches any §11 ceiling on any protected attribute, and only then ranks the *surviving* candidates by predictive quality. A candidate that tops the accuracy leaderboard but fails the fair-lending gate is removed from contention entirely. The promoted model — designated as the production reference via its MLflow alias — is therefore the best-performing model *among the fair ones*, which is frequently not the best-performing model overall.

### 18.10 Historical context: superseded editions

The current methodology is the product of two prior editions, both now retired. They are recorded here as historical context to show how the fair-lending discipline tightened over time. The values below are **superseded** and are presented only as historical record; they are not current criteria.

**Edition 1 (2023).** The first edition governed a model registered under the name `meridian_risk_model_v1`, stored at the artifact path `model`, and was evaluated on an 80/10/10 train/validation/test split with random seed 7. Its predictive bars were an accuracy of 0.80 and an AUC of 0.82. Its fair-lending discipline was comparatively coarse: the only disparity constraint was a regional disparity ceiling of 0.20, with no separately stated gender ceiling. Edition 1 is the source of the Bank's most instructive rejection. A candidate that satisfied the Edition 1 predictive bars was nonetheless **rejected** because its measured regional disparity came in at 0.22, exceeding the then-ceiling of 0.20. That rejection — a technically performant model blocked on a regional fairness breach — established the precedent that fairness is a hard gate and not a tunable trade-off, and it directly motivated the elevated `region` scrutiny carried forward into the current methodology.

**Edition 2 (2024).** The second edition retained an accuracy bar of 0.80 but recalibrated AUC to 0.81 and introduced a macro-F1 bar of 0.75. It moved to a 70/15/15 split with random seed 13, enlarging the validation and test partitions relative to Edition 1. Its principal fair-lending advance was the introduction of an explicit **gender disparity ceiling of 0.06**, formalizing per-attribute treatment of `gender` alongside the geographic dimension. Edition 2 thus marked the transition from a single geographic constraint to genuinely multi-attribute fair-lending assessment.

The current edition (Edition 3) supersedes both. It retains the lessons of those editions — the inviolability of the fairness gate first demonstrated in 2023, and the per-attribute, multi-dimensional discipline introduced in 2024 — and consolidates the binding criteria in §6–§13. The reader is reminded that the only authoritative statements of the *current* split, seeds, predictive bars, decision threshold, registry naming, alias designation, and per-attribute disparity ceilings are those sections, and the current fairness ceilings specifically are in §11. The Edition 1 and Edition 2 figures recited above are retired and must not be applied to any present-day candidate.

### 18.11 Summary

The fair-lending assessment reduces ECOA/Regulation B disparate-impact doctrine to a reproducible, label-free, outcome-level statistic — the demographic-parity difference, computed as the max-minus-min positive-prediction rate across each protected attribute's groups at the standard decision threshold — and applies it independently to `gender`, `age_group`, and `region`, with `region` under the heaviest scrutiny because of the geographic-proxy risk that also justifies the prohibition of `region_risk_index`. Alternative metrics (equal opportunity, predictive parity, the four-fifths ratio) are computed as diagnostics but do not govern the gate, for the reasons set out in §18.5. The Fair Lending Officer can veto a passing candidate but can never waive a breach. A candidate that exceeds any ceiling in §11 is disqualified and must be remediated and re-assessed from scratch — even, and especially, when it is the most accurate model on offer. The binding numbers themselves live in §6–§13, and the fairness ceilings in §11; this section governs only the method by which those numbers are measured and enforced.


## §19 Champion–Challenger Promotion Governance and Committee Charter

This section establishes the governance machinery through which a candidate consumer-credit 12-month probability-of-default (PD) classifier becomes the production model of record at Meridian Financial, N.A. It defines the Model Risk Committee (MRC) as the deciding authority, sets out the champion–challenger paradigm and the ordered promotion workflow, describes the Edition 3 MLflow registry operating model and the migration away from the deprecated stage-based mechanism, and fixes the change-management, evidentiary, and rollback expectations that surround every promotion. Consistent with the dossier's design, this section is procedural and authoritative on *who decides, in what order, and against what evidence*; it deliberately does not restate the binding numeric criteria. The acceptance thresholds, fairness ceilings, ranking metric, split protocol, and champion-selection rule are owned exclusively by §6 (registry conventions), §10 (ranking), §11 (acceptance gates), §12 (fairness gates and champion selection), and §13 (monitoring), and are referenced here only by pointer.

### §19.1 Purpose and Scope of the Model Risk Committee

The Model Risk Committee is the standing body accountable for authorizing the promotion, retention, demotion, and retirement of consumer-credit PD models within the bank's MLflow model registry. Its remit derives from the bank's enterprise Model Risk Management policy and from the supervisory expectations articulated in SR 11-7 / OCC 2011-12 and the bank's internal interpretation thereof. The Committee exists to ensure that no model is granted production authority — that is, no model receives the production alias defined in §6 — except by an explicit, recorded, multi-party decision grounded in a complete validation package and in conformance with the binding criteria in §6–§13.

The scope of MRC authority under this Edition covers:

- The single registered consumer-credit PD model slot in the MLflow registry as governed by the naming and registry conventions in §6.
- All candidate model versions registered against that slot, whether produced by scheduled retraining, ad-hoc experimentation, or remediation of a prior finding.
- The assignment, movement, and removal of the production alias that designates the operative champion.
- The disposition of non-promoted candidates and the recording of those non-promotions.
- The authorization of rollback and emergency demotion in coordination with the monitoring regime in §13.

Matters expressly outside MRC scope include feature engineering design decisions (owned by Model Development), the construction of the validation datasets and split protocol (owned by Model Validation under §10), and infrastructure operation of the registry itself (owned by ML Platform Engineering). The Committee consumes the outputs of these functions; it does not perform them. This separation is foundational to the control environment and is elaborated in §19.4.

### §19.2 Membership and Roles

The Committee is composed of voting members, non-voting standing attendees, and invited subject-matter participants. Voting membership is role-based, not person-based; a named individual holds a seat by virtue of an organizational role, and seats transfer with role changes recorded in the bank's governance register.

| Seat | Function | Voting | Primary responsibility in promotion |
|---|---|---|---|
| Chair | Head of Model Risk Management (or delegate) | Yes | Convenes meetings, sets agenda, certifies quorum, breaks ties |
| Validation Lead | Head of Model Validation | Yes | Attests that the validation package is complete and that acceptance and fairness gates were applied per §11–§12 |
| Risk Officer | Consumer Credit Chief Risk Officer delegate | Yes | Represents credit-risk appetite and portfolio impact |
| Fairness Officer | Head of Responsible AI / Fair Lending | Yes | Attests to fairness-gate application and protected-attribute handling |
| Compliance Member | Regulatory Compliance representative | Yes | Confirms regulatory and fair-lending alignment |
| Business Sponsor | Consumer Credit line-of-business owner | Yes | Represents business need and accepts operational consequences |
| Independent Member | Internal Audit liaison or external advisor | Yes (advisory weight) | Provides challenge independent of development and business lines |
| Model Owner | Named accountable owner of the registered model | Non-voting | Presents the candidate, answers technical questions |
| Lead Developer | Model Development representative | Non-voting | Explains methodology; recused from the promotion vote (see §19.4) |
| Secretary | MRM governance analyst | Non-voting | Records minutes, maintains evidence, tracks actions |

Invited participants — data engineering, legal, privacy, or external validators — may attend at the Chair's discretion for a specific agenda item and do not count toward quorum or voting.

### §19.3 Quorum, Voting, Conflicts, and Recusal

**Quorum.** A promotion decision may be taken only when a quorum of voting members is present. Quorum requires the attendance of at least a majority of the voting seats and, additionally, the mandatory presence of the Validation Lead and the Fairness Officer (or their formally delegated alternates). The rationale for the mandatory seats is that promotion turns on two independent attestations — that the acceptance gates of §11 were satisfied and that the fairness gates of §12 were satisfied — and neither attestation may be presumed in the attesting officer's absence. If either mandatory seat is vacant, the meeting may discuss but may not decide a promotion.

**Voting.** Promotion, retention, demotion, and rollback ratification are decided by vote of the voting members present. A motion to promote carries on an affirmative majority of votes cast, provided that no mandatory-seat holder casts a dissent recorded as a *gate objection*. A gate objection — a recorded assertion by the Validation Lead, Fairness Officer, or Compliance Member that a binding gate in §11–§12 or a regulatory requirement was not in fact satisfied — operates as a hold. A held motion cannot carry on majority alone; it must be resolved by remediation and re-presentation, or escalated to the Chief Risk Officer for adjudication. This asymmetry is deliberate and reflects the bank's conservative promotion posture: a candidate is promoted only when the gatekeepers affirmatively concur, never merely because a numerical majority is willing to proceed over a substantive gate concern. The Chair votes only to break a tie among non-objection votes.

**Conflicts and recusal.** Any member with a personal, financial, or performance-linked interest in the outcome of a specific promotion must declare the conflict at the opening of the relevant agenda item and recuse from the vote on that item. The most common structural conflict is authorship: a member who developed, tuned, or selected features for the candidate model may not vote on its promotion. The Lead Developer and Model Owner are therefore non-voting by design (§19.2), and any voting member who participated materially in producing the candidate recuses for that item. Recusals are recorded by the Secretary with the reason and the affected agenda item. A recused member does not count toward the quorum for that item's vote, though they may remain present to answer questions at the Chair's invitation.

### §19.4 Separation of Duties: Developer and Validator

The integrity of every promotion rests on a strict separation between the function that *builds* a candidate and the function that *judges* it. Under this Edition, Model Development and Model Validation are organizationally distinct, report through independent management chains, and are subject to the recusal rules above.

- **Model Development** designs, trains, and registers candidate versions. Development selects the modeling approach, performs hyperparameter search, and produces the candidate artifacts and the developer's self-assessment. Development does not run the official acceptance or fairness evaluations of record and does not vote on promotion.
- **Model Validation** independently re-derives the evaluation metrics on the governed validation and test partitions, applies the acceptance gates of §11 and the fairness gates of §12, performs the ranking of §10, and assembles the validation package. Validation's attestations are the evidentiary backbone of the promotion vote.
- **ML Platform Engineering** operates the registry, executes the mechanical assignment of the production alias once the MRC authorizes it, and has no discretionary authority over the promotion decision itself.

No single individual may both produce a candidate and attest to its acceptance, fairness, or ranking. This four-eyes principle is enforced procedurally (through recusal and role assignment) and technically (through registry permissions described in §19.7 and §6). A candidate whose validation was performed by a person who also contributed to its development is, by definition, not eligible for promotion until re-validated by an independent validator.

### §19.5 The Champion–Challenger Paradigm

Meridian operates a single production model of record — the *champion* — at any given time for the consumer-credit PD use case. The champion is the model version currently bearing the production alias defined in §6 and is the model whose scores feed downstream credit decisioning. All other candidate versions are *challengers*: models proposed as potential replacements for the champion.

The paradigm is comparative and adversarial by intent. A challenger does not earn promotion merely by being adequate in isolation; it earns promotion by demonstrating, on identical and independently governed evaluation data, that it is a justified replacement for the incumbent under the criteria of §10–§12. The discipline of always evaluating challengers against the current champion on the same partitions guards against drift in evaluation practice and ensures that promotion reflects genuine improvement rather than changes in how performance was measured.

**How challengers are produced.** Challengers arise from three streams: scheduled periodic retraining on refreshed data windows; targeted remediation of a finding raised under monitoring (§13) or by validation; and exploratory development of new features or methods. Regardless of origin, every challenger is registered as a new version against the single model slot in §6 and enters the same workflow.

**How challengers are compared.** Each challenger is evaluated on the governed validation and test partitions produced under the split protocol owned by §10. The same partitions, produced under the same protocol, are applied to the challenger and to the champion so that the comparison is apples-to-apples. Validation computes the acceptance metrics of §11, the fairness diagnostics of §12 over the protected attributes (age_group, gender, region), and the ranking metric of §10. The champion is included in the comparison as a reference point; a challenger that does not improve upon the incumbent under the ranking rule of §10 and the champion-selection rule of §12 is not promoted, even if it independently clears the acceptance gates. Shadow or parallel-run comparison — scoring the challenger alongside the live champion on production traffic without granting it decision authority — may be employed prior to a promotion vote and, when used, its results are appended to the validation package; shadow evidence supplements but does not replace the governed-partition evaluation.

A central and non-negotiable feature of the comparison is the prohibited proxy. The feature `region_risk_index` is a prohibited proxy for the protected attribute region and must not appear in any challenger's feature set. Validation rejects any candidate that includes it before any further evaluation is performed; such a candidate is recorded as a non-promotion with the reason "prohibited proxy present" and is not advanced.

### §19.6 End-to-End Promotion Workflow

The promotion of a challenger follows a fixed sequence of operations. The order is itself a control: gates are applied before ranking, and ranking is applied before any registry action. Performing these steps out of order — for example, ranking candidates before fairness has been adjudicated — is a control breach and invalidates the promotion. The canonical sequence is:

**Step 1 — Assemble the validation package.** Validation collects, for the challenger and the incumbent champion, the governed dataset lineage and split protocol (per §10), the trained artifacts and their provenance, the computed acceptance metrics (per §11), the fairness diagnostics over age_group, gender, and region (per §12), the ranking computation (per §10), the developer self-assessment, and a confirmation that no prohibited proxy is present. The package is the sole evidentiary basis for the vote; nothing decided by the MRC may rest on evidence outside it.

**Step 2 — Apply the acceptance gates.** Validation applies the binding acceptance criteria defined in §11 to each candidate. Candidates that fail any acceptance gate are eliminated and recorded as non-promotions with the specific failing gate noted. Acceptance gating is a pass/fail filter, not a ranking; it determines eligibility, not preference.

**Step 3 — Apply the fairness gates.** Validation applies the binding fairness criteria defined in §12 — including the demographic-parity-difference ceilings over the protected attributes — to every candidate that survived acceptance. Candidates that breach any fairness ceiling are eliminated and recorded as non-promotions with the breached attribute and metric noted. **Fairness gating precedes ranking.** This ordering is deliberate and binding: a candidate that fails fairness is removed from consideration *before* any ranking is computed, so that the bank never ranks, prefers, or promotes a model on the basis of performance that was achieved at the cost of an unacceptable disparity. Ranking operates only on the set of candidates that have already cleared both acceptance and fairness.

**Step 4 — Rank the survivors.** Among the candidates that have cleared both the acceptance gates (§11) and the fairness gates (§12), Validation computes the ranking metric of §10 and orders the survivors. The champion is included in this ranking as the incumbent reference. Ranking identifies the preferred candidate; it does not by itself authorize promotion.

**Step 5 — Apply the champion-selection rule and register/alias the champion.** The MRC applies the champion-selection rule of §12 to the ranked survivors to determine whether the top-ranked challenger should replace the incumbent. Only if the rule is satisfied and the vote carries does the candidate become the new champion. Upon authorization, ML Platform Engineering registers the candidate version (if not already registered) against the single model slot of §6 and moves the production alias defined in §6 to that version. The alias movement is the act of promotion; until it occurs, the incumbent remains champion.

**Step 6 — Record non-promotions.** Every candidate that did not become champion — whether eliminated at acceptance, eliminated at fairness, out-ranked at §10, or not selected under the §12 rule — is recorded as a non-promotion with its disposition reason. The incumbent's retention, when no challenger is promoted, is itself recorded as an explicit decision. No candidate is allowed to exit the workflow without a recorded disposition.

The workflow is intentionally a one-way ratchet toward conservatism: at every stage, the default outcome is *no change to the champion*, and a change occurs only when the candidate affirmatively earns it through the ordered gates, the ranking, the selection rule, and the vote.

### §19.7 The Edition 3 MLflow Registry Operating Model

Edition 3 standardizes the bank on an alias-based promotion mechanism within the MLflow Model Registry and retires the stage-based mechanism used in Editions 1 and 2.

**Single registered slot and versions.** The consumer-credit PD model occupies a single registered model slot in the registry, named per the conventions of §6. Every candidate — from scheduled retraining, remediation, or experimentation — is registered as a new *version* against this one slot. Versions are immutable and monotonically numbered by the registry; a version, once created, is never edited in place. This gives a complete, append-only history of every model that was ever a candidate, which is essential for audit and for reconstructing any past promotion decision.

**Alias-based promotion.** Production authority is expressed by an *alias* — the production alias defined in §6 — attached to exactly one version at a time. To promote is to move that alias from the incumbent version to the newly authorized version; to roll back is to move it back. Because the alias is a pointer rather than a property of the version, promotion and rollback are atomic, instantaneous, and reversible, and the full version history is preserved regardless of which version currently holds the alias. Downstream consumers resolve the champion exclusively by the production alias of §6 and never by hard-coded version numbers, so a promotion or rollback takes effect for all consumers the moment the alias moves.

**Migration away from the deprecated stage mechanism.** In Editions 1 and 2, the operative model was designated by transitioning a model version into the MLflow `Production` stage; the prior production version was transitioned to an archived stage. That stage-based mechanism is deprecated in the MLflow versions the bank now runs and is retired under this Edition. The migration entailed: (a) identifying the version most recently in the `Production` stage as the migration-time incumbent; (b) attaching the production alias of §6 to that version; (c) clearing legacy stage assignments so that stage is no longer load-bearing; and (d) updating all downstream resolution to read the alias rather than the stage. The migration was a one-time mechanical operation that did not by itself promote any new model — the migration-time incumbent under the alias was the same version that had held the `Production` stage. No re-validation of the incumbent was triggered by the migration; the next promotion decision proceeds through the full §19.6 workflow as normal.

| Aspect | Editions 1–2 (retired) | Edition 3 (current) |
|---|---|---|
| Production designator | MLflow `Production` stage | Production alias (per §6) |
| Prior champion handling | Transitioned to archived stage | Remains a version; loses the alias |
| Registered name | meridian_risk_model_v1 (Ed. 1) | per §6 conventions |
| Artifact path | `model` (Ed. 1) | per §6 conventions |
| Reversibility | Stage transition, slower | Atomic alias move |
| History | Stage history | Immutable version history + alias audit |

The retired designators and configurations above — the `Production`/archived stage transitions, the Edition 1 registered name `meridian_risk_model_v1`, and the Edition 1 artifact path `model` — are recorded here solely to document what was superseded. They have no current force and must not be used to designate, resolve, or promote a model under this Edition.

**Registry permissions.** Write access to move the production alias is restricted to ML Platform Engineering and is exercised only upon a recorded MRC authorization. Validators and developers have read access and version-registration access respectively but cannot move the alias. This permission split enforces, at the technical layer, the separation of duties described in §19.4.

### §19.8 Rollback Authority and Link to Monitoring

Promotion is not the end of governance; a promoted champion remains under continuous monitoring per §13. Where monitoring detects performance degradation, population or feature drift, a fairness regression on the protected attributes, or a data-quality breach against the thresholds owned by §13, the monitoring regime escalates to the MRC.

**Rollback authority.** Rollback — moving the production alias of §6 back from the current champion to the prior champion version — may be authorized in two modes:

1. **Ordinary rollback**, decided by the MRC under the standard quorum and voting rules of §19.3, where time permits a convened decision.
2. **Emergency demotion**, where a §13 monitoring trigger indicates that continued operation poses immediate risk to customers or to fair-lending compliance. In emergency mode, the Chair (or, in the Chair's absence, the joint authority of the Validation Lead and Fairness Officer) may direct ML Platform Engineering to move the alias back to the last known-good version without awaiting a full meeting. Any emergency demotion must be ratified by the full MRC at the next meeting, and the ratification — together with the triggering monitoring evidence — is minuted.

Because Edition 3 uses an alias pointer rather than stage transitions, rollback is an atomic move of the alias to a preserved prior version and requires no re-registration or re-build. The specific monitoring triggers, thresholds, and escalation timelines that determine *when* rollback is warranted are owned exclusively by §13 and are referenced here only by pointer; this section governs *who* may roll back and *how* the action is recorded, not the numeric conditions that prompt it.

### §19.9 Change Management and Approval Evidence

Every promotion, retention, demotion, and rollback is a controlled change and generates a durable evidentiary record. The Secretary is accountable for assembling and retaining this record, and Validation is accountable for the technical contents of the validation package.

The minimum approval-evidence set for any promotion comprises:

- The complete validation package of §19.6 Step 1, including dataset lineage, split protocol reference (§10), candidate artifacts and provenance, acceptance results (§11), fairness diagnostics over age_group, gender, and region (§12), the ranking computation (§10), and the prohibited-proxy confirmation.
- The attestations of the Validation Lead and the Fairness Officer.
- The minuted MRC decision, including the motion, the vote tally, recorded recusals, and any gate objections.
- The registry record of the alias movement (or, for non-promotions, the recorded disposition of each candidate).
- For rollbacks, the triggering §13 monitoring evidence and the ratification record.

Evidence is retained for the period mandated by the bank's records-retention schedule for model-risk artifacts and is reproducible on demand for internal audit and supervisory examination. Because registry versions are immutable and the alias movements are logged, the state of the champion at any past date is reconstructible from the registry alone, cross-referenced to the corresponding minutes.

**Change classification.** Promotions and demotions are *material model changes* and always require full MRC decision. Mechanical, non-discretionary actions — such as the one-time Edition 3 alias migration of §19.7 — are *technical changes* executed by ML Platform Engineering under a recorded change ticket with MRM notification, and do not require a promotion vote because they do not alter which model holds decision authority. Any change that would move the production alias to a different version is, by definition, material and never qualifies as a technical change.

### §19.10 Committee Minutes — 2026

The following minutes are recorded for the period and illustrate the decision narrative without restating any binding criterion. Numeric thresholds, metric values, and selection rules are held in §10–§13 and are referenced in the minutes only by pointer.

#### Minutes — MRC-2026-01-14 (Quarterly Promotion Review, Q4-2025 retraining cycle)

**Present (voting):** Chair (HoMRM delegate), Validation Lead, Risk Officer, Fairness Officer, Compliance Member, Business Sponsor, Independent Member. **Non-voting:** Model Owner, Lead Developer, Secretary. **Quorum:** confirmed by Chair; mandatory seats (Validation Lead, Fairness Officer) present.

**Item 1 — Edition 3 mechanism status.** Validation Lead confirmed that the registry now resolves the champion exclusively via the production alias of §6 and that the deprecated stage-based mechanism is fully retired. Platform Engineering confirmed legacy stage assignments are cleared. Noted for the record; no decision required (technical change previously ratified).

**Item 2 — Challenger slate.** The Model Owner presented three challengers (versions registered against the single slot of §6) arising from the Q4-2025 scheduled retraining. The Lead Developer summarized methodology and declared authorship; both recused from the vote per §19.4.

**Item 3 — Gating outcomes.** Validation reported that all three challengers cleared the acceptance gates of §11. On the fairness gates of §12, one challenger was eliminated for breaching the demographic-parity-difference ceiling on the region attribute; this candidate was recorded as a non-promotion with the breached attribute noted, and — per the workflow ordering — was removed before any ranking. Validation confirmed none of the candidates contained the prohibited proxy `region_risk_index`. The Fairness Officer attested to correct application of §12.

**Item 4 — Ranking and selection.** Of the two surviving challengers, Validation computed the ranking metric of §10 against the incumbent champion on the governed partitions. The top-ranked challenger satisfied the champion-selection rule of §12 relative to the incumbent. The Validation Lead and Fairness Officer attested; no gate objection was raised.

**Item 5 — Decision.** Motion to promote the top-ranked challenger and move the production alias of §6 to that version. Vote: 5 in favor, 0 against, 0 abstentions (Independent Member concurred). Motion carried. Platform Engineering directed to move the alias; the prior champion retained as a preserved version for rollback. The second surviving challenger and the fairness-eliminated challenger recorded as non-promotions with reasons.

**Actions:** Secretary to file the validation package and alias-movement record; Platform Engineering to confirm alias move within the agreed window; Monitoring to baseline the new champion under §13.

#### Minutes — MRC-2026-02-25 (Ad-hoc, monitoring escalation)

**Present (voting):** Chair, Validation Lead, Risk Officer, Fairness Officer, Compliance Member. **Quorum:** confirmed; mandatory seats present.

**Item 1 — Monitoring trigger.** A §13 monitoring escalation flagged a fairness regression on the gender attribute for the sitting champion against the §13 thresholds. The Chair convened the ad-hoc session to consider demotion.

**Item 2 — Assessment.** Validation confirmed the trigger reflected a genuine drift rather than a data-quality artifact. No validated alternative challenger was yet available to promote in replacement.

**Item 3 — Decision.** The Committee declined emergency demotion at this stage, judging the condition not to pose immediate customer harm under the §13 escalation criteria, and instead directed an expedited remediation retraining cycle and heightened monitoring. The Chair's authority for emergency demotion under §19.8 was noted as available should the condition worsen. Recorded as a retention-with-conditions decision.

**Actions:** Development to produce a remediation challenger; Validation to fast-track its package; reconvene by next scheduled meeting.

#### Minutes — MRC-2026-04-08 (Remediation promotion)

**Present (voting):** Chair, Validation Lead, Risk Officer, Fairness Officer, Compliance Member, Business Sponsor, Independent Member. **Non-voting:** Model Owner, Lead Developer, Secretary. **Quorum:** confirmed; mandatory seats present.

**Item 1 — Remediation challenger.** A single remediation challenger, registered as a new version against the slot of §6, was presented to address the gender-attribute regression from MRC-2026-02-25. Lead Developer recused.

**Item 2 — Gating and ranking.** Validation confirmed the challenger cleared the acceptance gates of §11 and all fairness ceilings of §12 — including the previously regressed gender attribute — with no prohibited proxy present. As the only survivor, it was ranked under §10 against the incumbent and satisfied the champion-selection rule of §12. Fairness Officer attested specifically to the resolution of the prior regression.

**Item 3 — Decision.** Motion to promote the remediation challenger and move the production alias of §6. Vote: 5 in favor, 0 against, 1 abstention (Independent Member abstained pending an unrelated audit query, noted). Motion carried. Alias moved; prior champion preserved for rollback. The MRC-2026-02-25 escalation was thereby closed.

**Actions:** Secretary to file evidence and close the escalation; Monitoring to re-baseline under §13 with specific attention to the gender attribute.

#### Minutes — MRC-2026-05-20 (Quarterly Promotion Review)

**Present (voting):** full voting complement. **Quorum:** confirmed.

**Item 1 — Challenger slate.** Two challengers from scheduled retraining presented. Both cleared acceptance (§11) and fairness (§12); neither contained the prohibited proxy.

**Item 2 — Ranking and selection.** Both survivors were ranked under §10 against the incumbent. Neither top-ranked challenger satisfied the champion-selection rule of §12 relative to the sitting champion; the rule's conservative bias toward the incumbent was not overcome.

**Item 3 — Decision.** Motion to retain the incumbent champion; no alias movement. Vote: unanimous. Both challengers recorded as non-promotions with the reason "did not satisfy §12 selection rule against incumbent." The Committee noted that retention is an affirmative, recorded decision and not merely the absence of action.

**Actions:** Secretary to record the retention decision and the two non-promotions; Development to incorporate learnings into the next cycle.

### §19.11 Promotion Workflow RACI

The following RACI matrix assigns responsibility across the promotion workflow steps of §19.6. R = Responsible (does the work), A = Accountable (owns the outcome, single per row), C = Consulted (two-way input), I = Informed (one-way notification). Roles abbreviate the seats of §19.2: MDV = Model Development, MV = Model Validation, MRC = Model Risk Committee (voting body), FO = Fairness Officer, PE = ML Platform Engineering, SEC = Secretary.

| Workflow step | MDV | MV | FO | MRC | PE | SEC |
|---|---|---|---|---|---|---|
| Produce and register challenger version (§6) | A/R | I | I | I | C | I |
| Assemble validation package (§19.6 S1) | C | A/R | C | I | C | I |
| Apply acceptance gates (§11) | I | A/R | I | I | I | I |
| Apply fairness gates (§12) | I | R | A | I | I | I |
| Confirm no prohibited proxy present | C | A/R | C | I | I | I |
| Rank survivors (§10) | I | A/R | C | I | I | I |
| Apply champion-selection rule (§12) | I | C | C | A/R | I | I |
| Vote / authorize promotion | recused | C | C | A/R | I | I |
| Move production alias (§6) | I | I | I | A | R | I |
| Record non-promotions and dispositions | I | C | C | A | I | R |
| Authorize rollback / emergency demotion (§13 link) | I | C | C | A/R | R | I |
| Assemble and retain approval evidence (§19.9) | C | C | C | A | I | R |
| Notify downstream consumers of champion change | I | I | I | I | A/R | C |

The matrix makes explicit that accountability for the *decision* always rests with the MRC, accountability for the *evidence* with Model Validation and the Secretary, and accountability for the *mechanical alias action* with ML Platform Engineering — and that Model Development, while accountable for producing candidates, is recused from the authorizing vote. This distribution operationalizes the separation of duties of §19.4 across the full lifecycle of a promotion.

### §19.12 Interaction with Other Sections

This section is procedural and does not own any binding numeric criterion. For the registry naming and alias conventions and the identity of the production alias, see §6. For the ranking metric and split protocol, see §10. For the acceptance gates, see §11. For the fairness gates, the protected-attribute treatment, and the champion-selection rule, see §12. For the monitoring triggers and rollback conditions, see §13. Where any apparent conflict arises between this section's narrative and the binding criteria in §6–§13, the binding sections govern, and this section is to be read as describing the governance process that applies those criteria.


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


## §23 Glossary of Terms

This glossary defines terms used throughout this dossier as they apply to the governance of the consumer-credit 12-month probability-of-default (PD) classifier at Meridian Financial, N.A. Definitions are intended to be conceptually precise and consistent with the dossier's usage; where a term is associated with a current binding numeric threshold, configuration value, or seed, the operative figure is not restated here but is specified in §10, §11, §12, or §13 as applicable. Terms are listed in alphabetical order.

**Accuracy.** The proportion of all predictions a classifier gets correct, computed as the count of correct predictions divided by the total number of predictions. For the consumer-credit PD problem, accuracy is a weak headline metric because the default class is a minority; a model can achieve high accuracy by predicting "no default" almost always while failing to identify the borrowers who matter most for credit-risk management. Accuracy is reported for completeness but is never used as a sole promotion gate.

**Adverse action.** A denial or unfavorable change in credit terms communicated to an applicant. Under the Equal Credit Opportunity Act and Regulation B, adverse-action notices must state the specific principal reasons for the decision, which constrains the model's features and explanation pipeline so that the drivers of a declination can be articulated to the applicant.

**Alias.** A named, movable pointer in the MLflow Model Registry that resolves to a specific model version, allowing downstream systems to reference a stable label rather than a hard-coded version number. In this dossier the production-serving alias designates the current champion, and promotion is effected by repointing that alias; the exact alias string is specified in §10/§11.

**Area under the ROC curve (ROC-AUC).** A threshold-independent measure of a binary classifier's ability to rank a randomly chosen positive (defaulting) case above a randomly chosen negative (non-defaulting) case, equal to the area under the receiver operating characteristic curve. A value of 0.5 denotes no discrimination beyond chance and 1.0 denotes perfect ranking. ROC-AUC is a primary discrimination metric for PD models; its governing minimum is specified in §10.

**Artifact.** Any file or directory produced by and logged to an MLflow run — for example, a serialized model, a calibration plot, a feature-importance table, or an evaluation report. Artifacts are stored in the tracking server's artifact store and are immutable once logged, forming part of the evidentiary record for a model version.

**Backtesting.** The retrospective evaluation of a model against historical outcomes that were not available when the model was trained, used to confirm that predicted default rates align with realized defaults over time. Backtesting supports outcomes analysis and is a component of ongoing monitoring rather than a one-time pre-promotion check.

**Benchmarking.** The practice of comparing a candidate model's performance, behavior, or assumptions against an alternative reference point — a prior champion, a simple challenger, or an industry-standard approach — to establish whether observed performance is genuinely strong or merely adequate. Under SR 11-7, benchmarking is one of the core tools of effective challenge.

**Business necessity.** Under fair-lending doctrine, the legitimate, nondiscriminatory business justification a lender must demonstrate for a practice that produces a disparate impact on a protected class. Even where business necessity is shown, the practice may still be unlawful if a less-discriminatory alternative exists that serves the same legitimate objective.

**Calibration.** The degree to which a model's predicted probabilities match observed frequencies — a well-calibrated PD model that assigns 8% default probability to a group should see roughly 8% of that group default. Calibration is distinct from discrimination: a model can rank borrowers well (high ROC-AUC) yet systematically over- or under-state absolute risk. Calibration is assessed via reliability diagrams and summary error statistics whose governing tolerance is specified in §10.

**Challenger.** An alternative candidate model evaluated against the incumbent champion to test whether it materially improves on the production model. The champion/challenger paradigm institutionalizes effective challenge by requiring every promotion candidate to demonstrably outperform, or at minimum not regress against, the current production model.

**Champion.** The model version currently designated for production decisioning, identified in the registry by the production-serving alias. Under this dossier's conservative promotion philosophy, the champion is displaced only when a challenger satisfies all binding criteria and the change is formally approved; the criteria are specified in §10–§13.

**Class imbalance.** The condition in which one outcome class is far more frequent than the other, as is typical in consumer-credit default data where non-defaulters greatly outnumber defaulters. Class imbalance motivates the use of ranking and per-class metrics (ROC-AUC, macro-averaged F1, precision/recall) over raw accuracy and informs sampling and threshold choices.

**Conceptual soundness.** The SR 11-7 evaluation of whether a model's design, theory, logic, and assumptions are appropriate for its intended purpose and supported by generally accepted methods. Conceptual soundness review examines variable selection, the modeling methodology, and the reasonableness of design choices before any consideration of empirical performance.

**Confusion matrix.** A two-by-two table cross-tabulating predicted versus actual classes into true positives, false positives, true negatives, and false negatives. It is the foundation from which accuracy, precision, recall, and related metrics are derived and is reported in the validation package for a chosen decision threshold.

**Cross-validation.** A resampling procedure that partitions training data into multiple folds, repeatedly training on a subset and evaluating on the held-out remainder, to estimate generalization performance more stably than a single split. Cross-validation is used during development and hyperparameter selection; the final promotion evaluation relies on the dedicated held-out test partition rather than cross-validation folds.

**Decision threshold.** The cutoff applied to a model's continuous predicted probability to produce a binary decision — for the PD classifier, the probability above which a borrower is classified as a likely defaulter. The threshold trades off precision against recall and is set deliberately rather than defaulting to 0.5; its governing value is specified in §10/§13.

**Demographic-parity difference.** A group-fairness metric equal to the difference in the rate of positive (e.g., adverse) outcomes across protected-attribute groups, with zero indicating exact parity. In this dossier it is computed across the protected attributes age_group, gender, and region, and its allowable magnitude is specified in §12.

**Disparate impact.** A fair-lending harm arising when a facially neutral policy or model produces a significantly worse outcome for a protected class, regardless of intent. Disparate impact is evaluated statistically (e.g., via the disparate-impact ratio and demographic-parity difference) and, if found, requires a business-necessity justification and a search for less-discriminatory alternatives.

**Disparate-impact ratio.** The ratio of the favorable-outcome rate for a protected group to that of the most-favored group, used to quantify disparate impact. It is the basis for the four-fifths rule of thumb; the governing threshold applied in this dossier is specified in §12.

**Disparate treatment.** A fair-lending violation in which an applicant is treated differently because of a protected characteristic, whether overtly or through a close proxy. Including a protected attribute or a prohibited proxy such as region_risk_index as a model input is a disparate-treatment concern, distinct from the outcome-based concept of disparate impact.

**Drift.** A change over time in the statistical properties of model inputs (feature/covariate drift) or in the relationship between inputs and outcomes (concept drift), which can erode model validity after deployment. Drift is detected through ongoing monitoring metrics such as the population stability index and triggers review or remediation per §13.

**Effective challenge.** Under SR 11-7, the critical analysis of a model by objective, informed parties with the competence, influence, and incentive to identify and escalate limitations and propose changes. It is operationalized in this dossier through independent validation, benchmarking against challengers, and the separation of development from review.

**Equal Credit Opportunity Act (ECOA).** The U.S. federal statute prohibiting creditors from discriminating against applicants on the basis of protected characteristics including race, color, religion, national origin, sex, marital status, age, and receipt of public assistance. ECOA, implemented through Regulation B, is the principal legal authority governing the fair-lending controls applied to the PD model.

**Equal opportunity.** A group-fairness criterion requiring that the true-positive rate (or, symmetrically, the false-negative rate) be equal across protected groups, so that qualified applicants have an equal chance of a favorable outcome regardless of group membership. It is one of several fairness lenses considered alongside demographic-parity difference.

**Experiment.** In MLflow, a named container that groups related runs, typically corresponding to a modeling effort or project. The PD model's development and evaluation runs are organized under designated experiments so that candidate runs can be compared and traced.

**Feature.** An individual measurable input variable supplied to the model, such as an applicant attribute or a derived ratio. Feature selection is governed by both predictive value and fair-lending constraints; protected attributes and prohibited proxies are excluded from the model's feature set even where they might be predictive.

**Feature importance.** A set of techniques that quantify each feature's contribution to a model's predictions, used to assess conceptual soundness, detect reliance on proxies, and support explainability. Importance rankings are logged as run artifacts and reviewed during validation.

**Four-fifths rule.** A regulatory rule of thumb under which a selection (or favorable-outcome) rate for a protected group below four-fifths (80%) of the rate for the most-favored group is treated as evidence of adverse impact. It informs the interpretation of the disparate-impact ratio; the binding threshold used here is specified in §12.

**Gender.** One of the three protected attributes tracked for fairness testing in this dossier. Gender is never used as a model feature; it is retained solely to compute group-fairness metrics such as the demographic-parity difference across gender groups.

**Gradient boosting.** A supervised learning method that builds an ensemble of decision trees sequentially, with each tree fit to correct the errors of the accumulated ensemble, yielding a strong nonlinear classifier. It is a candidate modeling methodology for the PD classifier; its specific hyperparameters are specified in §11 and are not restated here.

**Held-out test set.** The data partition reserved entirely from training and validation and used only for final, unbiased performance estimation prior to promotion. Touching the test set during development invalidates it as an honest measure of generalization; the partitioning scheme and its random seed are specified in §11.

**Hyperparameter.** A configuration value set before training that governs the learning process or model structure (for example, the number of boosting iterations, learning rate, tree depth, or regularization strength), as opposed to parameters learned from data. The governing hyperparameter settings for the PD model are specified in §11.

**Lineage.** The recorded provenance linking a model version to the data, code, parameters, environment, and run that produced it, enabling traceability from a production decision back to its origins. Complete lineage is a precondition for reproducibility and for the auditability required by model-risk governance.

**Logged model.** A model object recorded to an MLflow run in a standardized flavor/format, capturing the trained artifact together with its dependencies and signature so it can later be loaded and served consistently. A logged model is the candidate that, upon approval, becomes a registered model version.

**Logistic regression.** A linear classification method that models the log-odds of the positive class as a linear combination of features, producing interpretable coefficients and calibrated probabilities. It serves both as a transparent candidate methodology and as a simple challenger benchmark for more complex models.

**Macro-averaged F1.** The unweighted mean of the per-class F1 scores, where F1 is the harmonic mean of precision and recall. By averaging across classes equally, the macro-averaged F1 prevents the majority (non-default) class from dominating the metric, making it suitable for the imbalanced PD problem; its governing minimum is specified in §10.

**Meridian Financial, N.A.** The fictional national bank that is the subject of this governance dossier and the institution within which the consumer-credit PD classifier is developed, validated, promoted, and monitored. All policies, roles, and thresholds described herein apply to Meridian Financial's model-risk environment.

**MLflow.** The open-source platform used at Meridian Financial for experiment tracking, model packaging, and model lifecycle management. Its tracking server, registry, and aliasing features provide the technical backbone for reproducible, governed promotion of the PD model.

**Model.** A quantitative method, system, or approach that applies statistical, economic, financial, or mathematical techniques to process input data into output estimates. In SR 11-7 terms, the PD classifier is a model, and its full lifecycle is subject to model-risk management controls.

**Model registry.** The MLflow component that catalogs registered models, their versions, stages, and aliases, providing a governed system of record for which model is approved for which use. Promotion actions, including repointing the production alias, are performed and recorded in the registry.

**Model risk.** The potential for adverse consequences — financial loss, poor business decisions, or reputational and regulatory harm — arising from errors in a model's design, implementation, or use, or from using a model incorrectly. Managing model risk is the overarching purpose of this dossier and the governance regime it describes.

**Model version.** An immutable, numbered snapshot of a registered model produced when a logged model is registered, capturing a specific trained artifact and its metadata. Aliases such as the champion pointer reference a particular model version; promotion changes which version the alias targets.

**Monitoring.** The ongoing post-deployment surveillance of a model's performance, stability, and fairness, encompassing drift detection, calibration tracking, and outcomes analysis. Monitoring requirements and the metrics that trigger escalation or rollback are specified in §13.

**One-hot encoding.** A preprocessing technique that converts a categorical variable into a set of binary indicator columns, one per category, enabling models that require numeric input to consume categorical features without imposing a spurious ordinal relationship. The encoding scheme applied to the PD model's categorical inputs is part of the reproducible preprocessing pipeline.

**Outcomes analysis.** The SR 11-7 practice of comparing model outputs to actual realized results to evaluate model quality and performance over time. For the PD model, outcomes analysis compares predicted default probabilities to observed default experience and is central to ongoing monitoring.

**Overfitting.** The condition in which a model learns idiosyncratic noise in the training data rather than the underlying signal, producing strong training performance but degraded generalization to unseen data. Overfitting is guarded against through regularization, validation on held-out data, and scrutiny of the gap between training and test metrics.

**Population stability index (PSI).** A metric that quantifies the shift in the distribution of a variable or of model scores between a baseline period and a current period, summing the contribution of each bin to an overall divergence measure. PSI is a primary drift-monitoring statistic; the thresholds at which it triggers review or action are specified in §13.

**Precision.** Among the cases a model predicts as positive (likely default), the proportion that are truly positive — a measure of how trustworthy a positive prediction is. Precision trades off against recall as the decision threshold moves and is reported alongside recall in the validation package.

**Probability of default (PD).** The model's estimated likelihood that a given borrower will default within the defined 12-month performance window. PD is the central quantity the classifier produces; it is converted to a classification via the decision threshold and is the basis for downstream credit decisions and calibration assessment.

**Prohibited proxy.** A feature that, while not itself a protected attribute, is so correlated with one that using it effectively reintroduces the protected characteristic into decisioning. In this dossier the geographic variable region_risk_index is treated as a prohibited proxy and is excluded from the model's feature set.

**Protected attribute / protected class.** A characteristic that fair-lending law shields from discriminatory treatment, and the group of persons sharing it. This dossier tracks age_group, gender, and region as protected attributes for fairness testing; they are used only to measure fairness, never as model inputs.

**Random seed.** A fixed integer that initializes pseudorandom processes — data splitting, model initialization, sampling — so that those processes produce identical results on re-execution. Recording the seed is essential to reproducibility; the governing seed for the PD model's data split is specified in §11.

**RACI.** A responsibility-assignment framework that labels each party to an activity as Responsible, Accountable, Consulted, or Informed, clarifying ownership and decision rights. The dossier uses RACI matrices to allocate duties across the model lifecycle and to reinforce separation of duties.

**Recall.** Among the cases that are truly positive (actual defaults), the proportion the model correctly identifies — a measure of coverage of the default population. High recall is important for credit-risk management because missed defaulters represent unrecognized loss exposure; recall is reported with precision at the operating threshold.

**Region.** One of the three protected attributes tracked for fairness testing. Region is monitored for disparate impact via group-fairness metrics, and any geographic risk proxy derived from it — notably region_risk_index — is prohibited as a model feature.

**Registered model.** A named entry in the MLflow Model Registry that organizes the successive versions of a particular model under a single governed identity. Registration moves a logged model from a transient run artifact into the controlled lifecycle where promotion, aliasing, and approval occur.

**Regularization.** A family of techniques that penalize model complexity during training to discourage overfitting and improve generalization, such as L1/L2 penalties on coefficients or constraints on tree ensembles. The regularization settings applied to the PD model are part of its hyperparameter configuration specified in §11.

**Regulation B.** The implementing regulation of the Equal Credit Opportunity Act, which sets out detailed creditor obligations including the prohibition on collecting or using certain protected information in underwriting and the requirements for adverse-action notices. Regulation B operationalizes the constraints that exclude protected attributes and proxies from the model.

**Reliability diagram.** A calibration plot that compares predicted probabilities (binned) against observed outcome frequencies, with the diagonal representing perfect calibration. It is logged as a validation artifact and read together with summary calibration error to judge whether the PD estimates are trustworthy in absolute terms.

**Reproducibility.** The ability to regenerate a model's results exactly from the recorded data, code, environment, parameters, and random seed. Reproducibility is a foundational governance requirement, ensuring that a promoted model version can be independently rebuilt and audited.

**Rollback.** The reversion of the production-serving alias from a newly promoted champion back to the prior model version when post-deployment monitoring reveals unacceptable performance, drift, or fairness degradation. Rollback conditions and procedures are specified in §13 and reflect the dossier's conservative promotion philosophy.

**Run.** A single execution recorded in MLflow, capturing the parameters, metrics, tags, and artifacts produced by one training or evaluation invocation. Runs are the atomic unit of experiment tracking and the source from which logged models and their lineage derive.

**Separation of duties.** The control principle that no single individual should both develop and independently approve or validate the same model, reducing the risk of unchecked error or bias. It underpins the three-lines-of-defense structure and is encoded in the dossier's RACI assignments.

**SR 11-7.** The U.S. interagency supervisory guidance on model risk management (Federal Reserve SR 11-7 / OCC 2011-12) that defines model risk and prescribes a framework of conceptual soundness review, ongoing monitoring, outcomes analysis, and effective challenge. It is the principal regulatory foundation for this dossier's governance regime.

**Standardization.** A preprocessing step that rescales a numeric feature to zero mean and unit variance (or a comparable scale), placing features on comparable footing for models sensitive to magnitude. Standardization parameters are fit on training data only and reused on validation and test data to avoid leakage.

**Stratified sampling.** A sampling or splitting method that preserves the proportion of each class (and, where relevant, of protected groups) across the resulting partitions, ensuring that minority outcomes such as defaults are represented in every split. The PD model's train/validation/test partitioning uses stratification under the configuration specified in §11.

**Three lines of defense.** The governance model in which the first line owns and manages risk (model development and ownership), the second line provides independent oversight and challenge (model-risk management and validation), and the third line provides independent assurance (internal audit). This structure operationalizes effective challenge and separation of duties.

**Tracking server.** The MLflow service that records runs, their metadata, and pointers to the artifact store, providing the centralized system of record for experimentation. It is the authoritative source for the metrics and lineage that feed validation and promotion decisions.

**Train/validation/test split.** The partitioning of available data into three disjoint sets used respectively to fit the model, to tune and select among configurations, and to provide a final unbiased performance estimate. The proportions, stratification, and random seed governing this split are specified in §11.

**Validation package.** The assembled body of evidence — metrics, plots, fairness analyses, conceptual-soundness findings, and documentation — submitted for independent review to support a promotion decision. Its required contents and the criteria against which it is judged are specified in §10–§13.


## §24 Appendices

The appendices collected in this section are **reference material only and are NON-BINDING**. Where a current operating criterion would otherwise appear (for example, a metric floor, a registry identifier, a split ratio, or a fairness ceiling), the cell deliberately points to the binding clause in §6–§13 rather than restating a number. This prevents the appendices from drifting out of step with the controlling text and removes any ambiguity about which value governs a promotion decision. Historical values reproduced below from Edition 1 (2023, MRM-GOV-CCD-0102) and Edition 2 (2024, MRM-GOV-CCD-0219) are **retired** and are retained solely for audit traceability and to document the evolution of the control framework. They must not be cited as current acceptance criteria under any circumstances.

In the event of any conflict between an appendix and the governing sections, §6–§13 prevail. Validators encountering a numeric value in an appendix that appears to contradict the body of the dossier should treat the appendix entry as superseded and escalate to the Model Risk Management (MRM) function for correction in the next edition.

---

### Appendix A — Superseded Threshold History

This appendix records the acceptance and governance parameters as they stood in each prior edition of the dossier, plus the current edition's pointers to binding clauses. The purpose is to give validators, auditors, and the Model Risk Committee (MRC) a single chronological view of how the promotion bar has tightened and how the governance mechanism has changed across the three editions. Editions 1 and 2 values are reproduced verbatim from the retired documents and are **not** acceptance criteria for any model promoted under Edition 3.

| Parameter | Edition 1 (2023, CCD-0102) — RETIRED | Edition 2 (2024, CCD-0219) — RETIRED | Edition 3 (2026, CCD-0327) — CURRENT |
|---|---|---|---|
| Accuracy floor | 0.80 | 0.80 | see §10 |
| ROC-AUC floor | 0.82 | 0.81 | see §10 |
| Primary ranking metric | accuracy | macro-F1 (≥ 0.75 bar) | see §11 |
| Train/validation/test split | 80/10/10 | 70/15/15 | see §7 |
| Random seed | 7 | 13 | see §7 |
| Regional disparity ceiling | 0.20 | (not separately bounded) | see §12 |
| Gender disparity ceiling | (not separately bounded) | 0.06 | see §12 |
| Fairness metric basis | regional disparity ratio | demographic-parity-difference | see §12 |
| Promotion mechanism | MLflow **Production** stage | MLflow **Production** stage | see §7 |
| Registered model name | meridian_risk_model_v1 | (see Appendix B) | see §6 |
| Artifact path | model | (see Appendix B) | see §6 |

**Narrative notes on the threshold history.**

The trajectory across editions reflects three deliberate shifts in MRM philosophy. First, the **ranking metric** moved away from raw accuracy. Edition 1 ranked candidate models on accuracy, which on the consumer-credit portfolio is sensitive to the prevailing default base rate and can mask poor minority-class (default) detection. Edition 2 replaced this with macro-F1 guarded by a 0.75 bar, recognising that balanced recall across the repaid/default classes matters more for credit-loss avoidance than headline accuracy. The Edition 3 ranking approach is defined in §11 and should be read there.

Second, the **fairness control basis** was reworked. Edition 1 used a coarse regional disparity ratio with a wide 0.20 ceiling, which proved too permissive and did not align cleanly with Regulation B expectations around disparate impact. Edition 2 introduced a demographic-parity-difference construction with a much tighter 0.06 gender ceiling but did not separately bound regional outcomes, creating a gap. Edition 3 consolidates the fairness controls across the protected attributes age_group, gender, and region; the binding construction and ceilings are in §12.

Third, the **promotion mechanism** changed materially. Editions 1 and 2 both relied on the deprecated MLflow model **stage** transition (promotion into the "Production" stage). Following MLflow's deprecation of stage-based transitions in favour of model version aliases, Edition 3 governs promotion through an MLflow **alias** rather than a stage. The binding alias semantics, the controlling alias name, and the transition controls are specified in §6 and must not be inferred from this table.

A practical consequence of the stage-to-alias migration deserves emphasis for validators reconstructing historical decisions. Under Editions 1 and 2, the audit record of "which model was in production on date *D*" depended on the stage-transition event log, which recorded the moment a version entered or left the Production stage. Under Edition 3, the equivalent record is the alias-assignment history on the registered model. When auditing a promotion that straddles the Edition 2→3 boundary, both records may need to be consulted: the stage log for the pre-2026 period and the alias-assignment history thereafter. The Secretariat maintains a crosswalk between the two for the transition window. Validators should not assume that a version showing the deprecated "Production" stage label is currently promoted; under Edition 3, only the alias defined in §6 confers production status, and a residual legacy stage label carries no governance weight.

Finally, note that the **accuracy floor** held constant at 0.80 across both retired editions even as the ROC-AUC floor was relaxed from 0.82 to 0.81 between Editions 1 and 2. This was a deliberate choice: the MRC judged that the discrimination bar (ROC-AUC) could be modestly loosened once macro-F1 ranking was introduced to guard minority-class detection, while the accuracy floor remained a simple, interpretable guard for the supervisory audience. The Edition 3 floors are re-baselined and are stated only in §10.

---

### Appendix B — Registry Naming and Convention History

This appendix tracks the registered-model naming conventions and artifact-path conventions used across editions. As with Appendix A, the Edition 3 conventions are pointers; the binding registry identifiers, naming rules, and artifact-path requirements are defined in §6.

| Convention element | Edition 1 (2023) — RETIRED | Edition 2 (2024) — RETIRED | Edition 3 (2026) — CURRENT |
|---|---|---|---|
| Registered model name | meridian_risk_model_v1 | renamed mid-cycle (see note 1) | see §6 |
| Logged artifact path | model | model (carried over) | see §6 |
| Versioning scheme | name-embedded suffix (_v1) | name-embedded suffix deprecated | see §6 |
| Promotion pointer | Production stage label | Production stage label | alias-based (see §6) |
| Experiment naming | free-text per analyst | standardised prefix introduced | see §6 |
| Run tagging requirements | minimal (owner only) | owner + edition tag | see §6 |

**Convention narrative.**

*Note 1 — name-embedded version suffixes.* Edition 1 embedded the version directly in the registered model name (`meridian_risk_model_v1`). This was identified during the Edition 2 review as an anti-pattern: it caused the registry to accumulate parallel `_v1`, `_v2` entries that fragmented lineage and broke the assumption that a single registered model carries an ordered sequence of versions. Edition 2 began the migration away from name-embedded suffixes, and Edition 3 completes it — the registered model name is now stable and version-agnostic, with versioning handled natively by the registry. The current name is given in §6 and is **not** `meridian_risk_model_v1`.

*Note 2 — artifact path.* The Edition 1 and Edition 2 logged artifact path was the generic `model`. This was retained for backward compatibility through Edition 2 but is **retired** in Edition 3 because the generic path obscured which flavour and signature were being promoted when multiple artifacts were logged in a single run. The binding artifact path for Edition 3 is specified in §6.

*Note 3 — promotion pointer.* The stage-label promotion pointer ("Production") used in Editions 1 and 2 is retired. Edition 3 uses an MLflow alias on a specific model version as the production pointer; see §6.

---

### Appendix C — Committee Rosters

The two standing committees governing model promotion at Meridian Financial, N.A. are the **Model Risk Committee (MRC)**, which holds final promotion authority, and the **Feature Governance Committee (FGC)**, which adjudicates predictor admissibility, protected-attribute handling, and proxy-variable exclusions. Rosters are as of the Edition 3 effective date (2026-01-01). All names are fictional. Quorum and voting rules are summarised beneath each table; the binding voting thresholds and escalation paths are in §13.

**C.1 — Model Risk Committee (MRC).**

| Member | Role / Title | Committee Role | Voting Status |
|---|---|---|---|
| Dr. Helena Voss | Chief Model Risk Officer | Chair | Voting |
| Marcus Lindqvist | Head of Model Validation | Deputy Chair | Voting |
| Priya Raghavan | Lead Quantitative Validator, Credit | Member | Voting |
| Thomas Okonkwo | Head of Consumer Credit Analytics | Member | Voting |
| Sofia Marchetti | Director, Fair Lending & Compliance | Member | Voting |
| Daniel Reyes | Head of Model Deployment / MLOps | Member | Voting |
| Aisha Bello | Senior Counsel, Regulatory Affairs | Member | Non-voting (advisory) |
| Jonas Weber | Internal Audit Liaison | Observer | Non-voting (observer) |
| Rebecca Tanaka | MRM Secretariat | Secretary | Non-voting (recording) |

*MRC quorum and voting.* Quorum requires the Chair or Deputy Chair plus a majority of voting members. Promotion decisions require a supermajority of voting members present, with the Fair Lending & Compliance seat holding a documented objection right on fairness grounds. Detailed quorum counts and tie-breaking rules are binding under §13 and are not restated here. The Internal Audit Liaison attends in an observer capacity and does not vote, preserving audit independence.

**C.2 — Feature Governance Committee (FGC).**

| Member | Role / Title | Committee Role | Voting Status |
|---|---|---|---|
| Dr. Nadia Osei | Head of Feature Governance | Chair | Voting |
| Eli Grossman | Principal Data Scientist, Credit Risk | Member | Voting |
| Carmen Flores | Fair Lending Data Analyst | Member | Voting |
| Raj Malhotra | Data Engineering Lead | Member | Voting |
| Yuki Tanabe | Privacy & Data Protection Officer | Member | Voting |
| Sofia Marchetti | Director, Fair Lending & Compliance | Cross-committee liaison (from MRC) | Voting |
| Liam Donovan | Model Validation Representative | Member | Non-voting (advisory) |
| Grace Mbeki | FGC Secretariat | Secretary | Non-voting (recording) |

*FGC mandate.* The FGC maintains the approved-predictor list (income, loan_amount, dti_ratio, credit_score, employment_years, num_open_accounts, home_ownership, loan_purpose), enforces the exclusion of protected attributes (age_group, gender, region) from the model's predictive feature set, and maintains the prohibited-proxy register — most notably the geographic proxy `region_risk_index`, which is barred as an impermissible proxy for the protected attribute region. The FGC reviews any proposed new predictor for proxy risk before it may enter a candidate model. Sofia Marchetti sits on both committees to ensure fair-lending consistency between feature admissibility and final promotion. The binding admissibility criteria and proxy-exclusion rules are in §8 and §12.

---

### Appendix D — Document Change Log / Revision History

This appendix records the document-level revision history across the three editions, including effective dates, authoring/approving owners, and a summary of the substantive control changes introduced by each edition. It is intended to support audit reconstruction of "what the rules were on a given date."

| Edition | Document Ref | Effective Date | Status | Lead Author | Approving Authority | Summary of Changes |
|---|---|---|---|---|---|---|
| Edition 1 | MRM-GOV-CCD-0102 | 2023-02-15 | Superseded | M. Lindqvist | MRC (Chair: H. Voss) | Initial governance framework. Accuracy-ranked promotion (floor 0.80), ROC-AUC floor 0.82, 80/10/10 split (seed 7), regional disparity ceiling 0.20, registered name meridian_risk_model_v1, artifact path `model`, promotion via MLflow Production stage. |
| Edition 2 | MRM-GOV-CCD-0219 | 2024-03-01 | Superseded | P. Raghavan | MRC (Chair: H. Voss) | Ranking metric changed to macro-F1 (0.75 bar); ROC-AUC floor relaxed to 0.81; accuracy floor held at 0.80; split changed to 70/15/15 (seed 13); fairness reworked to demographic-parity-difference with gender ceiling 0.06; began retirement of name-embedded version suffix; retained Production-stage promotion. |
| Edition 3 | MRM-GOV-CCD-0327 | 2026-01-01 | **Current / Binding** | N. Osei & D. Reyes | MRC (Chair: H. Voss) | Promotion mechanism migrated from MLflow stage to MLflow **alias** (champion alias; see §6). Registry name stabilised (version-agnostic; see §6). Fairness controls consolidated across age_group, gender, region using demographic-parity-difference (see §11). Acceptance floors, ranking metric, split/seed, and hyperparameters re-baselined (see §7, §8, §10). Approved-predictor list and prohibited-proxy register formalised under FGC (see §9). All current binding values reside in §6–§13. |

**Revision narrative.**

The 2023→2024 revision (Edition 1 to Edition 2) was driven primarily by validation findings that accuracy-ranked selection was rewarding models that under-detected defaults on imbalanced cohorts, and by Fair Lending feedback that the 0.20 regional ceiling was too loose to evidence compliance with disparate-impact expectations. Edition 2 addressed both by switching the ranking metric to macro-F1 and tightening fairness on the gender attribute, though it left a regional-fairness gap that was flagged for the next cycle.

The 2024→2026 revision (Edition 2 to Edition 3) was the most substantial. The dominant driver was the deprecation of MLflow stage-based model transitions, which forced a move to alias-based promotion and a corresponding rewrite of §6. The MRC took the opportunity to (a) close the regional-fairness gap by extending demographic-parity-difference controls across all three protected attributes, (b) stabilise the registry naming convention to eliminate name-embedded version suffixes, and (c) re-baseline the quantitative acceptance criteria and training configuration. Because the re-baselined numbers are binding, they are documented only in §6–§13 and are intentionally **not** reproduced anywhere in these appendices.

---

### Appendix E — Approved Acronyms and Reference List

This appendix lists the acronyms, regulatory references, and standards cited throughout the dossier, with a one-line description of each. Inclusion here is for reader convenience and does not modify any obligation; the operative requirements derive from the cited authorities and from §6–§13.

**E.1 — Regulatory and supervisory references.**

| Reference | Issuer | One-line description |
|---|---|---|
| SR 11-7 | Federal Reserve / OCC | Supervisory guidance on model risk management; defines the model lifecycle, validation, and effective challenge expectations underpinning this dossier. |
| OCC 2011-12 | OCC | OCC companion bulletin adopting the SR 11-7 model risk management framework for national banks such as Meridian Financial, N.A. |
| ECOA | Federal statute | Equal Credit Opportunity Act; prohibits credit discrimination on the basis of protected characteristics, motivating the protected-attribute and fairness controls. |
| Regulation B | CFPB (12 CFR 1002) | Implements ECOA; governs adverse-action notices and disparate-impact considerations relevant to PD model deployment. |
| SR 15-18 | Federal Reserve | Supervisory expectations for capital planning and stress testing at large institutions; context for model governance rigor. |
| BCBS 239 | Basel Committee | Principles for effective risk data aggregation and risk reporting; informs data lineage and reporting controls in the validation package. |
| NIST AI RMF | NIST (AI 100-1) | AI Risk Management Framework; voluntary framework informing governance, fairness, and documentation practices applied here. |

**E.2 — Acronyms and terms.**

| Acronym / Term | Expansion / meaning |
|---|---|
| PD | Probability of Default — the 12-month consumer-credit default likelihood the classifier predicts. |
| MRM | Model Risk Management — the function owning this dossier and the validation framework. |
| MRC | Model Risk Committee — body holding final promotion authority (Appendix C.1). |
| FGC | Feature Governance Committee — body governing predictor admissibility and proxy exclusion (Appendix C.2). |
| MLOps | Machine Learning Operations — deployment/registry engineering discipline. |
| ROC-AUC | Area under the Receiver Operating Characteristic curve — a rank-discrimination metric. |
| DTI | Debt-to-income ratio — the `dti_ratio` approved predictor. |
| DPD | Demographic-Parity-Difference — the fairness construction used for protected-attribute disparity (see §12). |
| Alias | An MLflow model-version alias used as the production promotion pointer (see §6). |
| Champion | The alias designation for the currently promoted production model version (binding semantics in §6). |
| Proxy variable | A predictor that stands in for a protected attribute; prohibited proxies (e.g., region_risk_index) are barred (see §8/§12). |
| Edition | A numbered, dated revision of this governance dossier (see Appendix D). |

---

### Appendix F — Validation Package Checklist

A promotion submission to the MRC must include a complete validation package. The table below enumerates the required contents. The checklist is a completeness aid; the binding acceptance thresholds, the split/seed configuration, the hyperparameter baseline, and the fairness ceilings against which the submitted evidence is judged are all defined in §6–§13 and are intentionally not restated here. A package missing any "Required" item is returned without review.

| # | Checklist item | Description | Requirement |
|---|---|---|---|
| 1 | Model card | Standardised model card: intended use, scope, owner, version, training date. | Required |
| 2 | Data lineage statement | Source systems, extraction date, row counts, and BCBS 239-aligned lineage for training/validation/test data. | Required |
| 3 | Predictor manifest | Explicit list of features used, confirmed against the FGC approved-predictor list. | Required |
| 4 | Protected-attribute exclusion attestation | Signed confirmation that age_group, gender, and region are excluded from the predictive feature set. | Required |
| 5 | Prohibited-proxy attestation | Signed confirmation that region_risk_index and any other registered proxies are excluded. | Required |
| 6 | Split configuration evidence | Evidence of the train/validation/test split ratio and random seed actually used (must match §7). | Required |
| 7 | Hyperparameter record | Full record of training hyperparameters used for the candidate (must match the baseline in §9). | Required |
| 8 | Discrimination metrics | ROC-AUC and accuracy on the held-out test set, with comparison to the floors in §10. | Required |
| 9 | Ranking metric evidence | The primary ranking metric value and any guard bar, computed per §11. | Required |
| 10 | Fairness assessment | Demographic-parity-difference results for age_group, gender, and region against the ceilings in §12. | Required |
| 11 | Calibration evidence | Reliability/calibration analysis of predicted PD against observed default rates. | Required |
| 12 | Stability / drift analysis | Population and feature stability indices versus the prior champion's training population. | Required |
| 13 | Challenger comparison | Side-by-side performance and fairness comparison against the incumbent champion version. | Required |
| 14 | MLflow run reference | Run ID, registered model name, version number, and logged artifact path (per §6). | Required |
| 15 | Reproducibility package | Environment specification and code reference sufficient to reproduce reported metrics. | Required |
| 16 | Validator effective-challenge memo | Independent validation memo documenting challenge, findings, and disposition (SR 11-7). | Required |
| 17 | Fair Lending sign-off | Compliance review note from the Fair Lending & Compliance seat. | Required |
| 18 | Adverse-action mapping | Mapping of model outputs to Regulation B adverse-action reason codes. | Required |
| 19 | Monitoring plan | Post-promotion monitoring metrics, thresholds, and review cadence. | Required |
| 20 | Rollback plan | Documented procedure to revert the champion alias to the prior version (per §13). | Required |
| 21 | Known limitations register | Documented model limitations, assumptions, and out-of-scope use cases. | Conditional* |
| 22 | Prior-edition delta note | Note describing how the candidate differs from models built under retired editions, where relevant. | Conditional* |

\*Conditional items are required where applicable to the candidate (e.g., a known-limitations register is required whenever the validator has identified material limitations; a prior-edition delta note is required when a model was originally developed under a retired edition's configuration and is being re-validated under Edition 3).

**Submission and disposition.** A complete package is submitted to the MRM Secretariat, logged, and routed to an independent validator for effective challenge before the MRC convenes. The MRC's promotion decision, the controlling acceptance thresholds, and the alias-transition controls that take effect upon approval are governed by §6 and §10–§13, and the MRC voting rules in §13. Nothing in this checklist alters those binding requirements; it exists only to ensure that the evidence required to apply them is present and complete at the time of review.

