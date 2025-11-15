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
    Parses a Canvas assignment like the incident scenarios into:

    {
      "assignment_id": ...,
      "title": ...,
      "meta": {
        "raw_header": "...",
        "points": 100.0,
        "submission_types": ["online_upload"]
      },
      "scenarios": [
        {
          "name": "Cloud Storage",
          "scenario": "...",
          "containment": "...",
          "post_incident_activities": "...",
          "elevator_pitch": "..."
        },
        ...
      ]
    }
    """

    # e.g. "Cloud StorageScenario:", "PII AccidentScenario:", etc.
    SCENARIO_SPLIT_RE = re.compile(r"([A-Za-z0-9 \-]+)Scenario:")

    def __init__(self, assignment_data: Dict[str, Any]):
        self.data = assignment_data

    # ---------- PUBLIC INTERFACE ----------

    def parse(self) -> Dict[str, Any]:
        assignment_id = self.data["id"]
        title = self.data.get("title", "").strip()
        content = self.data.get("content", "")

        header, body = self._split_header_and_body(content)
        meta = self._parse_header(header)
        scenarios = self._parse_scenarios(body)

        return {
            "assignment_id": assignment_id,
            "title": title,
            "meta": meta,
            "scenarios": scenarios,
        }

    def save(self, path: str) -> None:
        structured = self.parse()
        with open(path, "w") as f:
            json.dump(structured, f, indent=2)
        print(f"[AssignmentParser] Saved structured assignment JSON to: {path}")

    # ---------- INTERNAL HELPERS ----------

    def _split_header_and_body(self, content: str) -> tuple[str, str]:
        """
        Everything before 'Description:' is header; everything after is body.
        """
        marker = "Description:"
        if marker in content:
            before, after = content.split(marker, 1)
            return before.strip(), after.lstrip("\n")
        return "", content

    def _parse_header(self, header: str) -> Dict[str, Any]:
        points: Optional[float] = None
        submission_types: List[str] = []

        for line in header.splitlines():
            line = line.strip()
            if line.startswith("Points:"):
                try:
                    payload = line.split("Points:", 1)[1].strip()
                    points = float(payload.split()[0])
                except Exception:
                    points = None
            elif line.startswith("Submission Types:"):
                payload = line.split("Submission Types:", 1)[1].strip()
                if payload:
                    submission_types = [t.strip() for t in payload.split(",") if t.strip()]

        return {
            "raw_header": header,
            "points": points,
            "submission_types": submission_types,
        }

    def _parse_scenarios(self, body: str) -> List[Dict[str, Any]]:
        """
        Split the body into scenarios using the 'XScenario:' pattern.
        """
        parts = self.SCENARIO_SPLIT_RE.split(body)

        # parts = ["<intro?>", "Cloud Storage", "<block1>", "PII Accident", "<block2>", ...]
        if len(parts) <= 1:
            return []

        scenarios: List[Dict[str, Any]] = []

        for i in range(1, len(parts), 2):
            name = parts[i].strip()
            block = parts[i + 1]
            scenarios.append(self._parse_scenario_block(name, block))

        return scenarios

    def _parse_scenario_block(self, name: str, block: str) -> Dict[str, Any]:
        text = block.strip()

        # 1. Scenario text vs discussion+elevator
        discussion_marker = "Items to discuss with your group:"
        scenario_text = text
        discussion_and_elevator = ""

        if discussion_marker in text:
            before, after = text.split(discussion_marker, 1)
            scenario_text = before.strip()
            discussion_and_elevator = after.strip()

        # 2. Discussion vs elevator pitch
        elevator_marker = "Be prepared to discuss in class (Elevator Pitch style):"
        discussion_text = discussion_and_elevator
        elevator_text = ""

        if elevator_marker in discussion_and_elevator:
            before, after = discussion_and_elevator.split(elevator_marker, 1)
            discussion_text = before.strip()
            elevator_text = after.strip()

        # 3. Containment vs Post-Incident Activities (just simple splits)
        # We assume both headings exist and in that order.
        containment_text = ""
        post_incident_text = ""

        cont_marker = "Containment"
        post_marker = "Post-Incident Activities"

        if cont_marker in discussion_text and post_marker in discussion_text:
            _, after_cont = discussion_text.split(cont_marker, 1)
            cont_part, after_post = after_cont.split(post_marker, 1)
            containment_text = cont_part.strip()
            post_incident_text = after_post.strip()
        else:
            # fallback: put all in containment if markers missing/broken
            containment_text = discussion_text

        return {
            "name": name,
            "scenario": " ".join(scenario_text.split()),
            "containment": containment_text.strip(),
            "post_incident_activities": post_incident_text.strip(),
            "elevator_pitch": elevator_text.strip(),
        }

# Example

if __name__ == "__main__":
    assignment_data = {
        "type": "assignment",
        "id": 790778,
        "title": "2024 Incident Scenerios",
        "content": "Assignment: 2024 Incident Scenerios\n\nPoints: 100.0\nSubmission Types: online_upload\n\nDescription:\nCloud StorageScenario:One of your organization\u2019s internal departments frequently uses outside cloud storage to store large amounts of data, some of which may be sensitive. You have recently learned that the cloud storage provider being used has been publicly compromised and large amounts of data have been exposed. All user passwords and data in the cloud provider\u2019s infrastructure may have been compromised.How do you respond?\nItems to discuss with your group:\nContainment\n\nWhat strategy should the organization take to contain the incident? Why is this strategy preferable to others?\n\nWhat could happen if the incident were not contained?\n\nWhat additional tools and organizations might be needed to respond to this particular incident?\n\nPost-Incident Activities\n\nWhat could be done to prevent similar incidents from occurring in the future?\n\nWhat could be done to improve detection of similar incidents?\n\nWhat could be done to improve containment of similar incidents?\n\nBe prepared to discuss in class (Elevator Pitch style):\n\nYour strategy to contain the attack.\n\nWhat additional tools and resources you would need.\n\nWhat your group learned.\n\nPII AccidentScenario:You receive news that one of your employees has accidentally disclosed sensitive personally identifiable information (PII) for over 200 clients and personnel. This occurred when they emailed a document that had not been properly scrubbed to a contractor. The employee had been recently trained on PII handling.How do you respond?\nItems to discuss with your group:\nContainment\n\nWhat strategy should the organization take to contain the incident?\n\nWhy is this strategy preferable to others?\n\nWhat could happen if the incident were not contained?\n\nWhat additional tools and organizations might be needed?\n\nPost-Incident Activities\n\nHow to prevent similar incidents in the future?\n\nHow to improve detection of similar incidents?\n\nHow to improve containment for similar incidents?\n\nBe prepared to discuss in class (Elevator Pitch style):\n\nYour strategy to contain the attack.\n\nTools/resources needed.\n\nWhat your group learned.\n\nSocial MediaScenario:Your organization\u2019s social media website is compromised. A terrorist group calling themselves \u201cRebellion Cyber Forces\u201d has claimed responsibility for attacks against government organizations. They have gained control of your organization\u2019s official social media account and are sending public notifications claiming your organization has been compromised.How do you respond?\nItems to discuss with your group:\nContainment\n\nStrategy to contain the incident and why.\n\nWhat happens if the incident isn't contained?\n\nAdditional tools/organizations needed?\n\nPost-Incident Activities\n\nHow to prevent similar incidents?\n\nHow to improve detection?\n\nHow to improve containment?\n\nBe prepared to discuss in class (Elevator Pitch style):\n\nYour strategy to contain the attack.\n\nTools/resources needed.\n\nWhat your group learned.\n\nZero-DayScenario:The browser deployed on all organizational workstations has a significant zero-day vulnerability being actively exploited. Ten workstations are already compromised and help desk calls are spiking. No patch or workaround exists yet; a patch is expected in one week.How do you respond?\nItems to discuss with your group:\nContainment\n\nRecommended containment strategy and why.\n\nRisks if not contained.\n\nAdditional tools/organizations needed?\n\nPost-Incident Activities\n\nPrevention of similar incidents.\n\nImproved detection.\n\nImproved containment.\n\nBe prepared to discuss in class (Elevator Pitch style):\n\nContainment strategy.\n\nTools/resources required.\n\nWhat your group learned.\n"
    }

    parser = AssignmentParser(assignment_data)
    structured = parser.parse()

    print(json.dumps(structured, indent=2))

    parser.save("parsed_assignment.json")
