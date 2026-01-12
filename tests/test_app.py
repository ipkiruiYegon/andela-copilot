import pytest


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_activities_success(self, client):
        """Test that we can retrieve all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) > 0
        assert "Chess Club" in data

    def test_get_activities_has_required_fields(self, client):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_info in data.items():
            assert "description" in activity_info
            assert "schedule" in activity_info
            assert "max_participants" in activity_info
            assert "participants" in activity_info
            assert isinstance(activity_info["participants"], list)

    def test_get_activities_chess_club(self, client):
        """Test specific activity details"""
        response = client.get("/activities")
        data = response.json()
        
        chess_club = data["Chess Club"]
        assert chess_club["max_participants"] == 12
        assert "michael@mergington.edu" in chess_club["participants"]
        assert "daniel@mergington.edu" in chess_club["participants"]


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_success(self, client):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Basketball/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]
        assert "Basketball" in data["message"]

    def test_signup_adds_participant(self, client):
        """Test that signup actually adds the participant"""
        client.post(
            "/activities/Tennis Club/signup?email=newstudent@mergington.edu"
        )
        
        response = client.get("/activities")
        activities = response.json()
        assert "newstudent@mergington.edu" in activities["Tennis Club"]["participants"]

    def test_signup_activity_not_found(self, client):
        """Test signup for non-existent activity"""
        response = client.post(
            "/activities/Nonexistent Club/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_signup_already_registered(self, client):
        """Test that a student cannot sign up twice"""
        response = client.post(
            "/activities/Chess Club/signup?email=michael@mergington.edu"
        )
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]

    def test_signup_updates_availability(self, client):
        """Test that available spots decrease after signup"""
        response = client.get("/activities")
        initial_spots = (
            response.json()["Basketball"]["max_participants"]
            - len(response.json()["Basketball"]["participants"])
        )
        
        client.post(
            "/activities/Basketball/signup?email=newstudent@mergington.edu"
        )
        
        response = client.get("/activities")
        new_spots = (
            response.json()["Basketball"]["max_participants"]
            - len(response.json()["Basketball"]["participants"])
        )
        
        assert new_spots == initial_spots - 1

    def test_signup_multiple_students(self, client):
        """Test signing up multiple different students"""
        emails = ["student1@mergington.edu", "student2@mergington.edu", "student3@mergington.edu"]
        
        for email in emails:
            response = client.post(
                f"/activities/Science Club/signup?email={email}"
            )
            assert response.status_code == 200
        
        response = client.get("/activities")
        participants = response.json()["Science Club"]["participants"]
        for email in emails:
            assert email in participants


class TestUnregisterFromActivity:
    """Tests for POST /activities/{activity_name}/unregister endpoint"""

    def test_unregister_success(self, client):
        """Test successful unregistration from an activity"""
        response = client.post(
            "/activities/Chess Club/unregister?email=michael@mergington.edu"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "michael@mergington.edu" in data["message"]
        assert "Chess Club" in data["message"]

    def test_unregister_removes_participant(self, client):
        """Test that unregister actually removes the participant"""
        client.post(
            "/activities/Chess Club/unregister?email=michael@mergington.edu"
        )
        
        response = client.get("/activities")
        activities = response.json()
        assert "michael@mergington.edu" not in activities["Chess Club"]["participants"]

    def test_unregister_activity_not_found(self, client):
        """Test unregister from non-existent activity"""
        response = client.post(
            "/activities/Nonexistent Club/unregister?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_unregister_not_registered(self, client):
        """Test that unregister fails if student is not registered"""
        response = client.post(
            "/activities/Chess Club/unregister?email=notregistered@mergington.edu"
        )
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"]

    def test_unregister_then_can_signup(self, client):
        """Test that a student can sign up after unregistering"""
        # Unregister
        client.post(
            "/activities/Basketball/unregister?email=alex@mergington.edu"
        )
        
        # Sign up again
        response = client.post(
            "/activities/Basketball/signup?email=alex@mergington.edu"
        )
        assert response.status_code == 200
        
        # Verify participant is registered
        response = client.get("/activities")
        assert "alex@mergington.edu" in response.json()["Basketball"]["participants"]

    def test_unregister_increases_availability(self, client):
        """Test that available spots increase after unregister"""
        response = client.get("/activities")
        initial_spots = (
            response.json()["Chess Club"]["max_participants"]
            - len(response.json()["Chess Club"]["participants"])
        )
        
        client.post(
            "/activities/Chess Club/unregister?email=daniel@mergington.edu"
        )
        
        response = client.get("/activities")
        new_spots = (
            response.json()["Chess Club"]["max_participants"]
            - len(response.json()["Chess Club"]["participants"])
        )
        
        assert new_spots == initial_spots + 1


class TestRootEndpoint:
    """Tests for GET / endpoint"""

    def test_root_redirect(self, client):
        """Test that root endpoint redirects to static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]
