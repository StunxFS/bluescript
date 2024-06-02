# Copyright (C) 2024 Jose Mendoza. All rights reserved. Use of this
# source code is governed by an MIT license that can be found in the
# LICENSE file.

from bsc import sym
from bsc.AST import BasicType
from bsc.prefs import Prefs
from bsc.astgen import AstGen
from bsc.sym import Scope, TypeSym, AccessModifier, Typekind, TypeField

class Context:
    def __init__(self):
        self.prefs = Prefs()

        self.astgen = AstGen(self)
        self.source_files = []

        self.universe = Scope(is_universe = True)
        self.universe.add_sym(
            TypeSym(AccessModifier.private, Typekind.void, "void", [], Scope())
        )
        self.void_type = BasicType.with_typesym(self.universe.syms[0])

        self.universe.add_sym(
            TypeSym(AccessModifier.private, Typekind.any, "any", [], Scope())
        )
        self.any_type = BasicType.with_typesym(self.universe.syms[1])

        self.universe.add_sym(
            TypeSym(AccessModifier.private, Typekind.bool, "bool", [], Scope())
        )
        self.bool_type = BasicType.with_typesym(self.universe.syms[2])

        self.universe.add_sym(
            TypeSym(
                AccessModifier.private, Typekind.number, "number", [], Scope()
            )
        )
        self.number_type = BasicType.with_typesym(self.universe.syms[3])

        self.universe.add_sym(
            TypeSym(
                AccessModifier.private, Typekind.string, "string", [
                    TypeField(
                        AccessModifier.public, "len", self.number_type, None
                    )
                ], Scope()
            )
        )
        self.string_type = BasicType.with_typesym(self.universe.syms[4])

    def parse_args(self):
        self.prefs.parse_args()

    def parse_files(self):
        self.source_files.append(self.astgen.parse_file(self.prefs.input))
