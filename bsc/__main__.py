# Copyright (C) 2024 Jose Mendoza. All rights reserved. Use of this 
# source code is governed by an MIT license that can be found in the 
# LICENSE file.

from lark import Lark

from astgen import AstGen

with open("bsc/bluescript.lark", "r") as bs_grammar_file:
    bs_grammar = bs_grammar_file.read()

bs_parser = Lark(bs_grammar, parser='earley')
ast = AstGen(True).transform(bs_parser.parse(open("examples/syntax.bs").read()))
print(ast)