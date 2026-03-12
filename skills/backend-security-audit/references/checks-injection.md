# Injection — BSAF v3.6

> SQL/NoSQL/Cmd/SSTI/XXE/ReDoS/Email/Prototype Pollution/LDAP/HPP/编码安全。自包含，无需引用其他 checks。

## SQL/NoSQL 注入

**Sink**：db.query/cursor.execute/sequelize.query/.raw()/$queryRaw(string)/knex.raw/whereRaw + 拼接/格式化。
**安全**：参数化、ORM 标准方法、Prisma tagged template、Drizzle sql``。
**不安全**：字符串拼接、$queryRaw(string)、.raw()+拼接、createQueryBuilder().where("..."+v)。
**NoSQL**：req.body 直传 find/findOne/aggregate/$where/$ne/$gt → 🔴。防护：express-mongo-sanitize、schema strict:true、DTO 类型强制。Mongoose $where 字符串→代码执行 🔴。查询操作符注入 {password:{$gt:""}} → 认证绕过 🔴。

## 列名/排序注入

`?sort=xxx` / `?orderBy=xxx` / `?fields=xxx` 类参数通常无法用参数化保护（列名不是值）：
- `ORDER BY ${req.query.sort}` → SQL 注入 🔴
- `SELECT ${fields}` → 列名拼接 → 注入/敏感字段暴露 🔴
- MyBatis `ORDER BY ${column}` → 🔴；MyBatis-Plus `.orderByAsc(userCol)` → 🔴
- **防护**：列名/排序方向白名单映射（`allowedSortFields = ['name','createdAt']`）；拒绝不在白名单内的值

## 命令注入

**Sink**：exec/execSync/spawn+shell:true/os.system/os.popen/subprocess+shell=True + 拼接。  
**安全**：execFile/spawn 参数数组(shell=False)、shlex.quote、白名单。  
**区分**：spawn shell:true=危险、list+shell=False=相对安全。

## SSTI

**Sink**：render_template_string(user_input)、Template(req.*)、ejs.render(req.*)、pug.render(req.*)、nunjucks.renderString(req.*)。  
用户输入进模板字符串 → 🔴。仅数据上下文 → 安全。

## XXE

**Sink**：xml2js/xmldom/DOMParser/etree.parse/lxml.parse/SAXParser 未禁外部实体。  
**安全**：resolve_entities=False、禁 FEATURE_EXTERNAL_GENERAL_ENTITIES。

## ReDoS

用户输入构造正则 `new RegExp(req.query.*)` → 🔴。固定正则含嵌套量词用于校验用户输入 → 🟡。Node 单线程 → ReDoS=全服务 DoS。安全替代：re2/safe-regex。

## Email Header Injection

nodemailer.sendMail/smtplib/send_mail 的 to/cc/subject/from 含用户输入 + 未过滤 \r\n → 🟡。

## HPP（HTTP 参数污染）

?role=user&role=admin → req.query.role=['user','admin']，类型校验仅 string → 数组绕过 → 🟡。

## Prototype Pollution（Node）

| 入口 | 风险 |
|------|------|
| lodash.merge/_.defaultsDeep/_.set + req.body | 🔴 |
| deepmerge/deep-extend + JSON.parse(body) | 🔴 |
| dot-prop/object-path/set-value/dset + 用户可控 path | 🔴 |
| Object.assign(target, JSON.parse(body)) | 🟡 |
| {...defaults, ...req.body} spread | 🔵（现代 V8 不复制 __proto__） |
| qs.parse / body-parser extended:true | 🟡 |

**利用链判定**：检测到原型污染 → 检查 package.json 是否有 EJS/Pug/Handlebars → 有则 🔴(RCE)；无 → 🟡 + 检查 isAdmin 类属性污染。  
**防御**：Object.create(null)→无原型链→安全 `[prototype-safe:no-proto]`；Map → 安全；Object.freeze(Object.prototype) → 安全但注意兼容。

## 编码/解码安全

双重编码绕过、UTF-8 异常、Unicode 正规化差异 — 仅在 Sink 上下文输入链关注。

## 二阶注入（Second-Order）

用户可控数据存入 DB → **后续**在另一上下文被取出用于危险操作，静态分析 Source→Sink 链路断开：
- **二阶 SQLi**：用户名存入 DB → admin 查询用该用户名拼接 SQL → 🔴
- **二阶 SSTI**：用户提交模板字符串存入 DB → 邮件/报告生成时 render → 🔴
- **二阶 Cmd**：文件名存入 DB → 后台 job 用该名拼接命令 → 🔴
- **二阶 XSS**：用户数据存入 DB → admin 面板/日志查看器渲染时无转义 → Stored XSS 🔴（严格说是前端，但 API 返回未净化数据时 backend 有责任）
- **检测**：Phase 1 Path B 追踪到 DB write（`[sink:db_store]`）→ 标记 `[stored-source:pending]`；Phase 2 或 Cross-Shard 追踪该数据的所有读取方是否到达危险 Sink

## LDAP

过滤器拼接用户输入 → 🔴。ldap.filter.filter_format/参数化 → 安全。

## 代码执行

eval(req.*)/new Function(req.*)/vm.runIn + 用户输入 → 🔴。Python: __import__(req)/exec(req) → 🔴。

## XPath 注入

**Sink**：XPath.evaluate/compile/selectNodes/xpath() + 用户输入拼接。
**安全**：XPathVariableResolver 参数化；不可信输入不进 XPath 表达式字符串。
**风险**：布尔盲注（and '1'='1）→ 认证绕过/数据泄露 🔴。

## Groovy / ScriptEngine（Java/JVM）

**Sink**：`GroovyShell.evaluate(userInput)` / `GroovyClassLoader.parseClass()` / `ScriptEngine.eval(userInput)` / `Binding.setVariable()+run()` + 用户可控脚本 → RCE 🔴。
**常见场景**：规则引擎、动态配置、Groovy DSL；低代码平台后端常见。
**安全**：SecureASTCustomizer 白名单（但可绕过，高危仍标 Candidate/Likely）；禁止直接 eval 用户输入。

## Java 特有注入（检测到 Java 时）

SpEL / EL / OGNL / JNDI 注入 → 详见 frameworks-java.md「注入类」。  
JPA / MyBatis / MyBatis-Plus / JDBC SQL 注入 → 详见 frameworks-java.md。

## 不安全反射（Java 等）

| Sink | 风险 |
|------|------|
| `Class.forName(userInput)` | 任意类加载 🔴 |
| `Method.invoke()` 用户可控方法名 | 任意方法调用 🔴 |
| `Constructor.newInstance()` 用户可控类名 | 🔴 |
| 反射得到的 Method/Constructor 调用用户可控参数 | 🔴 |

**安全**：类名/方法名白名单；不可信输入不进入反射 API。
