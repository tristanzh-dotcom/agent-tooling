# Gpt5.5_Only 配置

用途：将当前所有可由 GPT 替代的文本、推理、文案和结构化任务统一到 Codex runtime 中的当前对话模型能力，逻辑模型标记为 `gpt-5.5 / medium`。该配置适合直接在 Codex 系统内工作、目标转向质量与速度的阶段，不需要本地 OPENAI_API_KEY。

## 配置结论

已替代项：

- PowerPoint-creator 的 `OPENAI_MODEL`、`OPENAI_REVIEW_MODEL`、`OPENAI_FLASH_MODEL`、`OPENAI_THINKING_MODEL` 仅作为 GPT 层逻辑模型标记；实际执行由当前 Codex runtime 对话承担。
- PowerPoint-creator 的 `OPENAI_COST_FALLBACK_MODEL`、`OPENAI_MINI_MODEL`、`UPGRADE_STRUCTURE_MODEL`、`UPGRADE_LONG_DOC_MODEL`、`UPGRADE_PUBLICATION_REVIEW_MODEL` 仅作为审计、生成、评审任务的路由标签；不触发项目本地 OpenAI API 调用。
- Daily-Auto-Report 的 GPT 工作流编排、冲突解释、候选降级模型。
- JLR_data_statistic 的展示文案与 presentation wording 路由。
- Webstyle-editor 与 block 未来可选 AI suggestion / explanation 路由。

不可替代项：

- `deepseek-v4-pro`：中文语义理解、中文意图拆解、中文任务路由仍按既有硬规则保留。当前系统明确要求中文处理不静默降级到其他模型。
- `doubao-1-5-vision-pro-32k` / Ark Endpoint：Local-photo-model 的图片视觉索引能力依赖当前视觉模型接口，不能仅通过文本 GPT profile 等价替换。
- 本地确定性引擎：SQLite FTS、Jieba、AST/schema mutation、文件系统归档等不是模型能力，不应替换成 GPT。

## 可复制环境变量

这些变量用于记录 profile 与任务分层，不要求配置 `OPENAI_API_KEY`：

```bash
export MODEL_STACK_PROFILE="Gpt5.5_Only"
export OPENAI_MODEL="gpt-5.5"
export OPENAI_REVIEW_MODEL="gpt-5.5"
export OPENAI_FLASH_MODEL="gpt-5.5"
export OPENAI_FLASH_REASONING="medium"
export OPENAI_THINKING_MODEL="gpt-5.5"
export OPENAI_THINKING_REASONING="medium"
export OPENAI_COST_FALLBACK_MODEL="gpt-5.5"
export OPENAI_MINI_MODEL="gpt-5.5"
export UPGRADE_STRUCTURE_MODEL="gpt-5.5"
export UPGRADE_LONG_DOC_MODEL="gpt-5.5"
export UPGRADE_PUBLICATION_REVIEW_MODEL="gpt-5.5"
```

Daily-Auto-Report：

```bash
export OPENAI_FLASH_MODEL="gpt-5.5"
export OPENAI_FLASH_REASONING="medium"
export OPENAI_THINKING_MODEL="gpt-5.5"
export OPENAI_THINKING_REASONING="medium"
export OPENAI_COST_FALLBACK_MODEL="gpt-5.5"
export OPENAI_MINI_MODEL="gpt-5.5"
```

JLR_data_statistic：

```bash
export JLR_PRESENTATION_MODEL="gpt-5.5"
export JLR_PRESENTATION_REASONING="medium"
```

## 与其他配置的关系

- `Gpt5.5_Only` 是当前主配置。
- `cost-effective` 是行为策略回退配置；在 Codex runtime 内通过更短上下文、更少重试和更克制的审计深度控制消耗，不再切换到本地 OpenAI key 模式。
