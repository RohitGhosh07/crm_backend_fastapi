#!/usr/bin/env python3
"""
Test the simple admin dashboard functionality
"""
import requests
import json

def test_simple_admin():
    base_url = "http://127.0.0.1:8000"
    
    print("🧪 Testing Simple Admin Dashboard")
    print("=" * 50)
    
    # Test authentication first
    print("\n1. 🔐 Testing Authentication...")
    login_data = {
        "email": "admin@crm.com",
        "password": "admin123"
    }
    
    try:
        response = requests.post(f"{base_url}/auth/signin", json=login_data)
        if response.status_code == 200:
            data = response.json()
            token = data['access_token']
            print(f"   ✅ Login successful - Token: {token[:20]}...")
        else:
            print(f"   ❌ Login failed: {response.status_code}")
            return
    except Exception as e:
        print(f"   ❌ Login error: {e}")
        return
    
    # Test the all-data endpoint
    print("\n2. 📊 Testing All Data Endpoint...")
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{base_url}/admin/api/all-data", headers=headers)
        if response.status_code == 200:
            all_data = response.json()
            print("   ✅ All data endpoint working!")
            
            for table_name, table_data in all_data.items():
                if 'error' in table_data:
                    print(f"   ⚠️  {table_name}: {table_data['error']}")
                else:
                    print(f"   📋 {table_name}: {table_data['count']} records, {len(table_data['columns'])} columns")
        else:
            print(f"   ❌ All data endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ All data error: {e}")
    
    # Test dashboard access
    print("\n3. 🌐 Testing Dashboard Access...")
    try:
        response = requests.get(f"{base_url}/admin/dashboard")
        if response.status_code == 200:
            print("   ✅ Dashboard HTML served successfully!")
            print(f"   📝 Response size: {len(response.text)} characters")
        else:
            print(f"   ❌ Dashboard access failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Dashboard error: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Test Summary:")
    print(f"• Simple Admin Dashboard: {base_url}/admin/dashboard")
    print(f"• Full Admin Dashboard: {base_url}/admin/")
    print(f"• API Documentation: {base_url}/docs")
    print("\n🔑 Login Credentials:")
    print("• Email: admin@crm.com")
    print("• Password: admin123")

if __name__ == "__main__":
    test_simple_admin()