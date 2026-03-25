"""
Integration tests for the new Semantic Analysis Engine.
Verifies CFG construction, Data Flow Analysis, and Taint Tracking.
"""

import ast

from refactron.analysis.cfg.builder import CFGBuilder, EdgeType
from refactron.analysis.data_flow import DataFlowAnalyzer
from refactron.analysis.taint import TaintAnalyzer, TaintConfig, TaintSink, TaintSource


def test_cfg_construction_simple_if():
    code = """
if x:
    y = 1
else:
    y = 2
z = y
"""
    builder = CFGBuilder()
    entry = builder.build_from_source(code)

    # Entry block contains 'if x' test
    assert len(entry.statements) == 1
    assert (
        isinstance(entry.statements[0], ast.If) is False
    )  # The If node visitor handles this, stmt list gets 'x' (test)

    # Check successors
    assert len(entry.successors) == 2
    true_branch = [n for n, t in entry.successors if t == EdgeType.TRUE][0]
    false_branch = [n for n, t in entry.successors if t == EdgeType.FALSE][0]

    assert len(true_branch.statements) == 1  # y = 1
    assert len(false_branch.statements) == 1  # y = 2

    # Both should converge
    assert len(true_branch.successors) == 1
    assert len(false_branch.successors) == 1
    join_block = true_branch.successors[0][0]
    assert join_block == false_branch.successors[0][0]

    assert len(join_block.statements) == 1  # z = y


def test_reaching_definitions():
    code = """
x = 1
y = 2
if z:
    x = 3
w = x
"""
    builder = CFGBuilder()
    entry = builder.build_from_source(code)

    dfa = DataFlowAnalyzer(entry)
    reaching_defs = dfa.compute_reaching_definitions()

    # Find the block with 'w = x' (should be the last join block)
    # entry -> if -> (then) -> join
    # entry -> if -> (else) -> join

    # Identify the join block by content 'w = x'
    join_block = None
    for node in dfa.nodes:
        if any(isinstance(s, ast.Assign) and s.targets[0].id == "w" for s in node.statements):
            join_block = node
            break

    assert join_block is not None

    # In join block, 'x' definition should reach from both entry (x=1) and then_block (x=3)
    defs_at_join = reaching_defs[join_block.id]

    # Filter for 'x'
    x_defs = {d for v, d in defs_at_join if v == "x"}

    # We expect 2 definitions of x to reach here
    # 1. from initial assignment (in entry block)
    # 2. from re-assignment (in true branch)
    # Wait, standard Reaching Defs is about what reaches the ENTRY of the block.
    # Entry block defines x=1.
    # True branch defines x=3.
    # False branch (implicit) preserves x=1.
    # So at Join, we should have {x from entry, x from true_branch}

    assert len(x_defs) >= 2


def test_taint_analysis_sql_injection():
    code = """
user_input = request.args.get('id')
query = "SELECT * FROM users WHERE id = " + user_input
cursor.execute(query)
"""
    builder = CFGBuilder()
    entry = builder.build_from_source(code)

    config = TaintConfig(
        sources=[TaintSource("request.args.get", "function")],
        sinks=[TaintSink("cursor.execute", "function", 0)],
        sanitizers=[],
    )

    analyzer = TaintAnalyzer(entry, config)
    vulnerabilities = analyzer.analyze()

    assert len(vulnerabilities) == 1
    vuln = vulnerabilities[0]
    assert vuln.variable == "query"
    assert "cursor.execute" in vuln.sink
    assert "request.args.get" in vuln.message or "source" in vuln.message


def test_taint_analysis_safe_path():
    code = """
user_input = request.args.get('id')
clean_input = int(user_input)
query = "SELECT * FROM users WHERE id = " + str(clean_input)
cursor.execute(query)
"""
    builder = CFGBuilder()
    entry = builder.build_from_source(code)

    config = TaintConfig(
        sources=[TaintSource("request.args.get", "function")],
        sinks=[TaintSink("cursor.execute", "function", 0)],
        sanitizers=["int"],
    )

    analyzer = TaintAnalyzer(entry, config)
    vulnerabilities = analyzer.analyze()

    # Should find NO vulnerabilities because 'int()' sanitizes
    assert len(vulnerabilities) == 0
