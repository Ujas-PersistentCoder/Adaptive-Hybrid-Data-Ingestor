"""
Manages, adds, updates the metadata in the registry.json
- Serializes stats from sets to lists for JSON storing
- Writes intitial registry after the initial batch initialisation
- Updates the registry if at any point after the intial batch any field crosses the thresholds or decision metrics in either way
- Loads last saved state, to be used in case of shutdowns the metadata wont be lost and can be recovered
"""

import json
import os
import datetime

class MetadataManager:
    def __init__(self, filename="registry.json"):
        self.filename = filename

    def _serialize_stats(self, stats):
        """Internal helper to convert sets to lists for JSON."""
        serializable = {}
        for k, v in stats.items():
            new_val = v.copy()
            new_val['types_seen'] = list(v['types_seen'])
            serializable[k] = new_val
        return serializable

    def write_initial_registry(self, stats, decisions):
        """
        Called once after the first batch (e.g., 100 records).
        Establishes the baseline knowledge.
        """
        payload = {
            "stats": self._serialize_stats(stats),
            "decisions": decisions,
            "created_at": datetime.datetime.now().isoformat(),
            "mode": "initialized"
        }
        with open(self.filename, 'w') as f:
            json.dump(payload, f, indent=4)
        print(f"Initial Registry created with {len(decisions)} fields.")

    def update_if_changed(self, field_name, current_stats, current_decision):
        """
        Called during the live stream for every record.
        Only writes to disk if the DECISION for a field has shifted.
        """
        # 1. Load the current registry to check existing decision
        state = self.load_state()
        if not state:
            return

        old_decision = state['decisions'].get(field_name)

        # 2. Only update if the Judge has changed its mind
        if current_decision != old_decision:
            state['decisions'][field_name] = current_decision
            state['stats'][field_name] = current_stats.copy()
            
            state['stats'][field_name]['types_seen'] = list(current_stats['types_seen'])
            state['last_drift_update'] = datetime.datetime.now().isoformat()
            
            with open(self.filename, 'w') as f:
                json.dump(state, f, indent=4)
            return True # Signal that a change occurred for logging
        
        return False

    def load_state(self):
        """Loads knowledge back into memory and handles empty/corrupt files."""
        if os.path.exists(self.filename) and os.path.getsize(self.filename) > 0:
            try:
                with open(self.filename, 'r') as f:
                    data = json.load(f)
                    # Convert the lists back into sets for the Profiler
                    for key in data['stats']:
                        data['stats'][key]['types_seen'] = set(data['stats'][key]['types_seen'])
                    return data
            except json.JSONDecodeError:
                print(f"⚠️ Warning: {self.filename} was corrupt. Starting fresh.")
                return None
        return None