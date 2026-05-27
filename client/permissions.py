"""
Permission Manager - RBAC + Policy Validation

Enforces tool call permissions, URL whitelisting, file access controls,
and resource limits as defined in configs/permissions.yaml.
"""

import ipaddress
import os
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import yaml


class PermissionError_(Exception):
    """Raised when a permission check fails."""


class PermissionManager:
    """Validates tool calls, URLs, file access, and resource limits."""

    def __init__(self, config_path: str | None = None):
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "configs",
                "permissions.yaml",
            )

        with open(config_path, encoding="utf-8") as f:
            self._config = yaml.safe_load(f)

        self._url_whitelist = self._config.get("url_whitelist", {})
        self._url_blacklist = self._config.get("url_blacklist", {})
        self._approved_commodities = self._config.get("approved_commodities", [])
        self._limits = self._config.get("resource_limits", {})
        self._tool_perms = self._config.get("tools", {})

    def validate_tool_call(self, tool_name: str, role: str, params: dict[str, Any]) -> None:
        """Validate that a role is allowed to call a tool with given params."""
        tool_config = self._tool_perms.get(tool_name)
        if not tool_config:
            raise PermissionError_(f"Unknown tool: {tool_name}")

        allowed_roles = tool_config.get("allowed_roles", [])
        if role not in allowed_roles:
            raise PermissionError_(
                f"Role '{role}' not allowed to call '{tool_name}'. "
                f"Allowed: {allowed_roles}"
            )

        constraints = tool_config.get("constraints", {})
        self._validate_constraints(tool_name, constraints, params)

    def validate_url(self, url: str) -> None:
        """Validate a URL against whitelist and blacklist."""
        # Skip validation for unresolved template strings
        if "{{" in url:
            return
        try:
            parsed = urlparse(url)
        except Exception:
            raise PermissionError_(f"Invalid URL: {url}")

        # Check scheme blacklist
        denied_schemes = self._url_blacklist.get("schemes", [])
        if parsed.scheme in denied_schemes:
            raise PermissionError_(f"URL scheme '{parsed.scheme}' is blocked: {url}")

        # Check domain blacklist
        hostname = parsed.hostname or ""
        if self._is_blacklisted_host(hostname):
            raise PermissionError_(f"URL hostname '{hostname}' is blocked: {url}")

        # Check domain whitelist
        allowed_domains = self._url_whitelist.get("domains", [])
        if allowed_domains and not any(
            hostname == domain or hostname.endswith("." + domain)
            for domain in allowed_domains
        ):
            raise PermissionError_(
                f"URL domain '{hostname}' not in whitelist: {url}"
            )

    def validate_file_access(self, file_path: str) -> None:
        """Validate that a file path is within allowed directories."""
        resolved = str(Path(file_path).resolve())

        denied = self._config.get("file_access", {}).get("denied_paths", [])
        for denied_pattern in denied:
            if denied_pattern in resolved:
                raise PermissionError_(f"File access denied: {file_path}")

        allowed = self._config.get("file_access", {}).get("allowed_paths", [])
        if allowed:
            in_allowed = any(
                resolved.startswith(str(Path(p).resolve()))
                or str(Path(p).resolve()) in resolved
                for p in allowed
            )
            if not in_allowed:
                raise PermissionError_(f"File path not in allowed directories: {file_path}")

    def validate_resource_limits(self, tool_name: str, params: dict[str, Any]) -> None:
        """Check tool parameters against resource limits."""
        if tool_name == "search_news" and "days" in params:
            max_days = self._limits.get("max_news_days", 7)
            if params["days"] > max_days:
                raise PermissionError_(f"days exceeds max {max_days}")

        if tool_name == "get_trend" and "days" in params:
            max_days = self._limits.get("max_trend_days", 30)
            if params["days"] > max_days:
                raise PermissionError_(f"days exceeds max {max_days}")

        if tool_name == "extract_resources":
            max_size = self._limits.get("max_pdf_size_mb", 50)
            # Size check is done at download time

    def _validate_constraints(
        self, tool_name: str, constraints: dict, params: dict[str, Any]
    ) -> None:
        """Validate tool-specific constraints."""
        if constraints.get("url_whitelist_only") and "url" in params:
            self.validate_url(params["url"])

        if constraints.get("commodity_whitelist_only") and "commodity" in params:
            commodity = params["commodity"].lower().replace(" ", "_")
            if commodity not in self._approved_commodities:
                raise PermissionError_(
                    f"Commodity '{params['commodity']}' not in approved list"
                )

        if "days" in constraints and "days" in params:
            d = constraints["days"]
            if params["days"] < d.get("min", 1) or params["days"] > d.get("max", 30):
                raise PermissionError_(
                    f"days must be between {d['min']} and {d['max']}"
                )

        if "file_type" in constraints and "pdf_url" in params:
            url = params["pdf_url"]
            if not url.lower().endswith(".pdf"):
                raise PermissionError_("Only PDF files are allowed")

    def _is_blacklisted_host(self, hostname: str) -> bool:
        """Check if hostname matches blacklist entries (supports CIDR)."""
        for blocked in self._url_blacklist.get("domains", []):
            if "/" in blocked:
                try:
                    network = ipaddress.ip_network(blocked, strict=False)
                    addr = ipaddress.ip_address(hostname)
                    if addr in network:
                        return True
                except ValueError:
                    pass
            elif hostname == blocked:
                return True
        return False
