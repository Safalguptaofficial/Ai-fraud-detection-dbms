"""Tests for ML Risk Scoring API"""
import pytest
import sys
from pathlib import Path

# Add services/api to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "services" / "api"))

from ml_risk_scorer import MLRiskScorer


def test_risk_scorer_initialization():
    """Test risk scorer initializes correctly"""
    scorer = MLRiskScorer()
    assert scorer.weights is not None
    assert len(scorer.weights) == 6
    assert sum(scorer.weights.values()) == pytest.approx(1.0)


def test_high_amount_score():
    """Test high amount transactions get high risk scores"""
    scorer = MLRiskScorer()
    
    high_amount_txn = {
        'amount': 10000,
        'txn_time': '2025-10-29T14:30:00Z',
        'channel': 'POS',
        'merchant': 'GROCERY',
        'mcc': '5411',
        'country': 'US'
    }
    
    score = scorer.calculate_risk_score(high_amount_txn)
    assert score > 50  # High amounts should increase risk


def test_midnight_transaction_score():
    """Test midnight transactions get flagged"""
    scorer = MLRiskScorer()
    
    midnight_txn = {
        'amount': 500,
        'txn_time': '2025-10-29T02:30:00Z',  # 2:30 AM
        'channel': 'ATM',
        'merchant': 'ATM-CORP',
        'mcc': '6011',
        'country': 'US'
    }
    
    score = scorer.calculate_risk_score(midnight_txn)
    assert score > 40  # Midnight transactions are risky


def test_atm_channel_risk():
    """Test ATM channel has higher risk"""
    scorer = MLRiskScorer()
    
    atm_txn = {
        'amount': 1000,
        'txn_time': '2025-10-29T14:30:00Z',
        'channel': 'ATM',
        'merchant': 'ATM-CORP',
        'mcc': '6011',
        'country': 'US'
    }
    
    pos_txn = {
        'amount': 1000,
        'txn_time': '2025-10-29T14:30:00Z',
        'channel': 'POS',
        'merchant': 'GROCERY',
        'mcc': '5411',
        'country': 'US'
    }
    
    atm_score = scorer.calculate_risk_score(atm_txn)
    pos_score = scorer.calculate_risk_score(pos_txn)
    
    assert atm_score > pos_score


def test_risk_level_classification():
    """Test risk level classification"""
    scorer = MLRiskScorer()
    
    assert scorer.get_risk_level(80) == 'CRITICAL'
    assert scorer.get_risk_level(60) == 'HIGH'
    assert scorer.get_risk_level(40) == 'MEDIUM'
    assert scorer.get_risk_level(20) == 'LOW'


def test_velocity_scoring():
    """Test velocity scoring increases with transaction count"""
    scorer = MLRiskScorer()
    
    low_velocity = []
    high_velocity = [{'id': i} for i in range(15)]
    
    txn = {
        'amount': 100,
        'txn_time': '2025-10-29T14:30:00Z',
        'channel': 'POS',
        'merchant': 'GROCERY',
        'mcc': '5411',
        'country': 'US'
    }
    
    low_score = scorer.calculate_risk_score(txn, low_velocity)
    high_score = scorer.calculate_risk_score(txn, high_velocity)
    
    assert high_score > low_score


def test_score_explanation():
    """Test score explanation provides details"""
    scorer = MLRiskScorer()
    
    txn = {
        'amount': 5000,
        'txn_time': '2025-10-29T02:30:00Z',
        'channel': 'ATM',
        'merchant': 'ATM-CORP',
        'mcc': '6011',
        'country': 'US'
    }
    
    score = scorer.calculate_risk_score(txn)
    explanation = scorer.explain_score(txn, score)
    
    assert 'risk_score' in explanation
    assert 'risk_level' in explanation
    assert 'factors' in explanation
    assert 'recommendation' in explanation
    assert explanation['risk_score'] == pytest.approx(score, abs=0.1)


def test_score_bounds():
    """Test risk scores are always between 0 and 100"""
    scorer = MLRiskScorer()
    
    # Test various transactions
    test_cases = [
        {'amount': 10, 'txn_time': '2025-10-29T14:30:00Z', 'channel': 'POS', 'merchant': 'GROCERY', 'mcc': '5411'},
        {'amount': 10000, 'txn_time': '2025-10-29T02:30:00Z', 'channel': 'ATM', 'merchant': 'ATM-CORP', 'mcc': '6011'},
        {'amount': 500, 'txn_time': '2025-10-29T10:00:00Z', 'channel': 'ONLINE', 'merchant': 'AMAZON', 'mcc': '5999'},
    ]
    
    for txn in test_cases:
        score = scorer.calculate_risk_score(txn)
        assert 0 <= score <= 100

