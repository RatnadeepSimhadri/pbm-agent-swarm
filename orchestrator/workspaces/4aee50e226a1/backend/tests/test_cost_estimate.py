import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.auth import create_token

client = TestClient(app)


@pytest.fixture
def auth_headers():
    token = create_token(1, "Sarah Johnson")
    return {"Authorization": f"Bearer {token}"}


class TestCostEstimate:
    def test_search_by_drug_name(self, auth_headers):
        """AC1: Member can search for a drug and see copay"""
        response = client.get("/api/cost-estimate?drug_name=metformin", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total_results"] >= 1
        assert data["results"][0]["copay_amount"] == 10.0

    def test_results_include_tier_and_coverage(self, auth_headers):
        """AC2: Results show tier, copay, and coverage details"""
        response = client.get("/api/cost-estimate?drug_name=humira", headers=auth_headers)
        data = response.json()
        result = data["results"][0]
        assert "tier" in result
        assert "copay_amount" in result
        assert "prior_auth_required" in result
        assert "step_therapy_required" in result
        assert "quantity_limit" in result

    def test_partial_search(self, auth_headers):
        """AC3: Search supports partial matching"""
        response = client.get("/api/cost-estimate?drug_name=ator", headers=auth_headers)
        data = response.json()
        assert data["total_results"] >= 1

    def test_different_plans_different_copays(self):
        """AC5: Different plans show different copay amounts"""
        # Gold plan member (id=1)
        gold_token = create_token(1, "Sarah Johnson")
        gold_resp = client.get(
            "/api/cost-estimate?drug_name=metformin",
            headers={"Authorization": f"Bearer {gold_token}"}
        )
        # Bronze plan member (id=5)
        bronze_token = create_token(5, "Priya Patel")
        bronze_resp = client.get(
            "/api/cost-estimate?drug_name=metformin",
            headers={"Authorization": f"Bearer {bronze_token}"}
        )

        gold_copay = gold_resp.json()["results"][0]["copay_amount"]
        bronze_copay = bronze_resp.json()["results"][0]["copay_amount"]
        assert bronze_copay > gold_copay  # Bronze has higher copays

    def test_no_results(self, auth_headers):
        """Edge case: drug not found"""
        response = client.get("/api/cost-estimate?drug_name=zzzznotadrug", headers=auth_headers)
        data = response.json()
        assert data["total_results"] == 0
        assert data["results"] == []
