"""
Production-ready Flask application runner
Runs on 0.0.0.0:5000 with proper cache control headers
"""

import os
from app import app

if __name__ == '__main__':
    # Disable caching for development (important for Replit iframe)
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
    
    # Add cache control headers
    @app.after_request
    def add_header(response):
        """Add headers to prevent caching"""
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '-1'
        return response
    
    # Run on 0.0.0.0:5000 as required for Replit
    app.run(host='0.0.0.0', port=5000, debug=False)
