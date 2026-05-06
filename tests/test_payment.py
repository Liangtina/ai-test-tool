"""
Test cases for Payment Service
"""
import pytest
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from payment_service import PaymentService


class TestPaymentService:
    """Test suite for PaymentService"""
    
    @pytest.fixture
    def payment_service(self):
        """Create a fresh payment service instance for each test"""
        return PaymentService()
    
    # Positive Test Cases
    
    def test_successful_payment(self, payment_service):
        """Test successful payment processing"""
        result = payment_service.process_payment(
            amount=100.50,
            card_number="1234567890123456",
            cvv="123"
        )
        
        assert result["status"] == "success"
        assert result["transaction_id"] is not None
        assert result["message"] == "Payment processed successfully"
    
    def test_multiple_payments(self, payment_service):
        """Test processing multiple payments"""
        result1 = payment_service.process_payment(100.00, "1234567890123456", "123")
        result2 = payment_service.process_payment(200.00, "9876543210987654", "456")
        
        assert result1["status"] == "success"
        assert result2["status"] == "success"
        assert result1["transaction_id"] != result2["transaction_id"]
        assert len(payment_service.get_all_transactions()) == 2
    
    def test_get_transaction(self, payment_service):
        """Test retrieving transaction details"""
        result = payment_service.process_payment(150.00, "1234567890123456", "123")
        transaction_id = result["transaction_id"]
        
        transaction = payment_service.get_transaction(transaction_id)
        
        assert transaction is not None
        assert transaction["transaction_id"] == transaction_id
        assert transaction["amount"] == 150.00
    
    def test_successful_refund(self, payment_service):
        """Test successful refund processing"""
        # First make a payment
        payment_result = payment_service.process_payment(100.00, "1234567890123456", "123")
        transaction_id = payment_result["transaction_id"]
        
        # Then refund it
        refund_result = payment_service.refund_payment(transaction_id)
        
        assert refund_result["status"] == "success"
        assert refund_result["message"] == "Refund processed successfully"
    
    # Negative Test Cases
    
    def test_invalid_amount_zero(self, payment_service):
        """Test payment with zero amount"""
        result = payment_service.process_payment(0, "1234567890123456", "123")
        
        assert result["status"] == "failed"
        assert result["message"] == "Invalid amount"
        assert result["transaction_id"] is None
    
    def test_invalid_amount_negative(self, payment_service):
        """Test payment with negative amount"""
        result = payment_service.process_payment(-50.00, "1234567890123456", "123")
        
        assert result["status"] == "failed"
        assert result["message"] == "Invalid amount"
    
    def test_invalid_card_number_short(self, payment_service):
        """Test payment with short card number"""
        result = payment_service.process_payment(100.00, "123456", "123")
        
        assert result["status"] == "failed"
        assert result["message"] == "Invalid card number"
    
    def test_invalid_card_number_empty(self, payment_service):
        """Test payment with empty card number"""
        result = payment_service.process_payment(100.00, "", "123")
        
        assert result["status"] == "failed"
        assert result["message"] == "Invalid card number"
    
    def test_invalid_cvv_short(self, payment_service):
        """Test payment with short CVV"""
        result = payment_service.process_payment(100.00, "1234567890123456", "12")
        
        assert result["status"] == "failed"
        assert result["message"] == "Invalid CVV"
    
    def test_invalid_cvv_empty(self, payment_service):
        """Test payment with empty CVV"""
        result = payment_service.process_payment(100.00, "1234567890123456", "")
        
        assert result["status"] == "failed"
        assert result["message"] == "Invalid CVV"
    
    def test_refund_nonexistent_transaction(self, payment_service):
        """Test refunding a transaction that doesn't exist"""
        result = payment_service.refund_payment("TXN999999")
        
        assert result["status"] == "failed"
        assert result["message"] == "Transaction not found"
    
    def test_duplicate_refund(self, payment_service):
        """Test refunding the same transaction twice"""
        # Make a payment
        payment_result = payment_service.process_payment(100.00, "1234567890123456", "123")
        transaction_id = payment_result["transaction_id"]
        
        # First refund should succeed
        refund1 = payment_service.refund_payment(transaction_id)
        assert refund1["status"] == "success"
        
        # Second refund should fail
        refund2 = payment_service.refund_payment(transaction_id)
        assert refund2["status"] == "failed"
        assert refund2["message"] == "Transaction already refunded"
    
    # Edge Cases
    
    def test_large_amount_payment(self, payment_service):
        """Test payment with large amount"""
        result = payment_service.process_payment(999999.99, "1234567890123456", "123")
        
        assert result["status"] == "success"
    
    def test_small_amount_payment(self, payment_service):
        """Test payment with small valid amount"""
        result = payment_service.process_payment(0.01, "1234567890123456", "123")
        
        assert result["status"] == "success"
    
    def test_get_all_transactions_empty(self, payment_service):
        """Test getting all transactions when none exist"""
        transactions = payment_service.get_all_transactions()
        
        assert transactions == []
    
    def test_get_nonexistent_transaction(self, payment_service):
        """Test getting a transaction that doesn't exist"""
        transaction = payment_service.get_transaction("TXN999999")
        
        assert transaction is None
    
    def test_card_number_masking(self, payment_service):
        """Test that card numbers are properly masked in transactions"""
        payment_service.process_payment(100.00, "1234567890123456", "123")
        transaction = payment_service.get_all_transactions()[0]
        
        assert transaction["card_number"] == "****3456"
        assert "1234567890123456" not in str(transaction)
