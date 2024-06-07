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

    def gen_files(self, source_files):
        for file in source_files:
            self.gen_file(file)
        render = LuaRender(self.ctx, self.modules)
        render.render_modules()

    def gen_file(self, file):
        self.cur_module = LuaModule(file.mod_sym.name)
        self.gen_decls(file.decls)
        self.modules.append(self.cur_module)

    def gen_decls(self, decls):
        for decl in decls:
            self.gen_decl(decl)

    def gen_decl(self, decl):
        if isinstance(decl, AST.FnDecl):
            self.gen_fn_decl(decl)

    def gen_fn_decl(self, decl):
        luafn = LuaFunction(decl.name, [])
        self.cur_module.decls.append(luafn)
