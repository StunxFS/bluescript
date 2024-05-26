# Copyright (C) 2024 Jose Mendoza. All rights reserved. Use of this
# source code is governed by an MIT license that can be found in the
# LICENSE file.

from enum import IntEnum, auto

class Pos:
    def __init__(self,file, line, column, len, pos):
        self.file=file
        self.line=line
        self.column=column
        self.len=len
        self.pos=pos

    @staticmethod
    def from_token(file, token):
        return Pos(file, token.line,token.column,len(token), token.start_pos)

    def __add__(self, other):
        return Pos(self.file, other.line, other.column, other.pos - self.pos + other.len, self.pos)

    def __str__(self):
        return f"Pos(file='{self.file}', line={self.line}, column={self.column}, len={self.len}, pos={self.pos})"

class SourceFile:
    def __init__(self, file):
        self.file = file
        self.nodes = []

# Declarations

class AccessModifier(IntEnum):
    private = auto()
    public = auto()
    protected = auto()

class FnDecl:
    def __init__(self, name):
        self.name=name

# Statements

# Expressions

class ParExpr:
    def __init__(self, expr, pos):
        self.expr=expr
        self.pos=pos

class NilLiteral:
    def __init__(self, pos):
        self.pos=pos

class BoolLiteral:
    def __init__(self, value, pos):
        self.value=value
        self.pos=pos

class NumberLiteral:
    def __init__(self, value, pos):
        self.value=value
        self.pos=pos

class StringLiteral:
    def __init__(self, value, pos):
        self.value=value
        self.pos=pos

class SelfLiteral:
    def __init__(self, pos):
        self.pos=pos

class Ident:
    def __init__(self, name, pos):
        self.name = name
        self.pos=pos

class SelectorExpr:
    def __init__(self, left, name, pos):
        self.left=left
        self.name=name
        self.pos=pos

