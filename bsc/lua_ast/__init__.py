# Copyright (C) 2024 Jose Mendoza. All rights reserved. Use of this
# source code is governed by an MIT license that can be found in the
# LICENSE file.

class LuaModule:
    def __init__(self, name, decls = [], is_inline = False, lua_filename = ""):
        self.name = name
        self.decls = decls
        self.is_inline = is_inline
        self.lua_filename = lua_filename

class LuaTableField:
    def __init__(self, name, value):
        self.name = name
        self.value = value

class LuaTable:
    def __init__(self, name, fields):
        self.name = name
        self.fields = fields

class LuaFunction:
    def __init__(self, name, args):
        self.name = name
        self.args = args
        self.stmts = []

# Statements

class LuaWhile:
    def __init__(self, cond, stmts):
        self.cond = cond
        self.stmts = stmts

class LuaRepeat:
    def __init__(self, stmts, cond):
        self.stmts = stmts
        self.cond = cond

class LuaIf:
    def __init__(self, branches):
        self.branches = branches

class LuaIfBranch:
    def __init__(self, cond, is_else, stmts):
        self.cond = cond
        self.is_else = is_else
        self.stmts = stmts

class LuaBlock:
    def __init__(self):
        self.chunk = []

class LuaAssignment:
    def __init__(self, lefts, op, rights):
        self.lefts = lefts
        self.op = op
        self.rights = rights

# Expressions

class LuaCallExpr:
    def __init__(self, left, args):
        self.left = left
        self.args = args

class LuaSelector:
    def __init__(self, left, name):
        self.left = left
        self.name = name

class LuaIdent:
    def __init__(self, name):
        self.name = name

class LuaParenExpr:
    def __init__(self, expr):
        self.expr = expr

class LuaNumberLit:
    def __init__(self, value):
        self.value = value

class LuaBooleanLit:
    def __init__(self, value):
        self.value = value

class LuaNil:
    pass
