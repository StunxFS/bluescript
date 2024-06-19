# Copyright (C) 2024 Jose Mendoza. All rights reserved. Use of this
# source code is governed by an MIT license that can be found in the
# LICENSE file.

from bsc.AST import *
from bsc.lua_ast import *
from bsc.lua_ast.render import LuaRender

class Codegen:
    def __init__(self, ctx):
        self.ctx = ctx
        self.modules = []
        self.cur_module = None
        self.decls = []

    def gen_files(self, source_files):
        for file in source_files:
            self.gen_file(file)
        render = LuaRender(self.ctx, self.modules)
        render.render_modules()

    def gen_file(self, file):
        self.cur_module = LuaModule(file.mod_sym.name)
        self.gen_decls(file.decls)
        self.cur_module.decls = self.decls
        self.modules.append(self.cur_module)
        self.decls = []

    def gen_decls(self, decls):
        for decl in decls:
            self.gen_decl(decl)

    def gen_decl(self, decl):
        if isinstance(decl, ModDecl):
            self.gen_mod(decl)
        elif isinstance(decl, EnumDecl):
            self.gen_enum_decl(decl)
        elif isinstance(decl, FnDecl):
            self.gen_fn_decl(decl)

    def gen_mod(self, decl):
        if decl.is_inline:
            old_decls = self.decls
            self.decls = []
            self.gen_decls(decl.decls)
            old_decls.append(
                LuaModule(decl.sym.codegen_qualname(), self.decls, True)
            )
            self.decls = old_decls
        else:
            self.decls.append(
                LuaModule(
                    decl.sym.codegen_qualname(), [], False,
                    lua_filename = decl.name
                )
            )

    def gen_enum_decl(self, decl):
        fields = []
        for i, f in enumerate(decl.fields):
            fields.append(LuaTableField(f.name, str(i)))
        self.decls.append(LuaTable(decl.sym.codegen_qualname(), fields))
        self.gen_decls(decl.decls)

    def gen_fn_decl(self, decl):
        if not decl.has_body: return
        args = []
        for arg in decl.args:
            args.append(LuaIdent(arg.name))
        luafn = LuaFunction(decl.sym.codegen_qualname(), args)
        for arg in decl.args:
            if arg.default_value != None:
                left = LuaIdent(arg.name)
                luafn.add_stmt(
                    LuaAssignment([left], [
                        LuaBinaryExpr(
                            left, "or", self.gen_expr(arg.default_value)
                        )
                    ], False)
                )
        self.decls.append(luafn)

    def gen_expr(self, expr):
        if isinstance(expr, BinaryExpr):
            return LuaBinaryExpr(
                self.gen_expr(expr.left), expr.op.to_lua_op(),
                self.gen_expr(expr.right)
            )
        elif isinstance(expr, UnaryExpr):
            return LuaUnaryExpr(expr.op.to_lua_op(), self.gen_expr(expr.right))
        elif isinstance(expr, NumberLiteral):
            return LuaNumberLit(expr.value)
        elif isinstance(expr, BoolLiteral):
            return LuaBooleanLit("true" if expr.value else "false")
        elif isinstance(expr, NilLiteral):
            return LuaNil()
