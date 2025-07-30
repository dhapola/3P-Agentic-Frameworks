from flask import Flask, jsonify
from flask_restful import Api
from flask_cors import CORS
import os
import logging
from sqlalchemy import text

# Import API resources
from resources.models_api import ModelsResource
from resources.wizard_api import ApiInsightsResource
from resources.chart_api import ChartResource
from resources.streaming_api import StreamAnswerResource
from resources.chat_thread_api import ChatThreadListResource, ChatThreadResource

from providers.mcp_provider import MCPProvider
from utils.db_init import init_database
from utils.database import DatabaseManager
from config import get_config

#import asyncio

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app(config_object=None):
    """Create and configure the Flask application"""
    app = Flask(__name__)
    
    # Load configuration
    if config_object is None:
        config_object = get_config()
    app.config.from_object(config_object)
    
    # Enable CORS
    CORS(app, origins='*', methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
    
    # Initialize API
    api = Api(app)
    
    # Register API resources
    api.add_resource(ModelsResource, '/api/models')
    api.add_resource(ApiInsightsResource, '/api/insights')
    api.add_resource(ChartResource, '/api/chart')
    api.add_resource(StreamAnswerResource, '/api/answer')
    
    # Register thread management APIs
    api.add_resource(ChatThreadListResource, '/api/threads')
    api.add_resource(ChatThreadResource, '/api/thread/<string:thread_id>', '/api/thread')
    

    # Health check endpoint
    @app.route('/health', methods=['GET'])
    def health_check():
        return jsonify({"status": "healthy"})
    
    # Database status endpoint
    @app.route('/db/status', methods=['GET'])
    def db_status():
        db = DatabaseManager()
        return jsonify(db.test_connection())
    
    # Initialize database
    try:
        logger.info("Initializing database connection...")
        init_database()
        logger.info("Database initialization completed successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        logger.warning("Application will continue without database functionality")
    
    # Initialize MCP servers
    mcp_provider = MCPProvider()
    mcp_provider.load_mcp_servers()
    
    return app

def main():
    app = create_app()
    port = app.config.get('PORT', 8080)
    debug = app.config.get('DEBUG', False)
    logger.info(f"Starting server on port {port} with debug={debug}")
    app.run(host='0.0.0.0', port=port, debug=debug)

if __name__ == '__main__':
    main()
