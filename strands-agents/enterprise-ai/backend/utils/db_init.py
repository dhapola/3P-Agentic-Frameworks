"""
Database initialization script for self-managed PostgreSQL.
Creates tables if they don't exist.
"""

import logging
from utils.database import DatabaseManager

logger = logging.getLogger(__name__)

def init_database():
    """Initialize the database by creating necessary tables."""
    db = DatabaseManager()
    
    # Skip if database is not configured
    if not db.engine:
        logger.warning("Database not configured. Skipping initialization.")
        return
    
    try:
        # Create chat_history table if it doesn't exist
        create_chat_history_table = """
        CREATE TABLE IF NOT EXISTS chat_history (
            id SERIAL PRIMARY KEY,
            thread_id VARCHAR(255) NOT NULL,
            user_id VARCHAR(255) NOT NULL,
            thread_title TEXT,
            ui_msgs JSONB,
            agent_msgs JSONB,
            date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            deleted BOOLEAN DEFAULT FALSE,
            UNIQUE(thread_id, user_id)
        );
        """
        
        # Create indexes for better performance
        create_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_chat_history_thread_user ON chat_history(thread_id, user_id);",
            "CREATE INDEX IF NOT EXISTS idx_chat_history_user_date ON chat_history(user_id, date DESC);",
            "CREATE INDEX IF NOT EXISTS idx_chat_history_deleted ON chat_history(deleted);"
        ]
        
        # Execute table creation
        db.execute_write(create_chat_history_table)
        logger.info("chat_history table created/verified successfully")
        
        # Execute index creation
        for index_query in create_indexes:
            db.execute_write(index_query)
        
        logger.info("Database indexes created/verified successfully")
        logger.info("Database initialization completed successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise

def create_sample_data():
    """Create sample data for testing (optional)."""
    db = DatabaseManager()
    
    if not db.engine:
        logger.warning("Database not configured. Skipping sample data creation.")
        return
    
    try:
        # Check if sample data already exists
        existing_data = db.execute_query(
            "SELECT COUNT(*) as count FROM chat_history WHERE user_id = :user_id",
            {"user_id": "sample_user"}
        )
        
        if existing_data[0]["count"] > 0:
            logger.info("Sample data already exists. Skipping creation.")
            return
        
        # Insert sample chat thread
        sample_thread = {
            "thread_id": "sample_thread_001",
            "user_id": "sample_user",
            "thread_title": "Sample Chat Thread",
            "ui_msgs": '[]',
            "agent_msgs": '[]',
            "deleted": False
        }
        
        insert_query = """
        INSERT INTO chat_history (thread_id, user_id, thread_title, ui_msgs, agent_msgs, deleted)
        VALUES (:thread_id, :user_id, :thread_title, :ui_msgs, :agent_msgs, :deleted)
        """
        
        db.execute_write(insert_query, sample_thread)
        logger.info("Sample data created successfully")
        
    except Exception as e:
        logger.error(f"Failed to create sample data: {str(e)}")
        raise
