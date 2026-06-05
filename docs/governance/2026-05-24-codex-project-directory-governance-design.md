# Codex 项目物理目录治理与迁移设计

日期：2026-05-24  
状态：设计稿，等待 TZ 审阅  
适用范围：Codex 中所有长期工作流项目、Web 发布项目、通用运维能力与项目索引  
执行限制：本文只定义治理设计，不执行目录迁移、不修改代码、不修改 Web 路由、不修改 Codex 状态库。

## 1. 问题定义

当前 Codex 项目存在四类混乱：

1. **物理目录分散**  
   同样是 Codex 长期工作流项目，有的在 `/Users/tristanzh/Documents`，有的在 `/Users/tristanzh/agent`，导致归属不统一。

2. **Agent 与项目边界混淆**  
   `/agent01` 到 `/agent04` 是 Web 发布技术路由，不应直接等同于项目文件夹或业务归属。

3. **业务项目与通用 skill 混放**  
   `run codex self-audit`、模型治理、命名治理、TDD/SDD 这类通用能力不属于 `乘用车信息汇总`，但目前容易被 Agent02 目录吸收。

4. **历史名称与正式名称并存**  
   `DiamondTurtles`、`LIMB`、`Webstyle-editor` 等历史名仍在部分文档或目录中出现，需要明确它们是历史语境、目录名或回滚源，而不是正式项目名。

## 2. 第一性原则

### 2.1 同类目标同类物理归属

所有 Codex 长期工作流项目都应放在同一个根目录：

```text
/Users/tristanzh/agent/
```

`Documents` 应主要保存普通人工资料，不作为 Codex 项目的主工作区。

### 2.2 中文是产品名，英文是目录名

- 用户可见名称使用中文正式项目名。
- 物理目录使用稳定英文名或已经稳定的历史英文目录名。
- 不用 Web route、agent id、历史简称作为目录主命名依据。

### 2.3 Agent 是入口，不是项目

| 概念 | 定义 |
| --- | --- |
| Agent route | Web 发布入口，例如 `/agent02` |
| Codex project | 一个可持续维护的业务或平台工作流 |
| Workflow | 项目内部可执行能力，例如飞书推送、报告生成、图片检索 |
| Skill | 跨项目工具能力，例如 self-audit、TDD、SDD |

### 2.4 Skill 只被调用，不归属业务项目

通用 skill 的真实运行位置仍应在：

```text
/Users/tristanzh/.codex/skills/
```

其使用记录、治理文档和跨项目规范应归入 `Codex-Ops`，不放入某个业务项目。

### 2.5 迁移必须可回滚

涉及绝对路径的项目迁移必须分阶段执行：

- 先写规范；
- 再迁移一个项目；
- 再更新索引和引用；
- 再跑验证；
- 最后保留旧路径软链接或迁移说明一段时间。

## 3. 目标物理目录结构

建议最终结构：

```text
/Users/tristanzh/agent/
├── web/                         # Web 发布与编辑平台
├── Codex-Ops/                   # Codex 运维、自检、命名治理、通用工具文档
├── Document-creator/            # 文档生成小能手，Agent01
├── Passenger-Vehicle-Intel/     # 乘用车信息汇总，Agent02
│   ├── domestic-sales/          # 中国乘用车销量汇总，项目2.1
│   ├── jlr-sales/               # JLR 全球及中国销量数据，项目 2.2
│   ├── hardware-supplier/       # 硬件供应链关系看板，内部能力
│   └── data-platform/           # 乘用车数据平台，内部能力
├── DiamondTurtles/              # 钻纹龟资料库，Agent03
├── Local-photo-model/           # 本地图像检索，Agent04
├── Medical/                     # 镁健康营销资产
├── docs/
│   ├── governance/              # 跨项目治理规范
│   └── model-configs/           # 跨项目模型配置记录
└── _archive/                    # 归档项目
```

## 4. 项目映射表

| 正式项目名称 | 保留简称 | 当前目录 | 目标目录 | Web 路由 | 处理方式 |
| --- | --- | --- | --- | --- | --- |
| Web 发布与编辑平台 | 无 | `/Users/tristanzh/agent/web` | `/Users/tristanzh/agent/web` | `/agent01`-`/agent04` | 保持 |
| 文档生成小能手 | 文档生成小能手 | `/Users/tristanzh/Documents/PowerPoint-creator` | `/Users/tristanzh/agent/Document-creator` | `/agent01` | 迁移 |
| 乘用车信息汇总 | 乘用车信息汇总 | `/Users/tristanzh/agent/Passenger-Vehicle-Intel` | `/Users/tristanzh/agent/Passenger-Vehicle-Intel` | `/agent02` | 迁移 / 重命名 |
| 中国乘用车销量汇总 | 项目2.1 | `/Users/tristanzh/agent/Passenger-Vehicle-Intel` | `/Users/tristanzh/agent/Passenger-Vehicle-Intel/domestic-sales` | `/agent02`, key `domestic` | 归入父项目 |
| JLR 全球及中国销量数据 | 项目 2.2 | `/Users/tristanzh/agent/Passenger-Vehicle-Intel/jlr-sales` | `/Users/tristanzh/agent/Passenger-Vehicle-Intel/jlr-sales` | `/agent02`, key `jlr` | 迁入父项目 |
| 钻纹龟资料库 | 项目3 | `/Users/tristanzh/Documents/DiamondTurtles` | `/Users/tristanzh/agent/DiamondTurtles` | `/agent03` | 迁移 |
| 本地图像检索 | 项目4 | `/Users/tristanzh/agent/Local-photo-model` | `/Users/tristanzh/agent/Local-photo-model` | `/agent04` | 保持 |
| 镁健康营销资产 | 无 | `/Users/tristanzh/agent/Medical` | `/Users/tristanzh/agent/Medical` | 无 | 保持 |
| Codex 运维与治理 | Codex-Ops | 分散在 `Assistant/docs`、`agent/docs`、`.codex/skills` 使用记录 | `/Users/tristanzh/agent/Codex-Ops` | 无 | 新建归属 |

## 5. Agent02 边界重定义

### 5.1 Agent02 应拥有

- `乘用车信息汇总`
- `中国乘用车销量汇总 / 项目2.1`
- `JLR 全球及中国销量数据 / 项目 2.2`
- 汽车数据采集、清洗、飞书卡片、调度器、汽车 Web 调试面板
- 与汽车项目直接相关的内部能力：
  - `assistant_data_platform`
  - `硬件供应链关系看板`
  - 出口 / 进口 / 国产销量相关数据处理

### 5.2 Agent02 不应拥有

- `run codex self-audit`
- Codex 命名治理
- 全局模型路由治理
- TDD / SDD skill 本体
- Web 发布平台范式治理
- 非汽车项目的通用脚本、通用审计、通用工具文档

### 5.3 允许调用但不拥有

Agent02 可以调用通用 skill，但文档中必须表述为：

> 本项目调用该通用能力，不拥有该能力。

例如：

- 调用 `codex-self-audit` 检查汽车项目质量；
- 调用 TDD / SDD skill 指导开发流程；
- 调用 Lark skill 推送汽车报告。

## 6. Codex-Ops 定义

建议新增：

```text
/Users/tristanzh/agent/Codex-Ops/
```

职责：

- Codex 项目索引治理
- 命名规范与别名治理
- 通用模型路由策略记录
- `codex-self-audit` 使用记录和审计报告
- TDD / SDD / skill 使用规范
- 跨项目检查清单
- Codex 状态库修复记录
- 跨项目 handoff 总文档

不职责：

- 不存放业务代码。
- 不承载 Web 页面。
- 不替代 `~/.codex/skills`。
- 不拥有任何业务项目的数据。

## 7. 迁移顺序建议

### Phase 0：冻结规则

输出并确认本文。

不得迁移目录，不得改代码。

### Phase 1：创建 Codex-Ops

创建 `/Users/tristanzh/agent/Codex-Ops`，迁入或复制通用治理文档：

- 命名治理文档
- 模型治理文档
- Codex 状态修复记录
- self-audit 使用说明

不移动 `~/.codex/skills`。

### Phase 2：迁移 Agent01

从：

```text
/Users/tristanzh/Documents/PowerPoint-creator
```

到：

```text
/Users/tristanzh/agent/Document-creator
```

迁移后更新：

- 项目索引；
- Web 发布配置中引用的业务目录；
- Codex 最近项目记录；
- 文档中的绝对路径；
- 必要测试。

旧路径暂时保留软链接。

### Phase 3：迁移 Agent03

从：

```text
/Users/tristanzh/Documents/DiamondTurtles
```

到：

```text
/Users/tristanzh/agent/DiamondTurtles
```

迁移后更新：

- Web `/agent03` 文档引用；
- 项目索引；
- Codex 最近项目记录；
- `PROJECT_RULES.md`；
- 规格和计划文档中的绝对路径。

旧路径暂时保留软链接。

### Phase 4：整理 Agent02

从：

```text
/Users/tristanzh/agent/Passenger-Vehicle-Intel
```

到：

```text
/Users/tristanzh/agent/Passenger-Vehicle-Intel
```

同时将：

```text
/Users/tristanzh/agent/Passenger-Vehicle-Intel/jlr-sales
```

迁入：

```text
/Users/tristanzh/agent/Passenger-Vehicle-Intel/jlr-sales
```

注意：这是最高风险迁移，因为飞书推送、调度器、Web API、测试和数据路径中可能有大量绝对路径。

### Phase 5：收敛全局索引

将全局索引迁移或复制到更合适的治理位置：

```text
/Users/tristanzh/agent/Codex-Ops/PROJECT_INDEX.md
```

`/Users/tristanzh/agent/Assistant/PROJECT_INDEX.md` 可以在过渡期保留镜像或指向说明。

### Phase 6：清理旧路径

只有在连续多次项目启动、Web 预览、测试、飞书推送都稳定后，才考虑删除旧路径软链接。

## 8. 验证策略

每迁移一个项目，必须执行：

1. 文件存在检查。
2. 项目文档绝对路径检索。
3. Codex 项目记录检查。
4. Web 路由检查。
5. 项目级测试。
6. 跨项目 Web 测试。
7. 若涉及飞书，执行 preview 测试，不能默认发送真实消息。

示例验证分类：

| 项目 | 必要验证 |
| --- | --- |
| Web 发布与编辑平台 | `npm test` |
| 文档生成小能手 | `/agent01` 页面、项目列表、预览 API |
| 乘用车信息汇总 | 汽车测试、Agent02 API、飞书 preview |
| JLR 全球及中国销量数据 | JLR 数据文件、Agent02 `jlr` 子项目 preview |
| 钻纹龟资料库 | `/agent03` 页面、文档路径、Web 测试 |
| 本地图像检索 | `/agent04` 页面、后端状态、图片服务 |
| 镁健康营销资产 | 文档生成脚本、素材路径 |

## 9. 软链接策略

迁移后旧路径不立即删除。

建议过渡方式：

```text
旧路径 -> 新路径
```

例如：

```text
/Users/tristanzh/Documents/DiamondTurtles -> /Users/tristanzh/agent/DiamondTurtles
```

保留期规则：

1. 每个项目迁移完成后，立即执行该项目的全量测试和相关跨项目回归测试。
2. 如果所有测试项全部通过，旧路径软链接保留 1 天。
3. 如果任一测试项未通过，停止后续清理动作，并提示 TZ 给出下一步处理意见。
4. 迁移完成 3 天后，将保留文件全部移动到新建目录：

```text
/Users/tristanzh/agent/temp
```

并断开所有旧路径映射。

5. 迁移完成 6 天后，如果没有发现相关问题，物理删除 `/Users/tristanzh/agent/temp` 及其内部文件。

执行约束：

- `/Users/tristanzh/agent/temp` 需要在执行迁移计划时新建。
- `temp` 只用于迁移缓冲，不作为任何项目的正式工作区。
- 删除 `temp` 前必须再次确认没有测试失败、Web 路由异常、Codex 项目打开异常或飞书 preview 异常。

## 10. 命名债务处理规则

迁移期间发现旧称呼时：

1. 如果只是历史说明，保留并标注历史语境。
2. 如果是可见主名称，记录为命名债务。
3. 如果是代码路径或 API 字段，不直接改，先评估风险。
4. 如果是测试断言，必须按 TDD 方式先改测试再改实现。

## 11. 当前不做的事情

本文不建议立刻做：

- 不立即移动目录；
- 不立即删除 `/Users/tristanzh/Documents/PowerPoint-creator`；
- 不立即删除 `/Users/tristanzh/Documents/DiamondTurtles`；
- 不立即删除 `/Users/tristanzh/agent/Assistant`；
- 不移动 `~/.codex/skills`；
- 不修改 Web 路由 `/agent01` 到 `/agent04`；
- 不修改 LaunchAgent；
- 不修改模型配置；
- 不修改飞书推送链路。

## 12. TZ 决策记录

以下决策已由 TZ 在 2026-05-24 确认：

1. 目录英文名采用本文建议：
   - `Document-creator`
   - `Passenger-Vehicle-Intel`
   - `DiamondTurtles`
   - `Codex-Ops`
2. `Assistant/PROJECT_INDEX.md` 最终迁到 `Codex-Ops/PROJECT_INDEX.md`。
3. Agent02 的 JLR 子项目使用 `jlr-sales` 作为目录名。
4. 旧路径软链接保留规则：
   - 变更完成后立即全量测试；
   - 若所有测试项全部通过，保留 1 天软链接；
   - 若测试不全通过，提示 TZ 给出下一步处理意见；
   - 3 天后将保留文件移动到 `/Users/tristanzh/agent/temp`，并断开所有映射；
   - 6 天后若无相关问题，物理删除 `/Users/tristanzh/agent/temp` 及其内部文件。
5. 接受“每次只迁移一个项目”的节奏。

## 13. 推荐结论

推荐采用本文结构，并按 Phase 0 到 Phase 6 顺序执行。

核心收益：

- 所有 Codex 项目统一归到 `/Users/tristanzh/agent`；
- Agent02 从通用工具暂存区恢复为汽车业务容器；
- Codex-Ops 接管通用治理；
- Web 发布平台只负责发布壳与右边栏编辑范式；
- skill 保持跨项目工具属性，不被业务项目吸收；
- 历史目录和历史名称被保留为可追溯信息，而不是继续污染正式命名。
