
# 乘用车情报周报系统 — Tier A MVP 工程执行指令 (v1.2 Final)

## 一、系统定位与硬边界

构建一套**Python 异步状态机引擎**，每周自动产出乘用车行业情报周报 Markdown。Agent Skill 作为事后监控与干预界面，不参与确定性数据管线。

**硬边界**：
- ETL 层禁止使用 LangChain/LlamaIndex 做编排流控——其重试语义太粗糙
- LLM 仅允许在两条安全红线内介入：(1) 冲突仲裁前双源文本对齐 (2) 最终周报叙事编排与润色
- LLM 禁止做：降级路由决策、去重判定、数据冲突的自动裁决

## 二、信源矩阵与摄取协议

### T1 付费 API（定量基线）

| 信源 | 接入协议 | refresh_cadence | expected_lag（动态绑定） |
| --- | --- | --- | --- |
| Wind/Choice API（乘联会数据） | Python SDK / REST | weekly | ≤ 2 days |
| 车智云/易车 API（上险量） | B2B REST API | weekly | ≤ 3 days |
| ACEA 官网数据集 | HTTP 定向解析 | monthly | ≤ 7 days |

### T2 邮件解析（定性战略情报）

| 信源 | 接入协议 | refresh_cadence |
| --- | --- | --- |
| Automotive News（北美/欧洲/中国三站） | IMAP 邮件解析 | weekly |
| S&P Global Mobility / AutoTechInsight | IMAP 邮件解析 | weekly |
| WardsAuto / Cox Automotive | IMAP 邮件解析 | monthly |

### T3 RSS 聚合（技术前沿）

| 信源 | 接入协议 | refresh_cadence |
| --- | --- | --- |
| GGAI（高工智能汽车） | RSS + User-Agent + ≥5s interval | continuous |
| Gasgoo（盖世汽车） | RSS + User-Agent + ≥5s interval | continuous |
| CleanTechnica / Electrek | RSS | continuous |
| Autocar India / GaadiWaadi | RSS | continuous |

## 三、降级路由矩阵（Fallback Routing）

当主源不可达时，按以下路由降级并注入 `quality_degradation_flag`：

| 主源 | Fallback-1 | Fallback-2 | 降级触发条件 |
| --- | --- | --- | --- |
| Wind/Choice API | 崔东树公众号 RPA/OCR | CPCA 官网新闻中心月度通稿 | API 鉴权失败或无数据返回 |
| 车智云/易车 API | 中汽协(CAAM)月度产销公告 | **维度退场**（不提供任何近似替代） | API 欠费或阻断 |
| ACEA 官网 | KBA(德)/SMMT(英)/CCFA(法) 并行抓取 | — | 官网改版或反爬拦截 |
| Automotive News 邮件 | [QuotaGuard] → GNews API | — | 邮件未送达 |
| S&P/WardsAuto 邮件 | NADA / Edmunds 行业研报 | — | 邮件订阅失效 |

**崔东树公众号不存在二级降级**——见 CPCA Fallback-2 兜底。

**GNews API 配额守卫规则**：
- 免费层 100 req/day，单次周报运行消耗 ≤ 5 次请求
- 每次请求前读取 `gnews_quota.json` 中 `remaining_today`
- `remaining_today < 20` → 主动熔断，注入 `STATUS_GNEWS_QUOTA_EXHAUSTED`

## 四、摄取层超时与重试策略

每条摄取线定义 timeout/retry/backoff 三元组：

```
T1 定量 API:  timeout=30s, max_retries=2, backoff=exponential(1s, 4s)
T2 邮件IMAP:  timeout=15s, max_retries=1, backoff=none
T3 RSS:       timeout=10s, max_retries=0 (非关键路径)
```

全局 pipeline deadline: **300s**。超时后强制输出 partial report，注入 `[PIPELINE_INCOMPLETE]` 标签。

并发调度：使用 `asyncio.wait(return_when=FIRST_EXCEPTION)` 替代 `gather`，实现单线异常隔离。

## 五、数据处理层规则

### 去重
- 对所有摄取文本的标题+摘要执行 TF-IDF 向量化
- 余弦相似度 ≥ 0.75 → 合并，按信源等级 T1 > T2 > T3 保留最高权重源文本

### 冲突仲裁
- 同一指标双源数值偏差 ≥ 5% → 注入 `[数据冲突]` 标签
- LLM 收到此标签后**禁止生成确定性结论**，必须双源并列展示

### 新鲜度校验
- `expected_lag` 与 `fetch_path` 动态绑定（见 T1 表格），不从全局常量读取
- Δt = now - max(record_date)，若 Δt > expected_lag → 触发 `STATUS_DATA_STALE`
- 过期数据禁止用于环比/同比推演，注入 `[数据延迟未更新]`

### 降级质量标注
Fallback 激活时，ETL 注入 `quality_degradation_flag`，周报渲染模板输出显式警告框：

```
> ⚠️ **[情报源降级公告: GNews API 激活]**
> 本周未能解析 Automotive News 独家深度分析。
> 关键缺陷：缺乏车企高管专访、未公开的供应链 M&A 内幕及核心定点细节。
```

## 六、归档与审计追踪

每次 pipeline 运行后写入三级目录：

```
data/
  raw/        ← 各信源原始 payload（{date}/{source}.json），保留 30 天
  processed/  ← 去重+仲裁后中间态，保留 90 天
  output/     ← 最终周报 .md，永久保留
```

## 七、运维监控（HealthCheck 模块）

- **存储介质**：SQLite (`health_monitor.db`)，WAL 模式，容器部署时挂载 volume
- **状态监测**：每次 pipeline 结束后写入各信源状态（Active / Fallback / Offline）
- **连续异常告警**：任一主源连续 2 周处于 Fallback/Offline → 生成告警日志
- **Schema Drift**：对 API 返回 JSON key set 做 SHA-256，hash 变更 → `[Schema_Drift_Warning]`，暂停自动解析，转人工介入

## 八、周报空窗期渲染规范

月度信源（ACEA、WardsAuto、Cox 等）在非发布周渲染为：

```markdown
### 📊 欧洲市场动态 (ACEA)
*状态：[月度更新数据空窗期]*
*最近更新：2026-05-20（涵盖4月数据） | 下期预计：2026-06-20*
* 历史基线回顾：上月欧洲 BEV 渗透率 11.9%...
* 本周替代监测：（若无突发政策或降级事件，此项留白）
```

## 九、Tier A MVP 第一周（Day 1-7）交付清单

按优先级排序：

1. `asyncio` 摄取框架骨架，含 timeout/retry/backoff 三元组与全局 300s deadline
2. T1 Wind API 摄取模块 + freshness check（动态 expected_lag）
3. T2 Automotive News IMAP 邮件解析模块
4. T3 RSS 聚合模块（GGAI、CleanTechnica 等，≥5s interval）
5. GNews API 兜底模块 + QuotaGuard 配额计数器
6. TF-IDF 去重 + 跨源冲突仲裁（≥5% 偏差标记）
7. 三级归档目录（raw/processed/output）+ 保留策略
8. SQLite HealthCheck 模块 + 状态写入 + 连续 fallback 计数查询
9. 降级质量标注注入 + 空窗期渲染模板
10. LLM 推演层（系统提示词 + 带标签的上下文注入，仅做叙事编排与冲突对齐）

## 十、禁止事项

- ❌ Google News RSS（2022 年已停运）
- ❌ NewsAPI.org 进入 Tier A 代码路径（留 Tier C 选配）
- ❌ CPCA 官网 (cpcaauto.com) 作为周度数据主源（官网仅发布月度通稿）
- ❌ 金融监管总局“交强险月度公开摘要”（不存在该数据产品）
- ❌ 硬编码 `expected_lag` 为全局常量
- ❌ `asyncio.gather` 无超时控制
- ❌ LangChain/LlamaIndex 用于 ETL 编排
