"""
Main orchestrator for the entire project excluding starting the API endpoint
"""

import json
import requests
import datetime
from normalizer import DynamicNormalizer
from profiler import FieldProfiler
from judge import PlacementJudge
from metadata_manager import MetadataManager
from logger import clear_logs, log_event, log_routing, log_drift

# SETUP & GLOBAL STATE
clear_logs()  # Start fresh
dn = DynamicNormalizer()
profiler = FieldProfiler()
judge = PlacementJudge()
mm = MetadataManager()

# Check for existing memory
existing_state = mm.load_state()

if existing_state:
    profiler.stats = existing_state['stats']
    # Restore normalizer memory so fuzzy matching remains consistent
    dn.master_keys = [key.split('.')[-1] for key in existing_state['stats'].keys()]
    current_mode = "LIVE"
    log_event("REGISTRY LOADED: System resuming in LIVE mode.")
    print("🚀 Warm Start: Registry loaded. System is LIVE.")
else:
    current_mode = "LEARNING"
    log_event("NO REGISTRY: System entering BATCH LEARNING mode (1000 records).")
    print("🧠 Cold Start: Learning mode active. Waiting for 1000 records...")

ingestion_buffer = []

# ROUTING & ADAPTIVE LOGIC

def route_single_record(record, decisions, is_live=False):
    """
    Simulates the routing of data to SQL or MongoDB via logging.
    If is_live=True, it detects schema drift and updates the registry.
    """
    record_id = record.get('sys_ingested_at', 'unknown_id')
    flat_view = dn.get_flattened_view(record)
    
    for field_path, value in flat_view.items():
        # Get the current known decision
        decision = decisions.get(field_path, "MONGODB (Default)")

        # Adaptive Check (Only in Live Mode)
        if is_live:
            metrics = profiler.get_decision_metrics(field_path)
            if metrics:
                new_decision = judge.decide_placement(metrics)
                
                # Update registry only if the decision actually flips
                if mm.update_if_changed(field_path, profiler.stats[field_path], new_decision):
                    log_drift(field_path, decision, new_decision)
                    decision = new_decision # Log the new route
        
        log_routing(record_id, field_path, value, decision)

# BATCH FINALIZATION

def finalize_initial_batch():
    """
    Finalizes the first 1000 records, saves the registry, and flushes logs.
    """
    global ingestion_buffer, current_mode
    log_event("--- BATCH THRESHOLD REACHED (1000) ---")
    # Create the buffer_log.txt for the TA
    print("💾 Saving 1000-record buffer to buffer_log.txt...")
    with open("buffer_log.txt", "w") as f:
        for record in ingestion_buffer:
            f.write(json.dumps(record) + "\n")
    log_event("Buffer snapshot saved to buffer_log.txt.")
    print("🎯 1000 records reached. Generating baseline schema...")

    # Determine decisions
    initial_decisions = {}
    for field_path in profiler.stats.keys():
        metrics = profiler.get_decision_metrics(field_path)
        initial_decisions[field_path] = judge.decide_placement(metrics)

    # Save to Disk
    mm.write_initial_registry(profiler.stats, initial_decisions)
    
    # Flush Buffer to Logs
    log_event(f"Flushing {len(ingestion_buffer)} records from buffer.")
    for record in ingestion_buffer:
        route_single_record(record, initial_decisions, is_live=False)

    # Cleanup
    ingestion_buffer = []
    current_mode = "LIVE"
    log_event("Transitioned to LIVE mode.")
    print("✅ Initial Registry saved. Buffer flushed. System is now LIVE.")

# MAIN INGESTION ENGINE

def run_pipeline(n_records):
    global current_mode
    API_URL = f"http://127.0.0.1:8000/record/{n_records}"
    
    try:
        # stream=True is critical for SSE
        response = requests.get(API_URL, stream=True, timeout=15)
        
        # Manual line splitting to avoid buffer hanging
        pending_data = ""
        for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
            if chunk:
                pending_data += chunk
                while "\n" in pending_data:
                    line, pending_data = pending_data.split("\n", 1)
                    line = line.strip()
                    
                    if line.startswith("data: "):
                        raw_json = line.replace("data: ", "")
                        raw_record = json.loads(raw_json)
                        
                        # Add Traceability ID
                        raw_record['sys_ingested_at'] = datetime.datetime.now().isoformat()
                        
                        # Flatten and Observe for Profiling
                        flat_view = dn.get_flattened_view(raw_record)
                        profiler.observe(flat_view)
                        
                        # DECISION POINT
                        if current_mode == "LEARNING":
                            ingestion_buffer.append(raw_record)
                            if profiler.total_records == 1000:
                                finalize_initial_batch()
                        else:
                            # In live mode, we pull decisions fresh from registry/memory
                            state = mm.load_state()
                            decisions = state['decisions'] if state else {}
                            route_single_record(raw_record, decisions, is_live=True)

                        # Console Heartbeat
                        if profiler.total_records % 50 == 0:
                            print(f"📊 Processed {profiler.total_records} records...")

    except Exception as e:
        print(f"❌ Error: {e}")
        log_event(f"CRITICAL ERROR: {e}")

if __name__ == "__main__":
    # enter the number of records to be ingested
    run_pipeline(1200)