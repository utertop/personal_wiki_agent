# Personal Wiki Agent Backend

Personal Wiki Agent 后端使用 FastAPI 构建，当前阶段只提供最小项目骨架和健康检查接口。

## 本地开发

当前项目目标运行环境为 Python 3.11+。如果本机只有旧版本 Python，可以先安装 Python 3.11 或更高版本后再创建虚拟环境。

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m pytest -v
```

## 启动 API

```powershell
cd backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

健康检查接口：

```text
GET /health
```

期望响应：

```json
{"status": "ok"}
```
