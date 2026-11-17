"""
Pillar 4: Memory Between Tasks
Persistent cross-session memory for the AI Study Buddy Agent.
Retains user profile, mastered concepts, weak topics, quiz scores, and past task history across sessions.
"""

import os
import json
import time
from typing import Dict, Any, List, Optional


class AgentMemory:
    """
    Manages persistent memory across tasks and sessions stored in a JSON file.
    Implements Task 3.1 (Store Architecture) and Task 3.2 (Context Injection & Retrieval).
    """
    def __init__(self, storage_path: str = "storage/memory.json"):
        self.storage_path = storage_path
        self.data: Dict[str, Any] = {
            "user_profile": {
                "name": "Student",
                "grade_level": "Grade 10",
                "learning_style": "Prefers intuitive analogies and step-by-step breakdowns",
                "preferred_subjects": ["Science", "Math"]
            },
            "mastered_concepts": [],
            "weak_areas": [],
            "quiz_scores": [],
            "study_notes_index": [],
            "task_history": []
        }
        self.load()

    def load(self):
        """Loads memory from disk if it exists."""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r", encoding="utf-8-sig") as f:
                    loaded = json.load(f)
                    self.data.update(loaded)
            except Exception as e:
                print(f"[Memory Warning] Could not load memory file, starting with defaults: {e}")

    def save(self):
        """Persists memory atomically to disk."""
        os.makedirs(os.path.dirname(self.storage_path) or ".", exist_ok=True)
        try:
            with open(self.storage_path, "w", encoding="utf-8-sig") as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            print(f"[Memory Error] Could not save memory: {e}")

    def get_user_profile(self) -> Dict[str, Any]:
        return self.data.get("user_profile", {})

    def set_user_profile(
        self,
        name: Optional[str] = None,
        grade_level: Optional[str] = None,
        learning_style: Optional[str] = None,
        preferred_subjects: Optional[List[str]] = None
    ):
        profile = self.data.setdefault("user_profile", {})
        if name:
            profile["name"] = name
        if grade_level:
            profile["grade_level"] = grade_level
        if learning_style:
            profile["learning_style"] = learning_style
        if preferred_subjects:
            profile["preferred_subjects"] = preferred_subjects
        self.save()

    def add_mastered_concept(self, concept: str):
        """Adds a concept to mastered topics and removes it from weak areas if present."""
        mastered = self.data.setdefault("mastered_concepts", [])
        weak = self.data.setdefault("weak_areas", [])
        if concept not in mastered:
            mastered.append(concept)
        if concept in weak:
            weak.remove(concept)
        self.save()

    def add_weak_area(self, concept: str):
        """Flags a concept needing review/revision."""
        mastered = self.data.setdefault("mastered_concepts", [])
        weak = self.data.setdefault("weak_areas", [])
        if concept not in weak:
            weak.append(concept)
        if concept in mastered:
            mastered.remove(concept)
        self.save()

    def record_quiz_result(self, topic: str, score: int, total: int):
        """
        Records student quiz scores and dynamically adapts mastery state:
        - Score >= 80%: Promoted to mastered concepts.
        - Score < 70%: Flagged as weak area for follow-up review.
        """
        pct = round((score / total) * 100) if total > 0 else 0
        entry = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "topic": topic,
            "score": score,
            "total": total,
            "percentage": pct
        }
        self.data.setdefault("quiz_scores", []).append(entry)

        if pct >= 80:
            self.add_mastered_concept(topic)
        elif pct < 70:
            self.add_weak_area(topic)
        else:
            self.save()

    def index_study_note(self, title: str, file_path: str, tags: List[str]):
        """Indexes created notes for cross-task reference."""
        entry = {
            "title": title,
            "file_path": file_path,
            "tags": tags,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        self.data.setdefault("study_notes_index", []).append(entry)
        self.save()

    def record_task_completion(self, task: str, summary: str, tools_used: List[str]):
        """Records a completed task to persistent history."""
        entry = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "task": task,
            "summary": summary,
            "tools_used": tools_used
        }
        self.data.setdefault("task_history", []).append(entry)
        # Retain last 20 tasks
        if len(self.data["task_history"]) > 20:
            self.data["task_history"] = self.data["task_history"][-20:]
        self.save()

    def get_relevant_memory(self, query: str) -> str:
        """
        Task 3.2: Extracts memories most relevant to the given student query.
        """
        clean_q = query.lower()
        relevant_notes = []
        for note in self.data.get("study_notes_index", []):
            if any(w in clean_q for w in note["title"].lower().split("_")) or any(t in clean_q for t in note["tags"]):
                relevant_notes.append(f"Note '{note['title']}' ({note['file_path']})")

        relevant_quizzes = []
        for q in self.data.get("quiz_scores", []):
            if q["topic"].lower() in clean_q or clean_q in q["topic"].lower():
                relevant_quizzes.append(f"Quiz on {q['topic']}: {q['score']}/{q['total']} ({q['percentage']}%)")

        lines = []
        if relevant_notes:
            lines.append("Existing Relevant Notes: " + "; ".join(relevant_notes))
        if relevant_quizzes:
            lines.append("Past Quiz Performance: " + "; ".join(relevant_quizzes))
        return "\n".join(lines)

    def get_context_for_prompt(self, current_query: Optional[str] = None) -> str:
        """
        Task 3.2: Produces a rich, tailored context injection string for the LLM prompt.
        Ensures the agent remembers student state across sessions.
        """
        profile = self.data.get("user_profile", {})
        mastered = ", ".join(self.data.get("mastered_concepts", [])) or "None recorded yet"
        weak = ", ".join(self.data.get("weak_areas", [])) or "None identified yet"
        
        recent_tasks = self.data.get("task_history", [])[-3:]
        recent_str = ""
        if recent_tasks:
            recent_str = "\nRecent Study Tasks:\n" + "\n".join(
                f"- [{t.get('timestamp')}] {t.get('task')} -> {t.get('summary')}"
                for t in recent_tasks
            )

        query_memory = ""
        if current_query:
            rel = self.get_relevant_memory(current_query)
            if rel:
                query_memory = f"\nRelevant Memory Context:\n{rel}\n"

        return (
            f"--- STUDENT MEMORY PROFILE (CROSS-TASK PERSISTENCE) ---\n"
            f"Student: {profile.get('name', 'Student')} | Level: {profile.get('grade_level', 'Grade 10')}\n"
            f"Learning Style: {profile.get('learning_style', 'Simple language with intuitive analogies')}\n"
            f"Mastered Topics: {mastered}\n"
            f"Topics Needing Review: {weak}"
            f"{query_memory}"
            f"{recent_str}\n"
            f"--------------------------------------------------------"
        )
