from canvasreader import CanvasReader 
from embedding import QuizParser

import json

if __name__ == "__main__":

    
    # Configuration
    CANVAS_URL = 'https://canvas.its.virginia.edu'  # e.g., 'https://canvas.harvard.edu'
    API_TOKEN = '22119~LxPGrtw6eU9F8yKyX8QkrM8GUYKChGk4n4w8rAthr2ke6VJCwnV6uL93NhLNNnNt'  # Get this from Canvas Account Settings
    COURSE_ID = 175906  # Replace with your course ID
    
    # Get assignment ID from command line argument

    assignment_id = 155647
    
    # Create reader
    reader = CanvasReader(CANVAS_URL, API_TOKEN, COURSE_ID)
    allClasses = reader.get_all_quizzes()
    print(json.dumps(allClasses, indent=2))
    
    
    # Get the assignment
    assignment_data = reader.get_quiz(assignment_id)
    embedder = QuizParser(assignment_data)
    data = embedder.parse()
    #print(json.dumps(data, indent=2))
    
    
else:
    print("Usage: python3 canvas_reader.py <assignment_id>")
    print("Example: python3 canvas_reader.py 67890")