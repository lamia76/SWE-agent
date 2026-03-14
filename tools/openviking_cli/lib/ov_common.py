# Copyright (c) 2026 OpenViking-SWE-Agent Integration
# SPDX-License-Identifier: Apache-2.0
"""
OpenViking common utilities - 嵌入式模式，与 tools/openviking 相同逻辑。
使用 SyncOpenViking SDK 直接调用，无需远程 Server。
"""

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional


def get_repo_root() -> Path:
    """Get the repository root directory. Defaults to current working directory."""
    return Path.cwd()


def get_data_dir() -> Path:
    """Get OpenViking data directory. Priority: OPENVIKING_DATA_DIR, else ./.openviking"""
    env_dir = os.environ.get("OPENVIKING_DATA_DIR")
    if env_dir:
        return Path(env_dir)
    return get_repo_root() / ".openviking"


def get_config_file() -> Optional[str]:
    """Get config file path from OPENVIKING_CONFIG_FILE env var."""
    return os.environ.get("OPENVIKING_CONFIG_FILE")


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


def new_client():
    """Create and initialize SyncOpenViking client (embedded mode)."""
    try:
        import openviking as ov
    except ImportError as e:
        raise Exception(
            f"OpenViking SDK not installed: {e}. "
            "Please: pip install openviking"
        ) from e

    config = None
    config_file = get_config_file()
    if config_file and Path(config_file).exists():
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                config_dict = json.load(f)
            try:
                from openviking_cli.utils.config.open_viking_config import OpenVikingConfig
                config = OpenVikingConfig.from_dict(config_dict)
            except ImportError:
                config = config_dict
        except Exception as e:
            print(f"Warning: Failed to load config from {config_file}: {e}", file=sys.stderr)

    data_dir = get_data_dir()
    try:
        if config is not None:
            client = ov.SyncOpenViking(path=str(data_dir), config=config)
        else:
            client = ov.SyncOpenViking(path=str(data_dir))
        client.initialize()
        return client
    except Exception as e:
        raise Exception(f"Failed to initialize OpenViking client: {e}") from e


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
                hint="Check ov.conf (embedding/vlm/rerank API) and OPENVIKING_DATA_DIR",
                error_type="OpenVikingError",
            )
            sys.exit(1)

    return wrapper
