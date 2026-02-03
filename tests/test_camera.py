import cv2
cap = cv2.VideoCapture(0) # 0 is default webcam

if not cap.isOpened():
    print("ERROR: Cannot open camera.")
    exit()

while True:
    ret, frame = cap.read()
    if not ret:
        print("ERROR: Can't receive frame.")
        break

    cv2.imshow('WEBCAM TEST - PRESS Q TO QUIT', frame)

    if cv2.waitKey(1) == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()