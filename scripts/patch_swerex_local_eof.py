#!/usr/bin/env python3
"""
在 swerex/runtime/local.py 的 _run_normal 中为 expect 调用添加 EOF 捕获，
使 PTY 提前关闭时返回已读到的输出而非抛出异常。

用法:
  python scripts/patch_swerex_local_eof.py [path_to_swerex_runtime_local_py]
  不传参数时自动查找 site-packages 下的 swerex/runtime/local.py。
"""
from __future__ import annotations

import sys
from pathlib import Path


# 可能出现的缩进（4 或 8 个空格，依 _run_normal 所在缩进层级而定）
OLD_CANDIDATES = [
    "        expect_index = self.shell.expect(expect_strings, timeout=action.timeout)",
    "    expect_index = self.shell.expect(expect_strings, timeout=action.timeout)",
]

# 与上面第一个 OLD 对应的 NEW（缩进 8 空格）
NEW_8 = """        try:
            expect_index = self.shell.expect(expect_strings, timeout=action.timeout)
        except pexpect.EOF:
            before = self.shell.before
            if before is None:
                before = b""
            output = before.decode("utf-8", errors="replace")
            if not output.strip():
                output = "(Session ended unexpectedly; no output captured.)"
            return BashObservation(output=output, exit_code=-1)"""
# 缩进 4 空格版本
NEW_4 = """    try:
        expect_index = self.shell.expect(expect_strings, timeout=action.timeout)
    except pexpect.EOF:
        before = self.shell.before
        if before is None:
            before = b""
        output = before.decode("utf-8", errors="replace")
        if not output.strip():
            output = "(Session ended unexpectedly; no output captured.)"
        return BashObservation(output=output, exit_code=-1)"""


def find_local_py() -> Path | None:
    for p in sys.path:
        p = Path(p)
        if not p.is_dir():
            continue
        candidate = p / "swerex" / "runtime" / "local.py"
        if candidate.is_file():
            return candidate
    return None


def main() -> int:
    if len(sys.argv) > 1:
        target = Path(sys.argv[1])
    else:
        target = find_local_py()
    if not target or not target.is_file():
        print("Could not find swerex/runtime/local.py. Pass path as first argument.", file=sys.stderr)
        return 1
    text = target.read_text(encoding="utf-8")
    if NEW.strip() in text:
        print(f"Already patched: {target}")
        return 0
    if OLD not in text:
        print(f"Target string not found in {target}. Is the file from SWE-ReX?", file=sys.stderr)
        return 1
    text = text.replace(OLD, NEW, 1)
    target.write_text(text, encoding="utf-8")
    print(f"Patched: {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
