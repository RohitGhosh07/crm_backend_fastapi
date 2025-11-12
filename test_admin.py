#!/usr/bin/env python3
"""
Test the admin authentication and display admin dashboard info
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_admin_login():
    # Test login
    print("🔐 Testing Admin Login...")
    login_data = {
        "email": "admin@crm.com",
        "password": "admin123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/signin", json=login_data)
        if response.status_code == 200:
            data = response.json()
            print("✅ Login successful!")
            print(f"   User: {data['user']['name']} ({data['user']['email']})")
            token = data['access_token']
            return token
        else:
            print(f"❌ Login failed: {response.status_code}")
            print(response.text)
            return None
    except Exception as e:
        print(f"❌ Error during login: {e}")
        return None

def test_admin_endpoints(token):
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n📊 Testing Admin Dashboard Endpoints...")
    
    # Test stats endpoint
    try:
        response = requests.get(f"{BASE_URL}/admin/api/stats", headers=headers)
        if response.status_code == 200:
            stats = response.json()
            print("✅ Dashboard Stats:")
            print(f"   📈 Total Users: {stats['stats']['total_users']}")
            print(f"   👥 Active Users: {stats['stats']['active_users']}")
            print(f"   🏢 Total Clients: {stats['stats']['total_clients']}")
            print(f"   💰 Total Commissions: {stats['stats']['total_commissions']}")
            print(f"   💵 Commission Revenue: ${stats['stats']['total_commission_amount']:.2f}")
        else:
            print(f"❌ Stats endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error testing stats: {e}")
    
    # Test database structure endpoint
    try:
        response = requests.get(f"{BASE_URL}/admin/api/database/structure", headers=headers)
        if response.status_code == 200:
            db_structure = response.json()
            print(f"\n✅ Database Structure loaded - {len(db_structure['tables'])} tables found:")
            for table_name in db_structure['tables'].keys():
                table = db_structure['tables'][table_name]
                print(f"   📋 {table_name}: {len(table['columns'])} columns, {len(table['foreign_keys'])} foreign keys")
        else:
            print(f"❌ Database structure endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error testing database structure: {e}")

def main():
    print("🚀 Testing CRM Admin Dashboard\n")
    
    # Test authentication
    token = test_admin_login()
    if not token:
        return
    
    # Test admin endpoints
    test_admin_endpoints(token)
    
    print(f"\n🌐 Admin Dashboard URL: {BASE_URL}/admin/")
    print("📖 API Documentation: {BASE_URL}/docs")
    print("\n📋 Available Admin Features:")
    print("   • Dashboard Overview with Statistics")
    print("   • Database Structure Explorer")
    print("   • Users Management")
    print("   • Clients Management") 
    print("   • Commissions Tracking")
    print("   • SQL Terminal (SELECT queries only)")
    print("   • Real-time Data Viewing")

if __name__ == "__main__":
    main()