# Copyright (C) 2024 Jose Mendoza. All rights reserved. Use of this
# source code is governed by an MIT license that can be found in the
# LICENSE file.

import os
import argparse

import utils

class Prefs:
    def __init__(self):
        self.input = ""

    def parse_args(self):
        parser = argparse.ArgumentParser(
            prog = 'bsc', description = 'The BlueScript compiler'
        )
        parser.add_argument('input', help = "the input file")
        args = parser.parse_args()

        # check input file
        self.input = args.input
        if os.path.exists(self.input):
            if not os.path.isfile(self.input):
                utils.error(f"`{self.input}` is a directory, expected a file")
        else:
            utils.error(f"file `{self.input}` does not exist")
