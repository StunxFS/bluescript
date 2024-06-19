# Copyright (C) 2024 Jose Mendoza. All rights reserved. Use of this
# source code is governed by an MIT license that can be found in the
# LICENSE file.

import os, sys, glob

BSC_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "bsc"
)
sys.path.append(os.path.dirname(BSC_DIR))

from bsc import utils

ok, fail = 0, 0

bs_files = glob.glob("tests/invalid_code/*.bs")
for i, bs_file in enumerate(bs_files):
    out_file = bs_file[:-3] + ".out"
    print(f"  [{i+1}/{len(bs_files)}] {utils.bold(bs_file)}", end = "")
    res = utils.execute(f"python3", "bsc", bs_file)
    if res.exit_code == 0:
        print(utils.bold(utils.red(" -> FAILED")))
        fail += 1
    else:
        out_content = open(out_file).read().strip()
        if out_content == res.err:
            print(utils.bold(utils.green(" -> PASSED")))
            ok += 1
        else:
            print(utils.bold(utils.red(" -> FAILED")))
            print("Expected:")
            print(out_content)
            print("\nGot:")
            print(res.err)
            fail += 1

passed = utils.bold(utils.green(f'{ok} PASSED'))
failed = utils.bold(utils.red(f'{fail} FAILED'))
print(f"{utils.bold('Summary:')} {passed}, {failed}")
