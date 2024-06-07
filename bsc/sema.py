# Copyright (C) 2024 Jose Mendoza. All rights reserved. Use of this
# source code is governed by an MIT license that can be found in the
# LICENSE file.

from bsc.AST import *
from bsc.sym import *
from bsc import utils

class Sema:
    def __init__(self, ctx):
        self.ctx = ctx

        # In the first pass we register the symbols.
        self.first_pass = True

        self.cur_file = None
        self.cur_sym = None
        self.cur_scope = self.ctx.universe

    def check_files(self, files):
        self.check_files_(files)
        self.first_pass = False
        self.check_files_(files)

    def check_files_(self, files):
        for file in files:
            self.cur_file = file
            self.cur_sym = file.mod_sym
            self.check_file(file)

    def check_file(self, file):
        self.check_decls(file.decls)

    def check_decls(self, decls):
        for decl in decls:
            self.check_decl(decl)

    def check_decl(self, decl):
        if isinstance(decl, FnDecl):
            self.check_fn_decl(decl)

    def check_fn_decl(self, decl):
        if self.first_pass:
            decl.sym = Function(
                decl.access_modifier, decl.name, [], self.open_scope()
            )
            self.add_sym(decl.sym)
            return

    ## === Utilities ====================================

    def add_sym(self, sym):
        try:
            self.cur_sym.scope.add_sym(sym)
        except utils.CompilerError as e:
            utils.error(e.args[0])

    def open_scope(self, detach_from_parent = False):
        self.cur_scope = Scope(self.cur_scope, detach_from_parent)
        return self.cur_scope

    def close_scope(self):
        self.cur_scope = self.cur_scope.parent
