# Copyright (C) 2024 Jose Mendoza. All rights reserved. Use of this
# source code is governed by an MIT license that can be found in the
# LICENSE file.

class LuaModule:
    def __init__(self, name):
        self.name = name
        self.decls = []

class LuaTableField:
    def __init__(self, name, value):
        self.name = name
        self.value = value

class LuaTable:
    def __init__(self, is_local, name, fields):
        self.is_local = is_local
        self.name = name
        self.fields = fields

class LuaFunction:
    def __init__(self, name, args):
        self.name = name
        self.args = args
        self.stmts = []

class LuaBlock:
    def __init__(self):
        self.chunk = []

class LuaIdent:
    def __init__(self, name):
        self.name = name

class LuaNil:
    pass
