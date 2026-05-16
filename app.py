from flask import Flask, jsonify, request
import requests
import json
import os
from threading import Thread
import time

app = Flask(__name__)

# Configuration
DB_URL = "https://github.com/zaylix/nepali-number-info-api/raw/refs/heads/master/database.json"
API_KEY = "diwazz"

# Global variable to store the indexed database
indexed_db = {}
is_loading = False

def validate_nepali_number(number: str):
    """Validates if the number is a valid 10-digit Nepali mobile number."""
    if not number.isdigit() or len(number) != 10:
        return False
    
    prefix = number[:3]
    # Common Nepali prefixes: NTC (984, 985, 986, 974, 975, 976, 972), Ncell (980, 981, 982), Smart (961, 962, 988)
    valid_prefixes = ["984", "985", "986", "974", "975", "976", "972", "980", "981", "982", "961", "962", "988"]
    return prefix in valid_prefixes

def load_and_index_db():
    global indexed_db, is_loading
    is_loading = True
    print("Starting to fetch and index database...")
    try:
        response = requests.get(DB_URL)
        if response.status_code == 200:
            data = response.json()
            new_index = {}
            for entry in data:
                mobile = entry.get("mobile")
                if mobile:
                    if mobile not in new_index:
                        new_index[mobile] = []
                    new_index[mobile].append(entry)
            
            indexed_db = new_index
            print(f"Database indexed successfully. Total unique numbers: {len(indexed_db)}")
        else:
            print(f"Failed to fetch database. Status code: {response.status_code}")
    except Exception as e:
        print(f"Error during indexing: {e}")
    finally:
        is_loading = False

# Load database in a background thread on startup
Thread(target=load_and_index_db).start()

@app.route('/')
def home():
    status = "Loading..." if is_loading else "Ready"
    return jsonify({
        "message": "Nepali Info API is running",
        "db_status": status,
        "total_numbers": len(indexed_db)
    })

@app.route('/api/key=<key>/num=<number>')
def get_info(key, number):
    if key != API_KEY:
        return jsonify({"success": False, "message": "Invalid API Key"}), 403
    
    # Validate Nepali Number
    if not validate_nepali_number(number):
        return jsonify({
            "success": False, 
            "message": "Invalid Only Number for Nepali",
            "number": number
        }), 400
    
    if is_loading and not indexed_db:
        return jsonify({"success": False, "message": "Database is still loading, please try again in a few seconds"}), 503

    # Search in the indexed dictionary
    results = indexed_db.get(number)
    
    if results:
        return jsonify({
            "success": True,
            "data": results,
            "count": len(results)
        })
    else:
        return jsonify({
            "success": False,
            "message": "Number not found in database",
            "number": number
        }), 404

@app.route('/refresh')
def refresh():
    if not is_loading:
        Thread(target=load_and_index_db).start()
        return jsonify({"message": "Refresh started in background"})
    return jsonify({"message": "Refresh already in progress"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
