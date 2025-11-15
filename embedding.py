import re
from typing import Dict, Any, List, Optional

QUESTION_SPLIT_RE = re.compile(r"Question\s+(\d+):")


def parse_quiz_item(item: Dict[str, Any]) -> Dict[str, Any]:
    """
    item looks like:
    {
      "type": "quiz",
      "id": 155647,
      "title": "Reading Quiz 1",
      "content": "Quiz: Reading Quiz 1\n\nPoints: ...\n\nQuestions:\n\nQuestion 1: ..."
    }
    Returns a structured dict suitable for Nelson's AI pipeline.
    """
    quiz_id = item["id"]
    title = item.get("title", "").strip()
    content = item.get("content", "")

    # Split header vs questions
    header, body = _split_header_and_body(content)

    questions = _parse_questions(body)

    return {
        "quiz_id": quiz_id,
        "title": title,
        "meta": {
            "raw_header": header.strip(),
        },
        "questions": questions,
    }


def _split_header_and_body(content: str) -> tuple[str, str]:
    """
    Split on the 'Questions:' marker.
    Everything before is header/meta; everything after is question text.
    """
    marker = "Questions:"
    if marker in content:
        before, after = content.split(marker, 1)
        # body starts after 'Questions:\n\n'
        body = after.lstrip("\n")
        return before, body
    else:
        # fallback if somehow missing
        return "", content


def _parse_questions(body: str) -> List[Dict[str, Any]]:
    """
    body starts at 'Question 1:\n...'
    Use regex to split into blocks and parse each block.
    """
    parts = QUESTION_SPLIT_RE.split(body)
    # parts = ["", "1", "<block1>", "2", "<block2>", ...]
    if len(parts) <= 1:
        return []

    questions: List[Dict[str, Any]] = []

    # skip parts[0] (text before first 'Question N:')
    for i in range(1, len(parts), 2):
        q_index_str = parts[i]
        block = parts[i + 1]
        q_index = int(q_index_str)

        question_text, points, choices = _parse_question_block(block)

        questions.append(
            {
                "index": q_index,
                "question": question_text,
                "points": points,
                "choices": choices,
            }
        )

    return questions


def _parse_question_block(block: str) -> tuple[str, Optional[float], List[Dict[str, Any]]]:
    """
    One block looks like:

    "\\nOne type of ... is a:\\nPoints: 1.0\\n\\nAnswer Choices:\\n  • Firewall [CORRECT]\\n  • Black hat..."

    We want: question text, points (float or None), list of {text, is_correct}.
    """
    lines = [l.strip() for l in block.splitlines()]

    # strip leading / trailing empty lines
    while lines and not lines[0]:
        lines.pop(0)
    while lines and not lines[-1]:
        lines.pop()

    # find points line
    points_idx = None
    points_val: Optional[float] = None
    for idx, line in enumerate(lines):
        if line.startswith("Points:"):
            points_idx = idx
            # try to parse "Points: 1.0"
            try:
                parts = line.split("Points:", 1)[1].strip()
                points_val = float(parts.split()[0])
            except Exception:
                points_val = None
            break

    # question text is everything before the Points line
    if points_idx is not None:
        q_lines = [l for l in lines[:points_idx] if l]
        rest = lines[points_idx + 1 :]
    else:
        q_lines = [l for l in lines if l]
        rest = []

    question_text = " ".join(q_lines).strip()

    # find "Answer Choices:" in rest
    choices: List[Dict[str, Any]] = []
    if rest:
        ac_idx = None
        for idx, line in enumerate(rest):
            if line.startswith("Answer Choices:"):
                ac_idx = idx
                break

        if ac_idx is not None:
            choice_lines = [l for l in rest[ac_idx + 1 :] if l]
            for cl in choice_lines:
                # remove bullet characters and whitespace
                cleaned = cl.lstrip("•").lstrip("-").strip()
                is_correct = "[CORRECT]" in cleaned
                cleaned = cleaned.replace("[CORRECT]", "").strip()
                if cleaned:
                    choices.append(
                        {
                            "text": cleaned,
                            "is_correct": is_correct,
                        }
                    )

    return question_text, points_val, choices


# Example usage:
# Small CLI / test helper
if __name__ == "__main__":
    # quick manual test with your example
    example_item = {
  "type": "quiz",
  "id": 155647,
  "title": "Reading Quiz 1",
  "content": "Quiz: Reading Quiz 1\n\nPoints: 5.0\nDue: 2024-09-04T18:00:00Z\n\nQuestions:\n\nQuestion 1:\nOne type of Basic network security defense tool is a:\nPoints: 1.0\n\nAnswer Choices:\n  \u2022 Firewall [CORRECT]\n  \u2022 Black hat\n  \u2022 NotPetya\n  \u2022 Canadian\n\nQuestion 2:\nWhich of the following is a main type of network discussed in the text?\nPoints: 1.0\n\nAnswer Choices:\n  \u2022 Wide Area Networks (WAN) [CORRECT]\n  \u2022 Social Networks\n  \u2022 Peering Networks\n  \u2022 Aruba Networks\n\nQuestion 3:\nWhat common protocol used to transmit most network traffic on earth\u00a0was a section of the assigned chapter?\nPoints: 1.0\n\nAnswer Choices:\n  \u2022 TCP/IP [CORRECT]\n  \u2022 Appletalk\n  \u2022 Valve\n  \u2022 DMARK\n\nQuestion 4:\nThe assigned chapter included a section on wireless networks,\u00a0used to transmit data using radio waves.\nPoints: 1.0\n\nAnswer Choices:\n  \u2022 True [CORRECT]\n  \u2022 False\n\nQuestion 5:\nThe OSI in OSI model\u00a0stands for Optional Sidecar Insertion.\nPoints: 1.0\n\nAnswer Choices:\n  \u2022 True\n  \u2022 False [CORRECT]\n\n"
}

    structured = parse_quiz_item(example_item)
    import json

    print(json.dumps(structured, indent=2))

    # Save the structured data to a JSON file
    with open("output.json", "w") as f:
        json.dump(structured, f, indent=2)