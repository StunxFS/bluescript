# Copyright (C) 2024 Jose Mendoza. All rights reserved. Use of this
# source code is governed by an MIT license that can be found in the
# LICENSE file.

import os
from bsc import utils
from bsc.codegen.lua_ast import *
from bsc.utils import BSC_OUT_DIR

class LuaRender:
    def __init__(self, ctx, modules):
        self.ctx = ctx

        self.modules = modules
        self.cur_module = None

        self.indent = 0
        self.empty_line = True
        self.lua_file = utils.Builder()

    def render_modules(self):
        if not os.path.exists(BSC_OUT_DIR):
            os.mkdir(BSC_OUT_DIR)
        for module in self.modules:
            self.cur_module = module
            self.render_module(module)

    def render_module(self, module):
        self.writeln(
            f"-- Autogenerated by the BlueScript compiler - {utils.full_version()}"
        )
        self.writeln(
            "-- WARNING: DO NOT MODIFY MANUALLY! YOUR CHANGES WILL BE OVERWRITTEN --\n"
        )

        self.render_stmts(module.block.stmts)

        with open(f"{BSC_OUT_DIR}/{module.name}.lua", "w") as f:
            f.write(str(self.lua_file))
        self.lua_file.clear()

    def render_stmts(self, stmts):
        for stmt in stmts:
            self.render_stmt(stmt)

    def render_stmt(self, stmt):
        if isinstance(stmt, LuaComment):
            self.writeln(f"-- {stmt.comment}")
        elif isinstance(stmt, LuaFunction):
            self.render_fn_stmt(stmt)
        elif isinstance(stmt, LuaTable):
            self.render_table(stmt)
        elif isinstance(stmt, LuaAssignment):
            self.render_assign_stmt(stmt)
        elif isinstance(stmt, LuaWhile):
            self.write("while ")
            self.render_expr(stmt.cond)
            self.writeln(" do")
            self.indent += 1
            self.render_stmts(stmt.stmts)
            self.indent -= 1
            self.writeln("end")
        elif isinstance(stmt, LuaRepeat):
            self.writeln("repeat")
            self.indent += 1
            self.render_stmts(stmt.stmts)
            self.indent -= 1
            self.write("until ")
            self.render_expr(stmt.cond)
            self.writeln()
        elif isinstance(stmt, LuaIf):
            for i, branch in enumerate(stmt.branches):
                if branch.is_else:
                    self.writeln("else")
                else:
                    self.write("if " if i == 0 else "elseif ")
                    self.render_expr(branch.cond)
                self.indent += 1
                self.render_stmts(branch.stmts)
                self.indent -= 1
            self.writeln("end")
        elif isinstance(stmt, LuaBlock):
            self.writeln("do")
            self.indent += 1
            self.render_stmts(stmt.stmts)
            self.indent -= 1
            self.writeln("end\n")
        elif isinstance(stmt, LuaReturn):
            self.write("return")
            if stmt.expr != None:
                self.write(" ")
                self.render_expr(stmt.expr)
            self.writeln()
        else:
            self.render_expr(stmt) # support for using expressions as statements

    def render_fn_stmt(self, stmt):
        if not stmt.is_static:
            self.write("local ")
        self.write(f"function {stmt.name}(")
        for i, arg in enumerate(stmt.args):
            self.write(arg.name)
            if i < len(stmt.args) - 1:
                self.write(", ")
        self.writeln(")")
        self.indent += 1
        self.render_stmts(stmt.block.stmts)
        self.indent -= 1
        self.writeln("end\n")

    def render_assign_stmt(self, stmt):
        if stmt.is_local: self.write("local ")
        for i, left in enumerate(stmt.lefts):
            self.render_expr(left)
            if i < len(stmt.lefts) - 1:
                self.write(", ")
        if len(stmt.rights) > 0:
            self.write(" = ")
            for i, right in enumerate(stmt.rights):
                self.render_expr(right)
                if i < len(stmt.rights) - 1:
                    self.write(", ")
        self.writeln()

    def render_expr(self, expr):
        if isinstance(expr, LuaParenExpr):
            self.write("(")
            self.render_expr(expr.expr)
            self.write(")")
        elif isinstance(expr, LuaTable):
            if len(expr.fields) == 0:
                self.write("{}")
                return
            self.writeln("{")
            self.indent += 1
            for i, field in enumerate(expr.fields):
                if field.key != None:
                    needs_brackets = not isinstance(field.key, LuaIdent)
                    if needs_brackets:
                        self.write("[")
                    self.render_expr(field.key)
                    if needs_brackets:
                        self.write("]")
                    self.write(" = ")
                self.render_expr(field.value)
                if i < len(expr.fields) - 1:
                    self.writeln(",")
                else:
                    self.writeln()
            self.indent -= 1
            self.write("}")
        elif isinstance(expr, LuaBinaryExpr):
            self.write("(")
            self.render_expr(expr.left)
            self.write(f" {expr.op} ")
            self.render_expr(expr.right)
            self.write(")")
        elif isinstance(expr, LuaUnaryExpr):
            self.write("(")
            self.write(expr.op)
            self.render_expr(expr.right)
            self.write(")")
        elif isinstance(expr, LuaCallExpr):
            if expr.left != None:
                self.render_expr(expr.left)
                if expr.is_method:
                    self.write(":")
                else:
                    self.write(".")
            if len(expr.name) > 0:
                self.write(expr.name)
            self.write("(")
            for i, arg in enumerate(expr.args):
                self.render_expr(arg)
                if i < len(expr.args) - 1:
                    self.write(", ")
            self.write(")")
        elif isinstance(expr, LuaSelector):
            self.render_expr(expr.left)
            self.write(f".{expr.name}")
        elif isinstance(expr, LuaIdent):
            self.write(expr.name)
        elif isinstance(expr, LuaStringLit):
            self.write(f'"{expr.value}"')
        elif isinstance(expr, LuaNumberLit):
            if expr.value.startswith("0b") or expr.value.startswith("0o"):
                self.write(hex(int(expr.value, 0)))
            else:
                self.write(expr.value)
        elif isinstance(expr, LuaBooleanLit):
            self.write("true" if expr.value else "false")
        elif isinstance(expr, LuaNil):
            self.write("nil")

    ## Utils

    def write(self, s):
        if self.indent > 0 and self.empty_line:
            self.lua_file.write("\t" * self.indent)
        self.lua_file.write(s)
        self.empty_line = False

    def writeln(self, s = ""):
        if self.indent > 0 and self.empty_line:
            self.lua_file.write("\t" * self.indent)
        self.lua_file.writeln(s)
        self.empty_line = True