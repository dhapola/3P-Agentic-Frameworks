# POS Transaction Data Generator

This project generates synthetic data for a Point of Sale (POS) transaction system. It creates realistic data for merchants, payment gateways, payment methods, POS terminals, and transactions.

## Database Schema

The database consists of the following tables:

1. **merchants** - Stores merchant information
2. **payment_gateways** - Stores payment gateway information
3. **payment_methods** - Stores payment method information
4. **pos_terminals** - Stores POS terminal information
5. **transactions** - Stores transaction information
6. **state_zones** - Maps states to geographical zones
7. **daily_sales_report** - Aggregated sales data for reporting

## Setup

1. Create a virtual environment:
   ```
   python3 -m venv venv
   ```

2. Activate the virtual environment:
   ```
   source venv/bin/activate
   ```

3. Install required packages:
   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file with your database credentials:
   ```
   DB_HOST=localhost
   DB_NAME=paymentsdb
   DB_PORT=5432
   DB_USERNAME=your_db_username
   DB_PASSWORD=your_db_password
   REGION=ap-south-1
   ```

5. Ensure PostgreSQL is running and the database exists:
   ```
   # Connect to PostgreSQL and create database
   psql -U postgres
   CREATE DATABASE paymentsdb;
   CREATE USER paymentsappuser WITH PASSWORD 'payapp@2025';
   GRANT ALL PRIVILEGES ON DATABASE paymentsdb TO paymentsappuser;
   ```

## Data Generation Scripts

1. **test_connection.py** - Tests database connection and basic operations
2. **db_connection.py** - Database connection utility using SQLAlchemy
3. **create_tables.py** - Creates all database tables
4. **generate_merchants.py** - Generates 100 merchants
5. **payment_gateways.py** - Generates 20 payment gateways
6. **payment_methods.py** - Generates 10 payment methods
7. **pos_terminals.py** - Generates 2-5 POS terminals per merchant
8. **transactions.py** - Generates 20,000 transactions
9. **sales_report_table.py** - Creates aggregated sales report table
10. **query_sales_report.py** - Runs various reports on the sales data

## Running the Scripts

You can run all data generation scripts in sequence using:

```
./generate_all_data.sh
```

Or run individual scripts:

```
python test_connection.py
python create_tables.py
python generate_merchants.py
python payment_gateways.py
python payment_methods.py
python pos_terminals.py
python transactions.py
python sales_report_table.py
```

## Reporting

To view sales reports:

```
python query_sales_report.py
```

This will display:
- Sales summary by zone
- Monthly sales trend
- Top 5 performing states
- Transaction status summary

## Data Features

- Realistic Indian merchant data with proper GST numbers
- Common payment gateways and methods
- POS terminals with realistic serial numbers and statuses
- Transactions with appropriate payment methods and statuses
- Geographical zone mapping for states
- Time-based aggregation (day, month, quarter, year)
- Transaction status tracking (completed, pending, failed, etc.)
- **Now uses SQLAlchemy with localhost PostgreSQL instead of AWS Aurora**
- **Improved performance with batch inserts**
- **Better error handling and connection management**
