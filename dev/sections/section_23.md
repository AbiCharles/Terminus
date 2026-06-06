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
