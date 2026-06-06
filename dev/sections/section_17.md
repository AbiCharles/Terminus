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
