import logging
from flask import Flask, jsonify, request
from flask_cors import CORS
from query_service import QueryService
from logging_config import setup_logging

app = Flask(__name__)
CORS(app)

setup_logging()

@app.route("/ask", methods=["POST"])
def ask():
    data = request.json
    user_query = data.get("query")
    sql_in_answer = data.get("sql_in_answer", False)
    sql_mode = data.get("sql_mode", False)

    if not user_query:
        logging.error("No query provided")
        return jsonify({"error": "No query provided"}), 400

    query_service = QueryService()
    response = query_service.process_query(user_query, sql_in_answer, sql_mode)
    logging.info(f"Query processed: {user_query}")

    if response["Error"]:
        if "Only SELECT queries are allowed" in response["Error"] or \
           "Only language text is allowed" in response["Error"]:
            return jsonify({"error": response["Error"]}), 400
        else:
            return jsonify({"error": response["Error"]}), 500
    return jsonify(response["Data"]), 200

if __name__ == "__main__":
    # DEV
    # app.run(debug=True, port=5000)
    app.run(host='0.0.0.0', port=5000, debug=True)
