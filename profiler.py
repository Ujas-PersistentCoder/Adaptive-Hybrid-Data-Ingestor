"""
The Profiler first bifuractes the data received and decides types of the fields
- Decides upon the field type from nested, boolean, numeric, numeric_coercible, pattern(for ip_address), or str
- Handles fields like ip address by creating a seperate type for theem using the pattern of the numebr of digits and .
- observes the clean_record coming from normalizer, keeps track of the keys seen
- smartly checks if the the field type in the current record is similar to the max times seen field type, ie, either same as or convertible to it
- Updates the type counts otherwise
- gives metrics of the data for using in judge
"""

import re

class FieldProfiler:
    def __init__(self):
        self.stats = {}
        self.total_records = 0

    def _interpret_value_type(self, value):
        if isinstance(value, (list, tuple)):
            return "nested"
        if isinstance(value, bool):
            return "boolean"
        if isinstance(value, (int, float)):
            return "numeric"
        
        if isinstance(value, str):
            # 1. Is it a number disguised as a string?
            try:
                float(value)
                return "numeric_coercible"
            except ValueError:
                pass

            # 2. Pattern vs Plain Text
            # We only call it a "pattern" if it looks like an IP or a Version 
            # (contains digits mixed with dots/dashes)
            if re.search(r'\d', value) and re.search(r'[.\-_]', value):
                mask = re.sub(r'\d+', 'd', value)
                return f"pattern_{mask}"
            
            # 3. Everything else (names, usernames, weather) is just a string
            return "str"
        
        return "str"

    def observe(self, clean_record):
        self.total_records += 1
        
        for key, value in clean_record.items():
            if key not in self.stats:
                self.stats[key] = {
                    "types_seen": set(), 
                    "type_counts": {}, # Track how many times we see each type
                    "count": 0, 
                    "is_nested": False, 
                    "primary_type": None
                }
            
            v_type = self._interpret_value_type(value)
            self.stats[key]["count"] += 1
            
            # 1. Update type frequency
            self.stats[key]["type_counts"][v_type] = self.stats[key]["type_counts"].get(v_type, 0) + 1
            
            # 2. Update the "Primary Type" (The winner so far)
            # This makes the system more robust than just picking the first record
            self.stats[key]["primary_type"] = max(self.stats[key]["type_counts"], key=self.stats[key]["type_counts"].get)
            
            # 3. Smart Stability Check
            primary = self.stats[key]["primary_type"]
            if primary == "nested" or v_type == "nested":
                self.stats[key]["types_seen"].add(v_type)
                self.stats[key]["is_nested"] = True
            else:
                is_numeric_match = (primary == "numeric" and v_type == "numeric_coercible")
                is_coercible_match = (primary == "numeric_coercible" and v_type == "numeric")

                if not (is_numeric_match or is_coercible_match or v_type == primary):
                    self.stats[key]["types_seen"].add(v_type)
                else:
                    self.stats[key]["types_seen"].add(primary)

    def get_decision_metrics(self, key):
        """
        Prepares the data for Phase 3 (The Judge).
        """
        s = self.stats.get(key)
        if not s: return None
        
        # Stability is 1.0 only if exactly ONE type was ever seen
        stability = 1.0 if len(s["types_seen"]) == 1 else (1.0 / len(s["types_seen"]))
        frequency = s["count"] / self.total_records
        
        return {
            "field": key,
            "frequency": frequency,
            "stability": stability,
            "is_nested": s["is_nested"],
            "types": list(s["types_seen"])
        }