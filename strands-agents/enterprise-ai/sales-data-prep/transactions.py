import random
from datetime import datetime, timedelta
from db_connection import db

# Transaction statuses
transaction_statuses = ['COMPLETED', 'PENDING', 'FAILED', 'REFUNDED', 'CANCELLED']

# Transaction status weights (for realistic distribution)
status_weights = [0.75, 0.1, 0.08, 0.05, 0.02]  # 75% completed, 10% pending, etc.

def get_pos_terminal_ids():
    """Fetch existing POS terminal IDs from the database"""
    try:
        result = db.fetch_all("SELECT pos_terminal_id FROM pos_terminals WHERE status = 'ACTIVE'")
        terminal_ids = [row[0] for row in result]
        return terminal_ids
    except Exception as e:
        print(f"Error fetching POS terminal IDs: {e}")
        return []

def get_payment_method_ids():
    """Fetch existing payment method IDs from the database"""
    try:
        result = db.fetch_all("SELECT payment_method_id FROM payment_methods")
        method_ids = [row[0] for row in result]
        return method_ids
    except Exception as e:
        print(f"Error fetching payment method IDs: {e}")
        return []

def get_payment_gateway_ids():
    """Fetch existing payment gateway IDs from the database"""
    try:
        result = db.fetch_all("SELECT payment_gateway_id FROM payment_gateways")
        gateway_ids = [row[0] for row in result]
        return gateway_ids
    except Exception as e:
        print(f"Error fetching payment gateway IDs: {e}")
        return []

def generate_transaction_date():
    """Generate a random transaction date within the specified range (April 1, 2024 to June 22, 2025)"""
    start_date = datetime(2024, 4, 1)
    end_date = datetime(2025, 6, 22)
    
    # Calculate the difference in days
    delta_days = (end_date - start_date).days
    
    # Generate a random number of days to add to the start date
    random_days = random.randint(0, delta_days)
    
    # Generate random hours, minutes, and seconds
    random_hours = random.randint(0, 23)
    random_minutes = random.randint(0, 59)
    random_seconds = random.randint(0, 59)
    
    # Calculate the transaction date
    transaction_date = start_date + timedelta(
        days=random_days,
        hours=random_hours,
        minutes=random_minutes,
        seconds=random_seconds
    )
    
    return transaction_date.strftime('%Y-%m-%d %H:%M:%S')

def generate_card_last4():
    """Generate last 4 digits of a card number"""
    return ''.join(random.choices('0123456789', k=4))

def generate_upi_transaction_id():
    """Generate a UPI transaction ID"""
    prefix = random.choice(['UPI', 'BHIM', 'GPay', 'PhonePe', 'Paytm'])
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    suffix = ''.join(random.choices('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=8))
    return f"{prefix}-{timestamp}-{suffix}"

def insert_transactions(num_transactions=20000):
    try:
        # Get existing IDs from related tables
        terminal_ids = get_pos_terminal_ids()
        payment_method_ids = get_payment_method_ids()
        gateway_ids = get_payment_gateway_ids()
        
        if not terminal_ids or not payment_method_ids or not gateway_ids:
            print("Missing required data in related tables. Please run the other scripts first.")
            return
        
        successful_inserts = 0
        batch_size = 100  # Insert in batches for better performance
        transactions_data = []
        
        print(f"Starting to insert {num_transactions} transactions...")
        print(f"Using {len(terminal_ids)} terminals, {len(payment_method_ids)} payment methods, and {len(gateway_ids)} gateways")
        
        for i in range(num_transactions):
            # Select random IDs from related tables
            pos_terminal_id = random.choice(terminal_ids)
            payment_method_id = random.choice(payment_method_ids)
            payment_gateway_id = random.choice(gateway_ids)
            
            # Generate transaction amount (between ₹10 and ₹10,000)
            amount = round(random.uniform(10, 10000), 2)
            
            # Generate transaction status based on weighted distribution
            transaction_status = random.choices(transaction_statuses, weights=status_weights, k=1)[0]
            
            # Generate transaction date
            transaction_date = generate_transaction_date()
            
            # Card number last 4 digits (only for credit/debit card methods)
            card_last4 = None
            if payment_method_id in [1, 2]:  # Assuming 1 and 2 are Credit Card and Debit Card
                card_last4 = generate_card_last4()
            
            # UPI transaction ID (only for UPI method)
            upi_transaction_id = None
            if payment_method_id == 3:  # Assuming 3 is UPI
                upi_transaction_id = generate_upi_transaction_id()
            
            transaction_data = {
                'pos_terminal_id': pos_terminal_id,
                'payment_method_id': payment_method_id,
                'amount': amount,
                'transaction_status': transaction_status,
                'transaction_date': transaction_date,
                'card_number_last4': card_last4,
                'upi_transaction_id': upi_transaction_id,
                'payment_gateway_id': payment_gateway_id
            }
            transactions_data.append(transaction_data)
            
            # Insert in batches
            if len(transactions_data) >= batch_size:
                sql = """
                    INSERT INTO transactions (pos_terminal_id, payment_method_id, amount, 
                                            transaction_status, transaction_date, card_number_last4, 
                                            upi_transaction_id, payment_gateway_id) 
                    VALUES (:pos_terminal_id, :payment_method_id, :amount, 
                            :transaction_status, :transaction_date, :card_number_last4, 
                            :upi_transaction_id, :payment_gateway_id)
                """
                
                db.execute_many(sql, transactions_data)
                successful_inserts += len(transactions_data)
                print(f"Inserted batch of {len(transactions_data)} transactions. Total: {successful_inserts}")
                transactions_data = []
        
        # Insert remaining transactions
        if transactions_data:
            sql = """
                INSERT INTO transactions (pos_terminal_id, payment_method_id, amount, 
                                        transaction_status, transaction_date, card_number_last4, 
                                        upi_transaction_id, payment_gateway_id) 
                VALUES (:pos_terminal_id, :payment_method_id, :amount, 
                        :transaction_status, :transaction_date, :card_number_last4, 
                        :upi_transaction_id, :payment_gateway_id)
            """
            
            db.execute_many(sql, transactions_data)
            successful_inserts += len(transactions_data)
            
        print(f"Successfully inserted {successful_inserts} transactions using SQLAlchemy.")
    except Exception as e:
        print(f"Database error: {e}")

if __name__ == "__main__":
    insert_transactions(20000)  # Generate 20000 transactions
