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
# We use a dictionary for O(1) lookup time
indexed_db = {}
is_loading = False

def load_and_index_db():
    global indexed_db, is_loading
    is_loading = True
    print("Starting to fetch and index database...")
    try:
        response = requests.get(DB_URL)
        if response.status_code == 200:
            data = response.json()
            # Indexing by mobile number
            new_index = {}
            for entry in data:
                mobile = entry.get("mobile")
                if mobile:
                    # If multiple entries for same number, we store them in a list
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
