"""FactoryBot-style finite grid MDP instances for STARs evaluation.

The instances are generated procedurally from fixed seeds and stored as small
JSON files by scripts that need them. The grid is intentionally finite,
deterministic, and strongly connected over free cells, matching the setting in
which the paper's FactoryBot STARs have a known MDP and a Buchi objective.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import json
import random
from pathlib import Path
from typing import Iterable


ACTIONS = ("up", "down", "left", "right")
DELTAS = {
    "up": (-1, 0),
    "down": (1, 0),
    "left": (0, -1),
    "right": (0, 1),
}


@dataclass(frozen=True)
class FactoryBotInstance:
    name: str
    size: int
    walls: frozenset[tuple[int, int]]
    buchi: tuple[int, int]
    reward: tuple[int, int]
    start: tuple[int, int]
    category: str

    @property
    def states(self) -> tuple[tuple[int, int], ...]:
        return tuple(
            (r, c)
            for r in range(self.size)
            for c in range(self.size)
            if (r, c) not in self.walls
        )

    def to_json(self) -> dict:
        return {
            "name": self.name,
            "size": self.size,
            "walls": [list(x) for x in sorted(self.walls)],
            "buchi": list(self.buchi),
            "reward": list(self.reward),
            "start": list(self.start),
            "category": self.category,
        }

    @classmethod
    def from_json(cls, payload: dict) -> "FactoryBotInstance":
        return cls(
            name=payload["name"],
            size=int(payload["size"]),
            walls=frozenset(tuple(x) for x in payload["walls"]),
            buchi=tuple(payload["buchi"]),
            reward=tuple(payload["reward"]),
            start=tuple(payload["start"]),
            category=payload["category"],
        )

    def step(self, state: tuple[int, int], action: str) -> tuple[int, int]:
        dr, dc = DELTAS[action]
        nxt = (state[0] + dr, state[1] + dc)
        if (
            nxt[0] < 0
            or nxt[0] >= self.size
            or nxt[1] < 0
            or nxt[1] >= self.size
            or nxt in self.walls
        ):
            return state
        return nxt

    def reward_value(self, state: tuple[int, int], action: str) -> float:
        nxt = self.step(state, action)
        value = 1.0 if nxt == self.reward else 0.0
        return value - 0.01


def shortest_distances(instance: FactoryBotInstance, target: tuple[int, int]) -> dict[tuple[int, int], int]:
    q: deque[tuple[int, int]] = deque([target])
    dist = {target: 0}
    while q:
        s = q.popleft()
        for a in ACTIONS:
            pred = instance.step(s, opposite(a))
            # For deterministic four-neighbor grids, step(pred, a) == s iff
            # pred is a valid predecessor not blocked by a wall/boundary.
            if instance.step(pred, a) == s and pred not in dist:
                dist[pred] = dist[s] + 1
                q.append(pred)
    return dist


def opposite(action: str) -> str:
    return {"up": "down", "down": "up", "left": "right", "right": "left"}[action]


def connected(cells: Iterable[tuple[int, int]], size: int, walls: set[tuple[int, int]]) -> bool:
    cells = set(cells)
    if not cells:
        return False
    seen = {next(iter(cells))}
    q = deque(seen)
    while q:
        r, c = q.popleft()
        for dr, dc in DELTAS.values():
            nxt = (r + dr, c + dc)
            if 0 <= nxt[0] < size and 0 <= nxt[1] < size and nxt not in walls and nxt not in seen:
                seen.add(nxt)
                q.append(nxt)
    return seen == cells


def generate_instance(seed: int, size: int, category: str) -> FactoryBotInstance:
    rng = random.Random(seed)
    min_frac, max_frac = (0.65, 0.9) if category == "far" else (0.15, 0.3)
    cells = [(r, c) for r in range(size) for c in range(size)]

    for _ in range(500):
        wall_count = int(size * size * 0.12)
        walls = set(rng.sample(cells, wall_count))
        free = [x for x in cells if x not in walls]
        if not connected(free, size, walls):
            continue
        buchi = rng.choice(free)
        candidates = [
            x
            for x in free
            if min_frac * size <= abs(x[0] - buchi[0]) + abs(x[1] - buchi[1]) <= max_frac * size
        ]
        if not candidates:
            continue
        reward = rng.choice(candidates)
        starts = [x for x in free if x not in (buchi, reward)]
        start = rng.choice(starts)
        return FactoryBotInstance(
            name=f"{category}_{size}_{seed}",
            size=size,
            walls=frozenset(walls),
            buchi=buchi,
            reward=reward,
            start=start,
            category=category,
        )
    raise RuntimeError(f"could not generate connected instance seed={seed}")


def default_suite() -> list[FactoryBotInstance]:
    specs = [
        (101, 7, "close"),
        (102, 7, "close"),
        (201, 7, "far"),
        (202, 9, "far"),
        (301, 9, "close"),
        (302, 9, "far"),
    ]
    return [generate_instance(seed, size, category) for seed, size, category in specs]


def write_suite(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = [inst.to_json() for inst in default_suite()]
    path.write_text(json.dumps(payload, indent=2) + "\n")


def read_suite(path: Path) -> list[FactoryBotInstance]:
    return [FactoryBotInstance.from_json(x) for x in json.loads(path.read_text())]

