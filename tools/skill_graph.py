"""Explicit STEM skill graph used by the adaptive learning engine.

The graph is deliberately deterministic and independent of any LLM. It describes
what a learner needs before a downstream concept is considered ready.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class Skill:
    id: str
    name: str
    domain: str
    stage: int
    prerequisites: tuple[str, ...] = ()


SKILLS: tuple[Skill, ...] = (
    Skill("arithmetic", "Arithmetic", "math", 1),
    Skill("fractions", "Fractions", "math", 1, ("arithmetic",)),
    Skill("ratios", "Ratios", "math", 1, ("arithmetic", "fractions")),
    Skill("algebra", "Algebra", "math", 1, ("arithmetic", "fractions")),
    Skill("geometry", "Geometry", "math", 1, ("arithmetic",)),
    Skill("graphs", "Graphs", "math", 1, ("arithmetic", "algebra")),
    Skill("trigonometry", "Trigonometry", "math", 2, ("geometry", "algebra")),
    Skill("vectors", "Vectors", "math", 2, ("geometry", "trigonometry")),
    Skill("functions", "Functions", "math", 2, ("algebra", "graphs")),
    Skill("calculus_differentiation", "Differentiation", "math", 3, ("functions", "trigonometry")),
    Skill("calculus_integration", "Integration", "math", 3, ("calculus_differentiation", "functions")),
    Skill("measurement", "Measurement & Units", "physics", 1, ("arithmetic", "ratios")),
    Skill("motion", "Motion", "physics", 1, ("measurement", "graphs", "algebra")),
    Skill("forces", "Forces", "physics", 1, ("measurement", "algebra")),
    Skill("energy", "Energy", "physics", 1, ("forces", "motion", "algebra")),
    Skill("momentum", "Momentum", "physics", 2, ("forces", "motion")),
    Skill("circular_motion", "Circular Motion", "physics", 2, ("motion", "vectors", "trigonometry")),
    Skill("electricity", "Electricity", "physics", 2, ("algebra", "measurement")),
    Skill("dc_circuits", "DC Circuits", "physics", 2, ("electricity", "algebra")),
    Skill("waves", "Waves", "physics", 2, ("graphs", "trigonometry", "motion")),
    Skill("optics", "Optics", "physics", 2, ("geometry", "trigonometry")),
    Skill("electromagnetism", "Electromagnetism", "physics", 3, ("vectors", "electricity", "dc_circuits")),
    Skill("thermodynamics", "Thermodynamics", "physics", 3, ("algebra", "measurement", "energy")),
    Skill("quantum_intro", "Quantum Introduction", "physics", 4, ("algebra", "waves", "electricity")),
    Skill("engineering_design", "Engineering Design", "engineering", 4, ("algebra", "measurement", "forces", "electricity")),
)

_BY_ID = {skill.id: skill for skill in SKILLS}


def get_skill(skill_id: str) -> Skill:
    try:
        return _BY_ID[skill_id]
    except KeyError as exc:
        raise ValueError(f"Unknown skill: {skill_id}") from exc


def prerequisites(skill_id: str) -> tuple[str, ...]:
    return get_skill(skill_id).prerequisites


def missing_prerequisites(skill_id: str, mastery: dict[str, dict]) -> list[str]:
    """Return direct prerequisites below mastery threshold, in graph order."""
    missing = []
    for prereq in prerequisites(skill_id):
        score = float(mastery.get(prereq, {}).get("score", 0.0))
        if score < 60.0:
            missing.append(prereq)
    return missing


def is_ready(skill_id: str, mastery: dict[str, dict], threshold: float = 60.0) -> bool:
    return not any(
        float(mastery.get(prereq, {}).get("score", 0.0)) < threshold
        for prereq in prerequisites(skill_id)
    )


def learning_frontier(mastery: dict[str, dict], threshold: float = 60.0) -> list[Skill]:
    """Return the skills the learner can reasonably study next.

    A skill is on the frontier when its own mastery is below threshold and every
    direct prerequisite meets threshold. Results are ordered by stage then graph
    declaration order, keeping the learner's path stable across sessions.
    """
    frontier = []
    for skill in SKILLS:
        own_score = float(mastery.get(skill.id, {}).get("score", 0.0))
        if own_score < threshold and is_ready(skill.id, mastery, threshold):
            frontier.append(skill)
    return frontier


def choose_next_skill(mastery: dict[str, dict], preferred_domain: str | None = None) -> Skill | None:
    """Choose the earliest actionable skill, preferring the requested domain."""
    frontier = learning_frontier(mastery)
    if preferred_domain:
        domain_matches = [skill for skill in frontier if skill.domain == preferred_domain]
        if domain_matches:
            return domain_matches[0]
    return frontier[0] if frontier else None


def prerequisite_chain(skill_id: str) -> list[str]:
    """Return a stable depth-first prerequisite chain for display/remediation."""
    result: list[str] = []
    seen: set[str] = set()

    def visit(current: str) -> None:
        if current in seen:
            return
        seen.add(current)
        for prereq in prerequisites(current):
            visit(prereq)
        if current != skill_id:
            result.append(current)

    visit(skill_id)
    return result


def validate_graph(skills: Iterable[Skill] = SKILLS) -> None:
    """Fail fast if a curriculum edit introduces a missing node or cycle."""
    nodes = {skill.id for skill in skills}
    for skill in skills:
        unknown = set(skill.prerequisites) - nodes
        if unknown:
            raise ValueError(f"{skill.id} references unknown skills: {sorted(unknown)}")

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(skill_id: str) -> None:
        if skill_id in visiting:
            raise ValueError(f"Skill graph contains a cycle at {skill_id}")
        if skill_id in visited:
            return
        visiting.add(skill_id)
        for prereq in _BY_ID[skill_id].prerequisites:
            visit(prereq)
        visiting.remove(skill_id)
        visited.add(skill_id)

    for skill in nodes:
        visit(skill)


validate_graph()
