from ultralytics import YOLO
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ObjectDetector:
    """YOLO-based object detection for accessibility with intelligent prioritization"""
    
    # Enhanced priority system with danger levels
    # Priority levels: 1=Low, 2=Medium, 3=High, 4=Very High, 5=Critical
    # NOTE: YOLO v8 does NOT have 'stairs' class - removed from priorities
    
    # Emergency objects - immediate alert
    EMERGENCY_OBJECTS = {
        'fire hydrant',
        'stop sign',
        'traffic light',
    }
    
    PRIORITY_CLASSES = {
        # Critical hazards (immediate danger)
        'car': 5,
        'truck': 5,
        'bus': 5,
        'train': 5,
        
        # Very high priority (moving/dangerous objects)
        'motorcycle': 4,
        'bicycle': 4,
        'stop sign': 5,          # Emergency
        'traffic light': 5,      # Emergency
        'fire hydrant': 5,       # Emergency
        
        # High priority (obstacles/navigation)
        'person': 4,
        'dog': 4,
        'cat': 3,
        
        # Medium-high (furniture/obstacles)
        'chair': 3,
        'couch': 3,
        'bench': 3,
        'table': 3,
        'bed': 3,
        'potted plant': 2,
        'tv': 2,
        
        # Medium priority
        'door': 2,
        'refrigerator': 2,
        'oven': 2,
        'sink': 2,
        
        # Low priority (informational)
        'handbag': 1,
        'backpack': 1,
        'umbrella': 1,
        'bottle': 1,
        'cup': 1,
        'fork': 1,
        'knife': 2,
        'spoon': 1,
        'bowl': 1,
        'banana': 1,
        'apple': 1,
        'sandwich': 1,
        'orange': 1,
        'broccoli': 1,
        'carrot': 1,
        'hot dog': 1,
        'pizza': 1,
        'donut': 1,
        'cake': 1,
        'cell phone': 1,
        'laptop': 1,
        'mouse': 1,
        'remote': 1,
        'keyboard': 1,
        'book': 1,
        'clock': 1,
        'vase': 1,
        'scissors': 2,
        'teddy bear': 1,
        'hair drier': 1,
        'toothbrush': 1,
    }
    
    # Danger coefficient - how dangerous is this object type?
    DANGER_LEVEL = {
        # Vehicles (highest danger)
        'car': 10,
        'truck': 10,
        'bus': 10,
        'train': 10,
        'motorcycle': 9,
        'bicycle': 7,
        
        # Emergency/Safety
        'fire hydrant': 10,      # Emergency equipment
        'stop sign': 10,         # Safety critical
        'traffic light': 10,     # Safety critical
        
        # People and animals
        'person': 8,
        'dog': 7,
        'cat': 5,
        'horse': 8,
        'sheep': 5,
        'cow': 7,
        'elephant': 9,
        'bear': 9,
        'zebra': 6,
        'giraffe': 6,
        
        # Furniture (trip hazards)
        'chair': 5,
        'couch': 5,
        'table': 6,
        'bed': 4,
        'bench': 5,
        
        # Other obstacles
        'potted plant': 4,
        'tv': 3,
        'laptop': 2,
        'door': 3,
        
        'default': 3
    }
    
    def __init__(self, model_name='yolov8n.pt', confidence_threshold=0.5):
        """
        Initialize YOLO detector
        
        Args:
            model_name: YOLO model variant (yolov8n.pt is fastest)
            confidence_threshold: Minimum confidence for detection
        """
        self.confidence_threshold = confidence_threshold
        self.model = None
        self.model_name = model_name
        
    def load_model(self):
        """Load YOLO model"""
        try:
            logger.info(f"Loading YOLO model: {self.model_name}")
            self.model = YOLO(self.model_name)
            logger.info("YOLO model loaded successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to load YOLO model: {e}")
            return False
    
    def estimate_distance(self, bbox, frame_height, frame_width):
        """
        Estimate relative distance based on bounding box size
        Larger bbox = closer object
        
        Args:
            bbox: [x, y, w, h]
            frame_height: Height of frame
            frame_width: Width of frame
            
        Returns:
            float: Distance score (0-1, where 0=very close, 1=far)
        """
        x, y, w, h = bbox
        
        # Calculate bbox area relative to frame
        bbox_area = w * h
        frame_area = frame_height * frame_width
        relative_area = bbox_area / frame_area
        
        # Also consider vertical position (lower in frame = closer)
        # Objects at bottom of frame are typically closer
        vertical_position = (y + h) / frame_height  # 0=top, 1=bottom
        
        # Combine area and position
        # Larger area + lower position = closer (lower distance score)
        distance_score = 1.0 - (relative_area * 0.7 + (vertical_position * 0.3) * relative_area)
        
        return max(0.0, min(1.0, distance_score))
    
    def calculate_urgency(self, detection, frame_height, frame_width):
        """
        Calculate urgency score for a detection
        Combines: danger level, distance, and priority
        
        Higher urgency = more critical to announce
        
        Args:
            detection: Detection dict
            frame_height: Frame height
            frame_width: Frame width
            
        Returns:
            float: Urgency score (higher = more urgent)
        """
        class_name = detection['class']
        bbox = detection['bbox']
        
        # Get danger level
        danger = self.DANGER_LEVEL.get(class_name, self.DANGER_LEVEL['default'])
        
        # Get distance (0=very close, 1=far)
        distance = self.estimate_distance(bbox, frame_height, frame_width)
        
        # Calculate urgency
        # Formula: urgency = danger * (1 - distance) * confidence
        # Close + dangerous + confident = highest urgency
        urgency = danger * (1 - distance) * detection['confidence']
        
        return urgency
    
    def detect(self, frame):
        """
        Detect objects in frame with intelligent prioritization
        
        Args:
            frame: OpenCV image (numpy array)
            
        Returns:
            list: Detected objects sorted by URGENCY (most urgent first)
        """
        if self.model is None:
            logger.error("Model not loaded")
            return []
        
        try:
            # Get frame dimensions
            frame_height, frame_width = frame.shape[:2]
            
            # Run inference
            results = self.model(frame, verbose=False)
            
            detections = []
            
            for result in results:
                boxes = result.boxes
                
                for box in boxes:
                    # Extract detection info
                    confidence = float(box.conf[0])
                    
                    if confidence < self.confidence_threshold:
                        continue
                    
                    class_id = int(box.cls[0])
                    class_name = result.names[class_id]
                    
                    # Bounding box coordinates
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    bbox = [int(x1), int(y1), int(x2 - x1), int(y2 - y1)]
                    
                    # Assign priority
                    priority = self.PRIORITY_CLASSES.get(class_name, 1)
                    
                    # Check if emergency object
                    is_emergency = class_name in self.EMERGENCY_OBJECTS
                    
                    detection = {
                        'class': class_name,
                        'confidence': round(confidence, 2),
                        'bbox': bbox,
                        'priority': priority,
                        'is_emergency': is_emergency
                    }
                    
                    # Calculate urgency
                    urgency = self.calculate_urgency(detection, frame_height, frame_width)
                    detection['urgency'] = round(urgency, 2)
                    
                    # Estimate distance
                    distance = self.estimate_distance(bbox, frame_height, frame_width)
                    detection['distance'] = round(distance, 2)
                    
                    detections.append(detection)
            
            # Sort by URGENCY (most urgent first)
            detections.sort(key=lambda x: x['urgency'], reverse=True)
            
            # Log most urgent detection
            if detections:
                most_urgent = detections[0]
                logger.debug(f"Most urgent: {most_urgent['class']} "
                           f"(urgency={most_urgent['urgency']}, "
                           f"distance={most_urgent['distance']})")
            
            return detections
            
        except Exception as e:
            logger.error(f"Detection error: {e}")
            return []
    
    def get_priority_detections(self, detections, top_n=5):
        """
        Get top N priority detections (already sorted by urgency)
        
        Args:
            detections: List of detections
            top_n: Number of top detections to return
            
        Returns:
            list: Top priority detections
        """
        return detections[:top_n]
    
    def get_most_urgent(self, detections):
        """
        Get only the most urgent detection
        
        Args:
            detections: List of detections
            
        Returns:
            dict or None: Most urgent detection
        """
        return detections[0] if detections else None


# Test function
if __name__ == "__main__":
    import cv2
    
    detector = ObjectDetector()
    
    if detector.load_model():
        # Test with webcam
        cap = cv2.VideoCapture(0)
        
        print("Running detector. Press 'q' to quit")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            detections = detector.detect(frame)
            
            # Draw detections
            for det in detections:
                x, y, w, h = det['bbox']
                label = f"{det['class']} ({det['confidence']})"
                
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(frame, label, (x, y - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
            cv2.imshow("Object Detection", frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        cap.release()
        cv2.destroyAllWindows()
    else:
        print("Failed to load model")
