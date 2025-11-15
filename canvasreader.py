"""
Canvas Reader Class
Extracts course content and returns it as JSON with quiz/assignment/lecture attributes
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
    
    def get_all_quizzes(self):
        """Extract all quizzes and return as JSON"""
        quizzes_data = []
        
        try:
            quizzes = self.course.get_quizzes()
            
            for quiz in quizzes:
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
                
                quizzes_data.append({
                    "type": "quiz",
                    "id": quiz.id,
                    "title": quiz.title,
                    "content": quiz_text
                })
        
        except Exception as e:
            print(f"Error fetching quizzes: {e}")
        
        return quizzes_data
    
    def get_all_assignments(self):
        """Extract all assignments and return as JSON"""
        assignments_data = []
        
        try:
            assignments = self.course.get_assignments()
            
            for assignment in assignments:
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
                
                assignments_data.append({
                    "type": "assignment",
                    "id": assignment.id,
                    "title": assignment.name,
                    "content": assignment_text
                })
        
        except Exception as e:
            print(f"Error fetching assignments: {e}")
        
        return assignments_data
    
    def get_all_lectures(self):
        """Extract all lecture content (pages and modules) and return as JSON"""
        lectures_data = []
        
        try:
            # Get pages (often used for lecture notes)
            pages = self.course.get_pages()
            
            for page in pages:
                try:
                    # Get full page content
                    full_page = self.course.get_page(page.url)
                    
                    lecture_text = f"Lecture: {full_page.title}\n\n"
                    
                    if hasattr(full_page, 'body') and full_page.body:
                        lecture_text += self.clean_html(full_page.body)
                    
                    lectures_data.append({
                        "type": "lecture",
                        "id": page.page_id,
                        "title": full_page.title,
                        "content": lecture_text
                    })
                
                except Exception as e:
                    print(f"Error fetching page {page.title}: {e}")
            
            # Get modules (structured lecture content)
            modules = self.course.get_modules()
            
            for module in modules:
                try:
                    items = module.get_module_items()
                    
                    for item in items:
                        item_text = f"Module: {module.name} - {item.title}\n\n"
                        
                        # Handle different item types
                        if item.type == 'Page':
                            try:
                                page = self.course.get_page(item.page_url)
                                if hasattr(page, 'body') and page.body:
                                    item_text += self.clean_html(page.body)
                                
                                lectures_data.append({
                                    "type": "lecture",
                                    "id": f"module_{module.id}_{item.id}",
                                    "title": f"{module.name} - {item.title}",
                                    "content": item_text
                                })
                            except:
                                pass
                        
                        elif item.type == 'ExternalUrl':
                            if hasattr(item, 'external_url'):
                                item_text += f"External URL: {item.external_url}\n"
                                lectures_data.append({
                                    "type": "lecture",
                                    "id": f"module_{module.id}_{item.id}",
                                    "title": f"{module.name} - {item.title}",
                                    "content": item_text
                                })
                
                except Exception as e:
                    print(f"Error fetching module items for {module.name}: {e}")
        
        except Exception as e:
            print(f"Error fetching lectures: {e}")
        
        return lectures_data
    
    def get_all_content(self):
        """Get all course content (quizzes, assignments, lectures) as JSON"""
        print("Extracting all course content...")
        
        all_content = {
            "course_name": self.course.name,
            "course_id": self.course.id,
            "items": []
        }
        
        # Get all quizzes
        print("  Fetching quizzes...")
        quizzes = self.get_all_quizzes()
        all_content["items"].extend(quizzes)
        print(f"    ✓ Found {len(quizzes)} quizzes")
        
        # Get all assignments
        print("  Fetching assignments...")
        assignments = self.get_all_assignments()
        all_content["items"].extend(assignments)
        print(f"    ✓ Found {len(assignments)} assignments")
        
        # Get all lectures
        print("  Fetching lectures...")
        lectures = self.get_all_lectures()
        all_content["items"].extend(lectures)
        print(f"    ✓ Found {len(lectures)} lecture items")
        
        print(f"\n✓ Total items extracted: {len(all_content['items'])}")
        
        return all_content
    
    def save_to_json(self, filename='canvas_content.json'):
        """Extract all content and save to JSON file"""
        content = self.get_all_content()
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(content, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Content saved to {filename}")
        return content