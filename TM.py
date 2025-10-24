#!/usr/bin/env python3
"""
NDI Trajectory Mechanic — Universal Clause Metric Script
Author: White Terrantula (NDI)
Purpose:
    Calculate and visualize the Fivefold Honor trajectory ratio.
    Designed for embedding or pasting into any AI chat or notebook.
    Fully non-violent, symbolic, and lawful.

Updated Features:
- Added batch update capabilities for scaling with vector inputs.
- Enhanced reporting options including CSV export for historical data.
- Introduced smoothing of trajectory ratio via exponential moving average.
- Added flexible phase thresholds and customizable honor value.
- Improved timestamp consistency for large batch processing.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Union
import math
import json
import time
import csv
from io import StringIO


@dataclass
class TrajectoryMechanic:
    # Fivefold Honor Metrics
    courage: float = 0.0
    dexterity: float = 0.0
    clause_matter: float = 0.0
    audacity: float = 0.0
    honor: float = 1.0  # Honor default invariant, customizable

    # History of updates - supports scaling
    history: List[Dict] = field(default_factory=list)

    # Phase thresholds, can be tuned if needed
    phase_thresholds: List[float] = field(default_factory=lambda: [0.25, 0.5, 0.75, 1.0])

    # EMA smoothing factor for trajectory ratio (0 to disable)
    smoothing_alpha: float = 0.3
    _ema_ratio: Union[float, None] = field(default=None, init=False)

    def update(self, courage: float, dexterity: float, clause_matter: float, audacity: float) -> Dict:
        """
        Update current metrics; each input clamped between 0.0 – 1.0.
        Returns the current snapshot with computed trajectory.
        """
        self.courage = self._clamp(courage)
        self.dexterity = self._clamp(dexterity)
        self.clause_matter = self._clamp(clause_matter)
        self.audacity = self._clamp(audacity)
        snapshot = self._snapshot()
        self.history.append(snapshot)
        return snapshot

    def batch_update(self, updates: List[Dict[str, float]]) -> List[Dict]:
        """
        Batch update capability: accepts list of metric dicts.
        Each dict must have keys 'courage', 'dexterity', 'clause_matter', 'audacity'.
        Returns list of snapshot results.
        """
        results = []
        for update in updates:
            result = self.update(
                courage=update.get('courage', 0.0),
                dexterity=update.get('dexterity', 0.0),
                clause_matter=update.get('clause_matter', 0.0),
                audacity=update.get('audacity', 0.0),
            )
            results.append(result)
        return results

    def _clamp(self, val: float) -> float:
        return max(0.0, min(1.0, val))

    def compute_trajectory(self) -> Dict[str, Union[float, str]]:
        """
        Compute the trajectory ratio R = (C + D + M + A) / (4 * H)
        Honor (H) is 1.0 by default but customizable.
        Applies optional EMA smoothing.
        """
        raw_ratio = (self.courage + self.dexterity + self.clause_matter + self.audacity) / (4 * self.honor)

        # Apply EMA smoothing if enabled
        if self.smoothing_alpha > 0:
            if self._ema_ratio is None:
                self._ema_ratio = raw_ratio
            else:
                self._ema_ratio = (self.smoothing_alpha * raw_ratio) + (1 - self.smoothing_alpha) * self._ema_ratio
            ratio = round(self._ema_ratio, 4)
        else:
            ratio = round(raw_ratio, 4)

        phase = self._determine_phase(ratio)
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        return {"ratio": ratio, "phase": phase, "timestamp": timestamp}

    def _determine_phase(self, ratio: float) -> str:
        # Custom phases based on thresholds
        thresh = self.phase_thresholds
        if ratio < thresh[0]:
            return "Initiation (Courage)"
        elif ratio < thresh[1]:
            return "Adaptation (Dexterity)"
        elif ratio < thresh[2]:
            return "Verification (Clause Matter)"
        elif ratio < thresh[3]:
            return "Action (Audacity)"
        else:
            return "Equilibrium (Honor)"

    def _snapshot(self) -> Dict:
        return {
            "courage": self.courage,
            "dexterity": self.dexterity,
            "clause_matter": self.clause_matter,
            "audacity": self.audacity,
            "result": self.compute_trajectory()
        }

    def report(self, as_json: bool = False):
        """
        Print or return the current state and trajectory ratio.
        """
        result = self.compute_trajectory()
        data = {
            "Fivefold": {
                "Courage": self.courage,
                "Dexterity": self.dexterity,
                "ClauseMatter": self.clause_matter,
                "Audacity": self.audacity,
                "Honor": self.honor,
            },
            "Trajectory": result
        }
        if as_json:
            return json.dumps(data, indent=2)
        else:
            print("
--- NDI Trajectory Mechanic Report ---")
            for k, v in data["Fivefold"].items():
                print(f"{k:<15}: {v:.3f}")
            print(f"Trajectory Ratio  : {result['ratio']}")
            print(f"Operational Phase : {result['phase']}")
            print("--------------------------------------
")
        return data

    def export_history_csv(self) -> str:
        """
        Export the full update history as a CSV string.
        """
        if not self.history:
            return ""

        output = StringIO()
        fieldnames = list(self.history[0]['result'].keys()) + ['courage', 'dexterity', 'clause_matter', 'audacity']
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        for entry in self.history:
            row = {
                'courage': entry['courage'],
                'dexterity': entry['dexterity'],
                'clause_matter': entry['clause_matter'],
                'audacity': entry['audacity'],
                **entry['result']
            }
            writer.writerow(row)
        return output.getvalue()


# Example usage when executed directly
if __name__ == "__main__":
    tm = TrajectoryMechanic(smoothing_alpha=0.2)
    tm.update(courage=0.8, dexterity=0.75, clause_matter=0.9, audacity=0.85)
    tm.report()