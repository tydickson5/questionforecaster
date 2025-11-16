import json
import google.generativeai as genai

# Load Gemini model
genai.configure(api_key="AIzaSyC53fGc1AUpt8zHbXJrBI-87z2hw_OwW_U")
model = genai.GenerativeModel("gemini-2.5-flash")  

# =============================
# PROMPT
# =============================

PROMPT_TEMPLATE = """
You are generating an FAQ sheet for students based on the assignment or quiz content provided below. 
You should output a minimum of 5 FAQ questions and a maximum of 10 FAQ questions TOTAL for the whole assignment.
The goal is to anticipate the most common questions students are likely to ask about the material so that the instructor can release this FAQ and reduce confusion and repetitive student emails.

Your tasks:
1. Evaluate how challenging the material is for students INTERNALLY.
2. If the material is NOT challenging, give EITHER:
    - A likely student question showing misunderstanding, OR
    - A clarification that the professor could make to help students.
3. If the material IS challenging:
    - Identify 1-2 likely questions that a STUDENT would have about the content
    - Questions should reflect misunderstandings or confusions students might have.
    - Provide a clear, editable instructor-facing answer for each question.
4. Questions should focus on common points of confusion, interpretation issues, or deeper understanding—not trivial questions.
5. Provide clear, concise, student-friendly answers written in the instructor’s voice.
6. DO NOT mention difficulty or risk in the output.
7. DO NOT explain or justify your choices in the output.

Return STRICT JSON in the following format:

{
  "faq": [
    {
      "question": "string",
      "answer": "string"
    }
  ]
}

TEXT TO ANALYZE:
{TEXT}
"""

# =============================
# MAIN ENTRYPOINT
# =============================

def analyze_all_chunks(chunks):
    result_list = []
    for chunk in chunks:
        res = analyze_chunk(chunk)
        if res:  # ignore low-risk chunks
            result_list.append(res)

    final_output = {"results": result_list}

    print("\n===== FINAL OUTPUT =====\n")
    print(json.dumps(final_output, indent=2))

    with open("analysis_output.json", "w") as f:
        json.dump(final_output, f, indent=2)

    print("\nSaved analysis to: analysis_output.json\n")

    return final_output

# =============================
# SINGLE CHUNK ANALYSIS
# =============================

def analyze_chunk(chunk):
    text_to_analyze, section_title, chunk_id = normalize_chunk(chunk)

    print(f"\n=== Analyzing chunk {chunk_id}: {section_title} ===")

    prompt = PROMPT_TEMPLATE.replace("{TEXT}", text_to_analyze)

    response = model.generate_content(prompt)
    raw_output = response.text.strip()

    print("\n--- RAW GEMINI OUTPUT ---")
    print(raw_output)

    parsed = safe_parse_json(raw_output)

    print("\n--- PARSED JSON ---")
    print(json.dumps(parsed, indent=2))

    faq = parsed.get("faq", [])

    # If no FAQ returned, skip this section entirely
    if not faq:
        print(f"Chunk {chunk_id} skipped (not challenging).")
        return None

    # Only return FAQ sections
    return {
        "section_title": section_title,
        "faq": faq
    }

# =============================
# HELPERS
# =============================

def normalize_chunk(chunk):

    if "chunk_id" in chunk and "text" in chunk:
        return (
            chunk["text"],
            chunk.get("section_title", f"Chunk {chunk['chunk_id']}"),
            chunk["chunk_id"]
        )

    if "index" in chunk and "question" in chunk:
        section_title = f"Quiz Question {chunk['index']}"
        base_text = f"Question: {chunk['question']}"

        if "choices" in chunk:
            base_text += "\n\nAnswer Choices:\n"
            base_text += "\n".join(f"- {c['text']}" for c in chunk["choices"])

        return base_text, section_title, chunk["index"]

    return str(chunk), "Unknown", -1


def safe_parse_json(raw):
    try:
        return json.loads(raw)
    except:
        start = raw.find("{")
        end = raw.rfind("}") + 1
        cleaned = raw[start:end]
        return json.loads(cleaned)

# =============================
# RUN ANALYSIS (ENTRYPOINT)
# =============================
if __name__ == "__main__":
    test_chunks = [
        {
            "chunk_id": 1,
            "section_title": "Wireless Networks",
            "text": "Wireless networks transmit data using radio waves and require authentication protocols."
        }
    ]

    analyze_all_chunks(test_chunks)
