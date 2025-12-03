"""
Quick test script for RBAC functionality
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_login():
    """Test login with default admin"""
    print("=" * 50)
    print("Testing Login...")
    print("=" * 50)
    
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"username": "admin", "password": "admin123"}
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        token = response.json()["access_token"]
        print(f"\n✅ Login successful!")
        print(f"Token: {token[:50]}...")
        return token
    else:
        print(f"\n❌ Login failed!")
        return None


def test_get_me(token):
    """Test getting current user info"""
    print("\n" + "=" * 50)
    print("Testing Get Current User...")
    print("=" * 50)
    
    response = requests.get(
        f"{BASE_URL}/api/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        print(f"\n✅ Got user info successfully!")
    else:
        print(f"\n❌ Failed to get user info!")


def test_get_roles(token):
    """Test getting all roles"""
    print("\n" + "=" * 50)
    print("Testing Get Roles...")
    print("=" * 50)
    
    response = requests.get(
        f"{BASE_URL}/api/roles",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        print(f"\n✅ Got roles successfully!")
    else:
        print(f"\n❌ Failed to get roles!")


def test_protected_endpoint_without_auth():
    """Test accessing protected endpoint without authentication"""
    print("\n" + "=" * 50)
    print("Testing Protected Endpoint Without Auth...")
    print("=" * 50)
    
    response = requests.get(f"{BASE_URL}/api/users")
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 401:
        print(f"\n✅ Correctly rejected unauthorized access!")
    else:
        print(f"\n❌ Should have rejected unauthorized access!")


if __name__ == "__main__":
    print("\n🔐 RBAC System Test\n")
    
    # Test 1: Login
    token = test_login()
    
    if token:
        # Test 2: Get current user
        test_get_me(token)
        
        # Test 3: Get roles
        test_get_roles(token)
    
    # Test 4: Protected endpoint without auth
    test_protected_endpoint_without_auth()
    
    print("\n" + "=" * 50)
    print("✅ All tests completed!")
    print("=" * 50)
    print("\n📝 Next steps:")
    print("1. Visit http://localhost:8000/docs for interactive API testing")
    print("2. Change the default admin password")
    print("3. Create additional users with appropriate roles")
    print("4. Review RBAC_GUIDE.md for detailed documentation")
