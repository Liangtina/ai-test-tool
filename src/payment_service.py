"""
Dummy Payment Service for Testing
"""

class PaymentService:
    """Simple payment service for demonstration"""
    
    def __init__(self):
        self.transactions = []
    
    def process_payment(self, amount, card_number, cvv):
        """
        Process a payment transaction
        
        Args:
            amount (float): Payment amount
            card_number (str): Card number
            cvv (str): CVV code
            
        Returns:
            dict: Transaction result
        """
        if amount <= 0:
            return {
                "status": "failed",
                "message": "Invalid amount",
                "transaction_id": None
            }
        
        if not card_number or len(card_number) != 16:
            return {
                "status": "failed",
                "message": "Invalid card number",
                "transaction_id": None
            }
        
        if not cvv or len(cvv) != 3:
            return {
                "status": "failed",
                "message": "Invalid CVV",
                "transaction_id": None
            }
        
        transaction_id = f"TXN{len(self.transactions) + 1:06d}"
        transaction = {
            "transaction_id": transaction_id,
            "amount": amount,
            "card_number": f"****{card_number[-4:]}",
            "status": "success"
        }
        
        self.transactions.append(transaction)
        
        return {
            "status": "success",
            "message": "Payment processed successfully",
            "transaction_id": transaction_id
        }
    
    def refund_payment(self, transaction_id):
        """
        Refund a payment
        
        Args:
            transaction_id (str): Transaction ID to refund
            
        Returns:
            dict: Refund result
        """
        transaction = next(
            (t for t in self.transactions if t["transaction_id"] == transaction_id),
            None
        )
        
        if not transaction:
            return {
                "status": "failed",
                "message": "Transaction not found"
            }
        
        if transaction.get("refunded"):
            return {
                "status": "failed",
                "message": "Transaction already refunded"
            }
        
        transaction["refunded"] = True
        
        return {
            "status": "success",
            "message": "Refund processed successfully",
            "transaction_id": transaction_id
        }
    
    def get_transaction(self, transaction_id):
        """
        Get transaction details
        
        Args:
            transaction_id (str): Transaction ID
            
        Returns:
            dict: Transaction details or None
        """
        return next(
            (t for t in self.transactions if t["transaction_id"] == transaction_id),
            None
        )
    
    def get_all_transactions(self):
        """
        Get all transactions
        
        Returns:
            list: All transactions
        """
        return self.transactions.copy()
