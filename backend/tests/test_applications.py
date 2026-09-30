def test_create_and_list_applications(client, auth_headers):
    # Create app
    payload = {
        "company": "ABC Technologies",
        "job_title": "Python Backend Developer",
        "hr_name": "Jane Recruiter",
        "hr_email": "jane@abctech.com",
        "subject": "Application for Python Backend Developer",
        "initial_email_body": "Hello, I am applying for the Python Backend Developer role..."
    }
    response = client.post("/api/applications", json=payload, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["company"] == "ABC Technologies"
    assert data["status"] == "follow_up_scheduled"
    assert len(data["follow_ups"]) >= 1
    assert data["follow_ups"][0]["status"] == "scheduled"

    # List apps
    list_resp = client.get("/api/applications", headers=auth_headers)
    assert list_resp.status_code == 200
    apps_data = list_resp.json()
    assert len(apps_data) == 1
    assert apps_data[0]["company"] == "ABC Technologies"
