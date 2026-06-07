#!/usr/bin/env bash
set -euo pipefail

# Oracle fix: in dag_longest_path the predecessor edge-weight lookup falls back to
# a hardcoded 1 instead of the default_weight argument, so default_weight is
# ignored. Restore the default_weight fallback.
python3 - <<'PY'
f = "/app/networkx-src/networkx/algorithms/dag.py"
s = open(f).read()
old = ").get(weight, 1),"
new = ").get(weight, default_weight),"
assert s.count(old) == 1, f"expected exactly one buggy occurrence, found {s.count(old)}"
open(f, "w").write(s.replace(old, new, 1))
print("restored default_weight fallback in dag_longest_path")
PY
