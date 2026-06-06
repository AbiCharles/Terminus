import warnings
warnings.filterwarnings("ignore")
import numpy as np
import mlflow
import mlflow.sklearn
from mlflow.tracking import MlflowClient
from sklearn.linear_model import LogisticRegression

mlflow.set_tracking_uri("sqlite:////tmp/probe.db")
mlflow.set_experiment("probe")
X = np.random.rand(40, 3)
y = (X[:, 0] > 0.5).astype(int)
m = LogisticRegression().fit(X, y)
with mlflow.start_run() as run:
    info = mlflow.sklearn.log_model(m, name="credit_default_model")
    mlflow.log_metric("roc_auc", 0.9)
    rid = run.info.run_id

c = MlflowClient()
eid = mlflow.get_experiment_by_name("probe").experiment_id

# (1) does runs:/ uri still register in 3.x?
try:
    mv_runs = mlflow.register_model(f"runs:/{rid}/credit_default_model", "probe_runs")
    print("RUNS_URI_REGISTER ok v", mv_runs.version, "source:", mv_runs.source,
          "model_id:", getattr(mv_runs, "model_id", None))
except Exception as e:
    print("RUNS_URI_REGISTER FAIL:", repr(e)[:140])

# (2) register from models:/ uri and inspect ModelVersion attributes
mv = mlflow.register_model(info.model_uri, "probe_model")
print("MV attrs model_id:", getattr(mv, "model_id", None), "source:", mv.source, "run_id:", mv.run_id)

# (3) get_logged_model by id -> name
mid = info.model_id
lm = c.get_logged_model(mid)
print("GET_LOGGED_MODEL name:", lm.name, "id:", lm.model_id)

# (4) search logged models filtered by run
lms = c.search_logged_models(experiment_ids=[eid])
for x in lms:
    print("  LM:", x.name, "src_run:", x.source_run_id, "id:", x.model_id)

# (5) parse model_id out of a models:/ source
src = mv.source
print("PARSED_ID_FROM_SOURCE:", src.split("/")[-1], "==", mid, "?", src.split("/")[-1] == mid)
