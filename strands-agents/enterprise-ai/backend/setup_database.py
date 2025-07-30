#!/usr/bin/env python3
"""
Database setup script for AIUI application.
This script helps set up the PostgreSQL database and test the connection.
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.database import DatabaseManager
from utils.db_init import init_database, create_sample_data

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main setup function."""
    print("🚀 AIUI Database Setup")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    
    # Check required environment variables
    required_vars = ['DB_HOST', 'DB_NAME', 'DB_USERNAME', 'DB_PASSWORD']
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease update your .env file with the required database configuration.")
        return False
    
    print("✅ Environment variables loaded")
    print(f"   - Host: {os.environ.get('DB_HOST')}")
    print(f"   - Port: {os.environ.get('DB_PORT', '5432')}")
    print(f"   - Database: {os.environ.get('DB_NAME')}")
    print(f"   - Username: {os.environ.get('DB_USERNAME')}")
    print()
    
    # Test database connection
    print("🔍 Testing database connection...")
    db = DatabaseManager()
    connection_test = db.test_connection()
    
    if connection_test['connected']:
        print("✅ Database connection successful!")
        print(f"   - PostgreSQL Version: {connection_test.get('postgresql_version', 'Unknown')}")
        print(f"   - Current Database: {connection_test.get('current_database', 'Unknown')}")
        print(f"   - Current User: {connection_test.get('current_user', 'Unknown')}")
        print()
    else:
        print("❌ Database connection failed!")
        print(f"   Error: {connection_test.get('message', 'Unknown error')}")
        return False
    
    # Initialize database schema
    print("🏗️  Initializing database schema...")
    try:
        init_database()
        print("✅ Database schema initialized successfully!")
        print()
    except Exception as e:
        print(f"❌ Failed to initialize database schema: {str(e)}")
        return False
    
    # Ask if user wants to create sample data
    create_samples = input("📝 Create sample data for testing? (y/N): ").lower().strip()
    if create_samples in ['y', 'yes']:
        try:
            create_sample_data()
            print("✅ Sample data created successfully!")
        except Exception as e:
            print(f"❌ Failed to create sample data: {str(e)}")
    
    print()
    print("🎉 Database setup completed successfully!")
    print("You can now start your application with: python app.py")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
