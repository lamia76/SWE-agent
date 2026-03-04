#!/usr/bin/env python3
"""
OpenViking Proxy Server - runs on the host to bridge SWE-agent container and OpenViking.

Usage:
  1. Ensure OpenViking/bot is in PYTHONPATH:
     export PYTHONPATH="/path/to/OpenViking/bot:$PYTHONPATH"

  2. Run the server:
     python proxy_server.py [--port 8765] [--host 0.0.0.0]

  3. In SWE-agent config, add openviking_proxy bundle and set:
     OPENVIKING_PROXY_URL=http://host.docker.internal:8765  (Docker Desktop)
     or
     OPENVIKING_PROXY_URL=http://172.17.0.1:8765  (Linux Docker host IP)

Config: OpenViking SDK (used by VikingClient) reads OPENVIKING_CONFIG_FILE.
If unset, we set it to this bundle's ov.conf.third_party_api so it behaves like
tools/openviking loading ov.conf (same mechanism: env var -> get_openviking_config()).
"""
import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread

# 与 tools/openviking 一致：让 OpenViking SDK 通过 OPENVIKING_CONFIG_FILE 加载配置。
# SDK 在 get_openviking_config() 中读取该环境变量（openviking_cli.utils.config），
# 若未设置则在此处默认指向本 bundle 的 ov.conf.third_party_api。
if not os.environ.get("OPENVIKING_CONFIG_FILE"):
    _bundle_dir = Path(__file__).resolve().parent
    _ov_conf = _bundle_dir / "ov.conf.third_party_api"
    if _ov_conf.exists():
        os.environ["OPENVIKING_CONFIG_FILE"] = str(_ov_conf)

# Default agent_id for SWE-agent sessions (no session context in SWE-agent)
DEFAULT_AGENT_ID = "swe-agent"


def run_async(coro):
    """Run async code from sync context."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


class OpenVikingProxy:
    """Proxy that executes OpenViking operations via VikingClient."""

    def __init__(self):
        self._client = None

    async def _get_client(self):
        if self._client is None:
            try:
                from vikingbot.openviking_mount.ov_server import VikingClient

                self._client = await VikingClient.create(agent_id=DEFAULT_AGENT_ID)
            except ImportError as e:
                raise RuntimeError(
                    "Cannot import VikingClient. Ensure OpenViking/bot is in PYTHONPATH: "
                    "export PYTHONPATH=/path/to/OpenViking/bot:$PYTHONPATH"
                ) from e
        return self._client

    def _format_find_result(self, result, query: str = "", target_uri: str = "") -> str:
        """Format OpenViking find result (FindResult or dict) as string."""
        if result is None:
            return "No results found."
        # Handle dict (from VikingClient.search)
        if isinstance(result, dict):
            resources = result.get("resources", [])
            memories = result.get("memories", [])
            skills = result.get("skills", [])
        else:
            resources = getattr(result, "resources", []) or []
            memories = getattr(result, "memories", []) or []
            skills = getattr(result, "skills", []) or []
        lines = []
        for i, r in enumerate(resources, 1):
            uri = r.get("uri", getattr(r, "uri", ""))
            score = r.get("score", getattr(r, "score", 0))
            abstract = (r.get("abstract", getattr(r, "abstract", "")) or "")[:200]
            lines.append(f"{i}. {uri} (score={score:.3f}) {abstract}")
        for i, m in enumerate(memories, len(lines) + 1):
            uri = m.get("uri", getattr(m, "uri", ""))
            lines.append(f"{i}. [memory] {uri}")
        for i, s in enumerate(skills, len(lines) + 1):
            uri = s.get("uri", getattr(s, "uri", ""))
            lines.append(f"{i}. [skill] {uri}")
        if not lines:
            return "No results found."
        return "\n".join(lines)

    async def execute(self, tool: str, params: dict) -> str:
        """Execute an OpenViking tool; parameters align with OpenViking directory API."""
        client = await self._get_client()
        params = params or {}
        raw = getattr(client, "client", None)  # underlying openviking client

        try:
            if tool == "openviking_read":
                uri = params.get("uri", "")
                level = params.get("level", "abstract")
                return await client.read_content(uri, level=level) or ""

            elif tool == "openviking_list":
                uri = params.get("uri") or "viking://resources/"
                recursive = params.get("recursive", False)
                simple = params.get("simple", False)
                node_limit = params.get("node_limit", 1000)
                if raw and hasattr(raw, "ls"):
                    entries = await raw.ls(
                        uri,
                        simple=simple,
                        recursive=recursive,
                        node_limit=node_limit,
                    )
                else:
                    entries = await client.list_resources(path=uri, recursive=recursive)
                if not entries:
                    return f"No resources found at {uri}"
                out = []
                for entry in entries if isinstance(entries, list) else []:
                    item = {
                        "name": entry.get("name", ""),
                        "size": entry.get("size", 0),
                        "uri": entry.get("uri", ""),
                        "isDir": entry.get("isDir", False),
                    }
                    out.append(str(item))
                return "\n".join(out) if out else f"No resources found at {uri}"

            elif tool == "openviking_search":
                query = params.get("query", "")
                target_uri = params.get("target_uri") or ""
                limit = params.get("limit", 10)
                score_threshold = params.get("score_threshold")
                if raw and hasattr(raw, "find"):
                    result = await raw.find(
                        query,
                        target_uri=target_uri,
                        limit=limit,
                        score_threshold=score_threshold,
                    )
                else:
                    result = await client.search(query, target_uri=target_uri or "")
                return self._format_find_result(result, query=query, target_uri=target_uri)

            elif tool == "openviking_grep":
                uri = params.get("uri", "")
                pattern = params.get("pattern", "")
                case_insensitive = params.get("case_insensitive", False)
                node_limit = params.get("node_limit")
                if raw and hasattr(raw, "grep"):
                    kwargs = {"uri": uri, "pattern": pattern, "case_insensitive": case_insensitive}
                    if node_limit is not None:
                        kwargs["node_limit"] = node_limit
                    result = await raw.grep(**kwargs)
                else:
                    result = await client.grep(uri, pattern, case_insensitive=case_insensitive)
                if isinstance(result, dict):
                    matches = result.get("result", {}).get("matches", [])
                    count = result.get("result", {}).get("count", 0)
                else:
                    matches = getattr(result, "matches", [])
                    count = getattr(result, "count", 0)
                if not matches:
                    return f"No matches found for pattern: {pattern}"
                lines = [f"Found {count} match{'es' if count != 1 else ''}:"]
                for m in matches:
                    mu = m.get("uri", "unknown") if isinstance(m, dict) else getattr(m, "uri", "unknown")
                    line = m.get("line", "?") if isinstance(m, dict) else getattr(m, "line", "?")
                    content = m.get("content", "") if isinstance(m, dict) else getattr(m, "content", "")
                    lines.append(f"\n{mu}:{line}")
                    lines.append(f"   {content}")
                return "\n".join(lines)

            elif tool == "openviking_glob":
                pattern = params.get("pattern", "")
                uri = params.get("uri") or ""
                result = await client.glob(pattern, uri=uri or None)
                if isinstance(result, dict):
                    matches = result.get("result", {}).get("matches", [])
                    count = result.get("result", {}).get("count", 0)
                else:
                    matches = getattr(result, "matches", [])
                    count = getattr(result, "count", 0)
                if not matches:
                    return f"No files found for pattern: {pattern}"
                lines = [f"Found {count} file{'s' if count != 1 else ''}:"]
                for mu in matches:
                    if isinstance(mu, dict):
                        mu = mu.get("uri", str(mu))
                    lines.append(f"{mu}")
                return "\n".join(lines)

            elif tool == "openviking_add_resource":
                path = params.get("path", "")
                reason = params.get("reason", "")
                target = params.get("target")
                wait = params.get("wait", False)
                if not path:
                    return "Error: path is required for openviking_add_resource"
                try:
                    result = await client.add_resource(
                        local_path=path,
                        desc=reason,
                        target_path=target,
                        wait=wait,
                    )
                    if result is None:
                        return "Add resource completed (no result returned)."
                    return str(result)
                except Exception as e:
                    return f"Error adding resource: {e}"

            elif tool == "user_memory_search":
                query = params.get("query", "")
                results = await client.search_user_memory(query)
                if not results:
                    return f"No results found for query: {query}"
                return str(results)

            else:
                return f"Error: Unknown tool '{tool}'"

        except Exception as e:
            return f"Error: {e}"


proxy = OpenVikingProxy()


class ProxyHandler(BaseHTTPRequestHandler):
    """HTTP handler for proxy requests."""

    def do_POST(self):
        if self.path == "/execute" or self.path == "/execute/":
            self._handle_execute()
        else:
            self._send_error(404, "Not found")

    def _handle_execute(self):
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            data = json.loads(body.decode("utf-8"))
            tool = data.get("tool", "")
            params = data.get("params", {})

            if not tool:
                self._send_json({"success": False, "error": "Missing 'tool' in request"})
                return

            result = run_async(proxy.execute(tool, params))
            self._send_json({"success": True, "output": result})

        except json.JSONDecodeError as e:
            self._send_json({"success": False, "error": f"Invalid JSON: {e}"})
        except Exception as e:
            self._send_json({"success": False, "error": str(e)})

    def _send_json(self, data: dict):
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    def _send_error(self, code: int, message: str):
        self.send_response(code)
        self.end_headers()

    def log_message(self, format, *args):
        # Suppress default logging
        pass


def main():
    parser = argparse.ArgumentParser(description="OpenViking Proxy Server for SWE-agent")
    parser.add_argument("--port", type=int, default=8765, help="Port to listen on")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    args = parser.parse_args()

    server = HTTPServer((args.host, args.port), ProxyHandler)
    print(f"OpenViking Proxy Server listening on http://{args.host}:{args.port}")
    print("  POST /execute with JSON body: {\"tool\": \"openviking_read\", \"params\": {...}}")
    print()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()


if __name__ == "__main__":
    main()
