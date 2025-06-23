from flask import Blueprint, request, jsonify

reset = Blueprint("reset", __name__)

@reset.route("/reset", methods=["POST"])
def receive_command():
    data = request.get_json()
    print("수신된 데이터:", data)

    if data and data.get("command") == "reset":
        print("reset 수신 완료")
        return jsonify({"status": "success", "message": "reset received"}), 200
    else:
        return jsonify({"status": "error", "message": "invalid command"}), 400
