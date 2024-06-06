# Copyright (C) 2024 Jose Mendoza. All rights reserved. Use of this
# source code is governed by an MIT license that can be found in the
# LICENSE file.

import os, argparse

from bsc import utils

class Prefs:
    def __init__(self):
        self.input = ""
        self.is_library = False

    def parse_args(self):
        parser = argparse.ArgumentParser(
            prog = 'bsc', description = 'The BlueScript compiler'
        )
        parser.add_argument('input', help = "the input file")
        parser.add_argument(
            '--lib', action = 'store_true',
            help = 'specifies whether the entry is a library or not'
        )
        args = parser.parse_args()

        self.is_library = args.lib

        # check input file
        self.input = args.input
        if os.path.isdir(self.input):
            input_file = "lib.bs" if self.is_library else "main.bs"
            self.input = os.path.join(self.input, input_file)

        if not os.path.exists(self.input):
            utils.error(f"file `{self.input}` does not exist")
