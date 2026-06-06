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
