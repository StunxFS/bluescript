# Copyright (C) 2024 Jose Mendoza. All rights reserved. Use of this
# source code is governed by an MIT license that can be found in the
# LICENSE file.

from bsc import utils

errors = 0

def _format(pos, kind, kindc, msg):
    return "{} {}".format(
        utils.bold("{}:{}:{}: {}".format(pos.file, pos.line, pos.column, kindc(kind))),
        msg
    )

def error(msg, pos):
    global errors
    utils.eprint(_format(pos, "error: ", utils.red, msg))
    errors += 1

def warn(msg, pos):
    utils.eprint(_format(pos, "warning: ", utils.yellow, msg))
