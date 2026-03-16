#!/usr/bin/env python
# Copyright (c) 2026 OpenViking-SWE-Agent Integration
# SPDX-License-Identifier: Apache-2.0
"""
OpenViking CLI common utilities - 通过 ov 命令连接 OpenViking Server（HTTP）。
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def get_bundle_dir() -> Path:
    """Get the openviking_cli bundle directory."""
    return Path(__file__).resolve().parent.parent


def get_repo_root() -> Path:
    """Get the repository root directory."""
    return Path.cwd()


def get_root_uri_file() -> Path:
    """Path to the file storing the root URI."""
    return get_repo_root() / ".openviking_root_uri"


def load_root_uri(path: Optional[Path] = None) -> Optional[str]:
    """Load root URI from storage."""
    if path is None:
        path = get_root_uri_file()
    if path.exists():
        return path.read_text().strip()
    return None


def save_root_uri(uri: str, path: Optional[Path] = None) -> None:
    """Save root URI to storage."""
    if path is None:
        path = get_root_uri_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(uri)


def setup_cli_env() -> None:
    """
    Setup environment for ov CLI:
    - OPENVIKING_SERVER_URL -> generate .ovcli.env.json
    - ovcli.conf as fallback
    - tls-ca-bundle.pem for HTTPS（仅在未显式设置证书环境变量时作为缺省值）
    """
    bundle_dir = get_bundle_dir()
    ca_bundle = bundle_dir / "tls-ca-bundle.pem"
    if ca_bundle.exists():
        abs_path = str(ca_bundle.resolve())
        # 只在用户没有显式设置时才使用本地 CA bundle，避免覆盖系统/容器已有配置
        os.environ.setdefault("REQUESTS_CA_BUNDLE", abs_path)
        os.environ.setdefault("SSL_CERT_FILE", abs_path)

    # 优先使用环境变量中的 OPENVIKING_SERVER_URL / OPENVIKING_API_KEY
    url = os.environ.get("OPENVIKING_SERVER_URL")
    if url:
        ovcli_path = bundle_dir / ".ovcli.env.json"
        cfg = {
            "url": url,
            "api_key": os.environ.get("OPENVIKING_API_KEY") or None,
            "agent_id": None,
            "timeout": 120.0,
            "output": "json",
        }
        try:
            ovcli_path.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
            os.environ["OPENVIKING_CLI_CONFIG_FILE"] = str(ovcli_path.resolve())
        except Exception:
            # 配置文件写失败时，不影响后续通过 ovcli.conf 兜底
            pass
    elif (bundle_dir / "ovcli.conf").exists():
        # 若未设置 OPENVIKING_SERVER_URL，则回退到静态 ovcli.conf
        os.environ["OPENVIKING_CLI_CONFIG_FILE"] = str(
            (bundle_dir / "ovcli.conf").resolve()
        )

    # 确保 Python 安装的 bin 目录在 PATH 中，方便找到 ov/openviking 可执行文件
    py_bin = Path(sys.executable).parent.parent / "bin"
    if py_bin.exists():
        path = os.environ.get("PATH", "")
        if str(py_bin) not in path:
            os.environ["PATH"] = f"{py_bin}{os.pathsep}{path}"


def _ov_command() -> List[str]:
    """Return ov or openviking or python -m openviking."""
    for name in ("ov", "openviking"):
        p = shutil.which(name)
        if p:
            return [p]
    return [sys.executable, "-m", "openviking"]


def run_ov_cli(subcmd: str, args: List[str]) -> Tuple[int, str, str]:
    """Run ov <subcmd> <args> via subprocess. Returns (returncode, stdout, stderr)."""
    setup_cli_env()
    cmd = _ov_command() + [subcmd] + args
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired as e:
        return 124, "", str(e)
    except Exception as e:
        return -1, "", str(e)


def json_print(obj: Any) -> None:
    """Print object as JSON to stdout."""
    json.dump(obj, sys.stdout, ensure_ascii=False, indent=2)
    print()


def json_error(
    message: str, hint: Optional[str] = None, error_type: str = "OpenVikingError"
) -> None:
    """Print error in standardized JSON format."""
    error_obj: Dict[str, Any] = {"error": {"type": error_type, "message": message}}
    if hint:
        error_obj["error"]["hint"] = hint
    json_print(error_obj)


def truncate(text: str, max_chars: int = 16000) -> Dict[str, Any]:
    """Truncate text to max_chars limit."""
    if len(text) <= max_chars:
        return {"content": text, "truncated": False, "max_chars": max_chars}
    return {"content": text[:max_chars], "truncated": True, "max_chars": max_chars}


def handle_exceptions(func):
    """Decorator to handle exceptions and output standardized error JSON."""

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except FileNotFoundError as e:
            json_error(
                message=f"File not found: {e}",
                hint="Please ensure the file or directory path is correct",
                error_type="FileNotFoundError",
            )
            sys.exit(1)
        except ValueError as e:
            json_error(
                message=f"Invalid parameter: {e}",
                hint="Please check the provided arguments",
                error_type="ValueError",
            )
            sys.exit(1)
        except Exception as e:
            json_error(
                message=str(e),
                hint=(
                    "Check ovcli.conf, OPENVIKING_SERVER_URL, and "
                    "OpenViking Server connectivity"
                ),
                error_type="OpenVikingError",
            )
            sys.exit(1)

    return wrapper
