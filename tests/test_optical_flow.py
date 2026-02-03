import cv2 as cv
import numpy as np


def process_live_optical_flow(camera_index=0):
    """
    Process live camera feed to detect motion using dense optical flow.
    
    Controls:
        - Press 'f' to freeze/unfreeze the feed
        - Press 'q' to quit
    """
    
    # Open the camera
    cap = cv.VideoCapture(camera_index)
    
    if not cap.isOpened():
        print("Error: Could not open camera.")
        return
    
    # Set camera resolution for better performance
    cap.set(cv.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv.CAP_PROP_FRAME_HEIGHT, 480)
    
    # ret = a boolean return value from getting the frame
    # first_frame = the first frame in the entire video sequence
    ret, first_frame = cap.read()
    
    if not ret:
        print("Error: Could not read from camera.")
        return
    
    # Converts frame to grayscale because we only need the luminance channel
    # for detecting edges - less computationally expensive
    prev_gray = cv.cvtColor(first_frame, cv.COLOR_BGR2GRAY)
    
    # Creates an image filled with zero intensities with the same dimensions
    # as the frame
    mask = np.zeros_like(first_frame)
    
    # Sets image saturation to maximum
    mask[..., 1] = 255
    
    # Variables for freeze functionality
    frozen = False
    frozen_frame = first_frame.copy()
    frozen_gray = prev_gray.copy()
    frame_count = 0
    
    print("Live camera feed started.")
    print("Press 'f' to freeze/unfreeze the feed")
    print("Press 'q' to quit")
    print("-" * 60)
    
    while cap.isOpened():
        ret, frame = cap.read()
        
        if not ret:
            print("Error: Could not read frame.")
            break
        
        frame_count += 1
        
        # If frozen, keep using the frozen frame instead of new frames
        if frozen:
            frame = frozen_frame
            gray = frozen_gray
            status = "FROZEN"
        else:
            gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
            status = "LIVE"
        
        # Calculates dense optical flow by Farneback method
        h, w = gray.shape
        flow = np.zeros((h, w, 2), dtype=np.float32)
        cv.calcOpticalFlowFarneback(prev_gray, gray, flow,
                                    0.5, 3, 15, 3, 5, 1.2, 0)
        
        # Computes the magnitude and angle of the 2D vectors
        magnitude, angle = cv.cartToPolar(flow[..., 0], flow[..., 1])
        
        # Sets image hue according to the optical flow direction
        mask[..., 0] = angle * 180 / np.pi / 2
        
        # Sets image value according to the optical flow magnitude (normalized)
        magnitude_normalized = np.zeros_like(magnitude)
        cv.normalize(magnitude, magnitude_normalized, 0, 255, cv.NORM_MINMAX)
        mask[..., 2] = magnitude_normalized.astype(np.uint8)
        
        # Converts HSV to RGB (BGR) color representation
        rgb = cv.cvtColor(mask, cv.COLOR_HSV2BGR)
        
        # Calculate motion indicator based on average magnitude
        magnitude_array = np.asarray(magnitude)
        avg_magnitude = float(magnitude_array.mean())
        motion_detected = avg_magnitude > 1.1  # Threshold for motion detection
        motion_status = "MOTION DETECTED" if motion_detected else "NO MOTION"
        
        # Add text to both frames
        display_frame = frame.copy()
        
        # Status text
        cv.putText(display_frame, f"Status: {status}", (10, 30),
                   cv.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0) if not frozen else (0, 0, 255), 2)
        
        # Motion detection text
        color = (0, 255, 0) if motion_detected else (255, 0, 0)
        cv.putText(display_frame, f"Motion: {motion_status}", (10, 70),
                   cv.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        
        # Average magnitude
        cv.putText(display_frame, f"Avg Magnitude: {avg_magnitude:.2f}", (10, 110),
                   cv.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Instructions
        cv.putText(display_frame, "Press 'f' to freeze | 'q' to quit", (10, 450),
                   cv.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        # Add the same info to optical flow display
        cv.putText(rgb, f"Status: {status}", (10, 30),
                   cv.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0) if not frozen else (0, 0, 255), 2)
        
        cv.putText(rgb, f"Motion: {motion_status}", (10, 70),
                   cv.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        
        cv.putText(rgb, f"Avg Magnitude: {avg_magnitude:.2f}", (10, 110),
                   cv.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Print to console
        print(f"Frame {frame_count}: {status:6} | {motion_status:20} | Avg Magnitude: {avg_magnitude:7.2f}")
        
        # Display the input frame
        cv.imshow("Input Feed", display_frame)
        
        # Display the optical flow visualization
        cv.imshow("Dense Optical Flow", rgb)
        
        # Updates previous frame (only update if not frozen)
        if not frozen:
            prev_gray = gray
        
        # Handle key presses
        key = cv.waitKey(1) & 0xFF
        if key == ord('q'):
            print("Exiting...")
            break
        elif key == ord('f'):
            frozen = not frozen
            if frozen:
                # Store the current frame when freezing
                frozen_frame = frame.copy()
                frozen_gray = gray.copy()
                print(">>> FEED FROZEN <<<")
            else:
                print(">>> FEED UNFROZEN <<<")
                prev_gray = gray
    
    # The following frees up resources and closes all windows
    cap.release()
    cv.destroyAllWindows()


# Example usage
if __name__ == "__main__":
    process_live_optical_flow(camera_index=0)
