# Copyright (C) 2024 Jose Mendoza. All rights reserved. Use of this
# source code is governed by an MIT license that can be found in the
# LICENSE file.

from enum import IntEnum, auto

class Pos:
    def __init__(self, file, line, column, len, pos):
        self.file = file
        self.line = line
        self.column = column
        self.len = len
        self.pos = pos

    @staticmethod
    def from_token(file, token):
        return Pos(file, token.line, token.column, len(token), token.start_pos)

    def __add__(self, other):
        return Pos(
            self.file, other.line, other.column,
            other.pos - self.pos + other.len, self.pos
        )

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
        self.name = name

# Statements

# Expressions

class ParExpr:
    def __init__(self, expr, pos):
        self.expr = expr
        self.pos = pos

    def __str__(self):
        return f"({self.expr})"

class NilLiteral:
    def __init__(self, pos):
        self.pos = pos

    def __str__(self):
        return "nil"

class BoolLiteral:
    def __init__(self, value, pos):
        self.value = value
        self.pos = pos

    def __str__(self):
        return str(self.value)

class NumberLiteral:
    def __init__(self, value, pos):
        self.value = value
        self.pos = pos

    def __str__(self):
        return self.value

class StringLiteral:
    def __init__(self, value, pos):
        self.value = value
        self.pos = pos

    def __str__(self):
        return self.value

class SelfLiteral:
    def __init__(self, pos):
        self.pos = pos

    def __str__(self):
        return "self"

class Ident:
    def __init__(self, name, pos):
        self.name = name
        self.pos = pos

    def __str__(self):
        return self.name

class SelectorExpr:
    def __init__(self, left, name, pos):
        self.left = left
        self.name = name
        self.pos = pos

    def __str__(self):
        return f"{self.left}.{self.name}"

# Types
class BasicType:
    def __init__(self, expr,pos):
        self.expr=expr
        self.pos=pos

    def __str__(self):
        return str(self.expr)

class OptionType:
    def __init__(self, type, pos):
        self.type=type
        self.pos=pos

    def __str__(self):
        return f"?{self.type}"

class ArrayType:
    def __init__(self, size, type, pos):
        self.size=size
        self.type=type
        self.pos=pos

    def __str__(self):
        if self.size:
            return f"[{self.size}]{self.type}"
        return f"[]{self.type}"

class MapType:
    def __init__(self, k_type, v_type, pos):
        self.k_type=k_type
        self.v_type=v_type
        self.pos=pos

    def __str__(self):
        return f"{{{self.k_type}:{self.v_type}}}"

class SumType:
    def __init__(self, types, pos):
        self.types=types
        self.pos=pos

    def __str__(self):
        return " | ".join([str(t) for t in self.types])

class TupleType:
    def __init__(self, types, pos):
        self.types=types
        self.pos=pos

    def __str__(self):
        return "(" + ", ".join([str(t) for t in self.types]) + ")"
