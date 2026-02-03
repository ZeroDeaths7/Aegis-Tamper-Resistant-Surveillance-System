import hmac
import hashlib
import time
import random
from datetime import datetime
import csv
import os

# --- CONFIGURATION (MUST MATCH live_streamer.py) ---
SERVER_SECRET_KEY = b"YourUnbreakableWatermarkSecretKey12345" 
TOKEN_CHANGE_INTERVAL_SECONDS = 1 
WATERMARK_LOG_FILE = 'watermark_log.csv'
# ---

# --- 1. VALIDATOR'S CRYPTOGRAPHIC TOKEN LOGIC ---

def calculate_expected_hmac_token(timestamp_seconds):
    """
    The Validator's deterministic function to predict the Token at any given time.
    Uses the same HMAC-SHA256 logic as the live stream server.
    """
    
    message = str(timestamp_seconds).encode('utf-8')
    
    # 1. Compute the HMAC hash
    hmac_digest = hmac.new(
        key=SERVER_SECRET_KEY, 
        msg=message, 
        digestmod=hashlib.sha256
    ).hexdigest()
    
    # 2. TRUNCATE and Convert to a small integer (0000-9999)
    last_4_hex = hmac_digest[-4:]
    token_int = int(last_4_hex, 16)
    final_token = token_int % 10000
    
    return f"{final_token:04d}"

# --- 2. SIMULATED ATTACK & VALIDATION ---

def load_real_stream_log():
    """Loads the timestamp and token sequence from the server log file."""
    log = []
    if not os.path.exists(WATERMARK_LOG_FILE):
        print(f"Error: Log file '{WATERMARK_LOG_FILE}' not found. Run live_streamer.py first.")
        return None
    
    with open(WATERMARK_LOG_FILE, mode='r') as file:
        reader = csv.reader(file)
        next(reader) # Skip header row
        for row in reader:
            if row:
                try:
                    timestamp = int(row[0])
                    token = row[1]
                    log.append((timestamp, token))
                except (ValueError, IndexError):
                    # Skip malformed rows
                    continue
    return log

def simulate_hmac_attack_and_validate():
    print("-------------------------------------------------------")
    print("--- 🧪 HMAC-TST LOOP DETECTION TEST STARTING ---")
    print("-------------------------------------------------------")
    
    real_stream_log = load_real_stream_log()
    
    if not real_stream_log or len(real_stream_log) < 10:
        print("\nERROR: Insufficient log data. Please run live_streamer.py for at least 10 seconds.")
        return
        
    log_duration = len(real_stream_log)
    
    print(f"\n[SERVER LOG] Loaded {log_duration} seconds of tokens from {WATERMARK_LOG_FILE}.")

    # 2. SIMULATE THE THIEF'S RECORDING AND TOKEN EXTRACTION
    # The thief records a 5-second segment (5 tokens)
    RECORD_DURATION = 5
    RECORD_START_INDEX = 5 # Start recording at the 6th token (index 5)
    RECORD_END_INDEX = RECORD_START_INDEX + RECORD_DURATION # End at index 10
    
    if RECORD_END_INDEX > log_duration:
        print(f"\nERROR: Log file is too short ({log_duration}s). Need at least {RECORD_END_INDEX}s.")
        return
    
    # This is the sequence the thief extracts from the watermarked video
    # NOTE: This is the actual data extracted from the 'hijacked' feed.
    thief_recorded_segment = [log[1] for log in real_stream_log[RECORD_START_INDEX:RECORD_END_INDEX]]
    
    print(f"\n[THIEF EXTRACTION] Thief recorded segment (5 tokens): {thief_recorded_segment}")
    
    # 3. SIMULATE THE THIEF'S LOOPING ATTACK
    THIEF_LOOP_COUNT = 3 
    thief_attack_sequence = thief_recorded_segment * THIEF_LOOP_COUNT
    
    print(f"[THIEF ATTACK] Looping 5-token segment 3 times: {thief_attack_sequence}")
    
    # --- 4. VALIDATOR ANALYSIS ---
    
    # The Validator starts monitoring immediately after the recorded segment ends.
    # The absolute timestamp when the validation should start (end time of recording)
    validation_start_timestamp = real_stream_log[RECORD_END_INDEX - 1][0] + 1
    
    print(f"\n[VALIDATOR] Starting comparison after Log Index {RECORD_END_INDEX}...")
    
    mismatch_found = False
    
    for i, observed_token in enumerate(thief_attack_sequence):
        # Time the Validator expects the TRUE token to be shown
        expected_time = validation_start_timestamp + i
        
        # Validator calculates the TRUE token for that expected time using the SECRET KEY
        expected_token = calculate_expected_hmac_token(expected_time)
        
        comparison_time_index = RECORD_END_INDEX + i
        
        # Check for Mismatch (The loop will instantly fail because the token is non-sequential)
        if observed_token != expected_token:
            mismatch_found = True
            print("-------------------------------------------------------")
            print(f"🚨 **FAKE FEED DETECTED** at Index: {comparison_time_index:02d}s")
            print(f"   Observed Token (Thief, from video): {observed_token}")
            print(f"   Expected Token (Real, predicted): {expected_token}")
            print("   Reason: The observed token does not match the HMAC prediction for this moment in time.")
            print("-------------------------------------------------------")
            break
            
    if not mismatch_found:
        print("Test failed: No decisive mismatch found.")
    else:
        print("\n✅ **TEST PASSED: HMAC-TST LOGIC VALIDATED.**")


# --- EXECUTION ---
simulate_hmac_attack_and_validate()