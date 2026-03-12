# Grep Patterns — BSAF v3.6

> Phase 0 §0.2 加载。按场景取子集。噪声标注：低<20%/中20-50%/高>50%。

## Core（始终加载）

### SQL 注入 (Node) [噪声:低]
\.query\(.*\$\{|\.query\(.*\+|sequelize\.query\(|\.raw\(|\.execute\(.*\+|sequelize\.literal|knex\.raw|\.whereRaw\(|\$queryRaw[^`]|\$executeRaw[^`]|createQueryBuilder\(.*\.where\(.*\+|better-sqlite3.*\.exec\(.*\+

### SQL 注入 (Python) [噪声:低]
cursor\.execute\(.*%|cursor\.execute\(.*\.format|cursor\.execute\(.*f['""]|\.raw\(|\.extra\(|text\(.*%|text\(.*\.format|text\(.*f['""]|RawSQL\(

### 命令注入 (Node) [噪声:中]
child_process|exec\(|execSync\(|spawn\(.*shell|execFile\(|fork\(.*req\.|\.exec\(.*\$\{|\.exec\(.*\+|shelljs|execa\(.*req\.

### 命令注入 (Python) [噪声:中]
os\.system\(|os\.popen\(|subprocess\.\w+\(.*shell\s*=\s*True|eval\(.*req|exec\(.*req

### SSRF [噪声:中]
fetch\(.*req\.|axios[\.(].*req\.|got\(.*req\.|request\(.*req\.|new URL\(.*req\.|url\.parse\(.*req\.|requests\.(get|post|put|delete|patch)\(.*req\.|httpx\.\w+\(.*req\.|node-fetch|aiohttp\.ClientSession

### 凭证 [噪声:中]
(?:password|secret|key|token|credential|api.?key)\s*[:=]\s*['"][^'"]{8,}|(?:AWS_SECRET|PRIVATE_KEY|DATABASE_URL)\s*=\s*['"]

### 路由注册 [噪声:—]
app\.use\(|router\.use\(|fastify\.register|include_router|register_blueprint|urlpatterns|APIRouter\(|new Elysia\(|new Hono\(|defineEventHandler\(

### 动态 require/import [噪声:中]
require\(.*req\.|require\(.*param|import\(.*req\.|require\(.*query|require\(.*body

## Extended（按 Sink 类型）

### NoSQL [噪声:高]
\.find\(.*req\.|\.findOne\(.*req\.|\.aggregate\(.*req\.|\$where|\$ne|\$gt|\$regex.*req\.|collection\.\w+\(.*req\.body

### 路径遍历 [噪声:中]
readFile\(.*req\.|sendFile\(.*req\.|\.download\(.*req\.|fs\.\w+\(.*req\.|open\(.*req|send_file\(.*req

### 文件上传 [噪声:—]
multer|formidable|busboy|express-fileupload|request\.files|FileInterceptor|UploadedFile

### SSTI [噪声:低]
render_template_string|Template\(.*req|ejs\.render\(.*req|pug\.render\(.*req|nunjucks.*renderString

### 反序列化 [噪声:低]
node-serialize|pickle\.load|yaml\.load\((?!.*safe)|torch\.load\(

### XXE [噪声:中]
parseString|xml2js|xmldom|DOMParser|etree\.parse|lxml.*parse

### Prototype Pollution [噪声:低]
lodash\.merge|_\.merge|_\.defaultsDeep|_\.set\(|deepmerge|deep-extend|dot-prop|object-path|set-value|dset|__proto__|constructor\[

### 随机性/Crypto [噪声:中]
Math\.random|random\.random|Date\.now\(\).*(?:token|session|id|key)|uuid\.v1|createCipher\(|MD5|SHA1.*password

### 时序 [噪声:中]
===.*(?:secret|token|password|key|hash)|strcmp\(.*(?:secret|token|hash)

### ReDoS [噪声:中]
new\s+RegExp\(.*req\.|\.match\(.*req\.|\.test\(.*req\.

### Email [噪声:低]
sendMail\(|send_mail\(|nodemailer|smtplib

## Protocol（GraphQL/WS/gRPC 时）

### GraphQL [噪声:—]
graphql|apollo-server|type-graphql|@nestjs\/graphql|depthLimit|costAnalysis|introspection

### WebSocket [噪声:—]
ws\(|new WebSocket|socket\.io|\.on\('connection|wss\.

### gRPC [噪声:—]
grpc|\.proto|grpc-js|add_insecure_port|reflection

### HTTP Smuggling [噪声:高]
transfer\.encoding|chunked|Upgrade.*h2c|Content-Length.*Content-Length

## AI（检测到 AI 库时）[噪声:低]

openai|anthropic|langchain|llama-index|cohere|ChatCompletion|messages.*role.*content|AgentExecutor|create_react_agent|bind_tools\(|chromadb|pinecone|torch\.load\(|pickle\.load\(|mcp|@modelcontextprotocol

## Aux（Path C 时）

### 认证/授权 [噪声:—]
isAuthenticated|requireAuth|@UseGuards|@Roles|@Public|login_required|permission_required|AllowAny|jwt\.verify|passport\.|@SkipAuth

### Mass Assignment [噪声:中]
\.create\(req\.body|\.update\(req\.body|Object\.assign\(.*req\.body|serializer.*req\.data|\*\*request\.data

### Session/Cookie [噪声:—]
cookie|set-cookie|sameSite|httpOnly|secure|__Host-|__Secure-

### 环境分支 [噪声:—]
NODE_ENV|FLASK_DEBUG|DEBUG\s*=\s*True|app\.debug

### 配置/Secret 读取入口 [噪声:中]
process\.env\.|os\.environ|System\.getenv\(|Environment\.getProperty\(|@Value\(|config\.get\(|getSecret\(|Vault\.read

### Swagger [噪声:—]
swagger|openapi|api-docs|redoc|SwaggerModule

### 竞态 [噪声:极高]
(?:balance|inventory|stock|quota).*(?:update|save|increment)|FOR UPDATE|advisory.*lock

### 排序/过滤参数注入 [噪声:中]
ORDER\s+BY\s+\$\{|ORDER\s+BY\s+.*\+|GROUP\s+BY\s+.*\+|SELECT\s+\$\{|orderBy.*req\.|sort.*req\.query|sortBy.*req\.params

### HTTP Method Override [噪声:低]
x-http-method-override|x-http-method|_method.*req\.|HiddenHttpMethodFilter|methodOverride\(

### 文件类型混淆 [噪声:低]
Content-Disposition.*inline|res\.setHeader.*Content-Type.*svg|res\.setHeader.*Content-Type.*html.*upload|sendFile.*\.svg|sendFile.*\.html

### Webhook [噪声:—]
/webhook|verifySignature|stripe\.webhooks\.constructEvent|x-hub-signature

### SSRF 云 Metadata [噪声:—]
169\.254\.169\.254|metadata\.google|metadata\.azure|fd00:ec2::254

### SSRF 渲染 [噪声:—]
puppeteer|playwright|wkhtmlto|phantom|weasyprint

### 编码对抗 [噪声:高]
eval\(|new Function\(|String\.fromCharCode|\\x65\\x76\\x61\\x6c

### PII [噪声:高]
\.(ssn|phone|creditCard|idCard)\s*[=:]|logger\.\w+\(.*(user|req\.body)

## Java（检测到 pom.xml/build.gradle 时加载）

### SQL 注入 (Java) [噪声:低]
createQuery\(.*\+|createNativeQuery\(.*\+|JdbcTemplate.*\+.*query|\.query\(.*\+|\.update\(.*\+|StringBuilder.*append.*WHERE|String\.format\(.*SELECT|\$\{.*\}.*xml|nativeQuery.*true.*\+

### MyBatis ${} 注入 [噪声:低]
\$\{(?!.*#\{)

### SpEL 注入 [噪声:中]
SpelExpressionParser|parseExpression\(|ExpressionParser|StandardEvaluationContext|@Value\(.*#\{.*req|@PreAuthorize\(.*\+

### JNDI 注入 [噪声:低]
InitialContext\(\)|\.lookup\(|JndiTemplate|JndiObjectFactoryBean

### 反序列化 (Java) [噪声:低]
ObjectInputStream|readObject\(|XMLDecoder|enableDefaultTyping|DefaultTyping|JsonTypeInfo.*CLASS|Fastjson|JSON\.parse|autoType|SnakeYAML|XStream\.fromXML|readUnshared

### SSRF (Java) [噪声:中]
RestTemplate.*\+|WebClient\.create\(.*req|new URL\(.*req|HttpURLConnection|OkHttpClient.*req|HttpClient.*req|Jsoup\.connect\(.*req

### 路径遍历 (Java) [噪声:中]
new File\(.*req|Paths\.get\(.*req|getOriginalFilename|transferTo\(|ResourceLoader.*getResource\(.*req

### Spring Security 配置 [噪声:—]
SecurityFilterChain|WebSecurityConfigurerAdapter|authorizeHttpRequests|authorizeRequests|\.permitAll|\.authenticated|\.hasRole|\.hasAuthority|csrf\(\)\.disable|@PreAuthorize|@Secured|@RolesAllowed

### Actuator [噪声:—]
management\.endpoints|actuator|\.exposure\.include

### Mass Assignment (Java) [噪声:中]
@RequestBody.*(?:Entity|Model|Domain)|save\(.*@RequestBody|FAIL_ON_UNKNOWN_PROPERTIES.*false|@JsonIgnoreProperties

### 模板注入 (Java) [噪声:低]
__\$\{|th:utext|freemarker|velocity|TemplateUtils|process\(.*template

### 不安全随机 (Java) [噪声:中]
new Random\(\)|Math\.random|ThreadLocalRandom(?!.*Secure)

### 凭证 (Java) [噪声:中]
spring\.datasource\.password|spring\.redis\.password|spring\.mail\.password|secret.*=.*["'][^"']{8,}

### 命令注入 (Java) [噪声:低]
Runtime\.getRuntime\(\)\.exec|ProcessBuilder.*req|\.command\(.*req

### XXE (Java) [噪声:中]
DocumentBuilderFactory|SAXParserFactory|XMLInputFactory|TransformerFactory|SchemaFactory|FEATURE.*external|XMLReader|SAXReader

### Shiro [噪声:低]
ShiroFilterFactoryBean|filterChainDefinitionMap|anon|authc|perms\[|roles\[|SecurityManager|Subject\.get|doGetAuthorizationInfo

### WebSocket STOMP [噪声:—]
@MessageMapping|@SubscribeMapping|@SendTo|StompEndpoint|registerStompEndpoints|configureMessageBroker|SimpleBroker|StompBrokerRelay

### Content Negotiation [噪声:中]
MappingJackson2XmlHttpMessageConverter|Jaxb2RootElementHttpMessageConverter|ContentNegotiationConfigurer|application/xml

### DevTools [噪声:—]
spring-boot-devtools|devtools\.remote\.secret|LiveReloadServer

### Spring Profiles [噪声:—]
@Profile|spring\.profiles\.active|@ConditionalOnProperty.*security|@ConditionalOnProperty.*enabled

### Spring Cache [噪声:中]
@Cacheable|@CacheEvict|@CachePut|CacheManager|RedisCacheConfiguration|CaffeineCacheManager

### Spring GraphQL [噪声:—]
@QueryMapping|@MutationMapping|@SchemaMapping|@SubscriptionMapping|GraphQlSource|spring-graphql|DataFetcher

### JPA 二级缓存 [噪声:—]
use_second_level_cache|CacheConcurrencyStrategy|@org\.hibernate\.annotations\.Cache

### MyBatis-Plus 注入 [噪声:低]
\.apply\(.*\+|\.last\(.*\+|\.orderByAsc\(.*req|\.orderByDesc\(.*req|\.exists\(.*\+|\.having\(.*\+

### Filter/Interceptor [噪声:—]
OncePerRequestFilter|GenericFilterBean|HandlerInterceptor|preHandle|addInterceptor|FilterRegistrationBean|shouldNotFilter

### Spring Data REST [噪声:—]
spring-boot-starter-data-rest|@RepositoryRestResource|RepositoryRestConfiguration

### @Scheduled/@Async [噪声:—]
@Scheduled|@Async|@EnableScheduling|@EnableAsync|MODE_INHERITABLETHREADLOCAL

### @Transactional [噪声:中]
@Transactional(?!.*rollbackFor)|this\.\w+\(.*@Transactional|private.*@Transactional

### Singleton 可变状态 [噪声:高]
@Controller|@Service|@Component|@Repository

### Nacos/Sentinel [噪声:—]
nacos|sentinel|@RefreshScope|@SentinelResource

### Spring Cloud Stream [噪声:—]
@StreamListener|spring-cloud-stream|spring\.cloud\.stream|Consumer<Message

### Lombok [噪声:—]
@Data|@ToString|@Builder|@AllArgsConstructor|@NoArgsConstructor

### Virtual Threads [噪声:—]
spring\.threads\.virtual|newVirtualThreadPerTaskExecutor|VirtualThread|ScopedValue

### Spring AI [噪声:—]
spring-ai|ChatClient|@Tool|VectorStore|ChatMemory|FunctionCallback

### 不安全反射 [噪声:中]
Class\.forName\(|\.getMethod\(.*req|\.getDeclaredMethod\(.*req|Method\.invoke\(|Constructor\.newInstance\(.*req

### 开放重定向 (Java) [噪声:中]
redirect:.*getParameter|RedirectView\(|sendRedirect\(.*req|ModelAndView.*redirect:

### XPath 注入 [噪声:中]
\.evaluate\(.*req\.|XPath\.compile\(.*\+|selectNodes\(.*req\.|xpath\(.*req\.|XPathExpression.*\+|DOMXPath

### Groovy/ScriptEngine 执行 [噪声:低]
GroovyShell|GroovyClassLoader|ScriptEngine.*eval|new GroovyShell|parseClass\(|Binding\(\).*setVariable

### H2 Console [噪声:低]
h2-console\.enabled|CALL\s+SHELLEXEC|H2ConsoleAutoConfiguration|h2:mem:|h2:file:

### Host Header 注入 [噪声:中]
getHeader\("Host"\)|getHeader\("X-Forwarded-Host"\)|req\.headers\[.host.\]|req\.hostname.*resetLink|X-Forwarded-Host.*url

### SAML [噪声:低]
SAMLResponse|SAMLRequest|NameID|InResponseTo|xml-crypto|passport-saml|spring-security-saml|opensaml|SAMLObject

### 解压炸弹 [噪声:中]
ZipInputStream|ZipFile|TarArchiveInputStream|GZIPInputStream|Inflater|zipfile\.ZipFile|tarfile\.open|node-tar|adm-zip|yauzl

### Dubbo [噪声:—]
dubbo|RpcContext|Hessian2|Kryo\.|@DubboReference|@DubboService

### Spring Authorization Server [噪声:—]
spring-authorization-server|RegisteredClientRepository|OAuth2AuthorizationServer

### Jakarta 校验 [噪声:—]
javax\.validation\.|jakarta\.validation\.|@Valid|@Validated

### Sa-Token [噪声:低]
SaRouter|StpUtil|@SaCheckLogin|@SaCheckRole|@SaCheckPermission|sa-token-spring

### Remember-Me [噪声:—]
rememberMe|RememberMeAuthenticationFilter|PersistentTokenRepository|rememberMeKey|AbstractRememberMeServices

### Spring Boot Admin [噪声:—]
spring-boot-admin|@EnableAdminServer|AdminServerAutoConfiguration|SpringBootAdminClient

### 嵌入式服务器配置 [噪声:—]
relaxed-path-chars|relaxed-query-chars|allow-encoded-slash|sendServerVersion|server\.tomcat\.|server\.undertow\.|server\.jetty\.

### LDAP (Java) [噪声:低]
LdapTemplate.*search|DirContext.*search|SpringSecurityLdapTemplate|LdapQueryBuilder|ldap\.search|NamingException

### Padding Oracle / CBC [噪声:中]
AES.*CBC|Cipher\.getInstance.*CBC|CipherMode\.CBC|PKCS5Padding|PKCS7Padding|BadPaddingException|IllegalBlockSizeException

### 解压炸弹 Java 特化 [噪声:低]
commons-compress|TarArchiveEntry|ZipArchiveInputStream|ZipArchiveEntry.*getSize|ArArchiveInputStream

### Cache Poisoning [噪声:低]
X-Forwarded-Host.*url|X-Original-URL|X-Rewrite-URL|Vary.*Origin|Cache-Control.*no-store|cache.*key.*host

### 二阶注入标记 [噪声:高]
repository\.save\(|\.save\(.*req\.|\.create\(.*req\.|\.insert\(.*req\.|entityManager\.persist\(.*req\.

### 整数溢出 (Node/Java) [噪声:中]
parseInt\(.*req\.|Number\(.*req\.|quantity.*req\.|amount.*req\.|price.*req\.|\.intValue\(\).*req\.|Math\.abs\(.*req\.

### 错误响应信息泄露 [噪声:中]
error\.stack|err\.stack|error\.message.*res\.|err\.message.*res\.|\.send\(err\)|\.json\(error\)|stack.*trace.*response|SQLException.*message|NullPointerException.*response

### 注释中的凭证 [噪声:高]
#\s*(?:password|key|secret|token|api_key)\s*[:=]\s*\S|//\s*(?:password|key|secret|token)\s*[:=]\s*\S|/\*.*(?:password|key|secret)\s*[:=]\s*\S

### 认证类型混淆 (Node) [噪声:中]
token\s*==\s|password\s*==\s|token\s*==\s*null|token\s*==\s*undefined|typeof.*token\s*!==\s*['""]string|jwt.*==\s

### 未验证重定向 (Location Header) [噪声:中]
res\.set\(\s*['"]location|res\.header\(\s*['"]location|Location:.*req\.|redirectUrl.*req\.|returnUrl.*req\.|redirect_uri.*req\.

### Next.js 不安全重定向 [噪声:低]
redirect\(.*req\.|redirect\(.*query\.|redirect\(.*params\.|getServerSideProps.*redirect|permanentRedirect\(.*req\.

### HTTP/2 配置 [噪声:—]
http2|h2c|allowHTTP1|maxConcurrentStreams|Http2Server|http2\.createServer|server\.http2

### Java 反序列化 gadget 依赖 [噪声:低]
commons-collections|commons-beanutils|rome.*jar|xalan|ysoserial|SerialKiller|jdk\.serialFilter|readObjectNoData
