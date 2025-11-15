import cv2
import tamper_detector # <-- IMPORT YOUR NEW MODULE

# --- Configuration ---
BLUR_THRESHOLD = 80.0
SHAKE_THRESHOLD = 1.1 # You will need to tune this!
CAMERA_INDEX = 0
# ---

def run_live_test(camera_index, blur_thresh, shake_thresh):
    """
    Process live camera feed to check for blur and shake.
    """
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        print("Error: Could not open camera.")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    print("Live camera test started. Press 'q' to quit.")
    print(f"Blur Threshold: {blur_thresh} | Shake Threshold: {shake_thresh}")
    print("Press '+' / '-' to adjust BLUR threshold.")
    print("Press 'w' / 's' to adjust SHAKE threshold.")
    print("-" * 60)

    ret, frame = cap.read()
    if not ret:
        print("Error: Could not read first frame.")
        cap.release()
        return
        
    # Initialize previous frame for optical flow
    prev_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Could not read frame.")
            break

        # 1. Convert to grayscale (do it once)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # 2. Check for Blur
        is_blurred, blur_variance = tamper_detector.check_blur(
            gray, 
            threshold=blur_thresh
        )

        # 3. Check for Shake
        is_shaken, shake_magnitude = tamper_detector.check_shake(
            gray, 
            prev_gray, 
            threshold=shake_thresh
        )
        
        # --- Update previous frame ---
        prev_gray = gray 
        
        # --- Display Logic ---
        blur_status = "BLURRY" if is_blurred else "SHARP"
        shake_status = "SHAKE" if is_shaken else "STABLE"
        
        color = (0, 0, 255) # Default Red
        if not is_blurred and not is_shaken:
            color = (0, 255, 0) # Green

        # Add text to the frame
        cv2.putText(frame, f"STATUS: {blur_status} | {shake_status}",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        
        cv2.putText(frame, f"Blur Variance: {blur_variance:.2f} (Th: {blur_thresh:.0f})",
                    (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        cv2.putText(frame, f"Shake Magnitude: {shake_magnitude:.2f} (Th: {shake_thresh:.1f})",
                    (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        # Display the frame
        cv2.imshow("Live Tamper Detection Test", frame)

        # --- Key Controls ---
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            print("Exiting...")
            break
        # Blur controls
        elif key == ord("+") or key == ord("="):
            blur_thresh += 50
            print(f"Blur threshold increased to: {blur_thresh}")
        elif key == ord("-"):
            blur_thresh = max(0, blur_thresh - 50)
            print(f"Blur threshold decreased to: {blur_thresh}")
        # Shake controls
        elif key == ord("w"):
            shake_thresh += 1.0
            print(f"Shake threshold increased to: {shake_thresh}")
        elif key == ord("s"):
            shake_thresh = max(0, shake_thresh - 1.0)
            print(f"Shake threshold decreased to: {shake_thresh}")

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    run_live_test(
        camera_index=CAMERA_INDEX, 
        blur_thresh=BLUR_THRESHOLD, 
        shake_thresh=SHAKE_THRESHOLD
    )