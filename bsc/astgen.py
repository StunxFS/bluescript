# Copyright (C) 2024 Jose Mendoza. All rights reserved. Use of this
# source code is governed by an MIT license that can be found in the
# LICENSE file.

import os
from lark import Lark, v_args, Transformer, Token, Tree

from bsc.AST import *
from bsc.sym import AccessModifier, Module, Scope
from bsc import utils

bs_parser = Lark.open(
    "grammar.lark", rel_to = __file__, parser = 'earley', start = "module"
)

@v_args(inline = True)
class AstGen(Transformer):
    def __init__(self, ctx):
        super().__init__()
        self.ctx = ctx
        self.file = ""
        self.source_file = None

    def parse_file(self, mod_name, file):
        self.file = file
        mod_sym = Module(
            AccessModifier.public, mod_name, Scope(self.ctx.universe)
        )
        self.source_file = SourceFile(
            self.file, self.transform(bs_parser.parse(open(file).read())),
            mod_sym
        )
        try:
            self.ctx.universe.add_sym(self.source_file.mod_sym)
        except utils.CompilerError as e:
            utils.error(e.args[0])
        return self.source_file

    def mkpos(self, token):
        return Pos.from_token(self.file, token)

    # Declarations
    def module(self, *nodes):
        return list(nodes)

    def extern_pkg(self, *nodes):
        pos = self.mkpos(nodes[0]) + nodes[2].pos
        pkg_name = nodes[2].name
        alias_name = pkg_name
        if nodes[-1]:
            alias_name = nodes[-1].name
            pos += nodes[-1].pos
        return ExternPkg(pkg_name, alias_name, pos)

    def mod_decl(self, *nodes):
        is_inline = nodes[2] is None
        decls = []
        if not is_inline:
            decls = list(nodes[3:-2])
        pos = self.mkpos(nodes[0])
        if not is_inline:
            pos += self.mkpos(nodes[-1])
        return ModDecl(nodes[1].name, is_inline, decls, pos)

    def fn_decl(self, *nodes):
        access_modifier = self.access_modifier(nodes[0])
        name = nodes[2].name
        args = nodes[4]
        if isinstance(args, Token):
            is_method = False
            args = []
        else:
            is_method = args[0]
            args = list(args[1])
        ret_type = nodes[5]
        if isinstance(ret_type, BlockStmt
                      ) or isinstance(ret_type, Token) or not ret_type:
            ret_type = self.ctx.void_type
        stmts = []
        if not isinstance(nodes[-1], Token):
            stmts = nodes[-1]
            if stmts == ret_type: # no body
                stmts = None
        return FnDecl(
            access_modifier, name, args, is_method, ret_type, stmts,
            name == "main" and self.file == self.ctx.prefs.input
        )

    def fn_args(self, *nodes):
        is_method = str(nodes[0]) == "self"
        return (is_method, nodes[2:] if is_method else nodes)

    def fn_arg(self, *nodes):
        return FnArg(nodes[1], nodes[3], nodes[-1])

    def fn_body(self, *nodes):
        stmts = []
        if len(nodes) != 2:
            stmts = nodes[1:-1]
        return BlockStmt(stmts, self.mkpos(nodes[0]))

    # Statements
    def var_decl(self, *nodes):
        lefts = [nodes[1]]
        if len(nodes) != 4:
            lefts += list(
                filter(lambda n: not isinstance(n, Token), nodes[2:-2])
            )
        right = nodes[-1]
        return VarDecl(lefts, right)

    def var_ident(self, *nodes):
        typ = None
        if nodes[2]:
            typ = nodes[2]
        pos = nodes[0].pos
        if nodes[2]:
            pos += self.mkpos(nodes[2])
        return VarIdent(nodes[0].name, typ, pos)

    def assignment(self, *nodes):
        lefts = []
        op_assign = ""
        for node in nodes:
            if str(node) == ",":
                continue
            if isinstance(node, OpAssign):
                break
            lefts.append(node)
        right = nodes[-1]
        return AssignStmt(lefts, op_assign, right, lefts[0].pos + nodes[-1].pos)

    def op_assign(self, *nodes):
        op_assign = str(nodes[0])
        match op_assign:
            case "=":
                op_assign = OpAssign.Assign
            case "+=":
                op_assign = OpAssign.PlusAssign
            case "-=":
                op_assign = OpAssign.MinusAssign
            case "/=":
                op_assign = OpAssign.DivAssign
            case "*=":
                op_assign = OpAssign.MulAssign
            case "%=":
                op_assign = OpAssign.ModAssign
            case "&=":
                op_assign = OpAssign.AndAssign
            case "|=":
                op_assign = OpAssign.OrAssign
            case "^=":
                op_assign = OpAssign.XorAssign
            case _:
                assert False # unreachable
        return op_assign

    def block(self, *nodes):
        stmts = list(nodes[1:-1])
        return BlockStmt(stmts, self.mkpos(nodes[0]) + self.mkpos(nodes[-1]))

    def while_stmt(self, *nodes):
        return WhileStmt(
            nodes[1], nodes[3],
            self.mkpos(nodes[0]) + self.mkpos(nodes[-1])
        )

    # Expressions
    def par_expr(self, *nodes):
        return ParExpr(nodes[1], self.mkpos(nodes[0]) + self.mkpos(nodes[2]))

    def builtin_var(self, *nodes):
        return BuiltinVar(nodes[1].name, self.mkpos(nodes[0]) + nodes[1].pos)

    def KW_NIL(self, lit):
        return NilLiteral(self.mkpos(lit))

    def bool_lit(self, lit):
        return BoolLiteral(lit.value == "true", self.mkpos(lit))

    def number_lit(self, lit):
        return NumberLiteral(lit.value, self.mkpos(lit))

    def STRING(self, lit):
        return StringLiteral(lit.value, self.mkpos(lit))

    def KW_SELF(self, lit):
        return SelfLiteral(self.mkpos(lit))

    def NAME(self, lit):
        return Ident(lit.value, self.mkpos(lit))

    def path_expr(self, *nodes):
        if len(nodes) == 1:
            return nodes[0]
        return PathExpr(nodes[0], nodes[2].name, nodes[0].pos + nodes[2].pos)

    def selector_expr(self, *nodes):
        return SelectorExpr(
            nodes[0], nodes[2].name, nodes[0].pos + nodes[2].pos
        )

    def array_literal(self, *nodes):
        elems = []
        for node in nodes[1:]:
            if str(node) == ",":
                continue
            if str(node) == "]":
                break
            elems.append(node)
        is_fixed = str(nodes[-1]) == "!"
        return ArrayLiteral(
            elems, is_fixed,
            self.mkpos(nodes[0]) + self.mkpos(nodes[-1])
        )

    def tuple_literal(self, *nodes):
        elems = []
        for node in nodes[1:]:
            if str(node) == ",":
                continue
            if str(node) == ")":
                break
            elems.append(node)
        return TupleLiteral(elems, self.mkpos(nodes[0]) + self.mkpos(nodes[-1]))

    def LOGICAL_AND(self, *nodes):
        return BinaryOp.logical_and

    def LOGICAL_OR(self, *nodes):
        return BinaryOp.logical_or

    def and_expr(self, *nodes):
        left = nodes[0]
        i = 0
        nodes = nodes[1:]
        while i < len(nodes):
            tok = nodes[i]
            if isinstance(tok, BinaryOp):
                right = nodes[i + 1]
                left = BinaryExpr(left, tok, right, left.pos + right.pos)
                i += 1
            i += 1
        return left

    def or_expr(self, *nodes):
        left = nodes[0]
        i = 0
        nodes = nodes[1:]
        while i < len(nodes):
            tok = nodes[i]
            if isinstance(tok, BinaryOp):
                right = nodes[i + 1]
                left = BinaryExpr(left, tok, right, left.pos + right.pos)
                i += 1
            i += 1
        return left

    def compare_expr(self, *nodes):
        left = nodes[0]
        if len(nodes) == 3:
            return BinaryExpr(left, nodes[1], nodes[2], left.pos + nodes[2].pos)
        return left

    def bitwise_expr(self, *nodes):
        left = nodes[0]
        i = 0
        nodes = nodes[1:]
        while i < len(nodes):
            tok = nodes[i]
            if isinstance(tok, BinaryOp):
                right = nodes[i + 1]
                left = BinaryExpr(left, tok, right, left.pos + right.pos)
                i += 1
            i += 1
        return left

    def bitshift_expr(self, *nodes):
        left = nodes[0]
        i = 0
        nodes = nodes[1:]
        while i < len(nodes):
            tok = nodes[i]
            if isinstance(tok, BinaryOp):
                right = nodes[i + 1]
                left = BinaryExpr(left, tok, right, left.pos + right.pos)
                i += 1
            i += 1
        return left

    def addition_expr(self, *nodes):
        left = nodes[0]
        i = 0
        nodes = nodes[1:]
        while i < len(nodes):
            tok = nodes[i]
            if isinstance(tok, BinaryOp):
                right = nodes[i + 1]
                left = BinaryExpr(left, tok, right, left.pos + right.pos)
                i += 1
            i += 1
        return left

    def multiply_expr(self, *nodes):
        left = nodes[0]
        i = 0
        nodes = nodes[1:]
        while i < len(nodes):
            tok = nodes[i]
            if isinstance(tok, BinaryOp):
                right = nodes[i + 1]
                left = BinaryExpr(left, tok, right, left.pos + right.pos)
                i += 1
            i += 1
        return left

    def unary_expr(self, *nodes):
        if len(nodes) == 1:
            return nodes[0]
        right = nodes[-1]
        for op in nodes[:-1]:
            right = UnaryExpr(op, right, right.pos)
        return right

    def compare_op(self, *nodes):
        match nodes[0].value:
            case "<":
                return BinaryOp.lt
            case ">":
                return BinaryOp.gt
            case "<=":
                return BinaryOp.le
            case ">=":
                return BinaryOp.ge
            case "==":
                return BinaryOp.eq
            case "!=":
                return BinaryOp.neq
            case _:
                assert False # unreachable

    def bitwise_op(self, *nodes):
        match nodes[0].value:
            case "&":
                return BinaryOp.bit_and
            case "|":
                return BinaryOp.bit_or
            case "^":
                return BinaryOp.bit_xor
            case _:
                assert False # unreachable

    def bitshift_op(self, *nodes):
        match nodes[0].value:
            case "<<":
                return BinaryOp.lshift
            case ">>":
                return BinaryOp.rshift
            case _:
                assert False # unreachable

    def addition_op(self, *nodes):
        match nodes[0].value:
            case "+":
                return BinaryOp.plus
            case "-":
                return BinaryOp.minus
            case _:
                assert False # unreachable

    def multiply_op(self, *nodes):
        match nodes[0].value:
            case "*":
                return BinaryOp.mul
            case "/":
                return BinaryOp.div
            case "%":
                return BinaryOp.mod
            case _:
                assert False # unreachable

    def unary_op(self, *nodes):
        match nodes[0].value:
            case "!":
                return UnaryOp.bang
            case "~":
                return UnaryOp.bit_not
            case "-":
                return UnaryOp.minus
            case _:
                assert False # unreachable

    def call_expr(self, *nodes):
        left = nodes[0]
        if nodes[2]:
            args = list(nodes[2:-1])
        else:
            args = []
        return CallExpr(left, args, left.pos + self.mkpos(nodes[-1]))

    def if_expr(self, *nodes):
        return IfExpr(list(nodes), nodes[0].pos + nodes[-1].pos)

    def if_header(self, *nodes):
        cond = nodes[2]
        stmt = nodes[4]
        return IfBranch(cond, False, stmt, self.mkpos(nodes[0]) + nodes[-1].pos)

    def else_if_expr(self, *nodes):
        cond = nodes[3]
        stmt = nodes[5]
        return IfBranch(cond, False, stmt, self.mkpos(nodes[0]) + nodes[-1].pos)

    def else_stmt(self, *nodes):
        return IfBranch(
            None, True, nodes[1],
            self.mkpos(nodes[0]) + nodes[-1].pos
        )

    def match_expr(self, *nodes):
        expr = None
        if nodes[1]:
            expr = nodes[2]
        return MatchExpr(
            expr, nodes[5],
            self.mkpos(nodes[0]) + self.mkpos(nodes[-1])
        )

    def match_branches(self, *nodes):
        branches = []
        for node in nodes:
            if str(node) == ",":
                continue
            branches.append(node)
        return branches

    def match_branch(self, *nodes):
        is_else = str(nodes[0]) == "else"
        cases = []
        if is_else:
            pos = nodes[0].pos
            stmt = nodes[2]
        else:
            pos = nodes[0].pos
            for case in nodes:
                if str(case) == ",":
                    continue
                if str(case) == "->":
                    break
                cases.append(case)
            stmt = nodes[-1]
        return MatchBranch(cases, is_else, stmt, pos + nodes[-1].pos)

    # Modifiers
    def access_modifier(self, modifier):
        match str(modifier):
            case "pub":
                return AccessModifier.public
            case "prot":
                return AccessModifier.protected
        return AccessModifier.private

    # Types
    def primitive_type(self, *nodes):
        match nodes[0].value:
            case "any":
                return self.ctx.any_type
            case "bool":
                return self.ctx.bool_type
            case "number":
                return self.ctx.number_type
            case "string":
                return self.ctx.string_type
            case _:
                assert False # unreachable

    def user_type(self, *names):
        left = names[0]
        for name in names[1:]:
            if not isinstance(name, Ident):
                continue
            left = SelectorExpr(left, name, left.pos + name.pos)
        return BasicType(left, left.pos)

    def option_type(self, *nodes):
        return OptionType(nodes[1], self.mkpos(nodes[0]) + nodes[1].pos)

    def array_type(self, *nodes):
        has_size = not isinstance(nodes[1], Token)
        size = nodes[1] if has_size else None
        return ArrayType(
            size, nodes[3 if has_size else 2],
            self.mkpos(nodes[0]) + nodes[-1].pos
        )

    def map_type(self, *nodes):
        return MapType(
            nodes[1], nodes[3],
            self.mkpos(nodes[0]) + self.mkpos(nodes[-1])
        )

    def sum_type(self, *nodes):
        types = list(filter(lambda node: not isinstance(node, Token), nodes))
        return SumType(types, nodes[0].pos + nodes[-1].pos)

    # Utilities
    def get_access_modifier(self, node):
        print(node)
        _access_modifier = AccessModifier.private
        if isinstance(node, AccessModifier):
            _access_modifier = node
        return _access_modifier
