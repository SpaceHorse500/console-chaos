from __future__ import annotations

import random

from .datasets import DATASET_GENERATORS
from .tasks import TASKS_BY_KIND


class ExerciseEngine:
    def generate(self):
        dataset = random.choice(DATASET_GENERATORS)()
        tasks = TASKS_BY_KIND.get(dataset.kind, [])
        if not tasks:
            raise RuntimeError(f"No tasks registered for dataset kind {dataset.kind!r}")
        return random.choice(tasks)(dataset)
