# Copyright (C) 2024 Jose Mendoza. All rights reserved. Use of this
# source code is governed by an MIT license that can be found in the
# LICENSE file.

from bsc.sym import *
from bsc.astgen.ast import *
from bsc.codegen.lua_ast import *
from bsc.codegen.lua_render import LuaRender
from bsc.utils import BSC_OUT_DIR

class Codegen:
    def __init__(self, ctx):
        self.ctx = ctx
        self.modules = []

        self.cur_file = None
        self.cur_sym = None
        self.sym_stack = []

        self.cur_module = None
        self.cur_fn = None
        self.cur_block = None

    def switch_cur_sym(self, new_cur_sym = None):
        if new_cur_sym == None:
            self.cur_sym = self.sym_stack.pop()
        else:
            self.sym_stack.append(self.cur_sym)
            self.cur_sym = new_cur_sym

    def gen_files(self, source_files):
        for file in source_files:
            self.gen_file(file)
        render = LuaRender(self.ctx, self.modules)
        render.render_modules()

    def gen_file(self, file):
        self.cur_file = file
        self.switch_cur_sym(self.cur_file.mod_sym)
        self.cur_module = LuaModule(file.mod_sym.name)
        self.cur_block = self.cur_module.block
        self.gen_decls(file.decls)

        if self.cur_file.mod_sym.is_pkg and not self.ctx.prefs.is_library:
            self.cur_block.add_comment("the entry point")
            self.cur_block.add_stmt(LuaCallExpr("main"))
        else:
            self.export_public_symbols(file.mod_sym, True)

        self.cur_module.stmts = self.cur_block
        self.modules.append(self.cur_module)
        self.cur_block = LuaBlock()
        self.switch_cur_sym()

    def gen_decls(self, decls):
        for decl in decls:
            self.gen_decl(decl)

    def gen_decl(self, decl):
        if isinstance(decl, ModDecl):
            self.gen_mod_decl(decl)
        elif isinstance(decl, ConstDecl):
            self.gen_const_decl(decl)
        elif isinstance(decl, EnumDecl):
            self.gen_enum_decl(decl)
        elif isinstance(decl, FnDecl):
            self.gen_fn_decl(decl)

    def gen_mod_decl(self, decl):
        if decl.is_inline:
            self.switch_cur_sym(decl.sym)
            self.cur_block.add_comment(f"inline module `{decl.sym.qualname()}`")
            self.cur_block.add_stmt(LuaAssignment([LuaIdent(decl.name)], []))
            old_block = self.cur_block

            self.cur_block = LuaBlock()
            self.gen_decls(decl.decls)
            self.export_public_symbols(decl.sym)

            mod_decls = self.cur_block
            self.cur_block = old_block
            self.cur_block.add_stmt(mod_decls)
            self.switch_cur_sym()
        else:
            self.cur_block.add_comment(f"extern module `{decl.sym.qualname()}`")
            self.cur_block.add_stmt(
                LuaAssignment([LuaIdent(decl.sym.name)], [
                    LuaCallExpr(
                        "require", [LuaStringLit(f"{BSC_OUT_DIR}.{decl.name}")]
                    )
                ])
            )

    def gen_const_decl(self, decl):
        name = decl.name if decl.is_local else decl.sym.name
        lua_assign = LuaAssignment([LuaIdent(name)], [self.gen_expr(decl.expr)])
        self.cur_block.add_stmt(lua_assign)

    def gen_enum_decl(self, decl):
        self.cur_block.add_stmt(LuaAssignment([LuaIdent(decl.sym.name)], []))
        old_block = self.cur_block
        self.cur_block = LuaBlock()
        for i, f in enumerate(decl.fields):
            self.cur_block.add_stmt(
                LuaAssignment([LuaIdent(f.name)], [LuaNumberLit(str(i))])
            )
        self.switch_cur_sym(decl.sym)
        self.gen_decls(decl.decls)
        self.export_public_symbols(
            decl.sym, custom_fields = [f.name for f in decl.fields]
        )
        self.switch_cur_sym()
        old_block.add_stmt(self.cur_block)
        self.cur_block = old_block

    def gen_fn_decl(self, decl):
        if not decl.has_body: return
        old_block = self.cur_block
        args = []
        if decl.is_method:
            args.append(LuaIdent("self"))
        for arg in decl.args:
            args.append(LuaIdent(arg.name))
        luafn = LuaFunction(args, is_static = decl.sym.is_static())
        for arg in decl.args:
            if arg.default_value != None:
                left = LuaIdent(arg.name)
                luafn.block.add_stmt(
                    LuaAssignment([left], [
                        LuaBinaryExpr(
                            left, "or", self.gen_expr(arg.default_value)
                        )
                    ], False)
                )
        self.cur_fn = luafn
        self.cur_block = luafn.block
        self.gen_stmts(decl.stmts)
        self.cur_fn = None
        self.cur_block = old_block
        self.cur_block.add_stmt(
            LuaAssignment([LuaIdent(decl.sym.name)], [luafn])
        )

    ## == Statements ============================================

    def gen_stmts(self, stmts):
        for stmt in stmts:
            self.gen_stmt(stmt)

    def gen_stmt(self, stmt):
        if isinstance(stmt, ExprStmt):
            self.gen_expr(stmt.expr)
        elif isinstance(stmt, ConstDecl):
            self.gen_const_decl(stmt)
        elif isinstance(stmt, WhileStmt):
            while_stmt = LuaWhile(self.gen_expr(stmt.cond))
            old_block = self.cur_block
            self.cur_block = LuaBlock()
            self.gen_stmts(stmt.stmts)
            self.cur_block = old_block
            self.cur_block.add_stmt(while_stmt)

    ## == Expressions ===========================================

    def gen_expr(self, expr):
        if isinstance(expr, NilLiteral):
            return LuaNil()
        elif isinstance(expr, BoolLiteral):
            return LuaBooleanLit("true" if expr.value else "false")
        elif isinstance(expr, NumberLiteral):
            return LuaNumberLit(expr.value, expr.typ == self.ctx.float_type)
        elif isinstance(expr, UnaryExpr):
            right = self.gen_expr(expr.right)
            if isinstance(right, LuaBooleanLit) and expr.op == UnaryOp.bang:
                return LuaBooleanLit(str((not right.value).lower()))
            elif isinstance(right, LuaNumberLit) and expr.op == UnaryOp.bit_not:
                return LuaNumberLit(str(~int(right.value)))
            return LuaUnaryExpr(expr.op.to_lua_op(), right)
        elif isinstance(expr, BinaryExpr):
            op = expr.op.to_lua_op()
            left = self.gen_expr(expr.left)
            right = self.gen_expr(expr.right)
            if isinstance(left,
                          LuaNumberLit) and isinstance(right, LuaNumberLit):
                leftn = float(left.value) if left.is_float else int(left.value)
                rightn = float(right.value
                               ) if left.is_float else int(right.value)
                if left.is_float and op == "/": op = "//"
                match expr.op:
                    case BinaryOp.plus:
                        return LuaNumberLit(str(leftn + rightn))
                    case BinaryOp.minus:
                        return LuaNumberLit(str(leftn - rightn))
                    case BinaryOp.mul:
                        return LuaNumberLit(str(leftn * rightn))
                    case BinaryOp.div:
                        return LuaNumberLit(
                            str(
                                leftn / rightn if left.is_float else leftn //
                                rightn
                            ), left.is_float
                        )
                    case BinaryOp.mod:
                        return LuaNumberLit(str(leftn % rightn))
                    case BinaryOp.bit_and:
                        return LuaNumberLit(str(leftn & rightn))
                    case BinaryOp.bit_or:
                        return LuaNumberLit(str(leftn | rightn))
                    case BinaryOp.bit_xor:
                        return LuaNumberLit(str(leftn ^ rightn))
                    case BinaryOp.lshift:
                        return LuaNumberLit(str(leftn << rightn))
                    case BinaryOp.rshift:
                        return LuaNumberLit(str(leftn >> rightn))
                    case BinaryOp.eq:
                        return LuaBooleanLit(leftn == rightn)
                    case BinaryOp.neq:
                        return LuaBooleanLit(leftn != rightn)
                    case BinaryOp.lt:
                        return LuaBooleanLit(leftn < rightn)
                    case BinaryOp.gt:
                        return LuaBooleanLit(leftn > rightn)
                    case BinaryOp.le:
                        return LuaBooleanLit(leftn <= rightn)
                    case BinaryOp.ge:
                        return LuaBooleanLit(leftn >= rightn)
            elif isinstance(left, LuaBooleanLit
                            ) and isinstance(right, LuaBooleanLit):
                leftb = left.value
                rightb = right.value
                match expr.op:
                    case BinaryOp.logical_and:
                        return LuaBooleanLit(leftb and rightb)
                    case BinaryOp.logical_or:
                        return LuaBooleanLit(leftb or rightb)
            return LuaBinaryExpr(left, op, right)
        elif isinstance(expr, Ident):
            if isinstance(
                expr.sym, Object
            ) and expr.sym.level != ObjectLevel.static:
                return LuaIdent(expr.name)
            if expr.sym != None: return LuaIdent(expr.sym.name)
            return LuaIdent(expr.name)
        elif isinstance(expr, PathExpr):
            if expr.left_sym == self.cur_sym:
                return LuaIdent(expr.name)
            return LuaSelector(self.gen_expr(expr.left), expr.name)
        elif isinstance(expr, BlockExpr):
            old_block = self.cur_block
            block = LuaBlock()
            self.cur_block = block
            self.gen_stmts(expr.stmts)
            self.cur_block = old_block
            self.cur_block.add_stmt(block)
            return LuaSkip()
        elif isinstance(expr, ReturnExpr):
            if expr.expr == None:
                ret_expr = None
            else:
                ret_expr = self.gen_expr(expr.expr)
            self.cur_block.add_stmt(LuaReturn(ret_expr))
            return LuaSkip()

    def export_public_symbols(
        self, decl_sym, return_table = False, custom_fields = []
    ):
        exported_fields = []

        for custom_field in custom_fields:
            exported_fields.append(
                LuaTableField(LuaIdent(custom_field), LuaIdent(custom_field))
            )

        for sym in decl_sym.scope.syms:
            if sym.access_modifier.is_public():
                exported_fields.append(
                    LuaTableField(LuaIdent(sym.name), LuaIdent(sym.name))
                )

        if return_table:
            self.cur_block.add_stmt(LuaReturn(LuaTable(exported_fields)))
        else:
            self.cur_block.add_stmt(
                LuaAssignment([LuaIdent(decl_sym.name)],
                              [LuaTable(exported_fields)], False)
            )
