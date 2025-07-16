#!/usr/bin/env python3
"""
Basic test for research environment
"""

def test_basic():
    """Basic test function"""
    assert 1 + 1 == 2
    print("Basic test passed!")

def test_simple_calculation():
    """Test simple calculation"""
    result = sum(range(5))
    assert result == 10
    print("Simple calculation test passed!")

if __name__ == "__main__":
    test_basic()
    test_simple_calculation()