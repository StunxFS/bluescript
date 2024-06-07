# Copyright (C) 2024 Jose Mendoza. All rights reserved. Use of this
# source code is governed by an MIT license that can be found in the
# LICENSE file.

class LuaModule:
    def __init__(self, name):
        self.name = name
        self.decls = []

class LuaIdent:
    def __init__(self, name):
        self.name = name

class LuaFunction:
    def __init__(self, name, args):
        self.name = name
        self.args = args
        self.stmts = []

class LuaBlock:
    def __init__(self):
        self.chunk = []
