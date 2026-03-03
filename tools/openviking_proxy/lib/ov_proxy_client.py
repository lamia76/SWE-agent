"""
Client for calling the OpenViking proxy server from SWE-agent container.
"""
import json
import os
import sys
import urllib.request
import urllib.error


def get_proxy_url() -> str:
    return os.environ.get("OPENVIKING_PROXY_URL", "http://host.docker.internal:8765")


def call_proxy(tool: str, params: dict) -> str:
    """Call the OpenViking proxy server and return the result string."""
    url = get_proxy_url()
    data = json.dumps({"tool": tool, "params": params}).encode("utf-8")
    req = urllib.request.Request(
        f"{url.rstrip('/')}/execute",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            if result.get("success"):
                return result.get("output", "")
            return f"Error: {result.get('error', 'Unknown error')}"
    except urllib.error.URLError as e:
        return f"Error: Cannot connect to OpenViking proxy at {url}. Is the proxy server running? {e}"
    except json.JSONDecodeError as e:
        return f"Error: Invalid response from proxy: {e}"
    except Exception as e:
        return f"Error: {e}"


def parse_bool(s: str) -> bool:
    if isinstance(s, bool):
        return s
    return str(s).lower() in ("true", "1", "yes", "on")
