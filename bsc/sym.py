# Copyright (C) 2024 Jose Mendoza. All rights reserved. Use of this
# source code is governed by an MIT license that can be found in the
# LICENSE file.

from enum import IntEnum, auto

from bsc.utils import CompilerError

class AccessModifier(IntEnum):
    private = auto()
    internal = auto()
    public = auto()
    protected = auto()

    def is_public(self):
        return self == AccessModifier.public

    def is_private(self):
        return self in (
            AccessModifier.private, AccessModifier.internal,
            AccessModifier.protected
        )

    def __str__(self):
        match self:
            case AccessModifier.private:
                return "<priv>"
            case AccessModifier.internal:
                return "pub(pkg)"
            case AccessModifier.public:
                return "pub"
            case AccessModifier.protected:
                return "prot"
            case _:
                assert False #unreachable

    def __repr__(self):
        return str(self)

class Sym:
    def __init__(self, access_modifier, name, pos = None):
        self.parent = None
        self.access_modifier = access_modifier
        self.name = name
        self.pos = pos

    def get_pkg(self):
        s = self
        while True:
            if isinstance(s, Module) and s.is_pkg:
                return s
            if s.parent == None:
                break
            s = s.parent
        return None

    def get_mod(self):
        s = self
        while True:
            if isinstance(s, Module):
                return s
            if s.parent == None:
                break
            s = s.parent
        return None

    def has_access_to(self, other):
        match other.access_modifier:
            case AccessModifier.public:
                return True # other is public
            case AccessModifier.internal:
                return self.get_pkg() == other.get_pkg()
            case AccessModifier.private:
                if self_mod := self.get_mod():
                    if other_mod := other.get_mod():
                        return self_mod == other_mod
        return False

    def kind_of(self):
        if isinstance(self, Module):
            return "package" if self.is_pkg else "module"
        elif isinstance(self, Const):
            return "constant"
        elif isinstance(self, TypeSym):
            return self.kind_of()
        elif isinstance(self, Function):
            return "function"
        elif isinstance(self, Object):
            return "variable"
        return "symbol"

    def qualname(self, sep = "::"):
        if self.parent and not self.parent.scope.is_universe:
            return f"{self.parent.qualname(sep)}{sep}{self.name}"
        return self.name

    def cg_method_qualname(self):
        if isinstance(self.parent, TypeSym):
            return f"{self.parent.name}.{self.name}"
        return self.name

    def __eq__(self, other):
        return str(self) == str(other)

    def __repr__(self):
        return str(self)

    def __str__(self):
        if (isinstance(self, Object) and self.level != ObjectLevel.static
            ) or (isinstance(self, Const) and self.is_local):
            return self.name
        return self.qualname()

class ObjectLevel(IntEnum):
    static = auto()
    argument = auto()
    local = auto()

class Object(Sym):
    def __init__(self, access_modifier, name, level, typ, scope, pos = None):
        super().__init__(access_modifier, name, pos = pos)
        self.level = level
        self.typ = typ
        self.scope = scope

    def is_local(self):
        return self.level in (ObjectLevel.argument, ObjectLevel.local)

class Const(Sym):
    def __init__(
        self, access_modifier, name, typ, expr, scope, is_local = False,
        pos = None
    ):
        super().__init__(access_modifier, name, pos = pos)
        self.typ = typ
        self.expr = expr
        self.scope = scope
        self.is_local = is_local

class TypeKind(IntEnum):
    void = auto()
    never = auto()
    nil = auto()
    any = auto()
    bool = auto()
    int = auto()
    float = auto()
    string = auto()
    array = auto()
    table = auto()
    tuple = auto()
    sumtype = auto()
    enum = auto()
    _class = auto()

    def __str__(self):
        match self:
            case TypeKind.void:
                return "void"
            case TypeKind.never:
                return "never"
            case TypeKind.nil:
                return "nil"
            case TypeKind.any:
                return "any"
            case TypeKind.bool:
                return "bool"
            case TypeKind.int:
                return "int"
            case TypeKind.float:
                return "float"
            case TypeKind.string:
                return "string"
            case TypeKind.array:
                return "array"
            case TypeKind.table:
                return "table"
            case TypeKind.tuple:
                return "tuple"
            case TypeKind.sumtype:
                return "sumtype"
            case TypeKind.enum:
                return "enum"
            case TypeKind._class:
                return "class"
            case _:
                assert False # unreachable

class EnumInfo:
    def __init__(self, fields):
        self.fields = fields

class SumTypeInfo:
    def __init__(self, types):
        self.types = types

class TypeField:
    def __init__(self, access_modifier, name, typ, default_value):
        self.access_modifier = access_modifier
        self.name = name
        self.typ = typ
        self.default_value = default_value

class TypeSym(Sym):
    def __init__(
        self, access_modifier, kind, name, fields, scope, info = None,
        pos = None
    ):
        super().__init__(access_modifier, name, pos = pos)
        self.kind = kind
        self.info = info
        self.fields = fields
        scope.owner = self
        self.scope = scope

    def kind_of(self):
        return str(self.kind)

class Module(Sym):
    def __init__(
        self, access_modifier, name, scope, is_pkg, is_inline = False,
        pos = None
    ):
        super().__init__(access_modifier, name, pos = pos)
        scope.owner = self
        self.scope = scope
        self.is_pkg = is_pkg
        self.is_inline = is_inline

class FunctionArg:
    def __init__(self, name, typ, default_value):
        self.name = name
        self.typ = typ
        self.default_value = default_value

class Function(Sym):
    def __init__(self, access_modifier, name, args, scope, pos = None):
        super().__init__(access_modifier, name, pos = pos)
        self.args = args
        scope.owner = self
        self.scope = scope

    def is_static(self):
        return isinstance(self.parent, TypeSym)

class Scope:
    def __init__(
        self, parent = None, detach_from_parent = False, is_universe = False
    ):
        assert parent == None or isinstance(
            parent, Scope
        ), f"parent is {parent}"
        self.parent = parent
        self.owner = None
        self.syms = []
        self.children = []
        self.detached_from_parent = detach_from_parent
        self.is_universe = is_universe

    def find(self, name):
        for sym in self.syms:
            if sym.name == name:
                return sym
        return None

    def lookup(self, name):
        sc = self
        while True:
            if sym := sc.find(name):
                return sym
            if sc.dont_lookup_scope():
                break
            sc = sc.parent
        return None

    def dont_lookup_scope(self):
        return self.parent == None or self.detached_from_parent

    def add_sym(self, sym):
        if duplicate := self.lookup(sym.name):
            if self.owner:
                errmsg = f"duplicate symbol `{sym.name}` in {self.owner.kind_of()} `{self.owner}`"
            else:
                errmsg = f"duplicate symbol `{sym.name}` in global namespace"
            if duplicate.__class__ == sym.__class__:
                if isinstance(
                    duplicate, Object
                ) and duplicate.level == ObjectLevel.argument:
                    note = f"another argument with the same name was already declared previously"
                else:
                    note = f"another {duplicate.kind_of()} with the same name was defined before"
            else:
                note = f"a {duplicate.kind_of()} with the same name has already been defined"
            raise CompilerError(errmsg, note)
        sym.parent = self.owner
        self.syms.append(sym)
