
from flask import Flask, jsonify , request
from flask_cors import CORS

from tls_simulator import TLSHandshakeSimulator


app = Flask(__name__)

# Allow requests from the future React frontend.
CORS(
    app,
    resources={
        r"/api/*": {
            "origins": ["http://localhost:5173"]
        }
    }
)

simulator = TLSHandshakeSimulator()


@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "project": "CryptLink",
        "description": "TLS Handshake Simulation API",
        "status": "running"
    })


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy",
        "service": "CryptLink Backend"
    })


@app.route("/api/handshake/start", methods=["POST"])
def start_handshake():
    data = request.get_json(silent=True) or {}
    simulate_failure = data.get("simulate_failure")

    if simulate_failure not in (None, "tampered_signature"):
        return jsonify({
            "status": "INVALID_REQUEST",
            "message": "Unsupported failure simulation"
        }), 400

    try:
        result = simulator.run(
            simulate_failure=simulate_failure
        )
        return jsonify(result), 200

    except Exception:
        app.logger.exception("Handshake simulation failed")
        return jsonify({
            "status": "FAILED",
            "message": "Unexpected simulation error"
        }), 500

@app.route("/api/handshake/status", methods=["GET"])
def handshake_status():
    return jsonify(simulator.get_result()), 200


@app.route("/api/handshake/reset", methods=["POST"])
def reset_handshake():
    simulator.events = []
    simulator.status = "NOT_STARTED"

    return jsonify({
        "status": "NOT_STARTED",
        "message": "CryptLink simulation reset successfully"
    }), 200


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )
