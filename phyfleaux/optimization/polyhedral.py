from __future__ import absolute_import
from __future__ import annotations

__license__ = """
Copyright (c) 2020 R. Tohid

Distributed under the Boost Software License, Version 1.0. (See accompanying
file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
"""

import ast
from copy import deepcopy
from typing import Union

from phyfleaux.core.task import Task
from phyfleaux.plugins.tiramisu import Buffer, Call, Computation, Expr, Function
from phyfleaux.plugins.tiramisu import Var


class Polytope(ast.NodeVisitor):
    def __init__(self, task_: Task) -> None:
        """Representation of the function in an affine space.

        :arg task_: :class:task:`Task` object

        related resources:
        ------------------
        https://polyhedral.info/

        https://en.wikipedia.org/wiki/Polytope_model
        https://en.wikipedia.org/wiki/Affine_space
        """

        self.task = task_
        self.build_isl()

    def __call__(self, *args, **kwargs):
        self.isl_tree(*args, **kwargs)
        # self.isl_tree = self.isl_tree.compile()
        # self.tiramisu = self.isl_tree.build()
        # self.tiramisu.generate()
        # self.task(*args, **kwargs)
        # self.loops = OrderedDict()

    def build_isl(self):
        fn_body = self.task.py_ast.body[0]
        # if isinstance(fn_body[0], str):
        #     self.__doc__ = fn_body[0]
        #     del fn_body[0]

        self.isl_tree = self.visit_FunctionDef(fn_body)

    def visit_Add(self, node: ast.Add) -> str:
        return '__Add__'

    def visit_Assign(self, node: ast.Assign) -> Computation:
        target = node.targets
        value = node.value

        s = Computation()

        s.rhs = self.visit(value)

        if 1 < (len(target)):
            raise NotImplementedError(
                "Multi-target assignments are not yet supported.")
        s.lhs = self.visit(target[0])

        return s

    def visit_BinOp(self, node) -> Function:
        fn_name = self.visit(node.op)
        lhs = self.visit(node.left)
        rhs = self.visit(node.right)

        fn = Call(fn_name)
        fn.args = [lhs, rhs]

        return fn

    def visit_Call(self, node: ast.Call) -> Call:

        fn = Call(node)

        if isinstance(node.args, list):
            for arg in node.args:
                fn.args = arg
        else:
            self.args = node.args

        for attr in node.keywords:
            val = self.visit(attr.value)
            setattr(fn, attr.arg, val)

        return fn

    def visit_Constant(self, node: ast.Constant) -> Union[int, str]:
        return node.value

    def visit_Expr(self, node: ast.Expr) -> Expr:
        return Expr(self.visit(node.value))

    def visit_For(self, node: ast.For) -> Var:
        loop = Var(node.target.id)

        if isinstance(node.iter, ast.Call) and 'range' == node.iter.func.id:
            bounds = []
            for arg in node.iter.args:
                try:
                    if isinstance(arg, ast.Name):
                        bounds.append(arg.id)
                except AttributeError:
                    if isinstance(arg, ast.Constant):
                        bounds.append(arg.n)
                except AttributeError:
                    raise AttributeError(
                        f"Expected '<class ast.Name>' received {type(arg)}")

            if 1 == len(bounds):
                bounds = [0] + bounds

            loop.set_bounds(bounds[0], bounds[1])

        if isinstance(node.iter, ast.List):
            raise TypeError("'list' is not an affine space.")

        for statement in node.body:
            loop.body.append(self.visit(statement))

        return loop

    def visit_FunctionDef(self, node: ast.FunctionDef) -> Function:
        fn = Function(node.name, task=self.task)

        for statement in node.body:
            fn.add_statement(self.visit(statement))
        fn.build()

        for return_ in node.returns:
            fn.add_return(self.visit(return_))

        return fn

    def visit_Mult(self, node: ast.Mult) -> str:
        return '__Mult__'

    def visit_Name(self, node: ast.Name) -> str:
        return node.id

    def visit_Return(self, node):
        return self.visit(node.value)

    def visit_Subscript(self, node: ast.Subscript) -> tuple:

        ir_node = deepcopy(node)

        indices = []

        while isinstance(ir_node, ast.Subscript):
            slice_ = ir_node.slice
            if isinstance(slice_, ast.Index):
                val = self.visit(slice_)
                indices.insert(0, val)
            ir_node = self.visit(ir_node.value)

        buffer_name = ir_node

        buffer = Buffer(buffer_name)
        buffer.indices = indices

        return buffer
