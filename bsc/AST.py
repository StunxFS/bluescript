# Copyright (C) 2024 Jose Mendoza. All rights reserved. Use of this
# source code is governed by an MIT license that can be found in the
# LICENSE file.

class SourceFile:
    def __init__(self, file):
        self.file = file
        self.nodes = []