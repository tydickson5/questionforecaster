import json
import google.generativeai as genai

# Load Gemini model
genai.configure(api_key="AIzaSyC53fGc1AUpt8zHbXJrBI-87z2hw_OwW_U")
model = genai.GenerativeModel("gemini-2.5-flash")  

# =============================
# PROMPT
# =============================

PROMPT_TEMPLATE = """
You are analyzing educational course material and producing an instructor-facing FAQ.

Your tasks:
1. Evaluate the text and assign a difficulty score from 1 to 5.
2. If the difficulty is 3 or higher (moderate → advanced):
     • Identify 3–6 student questions that students are likely to ask.
     • Questions should reflect intermediate and advanced misunderstandings ONLY.
     • For each question, provide a clear, editable answer for the instructor.
3. If difficulty is below 3:
     • Return an empty FAQ list.
4. DO NOT mention difficulty in the FAQ or inside answers.

Return STRICT JSON:

{
  "difficulty": number,
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
    results = [analyze_chunk(chunk) for chunk in chunks]

    final_output = {"results": results}

    # ------------------------------
    # PRINT TO TERMINAL (PRETTY)
    # ------------------------------
    print("\n===== FINAL OUTPUT (PRINTED TO TERMINAL) =====\n")
    print(json.dumps(final_output, indent=2))

    # ------------------------------
    # SAVE TO JSON FILE
    # ------------------------------
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

    difficulty = parsed.get("difficulty", 3)
    risky = difficulty >= 3

    if not risky:
        return {
            "chunk_id": chunk_id,
            "section_title": section_title,
            "risky": False,
            "difficulty": difficulty,
            "faq": []
        }

    return {
        "chunk_id": chunk_id,
        "section_title": section_title,
        "risky": True,
        "difficulty": difficulty,
        "faq": parsed.get("faq", [])
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
