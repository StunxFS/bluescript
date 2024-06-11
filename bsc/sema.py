# Copyright (C) 2024 Jose Mendoza. All rights reserved. Use of this
# source code is governed by an MIT license that can be found in the
# LICENSE file.

from bsc.AST import *
from bsc.sym import *
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
        elif isinstance(decl, FnDecl):
            self.check_fn_decl(decl)

    def check_mod_decl(self, decl):
        old_sym = self.cur_sym
        old_mod = self.cur_mod
        if self.first_pass:
            decl.sym.parent = self.cur_sym
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
        self.check_decls(decl.decls)

    def check_enum_decl(self, decl):
        if self.first_pass:
            fields = []
            for i, field in enumerate(decl.fields):
                fields.append((field.name, i))
            decl.sym = TypeSym(
                decl.access_modifier, TypeKind.enum, decl.name, [],
                self.open_scope(), info = EnumInfo(fields)
            )
            self.add_sym(decl.sym, decl.pos)
            self.close_scope()
            return
        if len(decl.fields) == 0:
            report.error(f"enum `{decl.name}` cannot be empty", decl.pos)

    def check_fn_decl(self, decl):
        old_sym = self.cur_sym
        if self.first_pass:
            decl.sym = Function(
                decl.access_modifier, decl.name, [], self.open_scope()
            )
            self.add_sym(decl.sym, decl.pos)
            if decl.has_body:
                self.cur_sym = decl.sym
                self.cur_scope = decl.sym.scope
                self.check_stmts(decl.stmts)
                self.cur_sym = old_sym
                self.close_scope()
            return
        if decl.has_body:
            self.check_stmts(decl.stmts)

    def check_var_decl(self, stmt):
        if self.first_pass:
            for left in stmt.lefts:
                self.add_sym(
                    Object(
                        stmt.access_modifier, left.name, ObjectLevel.local,
                        left.typ, self.cur_scope
                    ), left.pos
                )

    ## === Statements ===================================

    def check_stmts(self, stmts):
        for stmt in stmts:
            self.check_stmt(stmt)

    def check_stmt(self, stmt):
        if isinstance(stmt, VarDecl):
            self.check_var_decl(stmt)

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
