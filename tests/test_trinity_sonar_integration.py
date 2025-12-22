import os
import json
import types
import pytest

from core.trinity import TrinityRuntime


class DummyResp:
    def __init__(self, status_code=200, data=None):
        self.status_code = status_code
        self._data = data or {}

    def json(self):
        return self._data


def _mock_requests_get(url, params=None, auth=None, timeout=None):
    # Simple URL routing for tests
    if "/api/issues/search" in url:
        return DummyResp(200, {"total": 2, "issues": [
            {"key": "i1", "message": "Leak", "severity": "CRITICAL", "component": "a.py", "textRange": {"startLine": 10}, "rule": "py:leak"},
            {"key": "i2", "message": "Raw types", "severity": "MAJOR", "component": "b.py", "textRange": {"startLine": 20}, "rule": "py:raw"}
        ]})
    if "/api/qualitygates/project_status" in url:
        return DummyResp(200, {"projectStatus": {"status": "OK", "conditions": []}})
    return DummyResp(404, {})


def test_fetch_sonar_issues_no_api_key(monkeypatch):
    monkeypatch.delenv("SONAR_API_KEY", raising=False)
    monkeypatch.setenv("COPILOT_API_KEY", "dummy")
    rt = TrinityRuntime(verbose=False)
    assert rt._fetch_sonar_issues() is None


def test_fetch_sonar_issues_success(monkeypatch):
    monkeypatch.setenv("SONAR_API_KEY", "dummy")
    monkeypatch.setenv("SONAR_URL", "https://sonarcloud.io")
    monkeypatch.setenv("SONAR_PROJECT_KEY", "test_proj")
    monkeypatch.setenv("COPILOT_API_KEY", "dummy")

    monkeypatch.setattr("requests.get", _mock_requests_get)

    rt = TrinityRuntime(verbose=False)
    res = rt._fetch_sonar_issues()
    assert res is not None
    assert res.get("project_key") == "test_proj"
    assert res.get("issues_count") == 2
    assert isinstance(res.get("issues"), list)


def test_pause_includes_sonar(monkeypatch):
    monkeypatch.setenv("SONAR_API_KEY", "dummy")
    monkeypatch.setenv("SONAR_URL", "https://sonarcloud.io")
    monkeypatch.setenv("SONAR_PROJECT_KEY", "test_proj")
    monkeypatch.setenv("COPILOT_API_KEY", "dummy")
    monkeypatch.setattr("requests.get", _mock_requests_get)

    rt = TrinityRuntime(verbose=False)

    state = {
        "original_task": "Make a dev change",
        "plan": [{"description": "edit file", "tools": [{"name": "write_file", "args": {"path": "x"}}]}]
    }

    new_state = rt._create_vibe_assistant_pause_state(state, "doctor_vibe_dev", "Doctor Vibe: Manual dev intervention required for this step")
    assert new_state.get("vibe_assistant_pause") is not None
    diags = new_state["vibe_assistant_pause"].get("diagnostics") or {}
    assert "sonar" in diags
    assert diags["sonar"]["issues_count"] == 2


def test_proactive_sonar_enrichment(monkeypatch):
    monkeypatch.setenv("SONAR_API_KEY", "dummy")
    monkeypatch.setenv("SONAR_URL", "https://sonarcloud.io")
    monkeypatch.setenv("SONAR_PROJECT_KEY", "test_proj")
    monkeypatch.setenv("COPILOT_API_KEY", "dummy")
    monkeypatch.setattr("requests.get", _mock_requests_get)

    rt = TrinityRuntime(verbose=False)
    state = {"is_dev": True, "retrieved_context": "", "original_task": "Make dev change"}
    new_state = rt._enrich_context_with_sonar(state)
    assert "SonarQube summary" in new_state.get("retrieved_context", "")
    assert "test_proj" in new_state.get("retrieved_context", "")
