from flask import Flask, jsonify
import json
import os

app = Flask(__name__)
API_KEY = "diwazz"
indexed_db = {}

# Server start hote hi local file load kar lega
print("Loading local database.json...")
try:
    with open('database.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        for entry in data:
            mobile = entry.get("mobile")
            if mobile:
                if mobile not in indexed_db:
                    indexed_db[mobile] = []
                indexed_db[mobile].append(entry)
    print(f"Database loaded! Total numbers: {len(indexed_db)}")
except Exception as e:
    print(f"Error loading database: {e}")

def validate_nepali_number(number: str):
    if not number.isdigit() or len(number) != 10:
        return False
    valid_prefixes = ["984", "985", "986", "974", "975", "976", "972", "980", "981", "982", "961", "962", "988"]
    return number[:3] in valid_prefixes

@app.route('/')
def home():
    return jsonify({
        "message": "Nepali Info API is running",
        "total_numbers": len(indexed_db)
    })

@app.route('/api/key=<key>/num=<number>')
def get_info(key, number):
    if key != API_KEY:
        return jsonify({"success": False, "message": "Invalid API Key"}), 403
    
    if not validate_nepali_number(number):
        return jsonify({"success": False, "message": "Invalid Only Number for Nepali", "number": number}), 400

    results = indexed_db.get(number)
    if results:
        return jsonify({"success": True, "data": results, "count": len(results)})
    else:
        return jsonify({"success": False, "message": "Number not found in database", "number": number}), 404

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
