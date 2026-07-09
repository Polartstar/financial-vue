# TourWise — 智能文旅行程规划助手

> 基于 Agent 技术的智慧文旅系统 | 软件架构大作业

## 📋 项目概述

TourWise 是一款融合**智能体（Agent）技术**的智慧文旅行程规划助手。它突破传统固定攻略/简单问答模式，具备**意图识别、自主任务拆解、RAG知识库检索、多轮对话记忆**等核心智能体能力，为用户提供一站式的文旅规划体验。

### 🎯 聚焦场景：智能文旅行程规划

用户输入自然语言需求（如"帮我规划一个3天北京游，预算3000"），系统自动：
1. **识别意图**：识别为 `plan_trip` 行程规划需求
2. **拆解任务**：拆解为景点筛选→路线编排→美食推荐→预算估算→行程生成
3. **检索知识**：从 RAG 知识库中检索相关景点、美食、贴士
4. **迭代优化**：记下用户偏好，支持根据反馈动态调整

## 🧠 智能体核心能力

| 能力 | 实现方式 | 对应模块 |
|------|---------|---------|
| (1) **用户意图自主识别** | 基于 LLM + 规则混合的意图分类器 | `app/agent/intent_recognizer.py` |
| (2) **自主任务拆解与推理** | 状态机驱动的多步任务规划与执行引擎 | `app/agent/task_planner.py` |
| (3) **RAG知识库检索增强** | ChromaDB 向量数据库 + 语义检索 | `app/rag/` |
| (4) **多轮对话记忆迭代** | 基于会话的层级记忆系统（短期对话+长期偏好） | `app/agent/memory.py` |

## 🏗️ 系统架构

```
用户输入
    │
    ▼
┌─────────────────────┐
│  Intent Recognizer  │  ← 意图识别（能力1）
│  (LLM/Rule Hybrid)  │
└────────┬────────────┘
         │ intent + entities
         ▼
┌─────────────────────┐
│  Context Enricher   │  ← 加载记忆 + 检索RAG
│  (Memory + RAG)     │
└────────┬────────────┘
         │ enriched context
         ▼
┌─────────────────────┐
│  Task Planner       │  ← 任务拆解（能力2）
│  (Sub-task Engine)  │     → 复杂需求拆为多步
└────────┬────────────┘
         │ sub-tasks
         ▼
┌─────────────────────┐
│  Sub-task Executor  │  ← 执行子任务
│  (RAG/Calculator)   │     → 检索/计算/编排
└────────┬────────────┘
         │ results
         ▼
┌─────────────────────┐
│  Response Synthesiz│  ← 生成自然回复
└────────┬────────────┘
         ▼
┌─────────────────────┐
│  Memory Updater     │  ← 保存记忆（能力4）
│  (Preferences+Hist) │
└─────────────────────┘
         │
         ▼
     用户输出
```

## 🚀 快速开始

### 1. 安装依赖

```bash
cd tourwise
pip install -r requirements.txt
```

### 2. 配置 LLM（可选）

复制 `.env.example` 为 `.env`，按需配置：

```env
# 可选：使用 Ollama 本地模型（推荐）
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2:7b

# 可选：使用阿里云 DashScope（通义千问）
# LLM_PROVIDER=dashscope
# DASHSCOPE_API_KEY=your-key-here

# 可选：使用 OpenAI 兼容接口
# LLM_PROVIDER=openai
# OPENAI_API_KEY=your-key-here
# OPENAI_BASE_URL=https://api.openai.com/v1
```

> **未配置 LLM 时，系统自动使用规则引擎模式**，仍可完整演示所有 Agent 能力。

### 3. 初始化知识库

```bash
python run.py --init-kb
```

### 4. 启动系统

```bash
python run.py
```

启动后访问 `http://localhost:7860` 打开 Gradio 对话界面。

## 💬 对话示例

### 场景1：行程规划（完整的多步任务拆解）

```
用户：帮我规划一个3天北京游，预算3000，带父母

系统：[意图识别] plan_trip
      [任务拆解] ①筛选适合老人的景点 ②编排3天路线 ③推荐美食 ④预算分配
      [知识检索] 从知识库检索北京景点/美食信息
      [生成] 输出完整行程表 + 预算明细
```

### 场景2：景点咨询（RAG检索）

```
用户：故宫的门票多少钱？什么时候去比较好？

系统：[意图识别] query_attraction
      [知识检索] 从RAG检索故宫信息
      [生成] 门票价格 + 最佳游览时间 + 游览建议
```

### 场景3：多轮迭代（记忆能力）

```
用户：我想去成都玩
系统：建议3天行程...

用户：预算只有2000
系统：[记忆：读取用户之前的兴趣偏好]
      [调整：重新编排更经济的方案]
      [生成] 调整后的成都经济游方案
```

## 📁 项目结构

```
tourwise/
├── run.py                     # 启动入口
├── requirements.txt           # 依赖
├── .env.example               # 环境变量模板
├── app/
│   ├── __init__.py
│   ├── config.py              # 配置管理
│   ├── main.py                # FastAPI 入口
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── intent_recognizer.py   # 意图识别（能力1）
│   │   ├── task_planner.py        # 任务拆解与执行（能力2）
│   │   ├── travel_agent.py        # Agent 主控（编排）
│   │   └── memory.py              # 多轮记忆系统（能力4）
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── embedder.py            # 嵌入模型
│   │   ├── vector_store.py        # 向量库（能力3）
│   │   ├── knowledge_base.py      # 知识库管理
│   │   └── data/
│   │       ├── attractions.json   # 景点数据
│   │       ├── cuisine.json       # 美食数据
│   │       └── travel_tips.json   # 旅行贴士
│   └── web/
│       ├── __init__.py
│       └── interface.py           # Gradio 界面
└── data/
    └── chroma_db/                 # 持久化向量库
```

## 🔬 技术栈

- **Python 3.10+** — 核心开发语言
- **LangChain / LangGraph** — Agent 编排框架
- **ChromaDB** — 向量数据库（RAG）
- **Sentence-Transformers** — 语义嵌入
- **Gradio** — Web 交互界面
- **FastAPI** — 后端 API
- **Ollama / DashScope / OpenAI** — LLM 后端（可选）

## 📊 项目亮点

1. ✅ **纯 Agent 架构**：非简单对话机器人，具备自主推理能力
2. ✅ **完整的 RAG 管线**：知识库构建→嵌入→检索→增强生成
3. ✅ **层级记忆系统**：短期对话记忆 + 长期偏好记忆
4. ✅ **混合意图识别**：LLM 精确分类 + 规则兜底
5. ✅ **多步任务编排**：复杂需求自动拆解为子任务链
6. ✅ **模块化设计**：各组件独立，可替换、可扩展
