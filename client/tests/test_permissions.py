"""
Tests for Permission Manager
"""

import os

import pytest

from client.permissions import PermissionError_, PermissionManager


@pytest.fixture
def perm_manager():
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "configs",
        "permissions.yaml",
    )
    return PermissionManager(config_path)


class TestToolPermissions:
    def test_executor_can_search_news(self, perm_manager):
        perm_manager.validate_tool_call("search_news", "executor", {"query": "test", "days": 3})

    def test_planner_cannot_call_tool(self, perm_manager):
        with pytest.raises(PermissionError_):
            perm_manager.validate_tool_call("search_news", "planner", {"query": "test", "days": 3})

    def test_reporter_cannot_call_tool(self, perm_manager):
        with pytest.raises(PermissionError_):
            perm_manager.validate_tool_call("get_price", "reporter", {"commodity": "lithium_carbonate"})

    def test_search_days_exceeds_max(self, perm_manager):
        with pytest.raises(PermissionError_):
            perm_manager.validate_tool_call("search_news", "executor", {"query": "test", "days": 10})

    def test_trend_days_exceeds_max(self, perm_manager):
        with pytest.raises(PermissionError_):
            perm_manager.validate_tool_call("get_trend", "executor", {"commodity": "lithium", "days": 60})


class TestURLValidation:
    def test_allowed_domain(self, perm_manager):
        perm_manager.validate_url("https://www.mining.com/news/article")

    def test_allowed_domain_http(self, perm_manager):
        perm_manager.validate_url("http://www.reuters.com/article")

    def test_blocked_localhost(self, perm_manager):
        with pytest.raises(PermissionError_):
            perm_manager.validate_url("http://localhost:8080/admin")

    def test_blocked_127001(self, perm_manager):
        with pytest.raises(PermissionError_):
            perm_manager.validate_url("http://127.0.0.1/test")

    def test_blocked_file_scheme(self, perm_manager):
        with pytest.raises(PermissionError_):
            perm_manager.validate_url("file:///etc/passwd")

    def test_unknown_domain(self, perm_manager):
        with pytest.raises(PermissionError_):
            perm_manager.validate_url("https://evil.example.com/steal")


class TestCommodityValidation:
    def test_approved_commodity(self, perm_manager):
        perm_manager.validate_tool_call("get_price", "executor", {"commodity": "lithium_carbonate"})

    def test_unapproved_commodity(self, perm_manager):
        with pytest.raises(PermissionError_):
            perm_manager.validate_tool_call("get_price", "executor", {"commodity": "uranium"})


class TestFileAccess:
    def test_allowed_path(self, perm_manager):
        perm_manager.validate_file_access("reports/output.md")

    def test_allowed_tmp(self, perm_manager):
        perm_manager.validate_file_access("/tmp/downloads/report.pdf")

    def test_denied_etc(self, perm_manager):
        with pytest.raises(PermissionError_):
            perm_manager.validate_file_access("/etc/passwd")

    def test_denied_env(self, perm_manager):
        with pytest.raises(PermissionError_):
            perm_manager.validate_file_access(".env")
