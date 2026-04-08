# SSR注入 + AI XSS — v6

## §1 SSR序列化注入

### §1.1 经典序列化注入
检测：JSON.stringify→`<script>` · __NEXT_DATA__/__NUXT__手动拼接 · 自定义_document/_app序列化 · 嵌套深层用户字段

判定：未用serialize-javascript/devalue/superjson = 漏洞。仅JSON.stringify但含`</script>`或`</style>`转义(如`<\/`) = 需验证转义充分性。

### §1.2 RSC Flight Payload注入（Next 13+ App Router）
检测：
- Server Component直接将用户数据嵌入JSX → 序列化为RSC payload
- 自定义RSC streaming处理
- Server Actions返回用户可控数据 → 客户端解析

判定：
- 框架默认序列化通常安全，但自定义`<script>`拼接/手动处理payload=绕过保护
- Server Component中dangerouslySetInnerHTML含用户数据 → hydrate后=XSS
- Server Actions返回值直达dangerouslySetInnerHTML → 同上

### §1.3 通用SSR
- Remix loader/action → useLoaderData → 未净化渲染 = 隐式Sink
- SvelteKit load → $page.data → {@html} = 隐式Sink
- Astro服务端组件 → set:html = 隐式Sink

## §2 AI生成内容XSS

规则：AI/LLM输出 = 🔴 external Source（不可信，即使是自有模型）

检测：
- WSS/SSE/ReadableStream → innerHTML/v-html/dangerouslySetInnerHTML
- Markdown→HTML(marked/remark/showdown/markdown-it) → 未净化DOM
- rehype-raw穿透(允许raw HTML) · allowDangerousHtml:true
- AI SDK(Vercel AI SDK/LangChain) streaming → 追加DOM
- innerHTML+=chunk / insertAdjacentHTML('beforeend',chunk) = 流式XSS
- EventSource.onmessage → DOM

判定：
- AI→DOM无净化 = 🔴漏洞
- Markdown未关闭raw HTML = 🔴漏洞
- innerHTML+= = 🔴漏洞（每次追加均可注入）
- 有净化但仅最终净化(非每chunk) → 🟡（流式中途可注入）
- Markdown配置sanitize:true + 无rehype-raw → 通常安全（验证配置）
