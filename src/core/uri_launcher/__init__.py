"""
Analytica URI Launcher
======================
Library for registering and handling custom URI schemes on Linux.

Similar to Android intents, allows launching applications from URIs like:
    analytica://desktop/run?project=myapp
    analytica://mobile/preview?hash=abc123

Usage:
    from core.uri_launcher import URILauncher
    
    launcher = URILauncher("analytica")
    launcher.register()  # Register the scheme system-wide
    launcher.launch("analytica://desktop/run")  # Open URI
"""

from .launcher import URILauncher, URIHandler, URISchemeRegistry

__all__ = ["URILauncher", "URIHandler", "URISchemeRegistry"]
