#!/usr/bin/env python3
"""
Test script to verify database connection and basic operations
"""
from db_connection import db

def test_connection():
    """Test database connection and basic operations"""
    try:
        print("Testing database connection...")
        
        # Test basic connection
        result = db.fetch_one("SELECT version()")
        print(f"✅ Database connection successful!")
        print(f"PostgreSQL version: {result[0]}")
        
        # Test table existence
        tables_query = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        ORDER BY table_name
        """
        
        tables = db.fetch_all(tables_query)
        if tables:
            print(f"\n✅ Found {len(tables)} tables:")
            for table in tables:
                print(f"  - {table[0]}")
        else:
            print("\n⚠️  No tables found. Run create_tables.py first.")
        
        # Test a simple insert and select
        print("\n🧪 Testing insert/select operations...")
        
        # Create a test table
        db.execute_sql("""
            CREATE TABLE IF NOT EXISTS test_table (
                id SERIAL PRIMARY KEY,
                name VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Insert test data
        db.execute_sql(
            "INSERT INTO test_table (name) VALUES (:name)",
            {'name': 'Test Connection'}
        )
        
        # Select test data
        result = db.fetch_one("SELECT name FROM test_table WHERE name = :name", {'name': 'Test Connection'})
        if result and result[0] == 'Test Connection':
            print("✅ Insert/Select operations working correctly!")
        else:
            print("❌ Insert/Select operations failed!")
        
        # Clean up test table
        db.execute_sql("DROP TABLE IF EXISTS test_table")
        
        print("\n🎉 All tests passed! Database is ready for use.")
        
    except Exception as e:
        print(f"❌ Database connection test failed: {e}")
        print("\nPlease check:")
        print("1. PostgreSQL is running on localhost:5432")
        print("2. Database 'paymentsdb' exists")
        print("3. User credentials in .env file are correct")
        print("4. User has necessary permissions")

if __name__ == "__main__":
    test_connection()
