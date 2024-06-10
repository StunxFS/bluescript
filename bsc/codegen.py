# Copyright (C) 2024 Jose Mendoza. All rights reserved. Use of this
# source code is governed by an MIT license that can be found in the
# LICENSE file.

from bsc import AST
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
        if isinstance(decl, AST.ModDecl):
            if decl.is_inline:
                self.gen_inline_mod(decl)
        elif isinstance(decl, AST.EnumDecl):
            self.gen_enum_decl(decl)
        elif isinstance(decl, AST.FnDecl):
            self.gen_fn_decl(decl)

    def gen_enum_decl(self, decl):
        fields = []
        for i, f in enumerate(decl.fields):
            fields.append(LuaTableField(f.name, str(i)))
        self.decls.append(LuaTable(decl.sym.mod_qualname("."), fields))

    def gen_inline_mod(self, decl):
        old_decls = self.decls
        self.decls = []
        self.gen_decls(decl.decls)
        old_decls.append(LuaModule(decl.sym.mod_qualname("."), self.decls))
        self.decls = old_decls

    def gen_fn_decl(self, decl):
        args = []
        for arg in decl.args:
            args.append(LuaIdent(arg.name))
        luafn = LuaFunction(decl.sym.mod_qualname("."), args)
        self.decls.append(luafn)
