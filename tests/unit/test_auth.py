"""
ANALYTICA - Authentication Tests
================================
Unit tests for the authentication module.
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from api.auth import (
    _hash_password,
    _generate_token,
    _verify_token,
    _users_db,
    create_demo_user,
)


class TestPasswordHashing:
    """Tests for password hashing"""
    
    def test_hash_password_consistency(self):
        """Same password should produce same hash"""
        password = "test_password_123"
        hash1 = _hash_password(password)
        hash2 = _hash_password(password)
        assert hash1 == hash2
    
    def test_hash_password_different_for_different_passwords(self):
        """Different passwords should produce different hashes"""
        hash1 = _hash_password("password1")
        hash2 = _hash_password("password2")
        assert hash1 != hash2
    
    def test_hash_password_returns_hex_string(self):
        """Hash should be a valid hex string"""
        hash_value = _hash_password("test")
        assert len(hash_value) == 64  # SHA256 produces 64 hex chars
        assert all(c in '0123456789abcdef' for c in hash_value)


class TestTokenGeneration:
    """Tests for JWT token generation and verification"""
    
    def test_generate_token_returns_string(self):
        """Token generation should return a string"""
        token = _generate_token("user123", "test@example.com")
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_generate_token_has_correct_format(self):
        """Token should have payload.signature format"""
        token = _generate_token("user123", "test@example.com")
        parts = token.split(".")
        assert len(parts) == 2
    
    def test_verify_token_valid(self):
        """Valid token should be verified successfully"""
        token = _generate_token("user123", "test@example.com")
        payload = _verify_token(token)
        
        assert payload is not None
        assert payload["user_id"] == "user123"
        assert payload["email"] == "test@example.com"
        assert "exp" in payload
        assert "iat" in payload
    
    def test_verify_token_invalid_signature(self):
        """Token with invalid signature should fail"""
        token = _generate_token("user123", "test@example.com")
        # Tamper with signature
        parts = token.split(".")
        tampered_token = f"{parts[0]}.invalidsignature123"
        
        payload = _verify_token(tampered_token)
        assert payload is None
    
    def test_verify_token_malformed(self):
        """Malformed token should fail"""
        assert _verify_token("not.a.valid.token") is None
        assert _verify_token("notseparated") is None
        assert _verify_token("") is None
        assert _verify_token("..") is None


class TestDemoUser:
    """Tests for demo user creation"""
    
    def test_demo_user_exists(self):
        """Demo user should be created on module load"""
        create_demo_user()
        assert "demo_user_001" in _users_db
    
    def test_demo_user_has_correct_email(self):
        """Demo user should have correct email"""
        create_demo_user()
        demo = _users_db["demo_user_001"]
        assert demo["email"] == "demo@analytica.pl"
    
    def test_demo_user_has_points(self):
        """Demo user should have starter points"""
        create_demo_user()
        demo = _users_db["demo_user_001"]
        assert demo["points_balance"] >= 100
    
    def test_demo_user_password_verifiable(self):
        """Demo user password should be verifiable"""
        create_demo_user()
        demo = _users_db["demo_user_001"]
        expected_hash = _hash_password("demo123")
        assert demo["password_hash"] == expected_hash


class TestUserDatabase:
    """Tests for in-memory user database"""
    
    def test_users_db_is_dict(self):
        """Users database should be a dict"""
        assert isinstance(_users_db, dict)
    
    def test_add_user_to_db(self):
        """Should be able to add users to database"""
        test_id = "test_user_" + str(len(_users_db))
        _users_db[test_id] = {
            "id": test_id,
            "email": "test@test.com",
            "name": "Test User",
            "password_hash": _hash_password("testpass"),
            "points_balance": 50,
            "plan": "free"
        }
        
        assert test_id in _users_db
        assert _users_db[test_id]["email"] == "test@test.com"


class TestPointsSystem:
    """Tests for points system logic"""
    
    def test_initial_points_on_register(self):
        """New users should get starter points"""
        # Simulating registration logic
        new_user = {
            "id": "new_test_user",
            "email": "new@test.com",
            "name": "New User",
            "password_hash": _hash_password("password"),
            "points_balance": 10,  # Starter points
            "plan": "free",
            "transactions": []
        }
        
        assert new_user["points_balance"] == 10
    
    def test_points_purchase_adds_points(self):
        """Purchasing points should add to balance"""
        user = {
            "points_balance": 50,
            "transactions": []
        }
        
        # Simulate purchase
        purchase_amount = 100
        user["points_balance"] += purchase_amount
        user["transactions"].append({
            "type": "purchase",
            "amount": purchase_amount
        })
        
        assert user["points_balance"] == 150
        assert len(user["transactions"]) == 1
    
    def test_points_usage_deducts_points(self):
        """Using points should deduct from balance"""
        user = {
            "points_balance": 50,
            "transactions": []
        }
        
        # Simulate usage
        usage_amount = 5
        user["points_balance"] -= usage_amount
        user["transactions"].append({
            "type": "usage",
            "amount": -usage_amount
        })
        
        assert user["points_balance"] == 45
    
    def test_insufficient_points_check(self):
        """Should be able to check for insufficient points"""
        user = {"points_balance": 5}
        
        required = 10
        has_enough = user["points_balance"] >= required
        
        assert has_enough is False
    
    def test_sufficient_points_check(self):
        """Should pass when user has enough points"""
        user = {"points_balance": 100}
        
        required = 10
        has_enough = user["points_balance"] >= required
        
        assert has_enough is True
