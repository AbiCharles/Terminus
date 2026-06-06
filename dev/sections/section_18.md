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
