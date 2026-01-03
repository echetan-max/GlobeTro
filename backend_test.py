import requests
import sys
import json
from datetime import datetime, timedelta

class TravelPlannerAPITester:
    def __init__(self, base_url="https://api-explorer-27.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api"
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
        else:
            print(f"❌ {name} - {details}")
        
        self.test_results.append({
            "test": name,
            "success": success,
            "details": details
        })

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.api_base}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        
        if headers:
            test_headers.update(headers)

        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers)

            success = response.status_code == expected_status
            details = f"Expected {expected_status}, got {response.status_code}"
            
            if not success:
                try:
                    error_data = response.json()
                    details += f" - {error_data.get('detail', 'Unknown error')}"
                except:
                    details += f" - {response.text[:100]}"
            
            self.log_test(name, success, details if not success else "")
            
            return success, response.json() if success and response.content else {}

        except Exception as e:
            self.log_test(name, False, f"Exception: {str(e)}")
            return False, {}

    def test_auth_signup(self):
        """Test user signup"""
        timestamp = datetime.now().strftime('%H%M%S')
        test_user = {
            "name": f"Test User {timestamp}",
            "email": f"test{timestamp}@example.com",
            "password": "TestPass123!"
        }
        
        success, response = self.run_test(
            "User Signup",
            "POST",
            "auth/signup",
            200,
            data=test_user
        )
        
        if success and 'token' in response:
            self.token = response['token']
            self.user_id = response['user']['id']
            self.test_user_email = test_user['email']
            self.test_user_password = test_user['password']
            return True
        return False

    def test_auth_login(self):
        """Test user login"""
        if not hasattr(self, 'test_user_email'):
            return False
            
        login_data = {
            "email": self.test_user_email,
            "password": self.test_user_password
        }
        
        success, response = self.run_test(
            "User Login",
            "POST",
            "auth/login",
            200,
            data=login_data
        )
        
        if success and 'token' in response:
            self.token = response['token']
            return True
        return False

    def test_auth_me(self):
        """Test get current user"""
        success, response = self.run_test(
            "Get Current User",
            "GET",
            "auth/me",
            200
        )
        return success

    def test_cities_get_all(self):
        """Test get all cities"""
        success, response = self.run_test(
            "Get All Cities",
            "GET",
            "cities",
            200
        )
        
        if success and isinstance(response, list) and len(response) > 0:
            self.test_city_id = response[0]['id']
            return True
        return False

    def test_activities_get_all(self):
        """Test get all activities"""
        success, response = self.run_test(
            "Get All Activities",
            "GET",
            "activities",
            200
        )
        
        if success and isinstance(response, list) and len(response) > 0:
            self.test_activity_id = response[0]['id']
            return True
        return False

    def test_trip_create(self):
        """Test create trip"""
        start_date = datetime.now().date()
        end_date = start_date + timedelta(days=7)
        
        trip_data = {
            "name": "Test Trip",
            "description": "A test trip for API testing",
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "cover_photo": "https://example.com/photo.jpg"
        }
        
        success, response = self.run_test(
            "Create Trip",
            "POST",
            "trips",
            200,
            data=trip_data
        )
        
        if success and 'id' in response:
            self.test_trip_id = response['id']
            return True
        return False

    def test_trip_get_all(self):
        """Test get all trips"""
        success, response = self.run_test(
            "Get All Trips",
            "GET",
            "trips",
            200
        )
        return success

    def test_trip_get_by_id(self):
        """Test get trip by ID"""
        if not hasattr(self, 'test_trip_id'):
            return False
            
        success, response = self.run_test(
            "Get Trip by ID",
            "GET",
            f"trips/{self.test_trip_id}",
            200
        )
        return success

    def test_trip_update(self):
        """Test update trip"""
        if not hasattr(self, 'test_trip_id'):
            return False
            
        update_data = {
            "name": "Updated Test Trip",
            "is_public": True
        }
        
        success, response = self.run_test(
            "Update Trip",
            "PUT",
            f"trips/{self.test_trip_id}",
            200,
            data=update_data
        )
        return success

    def test_stop_create(self):
        """Test create stop"""
        if not hasattr(self, 'test_trip_id') or not hasattr(self, 'test_city_id'):
            return False
            
        start_date = datetime.now().date()
        end_date = start_date + timedelta(days=3)
        
        stop_data = {
            "city_id": self.test_city_id,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "order": 0
        }
        
        success, response = self.run_test(
            "Create Stop",
            "POST",
            f"trips/{self.test_trip_id}/stops",
            200,
            data=stop_data
        )
        
        if success and 'id' in response:
            self.test_stop_id = response['id']
            return True
        return False

    def test_stops_get_all(self):
        """Test get all stops for trip"""
        if not hasattr(self, 'test_trip_id'):
            return False
            
        success, response = self.run_test(
            "Get All Stops",
            "GET",
            f"trips/{self.test_trip_id}/stops",
            200
        )
        return success

    def test_trip_activity_create(self):
        """Test add activity to stop"""
        if not hasattr(self, 'test_stop_id') or not hasattr(self, 'test_activity_id'):
            return False
            
        activity_date = datetime.now().date()
        
        activity_data = {
            "activity_id": self.test_activity_id,
            "date": activity_date.isoformat(),
            "time": "10:00",
            "cost": 50.00,
            "notes": "Test activity"
        }
        
        success, response = self.run_test(
            "Add Activity to Stop",
            "POST",
            f"stops/{self.test_stop_id}/activities",
            200,
            data=activity_data
        )
        
        if success and 'id' in response:
            self.test_trip_activity_id = response['id']
            return True
        return False

    def test_trip_activities_get_all(self):
        """Test get all activities for stop"""
        if not hasattr(self, 'test_stop_id'):
            return False
            
        success, response = self.run_test(
            "Get Stop Activities",
            "GET",
            f"stops/{self.test_stop_id}/activities",
            200
        )
        return success

    def test_cost_create(self):
        """Test add cost to trip"""
        if not hasattr(self, 'test_trip_id'):
            return False
            
        cost_data = {
            "category": "transport",
            "amount": 100.00,
            "description": "Flight tickets"
        }
        
        success, response = self.run_test(
            "Add Trip Cost",
            "POST",
            f"trips/{self.test_trip_id}/costs",
            200,
            data=cost_data
        )
        
        if success and 'id' in response:
            self.test_cost_id = response['id']
            return True
        return False

    def test_costs_get_all(self):
        """Test get all costs for trip"""
        if not hasattr(self, 'test_trip_id'):
            return False
            
        success, response = self.run_test(
            "Get Trip Costs",
            "GET",
            f"trips/{self.test_trip_id}/costs",
            200
        )
        return success

    def test_user_profile_get(self):
        """Test get user profile"""
        success, response = self.run_test(
            "Get User Profile",
            "GET",
            "users/profile",
            200
        )
        return success

    def test_user_profile_update(self):
        """Test update user profile"""
        profile_data = {
            "name": "Updated Test User",
            "profile_photo": "https://example.com/avatar.jpg"
        }
        
        success, response = self.run_test(
            "Update User Profile",
            "PUT",
            "users/profile",
            200,
            data=profile_data
        )
        return success

    def test_shared_trip_get(self):
        """Test get shared trip"""
        if not hasattr(self, 'test_trip_id'):
            return False
            
        # First get the trip to get share token
        success, trip_response = self.run_test(
            "Get Trip for Share Token",
            "GET",
            f"trips/{self.test_trip_id}",
            200
        )
        
        if success and 'share_token' in trip_response:
            share_token = trip_response['share_token']
            
            # Test accessing shared trip (should work since we made it public)
            success, response = self.run_test(
                "Get Shared Trip",
                "GET",
                f"trips/shared/{share_token}",
                200
            )
            return success
        return False

    def test_cleanup(self):
        """Clean up test data"""
        cleanup_success = True
        
        # Delete trip activity
        if hasattr(self, 'test_trip_activity_id'):
            success, _ = self.run_test(
                "Delete Trip Activity",
                "DELETE",
                f"trip-activities/{self.test_trip_activity_id}",
                200
            )
            cleanup_success = cleanup_success and success
        
        # Delete cost
        if hasattr(self, 'test_cost_id'):
            success, _ = self.run_test(
                "Delete Trip Cost",
                "DELETE",
                f"costs/{self.test_cost_id}",
                200
            )
            cleanup_success = cleanup_success and success
        
        # Delete stop (this should also delete activities)
        if hasattr(self, 'test_stop_id'):
            success, _ = self.run_test(
                "Delete Stop",
                "DELETE",
                f"stops/{self.test_stop_id}",
                200
            )
            cleanup_success = cleanup_success and success
        
        # Delete trip
        if hasattr(self, 'test_trip_id'):
            success, _ = self.run_test(
                "Delete Trip",
                "DELETE",
                f"trips/{self.test_trip_id}",
                200
            )
            cleanup_success = cleanup_success and success
        
        return cleanup_success

    def run_all_tests(self):
        """Run all tests in sequence"""
        print(f"🚀 Starting Travel Planner API Tests")
        print(f"📍 Backend URL: {self.base_url}")
        print("=" * 60)
        
        # Authentication tests
        print("\n🔐 Authentication Tests")
        if not self.test_auth_signup():
            print("❌ Signup failed, stopping tests")
            return False
        
        if not self.test_auth_login():
            print("❌ Login failed, stopping tests")
            return False
        
        self.test_auth_me()
        
        # Data retrieval tests (cities and activities)
        print("\n🏙️ Cities and Activities Tests")
        self.test_cities_get_all()
        self.test_activities_get_all()
        
        # Trip management tests
        print("\n✈️ Trip Management Tests")
        if not self.test_trip_create():
            print("❌ Trip creation failed, skipping related tests")
            return False
        
        self.test_trip_get_all()
        self.test_trip_get_by_id()
        self.test_trip_update()
        
        # Stop and activity tests
        print("\n📍 Stops and Activities Tests")
        if self.test_stop_create():
            self.test_stops_get_all()
            self.test_trip_activity_create()
            self.test_trip_activities_get_all()
        
        # Cost management tests
        print("\n💰 Cost Management Tests")
        self.test_cost_create()
        self.test_costs_get_all()
        
        # User profile tests
        print("\n👤 User Profile Tests")
        self.test_user_profile_get()
        self.test_user_profile_update()
        
        # Sharing tests
        print("\n🔗 Sharing Tests")
        self.test_shared_trip_get()
        
        # Cleanup
        print("\n🧹 Cleanup Tests")
        self.test_cleanup()
        
        # Results
        print("\n" + "=" * 60)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return True
        else:
            print(f"⚠️ {self.tests_run - self.tests_passed} tests failed")
            return False

def main():
    tester = TravelPlannerAPITester()
    success = tester.run_all_tests()
    
    # Save detailed results
    results = {
        "timestamp": datetime.now().isoformat(),
        "total_tests": tester.tests_run,
        "passed_tests": tester.tests_passed,
        "success_rate": (tester.tests_passed / tester.tests_run * 100) if tester.tests_run > 0 else 0,
        "test_details": tester.test_results
    }
    
    with open('/app/backend_test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())