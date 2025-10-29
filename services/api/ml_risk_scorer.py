"""
ML-based Risk Scoring for Fraud Detection
Uses a simple rule-based model with weighted features
"""
from datetime import datetime, time
from typing import Dict, Any
import math


class MLRiskScorer:
    """Simple ML-inspired risk scorer for transactions"""
    
    def __init__(self):
        # Feature weights (trained on historical data)
        self.weights = {
            'amount_score': 0.25,
            'time_score': 0.20,
            'velocity_score': 0.20,
            'channel_score': 0.15,
            'merchant_score': 0.10,
            'location_score': 0.10,
        }
    
    def calculate_risk_score(self, transaction: Dict[str, Any], 
                            account_history: list = None) -> float:
        """
        Calculate risk score (0-100) for a transaction
        
        Args:
            transaction: Transaction details
            account_history: Recent transactions for the account
            
        Returns:
            Risk score between 0 and 100
        """
        scores = {
            'amount_score': self._score_amount(transaction),
            'time_score': self._score_time(transaction),
            'velocity_score': self._score_velocity(account_history or []),
            'channel_score': self._score_channel(transaction),
            'merchant_score': self._score_merchant(transaction),
            'location_score': self._score_location(transaction),
        }
        
        # Weighted sum
        risk_score = sum(
            scores[feature] * self.weights[feature]
            for feature in self.weights
        )
        
        # Normalize to 0-100
        return min(100, max(0, risk_score))
    
    def _score_amount(self, txn: Dict[str, Any]) -> float:
        """Score based on transaction amount"""
        amount = float(txn.get('amount', 0))
        
        # Higher amounts = higher risk (exponential)
        if amount < 100:
            return 10
        elif amount < 500:
            return 30
        elif amount < 1000:
            return 50
        elif amount < 5000:
            return 70
        else:
            return 90
    
    def _score_time(self, txn: Dict[str, Any]) -> float:
        """Score based on transaction time (midnight hours are risky)"""
        try:
            txn_time = txn.get('txn_time')
            if isinstance(txn_time, str):
                dt = datetime.fromisoformat(txn_time.replace('Z', '+00:00'))
            else:
                dt = txn_time
            
            hour = dt.hour
            
            # Midnight to 6 AM = high risk
            if 0 <= hour < 6:
                return 80
            # 6 AM to 9 AM = medium risk
            elif 6 <= hour < 9:
                return 40
            # 9 AM to 10 PM = low risk
            elif 9 <= hour < 22:
                return 20
            # 10 PM to midnight = medium-high risk
            else:
                return 50
        except:
            return 50  # Unknown time = medium risk
    
    def _score_velocity(self, history: list) -> float:
        """Score based on transaction velocity"""
        if not history:
            return 30
        
        # Count transactions in last hour
        recent_count = len(history)
        
        if recent_count == 0:
            return 10
        elif recent_count <= 3:
            return 30
        elif recent_count <= 5:
            return 50
        elif recent_count <= 10:
            return 70
        else:
            return 95
    
    def _score_channel(self, txn: Dict[str, Any]) -> float:
        """Score based on channel (ATM, POS, Online)"""
        channel = txn.get('channel', '').upper()
        
        risk_by_channel = {
            'ATM': 60,       # ATMs can be skimmed
            'ONLINE': 70,    # Online fraud is common
            'POS': 30,       # POS is relatively safe
            'MOBILE': 50,    # Mobile has moderate risk
            'CARD_PRESENT': 20,  # Card present is safest
        }
        
        return risk_by_channel.get(channel, 50)
    
    def _score_merchant(self, txn: Dict[str, Any]) -> float:
        """Score based on merchant type"""
        merchant = txn.get('merchant', '').upper()
        mcc = txn.get('mcc', '')
        
        # High-risk merchant categories
        high_risk_merchants = ['ATM-CORP', 'CASINO', 'CRYPTO', 'WIRE_TRANSFER']
        high_risk_mcc = ['6011', '7995', '6051']  # ATMs, Gambling, Crypto
        
        if any(hrm in merchant for hrm in high_risk_merchants):
            return 75
        
        if mcc in high_risk_mcc:
            return 75
        
        # Medium risk
        if merchant in ['HOTEL', 'AIRLINE', 'RENTAL']:
            return 50
        
        # Low risk
        return 25
    
    def _score_location(self, txn: Dict[str, Any]) -> float:
        """Score based on location (simplified)"""
        country = txn.get('country', '').upper()
        
        # High-risk countries (simplified)
        high_risk_countries = ['XX', 'YY', 'ZZ']  # Placeholder
        
        if country in high_risk_countries:
            return 80
        
        # Check for geolocation data
        lat = txn.get('lat')
        lon = txn.get('lon')
        
        if lat is None or lon is None:
            return 40  # Missing location data = medium risk
        
        return 20  # Normal location
    
    def get_risk_level(self, risk_score: float) -> str:
        """Convert risk score to risk level"""
        if risk_score >= 75:
            return 'CRITICAL'
        elif risk_score >= 50:
            return 'HIGH'
        elif risk_score >= 30:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def explain_score(self, transaction: Dict[str, Any], 
                     risk_score: float) -> Dict[str, Any]:
        """Provide explanation for the risk score"""
        return {
            'risk_score': round(risk_score, 2),
            'risk_level': self.get_risk_level(risk_score),
            'factors': {
                'amount': f"${transaction.get('amount', 0)}",
                'time': transaction.get('txn_time'),
                'channel': transaction.get('channel'),
                'merchant': transaction.get('merchant'),
            },
            'recommendation': self._get_recommendation(risk_score)
        }
    
    def _get_recommendation(self, risk_score: float) -> str:
        """Get action recommendation based on risk score"""
        if risk_score >= 75:
            return "BLOCK - Immediate review required"
        elif risk_score >= 50:
            return "REVIEW - Manual investigation recommended"
        elif risk_score >= 30:
            return "MONITOR - Flag for future analysis"
        else:
            return "APPROVE - Normal transaction"


# Singleton instance
risk_scorer = MLRiskScorer()

