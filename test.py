import cv2

for i in range(5):  # Попробуйте больше индексов, если необходимо
    cap = cv2.VideoCapture(i)
    if cap.isOpened():
        print(f"Camera with index {i} is available")
        cap.release()
    else:
        print(f"Camera with index {i} is not available")
