from db_connection import db


# Table creation statements
CREATE_TABLE_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS merchants (
        merchant_id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        address VARCHAR(255),
        city VARCHAR(100),
        state VARCHAR(100),
        pin_code VARCHAR(10),
        contact_number VARCHAR(20),
        email VARCHAR(100),
        gst_number VARCHAR(50),
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS payment_gateways (
        payment_gateway_id SERIAL PRIMARY KEY,
        gateway_name VARCHAR(100) NOT NULL,
        gateway_type VARCHAR(20) NOT NULL,
        api_endpoint VARCHAR(255),
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS payment_methods (
        payment_method_id SERIAL PRIMARY KEY,
        method_name VARCHAR(50) NOT NULL,
        description VARCHAR(256)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS pos_terminals (
        pos_terminal_id SERIAL PRIMARY KEY,
        merchant_id INTEGER REFERENCES merchants(merchant_id),
        terminal_name VARCHAR(100),
        serial_number VARCHAR(100) NOT NULL UNIQUE,
        terminal_type VARCHAR(10) NOT NULL,
        location VARCHAR(255),
        status VARCHAR(20) DEFAULT 'ACTIVE',
        last_maintenance TIMESTAMP,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS transactions (
        transaction_id SERIAL PRIMARY KEY,
        pos_terminal_id INTEGER REFERENCES pos_terminals(pos_terminal_id),
        payment_method_id INTEGER REFERENCES payment_methods(payment_method_id),
        amount NUMERIC(10, 2),
        transaction_status VARCHAR(20) DEFAULT 'PENDING',
        transaction_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        card_number_last4 VARCHAR(4),
        upi_transaction_id VARCHAR(100),
        payment_gateway_id INTEGER REFERENCES payment_gateways(payment_gateway_id)
    );
    """
]

def create_tables():
    for idx, stmt in enumerate(CREATE_TABLE_STATEMENTS, 1):
        try:
            db.execute_sql(stmt)
            print(f"Table {idx}: Created successfully.")
        except Exception as e:
            print(f"Table {idx}: Error creating table - {e}")

if __name__ == "__main__":
    create_tables()
