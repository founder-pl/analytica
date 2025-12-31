"""
URI Launcher - Custom URI Scheme Registration and Handling for Linux
=====================================================================

This module provides functionality to:
1. Register custom URI schemes (like analytica://) on Linux
2. Create .desktop files that handle the URI
3. Launch applications from URIs using xdg-open

How it works on Linux:
- Creates a .desktop file in ~/.local/share/applications/
- Registers the MIME type x-scheme-handler/<scheme>
- Uses xdg-mime to set the default handler
- xdg-open then routes URIs to the handler

Example:
    launcher = URILauncher("analytica")
    launcher.register(handler_script="/path/to/handler.py")
    
    # Now you can run:
    # xdg-open "analytica://desktop/run?project=test"
"""

import os
import sys
import subprocess
import shutil
import json
import urllib.parse
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime


@dataclass
class URIHandler:
    """Configuration for a URI handler."""
    scheme: str
    name: str
    exec_command: str
    icon: str = "application-x-executable"
    comment: str = ""
    categories: List[str] = field(default_factory=lambda: ["Development", "Utility"])
    terminal: bool = False
    
    def to_desktop_entry(self) -> str:
        """Generate .desktop file content."""
        categories_str = ";".join(self.categories) + ";" if self.categories else ""
        return f"""[Desktop Entry]
Type=Application
Name={self.name}
Comment={self.comment or f'Handler for {self.scheme}:// URIs'}
Exec={self.exec_command} %u
Icon={self.icon}
Terminal={'true' if self.terminal else 'false'}
Categories={categories_str}
MimeType=x-scheme-handler/{self.scheme};
NoDisplay=true
"""


class URISchemeRegistry:
    """
    Registry for custom URI schemes on Linux.
    
    Uses XDG standards:
    - .desktop files in ~/.local/share/applications/
    - xdg-mime for MIME type registration
    - xdg-open for launching URIs
    """
    
    def __init__(self):
        self.applications_dir = Path.home() / ".local" / "share" / "applications"
        self.applications_dir.mkdir(parents=True, exist_ok=True)
    
    def _desktop_file_path(self, scheme: str) -> Path:
        """Get path to .desktop file for a scheme."""
        return self.applications_dir / f"{scheme}-handler.desktop"
    
    def register(self, handler: URIHandler) -> bool:
        """
        Register a URI scheme handler.
        
        Args:
            handler: URIHandler configuration
            
        Returns:
            True if registration succeeded
        """
        desktop_path = self._desktop_file_path(handler.scheme)
        
        try:
            desktop_path.write_text(handler.to_desktop_entry())
            
            subprocess.run(
                ["xdg-mime", "default", desktop_path.name, f"x-scheme-handler/{handler.scheme}"],
                check=True,
                capture_output=True
            )
            
            subprocess.run(
                ["update-desktop-database", str(self.applications_dir)],
                capture_output=True
            )
            
            return True
        except subprocess.CalledProcessError as e:
            print(f"Failed to register scheme {handler.scheme}: {e}", file=sys.stderr)
            return False
        except Exception as e:
            print(f"Error registering scheme {handler.scheme}: {e}", file=sys.stderr)
            return False
    
    def unregister(self, scheme: str) -> bool:
        """
        Unregister a URI scheme handler.
        
        Args:
            scheme: The scheme to unregister (e.g., "analytica")
            
        Returns:
            True if unregistration succeeded
        """
        desktop_path = self._desktop_file_path(scheme)
        
        try:
            if desktop_path.exists():
                desktop_path.unlink()
            
            subprocess.run(
                ["update-desktop-database", str(self.applications_dir)],
                capture_output=True
            )
            
            return True
        except Exception as e:
            print(f"Error unregistering scheme {scheme}: {e}", file=sys.stderr)
            return False
    
    def is_registered(self, scheme: str) -> bool:
        """Check if a scheme is registered."""
        desktop_path = self._desktop_file_path(scheme)
        return desktop_path.exists()
    
    def get_handler(self, scheme: str) -> Optional[str]:
        """Get the current handler for a scheme."""
        try:
            result = subprocess.run(
                ["xdg-mime", "query", "default", f"x-scheme-handler/{scheme}"],
                capture_output=True,
                text=True
            )
            return result.stdout.strip() if result.returncode == 0 else None
        except Exception:
            return None


class URILauncher:
    """
    High-level interface for URI scheme management and launching.
    
    Usage:
        launcher = URILauncher("analytica")
        
        # Register the scheme
        launcher.register(
            handler_script="/path/to/handler.py",
            name="Analytica Launcher"
        )
        
        # Launch a URI
        launcher.launch("analytica://desktop/run?project=test")
        
        # Parse a URI
        parsed = launcher.parse("analytica://desktop/run?project=test")
        # {'scheme': 'analytica', 'path': 'desktop/run', 'params': {'project': 'test'}}
    """
    
    def __init__(self, scheme: str):
        """
        Initialize launcher for a specific scheme.
        
        Args:
            scheme: URI scheme name (e.g., "analytica" for analytica://)
        """
        self.scheme = scheme
        self.registry = URISchemeRegistry()
        self._handlers: Dict[str, Callable] = {}
    
    def register(
        self,
        handler_script: Optional[str] = None,
        handler_command: Optional[str] = None,
        name: Optional[str] = None,
        icon: str = "application-x-executable",
        terminal: bool = False
    ) -> bool:
        """
        Register the URI scheme with the system.
        
        Args:
            handler_script: Path to Python script that handles URIs
            handler_command: Custom command to execute (overrides handler_script)
            name: Display name for the handler
            icon: Icon name or path
            terminal: Whether to run in terminal
            
        Returns:
            True if registration succeeded
        """
        if handler_command:
            exec_cmd = handler_command
        elif handler_script:
            python_path = sys.executable
            exec_cmd = f'"{python_path}" "{handler_script}"'
        else:
            default_handler = self._get_default_handler_path()
            python_path = sys.executable
            exec_cmd = f'"{python_path}" "{default_handler}"'
        
        handler = URIHandler(
            scheme=self.scheme,
            name=name or f"{self.scheme.capitalize()} URI Handler",
            exec_command=exec_cmd,
            icon=icon,
            terminal=terminal
        )
        
        return self.registry.register(handler)
    
    def unregister(self) -> bool:
        """Unregister the URI scheme."""
        return self.registry.unregister(self.scheme)
    
    def is_registered(self) -> bool:
        """Check if the scheme is registered."""
        return self.registry.is_registered(self.scheme)
    
    def launch(self, uri: str) -> bool:
        """
        Launch a URI using xdg-open.
        
        Args:
            uri: Full URI (e.g., "analytica://desktop/run?project=test")
            
        Returns:
            True if launch succeeded
        """
        if not uri.startswith(f"{self.scheme}://"):
            uri = f"{self.scheme}://{uri}"
        
        try:
            subprocess.Popen(
                ["xdg-open", uri],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            return True
        except Exception as e:
            print(f"Failed to launch URI {uri}: {e}", file=sys.stderr)
            return False
    
    def parse(self, uri: str) -> Dict[str, Any]:
        """
        Parse a URI into components.
        
        Args:
            uri: URI string
            
        Returns:
            Dict with scheme, host, path, params
        """
        parsed = urllib.parse.urlparse(uri)
        params = dict(urllib.parse.parse_qsl(parsed.query))
        
        return {
            "scheme": parsed.scheme,
            "host": parsed.netloc,
            "path": parsed.path.lstrip("/"),
            "params": params,
            "fragment": parsed.fragment,
            "raw": uri
        }
    
    def build_uri(
        self,
        path: str = "",
        host: str = "",
        params: Optional[Dict[str, str]] = None,
        fragment: str = ""
    ) -> str:
        """
        Build a URI from components.
        
        Args:
            path: URI path (e.g., "desktop/run")
            host: URI host (optional)
            params: Query parameters
            fragment: URI fragment
            
        Returns:
            Complete URI string
        """
        query = urllib.parse.urlencode(params) if params else ""
        
        uri = f"{self.scheme}://"
        if host:
            uri += host
        if path:
            uri += f"/{path}" if not path.startswith("/") else path
        if query:
            uri += f"?{query}"
        if fragment:
            uri += f"#{fragment}"
        
        return uri
    
    def add_handler(self, path_pattern: str, handler: Callable[[Dict[str, Any]], Any]):
        """
        Add a handler function for a specific path pattern.
        
        Args:
            path_pattern: Path to match (e.g., "desktop/run")
            handler: Function to call with parsed URI
        """
        self._handlers[path_pattern] = handler
    
    def handle(self, uri: str) -> Any:
        """
        Handle a URI by calling the appropriate registered handler.
        
        Args:
            uri: URI to handle
            
        Returns:
            Result from handler function
        """
        parsed = self.parse(uri)
        path = parsed.get("path", "")
        
        if path in self._handlers:
            return self._handlers[path](parsed)
        
        for pattern, handler in self._handlers.items():
            if path.startswith(pattern.rstrip("*")):
                return handler(parsed)
        
        raise ValueError(f"No handler registered for path: {path}")
    
    def _get_default_handler_path(self) -> str:
        """Get path to default handler script."""
        return str(Path(__file__).parent / "handler.py")


def create_handler_script(
    output_path: str,
    scheme: str,
    handlers: Dict[str, str]
) -> str:
    """
    Generate a standalone handler script.
    
    Args:
        output_path: Where to write the script
        scheme: URI scheme
        handlers: Dict mapping paths to shell commands
        
    Returns:
        Path to created script
    """
    handlers_json = json.dumps(handlers, indent=2)
    
    script = f'''#!/usr/bin/env python3
"""
Auto-generated URI handler for {scheme}:// scheme.
"""
import sys
import subprocess
import urllib.parse
import json

SCHEME = "{scheme}"
HANDLERS = {handlers_json}

def parse_uri(uri: str) -> dict:
    parsed = urllib.parse.urlparse(uri)
    params = dict(urllib.parse.parse_qsl(parsed.query))
    return {{
        "scheme": parsed.scheme,
        "host": parsed.netloc,
        "path": parsed.path.lstrip("/"),
        "params": params,
        "fragment": parsed.fragment,
        "raw": uri
    }}

def handle_uri(uri: str):
    parsed = parse_uri(uri)
    path = parsed.get("path", "")
    
    for pattern, command in HANDLERS.items():
        if path == pattern or path.startswith(pattern.rstrip("*")):
            cmd = command.format(**parsed.get("params", {{}}))
            print(f"Executing: {{cmd}}")
            subprocess.run(cmd, shell=True)
            return
    
    print(f"No handler for path: {{path}}", file=sys.stderr)
    sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {{sys.argv[0]}} <{scheme}://...>", file=sys.stderr)
        sys.exit(1)
    
    handle_uri(sys.argv[1])
'''
    
    Path(output_path).write_text(script)
    Path(output_path).chmod(0o755)
    
    return output_path
