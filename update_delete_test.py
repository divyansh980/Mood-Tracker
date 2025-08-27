#!/usr/bin/env python3
"""
Focused Testing for Update and Delete Functionality - Mood Tracker API
Tests specifically requested update/delete operations and edge cases
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
print(f"🔗 Testing Update/Delete API at: {API_URL}")

# Expected mood mappings
EXPECTED_MOODS = {
    1: {"emoji": "😢", "label": "Very Sad"},
    2: {"emoji": "😕", "label": "Sad"}, 
    3: {"emoji": "😐", "label": "Neutral"},
    4: {"emoji": "🙂", "label": "Happy"},
    5: {"emoji": "😄", "label": "Very Happy"}
}

class UpdateDeleteTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_entries = []
        self.errors = []
        self.successes = []

    def log_error(self, test_name, error):
        error_msg = f"❌ {test_name}: {error}"
        print(error_msg)
        self.errors.append(error_msg)

    def log_success(self, test_name, message=""):
        success_msg = f"✅ {test_name}" + (f": {message}" if message else "")
        print(success_msg)
        self.successes.append(success_msg)

    def setup_test_data(self):
        """Create test entries for update/delete testing"""
        print("\n🔧 Setting up test data...")
        
        test_data = [
            {
                "entry_date": (date.today() - timedelta(days=3)).isoformat(),
                "mood_score": 2,
                "notes": "Initial entry for update testing"
            },
            {
                "entry_date": (date.today() - timedelta(days=2)).isoformat(),
                "mood_score": 4,
                "notes": "Entry to be deleted"
            },
            {
                "entry_date": (date.today() - timedelta(days=1)).isoformat(),
                "mood_score": 1,
                "notes": "Another entry for partial update testing"
            }
        ]
        
        for i, entry_data in enumerate(test_data):
            try:
                response = self.session.post(
                    f"{API_URL}/moods",
                    json=entry_data,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    created_entry = response.json()
                    self.test_entries.append(created_entry)
                    print(f"✅ Created test entry {i+1}: {entry_data['entry_date']}")
                else:
                    # Entry might already exist, try to get it
                    get_response = self.session.get(f"{API_URL}/moods/{entry_data['entry_date']}")
                    if get_response.status_code == 200:
                        existing_entry = get_response.json()
                        self.test_entries.append(existing_entry)
                        print(f"✅ Using existing entry {i+1}: {entry_data['entry_date']}")
                    else:
                        print(f"❌ Failed to create or get test entry {i+1}: {response.text}")
                        return False
            except Exception as e:
                print(f"❌ Error setting up test entry {i+1}: {e}")
                return False
        
        return len(self.test_entries) >= 3

    def test_update_mood_score_and_notes(self):
        """Test Case: Update both mood_score and notes for existing entry"""
        print("\n🔍 Test 1: Update mood_score and notes together")
        
        if not self.test_entries:
            self.log_error("Update Both Fields", "No test entries available")
            return False
        
        entry = self.test_entries[0]
        entry_date = entry["entry_date"]
        original_score = entry["mood_score"]
        
        update_data = {
            "mood_score": 4,
            "notes": "Updated: Feeling much better now after some good news!"
        }
        
        try:
            response = self.session.put(
                f"{API_URL}/moods/{entry_date}",
                json=update_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                updated_entry = response.json()
                
                # Verify mood_score updated
                if updated_entry["mood_score"] != update_data["mood_score"]:
                    self.log_error("Update Both Fields", f"Mood score not updated: got {updated_entry['mood_score']}, expected {update_data['mood_score']}")
                    return False
                
                # Verify notes updated
                if updated_entry["notes"] != update_data["notes"]:
                    self.log_error("Update Both Fields", f"Notes not updated correctly")
                    return False
                
                # Verify emoji updated correctly
                expected_emoji = EXPECTED_MOODS[update_data["mood_score"]]["emoji"]
                if updated_entry["emoji"] != expected_emoji:
                    self.log_error("Update Both Fields", f"Emoji not updated: got {updated_entry['emoji']}, expected {expected_emoji}")
                    return False
                
                # Verify date unchanged
                if updated_entry["entry_date"] != entry_date:
                    self.log_error("Update Both Fields", "Entry date should not change during update")
                    return False
                
                self.log_success("Update Both Fields", f"Successfully updated mood from {original_score} to {update_data['mood_score']} with new notes and correct emoji")
                
                # Update our local copy
                self.test_entries[0] = updated_entry
                return True
            else:
                self.log_error("Update Both Fields", f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_error("Update Both Fields", f"Error: {e}")
        return False

    def test_partial_update_mood_score_only(self):
        """Test Case: Update only mood_score, leave notes unchanged"""
        print("\n🔍 Test 2: Partial update - mood_score only")
        
        if len(self.test_entries) < 2:
            self.log_error("Partial Update Mood", "Not enough test entries")
            return False
        
        entry = self.test_entries[1]
        entry_date = entry["entry_date"]
        original_notes = entry.get("notes", "")
        
        update_data = {
            "mood_score": 5
        }
        
        try:
            response = self.session.put(
                f"{API_URL}/moods/{entry_date}",
                json=update_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                updated_entry = response.json()
                
                # Verify mood_score updated
                if updated_entry["mood_score"] != update_data["mood_score"]:
                    self.log_error("Partial Update Mood", f"Mood score not updated")
                    return False
                
                # Verify notes unchanged
                if updated_entry.get("notes", "") != original_notes:
                    self.log_error("Partial Update Mood", f"Notes should remain unchanged: got '{updated_entry.get('notes', '')}', expected '{original_notes}'")
                    return False
                
                # Verify emoji updated
                expected_emoji = EXPECTED_MOODS[update_data["mood_score"]]["emoji"]
                if updated_entry["emoji"] != expected_emoji:
                    self.log_error("Partial Update Mood", f"Emoji not updated correctly")
                    return False
                
                self.log_success("Partial Update Mood", f"Successfully updated only mood_score to {update_data['mood_score']}, notes preserved")
                
                # Update our local copy
                self.test_entries[1] = updated_entry
                return True
            else:
                self.log_error("Partial Update Mood", f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_error("Partial Update Mood", f"Error: {e}")
        return False

    def test_partial_update_notes_only(self):
        """Test Case: Update only notes, leave mood_score unchanged"""
        print("\n🔍 Test 3: Partial update - notes only")
        
        if len(self.test_entries) < 3:
            self.log_error("Partial Update Notes", "Not enough test entries")
            return False
        
        entry = self.test_entries[2]
        entry_date = entry["entry_date"]
        original_mood_score = entry["mood_score"]
        original_emoji = entry["emoji"]
        
        update_data = {
            "notes": "Updated notes only - mood should stay the same"
        }
        
        try:
            response = self.session.put(
                f"{API_URL}/moods/{entry_date}",
                json=update_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                updated_entry = response.json()
                
                # Verify notes updated
                if updated_entry.get("notes", "") != update_data["notes"]:
                    self.log_error("Partial Update Notes", f"Notes not updated correctly")
                    return False
                
                # Verify mood_score unchanged
                if updated_entry["mood_score"] != original_mood_score:
                    self.log_error("Partial Update Notes", f"Mood score should remain unchanged: got {updated_entry['mood_score']}, expected {original_mood_score}")
                    return False
                
                # Verify emoji unchanged
                if updated_entry["emoji"] != original_emoji:
                    self.log_error("Partial Update Notes", f"Emoji should remain unchanged")
                    return False
                
                self.log_success("Partial Update Notes", f"Successfully updated only notes, mood_score and emoji preserved")
                
                # Update our local copy
                self.test_entries[2] = updated_entry
                return True
            else:
                self.log_error("Partial Update Notes", f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_error("Partial Update Notes", f"Error: {e}")
        return False

    def test_update_nonexistent_entry(self):
        """Test Case: Try to update non-existent entry (should return 404)"""
        print("\n🔍 Test 4: Update non-existent entry")
        
        future_date = (date.today() + timedelta(days=30)).isoformat()
        
        update_data = {
            "mood_score": 3,
            "notes": "This should fail"
        }
        
        try:
            response = self.session.put(
                f"{API_URL}/moods/{future_date}",
                json=update_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 404:
                error_data = response.json()
                if "not found" in error_data.get("detail", "").lower():
                    self.log_success("Update Non-existent", "Correctly returned 404 for non-existent entry")
                    return True
                else:
                    self.log_error("Update Non-existent", f"Wrong error message: {error_data}")
            else:
                self.log_error("Update Non-existent", f"Expected 404, got {response.status_code}: {response.text}")
        except Exception as e:
            self.log_error("Update Non-existent", f"Error: {e}")
        return False

    def test_delete_existing_entry(self):
        """Test Case: Delete existing mood entry and verify removal"""
        print("\n🔍 Test 5: Delete existing entry")
        
        if len(self.test_entries) < 2:
            self.log_error("Delete Existing", "Not enough test entries")
            return False
        
        # Use the second entry for deletion
        entry_to_delete = self.test_entries[1]
        entry_date = entry_to_delete["entry_date"]
        
        try:
            # First verify entry exists
            get_response = self.session.get(f"{API_URL}/moods/{entry_date}")
            if get_response.status_code != 200:
                self.log_error("Delete Existing", f"Entry doesn't exist before deletion: {get_response.status_code}")
                return False
            
            # Delete the entry
            delete_response = self.session.delete(f"{API_URL}/moods/{entry_date}")
            
            if delete_response.status_code == 200:
                delete_data = delete_response.json()
                
                if "deleted successfully" in delete_data.get("message", "").lower():
                    self.log_success("Delete Existing", f"Entry for {entry_date} deleted successfully")
                    
                    # Verify entry is actually removed from MongoDB
                    verify_response = self.session.get(f"{API_URL}/moods/{entry_date}")
                    if verify_response.status_code == 404:
                        self.log_success("Delete Verification", "Entry confirmed removed from database")
                        
                        # Remove from our local list
                        self.test_entries.remove(entry_to_delete)
                        return True
                    else:
                        self.log_error("Delete Verification", f"Entry still exists after deletion: {verify_response.status_code}")
                else:
                    self.log_error("Delete Existing", f"Unexpected response message: {delete_data}")
            else:
                self.log_error("Delete Existing", f"Status {delete_response.status_code}: {delete_response.text}")
        except Exception as e:
            self.log_error("Delete Existing", f"Error: {e}")
        return False

    def test_delete_nonexistent_entry(self):
        """Test Case: Try to delete non-existent entry (should return 404)"""
        print("\n🔍 Test 6: Delete non-existent entry")
        
        future_date = (date.today() + timedelta(days=45)).isoformat()
        
        try:
            response = self.session.delete(f"{API_URL}/moods/{future_date}")
            
            if response.status_code == 404:
                error_data = response.json()
                if "not found" in error_data.get("detail", "").lower():
                    self.log_success("Delete Non-existent", "Correctly returned 404 for non-existent entry")
                    return True
                else:
                    self.log_error("Delete Non-existent", f"Wrong error message: {error_data}")
            else:
                self.log_error("Delete Non-existent", f"Expected 404, got {response.status_code}: {response.text}")
        except Exception as e:
            self.log_error("Delete Non-existent", f"Error: {e}")
        return False

    def test_frontend_integration_scenario(self):
        """Test Case: Frontend integration - create, update, delete workflow"""
        print("\n🔍 Test 7: Frontend Integration Scenario")
        
        # Create entry with mood_score 2
        test_date = (date.today() + timedelta(days=1)).isoformat()
        
        create_data = {
            "entry_date": test_date,
            "mood_score": 2,
            "notes": "Starting with sad mood"
        }
        
        try:
            # Step 1: Create entry
            create_response = self.session.post(
                f"{API_URL}/moods",
                json=create_data,
                headers={"Content-Type": "application/json"}
            )
            
            if create_response.status_code != 200:
                self.log_error("Frontend Integration", f"Failed to create entry: {create_response.text}")
                return False
            
            created_entry = create_response.json()
            
            # Verify initial creation
            if created_entry["mood_score"] != 2 or created_entry["emoji"] != "😕":
                self.log_error("Frontend Integration", "Initial entry creation failed")
                return False
            
            self.log_success("Frontend Integration Step 1", "Created entry with mood_score 2")
            
            # Step 2: Update to mood_score 4
            update_data = {
                "mood_score": 4,
                "notes": "Feeling much better now!"
            }
            
            update_response = self.session.put(
                f"{API_URL}/moods/{test_date}",
                json=update_data,
                headers={"Content-Type": "application/json"}
            )
            
            if update_response.status_code != 200:
                self.log_error("Frontend Integration", f"Failed to update entry: {update_response.text}")
                return False
            
            updated_entry = update_response.json()
            
            # Verify update
            if updated_entry["mood_score"] != 4 or updated_entry["emoji"] != "🙂":
                self.log_error("Frontend Integration", "Entry update failed")
                return False
            
            self.log_success("Frontend Integration Step 2", "Updated entry from mood_score 2 to 4 with correct emoji")
            
            # Step 3: Verify statistics reflect changes
            stats_response = self.session.get(f"{API_URL}/moods/stats/summary")
            if stats_response.status_code != 200:
                self.log_error("Frontend Integration", "Failed to get statistics")
                return False
            
            stats_data = stats_response.json()
            if stats_data["total_entries"] < 1:
                self.log_error("Frontend Integration", "Statistics don't reflect created entry")
                return False
            
            self.log_success("Frontend Integration Step 3", "Statistics endpoint reflects changes")
            
            # Step 4: Delete the entry
            delete_response = self.session.delete(f"{API_URL}/moods/{test_date}")
            
            if delete_response.status_code != 200:
                self.log_error("Frontend Integration", f"Failed to delete entry: {delete_response.text}")
                return False
            
            # Verify deletion
            verify_response = self.session.get(f"{API_URL}/moods/{test_date}")
            if verify_response.status_code != 404:
                self.log_error("Frontend Integration", "Entry not properly deleted")
                return False
            
            self.log_success("Frontend Integration Step 4", "Entry successfully deleted and confirmed gone")
            
            # Step 5: Verify statistics updated after deletion
            final_stats_response = self.session.get(f"{API_URL}/moods/stats/summary")
            if final_stats_response.status_code == 200:
                self.log_success("Frontend Integration Step 5", "Statistics endpoint accessible after deletion")
            
            return True
            
        except Exception as e:
            self.log_error("Frontend Integration", f"Error: {e}")
        return False

    def cleanup_test_data(self):
        """Clean up any remaining test entries"""
        print("\n🧹 Cleaning up test data...")
        
        for entry in self.test_entries[:]:  # Copy list to avoid modification during iteration
            try:
                entry_date = entry["entry_date"]
                response = self.session.delete(f"{API_URL}/moods/{entry_date}")
                if response.status_code == 200:
                    print(f"✅ Cleaned up entry: {entry_date}")
                    self.test_entries.remove(entry)
                else:
                    print(f"⚠️  Could not clean up entry {entry_date}: {response.status_code}")
            except Exception as e:
                print(f"⚠️  Error cleaning up entry: {e}")

    def run_update_delete_tests(self):
        """Run all update and delete focused tests"""
        print("🚀 Starting Update/Delete Functionality Tests")
        print("=" * 60)
        
        # Setup test data
        if not self.setup_test_data():
            print("❌ Failed to setup test data, aborting tests")
            return False
        
        # Run all tests
        test_results = []
        
        test_results.append(self.test_update_mood_score_and_notes())
        test_results.append(self.test_partial_update_mood_score_only())
        test_results.append(self.test_partial_update_notes_only())
        test_results.append(self.test_update_nonexistent_entry())
        test_results.append(self.test_delete_existing_entry())
        test_results.append(self.test_delete_nonexistent_entry())
        test_results.append(self.test_frontend_integration_scenario())
        
        # Clean up
        self.cleanup_test_data()
        
        # Print results
        self.print_results(test_results)
        
        return all(test_results)

    def print_results(self, test_results):
        """Print final test results"""
        print("\n" + "=" * 60)
        print("📊 UPDATE/DELETE TEST RESULTS")
        print("=" * 60)
        
        test_names = [
            "Update mood_score and notes",
            "Partial update - mood_score only", 
            "Partial update - notes only",
            "Update non-existent entry (404)",
            "Delete existing entry",
            "Delete non-existent entry (404)",
            "Frontend integration scenario"
        ]
        
        for i, (name, passed) in enumerate(zip(test_names, test_results)):
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{status} {name}")
        
        passed_tests = sum(test_results)
        total_tests = len(test_results)
        
        print(f"\n📈 Overall: {passed_tests}/{total_tests} tests passed")
        
        if self.errors:
            print(f"\n🚨 {len(self.errors)} Errors Found:")
            for error in self.errors:
                print(f"  {error}")
        
        if passed_tests == total_tests:
            print("\n🎉 All update/delete tests passed! Functionality is working correctly.")
        else:
            print(f"\n⚠️  {total_tests - passed_tests} test(s) failed. Update/delete functionality needs attention.")

if __name__ == "__main__":
    tester = UpdateDeleteTester()
    success = tester.run_update_delete_tests()
    sys.exit(0 if success else 1)