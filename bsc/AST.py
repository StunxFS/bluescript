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

class ExternPkg:
    def __init__(self, pkg_name, alias_name, pos):
        self.pkg_name = pkg_name
        self.alias_name = alias_name
        self.pos = pos

class FnDecl:
    def __init__(self, name, args, ret_type, stmts, is_main):
        self.name = name
        self.args = ret_type
        self.ret_type = ret_type
        self.stmts = stmts
        self.is_main = is_main

class FnArg:
    def __init__(self, name, type, default_value):
        self.name = name
        self.type = type
        self.default_value = default_value

# Statements

class OpAssign(IntEnum):
    Decl = auto()
    Assign = auto()
    PlusAssign = auto()
    MinusAssign = auto()
    DivAssign = auto()
    MulAssign = auto()
    ModAssign = auto()
    AndAssign = auto()
    OrAssign = auto()
    XorAssign = auto()

    def __str__(self):
        return op_assign_str(self)

def op_assign_str(op_assign):
    match op_assign:
        case OpAssign.Decl:
            return "="
        case OpAssign.PlusAssign:
            return "+="
        case OpAssign.MinusAssign:
            return "-="
        case OpAssign.DivAssign:
            return "-="
        case OpAssign.MulAssign:
            return "*="
        case OpAssign.ModAssign:
            return "%="
        case OpAssign.AndAssign:
            return "&="
        case OpAssign.OrAssign:
            return "|="
        case OpAssign.XorAssign:
            return "^="
    return ":="

class AssignStmt:
    def __init__(self, lefts, op, right, pos):
        self.lefts = lefts
        self.op = op
        self.right = right
        self.pos = pos

    def __str__(self):
        return f"{', '.join([str(left) for left in self.lefts])} {self.op} {str(self.right)}"

class WhileStmt:
    def __init__(self, cond, stmt, pos):
        self.cond = cond
        self.stmt = stmt
        self.pos = pos

    def __str__(self):
        return f"while ({self.cond}) {self.stmt}"

class BlockStmt:
    def __init__(self, stmts, pos):
        self.stmts = stmts
        self.pos = pos

    def __str__(self):
        stmts = '\n'.join([str(stmt) for stmt in self.stmts])
        return f"{{ {stmts} }}"

# Expressions

class ParExpr:
    def __init__(self, expr, pos):
        self.expr = expr
        self.pos = pos

    def __str__(self):
        return f"({self.expr})"

class BuiltinVar:
    def __init__(self, name, pos):
        self.name = name
        self.pos = pos

    def __str__(self):
        return f"@{self.name}"

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

class ArrayLiteral:
    def __init__(self, elems, is_fixed, pos):
        self.elems = elems
        self.is_fixed = is_fixed
        self.pos = pos

    def __str__(self):
        _str = f"[{', '.join([str(elem) for elem in self.elems])}]"
        if self.is_fixed:
            _str += "!"
        return _str

class TupleLiteral:
    def __init__(self, elems, pos):
        self.elems = elems
        self.pos = pos

    def __str__(self):
        return f"[{', '.join([str(elem) for elem in self.elems])}]"

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

class CallExpr:
    def __init__(self, left, args, pos):
        self.left = left
        self.args = args
        self.pos = pos

    def __str__(self):
        return f"{self.left}({', '.join([str(arg) for arg in self.args])})"

class IfExpr:
    def __init__(self, branches, pos):
        self.branches = branches
        self.pos = pos

    def __str__(self):
        s = ""
        for i, branch in enumerate(self.branches):
            if branch.is_else:
                s += f"else {branch.stmt}"
                break
            if i > 0:
                s += "\nelse "
            s += f"if ({branch.cond}) {branch.stmt}" + "\n"
        return s

class IfBranch:
    def __init__(self, cond, is_else, stmt, pos):
        self.cond = cond
        self.is_else = is_else
        self.stmt = stmt
        self.pos = pos

# Types
class BasicType:
    def __init__(self, expr, pos):
        self.expr = expr
        self.typesym = None
        self.pos = pos

    @staticmethod
    def with_typesym(typesym, pos = None):
        res = BasicType(None, pos)
        res.typesym = typesym
        return res

    def __str__(self):
        if self.typesym:
            return str(self.typesym)
        return str(self.expr)

class OptionType:
    def __init__(self, type, pos):
        self.type = type
        self.pos = pos

    def __str__(self):
        return f"?{self.type}"

class ArrayType:
    def __init__(self, size, type, pos):
        self.size = size
        self.type = type
        self.pos = pos

    def __str__(self):
        if self.size:
            return f"[{self.size}]{self.type}"
        return f"[]{self.type}"

class MapType:
    def __init__(self, k_type, v_type, pos):
        self.k_type = k_type
        self.v_type = v_type
        self.pos = pos

    def __str__(self):
        return f"{{{self.k_type}:{self.v_type}}}"

class SumType:
    def __init__(self, types, pos):
        self.types = types
        self.pos = pos

    def __str__(self):
        return " | ".join([str(t) for t in self.types])

class TupleType:
    def __init__(self, types, pos):
        self.types = types
        self.pos = pos

    def __str__(self):
        return "(" + ", ".join([str(t) for t in self.types]) + ")"
