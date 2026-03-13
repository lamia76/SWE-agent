# Copyright (c) 2026 OpenViking-SWE-Agent Integration
# SPDX-License-Identifier: Apache-2.0
"""
OpenViking common utilities for SWE-agent tool bundle.

This module provides shared functionality for all OpenViking tools:
- SDK client initialization
- Root URI state management
- JSON output formatting
- Text truncation
- Error handling
"""

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional


def get_repo_root() -> Path:
    """
    Get the repository root directory.
    Defaults to the current working directory.
    
    Returns:
        Path to the repository root
    """
    return Path.cwd()


def get_data_dir() -> Path:
    """
    Get the OpenViking data directory.
    
    Priority:
    1. OPENVIKING_DATA_DIR environment variable
    2. Default: ./.openviking (relative to repo root)
    
    Returns:
        Path to the data directory
    """
    env_dir = os.environ.get("OPENVIKING_DATA_DIR")
    if env_dir:
        return Path(env_dir)
    return get_repo_root() / ".openviking"


def get_config_file() -> Optional[str]:
    """
    Get the OpenViking configuration file path.
    
    Returns:
        Path to config file from OPENVIKING_CONFIG_FILE env var, or None
    """
    return os.environ.get("OPENVIKING_CONFIG_FILE")


def get_root_uri_file() -> Path:
    """
    Get the path to the file storing the root URI.
    
    Returns:
        Path to the root URI file (.openviking_root_uri in repo root)
    """
    return get_repo_root() / ".openviking_root_uri"


def load_root_uri(path: Optional[Path] = None) -> Optional[str]:
    """
    Load the root URI from storage.
    
    Args:
        path: Custom path to the root URI file (optional)
    
    Returns:
        Root URI string, or None if not found
    """
    if path is None:
        path = get_root_uri_file()
    
    if path.exists():
        return path.read_text().strip()
    return None


def save_root_uri(uri: str, path: Optional[Path] = None) -> None:
    """
    Save the root URI to storage.
    
    Args:
        uri: Root URI to save
        path: Custom path to the root URI file (optional)
    """
    if path is None:
        path = get_root_uri_file()
    
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(uri)


def new_client():
    """
    Create and initialize a new OpenViking client.
    
    Returns:
        Initialized SyncOpenViking client instance
        
    Raises:
        Exception: If client initialization fails
    """
    try:
        import openviking as ov
        from openviking_cli.utils.config.open_viking_config import OpenVikingConfig
    except ImportError as e:
        raise Exception(
            f"OpenViking SDK not installed: {e}. "
            "Please: pip install openviking"
        ) from e
    
    # Load config if provided
    config = None
    config_file = get_config_file()
    if config_file and Path(config_file).exists():
        try:
            with open(config_file, 'r') as f:
                config_dict = json.load(f)
            config = OpenVikingConfig.from_dict(config_dict)
        except Exception as e:
            # Log warning but continue with default config
            print(f"Warning: Failed to load config from {config_file}: {e}", file=sys.stderr)
    
    # Create client
    data_dir = get_data_dir()
    try:
        if config:
            client = ov.SyncOpenViking(path=str(data_dir), config=config)
        else:
            client = ov.SyncOpenViking(path=str(data_dir))
        
        client.initialize()
        return client
    except Exception as e:
        raise Exception(f"Failed to initialize OpenViking client: {e}") from e


def json_print(obj: Any) -> None:
    """
    Print object as JSON to stdout.
    
    Args:
        obj: Object to serialize as JSON
    """
    json.dump(obj, sys.stdout, ensure_ascii=False, indent=2)
    print()  # Add newline


def json_error(message: str, hint: Optional[str] = None, error_type: str = "OpenVikingError") -> None:
    """
    Print an error in standardized JSON format.
    
    Args:
        message: Error message
        hint: Optional hint for resolving the error
        error_type: Type of error (default: "OpenVikingError")
    """
    error_obj = {
        "error": {
            "type": error_type,
            "message": message
        }
    }
    if hint:
        error_obj["error"]["hint"] = hint
    json_print(error_obj)


def truncate(text: str, max_chars: int = 16000) -> Dict[str, Any]:
    """
    Truncate text to maximum character limit.
    
    Args:
        text: Text to truncate
        max_chars: Maximum number of characters to keep
    
    Returns:
        Dict with 'content', 'truncated', and 'max_chars' keys
    """
    if len(text) <= max_chars:
        return {
            "content": text,
            "truncated": False,
            "max_chars": max_chars
        }
    else:
        return {
            "content": text[:max_chars],
            "truncated": True,
            "max_chars": max_chars
        }


def handle_exceptions(func):
    """
    Decorator to handle exceptions and output standardized error JSON.
    
    Args:
        func: Function to wrap
        
    Returns:
        Wrapped function that handles exceptions
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except FileNotFoundError as e:
            json_error(
                message=f"File not found: {e}",
                hint="Please ensure the file or directory path is correct",
                error_type="FileNotFoundError"
            )
            sys.exit(1)
        except ValueError as e:
            json_error(
                message=f"Invalid parameter: {e}",
                hint="Please check the provided arguments",
                error_type="ValueError"
            )
            sys.exit(1)
        except Exception as e:
            json_error(
                message=str(e),
                hint="CheckOpenViking",
                error_type="OpenVikingError"
            )
            sys.exit(1)
    return wrapper
同上