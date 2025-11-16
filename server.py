from flask import Flask, request, jsonify
from flask_cors import CORS
from embedding import AssignmentParser, QuizParser
import LLM
import json

app = Flask(__name__)
CORS(app)

@app.route("/forecast", methods=["POST"])
def forecast():
    data = request.get_json()
    item_title = data.get("title", "")
    assignment_id = data.get("assignment", 0)

    file_path = "assignment.json"
    other = "quiz.json"

    if item_title == "All":
        with open(file_path, 'r') as f:
            a = json.load(f)


        with open(other, 'r') as f:
            other = json.load(f)

        

        # Return as a list of items for frontend
        return jsonify({"sections": [a]})

    elif item_title == "quiz":
        # Quiz handling not implemented
        with open(other, 'r') as f:
            assignment_data = json.load(f)
        parser = QuizParser(assignment_data)
        parsed = parser.parse()
        analyzed = LLM.analyze_all_chunks(parsed.get("scenarios", []))
        return jsonify({"sections": analyzed})

    elif item_title == "assignment":
        with open(file_path, 'r') as f:
            assignment_data = json.load(f)

        parser = AssignmentParser(assignment_data)
        parsed = parser.parse()  # Expect {"scenarios": [...]}
        analyzed = LLM.analyze_all_chunks(parsed.get("scenarios", []))

        return jsonify({"sections": analyzed})

    else:
        return jsonify({"sections": ["Error: Unknown type"]})

if __name__ == "__main__":
    app.run(debug=True)
