#!/usr/bin/env python3
"""
Default URI Handler for Analytica
==================================

This script is called by the system when an analytica:// URI is opened.
It parses the URI and dispatches to the appropriate action.

URI Format:
    analytica://<action>/<target>?param1=value1&param2=value2

Examples:
    analytica://desktop/run?project=myapp&url=http://localhost:18000
    analytica://mobile/preview?hash=abc123
    analytica://web/open?url=http://example.com

Actions:
    desktop/run   - Launch Electron desktop app
    desktop/dev   - Start desktop dev server
    mobile/run    - Launch mobile app in emulator
    web/open      - Open URL in browser
    shell/exec    - Execute shell command (with confirmation)
"""

import sys
import os
import subprocess
import urllib.parse
import json
from pathlib import Path
from typing import Any, Dict, Optional


SCHEME = "analytica"


def parse_uri(uri: str) -> Dict[str, Any]:
    """Parse URI into components."""
    parsed = urllib.parse.urlparse(uri)
    params = dict(urllib.parse.parse_qsl(parsed.query))
    
    path_parts = parsed.path.strip("/").split("/", 1)
    action = path_parts[0] if path_parts else ""
    target = path_parts[1] if len(path_parts) > 1 else ""
    
    return {
        "scheme": parsed.scheme,
        "host": parsed.netloc,
        "action": action,
        "target": target,
        "path": parsed.path.lstrip("/"),
        "params": params,
        "fragment": parsed.fragment,
        "raw": uri
    }


def notify(title: str, message: str, icon: str = "dialog-information"):
    """Show desktop notification."""
    try:
        subprocess.run(
            ["notify-send", "-i", icon, title, message],
            capture_output=True
        )
    except Exception:
        print(f"{title}: {message}")


def handle_desktop_run(parsed: Dict[str, Any]) -> int:
    """Handle desktop/run - launch Electron app or open URL in browser."""
    params = parsed.get("params", {})
    project_dir = params.get("dir", params.get("project", ""))
    default_url = os.environ.get("DESKTOP_DEFAULT_URL", "http://localhost:18000")
    url = params.get("url", default_url)
    
    # If no project dir specified, just open URL in browser
    if not project_dir or project_dir == ".":
        notify("Analytica", f"Opening: {url}")
        try:
            subprocess.Popen(
                ["xdg-open", url],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            return 0
        except Exception as e:
            notify("Analytica", f"Failed to open URL: {e}", "dialog-error")
            return 1
    
    project_path = Path(project_dir).expanduser().resolve()
    
    if not project_path.exists():
        notify("Analytica", f"Project not found: {project_path}\nOpening URL instead: {url}", "dialog-warning")
        subprocess.Popen(["xdg-open", url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return 0
    
    package_json = project_path / "package.json"
    if not package_json.exists():
        notify("Analytica", f"No package.json in {project_path}\nOpening URL instead: {url}", "dialog-warning")
        subprocess.Popen(["xdg-open", url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return 0
    
    notify("Analytica", f"Starting desktop app from {project_path}")
    
    env = os.environ.copy()
    env["ANALYTICA_URL"] = url
    
    try:
        # Use nohup to detach process completely
        subprocess.Popen(
            ["npm", "start"],
            cwd=str(project_path),
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True  # Detach from parent process
        )
        return 0
    except Exception as e:
        notify("Analytica", f"Failed to start: {e}", "dialog-error")
        return 1


def handle_desktop_dev(parsed: Dict[str, Any]) -> int:
    """Handle desktop/dev - start dev server with hot reload."""
    params = parsed.get("params", {})
    project_dir = params.get("dir", params.get("project", "."))
    
    project_path = Path(project_dir).expanduser().resolve()
    
    if not project_path.exists():
        notify("Analytica", f"Project directory not found: {project_path}", "dialog-error")
        return 1
    
    notify("Analytica", f"Starting dev server in {project_path}")
    
    try:
        subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=str(project_path)
        )
        return 0
    except Exception as e:
        notify("Analytica", f"Failed to start dev: {e}", "dialog-error")
        return 1


def handle_web_open(parsed: Dict[str, Any]) -> int:
    """Handle web/open - open URL in browser."""
    params = parsed.get("params", {})
    url = params.get("url", "")
    
    if not url:
        notify("Analytica", "No URL provided", "dialog-error")
        return 1
    
    try:
        subprocess.Popen(
            ["xdg-open", url],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return 0
    except Exception as e:
        notify("Analytica", f"Failed to open URL: {e}", "dialog-error")
        return 1


def handle_shell_exec(parsed: Dict[str, Any]) -> int:
    """Handle shell/exec - execute command (with confirmation)."""
    params = parsed.get("params", {})
    cmd = params.get("cmd", params.get("command", ""))
    cwd = params.get("cwd", params.get("dir", "."))
    confirm = params.get("confirm", "true").lower() != "false"
    
    if not cmd:
        notify("Analytica", "No command provided", "dialog-error")
        return 1
    
    if confirm:
        try:
            result = subprocess.run(
                ["zenity", "--question", "--title=Analytica", 
                 f"--text=Execute command?\n\n{cmd}"],
                capture_output=True
            )
            if result.returncode != 0:
                return 0
        except Exception:
            pass
    
    notify("Analytica", f"Executing: {cmd}")
    
    try:
        subprocess.Popen(
            cmd,
            shell=True,
            cwd=cwd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return 0
    except Exception as e:
        notify("Analytica", f"Failed to execute: {e}", "dialog-error")
        return 1


def handle_mobile_run(parsed: Dict[str, Any]) -> int:
    """Handle mobile/run - launch in emulator."""
    params = parsed.get("params", {})
    platform = params.get("platform", "android")
    project_dir = params.get("dir", ".")
    
    project_path = Path(project_dir).expanduser().resolve()
    
    if platform == "android":
        cmd = ["npx", "react-native", "run-android"]
    elif platform == "ios":
        cmd = ["npx", "react-native", "run-ios"]
    else:
        notify("Analytica", f"Unknown platform: {platform}", "dialog-error")
        return 1
    
    notify("Analytica", f"Starting {platform} emulator...")
    
    try:
        subprocess.Popen(cmd, cwd=str(project_path))
        return 0
    except Exception as e:
        notify("Analytica", f"Failed to start emulator: {e}", "dialog-error")
        return 1


HANDLERS = {
    "desktop/run": handle_desktop_run,
    "desktop/dev": handle_desktop_dev,
    "web/open": handle_web_open,
    "shell/exec": handle_shell_exec,
    "mobile/run": handle_mobile_run,
}


def handle_uri(uri: str) -> int:
    """Main URI handler."""
    parsed = parse_uri(uri)
    path = parsed.get("path", "")
    
    if path in HANDLERS:
        return HANDLERS[path](parsed)
    
    action = parsed.get("action", "")
    for pattern, handler in HANDLERS.items():
        if pattern.startswith(action + "/"):
            return handler(parsed)
    
    notify("Analytica", f"Unknown action: {path}", "dialog-warning")
    return 1


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <{SCHEME}://action/target?params>", file=sys.stderr)
        print("\nSupported actions:")
        for action in HANDLERS:
            print(f"  {SCHEME}://{action}")
        sys.exit(1)
    
    uri = sys.argv[1]
    
    if not uri.startswith(f"{SCHEME}://"):
        print(f"Invalid URI scheme. Expected {SCHEME}://", file=sys.stderr)
        sys.exit(1)
    
    sys.exit(handle_uri(uri))


if __name__ == "__main__":
    main()
