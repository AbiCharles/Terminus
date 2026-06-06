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
