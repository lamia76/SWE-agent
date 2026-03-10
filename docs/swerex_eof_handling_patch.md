# SWE-ReX local.py：捕获 PTY EOF 并返回最后输出

当容器内命令执行完后 PTY 提前关闭时，`pexpect.expect()` 会抛出 `pexpect.exceptions.EOF`，导致 agent 收不到工具输出并异常退出。本补丁在 `swerex/runtime/local.py` 的 `_run_normal` 中捕获 EOF，将已读到的输出作为 observation 返回，使 agent 能继续根据错误信息重试。

## 适用位置

- **包**：`swerex`（SWE-ReX）
- **文件**：`swerex/runtime/local.py`
- **方法**：`_run_normal`（或包含 `self.shell.expect(expect_strings, timeout=action.timeout)` 的同一段逻辑）
- **典型安装路径**：`<venv>/lib/python3.x/site-packages/swerex/runtime/local.py`

## 修改步骤

### 1. 在文件顶部增加 EOF 异常导入

在现有 `import pexpect` 附近增加对 `pexpect.exceptions` 的引用（若已有则跳过）。例如：

```python
import pexpect
# 若需显式引用 EOF：
# from pexpect.exceptions import EOF as PexpectEOF
```

（EOF 可通过 `pexpect.EOF` 或 `pexpect.exceptions.EOF` 引用，见下方。）

### 2. 在 _run_normal 中为 expect 调用加上 try/except

**原逻辑（会抛 EOF）：**

```python
expect_index = self.shell.expect(expect_strings, timeout=action.timeout)
```

**改为：**

```python
try:
    expect_index = self.shell.expect(expect_strings, timeout=action.timeout)
except pexpect.EOF:
    # PTY 在等到 prompt 前就关闭了（例如命令报错后 shell 退出）。
    # 把已读到的输出返回给 agent，避免直接抛异常导致整轮退出。
    before = self.shell.before
    if before is None:
        before = b""
    output = before.decode("utf-8", errors="replace")
    if not output.strip():
        output = "(Session ended unexpectedly; no output captured.)"
    return BashObservation(output=output, exit_code=-1)
```

说明：

- `self.shell.before` 是 expect 匹配前（或 EOF 前）读到的内容，即本次命令的 stdout/stderr。
- 用 `exit_code=-1` 表示“未正常结束”，便于上层按非零处理；若你处 `BashObservation` 不支持 `exit_code`，可只传 `BashObservation(output=output)`，并在文档中说明依赖上层对 output 的解析。

### 3. 确认 BashObservation 的构造函数

若你使用的 `BashObservation` 只有 `output`，没有 `exit_code`，可改为：

```python
return BashObservation(output=output)
```

若支持关键字参数，可保留：

```python
return BashObservation(output=output, exit_code=-1)
```

## 完整补丁示例（仅 _run_normal 中 expect 一段）

在 `_run_normal` 中找到类似代码：

```python
expect_index = self.shell.expect(expect_strings, timeout=action.timeout)
# ... 后续根据 expect_index 解析并 return BashObservation(...)
```

替换为：

```python
try:
    expect_index = self.shell.expect(expect_strings, timeout=action.timeout)
except pexpect.EOF:
    before = self.shell.before
    if before is None:
        before = b""
    output = before.decode("utf-8", errors="replace")
    if not output.strip():
        output = "(Session ended unexpectedly; no output captured.)"
    return BashObservation(output=output, exit_code=-1)
# 原有逻辑：根据 expect_index 解析并 return BashObservation(...)
```

这样，当 str_replace 等工具报错（如 "did not appear verbatim"）后 PTY 关闭，agent 仍能收到这段错误信息并进入下一步，而不是因 EOF 直接退出并触发 autosubmit。

## 验证

1. 对曾出现 EOF 的实例（如 astropy-12907）重跑。
2. 在 str_replace 失败、PTY 关闭的场景下，检查 observation 是否包含工具报错内容。
3. 确认 agent 能根据该 observation 继续执行（例如重试或换用更短的 old_str），且不再因 EOF 直接 submitted(exit_error)。

## 参考

- 错误现象：日志中 `pexpect.exceptions.EOF`，`before (last 100 chars): "... did not appear verbatim ..."`，随后 `Exiting due to unknown error`、`submitted (exit_error)`。
- 原因：命令已结束并输出错误，但 expect 在等 prompt 时读到 EOF，未把 `before` 作为 observation 返回。
