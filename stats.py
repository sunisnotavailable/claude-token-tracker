"""
Quick token usage summary. Run:
    python stats.py          # 今日
    python stats.py week     # 本周
    python stats.py month    # 本月
    python stats.py all      # 全部
"""

import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path

DB_PATH = Path(__file__).parent / "token_usage.db"

def main():
    if not DB_PATH.exists():
        print("No data yet.")
        return

    period = sys.argv[1] if len(sys.argv) > 1 else "today"

    now = datetime.now()
    if period == "week":
        since = (now - timedelta(days=7)).isoformat()
        label = "近 7 天"
    elif period == "month":
        since = (now - timedelta(days=30)).isoformat()
        label = "近 30 天"
    elif period == "all":
        since = "2000-01-01"
        label = "全部"
    else:
        since = now.strftime("%Y-%m-%dT00:00:00")
        label = "今日"

    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("""
        SELECT model, COUNT(*), SUM(input_tok), SUM(output_tok)
        FROM usage WHERE ts >= ? GROUP BY model ORDER BY SUM(input_tok + output_tok) DESC
    """, (since,)).fetchall()

    total = conn.execute("""
        SELECT COUNT(*), SUM(input_tok), SUM(output_tok)
        FROM usage WHERE ts >= ?
    """, (since,)).fetchone()
    conn.close()

    if not rows or total[0] == 0:
        print(f"[{label}] 无数据")
        return

    print(f"\n{'='*45}")
    print(f"  Token 用量 · {label}")
    print(f"{'='*45}")
    print(f"  调用次数:  {total[0]}")
    print(f"  输入 token: {total[1]:,}")
    print(f"  输出 token: {total[2]:,}")
    print(f"  总计:      {total[1]+total[2]:,}")
    print(f"{'─'*45}")
    print(f"  {'模型':<40} {'次数':>5} {'token':>10}")
    print(f"  {'─'*40} {'─'*5} {'─'*10}")
    for model, count, inp, out in rows:
        short = model.replace("anthropic/", "").replace("claude-", "")
        print(f"  {short:<40} {count:>5} {inp+out:>10,}")
    print()


if __name__ == "__main__":
    main()
