"""
Field Normalizer module

- Cleans all field names into snakecase, for uniformity throughout
- Checks if the field name is similar to something seen earlier.
- Provides a masked view of values for structural analysis.
"""

import re
from difflib import get_close_matches

class DynamicNormalizer:

    def __init__(self, similarity_threshold=0.85):
        self.master_keys = []
        self.threshold = similarity_threshold

    def normalize_key(self, key):
        # 1. Handle camelCase and PascalCase (e.g., userName -> user_name)
        temp = re.sub('([a-z0-9])([A-Z])', r'\1_\2', key)
        # 2. Lowercase everything and replace spaces
        clean_key = temp.lower().replace(" ", "_")

        # Dynamic discovery
        matches = get_close_matches(clean_key, self.master_keys, n=1, cutoff=self.threshold)
        if matches:
            return matches[0]
        else:
            self.master_keys.append(clean_key)
            return clean_key

    def _mask_value(self, value):
        """
        Determines the structural type of a value. 
        Only masks purely numeric/delimiter strings to prevent registry explosion.
        """
        if not isinstance(value, str):
            return type(value).__name__

        # RULE: Only mask if the string consists ONLY of digits and delimiters (., -, :, _)
        # This catches IP addresses, IDs, and timestamps but leaves emails/names as 'str'
        if re.fullmatch(r'[0-9\.\-\:_]+', value):
            # Replace digits with <num> to see the structure
            masked = re.sub(r'\d+', '<num>', value)
            return f"pattern_{masked}"

        # If it has letters (like emails, names), it's just a string
        return "str"

    def get_flattened_view(self, record, prefix="", mask_values=True):
        """
        Creates a flat map. If mask_values is True, it returns patterns 
        for the Profiler. If False, it returns raw values.
        """
        items = {}
        for k, v in record.items():
            clean_k = self.normalize_key(k)
            new_key = f"{prefix}.{clean_k}" if prefix else clean_k
            
            if isinstance(v, dict):
                items.update(self.get_flattened_view(v, prefix=new_key, mask_values=mask_values))
            else:
                # Use the new masking logic for the value
                items[new_key] = self._mask_value(v) if mask_values else v
        return items
    
    def normalize_record(self, record):
        """Recursively cleans all keys while maintaining structural integrity."""
        if not isinstance(record, dict):
            return record
        return {self.normalize_key(k): self.normalize_record(v) for k, v in record.items()}