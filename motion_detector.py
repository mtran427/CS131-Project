import cv2

class MotionDetector:
    def __init__(self, sensitivity=500):
        self.last_frame = None
        self.sensitivity = sensitivity

    def detect(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)
        if self.last_frame is None:
            self.last_frame = gray
            return False
        frame_delta = cv2.absdiff(self.last_frame, gray)
        thresh = cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)[1]
        count = cv2.countNonZero(thresh)
        self.last_frame = gray
        return count > self.sensitivity
