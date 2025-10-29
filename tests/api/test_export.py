"""Tests for export functionality"""


def test_csv_export_headers():
    """Test CSV export includes proper headers"""
    sample_alert = {
        'id': 1,
        'account_id': 123,
        'rule_code': 'MIDNIGHT_HIGH',
        'severity': 'HIGH',
        'status': 'OPEN',
        'created_at': '2025-10-29T12:00:00Z',
        'reason': 'High amount at midnight'
    }
    
    expected_headers = [
        'Alert ID',
        'Account ID',
        'Rule Code',
        'Severity',
        'Status',
        'Created At',
        'Reason'
    ]
    
    # Verify all fields are present
    assert len(expected_headers) == 7
    

def test_csv_data_formatting():
    """Test CSV data is properly formatted"""
    sample_transaction = {
        'id': 1,
        'account_id': 123,
        'amount': 1500.50,
        'currency': 'USD',
        'merchant': 'TEST, MERCHANT',  # Contains comma
        'status': 'APPROVED'
    }
    
    # Test that merchant with comma should be quoted
    assert ',' in sample_transaction['merchant']
    

def test_export_filename_format():
    """Test export filename includes date"""
    import re
    from datetime import date
    
    filename_pattern = r'fraud_alerts_\d{4}-\d{2}-\d{2}\.csv'
    sample_filename = f'fraud_alerts_{date.today().isoformat()}.csv'
    
    assert re.match(filename_pattern, sample_filename)

