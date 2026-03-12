# 供应链 + 正则 + SRI — v6

**package.json：** */latest/>=宽松 · postinstall/prepare/preinstall含网络请求/shell命令 · git+ssh/https/file:仓库外 · lockfile缺失 · typosquatting(近似名包)

**.npmrc：** registry非官方+无HTTPS · @scope:registry缺失(Dependency Confusion) · _authToken硬编码

**lockfile：** resolved非官方 · integrity异常 · lockfile与package.json版本不一致

**CDN/外部脚本：**
- `<script src="外域">`缺integrity属性(SRI) → 🟡
- HTTP协议加载 → 🔴
- 非官方CDN域名 → 🟡
- 动态import()外域URL缺SRI → 🟡（浏览器支持有限,标注）

**正则：** URL白名单缺$/^/.未转义/通配不严 · ReDoS嵌套量词/重叠分组(如`(a+)+`) · HTML黑名单漏svg/math/大小写 · 路径遍历仅替一次../

**依赖版本（已知高危CVE参考）：** 如检测到以下版本建议升级（此列表仅供参考，完整检查请使用`npm audit`/`yarn audit`/`pnpm audit`）：
- DOMPurify<2.4.0 · lodash<4.17.21 · jQuery<3.5.0 · minimist<1.2.6 · node-fetch<2.6.7 · express<4.19.2
