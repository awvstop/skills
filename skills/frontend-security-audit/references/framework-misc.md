# Svelte / SvelteKit / jQuery / Lit / Astro / SW — v6

**Svelte：** {@html}无内置净化 · 动态src/href · bind:innerHTML

**SvelteKit：** load返回值=隐式Sink · form actions→$page.form=隐式Sink · +server.ts中fetch可控URL → SSRF · hooks.server.ts中redirect可控 → 开放重定向

**jQuery：** .html()/.append/.prepend/.after/.before/.replaceWith · .attr('src'|'href'|'on*',变量) · $(变量)<3.0选择器注入 · .load(url+变量) · $.ajax url拼接

**Lit/WC：** unsafeHTML/unsafeSVG · shadowRoot.innerHTML · connectedCallback中外部数据直达DOM

**Astro：** set:html无净化 · 服务端组件中fetch可控URL → SSRF

**SW：** importScripts外域 · fetch URL拼接 · clients.openWindow(动态) · cache投毒(caches.put可控key/value)
