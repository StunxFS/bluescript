# Copyright (C) 2024 Jose Mendoza. All rights reserved. Use of this
# source code is governed by an MIT license that can be found in the
# LICENSE file.

import os, argparse

from bsc import utils

class Prefs:
    def __init__(self):
        self.input = ""
        self.is_library = False

        self.pkg_name = ""

    def parse_args(self):
        parser = argparse.ArgumentParser(
            prog = 'bsc', description = 'The BlueScript compiler'
        )
        parser.add_argument('INPUT', help = "the input file", nargs = 1)
        parser.add_argument(
            '--lib', action = 'store_true',
            help = 'specifies whether the input is a library or not'
        )
        parser.add_argument(
            '--pkg-name', action = 'store', metavar = 'pkg_name', help =
            'specifies the name of the package being compiled (by default the name of the given file or directory will be used)'
        )
        args = parser.parse_args()

        self.is_library = args.lib
        self.pkg_name = args.pkg_name or ""

        # check input file
        self.input = args.INPUT[0]

        # the package name will be the name of the given input,
        # whether directory or file
        if self.pkg_name == "":
            self.pkg_name = os.path.basename(self.input)
            if self.pkg_name == "":
                self.pkg_name = os.path.normpath(self.input)
            if os.path.isfile(self.input):
                self.pkg_name = os.path.splitext(self.pkg_name)[0]

        # if the input is a directory, try loading `main.bs`
        # or `lib.bs` as main input
        if os.path.isdir(self.input):
            input_file = "lib.bs" if self.is_library else "main.bs"
            self.input = os.path.join(self.input, input_file)

        # we make sure the input exists
        if not os.path.exists(self.input):
            utils.error(f"file `{self.input}` does not exist")
