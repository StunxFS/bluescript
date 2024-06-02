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
        self.scope = scope

    def is_local(self):
        return self.level in (ObjectLevel.argument, ObjectLevel.local)

class Const(Sym):
    def __init__(self, access_modifier, name, typ, expr, scope):
        super().__init__(access_modifier, name)
        self.typ = typ
        self.expr = expr
        self.scope = scope

class Typekind(IntEnum):
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

class TypeField:
    def __init__(self, access_modifier, name, typ, default_value):
        self.access_modifier = access_modifier
        self.name = name
        self.typ = typ
        self.default_value = default_value

class TypeSym(Sym):
    def __init__(self, access_modifier, kind, name, fields, scope):
        super().__init__(access_modifier, name)
        self.fields = fields
        self.scope = scope

class Module(Sym):
    def __init__(self, access_modifier, name, scope):
        super().__init__(access_modifier, name)
        self.scope = scope

class Scope:
    def __init__(
        self, parent = None, detach_from_parent = False, is_universe = False
    ):
        self.parent = parent
        self.syms = []
        self.children = []
        self.detached_from_parent = False
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
            raise CompilerError(f"redefined symbol `{sym.name}`")
        sym.parent = self
        self.syms.append(sym)
