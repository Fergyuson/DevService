#!/usr/bin/env python3
"""
Backend API Testing Script for DevServices Web Store
Tests all API endpoints for products, cart, QR codes, and validation
"""

import requests
import json
import uuid
from typing import Dict, List, Any
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')

# Get backend URL from environment - use localhost for testing since external URL has routing issues
BACKEND_URL = 'http://localhost:8001'
API_BASE = f"{BACKEND_URL}/api"

class BackendTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.products = []
        
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   Details: {details}")
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details
        })
        
    def test_products_api(self):
        """Test products API endpoints"""
        print("\n=== TESTING PRODUCTS API ===")
        
        # Test GET /api/products
        try:
            response = self.session.get(f"{API_BASE}/products")
            if response.status_code == 200:
                products = response.json()
                self.products = products  # Store for later tests
                
                # Check if we have 20 products
                if len(products) == 20:
                    self.log_test("GET /api/products - Count", True, f"Found {len(products)} products")
                else:
                    self.log_test("GET /api/products - Count", False, f"Expected 20 products, got {len(products)}")
                
                # Check price range (500₽ to 10000₽)
                prices = [p['price'] for p in products]
                min_price, max_price = min(prices), max(prices)
                if min_price >= 500 and max_price <= 10000:
                    self.log_test("GET /api/products - Price Range", True, f"Prices from {min_price}₽ to {max_price}₽")
                else:
                    self.log_test("GET /api/products - Price Range", False, f"Price range {min_price}₽-{max_price}₽ not in expected 500₽-10000₽")
                
                # Check product structure
                required_fields = ['id', 'name', 'price', 'shortDescription', 'fullDescription', 'deliveryTime', 'icon', 'features', 'technologies', 'category']
                first_product = products[0]
                missing_fields = [field for field in required_fields if field not in first_product]
                if not missing_fields:
                    self.log_test("GET /api/products - Structure", True, "All required fields present")
                else:
                    self.log_test("GET /api/products - Structure", False, f"Missing fields: {missing_fields}")
                    
            else:
                self.log_test("GET /api/products", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("GET /api/products", False, f"Exception: {str(e)}")
        
        # Test GET /api/products/{id} with valid ID
        if self.products:
            try:
                product_id = self.products[0]['id']
                response = self.session.get(f"{API_BASE}/products/{product_id}")
                if response.status_code == 200:
                    product = response.json()
                    if product['id'] == product_id:
                        self.log_test("GET /api/products/{id} - Valid ID", True, f"Retrieved product: {product['name']}")
                    else:
                        self.log_test("GET /api/products/{id} - Valid ID", False, "Product ID mismatch")
                else:
                    self.log_test("GET /api/products/{id} - Valid ID", False, f"HTTP {response.status_code}")
            except Exception as e:
                self.log_test("GET /api/products/{id} - Valid ID", False, f"Exception: {str(e)}")
        
        # Test GET /api/products/{id} with invalid ID
        try:
            invalid_id = str(uuid.uuid4())
            response = self.session.get(f"{API_BASE}/products/{invalid_id}")
            if response.status_code == 404:
                self.log_test("GET /api/products/{id} - Invalid ID", True, "Correctly returned 404")
            else:
                self.log_test("GET /api/products/{id} - Invalid ID", False, f"Expected 404, got {response.status_code}")
        except Exception as e:
            self.log_test("GET /api/products/{id} - Invalid ID", False, f"Exception: {str(e)}")
    
    def test_cart_api(self):
        """Test cart API endpoints"""
        print("\n=== TESTING CART API ===")
        
        session_id = str(uuid.uuid4())
        
        # Test POST /api/cart/save
        try:
            if self.products:
                cart_data = {
                    "session_id": session_id,
                    "items": [
                        {"product_id": self.products[0]['id'], "quantity": 2},
                        {"product_id": self.products[1]['id'], "quantity": 1}
                    ]
                }
                
                response = self.session.post(f"{API_BASE}/cart/save", json=cart_data)
                if response.status_code == 200:
                    result = response.json()
                    if result.get('status') == 'success' and result.get('session_id') == session_id:
                        self.log_test("POST /api/cart/save", True, f"Cart saved for session: {session_id}")
                    else:
                        self.log_test("POST /api/cart/save", False, f"Unexpected response: {result}")
                else:
                    self.log_test("POST /api/cart/save", False, f"HTTP {response.status_code}: {response.text}")
            else:
                self.log_test("POST /api/cart/save", False, "No products available for testing")
                
        except Exception as e:
            self.log_test("POST /api/cart/save", False, f"Exception: {str(e)}")
        
        # Test GET /api/cart/{session_id} with valid session
        try:
            response = self.session.get(f"{API_BASE}/cart/{session_id}")
            if response.status_code == 200:
                cart = response.json()
                if 'items' in cart and len(cart['items']) > 0:
                    self.log_test("GET /api/cart/{session_id} - Valid", True, f"Retrieved cart with {len(cart['items'])} items")
                else:
                    self.log_test("GET /api/cart/{session_id} - Valid", False, "Cart is empty or malformed")
            else:
                self.log_test("GET /api/cart/{session_id} - Valid", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("GET /api/cart/{session_id} - Valid", False, f"Exception: {str(e)}")
        
        # Test GET /api/cart/{session_id} with invalid session
        try:
            invalid_session = str(uuid.uuid4())
            response = self.session.get(f"{API_BASE}/cart/{invalid_session}")
            if response.status_code == 200:
                cart = response.json()
                if cart.get('items') == []:
                    self.log_test("GET /api/cart/{session_id} - Invalid", True, "Correctly returned empty cart")
                else:
                    self.log_test("GET /api/cart/{session_id} - Invalid", False, f"Expected empty cart, got: {cart}")
            else:
                self.log_test("GET /api/cart/{session_id} - Invalid", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("GET /api/cart/{session_id} - Invalid", False, f"Exception: {str(e)}")
    
    def test_banks_api(self):
        """Test banks API"""
        print("\n=== TESTING BANKS API ===")
        
        try:
            response = self.session.get(f"{API_BASE}/banks")
            if response.status_code == 200:
                banks_data = response.json()
                banks = banks_data.get('banks', {})
                
                expected_banks = ['sovcombank', 'sber', 'vtb', 'tbank']
                expected_names = ['Совкомбанк', 'Сбер', 'ВТБ', 'Т-Банк']
                
                found_banks = list(banks.keys())
                found_names = [banks[bank]['name'] for bank in found_banks]
                
                if all(bank in found_banks for bank in expected_banks):
                    self.log_test("GET /api/banks - Bank Keys", True, f"Found banks: {found_banks}")
                else:
                    self.log_test("GET /api/banks - Bank Keys", False, f"Expected {expected_banks}, got {found_banks}")
                
                if all(name in found_names for name in expected_names):
                    self.log_test("GET /api/banks - Bank Names", True, f"Found names: {found_names}")
                else:
                    self.log_test("GET /api/banks - Bank Names", False, f"Expected {expected_names}, got {found_names}")
                    
            else:
                self.log_test("GET /api/banks", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("GET /api/banks", False, f"Exception: {str(e)}")
    
    def test_qr_codes_api(self):
        """Test QR codes API"""
        print("\n=== TESTING QR CODES API ===")
        
        # Test valid QR code requests
        test_cases = [
            ("sovcombank", 500),
            ("sber", 1000),
            ("vtb", 2000),
            ("tbank", 3000)
        ]
        
        for bank, amount in test_cases:
            try:
                response = self.session.get(f"{API_BASE}/qr-code/{bank}/{amount}")
                if response.status_code == 200:
                    qr_data = response.json()
                    if 'qr_url' in qr_data and qr_data['bank'] == bank and qr_data['amount'] == amount:
                        self.log_test(f"GET /api/qr-code/{bank}/{amount}", True, f"QR URL: {qr_data['qr_url'][:50]}...")
                    else:
                        self.log_test(f"GET /api/qr-code/{bank}/{amount}", False, f"Invalid response structure: {qr_data}")
                else:
                    self.log_test(f"GET /api/qr-code/{bank}/{amount}", False, f"HTTP {response.status_code}")
            except Exception as e:
                self.log_test(f"GET /api/qr-code/{bank}/{amount}", False, f"Exception: {str(e)}")
        
        # Test invalid bank
        try:
            response = self.session.get(f"{API_BASE}/qr-code/invalidbank/1000")
            if response.status_code == 404:
                self.log_test("GET /api/qr-code - Invalid Bank", True, "Correctly returned 404")
            else:
                self.log_test("GET /api/qr-code - Invalid Bank", False, f"Expected 404, got {response.status_code}")
        except Exception as e:
            self.log_test("GET /api/qr-code - Invalid Bank", False, f"Exception: {str(e)}")
        
        # Test invalid amount
        try:
            response = self.session.get(f"{API_BASE}/qr-code/sber/99999")
            if response.status_code == 404:
                self.log_test("GET /api/qr-code - Invalid Amount", True, "Correctly returned 404")
            else:
                self.log_test("GET /api/qr-code - Invalid Amount", False, f"Expected 404, got {response.status_code}")
        except Exception as e:
            self.log_test("GET /api/qr-code - Invalid Amount", False, f"Exception: {str(e)}")
    
    def test_api_root(self):
        """Test API root endpoint"""
        print("\n=== TESTING API ROOT ===")
        
        try:
            response = self.session.get(f"{API_BASE}/")
            if response.status_code == 200:
                data = response.json()
                if 'message' in data and 'products_count' in data:
                    self.log_test("GET /api/ - Root", True, f"Message: {data['message']}, Products: {data['products_count']}")
                else:
                    self.log_test("GET /api/ - Root", False, f"Unexpected response: {data}")
            else:
                self.log_test("GET /api/ - Root", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("GET /api/ - Root", False, f"Exception: {str(e)}")
    
    def run_all_tests(self):
        """Run all tests"""
        print(f"🚀 Starting Backend API Tests")
        print(f"Backend URL: {BACKEND_URL}")
        print(f"API Base: {API_BASE}")
        
        self.test_api_root()
        self.test_products_api()
        self.test_cart_api()
        self.test_banks_api()
        self.test_qr_codes_api()
        
        # Summary
        print("\n" + "="*50)
        print("TEST SUMMARY")
        print("="*50)
        
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if total - passed > 0:
            print("\nFAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"❌ {result['test']}: {result['details']}")
        
        return passed == total

if __name__ == "__main__":
    tester = BackendTester()
    success = tester.run_all_tests()
    exit(0 if success else 1)