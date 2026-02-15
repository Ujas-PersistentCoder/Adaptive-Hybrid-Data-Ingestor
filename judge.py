"""
Decides where to place each field according to the metrics received from profiler
"""
class PlacementJudge:
    def __init__(self, freq_threshold=0.5, stability_threshold=1.0):
        self.freq_threshold = freq_threshold
        self.stability_threshold = stability_threshold
        self.traceability_fields = ['username', 't_stamp', 'sys_ingested_at']

    def decide_placement(self, metrics):
        field = metrics['field']
        if field in self.traceability_fields:
            return "BOTH (Traceability)"
        if metrics['is_nested']:
            return "MONGODB (Complex/List)"
        if metrics['stability'] < self.stability_threshold:
            return "MONGODB (Unstable/Drifting)"
        if metrics['frequency'] < self.freq_threshold:
            return "MONGODB (Rare/Sparse)"
        
        return "SQL (Structured/Stable)"