"""
Decides where to place each field according to the metrics received from profiler
"""
class PlacementJudge:
    def __init__(self, freq_threshold=0.5, stability_threshold=1.0):
        self.freq_threshold = freq_threshold
        self.stability_threshold = stability_threshold
        self.traceability_fields = ['username', 't_stamp', 'sys_ingested_at']

    def decide_placement(self, metrics):
        field = metrics.get('field', 'unknown')
        
        # 1. Traceability Check (using your endswith fix)
        if any(field.endswith(tf) for tf in self.traceability_fields):
            return "BOTH (Traceability)"
        
        # 2. Existing Hard Gates
        if metrics.get('is_nested') or metrics.get('stability', 0) < self.stability_threshold:
            return "MONGODB (Complex/Unstable)"
        
        if metrics.get('frequency', 0) < self.freq_threshold:
            return "MONGODB (Sparse)"
        
        # 3. Safe Uniqueness Check
        # If cardinality isn't there, metrics.get returns None (which != 1.0)
        if metrics.get('cardinality') == 1.0:
            return "SQL (Unique Identifier)"
        
        return "SQL (Standard Column)"