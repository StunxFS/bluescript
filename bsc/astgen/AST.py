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
    def __init__(self, file, decls, mod_sym, deps = []):
        self.file = file
        self.mod_sym = mod_sym
        self.decls = decls
        self.deps = deps

# Declarations

class ExternPkg:
    def __init__(self, pkg_name, alias_name, pos):
        self.pkg_name = pkg_name
        self.alias_name = alias_name
        self.pos = pos
        self.sym = None

class ModDecl:
    def __init__(
        self, access_modifier, name, is_inline, decls, pos, sym = None
    ):
        self.access_modifier = access_modifier
        self.name = name
        self.is_inline = is_inline
        self.decls = decls
        self.pos = pos
        self.sym = sym

class EnumDecl:
    def __init__(self, access_modifier, name, fields, decls, pos):
        self.access_modifier = access_modifier
        self.name = name
        self.fields = fields
        self.decls = decls
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
        self.has_body = stmts != None
        self.is_main = is_main
        self.is_method = False
        self.sym = None
        self.pos = pos

class FnArg:
    def __init__(self, name, type, default_value, pos):
        self.name = name
        self.type = type
        self.default_value = default_value
        self.pos = pos

class ConstDecl:
    def __init__(self, access_modifier, name, typ, expr, pos):
        self.access_modifier = access_modifier
        self.name = name
        self.typ = typ
        self.expr = expr
        self.pos = pos
        self.sym = None
        self.is_local = False

class VarDecl:
    def __init__(self, access_modifier, lefts, right, pos):
        self.access_modifier = access_modifier
        self.lefts = lefts
        self.right = right
        self.pos = pos

class VarIdent:
    def __init__(self, name, typ, pos):
        self.name = name
        self.typ = typ
        self.pos = pos
        self.sym = None

# Statements

class Stmt:
    pass

class ExprStmt(Stmt):
    def __init__(self, expr):
        assert isinstance(expr, Expr)
        self.expr = expr
        self.pos = expr.pos

    def __str__(self):
        return f"{self.expr};"

    def __repr__(self):
        return str(self)

class AssignOp(IntEnum):
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
            case AssignOp.Assign:
                return "="
            case AssignOp.PlusAssign:
                return "+="
            case AssignOp.MinusAssign:
                return "-="
            case AssignOp.DivAssign:
                return "-="
            case AssignOp.MulAssign:
                return "*="
            case AssignOp.ModAssign:
                return "%="
            case AssignOp.AndAssign:
                return "&="
            case AssignOp.OrAssign:
                return "|="
            case AssignOp.XorAssign:
                return "^="
        assert False # unreachable

class WhileStmt(Stmt):
    def __init__(self, cond, stmts, pos):
        self.cond = cond
        self.stmts = stmts
        self.pos = pos

    def __str__(self):
        res = f"while {self.cond} {{\n"
        for stmt in self.stmts:
            res += f"    {stmt}\n"
        res += "}"
        return res

# Expressions

class Expr:
    pass

class ParExpr(Expr):
    def __init__(self, expr, pos):
        self.expr = expr
        self.pos = pos
        self.typ = None

    def __str__(self):
        return f"({self.expr})"

    def __repr__(self):
        return str(self)

class BuiltinVar(Expr):
    def __init__(self, name, pos):
        self.name = name
        self.pos = pos
        self.typ = None

    def __str__(self):
        return f"${self.name}"

    def __repr__(self):
        return str(self)

class NilLiteral(Expr):
    def __init__(self, pos):
        self.pos = pos
        self.typ = None

    def __str__(self):
        return "nil"

    def __repr__(self):
        return str(self)

class BoolLiteral(Expr):
    def __init__(self, value, pos):
        self.value = value
        self.pos = pos
        self.typ = None

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return str(self)

class NumberLiteral(Expr):
    def __init__(self, value, pos):
        self.value = value
        self.pos = pos
        self.typ = None

    def __str__(self):
        return self.value

    def __repr__(self):
        return str(self)

class StringLiteral(Expr):
    def __init__(self, value, pos):
        self.value = value
        self.pos = pos
        self.typ = None

    def __str__(self):
        return self.value

    def __repr__(self):
        return str(self)

class SelfLiteral(Expr):
    def __init__(self, pos):
        self.pos = pos
        self.typ = None

    def __str__(self):
        return "self"

    def __repr__(self):
        return str(self)

class ArrayLiteral(Expr):
    def __init__(self, elems, is_fixed, pos):
        self.elems = elems
        self.is_fixed = is_fixed
        self.pos = pos
        self.typ = None

    def __str__(self):
        _str = "#[" if self.is_fixed else "["
        return _str + f"{', '.join([str(elem) for elem in self.elems])}]"

    def __repr__(self):
        return str(self)

class TupleLiteral(Expr):
    def __init__(self, elems, pos):
        self.elems = elems
        self.pos = pos
        self.typ = None

    def __str__(self):
        return f"[{', '.join([str(elem) for elem in self.elems])}]"

    def __repr__(self):
        return str(self)

class EnumLiteral(Expr):
    def __init__(self, name, pos):
        self.name = name
        self.pos = pos
        self.typ = None

    def __str__(self):
        return f".{self.name}"

    def __repr__(self):
        return str(self)

class Ident(Expr):
    def __init__(self, name, pos):
        self.name = name
        self.pos = pos
        self.scope = None
        self.sym = None
        self.typ = None

    def __str__(self):
        return self.name

    def __repr__(self):
        return str(self)

class PathExpr(Expr):
    def __init__(self, left, name, pos):
        self.left = left
        self.name = name
        self.pos = pos
        self.typ = None

    def __str__(self):
        return f"{self.left}::{self.name}"

    def __repr__(self):
        return str(self)

class SelectorExpr(Expr):
    def __init__(self, left, name, pos):
        self.left = left
        self.name = name
        self.pos = pos
        self.sym = None
        self.typ = None

    def __str__(self):
        return f"{self.left}.{self.name}"

    def __repr__(self):
        return str(self)

class CallExpr(Expr):
    def __init__(self, left, args, pos):
        self.left = left
        self.args = args
        self.pos = pos
        self.typ = None

    def __str__(self):
        return f"{self.left}({', '.join([str(arg) for arg in self.args])})"

    def __repr__(self):
        return str(self)

class UnaryOp(IntEnum):
    bang = auto()
    bit_not = auto()
    minus = auto()

    def to_lua_op(self):
        match self:
            case UnaryOp.bang:
                return "not "
            case UnaryOp.bit_not:
                return "~"
            case UnaryOp.minus:
                return "-"
            case _:
                assert False #unreachable

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

    def __repr__(self):
        return str(self)

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
    eq = auto()
    neq = auto()
    lt = auto()
    gt = auto()
    le = auto()
    ge = auto()
    logical_and = auto()
    logical_or = auto()

    def is_relational(self):
        return self in (
            BinaryOp.eq, BinaryOp.neq, BinaryOp.lt, BinaryOp.gt, BinaryOp.le,
            BinaryOp.ge, BinaryOp.logical_and, BinaryOp.logical_or
        )

    def to_lua_op(self):
        match self:
            case BinaryOp.logical_and:
                return "and"
            case BinaryOp.logical_or:
                return "or"
            case _:
                return str(self)

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

class UnaryExpr(Expr):
    def __init__(self, op, right, pos):
        self.op = op
        self.right = right
        self.pos = pos
        self.typ = None

    def __str__(self):
        return f"{self.op}{self.right}"

    def __repr__(self):
        return str(self)

class BinaryExpr(Expr):
    def __init__(self, left, op, right, pos):
        self.left = left
        self.op = op
        self.right = right
        self.pos = pos
        self.typ = None

    def __str__(self):
        return f"{self.left} {self.op} {self.right}"

    def __repr__(self):
        return str(self)

class IfExpr(Expr):
    def __init__(self, branches, pos):
        self.branches = branches
        self.pos = pos
        self.typ = None

    def __str__(self):
        s = ""
        for i, branch in enumerate(self.branches):
            if branch.is_else:
                s += f" else {branch.expr}"
                break
            if i > 0:
                s += " else "
            s += f"if {branch.cond} {branch.expr}"
        return s

    def __repr__(self):
        return str(self)

class IfBranch:
    def __init__(self, cond, is_else, expr, pos):
        self.cond = cond
        self.is_else = is_else
        self.expr = expr
        self.pos = pos
        self.typ = None

class MatchExpr(Expr):
    def __init__(self, expr, branches, pos):
        self.expr = expr
        self.branches = branches
        self.pos = pos
        self.typ = None

    def __str__(self):
        if self.expr:
            s = f"match {self.expr} {{\n"
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
        self.typ = None

class BlockExpr(Expr):
    def __init__(self, is_unsafe, stmts, expr, pos):
        self.is_unsafe = is_unsafe
        self.stmts = stmts
        self.expr = expr
        self.pos = pos
        self.scope = None
        self.typ = None

    def __str__(self):
        stmts = '\n'.join([str(stmt) for stmt in self.stmts])
        res = "unsafe " if self.is_unsafe else ""
        res += f"{{ {stmts} }}"
        return res

class ReturnExpr(Expr):
    def __init__(self, expr, pos):
        self.expr = expr
        self.pos = pos
        self.typ = None

    def __str__(self):
        if self.expr != None:
            return f"return {self.expr}"
        return "return"

    def __repr__(self):
        return str(self)

class AssignExpr(Expr):
    def __init__(self, lefts, op, right, pos):
        self.lefts = lefts
        self.op = op
        self.right = right
        self.pos = pos
        self.typ = None

    def __str__(self):
        return f"{', '.join([str(left) for left in self.lefts])} {self.op} {str(self.right)}"

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

    def __eq__(self, other):
        if isinstance(other, BasicType):
            if self.typesym:
                return self.typesym == other.typesym
            return str(self.expr) == str(other.expr)
        return False

class OptionType:
    def __init__(self, type, pos):
        self.type = type
        self.pos = pos

    def __str__(self):
        return f"?{self.type}"

    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        if isinstance(other, OptionType):
            return self.type == other.type
        return False

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

    def __eq__(self, other):
        if isinstance(other, ArrayType):
            return str(self.size) == str(other.size) and self.type == other.type
        return False

class MapType:
    def __init__(self, k_type, v_type, pos):
        self.k_type = k_type
        self.v_type = v_type
        self.pos = pos

    def __str__(self):
        return f"{{{self.k_type}:{self.v_type}}}"

    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        if isinstance(other, MapType):
            return self.k_type == other.k_type and self.v_type == other.v_type
        return False

class SumType:
    def __init__(self, types, pos):
        self.types = types
        self.pos = pos

    def __str__(self):
        return " | ".join([str(t) for t in self.types])

    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        if isinstance(other, SumType):
            if len(self.types) != len(other.types):
                return False
            for i, t in enumerate(self.types):
                if t != other.types[i]:
                    return False
            return True
        return False

class TupleType:
    def __init__(self, types, pos):
        self.types = types
        self.pos = pos

    def __str__(self):
        return "(" + ", ".join([str(t) for t in self.types]) + ")"

    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        if isinstance(other, TupleType):
            if len(self.types) != len(other.types):
                return False
            for i, t in enumerate(self.types):
                if t != other.types[i]:
                    return False
            return True
        return False
