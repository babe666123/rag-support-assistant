# RAG 智能技术支持问答助手

这是一个面向企业 API 服务平台技术支持场景的 RAG 问答助手。系统会先从本地知识库检索与用户问题相关的文档片段，再把检索结果作为上下文交给 DeepSeek 生成回答，并在前端展示参考来源。

## 项目亮点

- 本地 Markdown 知识库：用 `knowledge_base/` 存放技术支持 FAQ。
- RAG 检索流程：支持文档加载、文本切分、关键词向量化、相似度检索。
- 上下文增强生成：把检索到的资料拼入 system prompt，减少模型凭空回答。
- 来源展示：前端显示回答参考的知识库文件和片段，提升可追溯性。
- 密钥隔离：API Key 只放在后端 `.env`，不会暴露到浏览器。
- 结构化错误提示：对缺少 API Key、网络失败和模型接口错误返回清晰提示。
- 可测试模块：`rag.py` 的核心检索逻辑有 `unittest` 测试覆盖。

## 技术栈

- 前端：HTML、CSS、JavaScript
- 后端：Python `http.server`
- 大模型：DeepSeek Chat Completions API
- 检索：本地 Markdown 文档 + 词频向量 + 余弦相似度
- 测试：Python `unittest`

## 目录结构

```text
.
├── knowledge_base/          # 模拟企业技术支持知识库
├── tests/                   # RAG 检索模块测试
├── index.html               # 页面结构
├── style.css                # 页面样式
├── script.js                # 前端交互和来源展示
├── rag.py                   # 文档切分、检索和相似度计算
├── server.py                # Web 服务、RAG 调用和模型 API 调用
├── .env.example             # 环境变量示例
└── README.md
```

## 运行方式

1. 创建 `.env` 文件：

```text
DEEPSEEK_API_KEY=你的真实 DeepSeek API Key
DEEPSEEK_MODEL=deepseek-chat
```

2. 启动后端服务：

```powershell
python server.py
```

3. 浏览器打开：

```text
http://127.0.0.1:8787
```

## 测试

```powershell
python -m unittest tests.test_rag
```

也可以运行全部测试：

```powershell
python -m unittest discover -s tests
```

## 检索评测

项目提供了一个不需要 API Key 的轻量评测脚本，用于检查典型问题能否命中正确知识库来源：

```powershell
python eval_retrieval.py
```

示例输出：

```text
[PASS] 接口返回 401 怎么办？ -> api-key-and-auth.md, rate-limit-and-timeout.md
[PASS] 403 和 401 有什么区别？ -> api-key-and-auth.md
[PASS] 请求太多返回 429 怎么处理？ -> rate-limit-and-timeout.md, api-key-and-auth.md, billing-and-deployment.md
[PASS] Webhook 没有收到回调怎么办？ -> webhook-and-sync.md, api-key-and-auth.md
[PASS] 本地部署后无法调用模型怎么排查？ -> billing-and-deployment.md

Total: 5, Passed: 5, Failed: 0
```

## 核心接口

### 检索知识库，不调用大模型

这个接口用于验证 RAG 检索是否命中正确资料，不需要 API Key：

```text
POST /api/retrieve
```

请求体：

```json
{
  "question": "接口返回 401 怎么办？"
}
```

返回值会包含命中的知识库来源和片段。

### 检索后调用大模型生成回答

```text
POST /api/chat
```

前端页面会调用这个接口。它需要 `.env` 中配置 `DEEPSEEK_API_KEY`。

## 可尝试的问题

- 接口返回 401 是什么原因？
- 403 和 401 有什么区别？
- 请求太多返回 429 怎么处理？
- Webhook 没有收到回调怎么办？
- 本地部署后无法调用模型怎么排查？

## 简历描述参考

基于 RAG 架构实现企业技术支持知识库问答助手，支持 Markdown 文档加载、文本切分、相似度检索、上下文增强生成和回答来源展示；后端封装 DeepSeek API 调用并隔离 API Key，解决通用大模型无法获取私有业务知识、回答不可溯源的问题。
