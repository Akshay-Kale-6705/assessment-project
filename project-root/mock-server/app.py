import json
import os
from flask import Flask, jsonify, request, abort

app = Flask(__name__)

# Load customers from JSON file at startup
DATA_FILE = os.path.join(os.path.dirname(__file__), "data", "customers.json")

def load_customers():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

CUSTOMERS = load_customers()


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "service": "mock-server", "total_customers": len(CUSTOMERS)}), 200


@app.route("/api/customers", methods=["GET"])
def get_customers():
    try:
        page = int(request.args.get("page", 1))
        limit = int(request.args.get("limit", 10))
    except ValueError:
        return jsonify({"error": "page and limit must be integers"}), 400

    if page < 1 or limit < 1:
        return jsonify({"error": "page and limit must be positive integers"}), 400

    total = len(CUSTOMERS)
    start = (page - 1) * limit
    end = start + limit
    paginated = CUSTOMERS[start:end]

    return jsonify({
        "data": paginated,
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": (total + limit - 1) // limit
    }), 200


@app.route("/api/customers/<string:customer_id>", methods=["GET"])
def get_customer(customer_id):
    customer = next((c for c in CUSTOMERS if c["customer_id"] == customer_id), None)
    if not customer:
        return jsonify({"error": f"Customer '{customer_id}' not found"}), 404
    return jsonify({"data": customer}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
