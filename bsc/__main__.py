# Copyright (C) 2024 Jose Mendoza. All rights reserved. Use of this
# source code is governed by an MIT license that can be found in the
# LICENSE file.

import os, sys

BSC_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(BSC_DIR))

from bsc import Context

ctx = Context()
ctx.parse_args()
ctx.compile()
