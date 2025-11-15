from flask import Flask, request, jsonify
from flask_cors import CORS
from canvasreader import CanvasReader 
from embedding import QuizParser, AssignmentParser
import LLM

import json

CANVAS_URL = 'https://canvas.its.virginia.edu'  # e.g., 'https://canvas.harvard.edu'
API_TOKEN = '22119~LxPGrtw6eU9F8yKyX8QkrM8GUYKChGk4n4w8rAthr2ke6VJCwnV6uL93NhLNNnNt'  # Get this from Canvas Account Settings
COURSE_ID = 175906  # Replace with your course ID

app = Flask(__name__)
CORS(app)

@app.route("/forecast", methods=["POST"])
def forecast():
    data = request.get_json()
    item_title = data.get("title", "")
    item_thing = data.get("assignment", 0)

    assignment_id = 155647
    
    # Create reader
    #reader = CanvasReader(CANVAS_URL, API_TOKEN, COURSE_ID)
    
    
    
    # Get the assignment
    
    #print(json.dumps(data, indent=2))

    # Example: sections generated for the frontend
    if(item_title == "All"):
        #return all items
        
        
        #quiz_data = reader.get_quiz(155647)           # list of quizzes
        #assignment_data = reader.get_assignment(790869) # list of assignments

        # Option 1: flat list with type tags
        all_classes = []




        all_classes.append(assignment_data)

        # Return combined JSON
        return jsonify({"sections": all_classes})

        #print(json.dumps(allClasses, indent=2))

    else:
        #return item by id
        if(item_title == "quiz"):
            assignment_data = reader.get_quiz(assignment_id)
            parser = QuizParser(assignment_data)
            data = parser.parse()
            return jsonify({"sections": data})
        else:

            file_path = 'assignment.json' 

            with open(file_path, 'r') as file:
                # Load the JSON data from the file into a Python variable
                # The json.load() function directly reads from the file object
                data_variable = json.load(file)

            #print(json.dumps(data_variable, indent=2))
            
            
            # Get the assignment
            #assignment_data = reader.get_assignment(790869)
            #print(json.dumps(assignment_data, indent=2))
            embedder = AssignmentParser(data_variable)
            data = embedder.parse()
            #print(json.dumps(data, indent=2))
            data = LLM.analyze_all_chunks(data["scenarios"])
            #print(json.dumps(data, indent=2))

            #assignment_data = reader.get_assignment(assignment_id)
            #parser = AssigmentParser(assignment_data)
            #data = parser.parse()
            return jsonify({"sections": data})

        #nelsons thing



        


    

    
if __name__ == "__main__":
    app.run(debug=True)



