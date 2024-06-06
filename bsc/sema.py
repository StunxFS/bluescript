# Copyright (C) 2024 Jose Mendoza. All rights reserved. Use of this
# source code is governed by an MIT license that can be found in the
# LICENSE file.

from bsc.AST import *
from bsc.sym import *

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
            if self.first_pass:
                pass
            self.cur_file = file
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
        pass

    ## === Utilities ====================================

    def open_scope(self, detach_from_parent = False):
        self.scope = Scope(self.scope, detach_from_parent)

    def close_scope(self):
        self.scope = self.scope.parent
