"""
Control Flow Graph Node definition.
Represents a basic block in the control flow graph.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, List, Tuple


class EdgeType(Enum):
    NORMAL = "normal"
    TRUE = "true"  # Branch taken
    FALSE = "false"  # Branch not taken
    EXCEPTION = "exception"


@dataclass
class CFGNode:
    id: int
    statements: List[Any] = field(default_factory=list)  # AST nodes in this block
    predecessors: List["CFGNode"] = field(default_factory=list)
    successors: List[Tuple["CFGNode", EdgeType]] = field(default_factory=list)

    def add_successor(self, node: "CFGNode", edge_type: EdgeType = EdgeType.NORMAL) -> None:
        self.successors.append((node, edge_type))
        node.predecessors.append(self)

    def __hash__(self) -> int:
        return self.id

    def __repr__(self) -> str:
        return f"CFGNode(id={self.id}, stmts={len(self.statements)})"
