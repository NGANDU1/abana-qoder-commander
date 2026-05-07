# Route Optimization Algorithm (Prototype)

## Why a Greedy Heuristic?
Full Vehicle Routing Problem (VRP) solvers can be complex to implement and explain in an academic prototype. This project uses a **Greedy Nearest-Neighbor heuristic** with an **urgency weight** to:
- prioritize urgent bins (Full/Overflow),
- keep computation fast,
- remain easy to explain, test, and demonstrate.

## Steps
1. Select bins with fill level ≥ threshold (default 70%).
2. Compute an urgency score:
   - Overflow: highest priority
   - Full: high priority
   - Moderate: low priority
3. Distribute bins across available trucks (round-robin).
4. For each truck, build an ordered route:
   - start at depot,
   - choose the next bin that minimizes:
     - **distance / (1 + urgencyWeight × urgencyScore)**
   - repeat until all assigned bins are visited,
   - return to depot (for distance estimation).

## Complexity
- Greedy ordering per truck is approximately **O(n²)** for n bins assigned to that truck, which is acceptable for a city/district prototype.

## Limitations (Expected for a Prototype)
- Does not consider vehicle capacity, time windows, or traffic.
- Uses straight-line (Haversine) distance instead of road distances.

