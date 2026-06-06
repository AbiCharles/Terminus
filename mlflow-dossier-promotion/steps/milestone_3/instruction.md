Milestone 3 — promote the compliant champion.

Apply the dossier's gates to the candidate runs you logged in milestone 2. Disqualify any candidate that misses an acceptance threshold, then disqualify any remaining candidate that breaches a fairness ceiling for any protected attribute. From whatever survives, choose the champion as the one with the best value of the policy's ranking metric.

Register that champion in the MLflow Model Registry under the policy's registered model name, promoting it from the run's logged model artifact, and assign it the policy's champion alias so the alias resolves to that version. The disqualified candidates stay as runs but must not be registered as the champion.
