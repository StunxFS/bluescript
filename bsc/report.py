# Copyright (C) 2024 Jose Mendoza. All rights reserved. Use of this
# source code is governed by an MIT license that can be found in the
# LICENSE file.

from bsc import utils

def _format(pos, kind, kindc, msg):
    return "{}:{}:{}: {}".format(
        pos.file, pos.line, pos.column,
        kindc(kind) + msg
    )

def error(msg, pos):
    utils.eprint(_format(pos, "error: ", utils.red, msg))

def warn(msg, pos):
    utils.eprint(_format(pos, "warning: ", utils.yellow, msg))
