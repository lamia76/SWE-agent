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
"""
import argparse
import asyncio
import json
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread


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

    async def execute(self, tool: str, params: dict) -> str:
        """Execute an OpenViking tool and return the result string."""
        client = await self._get_client()
        params = params or {}

        try:
            if tool == "openviking_read":
                uri = params.get("uri", "")
                level = params.get("level", "abstract")
                return await client.read_content(uri, level=level) or ""

            elif tool == "openviking_list":
                uri = params.get("uri", "viking://resources/")
                recursive = params.get("recursive", False)
                entries = await client.list_resources(path=uri, recursive=recursive)
                if not entries:
                    return f"No resources found at {uri}"
                result = []
                for entry in entries:
                    item = {
                        "name": entry.get("name", ""),
                        "size": entry.get("size", 0),
                        "uri": entry.get("uri", ""),
                        "isDir": entry.get("isDir", False),
                    }
                    result.append(str(item))
                return "\n".join(result)

            elif tool == "openviking_search":
                query = params.get("query", "")
                target_uri = params.get("target_uri")
                result = await client.search(query, target_uri=target_uri or "")
                if not result:
                    return f"No results found for query: {query}"
                # Format search result
                lines = []
                for key in ("resources", "memories", "skills"):
                    items = result.get(key, [])
                    if items:
                        for i, r in enumerate(items, 1):
                            lines.append(f"{i}. {r}")
                if lines:
                    return "\n".join(lines)
                return str(result)

            elif tool == "openviking_grep":
                uri = params.get("uri", "")
                pattern = params.get("pattern", "")
                case_insensitive = params.get("case_insensitive", False)
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
