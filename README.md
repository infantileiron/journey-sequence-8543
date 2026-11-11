# 栖山展馆 · 观展路径顺序复核

为栖山展馆9人策展分析组保留匿名观展顺序，用旅程支持度识别常见子序列，用加权编辑距离复核代表路径与退出差异。

## 场景

展馆原来只看最后触点，重复访问容易抬高频率、跳转顺序被丢弃、退出路径缺少代表样本。本工程接收 `gallery_paths_202611.csv` 匿名路径和触点编码册，替代顺序剖析与复核归档，下游策展组据此讨论展览信息组织。全部路径模拟，不接真实追踪服务，不记录个人身份，不作通道归因或因果推断。

六实体：JourneyDataset旅程数据、TouchpointDictionary触点编码、SequenceStudy挖掘方案、SequenceRun运行、PathReview路径复核、Report报告。六页：路径序册、匿名旅程、触点编码、挖掘方案、模式与对齐、策展复核。PathRibbon、PatternTable、MedoidPanel在总览与结果复用。

## 快速启动

```sh
cp .env.example .env
docker compose up -d --build --wait
docker compose exec -T backend python -m scripts.seed_demo
```

前端 http://localhost:18219 ，后端 http://localhost:19219/docs ，MySQL端口17719。恰好frontend/backend/worker/db/redis五服务及健康检查；数据库、Redis队列和共享导出产物使用命名卷。清理测试数据：`docker compose down -v --remove-orphans`。

| 账号 | 角色 | 权限 |
|---|---|---|
| admin@qishan.test | admin / 策展复核人 | 所有实体、批准/退回、审计 |
| analyst@qishan.test | analyst / 观展分析员 | 编码册、导入、方案、运行、提交复核、生成报告 |
| viewer@qishan.test | viewer / 展务观察员 | 六实体只读及批准报告下载 |

统一演示密码 `Gallery2026!`。JWT HS256、PBKDF2口令哈希、actor审计、全局错误响应、队列10任务配额。匿名401、写入越权403、重复复核409。开发密钥可用JWT_SECRET配置。

## 一天的工作剧本

1. 09:00 登录，核对700条匿名路径的转化/退出分组人数。
2. 09:05 检查六触点编码：ENTRY入口、INTRO序厅、MAIN主展厅、SIDE侧展廊、WORKSHOP体验室、SHOP纪念区。
3. 09:10 上传gallery_paths_202611.csv，保留上传文件名；校验重复ID、空路径与未知触点。
4. 09:15 设旅程支持度0.10、最长模式3、折叠连续重复，保存方案。
5. 09:20 Redis排队，独立Python worker运行PrefixSpan与缓存编辑距离，结果持久化MySQL及共享产物。
6. 09:25 对照常见有序子序列、转化/退出组支持差及按原始频数加权的代表路径。
7. 09:30 查看高频退出路径与最近成功路径的编辑操作，核查插入/删除/替换成本闭合。
8. 09:40 提交解释边界，策展复核人批准后生成报告，观察员下载CSV用于策展讨论。

## 输入与限制

CSV列 `journey_id,path,outcome`，路径用 `>` 分隔，终态仅converted/exited。每条路径1—20触点，最多2000旅程；编码册2—8个唯一大写编码。空路径、未知触点、重复旅程ID、缺字段和CSV短行明确返回422。连续重复折叠只移除相邻重复，ENTRY>MAIN>SIDE>MAIN中的返回保留。

最多160种唯一归一序列，超出则worker记录明确failed，请缩小样本/分组；模式最长4、候选上限6000、报告保存前200模式，最多12条高频退出序列对齐。模式排序按支持计数降序、长度降序、编码字典序；界面明确总模式数、截断状态与预览范围。

## PrefixSpan口径

采用前缀增长与投影后缀。每个投影旅程只保留能完成当前前缀的最早结束位置；对每个扩展符号，一条旅程最多贡献一次支持，重复出现不会重复计数。子序列允许中间跳过触点，并非连续片段；[A,X,B]包含[A,B]。

支持度=包含该有序子序列的旅程数/N。最小计数使用 `Decimal(str(min_support))*N` 向上取整，避免0.14×50的二进制浮点误差。转化组和退出组分别按该组旅程数计算支持度，差值=转化支持度−退出支持度。某组无路径时该支持度和差值为空，不当作0或因果效应。

## 编辑距离与代表序列

Levenshtein插入/删除/替换成本1，保留成本0。相同唯一序列合并计频，距离按两个唯一序列对称缓存；medoid最小化Σ(其他序列原始旅程频数×编辑距离)。不是对唯一序列等权。medoid目标值平局按编码序列字典序。

每个高频退出序列选择编辑距离最近的成功序列；同距离先取成功组频数高者，再按编码字典序。对齐回溯优先保留、替换、删除、插入，非保留操作数必须等于编辑距离。没有成功组时不虚构参考路径。退出对齐不承诺提高转化，也不是推荐个体行动的策略。

结果含模式与分母、代表序列/加权目标、距离缓存对数、对齐操作、折叠口径与输入SHA256。只有引用该运行批准复核的报告可导出；CSV含全部展示范围内模式、代表序列和对齐，文本公式前缀保护。

## 技术与结构

| 层 | 技术 |
|---|---|
| 前端 | Vue3.5 / TypeScript5.7 / Vite6 / Nginx1.28 |
| 后端 | Python3.12 / FastAPI / PyMySQL |
| 算法 | Python标准库PrefixSpan、Levenshtein、频数加权medoid |
| 存储与异步 | MySQL8.4 / Redis7.4 / 独立Python worker |

`frontend/src/{api,stores,types,components/common,hooks,pages,router,utils,constants}` 和 `backend/src/{routes,controllers,services,models,schemas,middlewares,utils,constants,config}` 分离职责，77职责源文件。业务表为VARCHAR主键+LONGTEXT JSON，避免700路径和结果超过64KB时被截断；DDL在backend/migrations/001_initial.sql，GET_LOCK保护首次并发建表。

枚举位置：后端src/constants/enums.py（角色/运行/复核）与src/constants/domain.py（终态/配额）；前端src/constants/enums.ts（角色、状态、终态、操作）。数据类型对应models/entities.py、schemas/entities.py、frontend/src/types/entities.ts。

Seed固定2210，700旅程、六触点、12种折叠后的顺序，部分原始路径带连续重复，有转化与退出终态；两种顺序仅在退出组出现，展示非零编辑对齐。SEED_DEMO=true自动执行，自然键insert-only，两次seed不新增且保留手工修改；失败记录日志。前端npm ci使用锁定依赖。

环境变量DATABASE_URL、REDIS_URL、JWT_SECRET、SEED_DEMO、TASK_MODE、ARTIFACT_DIR及端口/口令见.env.example。后端本地开发安装requirements后配置MySQL/Redis，运行`uvicorn src.main:app --reload`；前端`npm ci && npm run dev`，Vite把/api代理localhost:19219。

## 边界

模拟顺序只作描述，不推断因果或通道贡献。代表路径不保证对每个人适用。Redis出队后worker强杀没有自动重投，需要重提；业务JSON文本没有多人编辑乐观锁或迁移回滚。默认账号仅本地演示。

真实容器、权限、算法、浏览器上传与主流程、桌面/响应式截图证据在批次test-artifacts/gb-2210，源码不含截图、日志或TESTING报告。

## License

MIT，见LICENSE。
