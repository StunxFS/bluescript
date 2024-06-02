# Copyright (C) 2024 Jose Mendoza. All rights reserved. Use of this
# source code is governed by an MIT license that can be found in the
# LICENSE file.

from io import StringIO
import os, sys, subprocess

VERSION = "0.1.0a"

class CompilerError(Exception):
    pass

def supports_escape_sequences(fd):
    if sys.platform == "nt":
        return False
    if os.getenv("TERM") == "dumb":
        return False
    return os.isatty(fd) > 0

def can_show_color_on_stdout():
    return supports_escape_sequences(1)

def can_show_color_on_stderr():
    return supports_escape_sequences(2)

def format(msg, open, close):
    if not (can_show_color_on_stdout() and can_show_color_on_stderr()):
        return msg
    return f"\x1b[{open}m{msg}\x1b[{close}m"

def bold(msg):
    return format(msg, "1", "22")

def green(msg):
    return format(msg, "32", "39")

def yellow(msg):
    return format(msg, "33", "39")

def blue(msg):
    return format(msg, "34", "39")

def cyan(msg):
    return format(msg, "36", "39")

def white(msg):
    return format(msg, "37", "39")

def red(msg):
    return format(msg, "91", "39")

def commit_hash():
    return execute("git", "log", "-n", "1", '--pretty=format:%h').out

def full_version():
    commit_date = execute("git", "log", "-n", "1", '--pretty=format:%h %as').out
    return f"bsc {VERSION} ({commit_date})"

class ProcessResult:
    def __init__(self, out, err, exit_code):
        self.out = out
        self.err = err
        self.exit_code = exit_code

def execute(*args):
    res = subprocess.run(args, capture_output = True, encoding = 'utf-8')
    stdout = res.stdout.strip() if res.stdout else ""
    stderr = res.stderr.strip() if res.stderr else ""
    return ProcessResult(stdout, stderr, res.returncode)

class Builder:
    def __init__(self):
        self.buf = StringIO()
        self.len_ = 0

    def write(self, txt):
        self.len_ += self.buf.write(txt)

    def writeln(self, txt = ""):
        if len(txt) > 0:
            self.write(txt)
        self.write("\n")

    def write_octal_escape(self, c):
        self.write(chr(92)) # '\'
        self.write(chr(48 + (c >> 6))) # octal digit 2
        self.write(chr(48 + ((c >> 3) & 7))) # octal digit 1
        self.write(chr(48 + (c & 7))) # octal digit 0

    def clear(self):
        self.buf = StringIO()

    def len(self):
        return self.len_

    def __len__(self):
        return len(self.buf)

    def __repr__(self):
        return str(self.buf)

    def __str__(self):
        return self.buf.getvalue()

class CompilerError(Exception):
    pass

def eprint(*s, end = "\n"):
    print(*s, end = end, file = sys.stderr)

def error(msg):
    bg = bold(f'bsc: {red("error:")}')
    eprint(f"{bg} {msg}")
    exit(1)

class Bytestr:
    def __init__(self, buf, len_):
        self.buf = buf
        self.len = len_

def bytestr(s):
    buf = s.encode("utf-8")
    return Bytestr(buf, len(buf))

def index_any(s, chars):
    for i, ss in enumerate(s):
        for c in chars:
            if c == ss:
                return i
    return -1

def escape_nonascii(original):
    sb = Builder()
    for c in original.encode("utf-8"):
        if c < 32 or c > 126:
            # Encode with a 3 digit octal escape code, which has the
            # advantage to be limited/non dependant on what character
            # will follow next, unlike hex escapes:
            sb.write_octal_escape(c)
        else:
            sb.write(chr(c))
    return str(sb)

class OrderedDepMap:
    def __init__(self, keys = [], data = {}):
        self.keys = keys.copy()
        self.data = data.copy()

    def set(self, name, deps):
        if name not in self.data:
            self.keys.append(name)
        self.data[name] = deps

    def add(self, name, deps):
        d = self.get(name)
        for dep in deps:
            if dep not in d:
                d.append(dep)
        self.set(name, d)

    def get(self, name):
        return self.data[name] if name in self.data else []

    def delete(self, name):
        if name not in self.data:
            raise KeyError(f"OrderedDepMap.delete: no such key `{name}`")
        for i, _ in enumerate(self.keys):
            if self.keys[i] == name:
                self.keys.pop(i)
                break
        self.data.pop(name)

    def apply_diff(self, name, deps):
        diff = []
        deps_of_name = self.get(name)
        for dep in deps_of_name:
            if dep not in deps:
                diff.append(dep)
        self.set(name, diff)

    def size(self):
        return len(self.data)

class DepGraphNode:
    def __init__(self, name, deps):
        self.name = name
        self.deps = deps

class NodeNames:
    def __init__(self, is_cycle = {}, names = {}):
        self.is_cycle = is_cycle.copy()
        self.names = names.copy()

    def is_part_of_cycle(self, name, already_seen):
        seen = False
        new_already_seen = already_seen.copy()
        if name in self.is_cycle:
            return self.is_cycle[name], new_already_seen

        if name in already_seen:
            new_already_seen.append(name)
            self.is_cycle[name] = True
            return True, new_already_seen

        new_already_seen.append(name)
        deps = self.names[name] if name in self.names else []
        if len(deps) == 0:
            self.is_cycle[name] = False
            return False, new_already_seen

        for d in deps:
            d_already_seen = new_already_seen.copy()
            seen, d_already_seen = self.is_part_of_cycle(d, d_already_seen)
            if seen:
                new_already_seen = d_already_seen.copy()
                self.is_cycle[name] = True
                return True, new_already_seen
        self.is_cycle[name] = False
        return False, new_already_seen

class DepGraph:
    def __init__(self, acyclic = True, nodes = []):
        self.acyclic = acyclic
        self.nodes = nodes.copy()

    def add(self, name, deps):
        self.nodes.append(DepGraphNode(name, deps))

    def resolve(self):
        node_names = OrderedDepMap()
        node_deps = OrderedDepMap()
        for node in self.nodes:
            node_names.add(node.name, node.deps)
            node_deps.add(node.name, node.deps)
        iterations = 0
        resolved = DepGraph()
        while node_deps.size() != 0:
            iterations += 1
            ready_set = []
            for name in node_deps.keys:
                if len(node_deps.get(name)) == 0:
                    ready_set.append(name)
            if len(ready_set) == 0:
                g = DepGraph()
                g.acyclic = False
                for name in node_deps.keys:
                    g.add(name, node_names.get(name))
                return g
            for name in ready_set:
                node_deps.delete(name)
                resolved.add(name, node_names.get(name))
            for name in node_deps.keys:
                node_deps.apply_diff(name, ready_set)
        return resolved

    def last_node(self):
        return self.nodes[-1]

    def display(self):
        out = []
        for node in self.nodes:
            for dep in node.deps:
                out.append(f" > {node.name} -> {dep}")
        return "\n".join(out)

    def display_cycles(self):
        seen = False
        out = []
        nn = NodeNames()
        for node in self.nodes:
            nn.names[node.name] = node.deps
        for k, _ in nn.names.items():
            cycle_names = []
            if k in nn.is_cycle:
                continue
            seen, cycle_names = nn.is_part_of_cycle(k, cycle_names)
            if seen:
                out.append(" > " + " -> ".join(cycle_names))
        return "\n".join(out)
