# Copyright (C) 2024 Jose Mendoza. All rights reserved. Use of this
# source code is governed by an MIT license that can be found in the
# LICENSE file.

from typing import Any
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
    def __init__(self, file, decls, mod_sym):
        self.file = file
        self.mod_sym = mod_sym
        self.decls = decls

# Declarations

class ExternPkg:
    def __init__(self, pkg_name, alias_name, pos):
        self.pkg_name = pkg_name
        self.alias_name = alias_name
        self.pos = pos
        self.sym = None

class ModDecl:
    def __init__(self, access_modifier, name, is_inline, decls, pos, sym=None):
        self.access_modifier = access_modifier
        self.name = name
        self.is_inline = is_inline
        self.decls = decls
        self.pos = pos
        self.sym = sym

class EnumDecl:
    def __init__(self, access_modifier, name, fields, pos):
        self.access_modifier = access_modifier
        self.name = name
        self.fields = fields
        self.pos = pos
        self.sym = None

class EnumField:
    def __init__(self, name, value):
        self.name = name
        self.value = value

class FnDecl:
    def __init__(
        self, access_modifier, name, args, is_method, ret_type, stmts, is_main,
        pos
    ):
        self.access_modifier = access_modifier
        self.name = name
        self.args = args
        self.is_method = is_method
        self.ret_type = ret_type
        self.stmts = stmts
        self.is_main = is_main
        self.sym = None
        self.pos = pos

class FnArg:
    def __init__(self, name, type, default_value):
        self.name = name
        self.type = type
        self.default_value = default_value

# Statements

class OpAssign(IntEnum):
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
        match self:
            case OpAssign.Assign:
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
        assert False # unreachable

class VarIdent:
    def __init__(self, name, typ, pos):
        self.name = name
        self.typ = typ
        self.pos = pos

class VarDecl:
    def __init__(self, lefts, right):
        self.lefts = lefts
        self.right = right

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

    def __repr__(self):
        return str(self)

class BuiltinVar:
    def __init__(self, name, pos):
        self.name = name
        self.pos = pos

    def __str__(self):
        return f"@{self.name}"

    def __repr__(self):
        return str(self)

class NilLiteral:
    def __init__(self, pos):
        self.pos = pos

    def __str__(self):
        return "nil"

    def __repr__(self):
        return str(self)

class BoolLiteral:
    def __init__(self, value, pos):
        self.value = value
        self.pos = pos

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return str(self)

class NumberLiteral:
    def __init__(self, value, pos):
        self.value = value
        self.pos = pos

    def __str__(self):
        return self.value

    def __repr__(self):
        return str(self)

class StringLiteral:
    def __init__(self, value, pos):
        self.value = value
        self.pos = pos

    def __str__(self):
        return self.value

    def __repr__(self):
        return str(self)

class SelfLiteral:
    def __init__(self, pos):
        self.pos = pos

    def __str__(self):
        return "self"

    def __repr__(self):
        return str(self)

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

    def __repr__(self):
        return str(self)

class TupleLiteral:
    def __init__(self, elems, pos):
        self.elems = elems
        self.pos = pos

    def __str__(self):
        return f"[{', '.join([str(elem) for elem in self.elems])}]"

    def __repr__(self):
        return str(self)

class EnumLiteral:
    def __init__(self, name, pos):
        self.name = name
        self.pos = pos

    def __str__(self):
        return f".{self.name}"

    def __repr__(self):
        return str(self)

class Ident:
    def __init__(self, name, pos):
        self.name = name
        self.pos = pos

    def __str__(self):
        return self.name

    def __repr__(self):
        return str(self)

class PathExpr:
    def __init__(self, left, name, pos):
        self.left = left
        self.name = name
        self.pos = pos

    def __str__(self):
        return f"{self.left}::{self.name}"

    def __repr__(self):
        return str(self)

class SelectorExpr:
    def __init__(self, left, name, pos):
        self.left = left
        self.name = name
        self.pos = pos

    def __str__(self):
        return f"{self.left}.{self.name}"

    def __repr__(self):
        return str(self)

class CallExpr:
    def __init__(self, left, args, pos):
        self.left = left
        self.args = args
        self.pos = pos

    def __str__(self):
        return f"{self.left}({', '.join([str(arg) for arg in self.args])})"

    def __repr__(self):
        return str(self)

class UnaryOp(IntEnum):
    bang = auto()
    bit_not = auto()
    minus = auto()

    def __str__(self):
        match self:
            case UnaryOp.bang:
                return "!"
            case UnaryOp.bit_not:
                return "~"
            case UnaryOp.minus:
                return "-"
            case _:
                assert False #unreachable

class BinaryOp(IntEnum):
    plus = auto()
    minus = auto()
    mul = auto()
    div = auto()
    mod = auto()
    bit_and = auto()
    bit_or = auto()
    bit_xor = auto()
    lshift = auto()
    rshift = auto()
    lt = auto()
    gt = auto()
    le = auto()
    ge = auto()
    eq = auto()
    neq = auto()
    logical_and = auto()
    logical_or = auto()

    def __str__(self):
        match self:
            case BinaryOp.plus:
                return "+"
            case BinaryOp.minus:
                return "-"
            case BinaryOp.mul:
                return "*"
            case BinaryOp.div:
                return "/"
            case BinaryOp.mod:
                return "%"
            case BinaryOp.bit_and:
                return "&"
            case BinaryOp.bit_or:
                return "|"
            case BinaryOp.bit_xor:
                return "^"
            case BinaryOp.lshift:
                return "<<"
            case BinaryOp.rshift:
                return ">>"
            case BinaryOp.lt:
                return "<"
            case BinaryOp.gt:
                return ">"
            case BinaryOp.le:
                return "<="
            case BinaryOp.ge:
                return ">="
            case BinaryOp.eq:
                return "=="
            case BinaryOp.neq:
                return "!="
            case BinaryOp.logical_and:
                return "&&"
            case BinaryOp.logical_or:
                return "||"
            case _:
                assert False #unreachable

    def __repr__(self):
        return str(self)

class UnaryExpr:
    def __init__(self, op, right, pos):
        self.op = op
        self.right = right
        self.pos = pos

    def __str__(self):
        return f"{self.op}{self.right}"

    def __repr__(self):
        return str(self)

class BinaryExpr:
    def __init__(self, left, op, right, pos):
        self.left = left
        self.op = op
        self.right = right
        self.pos = pos

    def __str__(self):
        return f"{self.left} {self.op} {self.right}"

    def __repr__(self):
        return str(self)

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
                s += "else "
            s += f"if ({branch.cond}) {branch.stmt}" + "\n"
        return s

    def __repr__(self):
        return str(self)

class IfBranch:
    def __init__(self, cond, is_else, stmt, pos):
        self.cond = cond
        self.is_else = is_else
        self.stmt = stmt
        self.pos = pos

class MatchExpr:
    def __init__(self, expr, branches, pos):
        self.expr = expr
        self.branches = branches
        self.pos = pos

    def __str__(self):
        if self.expr:
            s = f"match ({self.expr}) {{\n"
        else:
            s = "match {\n"
        for i, branch in enumerate(self.branches):
            if branch.is_else:
                s += f"    else -> {branch.stmt}"
                break
            s += f"    {', '.join([str(pat) for pat in branch.cases])} -> {branch.stmt}"
            if i < len(self.branches) - 1:
                s += "\n"
        s += "\n}"
        return s

    def __repr__(self):
        return str(self)

class MatchBranch:
    def __init__(self, cases, is_else, stmt, pos):
        self.cases = cases
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

    def __repr__(self):
        return str(self)

class OptionType:
    def __init__(self, type, pos):
        self.type = type
        self.pos = pos

    def __str__(self):
        return f"?{self.type}"

    def __repr__(self):
        return str(self)

class ArrayType:
    def __init__(self, size, type, pos):
        self.size = size
        self.type = type
        self.pos = pos

    def __str__(self):
        if self.size:
            return f"[{self.size}]{self.type}"
        return f"[]{self.type}"

    def __repr__(self):
        return str(self)

class MapType:
    def __init__(self, k_type, v_type, pos):
        self.k_type = k_type
        self.v_type = v_type
        self.pos = pos

    def __str__(self):
        return f"{{{self.k_type}:{self.v_type}}}"

    def __repr__(self):
        return str(self)

class SumType:
    def __init__(self, types, pos):
        self.types = types
        self.pos = pos

    def __str__(self):
        return " | ".join([str(t) for t in self.types])

    def __repr__(self):
        return str(self)

class TupleType:
    def __init__(self, types, pos):
        self.types = types
        self.pos = pos

    def __str__(self):
        return "(" + ", ".join([str(t) for t in self.types]) + ")"

    def __repr__(self):
        return str(self)
