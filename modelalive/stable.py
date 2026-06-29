"""Behavioral stability — detect silent endpoint drift (ghost changes)."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from importlib import resources
from pathlib import Path
from typing import Any

from modelalive.exceptions import StableShiftError


def _load_prompts() -> list[dict[str, str]]:
    raw = resources.files("modelalive.data").joinpath("stable_prompts.json").read_text(encoding="utf-8")
    data = json.loads(raw)
    return list(data["prompts"])


def list_stable_prompts() -> list[dict[str, str]]:
    return _load_prompts()


def _trigram_distribution(text: str) -> Counter[str]:
    normalized = " ".join(text.lower().split())
    if len(normalized) < 3:
        return Counter({normalized or "∅": 1.0})
    counts: Counter[str] = Counter()
    for i in range(len(normalized) - 2):
        counts[normalized[i : i + 3]] += 1
    total = float(sum(counts.values()))
    return Counter({k: v / total for k, v in counts.items()})


def distribution_distance(a: Counter[str], b: Counter[str]) -> float:
    """L1 distance between normalized trigram distributions (0 = identical)."""
    keys = set(a) | set(b)
    return sum(abs(a.get(k, 0.0) - b.get(k, 0.0)) for k in keys) / 2.0


def response_distance(left: str, right: str) -> float:
    if left == right:
        return 0.0
    return distribution_distance(_trigram_distribution(left), _trigram_distribution(right))


@dataclass
class PromptFingerprint:
    id: str
    prompt: str
    responses: list[str] = field(default_factory=list)

    @property
    def digest(self) -> str:
        payload = "\n---\n".join(self.responses).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()[:16]

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "prompt": self.prompt,
            "responses": self.responses,
            "digest": self.digest,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PromptFingerprint:
        return cls(
            id=data["id"],
            prompt=data["prompt"],
            responses=list(data.get("responses") or []),
        )


@dataclass
class Fingerprint:
    model: str
    endpoint: str | None
    created_at: str
    prompts: list[PromptFingerprint]
    samples_per_prompt: int = 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": 1,
            "kind": "modelalive-stable-fingerprint",
            "model": self.model,
            "endpoint": self.endpoint,
            "created_at": self.created_at,
            "samples_per_prompt": self.samples_per_prompt,
            "prompts": [p.to_dict() for p in self.prompts],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Fingerprint:
        return cls(
            model=data["model"],
            endpoint=data.get("endpoint"),
            created_at=data.get("created_at") or datetime.now(timezone.utc).isoformat(),
            samples_per_prompt=int(data.get("samples_per_prompt") or 1),
            prompts=[PromptFingerprint.from_dict(p) for p in data.get("prompts", [])],
        )

    def save(self, path: str | Path) -> Path:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.to_dict(), indent=2) + "\n", encoding="utf-8")
        return target

    @classmethod
    def load(cls, path: str | Path) -> Fingerprint:
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))


def fingerprint_from_responses(
    model: str,
    responses_by_id: dict[str, list[str]],
    *,
    endpoint: str | None = None,
    samples_per_prompt: int = 1,
) -> Fingerprint:
    prompts: list[PromptFingerprint] = []
    for spec in _load_prompts():
        pid = spec["id"]
        prompts.append(
            PromptFingerprint(
                id=pid,
                prompt=spec["message"],
                responses=list(responses_by_id.get(pid, [])),
            )
        )
    return Fingerprint(
        model=model,
        endpoint=endpoint,
        created_at=datetime.now(timezone.utc).isoformat(),
        prompts=prompts,
        samples_per_prompt=samples_per_prompt,
    )


@dataclass
class PromptShift:
    prompt_id: str
    distance: float
    baseline_digest: str
    current_digest: str


@dataclass
class StabilityReport:
    model: str
    stable: bool
    mean_distance: float
    max_distance: float
    threshold: float
    prompt_shifts: list[PromptShift]
    baseline_created_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "model": self.model,
            "stable": self.stable,
            "mean_distance": round(self.mean_distance, 4),
            "max_distance": round(self.max_distance, 4),
            "threshold": self.threshold,
            "baseline_created_at": self.baseline_created_at,
            "prompt_shifts": [asdict(s) for s in self.prompt_shifts],
        }


def compare_fingerprints(
    baseline: Fingerprint,
    current: Fingerprint,
    *,
    threshold: float = 0.25,
) -> StabilityReport:
    by_id = {p.id: p for p in current.prompts}
    shifts: list[PromptShift] = []
    distances: list[float] = []

    for base in baseline.prompts:
        cur = by_id.get(base.id)
        if cur is None or not base.responses or not cur.responses:
            shifts.append(
                PromptShift(
                    prompt_id=base.id,
                    distance=1.0,
                    baseline_digest=base.digest,
                    current_digest=cur.digest if cur else "missing",
                )
            )
            distances.append(1.0)
            continue

        pair_distances = [
            response_distance(br, cr) for br in base.responses for cr in cur.responses
        ]
        dist = min(pair_distances) if pair_distances else 1.0
        distances.append(dist)
        if dist > threshold:
            shifts.append(
                PromptShift(
                    prompt_id=base.id,
                    distance=dist,
                    baseline_digest=base.digest,
                    current_digest=cur.digest,
                )
            )

    mean_dist = sum(distances) / len(distances) if distances else 1.0
    max_dist = max(distances) if distances else 1.0
    return StabilityReport(
        model=current.model,
        stable=mean_dist <= threshold,
        mean_distance=mean_dist,
        max_distance=max_dist,
        threshold=threshold,
        prompt_shifts=shifts,
        baseline_created_at=baseline.created_at,
    )


def assert_stable(
    baseline: Fingerprint,
    current: Fingerprint,
    *,
    threshold: float = 0.25,
) -> StabilityReport:
    report = compare_fingerprints(baseline, current, threshold=threshold)
    if not report.stable:
        shifted = ", ".join(s.prompt_id for s in report.prompt_shifts) or "aggregate"
        raise StableShiftError(
            f"Behavioral drift detected for {current.model} "
            f"(mean distance {report.mean_distance:.3f} > {threshold}). "
            f"Shifted prompts: {shifted}"
        )
    return report
