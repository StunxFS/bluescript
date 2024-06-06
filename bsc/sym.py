# Copyright (C) 2024 Jose Mendoza. All rights reserved. Use of this
# source code is governed by an MIT license that can be found in the
# LICENSE file.

from enum import IntEnum, auto

from bsc.utils import CompilerError

class AccessModifier(IntEnum):
    private = auto()
    public = auto()
    protected = auto()

class Sym:
    def __init__(self, access_modifier, name):
        self.parent = None
        self.access_modifier = access_modifier
        self.name = name

    def typeof(self):
        if isinstance(self, Object):
            return "variable"
        elif isinstance(self, Const):
            return "constant"
        elif isinstance(self, TypeSym):
            return self.type_kind()
        elif isinstance(self, Module):
            return "module"
        return "symbol"

    def __str__(self):
        if self.parent and not self.parent.scope.is_universe:
            return f"{self.parent}.{self.name}"
        return self.name

class ObjectLevel(IntEnum):
    _global = auto()
    argument = auto()
    local = auto()

class Object(Sym):
    def __init__(self, access_modifier, name, level, typ, scope):
        super().__init__(access_modifier, name)
        self.level = level
        self.typ = typ
        scope.owner = self
        self.scope = scope

    def is_local(self):
        return self.level in (ObjectLevel.argument, ObjectLevel.local)

class Const(Sym):
    def __init__(self, access_modifier, name, typ, expr, scope):
        super().__init__(access_modifier, name)
        self.typ = typ
        self.expr = expr
        scope.owner = self
        self.scope = scope

class TypeKind(IntEnum):
    void = auto()
    any = auto()
    bool = auto()
    number = auto()
    string = auto()
    array = auto()
    map = auto()
    tuple = auto()
    sumtype = auto()
    _class = auto()

    def __str__(self):
        match self:
            case TypeKind.void:
                return "<void>"
            case TypeKind.any:
                return "any"
            case TypeKind.bool:
                return "bool"
            case TypeKind.number:
                return "number"
            case TypeKind.string:
                return "string"
            case TypeKind.array:
                return "array"
            case TypeKind.map:
                return "map"
            case TypeKind.tuple:
                return "tuple"
            case TypeKind.sumtype:
                return "sumtype"
            case TypeKind._class:
                return "class"
            case _:
                assert False # unreachable

class TypeField:
    def __init__(self, access_modifier, name, typ, default_value):
        self.access_modifier = access_modifier
        self.name = name
        self.typ = typ
        self.default_value = default_value

class TypeSym(Sym):
    def __init__(self, access_modifier, kind, name, fields, scope):
        super().__init__(access_modifier, name)
        self.kind = kind
        self.fields = fields
        scope.owner = self
        self.scope = scope

    def type_kind(self):
        return str(self.kind)

class Module(Sym):
    def __init__(self, access_modifier, name, scope):
        super().__init__(access_modifier, name)
        scope.owner = self
        self.scope = scope

class Scope:
    def __init__(
        self, parent = None, detach_from_parent = False, is_universe = False
    ):
        self.parent = parent
        self.owner = None
        self.syms = []
        self.children = []
        self.detached_from_parent = detach_from_parent
        self.is_universe = is_universe

    def lookup(self, name):
        sc = self
        while True:
            for sym in sc.syms:
                if sym.name == name:
                    return sym
            if sc.dont_lookup_scope():
                break
            sc = sc.parent
        return None

    def dont_lookup_scope(self):
        return self.parent == None or self.detached_from_parent

    def add_sym(self, sym):
        if _ := self.lookup(sym.name):
            if self.owner:
                errmsg = f"duplicate symbol `{sym.name}` in {self.owner.typeof()} `{self.owner.name}`"
            else:
                errmsg = f"duplicate symbol `{sym.name}` in global namespace"
            raise CompilerError(errmsg)
        sym.parent = self
        self.syms.append(sym)
