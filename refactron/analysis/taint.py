"""
Taint Analysis Engine.
Tracks data flow from untrusted sources to sensitive sinks.
"""

import ast
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, NamedTuple, Set, Tuple

from .cfg.node import CFGNode
from .data_flow import DataFlowAnalyzer


class TaintSource(NamedTuple):
    name: str  # Function/Attribute name or variable name
    type: str  # 'function', 'variable', 'attribute'


class TaintSink(NamedTuple):
    name: str
    type: str
    arg_index: int = 0  # Which argument is sensitive?


@dataclass
class TaintConfig:
    sources: List[TaintSource] = field(default_factory=list)
    sinks: List[TaintSink] = field(default_factory=list)
    sanitizers: List[str] = field(default_factory=list)  # Functions that clean taint


# Default configuration for Python web/security context
DEFAULT_TAINT_CONFIG = TaintConfig(
    sources=[
        TaintSource("request", "variable"),  # Flask/Django request
        TaintSource("input", "function"),  # Standard input
        TaintSource("os.environ", "variable"),
        TaintSource("sys.argv", "variable"),
        TaintSource("argparse.ArgumentParser.parse_args", "function"),
        TaintSource("parse_args", "function"),  # Common alias for parser.parse_args()
    ],
    sinks=[
        TaintSink("eval", "function", 0),
        TaintSink("exec", "function", 0),
        TaintSink("os.system", "function", 0),
        TaintSink("subprocess.call", "function", 0),
        TaintSink("subprocess.run", "function", 0),
        TaintSink("sqlite3.execute", "function", 0),  # SQL Injection
    ],
    sanitizers=[
        "escape",
        "int",  # Casting to int usually sanitizes injection
        "float",
    ],
)


@dataclass
class TaintVulnerability:
    source: str
    sink: str
    node_id: int
    line_number: int
    variable: str
    message: str


class TaintAnalyzer:
    def __init__(self, cfg_entry: CFGNode, config: TaintConfig = DEFAULT_TAINT_CONFIG):
        self.cfg_entry = cfg_entry
        self.config = config
        self.data_flow = DataFlowAnalyzer(cfg_entry)

        # Helper maps for fast lookup
        self._sources = {s.name for s in config.sources}
        self._sinks = {s.name: s for s in config.sinks}
        self._sanitizers = set(config.sanitizers)

    def analyze(self) -> List[TaintVulnerability]:
        """
        Perform taint analysis.
        Returns a list of detected vulnerabilities.
        """
        # 1. Compute reaching definitions to help propagation
        # reaching_defs = self.data_flow.compute_reaching_definitions()

        # 2. Iterative Taint Propagation
        # taint_set[n] = set of tainted variable names at start of block n
        tainted_vars: Dict[int, Set[str]] = defaultdict(set)

        vulnerabilities = []

        # Simple iterative fixed-point might not be enough if we want path sensitivity
        # For MVP, we use a block-level propagation

        # Initialize worklist with all nodes (or just entry)
        # Using a topological sort would be better, but standard BFS/worklist works

        # We'll re-use the nodes list from data flow for iteration order
        nodes = self.data_flow.nodes

        changed = True
        while changed:
            changed = False
            for node in nodes:
                # Compute IN taint from predecessors
                incoming_taint = set()
                for pred in node.predecessors:
                    incoming_taint.update(tainted_vars[pred.id])

                # Process block statements
                current_taint = incoming_taint.copy()

                for stmt in node.statements:
                    # Check for Sink usage
                    vuls = self._check_sink(stmt, current_taint, node.id)
                    # We accumulate vulnerabilities but continue analysis
                    # De-duplicate vuls?
                    for v in vuls:
                        if v not in vulnerabilities:
                            vulnerabilities.append(v)

                    # Update Taint (Sources & Propagation)
                    new_taints, cleansed = self._propagate_taint(stmt, current_taint)
                    current_taint.update(new_taints)
                    current_taint.difference_update(cleansed)

                # If OUT taint changed, we might need to re-process successors?
                # For this simple implementation, we assume intra-block propagation is enough
                # IF variables persist across blocks.

                # Optimization: check if OUT set changed
                if current_taint != tainted_vars[node.id]:
                    tainted_vars[node.id] = current_taint
                    changed = True

        return vulnerabilities

    def _propagate_taint(self, stmt: ast.AST, current_taint: Set[str]) -> Tuple[Set[str], Set[str]]:
        """
        Analyze a statement and return (newly_tainted_vars, cleansed_vars).
        """
        generated = set()
        killed = set()

        if isinstance(stmt, (ast.Assign, ast.AnnAssign)):
            targets = []
            if isinstance(stmt, ast.Assign):
                targets = stmt.targets
            else:
                targets = [stmt.target]

            value = stmt.value  # type: ignore[union-attr, attr-defined]
            is_tainted = self._is_expression_tainted(value, current_taint)  # type: ignore[arg-type]

            for target in targets:
                if isinstance(target, ast.Name):
                    if is_tainted:
                        generated.add(target.id)
                    else:
                        # If assigning a clean value to a variable, it cleanses it
                        killed.add(target.id)

        return generated, killed

    def _is_expression_tainted(self, expr: ast.AST, current_taint: Set[str]) -> bool:
        """Check if an expression evaluates to a tainted value."""
        if isinstance(expr, ast.Name):
            # Check if variable is already tainted
            if expr.id in current_taint:
                return True
            # Check if it's a direct source (e.g. 'request')
            if expr.id in self._sources:
                return True

        elif isinstance(expr, ast.Call):
            # Check if function call returns taint (Source)
            func_name = self._get_call_name(expr)
            if func_name in self._sources:
                return True

            # Check if function call propagates taint (Sanitizer check)
            if func_name in self._sanitizers:
                return False

            # Default: propagate if any arg is tainted
            for arg in expr.args:
                if self._is_expression_tainted(arg, current_taint):
                    return True

        elif isinstance(expr, ast.BinOp):
            # Binary op is tainted if either side is tainted
            return self._is_expression_tainted(
                expr.left, current_taint
            ) or self._is_expression_tainted(expr.right, current_taint)

        elif isinstance(expr, ast.JoinedStr):
            # f-string: tainted if any value in it is tainted
            for value in expr.values:
                if isinstance(value, ast.FormattedValue):
                    if self._is_expression_tainted(value.value, current_taint):
                        return True
                elif self._is_expression_tainted(value, current_taint):
                    return True

        elif isinstance(expr, ast.Subscript):
            # Propagate from value (e.g. args.input)
            if self._is_expression_tainted(expr.value, current_taint):
                return True

        elif isinstance(expr, ast.Attribute):
            # Check specific attributes (e.g. os.environ)
            full_name = self._get_attribute_name(expr)
            if full_name in self._sources:
                return True
            # Propagate from object (simple object taint)
            if self._is_expression_tainted(expr.value, current_taint):
                return True

        return False

    def _check_sink(
        self, stmt: ast.AST, current_taint: Set[str], node_id: int
    ) -> List[TaintVulnerability]:
        """Check if a statement uses a tainted variable in a sink."""
        vuls = []

        # We need to traverse the statement to find Call nodes
        for node in ast.walk(stmt):
            if isinstance(node, ast.Call):
                func_name = self._get_call_name(node)
                if func_name in self._sinks:
                    sink_def = self._sinks[func_name]
                    # Check the sensitive argument
                    if len(node.args) > sink_def.arg_index:
                        arg = node.args[sink_def.arg_index]
                        if self._is_expression_tainted(arg, current_taint):
                            # Identify which variable caused it for reporting
                            var_name = "expression"
                            if isinstance(arg, ast.Name):
                                var_name = arg.id

                            vuls.append(
                                TaintVulnerability(
                                    source="untrusted input",  # Simplification
                                    sink=func_name,
                                    node_id=node_id,
                                    line_number=getattr(node, "lineno", 0),
                                    variable=var_name,
                                    message=(
                                        f"Tainted data from untrusted source reaches"
                                        f" sensitive sink '{func_name}' via '{var_name}'"
                                    ),
                                )
                            )
        return vuls

    def _get_call_name(self, node: ast.Call) -> str:
        """Extract function name from Call node."""
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            return self._get_attribute_name(node.func)
        return ""

    def _get_attribute_name(self, node: ast.Attribute) -> str:
        """Recursive attribute name extraction (e.g. os.path.join)."""
        if isinstance(node.value, ast.Name):
            return f"{node.value.id}.{node.attr}"
        elif isinstance(node.value, ast.Attribute):
            return f"{self._get_attribute_name(node.value)}.{node.attr}"
        return node.attr
