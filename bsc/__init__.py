# Copyright (C) 2024 Jose Mendoza. All rights reserved. Use of this
# source code is governed by an MIT license that can be found in the
# LICENSE file.

import os

from bsc import sym, report
from bsc.AST import BasicType
from bsc.prefs import Prefs
from bsc.astgen import AstGen
from bsc.sema import Sema
from bsc.codegen import Codegen
from bsc.sym import Scope, TypeSym, AccessModifier, TypeKind, TypeField

class Context:
    def __init__(self):
        self.prefs = Prefs()

        self.universe = Scope(is_universe = True)
        self.universe.add_sym(
            TypeSym(AccessModifier.private, TypeKind.void, "void", [], Scope())
        )
        self.void_type = BasicType.with_typesym(self.universe.syms[0])

        self.universe.add_sym(
            TypeSym(AccessModifier.private, TypeKind.any, "any", [], Scope())
        )
        self.any_type = BasicType.with_typesym(self.universe.syms[1])

        self.universe.add_sym(
            TypeSym(AccessModifier.private, TypeKind.bool, "bool", [], Scope())
        )
        self.bool_type = BasicType.with_typesym(self.universe.syms[2])

        self.universe.add_sym(
            TypeSym(
                AccessModifier.private, TypeKind.number, "number", [], Scope()
            )
        )
        self.number_type = BasicType.with_typesym(self.universe.syms[3])

        self.universe.add_sym(
            TypeSym(
                AccessModifier.private, TypeKind.string, "string", [
                    TypeField(
                        AccessModifier.public, "len", self.number_type, None
                    )
                ], Scope()
            )
        )
        self.string_type = BasicType.with_typesym(self.universe.syms[4])

        self.source_files = []

        self.astgen = AstGen(self)
        self.sema = Sema(self)
        self.codegen = Codegen(self)

    def parse_args(self):
        self.prefs.parse_args()

    def compile(self):
        self.parse_input()
        self.import_modules()
        if report.errors > 0:
            exit(1)
        self.sema.check_files(self.source_files)
        if report.errors > 0:
            exit(1)
        self.codegen.gen_files(self.source_files)

    def import_modules(self):
        for sf in self.source_files:
            self.import_modules_from_decls(sf.mod_sym, sf.decls)

    def import_modules_from_decls(self, parent, decls):
        for decl in decls:
            if isinstance(decl, AST.ModDecl):
                if decl.is_inline:
                    self.import_modules_from_decls(parent, decl.decls)
                else:
                    self.import_module(parent, decl)

    def import_module(self, parent, decl):
        dir = os.path.dirname(os.path.relpath(decl.pos.file))
        file = os.path.join(dir, f"{decl.name}.bs")
        if os.path.isfile(file):
            self.parse_file(decl.name, file, parent_mod=parent)
        elif os.path.isdir(os.path.join(dir, decl.name)):
            mod_bs = os.path.join(dir, decl.name, "mod.bs")
            if os.path.isfile(mod_bs):
                self.parse_file(decl.name, file, parent_mod=parent)
            else:
                report.error(f"cannot load module `{decl.name}`, because it does not contain a file `mod.bs`")
        else:
            report.error(f"module `{decl.name}` not found", decl.pos)

    def parse_input(self):
        self.parse_file(
            self.prefs.pkg_name, self.prefs.input, is_pkg = True
        )

    def parse_file(
        self, mod_name, file, is_pkg = False, parent_mod = None
    ):
        self.source_files.append(
            self.astgen.parse_file(mod_name, file, is_pkg, parent_mod)
        )
