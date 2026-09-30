"""
memory/store.py - ChromaDB-free, works on Python 3.14+
"""
from __future__ import annotations
import hashlib, json
from datetime import datetime
from pathlib import Path
from typing import Any


class WorkingMemory:
    def __init__(self, max_size: int = 30):
        self._items: list[dict] = []
        self._max = max_size

    def add(self, item: Any) -> None:
        self._items.append({"item": item, "ts": datetime.now().isoformat()})
        if len(self._items) > self._max:
            self._items.pop(0)

    def recent(self, n: int = 10) -> list[Any]:
        return [x["item"] for x in self._items[-n:]]

    def summary(self) -> str:
        if not self._items:
            return "(empty)"
        return "\n".join(f"  [{i+1}] {x['item']}" for i, x in enumerate(self._items[-10:]))

    def clear(self) -> None:
        self._items.clear()


class EpisodicMemory:
    def __init__(self, store_path: str = "./memory/store/episodic"):
        self._path = Path(store_path)
        self._path.mkdir(parents=True, exist_ok=True)
        self._file = self._path / "episodes.json"
        self._events: list[dict] = []
        if self._file.exists():
            try:
                self._events = json.loads(self._file.read_text(encoding="utf-8"))
            except Exception:
                self._events = []

    def _save(self) -> None:
        self._file.write_text(json.dumps(self._events, indent=2), encoding="utf-8")

    def store(self, event: str, outcome: str, metadata: dict | None = None) -> str:
        eid = hashlib.md5(f"{event}{datetime.now().isoformat()}".encode()).hexdigest()[:12]
        self._events.append({
            "id": eid, "event": event, "outcome": outcome,
            "ts": datetime.now().isoformat(), **(metadata or {}),
        })
        if len(self._events) > 200:
            self._events = self._events[-200:]
        self._save()
        return eid

    def recall(self, query: str, n: int = 5) -> list[dict]:
        if not self._events:
            return []
        q = query.lower()
        matched = [
            {"text": f"Event: {e['event']}\nOutcome: {e['outcome']}", "meta": e, "rank": i}
            for i, e in enumerate(reversed(self._events))
            if q in e.get("event", "").lower() or q in e.get("outcome", "").lower()
        ]
        if not matched:
            matched = [
                {"text": f"Event: {e['event']}\nOutcome: {e['outcome']}", "meta": e, "rank": i}
                for i, e in enumerate(reversed(self._events))
            ]
        return matched[:n]


class ProceduralMemory:
    def __init__(self, store_path: str = "./memory/store/procedural"):
        self._path = Path(store_path)
        self._path.mkdir(parents=True, exist_ok=True)
        self._file = self._path / "skills.json"
        self._skills: dict = {}
        if self._file.exists():
            try:
                self._skills = json.loads(self._file.read_text(encoding="utf-8"))
            except Exception:
                self._skills = {}

    def _save(self) -> None:
        self._file.write_text(json.dumps(self._skills, indent=2), encoding="utf-8")

    def store_skill(self, name: str, instructions: str) -> None:
        self._skills[name.lower().replace(" ", "_")] = {
            "name": name, "instructions": instructions,
            "ts": datetime.now().isoformat(),
        }
        self._save()

    def recall_skill(self, task: str, n: int = 3) -> list[str]:
        t = task.lower()
        return [
            f"Skill: {s['name']}\n{s['instructions']}"
            for s in self._skills.values()
            if t in s["name"].lower() or t in s["instructions"].lower()
        ][:n]


class AgentMemory:
    def __init__(self, agent_id: str = "agent", base_dir: str = "./memory/store"):
        self.working    = WorkingMemory()
        self.episodic   = EpisodicMemory(f"{base_dir}/episodic_{agent_id}")
        self.procedural = ProceduralMemory(f"{base_dir}/procedural_{agent_id}")

    def log(self, item: Any) -> None:
        self.working.add(item)

    def remember(self, event: str, outcome: str) -> None:
        self.episodic.store(event, outcome)

    def recall(self, query: str) -> list[dict]:
        return self.episodic.recall(query)

    def working_summary(self) -> str:
        return self.working.summary()