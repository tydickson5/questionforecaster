from canvasreader import CanvasReader 


if __name__ == "__main__":
    # Configuration
    CANVAS_URL = 'https://canvas.its.virginia.edu'  # e.g., 'https://canvas.harvard.edu'
    API_TOKEN = '22119~LxPGrtw6eU9F8yKyX8QkrM8GUYKChGk4n4w8rAthr2ke6VJCwnV6uL93NhLNNnNt'  # Get this from Canvas Account Settings
    COURSE_ID = 175906  # Replace with your course ID
    
    # Create reader
    reader = CanvasReader(CANVAS_URL, API_TOKEN, COURSE_ID)
    
    # Get all content and save to JSON
    content = reader.save_to_json('my_course_content.json')
    
    # Or get specific types
    # quizzes = reader.get_all_quizzes()
    # assignments = reader.get_all_assignments()
    # lectures = reader.get_all_lectures()
    
    # Print preview
    print("\n" + "="*60)
    print("PREVIEW OF FIRST ITEM:")
    print("="*60)
    if content['items']:
        first_item = content['items'][0]
        print(f"Type: {first_item['type']}")
        print(f"Title: {first_item['title']}")
        print(f"\nContent Preview (first 300 chars):")
        print(first_item['content'][:300] + "...")