"""
Logging functions, logs into the log.txt file
"""

import datetime
import os

def clear_logs():
    """
    Overwrites the log file with a clean header. 
    Use this at the very start of a fresh session.
    """
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("log.txt", "w") as f:
        f.write(f"--- NEW INGESTION SESSION STARTED AT {timestamp} ---\n")
    print("log.txt has been cleared for the new session.")

def log_event(message):
    """General purpose logging with a timestamp."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("log.txt", "a") as f:
        f.write(f"[{timestamp}] {message}\n")

def log_routing(record_id, field, value, decision):
    """
    Logs where a specific piece of data is being sent.
    Provides proof of the 'Hybrid' placement.
    """
    log_event(f"ID: {record_id} | FIELD: {field} | VALUE: {value} | ROUTE: {decision}")

def log_drift(field, old_decision, new_decision):
    """
    Logs when the system autonomously changes its mind.
    This is the 'Adaptive' part of your project.
    """
    message = f"ADAPTIVE UPDATE: Field '{field}' shifted from {old_decision} to {new_decision}."
    log_event(message)