"""Aggregate CostRecords into a savings report."""

from __future__ import annotations

from collections import Counter

from pydantic import BaseModel

from costrouter.models import CostRecord


class SavingsReport(BaseModel):
    requests: int
    total_actual_cost: float
    total_baseline_cost: float
    total_saved: float
    savings_pct: float
    escalations: int
    tier_distribution: dict[str, int]


class Telemetry:
    def __init__(self) -> None:
        self.records: list[CostRecord] = []

    def add(self, record: CostRecord) -> None:
        self.records.append(record)

    def report(self) -> SavingsReport:
        actual = sum(r.actual_cost for r in self.records)
        baseline = sum(r.baseline_cost for r in self.records)
        saved = baseline - actual
        dist = Counter(r.decision.chosen_tier for r in self.records)
        return SavingsReport(
            requests=len(self.records),
            total_actual_cost=actual,
            total_baseline_cost=baseline,
            total_saved=saved,
            savings_pct=(100.0 * saved / baseline) if baseline > 0 else 0.0,
            escalations=sum(1 for r in self.records if r.decision.escalated),
            tier_distribution=dict(dist),
        )
