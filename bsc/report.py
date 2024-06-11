# Copyright (C) 2024 Jose Mendoza. All rights reserved. Use of this
# source code is governed by an MIT license that can be found in the
# LICENSE file.

from bsc import utils

errors = 0

def _format(pos, kind, kindc, msg):
    return "{} {}".format(
        utils.bold(
            "{}:{}:{}: {}".format(pos.file, pos.line, pos.column, kindc(kind))
        ), msg
    )

def error(msg, pos):
    global errors
    utils.eprint(_format(pos, "error:", utils.red, msg))
    errors += 1

def warn(msg, pos):
    utils.eprint(_format(pos, "warning:", utils.yellow, msg))

def notes(notes):
    for i, note in enumerate(notes):
        _char = "└" if i == len(notes) - 1 else "├"
        utils.eprint(utils.bold(utils.cyan(f"   {_char} note: ")) + note)

def error_from_ce(ce, pos):
    error(ce.args[0], pos)
    notes(ce.args[1:])

def warn_from_ce(ce, pos):
    warn(ce.args[0], pos)
    notes(ce.args[1:])
