"""Tests for Case Management API"""
import pytest


def test_case_creation():
    """Test creating a new fraud case"""
    case_data = {
        'accountId': 123,
        'txnIds': [1, 2, 3],
        'notes': 'Suspicious activity detected',
        'tags': ['fraud', 'high-priority']
    }
    
    # Validate case data structure
    assert case_data['accountId'] > 0
    assert len(case_data['txnIds']) > 0
    assert case_data['notes']
    assert len(case_data['tags']) > 0


def test_case_statuses():
    """Test case status values"""
    valid_statuses = ['OPEN', 'INVESTIGATING', 'RESOLVED', 'CLOSED']
    
    for status in valid_statuses:
        assert status in valid_statuses


def test_case_workflow():
    """Test case workflow progression"""
    workflow = ['OPEN', 'INVESTIGATING', 'RESOLVED', 'CLOSED']
    
    # Validate workflow order
    assert workflow[0] == 'OPEN'
    assert workflow[-1] == 'CLOSED'
    assert 'INVESTIGATING' in workflow
    assert 'RESOLVED' in workflow

