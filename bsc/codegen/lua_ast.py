# Copyright (C) 2024 Jose Mendoza. All rights reserved. Use of this
# source code is governed by an MIT license that can be found in the
# LICENSE file.

class LuaSkip:
    pass

class LuaComment:
    def __init__(self, comment):
        self.comment = comment

class LuaModule:
    def __init__(self, name):
        self.name = name
        self.block = LuaBlock()

class LuaTableField:
    def __init__(self, key, value):
        self.key = key
        self.value = value

class LuaTable:
    def __init__(self, fields):
        self.fields = fields

class LuaFunction:
    def __init__(self, name, args, is_static = False):
        self.name = name
        self.args = args
        self.is_static = is_static
        self.block = LuaBlock()

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
    def __init__(self, stmts = []):
        self.stmts = stmts.copy()

    def add_comment(self, comment):
        self.add_stmt(LuaComment(comment))

    def add_stmt(self, stmt):
        self.stmts.append(stmt)

class LuaAssignment:
    def __init__(self, lefts, rights, is_local = True):
        self.is_local = is_local
        self.lefts = lefts
        self.rights = rights

class LuaReturn:
    def __init__(self, expr):
        self.expr = expr

# Expressions

class LuaParenExpr:
    def __init__(self, expr):
        self.expr = expr

class LuaBinaryExpr:
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right

class LuaUnaryExpr:
    def __init__(self, op, right):
        self.op = op
        self.right = right

class LuaCallExpr:
    def __init__(self, name, args = [], left = None, is_method = False):
        self.name = name
        self.args = args.copy()
        self.left = left
        self.is_method = is_method

class LuaSelector:
    def __init__(self, left, name):
        self.left = left
        self.name = name

class LuaIdent:
    def __init__(self, name):
        self.name = name

class LuaStringLit:
    def __init__(self, value):
        self.value = value

class LuaNumberLit:
    def __init__(self, value, is_float = False):
        self.value = value
        self.is_float = is_float

class LuaBooleanLit:
    def __init__(self, value):
        self.value = value

class LuaNil:
    pass
