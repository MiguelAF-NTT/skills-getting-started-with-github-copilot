import copy
from contextlib import contextmanager

from fastapi.testclient import TestClient

from src.app import app, activities

client = TestClient(app)


@contextmanager
def preserve_activities_state():
    original = copy.deepcopy(activities)
    try:
        yield
    finally:
        activities.clear()
        activities.update(copy.deepcopy(original))


def test_root_redirects_to_static_index():
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_all_activities():
    response = client.get("/activities")

    assert response.status_code == 200
    assert isinstance(response.json(), dict)
    assert "Chess Club" in response.json()


def test_signup_for_activity_adds_participant():
    activity_name = "Debate Team"
    email = "student@example.com"

    with preserve_activities_state():
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email},
        )

        assert response.status_code == 200
        assert response.json()["message"] == f"Signed up {email} for {activity_name}"

        activity = activities[activity_name]
        assert email in activity["participants"]


def test_signup_for_activity_already_registered_returns_400():
    activity_name = "Chess Club"
    existing_email = activities[activity_name]["participants"][0]

    with preserve_activities_state():
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": existing_email},
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "Student is already signed up for this activity"


def test_unregister_from_activity_removes_participant():
    activity_name = "Swimming Club"
    email = "newstudent@example.com"

    with preserve_activities_state():
        signup = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email},
        )
        assert signup.status_code == 200

        response = client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": email},
        )

        assert response.status_code == 200
        assert response.json()["message"] == f"Removed {email} from {activity_name}"
        assert email not in activities[activity_name]["participants"]


def test_unregister_missing_participant_returns_404():
    activity_name = "Gym Class"
    missing_email = "missing@example.com"

    with preserve_activities_state():
        response = client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": missing_email},
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Participant not found"
