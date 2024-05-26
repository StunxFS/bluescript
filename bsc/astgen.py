# Copyright (C) 2024 Jose Mendoza. All rights reserved. Use of this
# source code is governed by an MIT license that can be found in the
# LICENSE file.

import os

from lark import Lark, v_args, Transformer

from AST import *

bs_parser = Lark.open(
    "grammar.lark", rel_to = __file__, parser = 'earley', start = "module",
    ambiguity = "explicit"
)

@v_args(inline = True)
class AstGen(Transformer):
    def __init__(self, ctx):
        super().__init__()
        self.ctx = ctx
        self.file = ""
        self.source_file = None

    def parse_file(self, file):
        self.file = file
        self.source_file = SourceFile(self.file)
        return self.transform(bs_parser.parse(open(file).read()))

    def mkpos(self, token):
        return Pos.from_token(self.file, token)

    #def fn_arg(self, name, _, type, _, default_value):
    #    print(name, type, default_value)

    # Expressions
    def par_expr(self, *children):
        return ParExpr(
            children[1],
            self.mkpos(children[0]) + self.mkpos(children[2])
        )

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

    # Modifiers
    def access_modifier(self, modifier):
        if modifier.value == "pub":
            return AccessModifier.public
        elif modifier.value == "prot":
            return AccessModifier.protected
        return AccessModifier.private

    # Types
    def user_type(self, *names):
        left = names[0]
        for name in names[1:]:
            if not isinstance(name, Ident):
                continue
            left = SelectorExpr(left, name, left.pos + name.pos)
        return left
