#!/bin/bash
echo "Testing database connection..."
python3 test_connection.py

echo "Creating tables..."
python3 create_tables.py

echo "Generating synthetic data for all tables..."
echo "1. Generating merchants data..."
python3 generate_merchants.py

echo "2. Generating payment gateways data..."
python3 payment_gateways.py

echo "3. Generating payment methods data..."
python3 payment_methods.py

echo "4. Generating POS terminals data..."
python3 pos_terminals.py

echo "5. Generating transactions data (20,000 rows)..."
python3 transactions.py

echo "6. Creating sales report aggregation table..."
python3 sales_report_table.py

echo "Data generation complete!"

