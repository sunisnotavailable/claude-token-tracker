# Token Dashboard

A lightweight tool that tracks your Claude Code token usage in real time — without touching your code.

It runs a local HTTP proxy between Claude Code and your API endpoint, silently logs every call to SQLite, and lets you check usage via a terminal command or a Streamlit web dashboard.

![stats preview](https://placeholder.com/stats-preview)

---

## How it works

```
Claude Code  →  localhost:9000 (this proxy)  →  your API endpoint
                        ↓
                  token_usage.db  (SQLite)
                        ↓
              stats.py  /  dashboard.py
```

Claude Code sends requests to the local proxy instead of directly to the API. The proxy forwards everything transparently and logs token counts from the response.

---

## Requirements

- Python 3.9+
- pip

---

## Setup

### 1. Clone and install dependencies

```bash
git clone https://github.com/your-username/token-dashboard.git
cd token-dashboard
pip install -r requirements.txt
```

### 2. Configure your upstream API URL

```bash
cp .env.example .env
```

Edit `.env` and set `UPSTREAM_URL` to wherever Claude Code was originally pointing:

```
# If you use a company/team proxy:
UPSTREAM_URL=https://your-company-proxy.example.com

# If you use Anthropic directly (default):
UPSTREAM_URL=https://api.anthropic.com
```

### 3. Point Claude Code at the local proxy

In `~/.claude/settings.json`, add `ANTHROPIC_BASE_URL` under `env`:

```json
{
  "env": {
    "ANTHROPIC_BASE_URL": "http://localhost:9000"
  }
}
```

This overrides the system environment variable for Claude Code only — nothing else on your machine is affected.

### 4. Start the proxy

```bash
python proxy.py
```

Keep this running in the background while you use Claude Code. From this point on, every conversation is logged.

**Auto-start on boot (Windows):** Create a `.bat` file and drop it in your Startup folder (`Win+R` → `shell:startup`):

```bat
@echo off
start /min "TokenProxy" python C:\path\to\token-dashboard\proxy.py
```

---

## Viewing usage

### Terminal (quick)

```bash
python stats.py          # today
python stats.py week     # last 7 days
python stats.py month    # last 30 days
python stats.py all      # all time
```

Sample output:

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

### Web dashboard

```bash
streamlit run dashboard.py
```

Opens at `http://localhost:8501`. Shows daily trend charts, model breakdown, and a call history table. Auto-refreshes every 30 seconds.

---

## Files

| File | Purpose |
|------|---------|
| `proxy.py` | Local HTTP proxy — the core of the project |
| `db.py` | SQLite helpers (`init_db`, `log_usage`) |
| `stats.py` | Terminal stats script |
| `dashboard.py` | Streamlit web dashboard |
| `.env.example` | Config template |
| `requirements.txt` | Python dependencies |

---

## Privacy

`.env` and `token_usage.db` are in `.gitignore` and will never be committed. Your API keys and usage data stay local.

---

## Troubleshooting

**Claude Code shows API errors after setup**
→ Check that `proxy.py` is running (`python proxy.py` in a terminal). If it's not running, Claude Code can't reach the proxy and all requests will fail.

**No data in stats / dashboard**
→ Confirm `ANTHROPIC_BASE_URL` is set to `http://localhost:9000` in `~/.claude/settings.json`, then restart Claude Code.

**Token counts look wrong**
→ The proxy reads token counts from the API response (`message_start` / `message_delta` SSE events for streaming, `usage` field for non-streaming). If your API endpoint uses a different format, open an issue.

---

## License

MIT
