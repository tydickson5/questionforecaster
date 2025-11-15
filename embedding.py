import re
import json
from typing import Dict, Any, List, Optional


class QuizParser:
    """
    Parses a Canvas quiz item into a structured JSON object:
    {
      "quiz_id": ...,
      "title": ...,
      "meta": {...},
      "questions": [...]
    }
    """

    QUESTION_SPLIT_RE = re.compile(r"Question\s+(\d+):")

    def __init__(self, assignment_data: Dict[str, Any]):
        """
        assignment_data is the JSON dict you receive from your teammate, e.g.:

        {
          "type": "quiz",
          "id": 155647,
          "title": "Reading Quiz 1",
          "content": "..."
        }
        """
        self.data = assignment_data

    # ---------- PUBLIC INTERFACE ----------

    def parse(self) -> Dict[str, Any]:
        """
        Parse the quiz into a structured JSON-ready dict.
        """
        quiz_id = self.data["id"]
        title = self.data.get("title", "").strip()
        content = self.data.get("content", "")

        header, body = self._split_header_and_body(content)
        questions = self._parse_questions(body)

        return {
            "quiz_id": quiz_id,
            "title": title,
            "meta": {
                "raw_header": header.strip()
            },
            "questions": questions,
        }

    def save(self, path: str) -> None:
        """
        Save output of parse() to a .json file.
        """
        structured = self.parse()
        with open(path, "w") as f:
            json.dump(structured, f, indent=2)
        print(f"[QuizParser] Saved structured quiz JSON to: {path}")

    # ---------- INTERNAL HELPERS ----------

    def _split_header_and_body(self, content: str) -> tuple[str, str]:
        marker = "Questions:"
        if marker in content:
            before, after = content.split(marker, 1)
            body = after.lstrip("\n")
            return before, body
        return "", content

    def _parse_questions(self, body: str) -> List[Dict[str, Any]]:
        parts = self.QUESTION_SPLIT_RE.split(body)

        if len(parts) <= 1:
            return []

        questions: List[Dict[str, Any]] = []

        # parts = ["", "1", "<block1>", "2", "<block2>", ...]
        for i in range(1, len(parts), 2):
            q_index = int(parts[i])
            block = parts[i + 1]

            question_text, points, choices = self._parse_question_block(block)

            questions.append(
                {
                    "index": q_index,
                    "question": question_text,
                    "points": points,
                    "choices": choices,
                }
            )

        return questions

    def _parse_question_block(self, block: str) -> tuple[str, Optional[float], List[Dict[str, Any]]]:
        lines = [l.strip() for l in block.splitlines()]

        # strip blank top/bottom
        while lines and not lines[0]:
            lines.pop(0)
        while lines and not lines[-1]:
            lines.pop()

        # find Points:
        points_val = None
        points_idx = None
        for idx, line in enumerate(lines):
            if line.startswith("Points:"):
                points_idx = idx
                try:
                    payload = line.split("Points:", 1)[1].strip()
                    points_val = float(payload.split()[0])
                except:
                    points_val = None
                break

        # question text before Points:
        if points_idx is not None:
            q_lines = [l for l in lines[:points_idx] if l]
            rest = lines[points_idx + 1:]
        else:
            q_lines = [l for l in lines if l]
            rest = []

        question_text = " ".join(q_lines).strip()

        # Parse choices
        choices: List[Dict[str, Any]] = []
        if rest:
            ac_idx = None
            for idx, line in enumerate(rest):
                if line.startswith("Answer Choices:"):
                    ac_idx = idx
                    break

            if ac_idx is not None:
                choice_lines = [l for l in rest[ac_idx + 1:] if l]
                for cl in choice_lines:
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


