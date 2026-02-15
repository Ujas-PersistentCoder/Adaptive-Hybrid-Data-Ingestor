import json
import os
import datetime

class MetadataManager:
    def __init__(self, filename="registry.json"):
        self.filename = filename

    def _serialize_stats(self, stats):
        """Internal helper to convert sets to lists and REMOVE large cardinality sets."""
        serializable = {}
        for k, v in stats.items():
            # Create a shallow copy to avoid modifying the live data
            new_val = v.copy()
            
            # 1. Standard serialization for types_seen
            new_val['types_seen'] = list(v['types_seen'])
            
            # 2. THE FIX: Remove the large set before JSON serialization
            # This prevents the "not serializable" error and keeps registry small
            if 'unique_values' in new_val:
                del new_val['unique_values']
                
            serializable[k] = new_val
        return serializable

    def write_initial_registry(self, stats, decisions):
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
        state = self.load_state()
        if not state:
            return False

        old_decision = state['decisions'].get(field_name)

        if current_decision != old_decision:
            state['decisions'][field_name] = current_decision
            
            # Serialize the specific field's stats safely
            serialized_field = current_stats.copy()
            serialized_field['types_seen'] = list(current_stats['types_seen'])
            
            # Ensure unique_values doesn't sneak into the update
            if 'unique_values' in serialized_field:
                del serialized_field['unique_values']
                
            state['stats'][field_name] = serialized_field
            state['last_drift_update'] = datetime.datetime.now().isoformat()
            
            with open(self.filename, 'w') as f:
                json.dump(state, f, indent=4)
            return True
        
        return False

    def load_state(self):
        if os.path.exists(self.filename) and os.path.getsize(self.filename) > 0:
            try:
                with open(self.filename, 'r') as f:
                    data = json.load(f)
                    for key in data['stats']:
                        data['stats'][key]['types_seen'] = set(data['stats'][key]['types_seen'])
                    return data
            except json.JSONDecodeError:
                return None
        return None