"""
Local proxy server for Claude Code token tracking.

Sits between Claude Code and the upstream API endpoint.
Forwards all requests transparently, and logs token usage from responses.

Configuration:
    Set UPSTREAM_URL in a .env file or as an environment variable:
        UPSTREAM_URL=https://your-company-proxy.example.com

    Then point Claude Code at this proxy:
        ANTHROPIC_BASE_URL=http://localhost:9000  (in .claude/settings.json)

Usage:
    python proxy.py
"""

import json
import os
import sys
from flask import Flask, request, Response
import requests as http_requests

from db import init_db, log_usage

# Load .env if present (pip install python-dotenv, or set env var directly)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

TARGET_BASE = os.environ.get("UPSTREAM_URL", "https://api.anthropic.com")
app = Flask(__name__)

init_db()


@app.route("/<path:path>", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
def proxy(path):
    target_url = f"{TARGET_BASE}/{path}"

    # Copy headers, remove Host (will be set by requests library)
    headers = dict(request.headers)
    headers.pop("Host", None)

    resp = http_requests.request(
        method=request.method,
        url=target_url,
        headers=headers,
        data=request.get_data(),
        params=request.args,
        stream=True,
        timeout=300,
    )

    content_type = resp.headers.get("Content-Type", "")

    # Streaming response (SSE) — Anthropic uses event-stream for /v1/messages
    if "text/event-stream" in content_type:
        input_tokens = 0
        output_tokens = 0
        model_name = "unknown"

        def generate():
            nonlocal input_tokens, output_tokens, model_name
            for chunk in resp.iter_content(chunk_size=None):
                yield chunk
                # Try to extract token info from each chunk
                try:
                    text = chunk.decode("utf-8", errors="ignore")
                    for line in text.splitlines():
                        if not line.startswith("data: "):
                            continue
                        payload = line[6:].strip()
                        if not payload or payload == "[DONE]":
                            continue
                        data = json.loads(payload)
                        msg_type = data.get("type", "")

                        # message_start contains input_tokens and model
                        if msg_type == "message_start":
                            msg = data.get("message", {})
                            model_name = msg.get("model", model_name)
                            usage = msg.get("usage", {})
                            input_tokens = usage.get("input_tokens", 0)

                        # message_delta contains output_tokens
                        elif msg_type == "message_delta":
                            usage = data.get("usage", {})
                            output_tokens = usage.get("output_tokens", output_tokens)

                except Exception:
                    pass

            # Stream ended — log totals
            if input_tokens > 0 or output_tokens > 0:
                log_usage(model=model_name, input_tok=input_tokens, output_tok=output_tokens)
                print(f"[LOG·stream] {model_name} | in={input_tokens} out={output_tokens}", flush=True)

        response_headers = _filter_headers(resp.headers)
        return Response(generate(), status=resp.status_code, headers=response_headers)

    # Non-streaming response — parse JSON directly
    body = resp.content
    _log_from_body(body)

    response_headers = _filter_headers(resp.headers)

    return Response(body, status=resp.status_code, headers=response_headers)


def _filter_headers(headers):
    excluded = {"content-encoding", "content-length", "transfer-encoding", "connection"}
    return {k: v for k, v in headers.items() if k.lower() not in excluded}


def _log_from_body(body):
    """Extract usage from a non-streaming Anthropic JSON response."""
    if b"usage" not in body:
        return
    try:
        data = json.loads(body)
        usage = data.get("usage", {})
        model = data.get("model", "unknown")
        # Anthropic format
        input_tok = usage.get("input_tokens", 0)
        output_tok = usage.get("output_tokens", 0)
        if input_tok > 0 or output_tok > 0:
            log_usage(model=model, input_tok=input_tok, output_tok=output_tok)
            print(f"[LOG] {model} | in={input_tok} out={output_tok}", flush=True)
    except Exception as e:
        print(f"[WARN] Failed to parse response: {e}", file=sys.stderr)


if __name__ == "__main__":
    print("=" * 50)
    print("Token Tracking Proxy")
    print("=" * 50)
    print(f"Listening on:   http://localhost:9000")
    print(f"Forwarding to:  {TARGET_BASE}")
    print(f"Dashboard:      streamlit run dashboard.py")
    print("=" * 50)
    app.run(host="127.0.0.1", port=9000, threaded=True)
