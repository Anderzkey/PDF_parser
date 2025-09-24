#!/usr/bin/env python3
"""
PDF Invoice Parser Web Service
Flask-based REST API for parsing Russian warehouse invoice PDFs
"""

import os
import uuid
import tempfile
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
import logging
from datetime import datetime

from pdf_parser import InvoiceParser

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()
ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    """Check if uploaded file has allowed extension"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def create_error_response(message, status_code=400):
    """Create standardized error response"""
    return jsonify({
        'status': 'error',
        'message': message,
        'timestamp': datetime.now().isoformat()
    }), status_code

def create_success_response(data, message="Success"):
    """Create standardized success response"""
    return jsonify({
        'status': 'success',
        'message': message,
        'data': data,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/v1/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return create_success_response({
        'service': 'PDF Invoice Parser',
        'version': '1.0.0',
        'status': 'healthy'
    })

@app.route('/api/v1/parse', methods=['POST'])
def parse_pdf():
    """
    Parse uploaded PDF invoice
    
    Expects:
    - multipart/form-data with 'file' field containing PDF
    
    Returns:
    - JSON with parsed invoice data
    """
    try:
        # Check if file is present
        if 'file' not in request.files:
            return create_error_response('No file provided')
        
        file = request.files['file']
        
        # Check if file is selected
        if file.filename == '':
            return create_error_response('No file selected')
        
        # Check file extension
        if not allowed_file(file.filename):
            return create_error_response('Invalid file type. Only PDF files are allowed')
        
        # Generate unique filename
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        
        # Save uploaded file
        file.save(file_path)
        logger.info(f"File saved to: {file_path}")
        
        try:
            # Parse the PDF
            parser = InvoiceParser(file_path)
            parsed_data = parser.parse()
            
            # Add parsing metadata
            parsing_info = {
                'original_filename': filename,
                'file_size_bytes': os.path.getsize(file_path),
                'parsed_at': datetime.now().isoformat()
            }
            
            response_data = {
                'parsing_info': parsing_info,
                'invoice_data': parsed_data
            }
            
            logger.info(f"Successfully parsed PDF: {filename}")
            return create_success_response(response_data, "PDF parsed successfully")
            
        except Exception as parsing_error:
            logger.error(f"Error parsing PDF {filename}: {str(parsing_error)}")
            return create_error_response(f"Error parsing PDF: {str(parsing_error)}", 500)
        
        finally:
            # Clean up temporary file
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.info(f"Temporary file deleted: {file_path}")
            except OSError as e:
                logger.warning(f"Could not delete temporary file {file_path}: {e}")
    
    except RequestEntityTooLarge:
        return create_error_response('File too large. Maximum size is 16MB', 413)
    except Exception as e:
        logger.error(f"Unexpected error in parse_pdf: {str(e)}")
        return create_error_response(f"Internal server error: {str(e)}", 500)

@app.route('/api/v1/parse/info', methods=['GET'])
def parse_info():
    """Get information about the parsing service"""
    return create_success_response({
        'supported_formats': ['PDF'],
        'max_file_size_mb': 16,
        'supported_languages': ['Russian'],
        'invoice_types': ['Warehouse invoices', 'Storage charges', 'Reception charges'],
        'extracted_fields': [
            'invoice_info (number, date)',
            'company_info (name, INN)',
            'customer_info (name, INN, address, phone)',
            'line_items (storage, reception, shipment operations)',
            'totals (total_amount, vat_amount, total_items)'
        ]
    })

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return create_error_response('Endpoint not found', 404)

@app.errorhandler(405)
def method_not_allowed(error):
    """Handle 405 errors"""
    return create_error_response('Method not allowed', 405)

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return create_error_response('Internal server error', 500)

if __name__ == '__main__':
    print("🚀 Starting PDF Invoice Parser Web Service")
    print("📚 API Documentation:")
    print("  POST /api/v1/parse        - Upload and parse PDF")
    print("  GET  /api/v1/health       - Health check")
    print("  GET  /api/v1/parse/info   - Service information")
    print("\n🔧 Configuration:")
    print(f"  Max file size: {app.config['MAX_CONTENT_LENGTH'] // (1024*1024)}MB")
    print(f"  Allowed formats: {', '.join(ALLOWED_EXTENSIONS)}")
    print(f"  Temp directory: {app.config['UPLOAD_FOLDER']}")
    print("\n🌐 Starting server on http://localhost:5000")
    
    app.run(host='0.0.0.0', port=5000, debug=True)