from flask import Flask, request, jsonify
import importlib.util
import os
from concurrent.futures import ThreadPoolExecutor

# ── استيراد الأداة ────────────────────────────
SCRIPT_NAME = "tool"

spec = importlib.util.spec_from_file_location(
    SCRIPT_NAME,
    os.path.join(os.path.dirname(os.path.abspath(__file__)), f"{SCRIPT_NAME}.py")
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

DEV_NAME = "https://t.me/afuonaz"

# ── 8 عمال متوازيين + طابور ──────────────────────
executor = ThreadPoolExecutor(max_workers=5)

app = Flask(__name__)


@app.route("/charge", methods=["POST"])
def charge():
    try:
        data = request.get_json(silent=True) or {}
        card = data.get("card", "").strip()
        proxy = data.get("proxy") or None

        if not card:
            return jsonify({
                "developer": DEV_NAME,
                "error": "Missing 'card' field"
            }), 400

        if len(card.split("|")) != 4:
            return jsonify({
                "developer": DEV_NAME,
                "error": "Card format must be PAN|MM|YY|CVV"
            }), 400

        # ← الطلب بيتحط في الطابور + بيتنفذ لما worker يفضى
        future = executor.submit(module.run, card, proxy)
        result = future.result(timeout=120)  # أقصى وقت انتظار = دقيقتين

        return jsonify({
            "developer": DEV_NAME,
            "status": result.get("Status", "Unknown"),
            "response": result.get("Response", "")
        }), 200

    except Exception as e:
        return jsonify({
            "developer": DEV_NAME,
            "error": str(e)
        }), 500


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "developer": DEV_NAME,
        "status": "ok",
        "workers": 5,
        "active": executor._work_queue.qsize() if hasattr(executor, "_work_queue") else 0
    }), 200


if __name__ == "__main__":
    print(f"[*] API started — Dev: {DEV_NAME}")
    print(f"[*] Workers: 8 (queue for the rest)")
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)