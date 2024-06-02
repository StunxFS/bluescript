# Copyright (C) 2024 Jose Mendoza. All rights reserved. Use of this
# source code is governed by an MIT license that can be found in the
# LICENSE file.

from bsc.prefs import Prefs
from bsc.astgen import AstGen

class Context:
    def __init__(self):
        self.prefs = Prefs()
        self.astgen = AstGen(self)

        self.prefs.parse_args()

        self.source_files = []

    def parse_files(self):
        self.source_files.append(self.astgen.parse_file(self.prefs.input))
