from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .geo import Point, haversine_km


@dataclass(frozen=True)
class CandidateBin:
    id: int
    code: str
    point: Point
    fill_level: int
    status: str


def urgency_score(fill_level: int, status: str) -> float:
    """
    Simple urgency scoring:
    - Overflow: strong priority
    - Full: high priority
    - Moderate: low priority
    - Empty: none
    """

    base = max(0, min(100, int(fill_level))) / 100.0
    if status == "Overflow":
        return 2.0 + base
    if status == "Full":
        return 1.0 + base
    if status == "Moderate":
        return 0.25 + base
    return 0.0


def build_greedy_route(
    depot: Point,
    bins: Iterable[CandidateBin],
    urgency_weight: float = 1.5,
) -> tuple[list[CandidateBin], float]:
    """
    Greedy nearest-neighbor (urgency weighted):
    pick next bin that minimizes: distance_km / (1 + urgency_weight * urgency)

    This is not optimal like full VRP solvers, but it is:
    - easy to explain in an academic report
    - fast
    - produces good-enough routes for a prototype
    """

    remaining = list(bins)
    route: list[CandidateBin] = []
    total = 0.0
    current = depot

    while remaining:
        best_idx = 0
        best_cost = None
        best_dist = 0.0
        for i, b in enumerate(remaining):
            dist = haversine_km(current, b.point)
            urgency = urgency_score(b.fill_level, b.status)
            cost = dist / (1.0 + urgency_weight * urgency) if urgency > 0 else dist * 10.0
            if best_cost is None or cost < best_cost:
                best_cost = cost
                best_idx = i
                best_dist = dist
        chosen = remaining.pop(best_idx)
        route.append(chosen)
        total += best_dist
        current = chosen.point

    # Return to depot (optional for distance estimation)
    if route:
        total += haversine_km(current, depot)
    return route, round(total, 3)


def split_routes_round_robin(
    bins_sorted: list[CandidateBin],
    num_trucks: int,
) -> list[list[CandidateBin]]:
    """
    Quick workload split: distribute bins across trucks in round-robin order.
    """

    if num_trucks <= 0:
        return []
    buckets: list[list[CandidateBin]] = [[] for _ in range(num_trucks)]
    for i, b in enumerate(bins_sorted):
        buckets[i % num_trucks].append(b)
    return buckets


