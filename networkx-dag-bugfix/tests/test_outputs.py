"""Hidden verifier for the dag_longest_path default_weight regression.

These checks are not present in the agent's vendored tree; the agent only has a
symptom description. They assert that nx.dag_longest_path honours default_weight,
and that the rest of the dag test module still passes (no regression).
"""
import subprocess
import sys

import networkx as nx


def test_default_weight_respected_multigraph():
    """dag_longest_path must apply default_weight to unweighted edges (multigraph case)."""
    G = nx.MultiDiGraph([(1, 2), (2, 3)])
    G.add_weighted_edges_from([(1, 3, 1), (1, 3, 5), (1, 3, 2)])
    assert nx.dag_longest_path(G) == [1, 3]
    assert nx.dag_longest_path(G, default_weight=3) == [1, 2, 3]


def test_default_weight_respected_digraph():
    """dag_longest_path must apply default_weight to unweighted edges (simple DiGraph)."""
    G = nx.DiGraph()
    G.add_edge(1, 2)
    G.add_edge(2, 3)
    G.add_edge(1, 3, weight=5)
    assert nx.dag_longest_path(G) == [1, 3]
    assert nx.dag_longest_path(G, default_weight=3) == [1, 2, 3]


def test_no_regression_in_dag_module():
    """The fix must not break the rest of networkx's dag test module."""
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q",
         "/app/networkx-src/networkx/algorithms/tests/test_dag.py"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, f"dag test module regressed:\n{result.stdout[-2000:]}"
