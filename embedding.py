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

class AssignmentParser:
    """
    Parses assignment into structured sections.

    Output shape:

    {
      "assignment_id": ...,
      "title": "...",
      "sections": [
        {
          "name": "Cloud Storage",
          "scenario": "...",
          "prompts": {
            "containment": [...],
            "post_incident": [...],
            "elevator_pitch": [...]
          }
        },
        ...
      ]
    }
    """

    SECTION_RE = re.compile(
        r"^(Cloud Storage|PII Accident|Social Media|Zero-Day)\s*$",
        re.MULTILINE,
    )

    def __init__(self, assignment_data: Dict[str, Any]):
        self.data = assignment_data

    def parse(self) -> Dict[str, Any]:
        assignment_id = self.data["id"]
        title = self.data.get("title", "").strip()
        content = self.data.get("content", "")

        sections = self._split_into_sections(content)
        parsed_sections: List[Dict[str, Any]] = []

        for name, block in sections:
            parsed_sections.append(self._parse_section(name, block))

        return {
            "assignment_id": assignment_id,
            "title": title,
            "sections": parsed_sections,
        }

    def _split_into_sections(self, content: str) -> List[tuple[str, str]]:
        """
        Split the assignment into blocks per scenario heading.

        Returns list of (section_name, block_text).
        """
        sections: List[tuple[str, str]] = []
        last_name: Optional[str] = None
        last_start: Optional[int] = None

        for match in self.SECTION_RE.finditer(content):
            name = match.group(1)
            if last_name is not None and last_start is not None:
                block = content[last_start:match.start()].strip()
                sections.append((last_name, block))
            last_name = name
            last_start = match.end()

        # tail
        if last_name is not None and last_start is not None:
            block = content[last_start:].strip()
            sections.append((last_name, block))

        return sections

    def _parse_section(self, name: str, block: str) -> Dict[str, Any]:
        """
        For each section block, extract:
          - scenario text
          - containment prompts
          - post-incident prompts
          - elevator pitch prompts
        Tailored to the specific wording of this assignment.
        """
        scenario_label = "Scenario:"
        items_label = "Items to discuss with your group:"

        scenario_text = ""
        discussion_block = ""

        if scenario_label in block:
            s_idx = block.index(scenario_label) + len(scenario_label)
            # try to find the items label after the scenario
            items_idx = block.find(items_label, s_idx)
            if items_idx != -1:
                scenario_text = block[s_idx:items_idx].strip()
                discussion_block = block[items_idx + len(items_label):].strip()
            else:
                scenario_text = block[s_idx:].strip()
                discussion_block = ""
        else:
            # fallback: whole block is "scenario"
            scenario_text = block.strip()
            discussion_block = ""

        containment_text = ""
        post_text = ""
        elevator_text = ""

        if discussion_block:
            cont_label = "Containment"
            post_label = "Post-Incident Activities"
            elevator_label = "Be prepared to discuss in class"

            cont_idx = discussion_block.find(cont_label)
            post_idx = discussion_block.find(post_label)
            elev_idx = discussion_block.find(elevator_label)

            # Assume they appear in this order: Containment -> Post-Incident -> Elevator Pitch
            if cont_idx != -1 and post_idx != -1 and elev_idx != -1:
                containment_text = discussion_block[cont_idx + len(cont_label):post_idx].strip()
                post_text = discussion_block[post_idx + len(post_label):elev_idx].strip()
                elevator_text = discussion_block[elev_idx + len(elevator_label):].strip()
            else:
                # Very crude fallback: everything is containment
                containment_text = discussion_block.strip()

        def _lines_to_list(text: str) -> List[str]:
            return [line.strip() for line in text.splitlines() if line.strip()]

        prompts = {
            "containment": _lines_to_list(containment_text),
            "post_incident": _lines_to_list(post_text),
            "elevator_pitch": _lines_to_list(elevator_text),
        }

        return {
            "name": name,
            "scenario": scenario_text,
            "prompts": prompts,
        }




# Example

if __name__ == "__main__":
    assignment_data = {
      "type": "quiz",
      "id": 155647,
      "title": "Reading Quiz 1",
      "content": "Quiz: Reading Quiz 1\n\nPoints: 5.0\nDue: 2024-09-04T18:00:00Z\n\nQuestions:\n\nQuestion 1:\nOne type of Basic network security defense tool is a:\nPoints: 1.0\n\nAnswer Choices:\n  • Firewall [CORRECT]\n  • Black hat\n  • NotPetya\n  • Canadian\n\nQuestion 2:\nWhich of the following is a main type of network discussed in the text?\nPoints: 1.0\n\nAnswer Choices:\n  • Wide Area Networks (WAN) [CORRECT]\n  • Social Networks\n  • Peering Networks\n  • Aruba Networks\n\n"
    }

    parser = QuizParser(assignment_data)
    structured = parser.parse()

    print(json.dumps(structured, indent=2))

    parser.save("output_quiz_155647.json")
