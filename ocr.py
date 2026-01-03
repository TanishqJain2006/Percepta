import easyocr
import logging
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TextRecognizer:
    """OCR-based text recognition for signs and labels"""
    
    def __init__(self, languages=['en'], gpu=False):
        """
        Initialize OCR reader
        
        Args:
            languages: List of language codes to recognize
            gpu: Use GPU acceleration if available
        """
        self.languages = languages
        self.gpu = gpu
        self.reader = None
        
    def load_model(self):
        """Load EasyOCR model"""
        try:
            logger.info(f"Loading OCR model for languages: {self.languages}")
            self.reader = easyocr.Reader(self.languages, gpu=self.gpu)
            logger.info("OCR model loaded successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to load OCR model: {e}")
            return False
    
    def recognize_text(self, frame, confidence_threshold=0.5):
        """
        Recognize text in frame
        
        Args:
            frame: OpenCV image (numpy array)
            confidence_threshold: Minimum confidence for text detection
            
        Returns:
            list: Detected text strings with format:
                  [{
                      'text': str,
                      'confidence': float,
                      'bbox': [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
                  }]
        """
        if self.reader is None:
            logger.error("OCR reader not loaded")
            return []
        
        try:
            # Run OCR
            results = self.reader.readtext(frame)
            
            detected_texts = []
            
            for detection in results:
                bbox, text, confidence = detection
                
                if confidence < confidence_threshold:
                    continue
                
                # Clean text
                text = text.strip()
                
                if len(text) == 0:
                    continue
                
                detected_texts.append({
                    'text': text,
                    'confidence': round(confidence, 2),
                    'bbox': bbox
                })
            
            return detected_texts
            
        except Exception as e:
            logger.error(f"OCR error: {e}")
            return []
    
    def get_all_text(self, detections):
        """
        Extract just the text strings from detections
        
        Args:
            detections: List of text detections
            
        Returns:
            list: List of text strings
        """
        return [det['text'] for det in detections]
    
    def filter_important_text(self, texts):
        """
        Filter for important/safety-related text
        
        Args:
            texts: List of text strings
            
        Returns:
            list: Filtered important texts
        """
        # Keywords that indicate important information
        important_keywords = [
            'exit', 'entrance', 'danger', 'warning', 'caution',
            'stop', 'stairs', 'elevator', 'restroom', 'emergency',
            'no entry', 'authorized', 'room', 'floor', 'level',
            'open', 'closed', 'push', 'pull', 'wet floor'
        ]
        
        important_texts = []
        
        for text in texts:
            text_lower = text.lower()
            
            # Check if text contains important keywords
            if any(keyword in text_lower for keyword in important_keywords):
                important_texts.append(text)
            # Also include short all-caps text (likely signs)
            elif text.isupper() and len(text) <= 20:
                important_texts.append(text)
        
        return important_texts


# Test function
if __name__ == "__main__":
    import cv2
    
    recognizer = TextRecognizer()
    
    if recognizer.load_model():
        # Test with webcam
        cap = cv2.VideoCapture(0)
        
        print("Running OCR. Press 'q' to quit, 's' to scan")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            cv2.imshow("OCR Test - Press 's' to scan", frame)
            
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('q'):
                break
            elif key == ord('s'):
                print("Scanning for text...")
                detections = recognizer.recognize_text(frame)
                
                if detections:
                    print(f"\nFound {len(detections)} text(s):")
                    for det in detections:
                        print(f"  - {det['text']} (confidence: {det['confidence']})")
                    
                    all_texts = recognizer.get_all_text(detections)
                    important = recognizer.filter_important_text(all_texts)
                    
                    if important:
                        print(f"\nImportant text: {important}")
                else:
                    print("No text detected")
        
        cap.release()
        cv2.destroyAllWindows()
    else:
        print("Failed to load OCR model")