# Production Flask app for deployment
import os
from webapp import app, create_database_if_needed
import assistant_core

# Initialize the app for production
if __name__ == '__main__':
    # Initialize Gemini AI
    if not assistant_core.initialize():
        print("Halting application due to API key initialization failure.")
        exit(1)
    
    # Create database if needed
    create_database_if_needed()
    
    # Run the app
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port) 