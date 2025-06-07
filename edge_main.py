import cv2
import time
import torch
from motion_detector import MotionDetector
from local_utils import log_event, is_school_hour
from object_tracker import CentroidTracker


cap = cv2.VideoCapture(0)

model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)
model.conf = 0.5 

motion = MotionDetector()
tracker = CentroidTracker()
object_directions = {}
occupancy_count = 0

frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))

while True:
    ret, frame = cap.read()

    if is_school_hour():
        print("School hours: tracking occupancy...")
        results = model(frame)
        rects = []

  
        for *box, conf, cls in results.pred[0]:
            if int(cls) == 0: 
                x1, y1, x2, y2 = map(int, box)
                rects.append((x1, y1, x2, y2))

        objects = tracker.update(rects)

        for object_id, centroid in objects.items():
            cX, cY = centroid
            prev_cX = object_directions.get(object_id, None)

            if prev_cX is not None:
               
                direction = cX - prev_cX
                if direction < 0:
                    occupancy_count += 1
                    print(f"Person entered => occupancy: {occupancy_count}")
                    log_event("occupancy", {"count": occupancy_count})
                elif direction > 0:
                    occupancy_count = max(0, occupancy_count - 1)
                    print(f"Person exited <= occupancy: {occupancy_count}")
                    log_event("occupancy", {"count": occupancy_count})

            object_directions[object_id] = cX

        time.sleep(1)

    else:
       
        if motion.detect(frame):
            print("Motion detected. Running YOLOv5...")
            results = model(frame)
            people = [det for det in results.pred[0] if int(det[-1]) == 0]
            if people:
                print("Person detected during off hours")
                log_event("intrusion", {"alert": "Person detected during off hours"})
            time.sleep(10)
