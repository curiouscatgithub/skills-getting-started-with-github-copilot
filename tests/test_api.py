"""
Tests for the Mergington High School API
"""
import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities database before each test"""
    activities.clear()
    activities.update({
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
    })


def test_root_redirect(client):
    """Test that root redirects to static/index.html"""
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities(client):
    """Test getting all activities"""
    response = client.get("/activities")
    assert response.status_code == 200
    data = response.json()
    assert "Chess Club" in data
    assert "Programming Class" in data
    assert data["Chess Club"]["max_participants"] == 12
    assert len(data["Chess Club"]["participants"]) == 2


def test_signup_for_activity_success(client):
    """Test successfully signing up for an activity"""
    response = client.post(
        "/activities/Chess Club/signup?email=newstudent@mergington.edu"
    )
    assert response.status_code == 200
    data = response.json()
    assert "Signed up newstudent@mergington.edu for Chess Club" in data["message"]
    
    # Verify the participant was added
    activities_response = client.get("/activities")
    activities_data = activities_response.json()
    assert "newstudent@mergington.edu" in activities_data["Chess Club"]["participants"]


def test_signup_for_nonexistent_activity(client):
    """Test signing up for an activity that doesn't exist"""
    response = client.post(
        "/activities/Nonexistent Club/signup?email=student@mergington.edu"
    )
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Activity not found"


def test_signup_duplicate_participant(client):
    """Test that a student cannot sign up twice for the same activity"""
    # First signup
    response = client.post(
        "/activities/Chess Club/signup?email=test@mergington.edu"
    )
    assert response.status_code == 200
    
    # Try to signup again
    response = client.post(
        "/activities/Chess Club/signup?email=test@mergington.edu"
    )
    assert response.status_code == 400
    data = response.json()
    assert data["detail"] == "Student already signed up for this activity"


def test_unregister_participant_success(client):
    """Test successfully unregistering a participant"""
    # First, add a participant
    client.post("/activities/Chess Club/signup?email=temp@mergington.edu")
    
    # Now unregister them
    response = client.delete(
        "/activities/Chess Club/participants/temp@mergington.edu"
    )
    assert response.status_code == 200
    data = response.json()
    assert "Unregistered temp@mergington.edu from Chess Club" in data["message"]
    
    # Verify the participant was removed
    activities_response = client.get("/activities")
    activities_data = activities_response.json()
    assert "temp@mergington.edu" not in activities_data["Chess Club"]["participants"]


def test_unregister_participant_not_found(client):
    """Test unregistering a participant that is not signed up"""
    response = client.delete(
        "/activities/Chess Club/participants/notregistered@mergington.edu"
    )
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Student not found in this activity"


def test_unregister_from_nonexistent_activity(client):
    """Test unregistering from an activity that doesn't exist"""
    response = client.delete(
        "/activities/Nonexistent Club/participants/student@mergington.edu"
    )
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Activity not found"


def test_activities_participants_list(client):
    """Test that participants list is properly maintained"""
    # Get initial count
    response = client.get("/activities")
    initial_count = len(response.json()["Programming Class"]["participants"])
    
    # Add a participant
    client.post("/activities/Programming Class/signup?email=new@mergington.edu")
    
    # Verify count increased
    response = client.get("/activities")
    new_count = len(response.json()["Programming Class"]["participants"])
    assert new_count == initial_count + 1
    
    # Remove a participant
    client.delete("/activities/Programming Class/participants/new@mergington.edu")
    
    # Verify count decreased
    response = client.get("/activities")
    final_count = len(response.json()["Programming Class"]["participants"])
    assert final_count == initial_count
