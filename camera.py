import cv2
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CameraHandler:
    """Handles camera initialization and frame capture"""
    
    def __init__(self, camera_id=0, width=640, height=480):
        """
        Initialize camera
        
        Args:
            camera_id: Camera device ID (0 for default webcam)
            width: Frame width
            height: Frame height
        """
        self.camera_id = camera_id
        self.width = width
        self.height = height
        self.cap = None
        
    def initialize(self):
        """Initialize camera capture"""
        try:
            self.cap = cv2.VideoCapture(self.camera_id)
            
            if not self.cap.isOpened():
                raise Exception(f"Cannot open camera {self.camera_id}")
            
            # Set resolution
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            
            logger.info(f"Camera {self.camera_id} initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Camera initialization failed: {e}")
            return False
    
    def read_frame(self):
        """
        Read a frame from camera
        
        Returns:
            tuple: (success, frame) where success is bool and frame is numpy array
        """
        if self.cap is None or not self.cap.isOpened():
            logger.error("Camera not initialized")
            return False, None
        
        ret, frame = self.cap.read()
        
        if not ret:
            logger.warning("Failed to read frame")
            return False, None
        
        return True, frame
    
    def release(self):
        """Release camera resources"""
        if self.cap is not None:
            self.cap.release()
            logger.info("Camera released")
    
    def __del__(self):
        """Cleanup on deletion"""
        self.release()


# Test function
if __name__ == "__main__":
    camera = CameraHandler()
    if camera.initialize():
        print("Camera working! Press 'q' to quit")
        
        while True:
            ret, frame = camera.read_frame()
            if ret:
                cv2.imshow("Camera Test", frame)
                
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        camera.release()
        cv2.destroyAllWindows()
    else:
        print("Camera initialization failed")