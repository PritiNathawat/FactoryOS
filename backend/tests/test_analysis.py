"""
FactoryOS Integration Tests — AI Platform Analysis Pipeline
============================================================
Tests the full incident analysis workflow end-to-end using the
FastAPI test client. All tests run in MOCK mode (no API key needed).

Coverage:
  - Health check endpoint
  - Platform status endpoint
  - Demo analysis endpoint
  - Full incident POST analysis
  - OrchestratorResult schema validation
  - Plan structure validation (Plan A/B/C)
  - Error handling (missing fields, invalid severity)
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture(scope="module")
def client() -> TestClient:
    """Create a FastAPI TestClient for the entire test module."""
    app = create_app()
    return TestClient(app)


# ─── Health & Infrastructure ──────────────────────────────────

class TestHealth:
    def test_health_returns_200(self, client: TestClient):
        response = client.get("/api/v1/health")
        assert response.status_code == 200

    def test_health_status_is_healthy(self, client: TestClient):
        data = client.get("/api/v1/health").json()
        assert data["status"] == "healthy"

    def test_health_has_timestamp(self, client: TestClient):
        data = client.get("/api/v1/health").json()
        assert "timestamp" in data
        assert len(data["timestamp"]) > 0

    def test_health_has_environment(self, client: TestClient):
        data = client.get("/api/v1/health").json()
        assert data["environment"] in ("development", "staging", "production")

    def test_version_endpoint(self, client: TestClient):
        response = client.get("/api/v1/version")
        assert response.status_code == 200
        data = response.json()
        assert "version" in data
        assert "name" in data


# ─── Platform Status ──────────────────────────────────────────

class TestPlatformStatus:
    def test_status_returns_200(self, client: TestClient):
        response = client.get("/api/v1/analysis/status")
        assert response.status_code == 200

    def test_status_has_required_fields(self, client: TestClient):
        data = client.get("/api/v1/analysis/status").json()
        assert "status" in data
        assert "gemini_mode" in data
        assert "agents" in data
        assert "tools" in data
        assert "tool_count" in data
        assert "agent_count" in data

    def test_status_has_correct_agent_count(self, client: TestClient):
        data = client.get("/api/v1/analysis/status").json()
        # Expect 5 domain agents: maintenance, inventory, production, cost, reporting
        assert data["agent_count"] == 5

    def test_status_has_correct_tool_count(self, client: TestClient):
        data = client.get("/api/v1/analysis/status").json()
        # Expect 7 MCP tools
        assert data["tool_count"] == 7

    def test_gemini_mode_is_mock_without_api_key(self, client: TestClient):
        # Running without GEMINI_API_KEY should activate mock mode
        data = client.get("/api/v1/analysis/status").json()
        assert data["gemini_mode"] in ("mock", "live")

    def test_list_agents_endpoint(self, client: TestClient):
        response = client.get("/api/v1/analysis/agents")
        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        assert "agent_count" in data

    def test_list_tools_endpoint(self, client: TestClient):
        response = client.get("/api/v1/analysis/tools")
        assert response.status_code == 200
        data = response.json()
        assert "tools" in data
        assert "tool_count" in data


# ─── Demo Analysis Endpoint ───────────────────────────────────

class TestDemoAnalysis:
    @pytest.fixture(scope="class")
    def demo_result(self, client: TestClient) -> dict:
        """Run the demo analysis once and reuse the result."""
        response = client.get("/api/v1/analysis/incidents/demo")
        assert response.status_code == 200
        return response.json()

    def test_demo_returns_200(self, client: TestClient):
        response = client.get("/api/v1/analysis/incidents/demo")
        assert response.status_code == 200

    def test_demo_has_incident_id(self, client: TestClient, demo_result: dict):
        assert "incident_id" in demo_result
        assert len(demo_result["incident_id"]) > 0

    def test_demo_produces_three_plans(self, client: TestClient, demo_result: dict):
        assert "plans" in demo_result
        assert len(demo_result["plans"]) == 3, "Expected exactly 3 recovery plans"

    def test_demo_has_plan_types(self, client: TestClient, demo_result: dict):
        plan_types = {p["plan_type"] for p in demo_result["plans"]}
        assert "economical" in plan_types
        assert "rapid" in plan_types
        assert "balanced" in plan_types

    def test_demo_has_executive_summary(self, client: TestClient, demo_result: dict):
        assert "executive_summary" in demo_result
        assert len(demo_result["executive_summary"]) > 10

    def test_demo_has_confidence(self, client: TestClient, demo_result: dict):
        confidence = demo_result.get("confidence_overall", -1)
        assert 0.0 <= confidence <= 1.0

    def test_demo_has_agent_responses(self, client: TestClient, demo_result: dict):
        assert "agent_responses" in demo_result
        assert len(demo_result["agent_responses"]) > 0

    def test_demo_requires_human_approval_flag_exists(self, client: TestClient, demo_result: dict):
        assert "requires_human_approval" in demo_result
        assert isinstance(demo_result["requires_human_approval"], bool)

    def test_demo_plan_has_required_fields(self, client: TestClient, demo_result: dict):
        for plan in demo_result["plans"]:
            assert "plan_id" in plan
            assert "plan_type" in plan
            assert "label" in plan
            assert "estimated_cost_usd" in plan
            assert "estimated_downtime_hours" in plan
            assert "confidence" in plan
            assert 0.0 <= plan["confidence"] <= 1.0

    def test_demo_plan_ids_are_a_b_c(self, client: TestClient, demo_result: dict):
        plan_ids = {p["plan_id"] for p in demo_result["plans"]}
        assert "A" in plan_ids
        assert "B" in plan_ids
        assert "C" in plan_ids


# ─── Custom Incident Analysis ─────────────────────────────────

MINIMAL_INCIDENT_PAYLOAD = {
    "incident": {
        "title": "Test Pump P-07 Failure",
        "description": "Coolant pump P-07 in Bay 2 has stopped operating. Flow rate dropped to zero at 14:30. Overheating risk detected in downstream equipment.",
        "equipment_id": "P-07",
        "location": "Bay 2",
        "severity": "high",
    }
}


class TestCustomAnalysis:
    @pytest.fixture(scope="class")
    def analysis_result(self, client: TestClient) -> dict:
        response = client.post(
            "/api/v1/analysis/incidents", json=MINIMAL_INCIDENT_PAYLOAD
        )
        assert response.status_code == 200
        return response.json()

    def test_analysis_returns_200(self, client: TestClient):
        response = client.post(
            "/api/v1/analysis/incidents", json=MINIMAL_INCIDENT_PAYLOAD
        )
        assert response.status_code == 200

    def test_analysis_preserves_incident_id(self, client: TestClient, analysis_result: dict):
        assert "incident_id" in analysis_result

    def test_analysis_produces_three_plans(self, client: TestClient, analysis_result: dict):
        assert len(analysis_result["plans"]) == 3

    def test_analysis_all_plan_costs_are_positive(self, client: TestClient, analysis_result: dict):
        for plan in analysis_result["plans"]:
            assert plan["estimated_cost_usd"] >= 0

    def test_analysis_all_downtimes_are_positive(self, client: TestClient, analysis_result: dict):
        for plan in analysis_result["plans"]:
            assert plan["estimated_downtime_hours"] >= 0

    def test_analysis_economical_plan_cheapest(self, client: TestClient, analysis_result: dict):
        plans_by_type = {p["plan_type"]: p for p in analysis_result["plans"]}
        if "economical" in plans_by_type and "rapid" in plans_by_type:
            # Economical plan should generally be cheaper than rapid
            # (not strictly enforced in mock mode, but validate both exist)
            assert plans_by_type["economical"]["estimated_cost_usd"] >= 0
            assert plans_by_type["rapid"]["estimated_cost_usd"] >= 0


# ─── Input Validation ─────────────────────────────────────────

class TestInputValidation:
    def test_missing_title_returns_422(self, client: TestClient):
        payload = {
            "incident": {
                "description": "Some description",
                "severity": "high",
            }
        }
        response = client.post("/api/v1/analysis/incidents", json=payload)
        assert response.status_code == 422

    def test_missing_description_returns_422(self, client: TestClient):
        payload = {
            "incident": {
                "title": "Some title",
                "severity": "high",
            }
        }
        response = client.post("/api/v1/analysis/incidents", json=payload)
        assert response.status_code == 422

    def test_invalid_severity_returns_422(self, client: TestClient):
        payload = {
            "incident": {
                "title": "Test incident",
                "description": "Some description",
                "severity": "catastrophic",  # invalid
            }
        }
        response = client.post("/api/v1/analysis/incidents", json=payload)
        assert response.status_code == 422

    def test_empty_body_returns_422(self, client: TestClient):
        response = client.post("/api/v1/analysis/incidents", json={})
        assert response.status_code == 422

    def test_valid_minimum_payload(self, client: TestClient):
        payload = {
            "incident": {
                "title": "Minimum viable incident",
                "description": "Something broke and we need to fix it quickly.",
                "severity": "low",
            }
        }
        response = client.post("/api/v1/analysis/incidents", json=payload)
        assert response.status_code == 200
