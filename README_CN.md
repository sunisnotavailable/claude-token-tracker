# Token Dashboard

一个轻量的本地工具，实时追踪你使用 Claude Code 时的 token 消耗 —— 无需修改任何代码。

它在 Claude Code 和你的 API 端点之间运行一个本地 HTTP 代理，静默记录每次调用到 SQLite，并支持通过终端命令或 Streamlit 网页看板查看用量。

---

## 工作原理

```
Claude Code  →  localhost:9000（本地代理）  →  你的 API 端点
                        ↓
                  token_usage.db（SQLite）
                        ↓
              stats.py  /  dashboard.py
```

Claude Code 将请求发送到本地代理，代理透明转发所有请求，并从响应中提取 token 数量记录下来。

---

## 环境要求

- Python 3.9+
- pip

---

## 安装与配置

### 1. 克隆项目并安装依赖

```bash
git clone https://github.com/sunisnotavailable/claude-token-tracker.git
cd claude-token-tracker
pip install -r requirements.txt
```

### 2. 配置上游 API 地址

```bash
cp .env.example .env
```

编辑 `.env`，填入 Claude Code 原来指向的 API 地址：

```
# 公司/团队代理：
UPSTREAM_URL=https://your-company-proxy.example.com

# 直连 Anthropic（默认值）：
UPSTREAM_URL=https://api.anthropic.com
```

### 3. 让 Claude Code 指向本地代理

在 `~/.claude/settings.json` 的 `env` 字段中添加：

```json
{
  "env": {
    "ANTHROPIC_BASE_URL": "http://localhost:9000"
  }
}
```

这只会影响 Claude Code，不会改变系统其他程序的环境变量。

### 4. 启动代理

```bash
python proxy.py
```

使用 Claude Code 期间保持此进程运行，之后每次对话都会被记录。

**Windows 开机自启：** 新建一个 `.bat` 文件，放入启动文件夹（`Win+R` → 输入 `shell:startup`）：

```bat
@echo off
start /min "TokenProxy" python C:\path\to\claude-token-tracker\proxy.py
```

---

## 查看用量

### 终端（快速）

```bash
python stats.py          # 今日
python stats.py week     # 近 7 天
python stats.py month    # 近 30 天
python stats.py all      # 全部
```

示例输出：

```
=============================================
  Token 用量 · 今日
=============================================
  调用次数:  12
  输入 token: 48,302
  输出 token: 6,891
  总计:      55,193
---------------------------------------------
  模型                                     次数      token
  ---------------------------------------- ----- ----------
  opus-4.6                                    12     55,193
```

### 网页看板

```bash
streamlit run dashboard.py
```

访问 `http://localhost:8501`，包含每日趋势图、模型分布、调用明细，每 30 秒自动刷新。

---

## 文件说明

| 文件 | 用途 |
|------|------|
| `proxy.py` | 本地 HTTP 代理，项目核心 |
| `db.py` | SQLite 工具函数（init_db、log_usage） |
| `stats.py` | 终端统计脚本 |
| `dashboard.py` | Streamlit 网页看板 |
| `.env.example` | 配置模板 |
| `requirements.txt` | Python 依赖 |

---

## 隐私说明

`.env` 和 `token_usage.db` 已加入 `.gitignore`，不会被提交。你的 API 密钥和使用数据完全保留在本地。

---

## 常见问题

**配置完之后 Claude Code 报 API 错误**
→ 检查 `proxy.py` 是否在运行（在终端执行 `python proxy.py`）。代理未运行时 Claude Code 无法转发请求，所有调用都会失败。

**stats / dashboard 没有数据**
→ 确认 `~/.claude/settings.json` 中 `ANTHROPIC_BASE_URL` 已设为 `http://localhost:9000`，然后重启 Claude Code。

**token 数量看起来不对**
→ 代理从 API 响应中读取 token 数（流式响应读 `message_start` / `message_delta` SSE 事件，非流式读 `usage` 字段）。如果你的 API 端点格式不同，欢迎提 issue。

---

## 开源协议

MIT
