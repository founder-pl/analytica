#!/usr/bin/env python3
"""
CLI for Analytica URI Launcher
==============================

Commands:
    register    - Register the analytica:// URI scheme
    unregister  - Unregister the URI scheme
    status      - Check registration status
    launch      - Launch a URI
    test        - Test URI parsing

Usage:
    python -m core.uri_launcher.cli register
    python -m core.uri_launcher.cli launch "analytica://desktop/run?dir=/path/to/project"
    python -m core.uri_launcher.cli status
"""

import sys
import argparse
from pathlib import Path

from .launcher import URILauncher


def cmd_register(args):
    """Register the URI scheme."""
    launcher = URILauncher(args.scheme)
    
    handler_path = Path(__file__).parent / "handler.py"
    
    success = launcher.register(
        handler_script=str(handler_path),
        name=f"{args.scheme.capitalize()} URI Handler",
        terminal=args.terminal
    )
    
    if success:
        print(f"✓ Registered {args.scheme}:// URI scheme")
        print(f"  Handler: {handler_path}")
        print(f"\nTest with:")
        print(f"  xdg-open '{args.scheme}://desktop/run?dir=.'")
    else:
        print(f"✗ Failed to register {args.scheme}:// scheme", file=sys.stderr)
        sys.exit(1)


def cmd_unregister(args):
    """Unregister the URI scheme."""
    launcher = URILauncher(args.scheme)
    
    if launcher.unregister():
        print(f"✓ Unregistered {args.scheme}:// URI scheme")
    else:
        print(f"✗ Failed to unregister {args.scheme}:// scheme", file=sys.stderr)
        sys.exit(1)


def cmd_status(args):
    """Check registration status."""
    launcher = URILauncher(args.scheme)
    
    if launcher.is_registered():
        handler = launcher.registry.get_handler(args.scheme)
        print(f"✓ {args.scheme}:// is registered")
        if handler:
            print(f"  Handler: {handler}")
    else:
        print(f"✗ {args.scheme}:// is NOT registered")
        print(f"\nTo register, run:")
        print(f"  python -m core.uri_launcher.cli register")


def cmd_launch(args):
    """Launch a URI."""
    launcher = URILauncher(args.scheme)
    
    uri = args.uri
    if not uri.startswith(f"{args.scheme}://"):
        uri = f"{args.scheme}://{uri}"
    
    print(f"Launching: {uri}")
    
    if launcher.launch(uri):
        print("✓ URI launched")
    else:
        print("✗ Failed to launch URI", file=sys.stderr)
        sys.exit(1)


def cmd_test(args):
    """Test URI parsing."""
    launcher = URILauncher(args.scheme)
    
    uri = args.uri
    if not uri.startswith(f"{args.scheme}://"):
        uri = f"{args.scheme}://{uri}"
    
    parsed = launcher.parse(uri)
    
    print(f"URI: {uri}")
    print(f"  Scheme:   {parsed['scheme']}")
    print(f"  Host:     {parsed['host']}")
    print(f"  Path:     {parsed['path']}")
    print(f"  Params:   {parsed['params']}")
    print(f"  Fragment: {parsed['fragment']}")


def cmd_build(args):
    """Build a URI from components."""
    launcher = URILauncher(args.scheme)
    
    params = {}
    if args.params:
        for p in args.params:
            if "=" in p:
                k, v = p.split("=", 1)
                params[k] = v
    
    uri = launcher.build_uri(
        path=args.path or "",
        host=args.host or "",
        params=params if params else None
    )
    
    print(uri)


def main():
    parser = argparse.ArgumentParser(
        description="Analytica URI Launcher CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Register the scheme:
    %(prog)s register
    
  Launch a URI:
    %(prog)s launch "analytica://desktop/run?dir=/path/to/project"
    
  Check status:
    %(prog)s status
    
  Build a URI:
    %(prog)s build --path desktop/run --params dir=/home/user/project url=http://localhost:18000
"""
    )
    
    parser.add_argument(
        "--scheme", "-s",
        default="analytica",
        help="URI scheme name (default: analytica)"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    reg_parser = subparsers.add_parser("register", help="Register URI scheme")
    reg_parser.add_argument("--terminal", "-t", action="store_true", help="Run handler in terminal")
    reg_parser.set_defaults(func=cmd_register)
    
    unreg_parser = subparsers.add_parser("unregister", help="Unregister URI scheme")
    unreg_parser.set_defaults(func=cmd_unregister)
    
    status_parser = subparsers.add_parser("status", help="Check registration status")
    status_parser.set_defaults(func=cmd_status)
    
    launch_parser = subparsers.add_parser("launch", help="Launch a URI")
    launch_parser.add_argument("uri", help="URI to launch")
    launch_parser.set_defaults(func=cmd_launch)
    
    test_parser = subparsers.add_parser("test", help="Test URI parsing")
    test_parser.add_argument("uri", help="URI to parse")
    test_parser.set_defaults(func=cmd_test)
    
    build_parser = subparsers.add_parser("build", help="Build a URI")
    build_parser.add_argument("--path", "-p", help="URI path")
    build_parser.add_argument("--host", "-H", help="URI host")
    build_parser.add_argument("--params", "-P", nargs="*", help="Parameters (key=value)")
    build_parser.set_defaults(func=cmd_build)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    args.func(args)


if __name__ == "__main__":
    main()
