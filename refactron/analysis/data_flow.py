"""
Data Flow Analysis Engine.
Implements standard data flow analyses like Reaching Definitions.
"""

import ast
from collections import defaultdict
from typing import Dict, List, Set, Tuple

from .cfg.node import CFGNode


class DataFlowAnalyzer:
    def __init__(self, cfg_entry: CFGNode):
        self.entry_node = cfg_entry
        self.nodes = self._collect_nodes(cfg_entry)

    def _collect_nodes(self, entry: CFGNode) -> List[CFGNode]:
        """BFS to collect all reachable nodes."""
        nodes = []
        visited = set()
        queue = [entry]
        visited.add(entry.id)

        while queue:
            node = queue.pop(0)
            nodes.append(node)
            for succ, _ in node.successors:
                if succ.id not in visited:
                    visited.add(succ.id)
                    queue.append(succ)
        return sorted(nodes, key=lambda n: n.id)

    def compute_reaching_definitions(self) -> Dict[int, Set[Tuple[str, int]]]:
        """
        Compute Reaching Definitions for each block.
        Returns a map: node_id -> set of (variable_name, definition_node_id)
        definition_node_id can be the CFG node ID where it was defined.
        """
        # specialized sets for gen/kill
        # gen[n]: definitions generated in block n
        # kill[n]: definitions killed in block n
        gen: Dict[int, Set[Tuple[str, int]]] = defaultdict(set)
        kill: Dict[int, Set[str]] = defaultdict(set)

        # 1. Initialize Gen/Kill sets for each block
        for node in self.nodes:
            node_gen: Set[Tuple[str, int]] = set()
            node_kill = set()

            # Iterate statements to find assignments
            for stmt in node.statements:
                if isinstance(stmt, (ast.Assign, ast.AnnAssign)):
                    targets = []
                    if isinstance(stmt, ast.Assign):
                        targets = stmt.targets
                    else:
                        targets = [stmt.target]

                    for target in targets:
                        if isinstance(target, ast.Name):
                            var_name = target.id
                            # This definition kills previous definitions of 'var_name'
                            node_kill.add(var_name)
                            # And generates a new definition at this node
                            # Filter out any previous gen for the same var in this block
                            node_gen = {(v, d) for v, d in node_gen if v != var_name}
                            node_gen.add((var_name, node.id))

            gen[node.id] = node_gen
            kill[node.id] = node_kill

        # 2. Iterative Worklist Algorithm
        # in_set[n] = union(out_set[p] for p in predecessors)
        # out_set[n] = gen[n] union (in_set[n] - kill[n])

        in_sets: Dict[int, Set[Tuple[str, int]]] = defaultdict(set)
        out_sets: Dict[int, Set[Tuple[str, int]]] = defaultdict(set)

        changed = True
        while changed:
            changed = False
            for node in self.nodes:
                # Compute IN set
                new_in = set()
                for pred in node.predecessors:
                    new_in.update(out_sets[pred.id])

                if new_in != in_sets[node.id]:
                    in_sets[node.id] = new_in
                    # recompute OUT causes change?
                    # actually OUT depends on IN, so we just check if OUT changes

                # Compute OUT set
                # kill[node.id] is set of var names.
                # We remove any definition (v, d) where v is in kill set.
                preserved = {(v, d) for v, d in new_in if v not in kill[node.id]}
                new_out = gen[node.id].union(preserved)

                if new_out != out_sets[node.id]:
                    out_sets[node.id] = new_out
                    changed = True

        return in_sets

    def find_variable_usages(self) -> Dict[str, List[int]]:
        """
        Find where variables are used.
        Returns: var_name -> list of node_ids where used
        """
        usages = defaultdict(list)
        for node in self.nodes:
            for stmt in node.statements:
                for child in ast.walk(stmt):
                    if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Load):
                        usages[child.id].append(node.id)
        return usages
