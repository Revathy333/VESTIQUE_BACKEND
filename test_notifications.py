#!/usr/bin/env python
"""
Quick Test Script for Push Notifications API
Run from Backend/backend_service directory:
python test_notifications.py
"""

import requests
import json
from decouple import config

BASE_URL = "http://localhost:8000/api"
JWT_TOKEN = "your_jwt_token_here"  # Replace with actual token

HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {JWT_TOKEN}"
}


def test_save_fcm_token():
    """Test saving FCM token"""
    print("\n1️⃣  Testing: Save FCM Token")
    print("=" * 50)
    
    url = f"{BASE_URL}/notifications/save-token/"
    payload = {
        "fcm_token": "eH2_sZjSvFI0xZ-KF1qKrq:APA91bHvR_H2YZ0qZ-F3Kq8M9L2J4X6Y8Z0A1B2C3D4E5F6G7H8I9J0K1L2M3N4O5"
    }
    
    response = requests.post(url, json=payload, headers=HEADERS)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.json()


def test_send_to_user(user_id=2):
    """Test sending notification to single user"""
    print("\n2️⃣  Testing: Send Notification to Single User")
    print("=" * 50)
    
    url = f"{BASE_URL}/notifications/send-to-user/"
    payload = {
        "user_id": user_id,
        "title": "Welcome Back!",
        "body": "We're glad to see you again",
        "data": {
            "type": "greeting",
            "user_id": user_id
        },
        "icon": "https://vestique.com/logo.png",
        "click_action": "https://vestique.com/home"
    }
    
    response = requests.post(url, json=payload, headers=HEADERS)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.json()


def test_send_bulk(user_ids=[2, 3, 4]):
    """Test sending bulk notifications"""
    print("\n3️⃣  Testing: Send Bulk Notifications")
    print("=" * 50)
    
    url = f"{BASE_URL}/notifications/send-bulk/"
    payload = {
        "user_ids": user_ids,
        "title": "New Collection Available",
        "body": "Check out our latest fashion collection",
        "data": {
            "type": "product_alert",
            "collection_id": "col_12345"
        }
    }
    
    response = requests.post(url, json=payload, headers=HEADERS)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.json()


def test_send_to_topic(topic="announcements"):
    """Test sending to topic (admin only)"""
    print("\n4️⃣  Testing: Send to Topic (Admin Only)")
    print("=" * 50)
    
    url = f"{BASE_URL}/notifications/send-to-topic/"
    payload = {
        "topic": topic,
        "title": "Important Announcement",
        "body": "We have exciting news to share!",
        "data": {
            "type": "announcement"
        }
    }
    
    response = requests.post(url, json=payload, headers=HEADERS)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.json()


def test_notification_history(limit=10, offset=0):
    """Test getting notification history"""
    print("\n5️⃣  Testing: Get Notification History")
    print("=" * 50)
    
    url = f"{BASE_URL}/notifications/history/?limit={limit}&offset={offset}"
    
    response = requests.get(url, headers=HEADERS)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.json()


def test_mark_as_read(notification_id=1):
    """Test marking notification as read"""
    print("\n6️⃣  Testing: Mark Notification as Read")
    print("=" * 50)
    
    url = f"{BASE_URL}/notifications/{notification_id}/mark-read/"
    
    response = requests.patch(url, headers=HEADERS)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.json()


def test_invalid_token():
    """Test with invalid token"""
    print("\n7️⃣  Testing: Invalid Token (Should Fail)")
    print("=" * 50)
    
    url = f"{BASE_URL}/notifications/history/"
    bad_headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer invalid_token_here"
    }
    
    response = requests.get(url, headers=bad_headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.json()


def test_missing_required_field():
    """Test missing required field"""
    print("\n8️⃣  Testing: Missing Required Field (Should Fail)")
    print("=" * 50)
    
    url = f"{BASE_URL}/notifications/send-to-user/"
    payload = {
        "user_id": 2,
        # Missing 'title' - should fail
        "body": "Test"
    }
    
    response = requests.post(url, json=payload, headers=HEADERS)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.json()


if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("PUSH NOTIFICATIONS API TEST SUITE")
    print("=" * 50)
    print(f"\nBase URL: {BASE_URL}")
    print(f"Using JWT Token: {JWT_TOKEN[:20]}...")
    
    print("\n⚠️  NOTE: Replace JWT_TOKEN with actual token before running!")
    print("Get token: POST /api/auth/token/ with username and password\n")
    
    # Run tests
    try:
        # test_save_fcm_token()
        # test_send_to_user(user_id=2)
        # test_send_bulk(user_ids=[2, 3, 4])
        # test_send_to_topic(topic="announcements")
        # test_notification_history(limit=10)
        # test_mark_as_read(notification_id=1)
        test_invalid_token()
        test_missing_required_field()
        
        print("\n" + "=" * 50)
        print("✅ Test Suite Complete!")
        print("=" * 50)
    
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
