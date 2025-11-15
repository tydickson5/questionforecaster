from flask import Flask, request, jsonify
from flask_cors import CORS
from canvasreader import CanvasReader 
from embedding import QuizParser

import json

CANVAS_URL = 'https://canvas.its.virginia.edu'  # e.g., 'https://canvas.harvard.edu'
API_TOKEN = '22119~LxPGrtw6eU9F8yKyX8QkrM8GUYKChGk4n4w8rAthr2ke6VJCwnV6uL93NhLNNnNt'  # Get this from Canvas Account Settings
COURSE_ID = 175906  # Replace with your course ID

app = Flask(__name__)
CORS(app)   # Allows requests from your HTML/JS frontend

@app.route("/forecast", methods=["POST"])
def forecast():
    data = request.get_json()
    item_title = data.get("title", "")
    item_thing = data.get("assignment", 0)

    assignment_id = 155647
    
    # Create reader
    reader = CanvasReader(CANVAS_URL, API_TOKEN, COURSE_ID)
    
    
    
    # Get the assignment
    
    #print(json.dumps(data, indent=2))

    # Example: sections generated for the frontend
    if(item_title == "All"):
        #return all items
        allClasses = reader.get_all_quizzes()
        return jsonify({"sections": allClasses})

        #print(json.dumps(allClasses, indent=2))

    else:
        #return item by id
        assignment_data = reader.get_quiz(assignment_id)
        embedder = QuizParser(assignment_data)
        data = embedder.parse()


    

    
if __name__ == "__main__":
    app.run(debug=True)



