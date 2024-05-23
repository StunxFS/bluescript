# Copyright (C) 2024 Jose Mendoza. All rights reserved. Use of this 
# source code is governed by an MIT license that can be found in the 
# LICENSE file.

from lark import Lark, Transformer, v_args

with open("bsc/bluescript.lark", "r") as bs_grammar_file:
    bs_grammar = bs_grammar_file.read()

bs_parser = Lark(bs_grammar, parser='lalr')
# Disabling propagate_positions and placeholders slightly improves speed
#propagate_positions=False,
#maybe_placeholders=False,
# Using an internal transformer is faster and more memory efficient
print(bs_parser.parse(open("examples/hello_world.bs").read()))