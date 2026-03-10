# 通过 Prompt 促使模型调用 OpenViking

当模型替换后运行正常，但 OpenViking 仍未被调用时，可以通过修改 `instance_template` 的步骤 1，明确引导模型使用 OpenViking 的语义搜索与读取能力。

## 推荐修改

在配置文件的 `agent.templates.instance_template` 中，将步骤 1 从：

```
1. As a first step, it might be a good idea to find and read code relevant to the <pr_description>
```

改为更明确的指引，例如：

```
1. As a first step, find and read code relevant to the <pr_description>.
   Use `openviking_search <query>` to search for relevant code semantically, then `openviking_read <uri>` to read file contents.
   If the repo is not yet indexed, run `openviking_add_resource {{working_dir}} --wait` first.
```

## 完整示例片段

```yaml
instance_template: |-
  <uploaded_files>
  {{working_dir}}
  </uploaded_files>
  I've uploaded a python code repository in the directory {{working_dir}}. Consider the following PR description:

  <pr_description>
  {{problem_statement}}
  </pr_description>

  Can you help me implement the necessary changes to the repository so that the requirements specified in the <pr_description> are met?
  ...
  Follow these steps to resolve the issue:
  1. As a first step, find and read code relevant to the <pr_description>.
     Use `openviking_search <query>` to search semantically, then `openviking_read <uri>` to read files.
     If needed, run `openviking_add_resource {{working_dir}} --wait` to index the repo first.
  2. Create a script to reproduce the error: first write the script to a file, then run it with `python <filename.py>` to confirm.
  3. Edit the sourcecode of the repo to resolve the issue
  4. Rerun your reproduce script and confirm that the error is fixed!
  5. Think about edgecases and make sure your fix handles them as well
  ...
```

## 可选： softer 表述

若不希望强制使用 OpenViking，可用建议式语气：

```
1. As a first step, find and read code relevant to the <pr_description>.
   You may use openviking_search and openviking_read for semantic search and file reading.
```

## 前提条件

- OpenViking proxy 已启动，且 `_PROXY_URL` 或相关环境变量配置正确
- 若需语义搜索，需先索引仓库：`openviking_add_resource {{working_dir}} --wait`
