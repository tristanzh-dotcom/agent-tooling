# 性价比配置

用途：当需要降低消耗或加快审计/生成节奏时启用。该配置仍在 Codex runtime 对话中执行 GPT 层任务，不需要本地 OPENAI_API_KEY；它通过行为策略控成本，而不是切换到项目本地 OpenAI API。

## 适用规则

- 中文语义理解、中文意图拆解、中文任务路由继续使用 `deepseek-v4-pro`。
- 普通 GPT 任务由当前 Codex runtime 模型承担，逻辑模型标记保持 `gpt-5.5`。
- 成本敏感与批量任务通过更短上下文、更少重试、更明确的输入边界和更克制的审计深度控成本。
- 不启用 `high` 或 `xhigh` 作为默认配置。
- 不把真实 API Key 写入仓库或脚本。

## 可复制环境变量

```bash
export MODEL_STACK_PROFILE="cost-effective"
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

Daily-Auto-Report 备份配置：

```bash
export OPENAI_FLASH_MODEL="gpt-5.5"
export OPENAI_FLASH_REASONING="medium"
export OPENAI_THINKING_MODEL="gpt-5.5"
export OPENAI_THINKING_REASONING="medium"
export OPENAI_COST_FALLBACK_MODEL="gpt-5.5"
export OPENAI_MINI_MODEL="gpt-5.5"
```

JLR 展示文案备份路由：

```bash
export JLR_PRESENTATION_MODEL="gpt-5.5"
export JLR_PRESENTATION_REASONING="medium"
```

## 恢复方式

将上述 env 块写回目标项目 `.env`，或在启动服务前执行对应 `export`。如果运行环境已有 `Gpt5.5_Only` 配置变量，必须先 unset 或覆盖，否则环境变量优先级会高于 `.env`。该配置只改变 profile 与行为策略，不要求本地 `OPENAI_API_KEY`。
