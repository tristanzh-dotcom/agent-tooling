### ☀️ 次日启动胶囊 (Boot Prompt)
请在明天开启新对话时，直接复制以下指令发给系统：

```text
请静默读取并完全理解当前目录下的 `HANDOVER_git_20260614.md`。
1. 请将本对话的逻辑分支锁定为：【Git 仓库治理】，并在你回复的第一句话使用 Markdown 的 H1 标题 (`# Git 仓库治理 工作流重启`) 输出，以便系统自动重命名此对话。
2. 在执行任何操作前，请简要复述当前的【核心卡点】与【下一步行动】。等待我的确认后，再开始执行。
```

## 第一性原理与项目上下文

本次对话的核心目标是把 `/Users/tristanzh/agent` 的开发资产纳入可靠 Git/GitHub 管理，并明确仓库边界与后续治理规则。

当前结构已经确认为双仓：

- `/Users/tristanzh/agent` -> `agent-monorepo`，承载除 `web/` 外的业务项目、治理文档、技能和资料。
- `/Users/tristanzh/agent/web` -> `web-platform`，独立承载可见发布中心。

关键判断：

- 不因为 agent02/03/04/05/06 开发进度不同而拆仓库；仓库边界按权限、发布、共享治理和数据流决定。
- `web/` 独立合理，因为它是共享可见发布面。
- `latest_card_payload.json` 被识别为 agent02 运行快照，但当前决策是继续跟踪，用 `chore(agent02): refresh latest card payload` 保留运行审计锚点。
- 生成产物和本地测试数据不应进入版本控制。

## 今日完成事项

### GitHub 仓库与远程

- 建立并推送根仓库 `agent-monorepo`：
  - `origin`: `https://github.com/tristanzh-dotcom/agent-monorepo.git`
- 建立并推送 `web-platform`：
  - `origin`: `https://github.com/tristanzh-dotcom/web-platform.git`
- 配置 `web/main` upstream，后续可直接 `git push`。
- 确认 `gh` 已登录，token scope 包含 `repo` 和 `workflow`。

### True Monorepo 合并

- 删除 7 个无远程的嵌套 `.git`：
  - `Codex-Ops`
  - `Local-photo-model`
  - `Medical`
  - `Passenger-Vehicle-Intel`
  - `PetRelatedServices`
  - `Stratigic-AGI-System`
  - `Webstyle-editor`
- 将其当前文件状态作为普通目录纳入根仓库。
- 保留 `web/` 独立 Git 仓库，并在根 `.gitignore` 中排除。

### 根仓库 Git 卫生治理

- 更新 `/Users/tristanzh/agent/.gitignore`：
  - `web/`
  - `temp/`
  - `PPT-maker/work/`
  - `Local-photo-model/data/`
  - `pytest-cache-files-*/`
  - `Local-photo-model/tests/test_query_sandbox.db*`
- 从 Git 跟踪中移除 `PPT-maker/work/`，本地文件保留。
- 新增 `/Users/tristanzh/agent/.githooks/pre-commit`：
  - 拦截超过 10MB 的新增文件。
  - 拦截 `.env`、`*.pem`、`*.key`、`*.p12`。
  - 基础扫描私钥、AWS key、OpenAI key 模式。
- 新增 `/Users/tristanzh/agent/.githooks/commit-msg`：
  - 强制 conventional commit 格式。
- 设置根仓库：
  - `core.hooksPath = .githooks`
- 创建并推送 tag：
  - `agent04-stable-20260614`

### 今日根仓库关键提交

- `01c5fcf fix(agent04): stabilize face indexing workflow`
- `d847500 fix(agent02): update vehicle intelligence workflows`
- `2cd780f feat(agent06): add trusted ingest quality workflow`
- `03ed116 fix(agent03): update aquatic report workflow`
- `c3ab7df chore(git): ignore generated work artifacts`
- `acb18d5 chore(git): add repository safety hooks`
- `56c1275 feat(pka): seal trusted ingest quality gates`
- `3863eea feat(agent02): seal foreign JV card v1.8`
- `ae37012 test(agent02): add card3 adapter test coverage and review docs`
- `31d493e docs(agent04): add final audit checkpoint`
- `c6ce3e7 docs(pka): archive stale handover notes`
- `781899f feat(agent03): add mantou ledger insights`
- `936c44f chore(agent02): refresh latest card payload`

### 今日 web-platform 关键提交

- `084f028 feat(web): update agent publishing workflows`
- `95e29d9 feat(agent03): unify MCHT header layout and query input placeholder`
- `ff51b28 fix(agent03): refine MCHT header interaction`
- `fba8d26 feat(agent02): add Bark notifier workflow`

### 当前验证状态

最后一次验证显示：

```text
/Users/tristanzh/agent      ## main...origin/main
/Users/tristanzh/agent/web  ## main...origin/main
```

并确认：

- `PPT-maker/work/` 跟踪数为 0。
- `Local-photo-model/data/` 跟踪数为 0。
- `Local-photo-model/tests/test_query_sandbox.db*` 被 `.gitignore` 命中。
- 两个仓库均已推送到 GitHub。

## 已作出的关键决策

- 选择 true monorepo：7 个无远程嵌套 Git 仓库的历史只有少量 baseline/quality gate 提交，无保留价值；当前文件状态比残留本地 commit 更重要。
- 保持 `web-platform` 独立：`web/` 是可见发布面，受发布边界和 UI 治理约束，应与业务根仓库分开。
- 不因 agent 进度不同拆仓库：agent04 接近完成、agent05/06 调试中只是状态差异，不是仓库边界依据。
- 优先治理增量风险：先拆分提交、推送、ignore 生成产物、加 hooks，再考虑历史重写。
- 暂不重写历史：`.git` 约 171MB 的历史膨胀已知，但当前先截断新增污染；历史清理留待后续专门执行。
- `latest_card_payload.json` 继续跟踪：虽然它是运行时快照，但文件小，且作为 agent02 运行审计锚点有价值。
- `_archive_legacy/` 不盲清：归档目录先判用途，再决定保留、忽略或移出。

## 未解决的风险/报错

- 历史大文件仍在 Git 对象库中，`.git` 大小仍约 171MB；若 clone/push 变慢，需要用 `git filter-repo` 或 BFG 做历史清理。
- 尚未运行历史 `gitleaks detect`，无法证明历史中从未提交过密钥。
- 根仓库 hooks 已加入并本地启用，但新 clone 后仍需执行：
  ```bash
  git config core.hooksPath .githooks
  ```
- `latest_card_payload.json` 未来仍会因 agent02 运行而变脏；当前策略是定期小提交，不是忽略。
- 本轮 Git 治理没有运行全量业务测试；验证集中在 Git 状态、提交拆分、推送、ignore、hooks 和 tag。
- GitHub 私有仓库 branch protection 受账号 plan 限制，不能作为当前必备治理手段。

## 下一步行动

1. 启动后先检查两个仓库状态：
   ```bash
   cd /Users/tristanzh/agent
   git status --short --branch
   git log --oneline -8

   cd /Users/tristanzh/agent/web
   git status --short --branch
   git log --oneline -8
   ```
2. 运行一次历史密钥扫描：
   ```bash
   cd /Users/tristanzh/agent
   gitleaks detect --verbose
   ```
   如果本机没有 `gitleaks`，先安装或改用可用 secret scan 工具。
3. 判断是否需要历史清理：
   ```bash
   cd /Users/tristanzh/agent
   git count-objects -vH
   git rev-list --objects --all | sort
   ```
   若决定清理，先备份并明确是否允许 force push。
4. 继续按路径提交，不做跨 agent 混合 commit：
   ```bash
   git add <single-agent-path>
   git commit -m "fix(agentXX): concise description"
   git push
   ```
5. 如果 agent02 再次刷新卡片快照，按当前策略提交：
   ```bash
   git add Passenger-Vehicle-Intel/workflows/foreign-jv-china-watch/data/latest_card_payload.json
   git commit -m "chore(agent02): refresh latest card payload"
   git push
   ```
6. 视稳定程度为其他 agent 增加 tag，例如 agent02、agent03、agent06/PKA。
