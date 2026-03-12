# Vue / Nuxt — v6

> v-html=常识不列

**Vue：** $route.query/$route.params直达DOM · Vue.compile(用户模板)=代码执行 · v-bind="$attrs"透传危险属性 · :is="用户输入"加载任意组件 · render函数中createElement第二参数domProps.innerHTML

**Nuxt 2：** asyncData/fetch=隐式Sink · __NUXT__序列化→risks-ssr-ai §1 · nuxt.config head拼接可控

**Nuxt 3：** useAsyncData/useFetch=隐式Sink · server/api/路由中fetch可控URL → SSRF · useFetch的baseURL可控时注意SSRF · definePageMeta中redirect可控 → 开放重定向
