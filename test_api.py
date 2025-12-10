#!/usr/bin/env python3
"""
Test script for Neural Search API
Run locally before deploying to Railway
"""

import requests
import json

# Configuration
API_URL = "http://localhost:8080"  # Change to Railway URL after deployment
SHOP_ID = "test_shop"

# Sample XML for testing
SAMPLE_XML = """<?xml version="1.0" encoding="UTF-8"?>
<products>
  <product>
    <id>1</id>
    <name>Ashley Slim Fit Τζιν Μαύρο</name>
    <model>ASH-001-BLK</model>
    <description>Μοντέρνο slim fit τζιν σε μαύρο χρώμα. Υψηλής ποιότητας ύφασμα με ελαστικότητα για άνετη εφαρμογή.</description>
    <category>Jeans</category>
    <price>62.97</price>
    <image>https://example.com/ashley-black.jpg</image>
    <url>https://example.com/product/ashley-black</url>
  </product>
  <product>
    <id>2</id>
    <name>Grace Bootcut Τζιν Μπλε</name>
    <model>GRC-002-BLU</model>
    <description>Κλασικό bootcut τζιν σε μπλε απόχρωση. Ιδανικό για casual εμφανίσεις.</description>
    <category>Jeans</category>
    <price>59.90</price>
    <image>https://example.com/grace-blue.jpg</image>
    <url>https://example.com/product/grace-blue</url>
  </product>
  <product>
    <id>3</id>
    <name>Simon Regular Τζιν Ανθρακί</name>
    <model>SIM-003-GRY</model>
    <description>Regular fit τζιν σε ανθρακί χρώμα. Άνετη γραμμή για καθημερινή χρήση.</description>
    <category>Jeans</category>
    <price>54.95</price>
    <image>https://example.com/simon-grey.jpg</image>
    <url>https://example.com/product/simon-grey</url>
  </product>
</products>"""

def test_health():
    """Test health endpoint"""
    print("\n1. Testing /health endpoint...")
    try:
        response = requests.get(f"{API_URL}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_train():
    """Test training endpoint"""
    print(f"\n2. Testing /train endpoint for shop '{SHOP_ID}'...")
    try:
        response = requests.post(
            f"{API_URL}/train",
            json={
                "shop_id": SHOP_ID,
                "xml": SAMPLE_XML
            }
        )
        print(f"Status: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}")
        return result.get('success', False)
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_status():
    """Test status endpoint"""
    print(f"\n3. Testing /status endpoint for shop '{SHOP_ID}'...")
    try:
        response = requests.get(f"{API_URL}/status", params={"shop_id": SHOP_ID})
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_search(query):
    """Test search endpoint"""
    print(f"\n4. Testing /search endpoint with query: '{query}'...")
    try:
        response = requests.get(
            f"{API_URL}/search",
            params={
                "shop_id": SHOP_ID,
                "q": query,
                "limit": 3
            }
        )
        print(f"Status: {response.status_code}")
        result = response.json()
        
        if result.get('success'):
            print(f"\n✅ Found {result['count']} results:")
            for i, product in enumerate(result['results'], 1):
                print(f"\n  {i}. {product['name']}")
                print(f"     Model: {product['model']}")
                print(f"     Price: €{product['price']}")
                print(f"     Score: {product['score']:.3f} (neural: {product['neural_score']:.3f}, fuzzy: {product['fuzzy_score']:.3f})")
        else:
            print(f"Response: {json.dumps(result, indent=2)}")
        
        return result.get('success', False)
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_shops():
    """Test shops list endpoint"""
    print("\n5. Testing /shops endpoint...")
    try:
        response = requests.get(f"{API_URL}/shops")
        print(f"Status: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("Neural Search API Test Suite")
    print("=" * 60)
    print(f"\nTesting API at: {API_URL}")
    print(f"Shop ID: {SHOP_ID}")
    
    # Run tests
    tests = [
        ("Health Check", test_health),
        ("Train Model", test_train),
        ("Check Status", test_status),
        ("Search 'μαύρο τζιν'", lambda: test_search("μαύρο τζιν")),
        ("Search 'mavro tzin' (Greeklish)", lambda: test_search("mavro tzin")),
        ("Search 'bootcut'", lambda: test_search("bootcut")),
        ("List Shops", test_shops)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"\n❌ Test '{name}' failed with error: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Ready for production!")
    else:
        print("\n⚠️  Some tests failed. Check logs above.")

if __name__ == "__main__":
    main()
