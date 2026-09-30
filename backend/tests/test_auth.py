def test_register_user(client):
    response = client.post(
        "/api/auth/register",
        json={"name": "Alice User", "email": "alice@example.com", "password": "securepassword"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "alice@example.com"

def test_login_user(client, test_user):
    response = client.post(
        "/api/auth/login",
        json={"email": "nikhil@example.com", "password": "testpassword123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "nikhil@example.com"

def test_get_me(client, auth_headers):
    response = client.get("/api/auth/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "nikhil@example.com"
