#!/usr/bin/env python3
"""
WSGI entry point for PDF Invoice Parser Web Service
Production deployment configuration
"""

import os
import sys
import logging
from logging.handlers import RotatingFileHandler

# Add the current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from app import app

# Production configuration
class ProductionConfig:
    """Production configuration settings"""
    DEBUG = False
    TESTING = False
    LOG_LEVEL = logging.INFO
    LOG_FILE = '/var/log/pdf-parser/app.log'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    
def setup_logging():
    """Setup production logging"""
    # Create log directory if it doesn't exist
    log_dir = os.path.dirname(ProductionConfig.LOG_FILE)
    os.makedirs(log_dir, exist_ok=True)
    
    # Setup rotating file handler
    file_handler = RotatingFileHandler(
        ProductionConfig.LOG_FILE,
        maxBytes=10485760,  # 10MB
        backupCount=5
    )
    
    # Format logs
    formatter = logging.Formatter(
        '%(asctime)s %(levelname)s [%(name)s] %(message)s'
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(ProductionConfig.LOG_LEVEL)
    
    # Add handler to app logger
    app.logger.addHandler(file_handler)
    app.logger.setLevel(ProductionConfig.LOG_LEVEL)
    
    # Add handler to root logger for other modules
    root_logger = logging.getLogger()
    root_logger.addHandler(file_handler)
    root_logger.setLevel(ProductionConfig.LOG_LEVEL)

def create_application():
    """Create and configure the application for production"""
    
    # Apply production configuration
    app.config.from_object(ProductionConfig)
    
    # Setup logging
    setup_logging()
    
    # Log startup
    app.logger.info("PDF Invoice Parser Web Service starting in production mode")
    app.logger.info(f"Log file: {ProductionConfig.LOG_FILE}")
    app.logger.info(f"Max upload size: {ProductionConfig.MAX_CONTENT_LENGTH} bytes")
    
    return app

# Create the application instance
application = create_application()

if __name__ == "__main__":
    # This won't be used in production, but useful for testing
    application.run(host='0.0.0.0', port=5000)