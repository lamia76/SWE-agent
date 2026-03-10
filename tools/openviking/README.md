# OpenViking Tool Bundle for SWE-agent

OpenViking是一个Agent原生的上下文数据库，为SWE-agent提供语义搜索和分层上下文加载能力。此工具包通过8个Python CLI工具将OpenViking集成到SWE-agent的工作流中。

## 功能特性

OpenViking的核心能力：
- **语义搜索**：基于向量的智能搜索，而非简单的关键词匹配
- **分层加载**：L0摘要、L1概览、L2完整内容，渐进式加载上下文
- **目录递归**：支持模式匹配（glob）和目录浏览（ls）

此工具包为SWE-agent提供的8个工具：
1. `ov_index_repo` - 索引仓库
2. `ov_wait` - 等待处理完成
3. `ov_find` - 语义搜索
4. `ov_abstract` - 获取极简摘要（L0）
5. `ov_overview` - 获取结构化概览（L1）
6. `ov_read` - 读取完整内容（L2）
7. `ov_ls` - 列出目录内容
8. `ov_glob` - 按模式查找文件

## 安装

### 自动安装

运行工具包提供的安装脚本：

```bash
cd tools/openviking
./install.sh
```

安装脚本会：
- 检查Python和pip环境
- 安装OpenViking SDK
- 创建默认数据目录（可选）

### 手动安装

```bash
pip install openviking
```

## 配置

### 环境变量

- `OPENVIKING_DATA_DIR`：OpenViking数据目录路径（默认：`./.openviking`）
- `OPENVIKING_CONFIG_FILE`：OpenViking配置文件路径（可选）

### 配置文件

如果需要自定义配置，可以创建一个JSON配置文件并通过`OPENVIKING_CONFIG_FILE`环境变量指定：

```bash
export OPENVIKING_CONFIG_FILE=/path/to/ov.conf
```

## 工具使用指南

### 工作流概览

推荐的上下文装载策略（分层加载）：

1. **定位优先**：使用`ov_find`查找相关文件/目录
2. **分层加深**：对候选URI先用`ov_abstract`，再用`ov_overview`，最后用`ov_read`
3. **克制读取**：`ov_read`必须带`--max_chars`，且只对1-2个最相关文件调用
4. **目录导航**：使用`ov_ls/ov_glob`在候选目录下收敛

### 快速开始

```bash
# 1. 索引当前仓库
ov_index_repo .

# 2. 等待处理完成（首次必须）
ov_wait

# 3. 语义搜索
ov_find "authentication error"

# 4. 查看最相关结果的摘要
ov_abstract viking://src/auth/login.py

# 5. 如果相关，查看结构化概览
ov_overview viking://src/auth/login.py

# 6. 读取完整内容
ov_read viking://src/auth/login.py --max-chars 16000
```

### 工具详解

#### ov_index_repo

索引仓库到OpenViking数据库，用于语义搜索。

**用法：**
```bash
ov_index_repo [<repo_path>]
```

**参数：**
- `repo_path`：仓库目录路径（默认为当前目录）

**输出：**
```json
{
  "root_uri": "viking://...",
  "indexed_path": "/path/to/repo",
  "status": "indexed"
}
```

#### ov_wait

等待OpenViking完成所有后台处理操作。

**用法：**
```bash
ov_wait [--timeout TIMEOUT]
```

**参数：**
- `--timeout`：最大等待时间（秒，默认300）

**输出：**
```json
{
  "status": "ready",
  "message": "All operations completed successfully"
}
```

#### ov_find

在索引的仓库中进行语义搜索。

**用法：**
```bash
ov_find <query> [-k K] [--score-threshold THRESHOLD]
```

**参数：**
- `query`：搜索查询（必需）
- `-k`：返回结果数量（默认10）
- `--score-threshold`：最小相关性分数（0.0-1.0，可选）

**示例：**
```bash
ov_find "test for user login" -k 5
ov_find "database connection pool" --score-threshold 0.3
```

**输出：**
```json
{
  "query": "user login",
  "results": [
    {"uri": "viking://src/auth/login.py", "score": 0.87},
    {"uri": "viking://tests/test_login.py", "score": 0.76}
  ]
}
```

#### ov_abstract

获取极简摘要（L0层级），用于快速判断相关性。

**用法：**
```bash
ov_abstract <uri> [--max-chars MAX_CHARS]
```

**参数：**
- `uri`：OpenViking URI（必需）
- `--max-chars`：最大返回字符数（默认1000）

**输出：**
```json
{
  "uri": "viking://src/auth/login.py",
  "abstract": "...",
  "truncated": false,
  "max_chars": 1000
}
```

#### ov_overview

获取结构化概览（L1层级），提供更详细的理解。

**用法：**
```bash
ov_overview <uri> [--max-chars MAX_CHARS]
```

**参数：**
- `uri`：OpenViking URI（必需）
- `--max-chars`：最大返回字符数（默认8192）

**输出：**
```json
{
  "uri": "viking://src/auth/login.py",
  "overview": "...",
  "truncated": true,
  "max_chars": 8192
}
```

#### ov_read

读取文件的完整内容（L2层级），最深层的加载方式，应谨慎使用。

**用法：**
```bash
ov_read <uri> [--max-chars MAX_CHARS]
```

**参数：**
- `uri`：OpenViking URI（必需）
- `--max-chars`：最大返回字符数（默认16000）

**输出：**
```json
{
  "uri": "viking://src/auth/login.py",
  "content": "...",
  "truncated": true,
  "max_chars": 16000
}
```

#### ov_ls

列出目录内容。

**用法：**
```bash
ov_ls [uri] [--simple] [--recursive]
```

**参数：**
- `uri`：OpenViking URI（默认viking://）
- `--simple`：仅返回相对路径
- `--recursive`：递归列出所有子目录

**输出：**
```json
{
  "uri": "viking://src/",
  "entries": [...]
}
```

#### ov_glob

按模式查找文件。

**用法：**
```bash
ov_glob <pattern> [--uri URI]
```

**参数：**
- `pattern`：Glob匹配模式（必需，如`**/*.py`）
- `--uri`：搜索范围URI（默认viking://）

**示例：**
```bash
ov_glob "**/test_*.py"
ov_glob "**/*.md" --uri viking://docs/
```

**输出：**
```json
{
  "pattern": "**/test_*.py",
  "uri": "viking://",
  "matches": [...]
}
```

## 运行时工作流示例

### 处理一个新的issue

```bash
# 每个任务开始时
ov_index_repo .
ov_wait  # 首次或大变更必须

# 遇到报错/失败测试后
ov_find "error message" -k 10

# 对top3-5个结果
ov_abstract viking://file1.py
ov_abstract viking://file2.py
ov_abstract viking://file3.py

# 选出top1-2个
ov_overview viking://file1.py

# 必要时
ov_read viking://file1.py --max-chars 16000

# 用SWE-agent原生工具edit/patch/run tests

# 如果改动很大且find命中变差，可选
ov_index_repo .  # 重新索引
```

## 使用约定（上下文装载策略）

为了保证OpenViking的优势充分发挥，建议遵循以下使用约定：

1. **定位优先**：需要找代码/配置/测试入口时，先`ov_find`，不要直接遍历或全量`ov_read`
2. **分层加深**：对候选URI先`ov_abstract`，再`ov_overview`，最后才`ov_read`
3. **读要克制**：`ov_read`必须带`--max_chars`，并尽量只对1-2个最相关文件调用
4. **需要目录递归时**：用`ov_ls`/`ov_glob`在候选目录下收敛

这就足够把OpenViking的优势（检索+分层加载+目录递归）发挥出来，而不用SWE-agent做任何"自动上下文管理"。

## 故障排除

### 错误格式

所有工具的错误输出都采用统一的JSON格式：

```json
{
  "error": {
    "type": "OpenVikingError",
    "message": "...",
    "hint": "..."
  }
}
```

### 常见问题

**问题： `openviking`模块未找到**

解决方案：运行`pip install openviking`或执行`./install.sh`

**问题： 索引后搜索结果为空**

解决方案：运行`ov_wait`确保处理完成，或重新索引

**问题： 文件读取内容被截断**

解决方案：增加`--max-chars`参数的值，或使用`ov_find`定位特定区域

## 架构设计

此工具包遵循"低侵入/解耦"的设计原则：
- 通过一个独立的tool bundle（`tools/openviking/`）暴露工具
- 所有OpenViking的接入细节集中在`lib/ov_common.py`中
- 未来如果需要切换到HTTP端点，只需修改`ov_common.py`，上层命令签名不变

## 开发和调试

### 启用调试日志

```bash
export OV_DEBUG=1
ov_find "your query"
```

### 查看数据目录

默认数据目录位于`./.openviking/`，可以通过`OPENVIKING_DATA_DIR`环境变量修改。

### 状态文件

根URI存储在仓库根目录的`.openviking_root_uri`文件中。

## 许可证

本工具包遵循Apache-2.0许可证。

OpenViking SDK的许可请参考：https://github.com/volcengine/OpenViking
