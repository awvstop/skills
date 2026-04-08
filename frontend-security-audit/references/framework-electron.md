# Electron / Extension — v6

**Electron 安全配置：**
- nodeIntegration:true + contextIsolation:false = Node权限暴露（🔴最高危）
- webSecurity:false = 禁用同源策略
- allowRunningInsecureContent:true = HTTP资源混合加载
- webviewTag:true + 未限制preload/nodeIntegration

**Electron IPC（追踪路径：renderer→contextBridge API→preload→ipcMain handler→main逻辑）：**
- ipcMain.handle/on 未校验sender(event.senderFrame.url) → 任意renderer可调用
- ipcRenderer.invoke/send参数可控 → 追踪到main进程处理逻辑
- contextBridge.exposeInMainWorld暴露过多API(文件/命令/网络) → 审计每个暴露的方法
- preload脚本暴露eval/exec/spawn → 等同RCE

**Electron 其他：**
- webContents.executeJavaScript(可控) = RCE
- shell.openExternal(可控URL) = 命令注入(file://+特殊字符)
- protocol.registerSchemeAsPrivileged自定义协议 → 检查handler
- 自动更新URL可控/无签名验证

**Extension(浏览器扩展)：**
- content script innerHTML处理网页数据 → 网页=🔴Source
- background script中fetch(网页数据URL) → SSRF
- manifest CSP unsafe-eval/unsafe-inline
- externally_connectable matches过宽
- storage.local/chrome.storage无加密存敏感数据
- tabs.executeScript(可控) = 代码注入
