# Copyright (C) 2024 Jose Mendoza. All rights reserved. Use of this
# source code is governed by an MIT license that can be found in the
# LICENSE file.

import os

from lark import Lark, v_args, Transformer

from AST import *

bs_parser = Lark.open("bluescript.lark", rel_to=__file__, parser='earley')

@v_args(inline=True)
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

    #def fn_arg(self, name, _, type, _, default_value):
    #    print(name, type, default_value)

    # Modifiers
    def access_modifier(self, modifier):
        if modifier.value == "pub":
            return AccessModifier.public
        elif modifier.value == "prot":
            return AccessModifier.protected
        return AccessModifier.private

    # Types
    def user_type(self, *names):
        left = Ident(names[0].value, Pos.from_token(self.file,names[0]))
        for name in names[1:]:
            left = SelectorExpr(
                left, Ident(name.value, Pos.from_token(self.file, name)),
                left.pos + Pos.from_token(self.file,name)
            )
        print(left.__dict__)
