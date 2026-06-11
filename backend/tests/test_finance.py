import uuid
from datetime import date

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _register_and_login(email: str | None = None, password: str = "Test1234") -> str:
    email = email or f"user-{uuid.uuid4().hex[:8]}@test.com"
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": "Finance Tester"},
    )
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    return response.json()["access_token"]


def test_categories_and_transaction_flow() -> None:
    token = _register_and_login()
    headers = {"Authorization": f"Bearer {token}"}

    categories = client.get("/api/v1/finance/categories?type=expense", headers=headers)
    assert categories.status_code == 200
    expense_categories = categories.json()
    assert len(expense_categories) >= 1

    create_response = client.post(
        "/api/v1/finance/transactions",
        headers=headers,
        json={
            "category_id": expense_categories[0]["id"],
            "amount": "150.50",
            "type": "expense",
            "description": "Cumpărături",
            "transaction_date": date.today().isoformat(),
        },
    )
    assert create_response.status_code == 201

    summary = client.get("/api/v1/finance/analytics/summary", headers=headers)
    assert summary.status_code == 200
    data = summary.json()
    assert float(data["month_expenses"]) == 150.50

    breakdown = client.get("/api/v1/finance/analytics/spending-by-category", headers=headers)
    assert breakdown.status_code == 200
    assert len(breakdown.json()) >= 1

    trend = client.get("/api/v1/finance/analytics/monthly-trend", headers=headers)
    assert trend.status_code == 200
    assert len(trend.json()) == 6


def test_budgets_and_balance_trend() -> None:
    token = _register_and_login()
    headers = {"Authorization": f"Bearer {token}"}
    today = date.today()

    categories = client.get("/api/v1/finance/categories?type=expense", headers=headers).json()
    category_id = categories[0]["id"]

    client.post(
        "/api/v1/finance/transactions",
        headers=headers,
        json={
            "category_id": category_id,
            "amount": "200.00",
            "type": "expense",
            "transaction_date": today.isoformat(),
        },
    )

    budget = client.put(
        "/api/v1/finance/budgets",
        headers=headers,
        json={
            "category_id": category_id,
            "year": today.year,
            "month": today.month,
            "amount": "500.00",
        },
    )
    assert budget.status_code == 200
    assert float(budget.json()["usage_percent"]) == 40.0

    balance = client.get("/api/v1/finance/analytics/balance-trend", headers=headers)
    assert balance.status_code == 200
    assert len(balance.json()) == 6

    filtered = client.get(
        f"/api/v1/finance/transactions?month={today.month}&year={today.year}",
        headers=headers,
    )
    assert filtered.status_code == 200
    assert len(filtered.json()) == 1
