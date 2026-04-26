import pytest
from backend.auth.security.password import hash_password, verify_password


def test_hash_password():
    password = "test_password123"
    hashed = hash_password(password)
    
    assert hashed != password
    assert len(hashed) > 0
    assert hashed.startswith("$2b$")


def test_verify_password_correct():
    password = "test_password123"
    hashed = hash_password(password)
    
    assert verify_password(password, hashed) is True


def test_verify_password_incorrect():
    password = "test_password123"
    hashed = hash_password(password)
    
    assert verify_password("wrong_password", hashed) is False


def test_hash_password_different_hashes():
    password = "test_password123"
    hash1 = hash_password(password)
    hash2 = hash_password(password)
    
    assert hash1 != hash2
    assert verify_password(password, hash1) is True
    assert verify_password(password, hash2) is True
