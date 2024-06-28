# Copyright (C) 2024 Jose Mendoza. All rights reserved. Use of this
# source code is governed by an MIT license that can be found in the
# LICENSE file.

from lark import Lark, v_args, Transformer, Token, visitors, exceptions

from bsc.AST import *
from bsc.sym import AccessModifier, Module, Scope
from bsc import utils, report

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
        self.source_file_deps = []
        self.mod_sym = None

    def parse_file(self, mod_name, file, is_pkg = False, parent_mod = None):
        self.file = file
        self.mod_sym = Module(
            AccessModifier.public, mod_name, Scope(self.ctx.universe, True),
            is_pkg
        )
        try:
            self.source_file = SourceFile(
                self.file, self.transform(bs_parser.parse(open(file).read())),
                self.mod_sym, deps = self.source_file_deps
            )
        except exceptions.UnexpectedCharacters as e:
            report.error(
                f"unexpected character `{e.char}`",
                Pos(file, e.line, e.column, 1, e.pos_in_stream)
            )
            return SourceFile("", [], None)
        except exceptions.UnexpectedToken as e:
            report.error(
                f"expected {e.expected}, got {e.token}, ",
                Pos(file, e.line, e.column, 1, e.pos_in_stream)
            )
            return SourceFile("", [], None)
        except exceptions.UnexpectedEOF as e:
            report.error(
                f"unexpected end of file, expected {e.expected}",
                Pos(file, e.line, e.column, 1, e.pos_in_stream)
            )
            return SourceFile("", [], None)
        try:
            if is_pkg:
                self.ctx.universe.add_sym(self.source_file.mod_sym)
            else:
                assert parent_mod, f"parent_mod is None for `{mod_name}`"
                parent_mod.scope.add_sym(self.source_file.mod_sym)
        except utils.CompilerError as e:
            utils.error(e.args[0])
        self.source_file_deps = []
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
        access_modifier = self.get_access_modifier(nodes[0])
        pos = self.mkpos(nodes[1])
        name = nodes[2].name
        is_inline = len(nodes) > 3
        decls = []
        if is_inline:
            decls = list(nodes[4:-1])
        else:
            pos += nodes[2].pos
        mod_sym = Module(
            access_modifier, name, Scope(self.mod_sym.scope, True), False,
            is_inline
        )
        if is_inline:
            mod_sym.pos = pos
        if not is_inline:
            self.source_file_deps.append(mod_sym)
        return ModDecl(access_modifier, name, is_inline, decls, pos, mod_sym)

    def enum_decl(self, *nodes):
        pos = self.mkpos(nodes[1])
        access_modifier = self.get_access_modifier(nodes[0])
        name = nodes[2].name
        enum_fields = nodes[4]
        decls = []
        for node in nodes[5:]:
            if isinstance(node, Token): break
            decls.append(node)
        return EnumDecl(access_modifier, name, enum_fields, decls, pos)

    def enum_fields(self, *nodes):
        return list(filter(lambda field: not isinstance(field, Token), nodes))

    def enum_field(self, *nodes):
        return EnumField(nodes[0].name, nodes[-1])

    def fn_decl(self, *nodes):
        pos = self.mkpos(nodes[1])
        access_modifier = self.get_access_modifier(nodes[0])
        name = nodes[2].name
        args = nodes[4]
        is_method = False
        if args:
            if isinstance(args, Token):
                args = []
            else:
                is_method = args[0]
                args = list(filter(lambda arg: isinstance(arg, FnArg), args[1]))
        else:
            args = []
        ret_type = nodes[6]
        if isinstance(ret_type, BlockExpr
                      ) or isinstance(ret_type, Token) or not ret_type:
            ret_type = self.ctx.void_type
        stmts = []
        if len(nodes) == 8:
            stmts = nodes[-1]
        else:
            stmts = None
        return FnDecl(
            access_modifier, name, args, is_method, ret_type, stmts,
            name == "main" and self.file == self.ctx.prefs.input, pos
        )

    def fn_args(self, *nodes):
        is_method = str(nodes[0]) == "self"
        return (is_method, nodes[1:] if is_method else nodes)

    def fn_arg(self, *nodes):
        return FnArg(nodes[0].name, nodes[2], nodes[-1], nodes[0].pos)

    def const_decl(self, *nodes):
        access_modifier = self.get_access_modifier(nodes[0])
        return ConstDecl(
            access_modifier, nodes[2].name, nodes[4], nodes[-1],
            self.mkpos(nodes[1])
        )

    def var_decl(self, *nodes):
        access_modifier = self.get_access_modifier(nodes[0])
        lefts = list(filter(lambda n: isinstance(n, VarIdent), nodes[2:-2]))
        return VarDecl(access_modifier, lefts, nodes[-1], self.mkpos(nodes[1]))

    def var_ident(self, *nodes):
        typ = None
        if nodes[2]:
            typ = nodes[2]
        pos = nodes[0].pos
        if nodes[2]:
            pos += self.mkpos(nodes[2])
        return VarIdent(nodes[0].name, typ, pos)

    # Statements

    def expr_stmt(self, *nodes):
        return ExprStmt(nodes[0])

    def assignment(self, *nodes):
        lefts = []
        assign_op = ""
        for node in nodes:
            if str(node) == ",":
                continue
            if isinstance(node, AssignOp):
                break
            lefts.append(node)
        right = nodes[-1]
        return AssignExpr(lefts, assign_op, right, lefts[0].pos + nodes[-1].pos)

    def assign_op(self, *nodes):
        assign_op = str(nodes[0])
        match assign_op:
            case "=":
                assign_op = AssignOp.Assign
            case "+=":
                assign_op = AssignOp.PlusAssign
            case "-=":
                assign_op = AssignOp.MinusAssign
            case "/=":
                assign_op = AssignOp.DivAssign
            case "*=":
                assign_op = AssignOp.MulAssign
            case "%=":
                assign_op = AssignOp.ModAssign
            case "&=":
                assign_op = AssignOp.AndAssign
            case "|=":
                assign_op = AssignOp.OrAssign
            case "^=":
                assign_op = AssignOp.XorAssign
            case _:
                assert False # unreachable
        return assign_op

    def block(self, *nodes):
        return list(nodes[1:-1])

    def block_stmt(self, *nodes):
        return ExprStmt(nodes[0])

    def while_stmt(self, *nodes):
        return WhileStmt(nodes[1], nodes[2], self.mkpos(nodes[0]))

    def match_stmt(self, *nodes):
        return ExprStmt(nodes[0])

    def if_stmt(self, *nodes):
        return ExprStmt(nodes[0])

    # Expressions
    def par_expr(self, *nodes):
        return ParExpr(nodes[1], self.mkpos(nodes[0]) + self.mkpos(nodes[2]))

    def builtin_var(self, *nodes):
        return BuiltinVar(nodes[1].name, self.mkpos(nodes[0]) + nodes[1].pos)

    def KW_NIL(self, lit):
        return NilLiteral(self.mkpos(lit))

    def BOOL_LIT(self, lit):
        return BoolLiteral(str(lit) == "true", self.mkpos(lit))

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
        is_fixed = nodes[0] != None
        elems = []
        for node in nodes[2:]:
            if isinstance(node, Token):
                continue
            elems.append(node)
        return ArrayLiteral(
            elems, is_fixed,
            self.mkpos(nodes[0] or nodes[1]) + self.mkpos(nodes[-1])
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

    def enum_literal(self, *nodes):
        return EnumLiteral(nodes[1].name, self.mkpos(nodes[0]) + nodes[1].pos)

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
        return UnaryExpr(nodes[0], nodes[1], right.pos)

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
        return IfBranch(nodes[1], False, nodes[2], self.mkpos(nodes[0]))

    def else_if_expr(self, *nodes):
        return IfBranch(nodes[2], False, nodes[3], self.mkpos(nodes[0]))

    def else_stmt(self, *nodes):
        return IfBranch(None, True, nodes[1], self.mkpos(nodes[0]))

    def match_expr(self, *nodes):
        expr = None
        if nodes[1]:
            expr = nodes[1]
        return MatchExpr(expr, nodes[3], self.mkpos(nodes[0]))

    def match_branches(self, *nodes):
        return [node for node in nodes if isinstance(node, MatchBranch)]

    def match_branch(self, *nodes):
        is_else = str(nodes[0]) == "else"
        cases = []
        if is_else:
            pos = self.mkpos(nodes[0])
            stmt = nodes[2]
        else:
            pos = nodes[0].pos
            for case in nodes:
                if str(case) == ",":
                    continue
                if str(case) == "=>":
                    break
                cases.append(case)
            stmt = nodes[-1]
        return MatchBranch(cases, is_else, stmt, pos + nodes[-1].pos)

    def block_expr(self, *nodes):
        is_unsafe = nodes[0] != None
        stmts = list(nodes[2:-2])
        expr = nodes[-2]
        return BlockExpr(
            is_unsafe, stmts, expr, self.mkpos(nodes[0] or nodes[1])
        )

    def return_expr(self, *nodes):
        return ReturnExpr(nodes[1], self.mkpos(nodes[0]))

    # Modifiers
    def access_modifier(self, *nodes):
        modifier = nodes[0]
        match str(modifier):
            case "pub":
                if nodes[2]:
                    return AccessModifier.internal
                return AccessModifier.public
            case "prot":
                return AccessModifier.protected
        return AccessModifier.private

    # Types
    def user_type(self, *names):
        left = names[0]
        if isinstance(left, Ident):
            match left.name:
                case "void":
                    return self.ctx.void_type
                case "never":
                    return self.ctx.never_type
                case "any":
                    return self.ctx.any_type
                case "bool":
                    return self.ctx.bool_type
                case "int":
                    return self.ctx.int_type
                case "float":
                    return self.ctx.float_type
                case "string":
                    return self.ctx.string_type
                case _:
                    return BasicType(left, left.pos)
        return BasicType(left, left.pos)

    def option_type(self, *nodes):
        return OptionType(nodes[1], self.mkpos(nodes[0]))

    def array_type(self, *nodes):
        has_size = not isinstance(nodes[1], Token)
        size = nodes[1] if has_size else None
        return ArrayType(
            size, nodes[3 if has_size else 2], self.mkpos(nodes[0])
        )

    def map_type(self, *nodes):
        return MapType(nodes[1], nodes[3], self.mkpos(nodes[0]))

    def sum_type(self, *nodes):
        types = list(filter(lambda node: not isinstance(node, Token), nodes))
        return SumType(types, nodes[0].pos)

    # Discard ;
    def SEMICOLON(self, *nodes):
        return visitors.Discard

    # Utilities
    def get_access_modifier(self, node):
        _access_modifier = AccessModifier.private
        if isinstance(node, AccessModifier):
            _access_modifier = node
        return _access_modifier
