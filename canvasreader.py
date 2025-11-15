"""
Canvas Reader Class
Extracts a single assignment and returns it as JSON
"""

from canvasapi import Canvas
import re
from html import unescape
import json

class CanvasReader:
    
    course = None
    
    def __init__(self, canvas_url, api_token, course_id):
        """Initialize Canvas Reader with a specific course"""
        print('New Canvas reader')
        
        # Connect to Canvas
        canvas = Canvas(canvas_url, api_token)
        self.course = canvas.get_course(course_id)
        
        print(f'Connected to course: {self.course.name}')
    
    def clean_html(self, html_text):
        """Remove HTML tags and clean up text"""
        if not html_text:
            return ""
        # Remove HTML tags
        text = re.sub('<[^<]+?>', '', html_text)
        # Unescape HTML entities
        text = unescape(text)
        # Clean up whitespace
        text = re.sub(r'\n\s*\n', '\n\n', text)
        return text.strip()
    
    def get_assignment(self, assignment_id):
        """Get a single assignment and return as JSON"""
        try:
            assignment = self.course.get_assignment(assignment_id)
            
            assignment_text = f"Assignment: {assignment.name}\n\n"
            
            # Add metadata
            if hasattr(assignment, 'due_at') and assignment.due_at:
                assignment_text += f"Due: {assignment.due_at}\n"
            if hasattr(assignment, 'points_possible'):
                assignment_text += f"Points: {assignment.points_possible}\n"
            if hasattr(assignment, 'submission_types'):
                assignment_text += f"Submission Types: {', '.join(assignment.submission_types)}\n"
            
            assignment_text += "\n"
            
            # Add description
            if hasattr(assignment, 'description') and assignment.description:
                assignment_text += "Description:\n"
                assignment_text += self.clean_html(assignment.description) + "\n"
            
            return {
                "type": "assignment",
                "id": assignment.id,
                "title": assignment.name,
                "content": assignment_text
            }
        
        except Exception as e:
            print(f"Error fetching assignment: {e}")
            return None
        
    def get_quiz(self, quiz_id):
        """Get a single quiz and return as JSON"""
        try:
            quiz = self.course.get_quiz(quiz_id)
            
            quiz_text = f"Quiz: {quiz.title}\n\n"
            
            # Add description
            if hasattr(quiz, 'description') and quiz.description:
                quiz_text += f"Description: {self.clean_html(quiz.description)}\n\n"
            
            # Add quiz metadata
            if hasattr(quiz, 'points_possible'):
                quiz_text += f"Points: {quiz.points_possible}\n"
            if hasattr(quiz, 'due_at') and quiz.due_at:
                quiz_text += f"Due: {quiz.due_at}\n"
            
            quiz_text += "\n"
            
            # Try to get questions
            try:
                questions = quiz.get_questions()
                quiz_text += "Questions:\n\n"
                
                for i, question in enumerate(questions, 1):
                    quiz_text += f"Question {i}:\n"
                    quiz_text += f"{self.clean_html(question.question_text)}\n"
                    
                    if hasattr(question, 'points_possible'):
                        quiz_text += f"Points: {question.points_possible}\n"
                    
                    # Add answer choices
                    if hasattr(question, 'answers') and question.answers:
                        quiz_text += "\nAnswer Choices:\n"
                        for ans in question.answers:
                            correct = " [CORRECT]" if ans.get('weight', 0) > 0 else ""
                            quiz_text += f"  • {self.clean_html(ans['text'])}{correct}\n"
                    
                    quiz_text += "\n"
            
            except Exception as e:
                quiz_text += f"[Questions not accessible: {e}]\n"
            
            return {
                "type": "quiz",
                "id": quiz.id,
                "title": quiz.title,
                "content": quiz_text
            }
        
        except Exception as e:
            print(f"Error fetching quiz: {e}")
            return None


    def get_all_quizzes(self):
        """Get all quizzes and return as list of JSON objects"""
        quizzes_data = []
        
        try:
            quizzes = self.course.get_quizzes()
            
            for quiz in quizzes:
                
                
                quizzes_data.append({
                    "type": "quiz",
                    "id": quiz.id,
                    "title": quiz.title,
                })
            
            print(f"✓ Found {len(quizzes_data)} quizzes")
        
        except Exception as e:
            print(f"Error fetching quizzes: {e}")
        
        return quizzes_data

