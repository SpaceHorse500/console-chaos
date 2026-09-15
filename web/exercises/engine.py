from __future__ import annotations

import random

from .datasets import DATASET_GENERATORS
from .skills import SKILLS, STATUS_ORDER, build_progress, prerequisites_ready
from .tasks import TASKS_BY_KIND


class ExerciseEngine:
    """Adaptive selector: deliberate skill progression, randomized scenarios."""

    def _candidate_pool(self):
        candidates = []
        for dataset_factory in DATASET_GENERATORS:
            dataset = dataset_factory()
            for task in TASKS_BY_KIND.get(dataset.kind, []):
                candidates.append(task(dataset))
        return candidates

    @staticmethod
    def _target_ids(exercise):
        target_ids = [
            use.skill_id
            for use in exercise.skills
            if use.role == "target"
        ]
        return target_ids or [use.skill_id for use in exercise.skills]

    def _targets_ready(self, exercise, progress) -> bool:
        target_ids = set(self._target_ids(exercise))
        for skill_id in target_ids:
            definition = SKILLS[skill_id]
            for required in definition.requires:
                # A tightly coupled focused exercise may introduce adjacent concepts
                # together (for example jq field extraction + raw output, or an AWK
                # loop + dynamic field reference). Other prerequisites must already
                # have reached at least Learning.
                if required in target_ids:
                    continue
                if progress[required]["status_rank"] < STATUS_ORDER["learning"]:
                    return False
        return True

    def _eligible(self, exercise, progress, solved_count: int) -> bool:
        if not self._targets_ready(exercise, progress):
            return False

        target_ids = self._target_ids(exercise)
        target_states = [progress[sid] for sid in target_ids]

        if exercise.style == "focused":
            return True

        if exercise.style == "integration":
            if solved_count < 3:
                return False
            # Integration may introduce one simple concept, but it should not leap
            # several levels ahead of the learner's current frontier.
            unseen_high = sum(
                state["status"] == "not_introduced" and state["level"] >= 4
                for state in target_states
            )
            return unseen_high == 0

        if exercise.style == "challenge":
            if solved_count < 8:
                return False
            # Challenges come only after the target concepts have already appeared
            # in at least one integration exercise. That preserves the sequence:
            # teach -> reinforce -> integrate -> challenge.
            return all(
                state["status_rank"] >= STATUS_ORDER["introduced"]
                and state["integration_uses"] >= 1
                for state in target_states
            )

        return False

    @staticmethod
    def _style_weights(solved_count: int, progress: dict) -> dict[str, float]:
        if solved_count < 3:
            return {"focused": 1.0, "integration": 0.0, "challenge": 0.0}

        if solved_count < 8:
            return {"focused": 0.75, "integration": 0.25, "challenge": 0.0}

        ready_unseen = sum(
            state["status"] == "not_introduced"
            and prerequisites_ready(skill_id, progress)
            for skill_id, state in progress.items()
        )

        # While a lot of the curriculum is still untouched, keep teaching new
        # concepts frequently. Later, spend more time integrating and challenging.
        if ready_unseen >= 6:
            return {"focused": 0.55, "integration": 0.35, "challenge": 0.10}

        return {"focused": 0.35, "integration": 0.45, "challenge": 0.20}

    def _score(self, exercise, progress, records):
        score = random.uniform(0.0, 1.25)
        target_ids = self._target_ids(exercise)
        states = [progress[sid] for sid in target_ids]

        recent_templates = {
            record.get("template_id")
            for record in records[:7]
            if record.get("template_id")
        }

        # Within each style, choose skills near the current learning frontier.
        if exercise.style == "focused":
            values = [{
                "not_introduced": 13.0,
                "introduced": 9.0,
                "learning": 7.0,
                "practiced": 3.5,
                "comfortable": 1.0,
            }[state["status"]] for state in states]
            score += sum(values) / len(values)
            # Explicitly favor a ready concept that has never been taught yet.
            unseen = sum(state["status"] == "not_introduced" for state in states)
            if unseen:
                score += 4.0
            # Avoid teaching too many unrelated new concepts in one focused task.
            if unseen > 1:
                score -= (unseen - 1) * 1.5

        elif exercise.style == "integration":
            values = [{
                "not_introduced": 1.0,
                "introduced": 5.0,
                "learning": 7.0,
                "practiced": 7.5,
                "comfortable": 5.0,
            }[state["status"]] for state in states]
            score += sum(values) / len(values)

        elif exercise.style == "challenge":
            values = [{
                "not_introduced": -50.0,
                "introduced": -20.0,
                "learning": 5.0,
                "practiced": 8.0,
                "comfortable": 9.0,
            }[state["status"]] for state in states]
            score += sum(values) / len(values)

        # Nudge progression upward once prerequisites are ready without making it
        # strictly linear. Old concepts still return as spaced review.
        if states:
            score += min(max(state["level"] for state in states), 8) * 0.12

        if exercise.template_id in recent_templates:
            score -= 8.0

        return score

    @staticmethod
    def _pick_style(weights: dict[str, float], available: set[str]) -> str:
        styles = [style for style in ("focused", "integration", "challenge") if style in available]
        if not styles:
            raise RuntimeError("No eligible exercise styles are available.")

        values = [max(weights.get(style, 0.0), 0.0) for style in styles]
        if sum(values) <= 0:
            values = [1.0] * len(styles)
        return random.choices(styles, weights=values, k=1)[0]

    def generate(self, records: list[dict] | None = None):
        records = records or []
        progress = build_progress(records)
        solved_count = len(records)
        candidates = self._candidate_pool()

        eligible = [
            candidate
            for candidate in candidates
            if self._eligible(candidate, progress, solved_count)
        ]
        if not eligible:
            # Defensive fallback: any focused exercise whose prerequisites are ready.
            eligible = [
                candidate
                for candidate in candidates
                if candidate.style == "focused" and self._targets_ready(candidate, progress)
            ]
        if not eligible:
            raise RuntimeError("No exercise candidates are available for the current skill state.")

        available_styles = {candidate.style for candidate in eligible}
        wanted_style = self._pick_style(
            self._style_weights(solved_count, progress),
            available_styles,
        )
        same_style = [candidate for candidate in eligible if candidate.style == wanted_style]

        ranked = sorted(
            ((self._score(candidate, progress, records), candidate) for candidate in same_style),
            key=lambda pair: pair[0],
            reverse=True,
        )

        best_score = ranked[0][0]
        shortlist = [
            candidate
            for score, candidate in ranked
            if score >= best_score - 1.5
        ]
        return random.choice(shortlist)
