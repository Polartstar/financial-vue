# TourWise 快速部署指南

## 给你队友的话

**要跑这个项目，需要发给他 3 样东西：**

1. 整个 `tourwise` 文件夹（源代码）
2. 下面这份指南
3. 告诉他装好 Python 3.10+

---

## 一、环境要求

- Windows / macOS / Linux 均可
- Python 3.10 或更高版本（[下载](https://www.python.org/downloads/)）
- 至少 4GB 可用磁盘空间

## 二、安装依赖

打开终端（CMD / PowerShell / Terminal），进入 `tourwise` 目录：

```bash
cd 你的路径/tourwise
pip install -r requirements.txt
```

> 如果下载慢，可以加国内镜像：`pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/`

## 三、初始化知识库

```bash
python run.py --init-kb
```

看到 `[OK] 知识库构建完成！共索引 67 条数据。` 就成功了。

## 四、启动

```bash
python run.py
```

打开浏览器访问 `http://localhost:7860` 即可使用。

## 五、（可选）开启 LLM 增强

如果想要更自然的对话回复，可以装 Ollama：

### 1. 安装 Ollama
访问 https://ollama.com/download 下载安装

### 2. 拉取模型
```bash
ollama pull qwen2.5:1.5b
```

### 3. 修改配置
将 `tourwise/` 下的 `.env.example` 复制为 `.env`（如已有则直接编辑），改成：

```env
LLM_PROVIDER=ollama
OLLAMA_MODEL=qwen2.5:1.5b
```

### 4. 重启
```bash
python run.py
```

---

## 常见问题

**Q: 启动时报端口被占用？**
A: 换个端口：`python run.py --port 7861`

**Q: 界面没响应？**
A: 确保 `pip install` 全部成功，重新运行 `python run.py`

**Q: 提示缺什么模块？**
A: 运行 `pip install -r requirements.txt` 重装依赖

**Q: 没有 GPU 也能跑吗？**
A: 能。LLM 增强需要 Ollama，没有 GPU 也能跑（CPU 模式，会慢一些）。不开 LLM 增强则完全没问题，规则引擎模式不需要 GPU。

---

> 有任何问题直接问我（格温）就行！😊
