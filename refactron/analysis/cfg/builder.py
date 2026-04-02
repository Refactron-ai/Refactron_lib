"""
Control Flow Graph Builder.
Converts Python AST into a Control Flow Graph.
"""

import ast
from typing import List, Optional, Tuple

from .node import CFGNode, EdgeType


class CFGBuilder:
    def __init__(self) -> None:
        self.nodes: List[CFGNode] = []
        self.current_id = 0
        self.current_block: Optional[CFGNode] = None

        # Stack for managing control flow targets
        # loop_stack stores (break_target, continue_target)
        self.loop_stack: List[Tuple[CFGNode, CFGNode]] = []

    def _new_block(self) -> CFGNode:
        """Create a new basic block."""
        node = CFGNode(id=self.current_id)
        self.current_id += 1
        self.nodes.append(node)
        return node

    def build_from_source(self, source_code: str) -> CFGNode:
        """Build CFG from source code string."""
        tree = ast.parse(source_code)
        return self.build_from_ast(tree)

    def build_from_ast(self, tree: ast.AST) -> CFGNode:
        """Build CFG from AST."""
        entry_block = self._new_block()
        self.current_block = entry_block

        # We handle function definitions specially if we want interprocedural analysis later
        # For now, we process top-level code or body of functions
        if isinstance(tree, ast.Module):
            self._process_statements(tree.body)
        elif isinstance(tree, (ast.FunctionDef, ast.AsyncFunctionDef)):
            self._process_statements(tree.body)
        else:
            # Fallback for snippets
            self._visit(tree)

        return entry_block

    def _process_statements(self, statements: List[ast.stmt]) -> None:
        """Process a list of statements sequentially."""
        for stmt in statements:
            self._visit(stmt)

    def _visit(self, node: ast.AST) -> None:
        """Dispatch visitor method."""
        method_name = f"_visit_{node.__class__.__name__}"
        visitor = getattr(self, method_name, self._visit_generic)
        visitor(node)

    def _visit_generic(self, node: ast.AST) -> None:
        """Default visitor for simple statements."""
        if self.current_block is None:
            # Unreachable code or detached block
            self.current_block = self._new_block()

        self.current_block.statements.append(node)

    def _visit_If(self, node: ast.If) -> None:
        """Handle if statements."""
        if self.current_block is None:
            return

        # Condition evaluation is in the current block
        self.current_block.statements.append(node.test)
        condition_block = self.current_block

        # Prepare blocks
        then_block = self._new_block()
        else_block = self._new_block() if node.orelse else None
        join_block = self._new_block()

        # Connect condition to branches
        condition_block.add_successor(then_block, EdgeType.TRUE)
        if else_block:
            condition_block.add_successor(else_block, EdgeType.FALSE)
        else:
            condition_block.add_successor(join_block, EdgeType.FALSE)

        # Process THEN branch
        self.current_block = then_block
        self._process_statements(node.body)
        if self.current_block:  # If didn't return/break/raise
            self.current_block.add_successor(join_block, EdgeType.NORMAL)

        # Process ELSE branch
        if else_block:
            self.current_block = else_block
            self._process_statements(node.orelse)
            if self.current_block:
                self.current_block.add_successor(join_block, EdgeType.NORMAL)

        self.current_block = join_block

    def _visit_For(self, node: ast.For) -> None:
        """Handle for loops."""
        if self.current_block is None:
            return

        # Initialization logic (iterating) happens in loop_head
        loop_head = self._new_block()
        self.current_block.add_successor(loop_head, EdgeType.NORMAL)

        loop_body = self._new_block()
        loop_exit = self._new_block()

        # Head connects to Body (True) and Exit (False/Done)
        loop_head.statements.append(node.iter)  # Approximation
        loop_head.add_successor(loop_body, EdgeType.TRUE)
        loop_head.add_successor(loop_exit, EdgeType.FALSE)

        # Push loop context for break/continue
        self.loop_stack.append((loop_exit, loop_head))

        # Process Body
        self.current_block = loop_body
        # Assignment of target happens at start of body
        self.current_block.statements.append(node.target)
        self._process_statements(node.body)

        # Loop back
        if self.current_block:
            self.current_block.add_successor(loop_head, EdgeType.NORMAL)

        # Handle orelse (executed if loop finishes normally, not via break)
        if node.orelse:
            orelse_block = self._new_block()
            # The "False" edge from head actually goes to orelse if present
            # Fix previous connection
            loop_head.successors = [s for s in loop_head.successors if s[1] != EdgeType.FALSE]
            loop_head.add_successor(orelse_block, EdgeType.FALSE)

            self.current_block = orelse_block
            self._process_statements(node.orelse)
            if self.current_block:
                self.current_block.add_successor(loop_exit, EdgeType.NORMAL)

        self.loop_stack.pop()
        self.current_block = loop_exit

    def _visit_While(self, node: ast.While) -> None:
        """Handle while loops."""
        if self.current_block is None:
            return

        loop_head = self._new_block()
        self.current_block.add_successor(loop_head, EdgeType.NORMAL)

        loop_body = self._new_block()
        loop_exit = self._new_block()

        # Head evaluates condition
        loop_head.statements.append(node.test)
        loop_head.add_successor(loop_body, EdgeType.TRUE)
        loop_head.add_successor(loop_exit, EdgeType.FALSE)

        self.loop_stack.append((loop_exit, loop_head))

        # Body
        self.current_block = loop_body
        self._process_statements(node.body)
        if self.current_block:
            self.current_block.add_successor(loop_head, EdgeType.NORMAL)

        # Orelse
        if node.orelse:
            orelse_block = self._new_block()
            loop_head.successors = [s for s in loop_head.successors if s[1] != EdgeType.FALSE]
            loop_head.add_successor(orelse_block, EdgeType.FALSE)

            self.current_block = orelse_block
            self._process_statements(node.orelse)
            if self.current_block:
                self.current_block.add_successor(loop_exit, EdgeType.NORMAL)

        self.loop_stack.pop()
        self.current_block = loop_exit

    def _visit_Break(self, node: ast.Break) -> None:
        """Handle break statement."""
        if self.current_block is None:
            return

        self.current_block.statements.append(node)
        if self.loop_stack:
            break_target, _ = self.loop_stack[-1]
            self.current_block.add_successor(break_target, EdgeType.NORMAL)

        # Code after break is unreachable in this block
        self.current_block = None

    def _visit_Continue(self, node: ast.Continue) -> None:
        """Handle continue statement."""
        if self.current_block is None:
            return

        self.current_block.statements.append(node)
        if self.loop_stack:
            _, continue_target = self.loop_stack[-1]
            self.current_block.add_successor(continue_target, EdgeType.NORMAL)

        self.current_block = None

    def _visit_Return(self, node: ast.Return) -> None:
        """Handle return statement."""
        if self.current_block is None:
            return

        self.current_block.statements.append(node)
        # In a full implementation, this connects to the Exit block of the function
        self.current_block = None

    def _visit_Raise(self, node: ast.Raise) -> None:
        """Handle raise statement."""
        if self.current_block is None:
            return

        self.current_block.statements.append(node)
        # Connects to exception handler or Exit
        self.current_block = None
