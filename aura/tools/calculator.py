"""Safe arithmetic calculator tool for AURA-1."""

from __future__ import annotations

import ast
import operator
from typing import Any

from aura.tools.base import Tool


class CalculatorTool(Tool):
    """Evaluate basic arithmetic without using eval()."""

    _OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }

    def __init__(self) -> None:
        super().__init__(
            name="calculator",
            description="Calcula expressões aritméticas básicas de forma segura.",
        )

    def run(self, expression: str, **kwargs: Any) -> int | float:
        """Evaluate a safe arithmetic expression."""
        if kwargs or not isinstance(expression, str):
            raise ValueError("Indica apenas uma expressão matemática em texto.")
        expression = expression.strip()
        if not expression:
            raise ValueError("A expressão não pode estar vazia.")
        if len(expression) > 200:
            raise ValueError("A expressão é demasiado longa.")

        try:
            tree = ast.parse(expression, mode="eval")
        except SyntaxError as exc:
            raise ValueError("Expressão matemática inválida.") from exc

        return self._evaluate(tree.body)

    def _evaluate(self, node: ast.AST) -> int | float:
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
            if abs(node.value) > 10**12:
                raise ValueError("Os números são demasiado grandes.")
            return node.value

        if isinstance(node, ast.UnaryOp) and type(node.op) in self._OPERATORS:
            operand = self._evaluate(node.operand)
            return self._OPERATORS[type(node.op)](operand)

        if isinstance(node, ast.BinOp) and type(node.op) in self._OPERATORS:
            left = self._evaluate(node.left)
            right = self._evaluate(node.right)
            if isinstance(node.op, ast.Pow) and abs(right) > 100:
                raise ValueError("O expoente é demasiado grande.")
            try:
                result = self._OPERATORS[type(node.op)](left, right)
            except (ZeroDivisionError, OverflowError) as exc:
                raise ValueError("Não foi possível calcular a expressão.") from exc
            if isinstance(result, complex) or abs(result) > 10**12:
                raise ValueError("O resultado é demasiado grande.")
            return result

        raise ValueError("Só são permitidas operações aritméticas básicas.")
