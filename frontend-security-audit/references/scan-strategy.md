# Phase 1 Sink-first 扫描操作规程 — v6

> Phase 1执行时加载。定义代码读取策略、追踪规则、预算控制。

## 代码视窗（两步读取，严禁全文件）

```
Step A：读取Sink行±40行 → 识别数据来源变量/函数名
Step B：Step A中未解析到定义的变量 →
  同文件 → 读取定义区域(±20行)
  跨文件 → 利用aliases+依赖子图定位 → 读取目标函数体(±40行)
Step A+B合计计入该Sink行预算
```

## 预算自适应

- 当前文件内grep命中≥4个Sink → 视窗压缩至±25行
- 已用行数>80%预算且P0/P1未完 → P3+延后至下批
- 已用行数>90%预算 → 仅P0继续，余项记入「未扫描清单」

## grep命中首次确认

读取时确认Sink位于活跃代码（非注释/字符串/日志）。
- 注释/字符串中 → 标`[noise]`剔除
- 被注释的代码块(`// el.innerHTML = ...`) → 标`[noise]`
- 条件编译/dead code(如`if(false){...}`) → 标`[noise]`

## 优先级

| 级别 | 类型 |
|------|------|
| P0 | 直接XSS/RCE/SSRF(SSR) |
| P1 | 凭证/认证/授权 |
| P2 | 间接/链式(原型污染→XSS等) |
| P3 | DOM/URL/Message/开放重定向 |
| P4 | 配置(CSP/CORS/Cookie等) |
| P5 | 供应链/信息泄露/最佳实践 |

## Source信任标签（简表，Phase 2详用）

| 标记 | 来源 |
|------|------|
| 🔴 external | URL参数/postMessage/WebSocket/AI输出/window.name/document.referrer |
| 🟠 user | 表单/文件上传/contenteditable/clipboard |
| 🟡 indirect | API响应(含用户内容)/CMS/i18n/GraphQL用户字段 |
| 🟢 storage | localStorage/sessionStorage/cookie/indexedDB |
| ⚪ internal | store/cache/computed — **继续追踪到写入源** |

## 特殊标记

- SSR数据获取函数返回值 = 隐式Sink（见framework-*.md）
- SSR/API route中fetch(动态URL) = SSRF Sink（见sinks-sources.md §ssrf）
- as any/@ts-ignore 仅在绕过框架安全类型约束时提升优先级
- 净化库包裹的Sink仍标记（Phase 2验证净化质量）
- Trusted Types + require-trusted-types-for → 重点createPolicy回调

## 去重

同Sink表达式+同数据流 → 合并为单条TODO

## 追踪剪枝(deep模式)

- node_modules/第三方库 → 停止，记录边界（`[boundary:lib-name]`）
- utils调用深度>2 → 截断记录
- .d.ts/类型文件 → 跳过
- 自适应深度：直到确认Source信任等级 或 硬限制8层
- 超5层标记`[deep-trace]`

## 响应式状态桥接

写入端(dispatch/commit/set/setState) = 传播节点
读取端(useSelector/computed/mapState/useStore) = 新Source起点
两端之间的状态管理层视为传播通道，不视为净化。

## TRACE格式（每次跨文件/跨状态跳转）

```
[TRACE] fetchComments()@api.ts →[dispatch] store/comments.ts →[read] Comment.vue:v-html [🟡]
```

- 每跳标注`[✓]`(已读)或`[?]`(推断)
- 未完成链路禁止推断补全，标`[incomplete]`
- 预算紧张时压缩为单行

## 证据等级

- E1: 完整Source→Sink链路，每个节点已通过读取代码确认`[✓]`
- E2: 链路含`[inferred]`节点（未读取代码，依据命名/上下文推断）
- E3: 仅Sink模式匹配，未做任何追踪

## 内联凭证检测（非grep阶段）

Phase 1读取代码时遇到以下模式 → 标记为TODO：
- 硬编码JWT字符串字面量（见checks-credentials.md §jwt）
- 上述高置信凭证模式出现在非grep扫描路径的文件中
