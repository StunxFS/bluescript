# Copyright (C) 2024 Jose Mendoza. All rights reserved. Use of this
# source code is governed by an MIT license that can be found in the
# LICENSE file.

import os

from lark import Transformer, Lark

from AST import *

cur_dirname = os.path.dirname(__file__)

class AstGen(Transformer):
    def __init__(self, ctx):
        super().__init__(True)
        self.ctx = ctx
        self.file = ""

    def parse_file(self, file):
        self.file = file

        with open(os.path.join(cur_dirname, "bluescript.lark"), "r") as bs_grammar_file:
            bs_grammar = bs_grammar_file.read()

        bs_parser = Lark(bs_grammar, parser='earley')
        return self.transform(bs_parser.parse(open(file).read()))

    def start(self, nodes):
        return SourceFile(self.file)
