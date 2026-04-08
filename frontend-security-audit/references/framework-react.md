# React / Next.js / Remix — v6

> dangerouslySetInnerHTML=常识不列

**React：** ref.current.innerHTML/insertAdjacentHTML(绕虚拟DOM) · href={变量}协议未校验(javascript:) · 动态src/style可控(追踪props调用方)

**Next Pages：** getServerSideProps/getStaticProps/getInitialProps返回值=隐式Sink · __NEXT_DATA__序列化→risks-ssr-ai §1 · _document.js自定义script拼接

**Next App(13+)：**
- Server Component→'use client' props=隐式序列化边界，用户数据经props传递时等同SSR注入
- generateMetadata拼接可控meta(Open Graph注入)
- Server Actions返回值经客户端消费=隐式Sink
- RSC Flight Payload：流式传输React树的JSON表示 → 如Server Component直接拼接用户数据，payload含未转义内容 → 客户端hydrate时注入（见risks-ssr-ai §1.2）
- Route Handlers(app/api/)中fetch可控URL → SSRF Sink
- Parallel Routes / Intercepting Routes：多路由共享layout → 检查layout中的数据流

**Next Middleware：** 重写/重定向URL含用户输入 → 开放重定向 · headers操作

**Remix：** loader/action→useLoaderData/useActionData=隐式Sink · 资源路由中fetch可控URL → SSRF

**SSR通用：** SSR中dangerouslySetInnerHTML无浏览器保护 · hydration mismatch可导致XSS(极端)
