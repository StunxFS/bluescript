# Copyright (C) 2024 Jose Mendoza. All rights reserved. Use of this
# source code is governed by an MIT license that can be found in the
# LICENSE file.

from bsc.sym import *
from bsc.astgen.ast import *
from bsc import utils, report

class Sema:
    def __init__(self, ctx):
        self.ctx = ctx

        # In the first pass we register the symbols.
        self.first_pass = True

        self.cur_file = None
        self.cur_pkg = None # is used for the expression `pkg::`
        self.cur_mod = None # is used for the expression `self::`

        self.cur_sym = None
        self.cur_scope = self.ctx.universe
        self.old_scope = None

    def check_files(self, files):
        self.check_files_(files)
        self.first_pass = False
        self.check_files_(files)

    def check_files_(self, files):
        for file in files:
            self.check_file(file)

    def check_file(self, file):
        self.cur_file = file
        if file.mod_sym.is_pkg:
            self.cur_pkg = file.mod_sym
        self.cur_mod = file.mod_sym
        self.cur_sym = file.mod_sym
        self.check_decls(file.decls)

    def check_decls(self, decls):
        for decl in decls:
            self.check_decl(decl)

    def check_decl(self, decl):
        if isinstance(decl, ModDecl):
            self.check_mod_decl(decl)
        elif isinstance(decl, EnumDecl):
            self.check_enum_decl(decl)
        elif isinstance(decl, ConstDecl):
            self.check_const_decl(decl)
        elif isinstance(decl, VarDecl):
            self.check_var_decl(decl)
        elif isinstance(decl, FnDecl):
            self.check_fn_decl(decl)

    def check_mod_decl(self, decl):
        old_sym = self.cur_sym
        old_mod = self.cur_mod
        old_scope = self.cur_scope
        if self.first_pass:
            if decl.is_inline:
                self.add_sym(decl.sym, decl.pos)
                self.cur_mod = decl.sym
                self.cur_sym = decl.sym
                self.cur_scope = decl.sym.scope
                self.check_decls(decl.decls)
                self.cur_sym = old_sym
                self.cur_mod = old_mod
                self.close_scope()
            return
        if decl.is_inline:
            self.cur_mod = decl.sym
            self.cur_sym = decl.sym
            self.cur_scope = decl.sym.scope
            self.check_decls(decl.decls)
            self.cur_scope = old_scope
            self.cur_sym = old_sym
            self.cur_mod = old_mod

    def check_enum_decl(self, decl):
        old_sym = self.cur_sym
        old_scope = self.cur_scope
        if self.first_pass:
            fields = []
            for i, field in enumerate(decl.fields):
                fields.append((field.name, i))
            decl.sym = TypeSym(
                decl.access_modifier, TypeKind.enum, decl.name, [],
                self.open_scope(), info = EnumInfo(fields), pos = decl.pos
            )
            self.add_sym(decl.sym, decl.pos)
            self.cur_sym = decl.sym
            self.cur_scope = decl.sym.scope
            self.check_decls(decl.decls)
            self.cur_sym = old_sym
            self.close_scope()
            return
        if len(decl.fields) == 0:
            report.error(f"enum `{decl.name}` cannot be empty", decl.pos)
        self.cur_sym = decl.sym
        self.check_decls(decl.decls)
        self.cur_sym = old_sym

    def check_fn_decl(self, decl):
        old_sym = self.cur_sym
        old_scope = self.cur_scope
        if self.first_pass:
            decl.sym = Function(
                decl.access_modifier, decl.name,
                list(
                    map(
                        lambda arg:
                        FunctionArg(arg.name, arg.type, arg.default_value),
                        decl.args
                    )
                ), self.open_scope(True), decl.pos
            )
            self.add_sym(decl.sym, decl.pos)
            self.cur_sym = decl.sym
            self.cur_scope = decl.sym.scope
            for arg in decl.args:
                self.add_sym(
                    Object(
                        AccessModifier.private, arg.name, ObjectLevel.argument,
                        arg.type, self.cur_scope
                    ), arg.pos
                )
            if decl.has_body:
                self.check_stmts(decl.stmts)
            self.cur_sym = old_sym
            self.close_scope()
            if len(decl.sym.scope.syms) > 200:
                report.error(
                    f"function `{decl.name}` exceeded the maximum number of local variables allowed (200)",
                    decl.pos
                )
            return
        if decl.has_body:
            self.cur_sym = decl.sym
            self.cur_scope = decl.sym.scope
            self.check_stmts(decl.stmts)
            self.cur_scope = old_scope
            self.cur_sym = old_sym

    def check_const_decl(self, decl):
        if self.first_pass:
            decl.sym = Const(
                decl.access_modifier, decl.name, decl.typ, decl.expr,
                self.cur_scope, isinstance(self.cur_sym, Function), decl.pos
            )
            if isinstance(self.cur_sym, Function):
                decl.is_local = True
                if decl.access_modifier != AccessModifier.private:
                    report.error(
                        "local constants cannot have access modifier", decl.pos
                    )
            self.add_sym(decl.sym, decl.pos)
            return
        expr_typ = self.check_expr(decl.expr)
        if decl.typ == None:
            decl.typ = expr_typ
            decl.sym.typ = expr_typ

    def check_var_decl(self, stmt):
        if self.first_pass:
            for left in stmt.lefts:
                level = ObjectLevel.static
                if isinstance(self.cur_sym, Function):
                    level = ObjectLevel.local
                    if stmt.access_modifier != AccessModifier.private:
                        report.error(
                            "local variables cannot have access modifier",
                            left.pos
                        )
                left.sym = Object(
                    stmt.access_modifier, left.name, level, left.typ,
                    self.cur_scope, pos = stmt.pos
                )
                self.add_sym(left.sym, left.pos)
            return

    ## === Statements ===================================

    def check_stmts(self, stmts):
        for stmt in stmts:
            self.check_stmt(stmt)

    def check_stmt(self, stmt):
        if isinstance(stmt, ExprStmt):
            if self.check_expr(stmt.expr) != self.ctx.void_type:
                report.warn("expression evaluated but not used", stmt.pos)
        elif isinstance(stmt, ConstDecl):
            self.check_const_decl(stmt)
        elif isinstance(stmt, VarDecl):
            self.check_var_decl(stmt)

    ## === Expressions ==================================

    def check_expr(self, expr):
        if self.first_pass and not isinstance(expr, BlockExpr):
            return self.ctx.void_type
        if isinstance(expr, ParExpr):
            expr.typ = self.check_expr(expr.expr)
        elif isinstance(expr, AssignExpr):
            #self.check_expr(expr.lefts)
            self.check_expr(expr.right)
            expr.typ = self.ctx.void_type
        elif isinstance(expr, NilLiteral):
            expr.typ = self.ctx.nil_type
        elif isinstance(expr, BoolLiteral):
            expr.typ = self.ctx.bool_type
        elif isinstance(expr, NumberLiteral):
            if any(ch in expr.value for ch in [".", "e", "E"]
                   ) and (expr.value[:2].lower() not in ['0x', '0o', '0b']):
                expr.typ = self.ctx.float_type
            else:
                expr.typ = self.ctx.int_type
        elif isinstance(expr, StringLiteral):
            expr.typ = self.ctx.string_type
        elif isinstance(expr, Ident):
            expr.typ = self.ctx.void_type
            if sym := self.check_symbol(expr.name, expr.pos):
                if isinstance(sym, (Object, Const)):
                    expr.typ = sym.typ
                else:
                    report.error(
                        f"expected value, found {sym.kind_of()} `{sym.name}`",
                        expr.pos
                    )
        elif isinstance(expr, PathExpr):
            expr.typ = self.ctx.void_type
            self.check_path_expr(expr)
            if expr.sym != None:
                if isinstance(expr.sym, (Object, Const)):
                    expr.typ = expr.sym.typ
                else:
                    report.error(
                        f"expected value, found {expr.sym.kind_of()} `{expr.sym.name}`",
                        expr.pos
                    )
        elif isinstance(expr, BlockExpr):
            if self.first_pass:
                expr.scope = self.open_scope()
                self.check_stmts(expr.stmts)
                return self.ctx.void_type
            old_scope = self.cur_scope
            self.cur_scope = expr.scope
            self.check_stmts(expr.stmts)
            self.cur_scope = old_scope
            if expr.expr != None:
                expr.typ = self.check_expr(expr.expr)
            else:
                expr.typ = self.ctx.void_type
        elif isinstance(expr, UnaryExpr):
            right_t = self.check_expr(expr.right)
            match expr.op:
                case UnaryOp.bang:
                    if right_t != self.ctx.bool_type:
                        report.error(
                            f"operator `!` is not defined for type `{right_t}`",
                            expr.pos,
                            ["operator `!` is only defined for type `bool`"]
                        )
                case UnaryOp.minus:
                    if right_t not in (self.ctx.int_type, self.ctx.float_type):
                        report.error(
                            f"operator `-` is not defined for type `{right_t}`",
                            expr.pos, [
                                "operator `-` is only defined for `int` and `float` types"
                            ]
                        )
                case UnaryOp.bit_not:
                    if right_t != self.ctx.int_type:
                        report.error(
                            f"operator `~` is not defined for type `{right_t}`",
                            expr.pos,
                            ["operator `~` is only defined for type `int`"]
                        )
        elif isinstance(expr, BinaryExpr):
            left_t = self.check_expr(expr.left)
            right_t = self.check_expr(expr.right)
            match expr.op:
                case BinaryOp.logical_and | BinaryOp.logical_or:
                    if not (
                        left_t == self.ctx.bool_type
                        and right_t == self.ctx.bool_type
                    ):
                        report.error(
                            f"operator `{expr.op}` is not defined for type `{right_t}`",
                            expr.pos, [
                                f"operator `{expr.op}` is only defined for type `bool`"
                            ]
                        )
            if expr.op.is_relational():
                expr.typ = self.ctx.bool_type
            else:
                expr.typ = left_t
        elif isinstance(expr, IfExpr):
            branch_t = None
            for i, branch in enumerate(expr.branches):
                if (not branch.is_else) and self.check_expr(
                    branch.cond
                ) != self.ctx.bool_type:
                    report.error("non-boolean `if` condition", branch.cond.pos)
                branch_t = self.check_expr(branch.expr)
                if i == 0:
                    expr.typ = branch_t
        else:
            expr.typ = self.ctx.void_type # tmp
        return expr.typ

    def check_path_expr(self, expr: PathExpr):
        if isinstance(expr.left, Ident):
            expr.left_sym = self.check_symbol(expr.left.name, expr.pos)
        elif isinstance(expr.left, PathExpr):
            expr.left_sym = self.check_path_expr(expr.left)
        else:
            report.error(
                "invalid expression on left side of path", expr.left.pos
            )

        if expr.left_sym == None:
            return

        if path_sym := expr.left_sym.scope.find(expr.name):
            expr.sym = path_sym
            if not self.cur_sym.has_access_to(path_sym):
                report.error(
                    f"cannot access private {path_sym.kind_of()} `{path_sym.name}`",
                    expr.pos
                )
        else:
            report.error(
                f"{expr.left_sym.kind_of()} `{expr.left_sym}` does not contain a symbol named `{expr.name}`",
                expr.pos
            )

    ## === Symbols ======================================

    def check_symbol(self, name, pos):
        ret_sym = None
        if local_sym := self.cur_scope.lookup(name):
            ret_sym = local_sym
        elif symbol_sym := self.cur_sym.scope.find(name):
            ret_sym = symbol_sym
        elif module_sym := self.cur_mod.scope.find(name):
            ret_sym = module_sym
        else:
            report.error(f"cannot find symbol `{name}` in this scope", pos)
        if ret_sym != None and ret_sym.pos != None and ret_sym.pos.line > pos.line:
            report.error(
                f"{ret_sym.kind_of()} `{ret_sym.name}` is used before its declaration",
                pos
            )
        return ret_sym

    ## === Utilities ====================================

    def add_sym(self, sym, pos):
        try:
            self.cur_sym.scope.add_sym(sym)
        except utils.CompilerError as e:
            report.error_from_ce(e, pos)

    def open_scope(self, detach_from_parent = False):
        self.cur_scope = Scope(self.cur_scope, detach_from_parent)
        return self.cur_scope

    def close_scope(self):
        self.cur_scope = self.cur_scope.parent
