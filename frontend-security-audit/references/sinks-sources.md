# 非常识 Sink/Source — v6

## Sink

**HTML注入：** createContextualFragment · element.setHTML()(配置不当) · shadowRoot.innerHTML · DOMParser→插入DOM · iframe.srcdoc动态 · innerHTML+=chunk(流式) · insertAdjacentHTML(增量)

**属性注入：** style.setProperty/.cssText · CSS url(...)拼接输入 · `<base href>`动态 · setAttribute()对srcdoc/formAction/poster

**代码执行：** AsyncFunction()/GeneratorFunction() · new Worker/SharedWorker(动态URL) · import(动态) · importScripts()(Worker/SW) · 动态`<script>`设src/textContent

**URL导航：** pushState/replaceState可控 · `<button formaction>` · meta refresh动态

**消息：** BroadcastChannel.onmessage · MessageChannel.port.onmessage · SW clients.openWindow(动态URL)

**流式：** ReadableStream/TransformStream→DOM · EventSource.onmessage→DOM · for await→innerHTML · TextDecoderStream未净化

**Markdown：** rehype-raw(HTML穿透) · allowDangerousHtml:true · showdown默认不转义

**模板引擎：** EJS `<%-` · Handlebars `{{{` · Pug `!{` · Nunjucks `|safe` · Liquid `|raw` · _.template `<%-`

**§ssrf SSRF（仅SSR/API route上下文）：**
- fetch/axios/got/undici/http.request(用户可控URL)
- 适用：getServerSideProps/loader/server actions/API routes/server中间件
- 判定：URL参数来自req.query/req.body/params/searchParams + 未校验协议/域名/IP = SSRF Sink
- 注意：纯客户端fetch非SSRF（浏览器同源策略保护）

## Source

**直接可控：** window.name(跨域持久) · document.referrer · FileReader.readAsText/readAsDataURL · performance.getEntries()

**存储：** localStorage · sessionStorage · document.cookie · indexedDB · caches.match()

**间接可控：** API响应用户内容 · AI/LLM生成 · GraphQL用户字段(comments/posts/profiles/messages) · CMS配置 · i18n翻译(CMS编辑+HTML)

**外部可控：** postMessage event.data(未验证origin) · WebSocket.onmessage · BroadcastChannel · 第三方API/SDK · CDN JSON配置

**WebRTC：** RTCPeerConnection ICE candidate(泄露内网IP,现代浏览器默认mDNS缓解) · RTCDataChannel.onmessage
