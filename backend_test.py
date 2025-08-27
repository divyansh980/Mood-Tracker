#!/usr/bin/env python3
"""
Comprehensive Backend API Testing for Mood Tracker App
Tests all CRUD operations, statistics, CSV export, and MongoDB integration
"""

import requests
import json
from datetime import date, datetime, timedelta
import sys
import os

# Get backend URL from frontend .env file
def get_backend_url():
    try:
        with open('/app/frontend/.env', 'r') as f:
            for line in f:
                if line.startswith('REACT_APP_BACKEND_URL='):
                    return line.split('=', 1)[1].strip()
    except Exception as e:
        print(f"Error reading backend URL: {e}")
        return None

BASE_URL = get_backend_url()
if not BASE_URL:
    print("❌ Could not get backend URL from frontend/.env")
    sys.exit(1)

API_URL = f"{BASE_URL}/api"
print(f"🔗 Testing API at: {API_URL}")

# Test data - realistic mood entries
test_entries = [
    {
        "entry_date": (date.today() - timedelta(days=2)).isoformat(),
        "mood_score": 4,
        "notes": "Had a great day at work, finished my project successfully!"
    },
    {
        "entry_date": (date.today() - timedelta(days=1)).isoformat(), 
        "mood_score": 2,
        "notes": "Feeling a bit down today, had some challenges with family"
    },
    {
        "entry_date": date.today().isoformat(),
        "mood_score": 5,
        "notes": "Amazing day! Got promoted and celebrated with friends"
    }
]

# Expected mood mappings
EXPECTED_MOODS = {
    1: {"emoji": "😢", "label": "Very Sad"},
    2: {"emoji": "😕", "label": "Sad"}, 
    3: {"emoji": "😐", "label": "Neutral"},
    4: {"emoji": "🙂", "label": "Happy"},
    5: {"emoji": "😄", "label": "Very Happy"}
}

class MoodTrackerTester:
    def __init__(self):
        self.session = requests.Session()
        self.created_entries = []
        self.test_results = {
            "crud_operations": False,
            "statistics_api": False,
            "csv_export": False,
            "mongodb_integration": False,
            "emoji_mapping": False,
            "date_handling": False,
            "error_handling": False
        }
        self.errors = []

    def log_error(self, test_name, error):
        error_msg = f"❌ {test_name}: {error}"
        print(error_msg)
        self.errors.append(error_msg)

    def log_success(self, test_name, message=""):
        success_msg = f"✅ {test_name}" + (f": {message}" if message else "")
        print(success_msg)

    def test_api_root(self):
        """Test basic API connectivity"""
        print("\n🔍 Testing API Root Endpoint...")
        try:
            response = self.session.get(f"{API_URL}/")
            if response.status_code == 200:
                data = response.json()
                if data.get("message") == "Mood Tracker API":
                    self.log_success("API Root", "API is accessible")
                    return True
                else:
                    self.log_error("API Root", f"Unexpected response: {data}")
            else:
                self.log_error("API Root", f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_error("API Root", f"Connection error: {e}")
        return False

    def test_mood_options(self):
        """Test mood options endpoint"""
        print("\n🔍 Testing Mood Options Endpoint...")
        try:
            response = self.session.get(f"{API_URL}/moods/options")
            if response.status_code == 200:
                data = response.json()
                moods = data.get("moods", {})
                
                # Verify all expected moods are present
                for score, expected in EXPECTED_MOODS.items():
                    if str(score) in moods:
                        mood_data = moods[str(score)]
                        if (mood_data.get("emoji") == expected["emoji"] and 
                            mood_data.get("label") == expected["label"]):
                            continue
                        else:
                            self.log_error("Mood Options", f"Incorrect mood data for score {score}")
                            return False
                    else:
                        self.log_error("Mood Options", f"Missing mood score {score}")
                        return False
                
                self.log_success("Mood Options", "All mood mappings correct")
                self.test_results["emoji_mapping"] = True
                return True
            else:
                self.log_error("Mood Options", f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_error("Mood Options", f"Error: {e}")
        return False

    def test_create_mood_entries(self):
        """Test creating mood entries (POST /api/moods)"""
        print("\n🔍 Testing Mood Entry Creation...")
        
        for i, entry_data in enumerate(test_entries):
            try:
                response = self.session.post(
                    f"{API_URL}/moods",
                    json=entry_data,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Verify response structure
                    required_fields = ["id", "entry_date", "mood_score", "emoji", "created_at"]
                    for field in required_fields:
                        if field not in data:
                            self.log_error("Create Mood Entry", f"Missing field '{field}' in response")
                            return False
                    
                    # Verify emoji mapping
                    expected_emoji = EXPECTED_MOODS[entry_data["mood_score"]]["emoji"]
                    if data["emoji"] != expected_emoji:
                        self.log_error("Create Mood Entry", f"Wrong emoji: got {data['emoji']}, expected {expected_emoji}")
                        return False
                    
                    # Verify date handling
                    if data["entry_date"] != entry_data["entry_date"]:
                        self.log_error("Create Mood Entry", f"Date mismatch: got {data['entry_date']}, expected {entry_data['entry_date']}")
                        return False
                    
                    self.created_entries.append(data)
                    self.log_success("Create Mood Entry", f"Entry {i+1} created successfully")
                    
                else:
                    self.log_error("Create Mood Entry", f"Status {response.status_code}: {response.text}")
                    return False
                    
            except Exception as e:
                self.log_error("Create Mood Entry", f"Error creating entry {i+1}: {e}")
                return False
        
        self.test_results["date_handling"] = True
        return True

    def test_duplicate_entry_prevention(self):
        """Test that duplicate entries for same date are prevented"""
        print("\n🔍 Testing Duplicate Entry Prevention...")
        
        if not self.created_entries:
            self.log_error("Duplicate Prevention", "No entries created to test with")
            return False
        
        # Try to create entry for same date as first entry
        duplicate_data = {
            "entry_date": self.created_entries[0]["entry_date"],
            "mood_score": 3,
            "notes": "This should fail"
        }
        
        try:
            response = self.session.post(
                f"{API_URL}/moods",
                json=duplicate_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 400:
                error_data = response.json()
                if "already exists" in error_data.get("detail", "").lower():
                    self.log_success("Duplicate Prevention", "Correctly prevented duplicate entry")
                    self.test_results["error_handling"] = True
                    return True
                else:
                    self.log_error("Duplicate Prevention", f"Wrong error message: {error_data}")
            else:
                self.log_error("Duplicate Prevention", f"Expected 400 status, got {response.status_code}")
        except Exception as e:
            self.log_error("Duplicate Prevention", f"Error: {e}")
        return False

    def test_get_all_moods(self):
        """Test retrieving all mood entries (GET /api/moods)"""
        print("\n🔍 Testing Get All Mood Entries...")
        
        try:
            response = self.session.get(f"{API_URL}/moods")
            
            if response.status_code == 200:
                data = response.json()
                
                if not isinstance(data, list):
                    self.log_error("Get All Moods", "Response is not a list")
                    return False
                
                if len(data) < len(self.created_entries):
                    self.log_error("Get All Moods", f"Expected at least {len(self.created_entries)} entries, got {len(data)}")
                    return False
                
                # Verify entries are sorted by date (newest first)
                if len(data) > 1:
                    for i in range(len(data) - 1):
                        current_date = data[i]["entry_date"]
                        next_date = data[i + 1]["entry_date"]
                        if current_date < next_date:
                            self.log_error("Get All Moods", "Entries not sorted by date (newest first)")
                            return False
                
                self.log_success("Get All Moods", f"Retrieved {len(data)} entries, properly sorted")
                return True
            else:
                self.log_error("Get All Moods", f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_error("Get All Moods", f"Error: {e}")
        return False

    def test_get_mood_by_date(self):
        """Test retrieving mood entry by date (GET /api/moods/{date})"""
        print("\n🔍 Testing Get Mood by Date...")
        
        if not self.created_entries:
            self.log_error("Get Mood by Date", "No entries to test with")
            return False
        
        # Test getting existing entry
        test_entry = self.created_entries[0]
        entry_date = test_entry["entry_date"]
        
        try:
            response = self.session.get(f"{API_URL}/moods/{entry_date}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify it's the correct entry
                if (data["entry_date"] == entry_date and 
                    data["mood_score"] == test_entry["mood_score"]):
                    self.log_success("Get Mood by Date", f"Retrieved correct entry for {entry_date}")
                else:
                    self.log_error("Get Mood by Date", "Retrieved entry doesn't match expected data")
                    return False
            else:
                self.log_error("Get Mood by Date", f"Status {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_error("Get Mood by Date", f"Error: {e}")
            return False
        
        # Test getting non-existent entry
        future_date = (date.today() + timedelta(days=30)).isoformat()
        try:
            response = self.session.get(f"{API_URL}/moods/{future_date}")
            
            if response.status_code == 404:
                self.log_success("Get Mood by Date", "Correctly returned 404 for non-existent entry")
                return True
            else:
                self.log_error("Get Mood by Date", f"Expected 404 for non-existent entry, got {response.status_code}")
        except Exception as e:
            self.log_error("Get Mood by Date", f"Error testing non-existent entry: {e}")
        return False

    def test_update_mood_entry(self):
        """Test updating mood entry (PUT /api/moods/{date})"""
        print("\n🔍 Testing Update Mood Entry...")
        
        if not self.created_entries:
            self.log_error("Update Mood Entry", "No entries to test with")
            return False
        
        # Update the first entry
        test_entry = self.created_entries[0]
        entry_date = test_entry["entry_date"]
        
        update_data = {
            "mood_score": 3,
            "notes": "Updated: Feeling neutral now after some reflection"
        }
        
        try:
            response = self.session.put(
                f"{API_URL}/moods/{entry_date}",
                json=update_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify updates were applied
                if (data["mood_score"] == update_data["mood_score"] and
                    data["notes"] == update_data["notes"] and
                    data["emoji"] == EXPECTED_MOODS[3]["emoji"]):
                    self.log_success("Update Mood Entry", "Entry updated successfully")
                    
                    # Update our local copy
                    for entry in self.created_entries:
                        if entry["entry_date"] == entry_date:
                            entry.update(data)
                            break
                    
                    return True
                else:
                    self.log_error("Update Mood Entry", "Update data not reflected correctly")
            else:
                self.log_error("Update Mood Entry", f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_error("Update Mood Entry", f"Error: {e}")
        return False

    def test_mood_statistics(self):
        """Test mood statistics endpoint (GET /api/moods/stats/summary)"""
        print("\n🔍 Testing Mood Statistics...")
        
        try:
            response = self.session.get(f"{API_URL}/moods/stats/summary")
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify required fields
                required_fields = ["total_entries", "average_mood", "mood_distribution", "recent_trend"]
                for field in required_fields:
                    if field not in data:
                        self.log_error("Mood Statistics", f"Missing field '{field}'")
                        return False
                
                # Verify data types and ranges
                if not isinstance(data["total_entries"], int) or data["total_entries"] < 0:
                    self.log_error("Mood Statistics", "Invalid total_entries")
                    return False
                
                if not isinstance(data["average_mood"], (int, float)) or not (0 <= data["average_mood"] <= 5):
                    self.log_error("Mood Statistics", f"Invalid average_mood: {data['average_mood']}")
                    return False
                
                if not isinstance(data["mood_distribution"], dict):
                    self.log_error("Mood Statistics", "mood_distribution is not a dict")
                    return False
                
                if not isinstance(data["recent_trend"], list):
                    self.log_error("Mood Statistics", "recent_trend is not a list")
                    return False
                
                self.log_success("Mood Statistics", f"Stats: {data['total_entries']} entries, avg mood {data['average_mood']}")
                self.test_results["statistics_api"] = True
                return True
            else:
                self.log_error("Mood Statistics", f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_error("Mood Statistics", f"Error: {e}")
        return False

    def test_csv_export(self):
        """Test CSV export endpoint (GET /api/moods/export/csv)"""
        print("\n🔍 Testing CSV Export...")
        
        try:
            response = self.session.get(f"{API_URL}/moods/export/csv")
            
            if response.status_code == 200:
                data = response.json()
                
                if "csv_data" not in data:
                    self.log_error("CSV Export", "Missing csv_data field")
                    return False
                
                csv_content = data["csv_data"]
                
                # Verify CSV structure
                lines = csv_content.strip().split('\n')
                if len(lines) < 1:
                    self.log_error("CSV Export", "Empty CSV content")
                    return False
                
                # Check header
                expected_header = "Date,Mood Score,Emoji,Mood Label,Notes"
                if lines[0] != expected_header:
                    self.log_error("CSV Export", f"Wrong CSV header: {lines[0]}")
                    return False
                
                # Verify we have data rows (at least our test entries)
                if len(lines) < len(self.created_entries) + 1:  # +1 for header
                    self.log_error("CSV Export", f"Expected at least {len(self.created_entries)} data rows, got {len(lines)-1}")
                    return False
                
                # Verify CSV format of data rows
                for i, line in enumerate(lines[1:], 1):
                    parts = line.split(',')
                    if len(parts) < 5:  # Date, Score, Emoji, Label, Notes (notes can be empty)
                        self.log_error("CSV Export", f"Invalid CSV format in line {i+1}: {line}")
                        return False
                
                self.log_success("CSV Export", f"Generated CSV with {len(lines)-1} data rows")
                self.test_results["csv_export"] = True
                return True
            else:
                self.log_error("CSV Export", f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_error("CSV Export", f"Error: {e}")
        return False

    def test_delete_mood_entry(self):
        """Test deleting mood entry (DELETE /api/moods/{date})"""
        print("\n🔍 Testing Delete Mood Entry...")
        
        if not self.created_entries:
            self.log_error("Delete Mood Entry", "No entries to test with")
            return False
        
        # Delete the last entry
        test_entry = self.created_entries[-1]
        entry_date = test_entry["entry_date"]
        
        try:
            response = self.session.delete(f"{API_URL}/moods/{entry_date}")
            
            if response.status_code == 200:
                data = response.json()
                
                if "deleted successfully" in data.get("message", "").lower():
                    self.log_success("Delete Mood Entry", f"Entry for {entry_date} deleted successfully")
                    
                    # Verify entry is actually deleted
                    verify_response = self.session.get(f"{API_URL}/moods/{entry_date}")
                    if verify_response.status_code == 404:
                        self.log_success("Delete Verification", "Entry confirmed deleted")
                        self.created_entries.remove(test_entry)
                        return True
                    else:
                        self.log_error("Delete Verification", "Entry still exists after deletion")
                else:
                    self.log_error("Delete Mood Entry", f"Unexpected response: {data}")
            else:
                self.log_error("Delete Mood Entry", f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_error("Delete Mood Entry", f"Error: {e}")
        return False

    def test_mongodb_integration(self):
        """Test MongoDB data persistence by creating, retrieving, and verifying data"""
        print("\n🔍 Testing MongoDB Integration...")
        
        # Create a test entry specifically for persistence testing
        persistence_test_data = {
            "entry_date": (date.today() + timedelta(days=1)).isoformat(),
            "mood_score": 4,
            "notes": "Testing MongoDB persistence - this should be stored and retrieved correctly"
        }
        
        try:
            # Create entry
            create_response = self.session.post(
                f"{API_URL}/moods",
                json=persistence_test_data,
                headers={"Content-Type": "application/json"}
            )
            
            if create_response.status_code != 200:
                self.log_error("MongoDB Integration", f"Failed to create test entry: {create_response.text}")
                return False
            
            created_data = create_response.json()
            
            # Retrieve entry to verify persistence
            retrieve_response = self.session.get(f"{API_URL}/moods/{persistence_test_data['entry_date']}")
            
            if retrieve_response.status_code != 200:
                self.log_error("MongoDB Integration", "Failed to retrieve created entry")
                return False
            
            retrieved_data = retrieve_response.json()
            
            # Verify data integrity
            if (retrieved_data["entry_date"] == persistence_test_data["entry_date"] and
                retrieved_data["mood_score"] == persistence_test_data["mood_score"] and
                retrieved_data["notes"] == persistence_test_data["notes"] and
                retrieved_data["id"] == created_data["id"]):
                
                self.log_success("MongoDB Integration", "Data persisted and retrieved correctly")
                
                # Clean up test entry
                self.session.delete(f"{API_URL}/moods/{persistence_test_data['entry_date']}")
                
                self.test_results["mongodb_integration"] = True
                return True
            else:
                self.log_error("MongoDB Integration", "Data integrity check failed")
        except Exception as e:
            self.log_error("MongoDB Integration", f"Error: {e}")
        return False

    def run_all_tests(self):
        """Run comprehensive test suite"""
        print("🚀 Starting Comprehensive Mood Tracker Backend API Tests")
        print("=" * 60)
        
        # Test basic connectivity first
        if not self.test_api_root():
            print("\n❌ API not accessible, stopping tests")
            return False
        
        # Test mood options
        self.test_mood_options()
        
        # Test CRUD operations
        print("\n📝 Testing CRUD Operations...")
        crud_success = (
            self.test_create_mood_entries() and
            self.test_duplicate_entry_prevention() and
            self.test_get_all_moods() and
            self.test_get_mood_by_date() and
            self.test_update_mood_entry() and
            self.test_delete_mood_entry()
        )
        
        if crud_success:
            self.test_results["crud_operations"] = True
        
        # Test statistics and export
        self.test_mood_statistics()
        self.test_csv_export()
        
        # Test MongoDB integration
        self.test_mongodb_integration()
        
        # Print final results
        self.print_final_results()
        
        return all(self.test_results.values())

    def print_final_results(self):
        """Print comprehensive test results"""
        print("\n" + "=" * 60)
        print("📊 FINAL TEST RESULTS")
        print("=" * 60)
        
        for test_name, passed in self.test_results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{status} {test_name.replace('_', ' ').title()}")
        
        total_tests = len(self.test_results)
        passed_tests = sum(self.test_results.values())
        
        print(f"\n📈 Overall: {passed_tests}/{total_tests} tests passed")
        
        if self.errors:
            print(f"\n🚨 {len(self.errors)} Errors Found:")
            for error in self.errors:
                print(f"  {error}")
        
        if passed_tests == total_tests:
            print("\n🎉 All tests passed! Backend API is fully functional.")
        else:
            print(f"\n⚠️  {total_tests - passed_tests} test(s) failed. Backend needs attention.")

if __name__ == "__main__":
    tester = MoodTrackerTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)