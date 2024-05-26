# Copyright (C) 2024 Jose Mendoza. All rights reserved. Use of this
# source code is governed by an MIT license that can be found in the
# LICENSE file.

import os

from lark import Lark, v_args, Transformer, Token

from AST import *

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

    def parse_file(self, file):
        self.file = file
        self.source_file = SourceFile(self.file)
        return self.transform(bs_parser.parse(open(file).read()))

    def mkpos(self, token):
        return Pos.from_token(self.file, token)

    # Declarations
    def fn_decl(self, *nodes):
        name = nodes[1]
        args = nodes[3]
        if isinstance(args, Token):
            is_method = False
            args = []
        else:
            is_method = args[0]
            args = list(args[1])
        ret_type = nodes[5]
        if isinstance(ret_type, Token) or not ret_type:
            ret_type = VoidType()
        print(ret_type)
        return FnDecl(name, args, ret_type)

    def fn_args(self, *nodes):
        is_method = str(nodes[0]) == "self"
        return (is_method, nodes[2:] if is_method else nodes)

    def fn_arg(self, *nodes):
        return FnArg(nodes[1], nodes[3], nodes[-1])

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
        match modifier.value:
            case "pub": return AccessModifier.public
            case "prot": return AccessModifier.protected
        return AccessModifier.private

    # Types
    def primitive_type(self, *nodes):
        return BasicType(nodes[0].value, self.mkpos(nodes[0]))

    def user_type(self, *names):
        left = names[0]
        for name in names[1:]:
            if not isinstance(name, Ident):
                continue
            left = SelectorExpr(left, name, left.pos + name.pos)
        return BasicType(left, left.pos)

    def option_type(self, *nodes):
        return OptionType(nodes[1], self.mkpos(nodes[0])+nodes[1].pos)

    def array_type(self, *nodes):
        has_size = not isinstance(nodes[1], Token)
        size = nodes[1] if has_size else None
        return ArrayType(size, nodes[3 if has_size else 2], self.mkpos(nodes[0])+nodes[-1].pos)

    def map_type(self, *nodes):
        return MapType(nodes[1], nodes[3], self.mkpos(nodes[0])+self.mkpos(nodes[-1]))

    def sum_type(self, *nodes):
        types = list(filter(lambda node: not isinstance(node, Token), nodes))
        return SumType(types, nodes[0].pos+nodes[-1].pos)
