import os
from pathlib import Path

os.environ["DATABASE_URL"] = "sqlite:///./test_voyageai.db"

from fastapi.testclient import TestClient

from app.main import Base, engine, app


def setup_module():
    Base.metadata.drop_all(engine)
    with TestClient(app):
        pass


def teardown_module():
    Base.metadata.drop_all(engine)
    engine.dispose()
    Path("test_voyageai.db").unlink(missing_ok=True)


def token(client, email, password):
    response = client.post("/api/auth/login", data={"username": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def test_client_request_workflow():
    with TestClient(app) as client:
        access = token(client, "client@acme.demo", "Client123!")
        headers = {"Authorization": f"Bearer {access}"}
        created = client.post(
            "/api/travel/requests",
            headers=headers,
            json={
                "service_type": "flight",
                "origin": "Coimbatore",
                "destination": "Delhi",
                "start_date": "2026-09-10",
                "end_date": "2026-09-14",
                "travelers": 2,
                "budget": 30000,
            },
        )
        assert created.status_code == 201
        request_id = created.json()["id"]
        updated = client.patch(
            f"/api/travel/requests/{request_id}",
            headers=headers,
            json={"travelers": 3, "notes": "Aisle seats"},
        )
        assert updated.status_code == 200
        assert updated.json()["travelers"] == 3
        assert len(client.get("/api/travel/requests", headers=headers).json()) == 1


def test_admin_onboarding_and_reports():
    with TestClient(app) as client:
        access = token(client, "admin@voyageai.demo", "Admin123!")
        headers = {"Authorization": f"Bearer {access}"}
        organization = client.post(
            "/api/organizations",
            headers=headers,
            json={"name": "Globex India", "code": "GLOBEX", "billing_email": "billing@globex.demo"},
        )
        assert organization.status_code == 201
        new_user = client.post(
            "/api/users",
            headers=headers,
            json={
                "email": "traveler@globex.demo",
                "full_name": "Demo Traveler",
                "password": "Secure123!",
                "role": "client",
                "organization_id": organization.json()["id"],
            },
        )
        assert new_user.status_code == 201
        report = client.get("/api/reports/summary", headers=headers)
        assert report.status_code == 200
        assert report.json()["organizations"] == 2


def test_inventory_and_itinerary():
    with TestClient(app) as client:
        access = token(client, "client@acme.demo", "Client123!")
        headers = {"Authorization": f"Bearer {access}"}
        results = client.get(
            "/api/travel/search?service=hotel&destination=Goa&travelers=2",
            headers=headers,
        )
        assert results.status_code == 200
        assert len(results.json()["results"]) == 3
        plan = client.post(
            "/api/ai/itinerary",
            headers=headers,
            json={
                "destination": "Goa",
                "start_date": "2026-10-01",
                "end_date": "2026-10-03",
                "interests": ["beaches", "food"],
                "budget": 25000,
            },
        )
        assert plan.status_code == 200
        assert len(plan.json()["schedule"]) == 3


def test_profile_booking_payment_and_invoice_workflow():
    with TestClient(app) as client:
        client_token = token(client, "client@acme.demo", "Client123!")
        client_headers = {"Authorization": f"Bearer {client_token}"}
        profile = client.patch(
            "/api/profile",
            headers=client_headers,
            json={"phone": "+91 98888 77777", "preferences": {"seat": "window"}},
        )
        assert profile.status_code == 200
        assert profile.json()["preferences"]["seat"] == "window"

        requests = client.get("/api/travel/requests", headers=client_headers).json()
        assert requests
        request_id = requests[0]["id"]

        admin_token = token(client, "admin@voyageai.demo", "Admin123!")
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        booking = client.post(
            "/api/bookings",
            headers=admin_headers,
            json={
                "request_id": request_id,
                "provider": "VoyageAI Test Inventory",
                "item": {"name": "SkyJet Flex", "fare": "business"},
                "total_amount": 25000,
                "currency": "INR",
            },
        )
        assert booking.status_code == 201
        booking_id = booking.json()["id"]

        order = client.post(
            f"/api/payments/{booking_id}/order", headers=client_headers
        )
        assert order.status_code == 200
        assert order.json()["checkout_mode"] == "sandbox"
        confirmed = client.post(
            f"/api/payments/{order.json()['payment_id']}/confirm",
            headers=client_headers,
        )
        assert confirmed.json()["status"] == "paid"
        invoices = client.get("/api/invoices", headers=client_headers).json()
        assert invoices[0]["total"] == 29500


def test_role_isolation_and_input_validation():
    with TestClient(app) as client:
        client_token = token(client, "client@acme.demo", "Client123!")
        headers = {"Authorization": f"Bearer {client_token}"}
        assert client.get("/api/organizations", headers=headers).status_code == 403
        invalid = client.post(
            "/api/travel/requests",
            headers=headers,
            json={
                "service_type": "flight",
                "origin": "Delhi",
                "destination": "Mumbai",
                "start_date": "2026-12-10",
                "end_date": "2026-12-01",
                "travelers": 1,
            },
        )
        assert invalid.status_code == 422
