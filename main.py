import cv2
import time
import requests
import logging
from camera import CameraHandler
from detector import ObjectDetector
from ocr import TextRecognizer
from formatter import ContextFormatter
from tts_multilang import MultiLanguageTTS as TextToSpeech

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PerceptaVisionPipeline:
    """
    Main orchestrator for Percepta vision system
    Coordinates all modules and manages the processing loop
    """
    
    def __init__(self, backend_url="http://localhost:5000"):
        """
        Initialize vision pipeline
        
        Args:
            backend_url: URL of Flask backend API
        """
        self.backend_url = backend_url
        self.current_language = 'en'  # Default language
        
        # Initialize modules
        self.camera = CameraHandler()
        self.detector = ObjectDetector(confidence_threshold=0.5)
        self.ocr = TextRecognizer()
        self.formatter = ContextFormatter(cooldown_seconds=5)
        self.tts = TextToSpeech(rate=160, use_gtts_for_hindi=True)
        
        # Processing control
        self.is_running = False
        self.frame_count = 0
        
        # Timing control
        self.ocr_interval = 30  # Run OCR every N frames (OCR is slow)
        self.detection_interval = 3  # Run detection every N frames
        
        logger.info("Percepta Vision Pipeline initialized")
    
    def initialize_all(self):
        """Initialize all modules"""
        logger.info("Initializing all modules...")
        
        success = True
        
        if not self.camera.initialize():
            logger.error("Camera initialization failed")
            success = False
        
        if not self.detector.load_model():
            logger.error("Detector initialization failed")
            success = False
        
        if not self.ocr.load_model():
            logger.error("OCR initialization failed")
            success = False
        
        if not self.tts.initialize():
            logger.error("TTS initialization failed")
            success = False
        
        if success:
            logger.info("All modules initialized successfully")
        
        return success
    
    def get_current_language(self):
        """Fetch current language from backend"""
        try:
            response = requests.get(
                f"{self.backend_url}/get_language",
                timeout=1
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('language', 'en')
        except:
            pass
        
        return self.current_language
    
    def process_frame(self, frame):
        """
        Process a single frame through the pipeline
        
        Args:
            frame: OpenCV image frame
            
        Returns:
            dict: Processing results
        """
        self.frame_count += 1
        
        # Check for language changes every 30 frames
        if self.frame_count % 30 == 0:
            new_language = self.get_current_language()
            if new_language != self.current_language:
                logger.info(f"Language changed from {self.current_language} to {new_language}")
                self.current_language = new_language
        
        objects = []
        texts = []
        
        # Run object detection (throttled)
        if self.frame_count % self.detection_interval == 0:
            objects = self.detector.detect(frame)
            if objects:
                logger.info(f"Detected {len(objects)} objects: {[obj['class'] for obj in objects[:3]]}")
        
        # Run OCR (heavily throttled - it's slow)
        if self.frame_count % self.ocr_interval == 0:
            ocr_results = self.ocr.recognize_text(frame, confidence_threshold=0.6)
            texts = self.ocr.get_all_text(ocr_results)
            if texts:
                logger.info(f"Detected {len(texts)} text(s): {texts}")
        
        # Format context and generate narration
        result = self.formatter.format_context(objects, texts, language=self.current_language)
        
        # Speak if there's something to say
        if result['speech']:
            logger.info(f"🔊 SPEAKING ({self.current_language}): {result['speech']}")
            
            # Pass language to TTS
            if hasattr(self.tts, 'speak') and 'language' in self.tts.speak.__code__.co_varnames:
                # New multi-language TTS
                speech_success = self.tts.speak(result['speech'], language=self.current_language, blocking=False)
            else:
                # Old TTS (no language support)
                speech_success = self.tts.speak(result['speech'], blocking=False)
                
            if not speech_success:
                logger.warning("TTS failed to speak")
        
        # Add language to result
        result['language'] = self.current_language
        
        return result
    
    def send_to_backend(self, data):
        """
        Send processing results to backend API
        
        Args:
            data: Result dictionary to send
        """
        try:
            response = requests.post(
                f"{self.backend_url}/update",
                json=data,
                timeout=1
            )
            
            if response.status_code != 200:
                logger.warning(f"Backend update failed: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            logger.debug(f"Backend connection error: {e}")
    
    def run(self, show_preview=True):
        """
        Main processing loop
        
        Args:
            show_preview: Show OpenCV window with video preview
        """
        logger.info("Starting Percepta vision pipeline...")
        self.is_running = True
        
        # Initial announcement
        self.tts.speak("Percepta activated. Vision assistance ready.", blocking=True)
        
        # Test if preview is possible
        preview_available = False
        if show_preview:
            try:
                # Test if cv2.imshow works
                test_frame = cv2.imread('test.jpg') if False else None
                if test_frame is not None:
                    cv2.imshow("Test", test_frame)
                    cv2.destroyWindow("Test")
                preview_available = True
            except:
                logger.warning("OpenCV GUI not available. Running in headless mode.")
                logger.info("Use the web dashboard at http://localhost:5000 to monitor")
                preview_available = False
        
        try:
            while self.is_running:
                # Read frame from camera
                ret, frame = self.camera.read_frame()
                
                if not ret:
                    logger.error("Failed to read frame")
                    break
                
                # Process frame
                result = self.process_frame(frame)
                
                # Send to backend
                if result['objects'] or result['text']:
                    self.send_to_backend(result)
                
                # Show preview window (if available)
                if show_preview and preview_available:
                    try:
                        # Draw detection info on frame
                        display_frame = frame.copy()
                        
                        # Add text overlay
                        if result['speech']:
                            cv2.putText(display_frame, result['speech'][:50], 
                                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 
                                       0.7, (0, 255, 0), 2)
                        
                        cv2.imshow("Percepta Vision", display_frame)
                        
                        # Check for quit key
                        if cv2.waitKey(1) & 0xFF == ord('q'):
                            logger.info("Quit key pressed")
                            break
                    except cv2.error:
                        logger.warning("Preview window error. Continuing in headless mode.")
                        preview_available = False
                else:
                    # Headless mode - just wait a bit
                    time.sleep(0.03)  # ~30 FPS
                
                # Check for keyboard interrupt in headless mode
                # (Ctrl+C will be caught by KeyboardInterrupt)
        
        except KeyboardInterrupt:
            logger.info("Interrupted by user")
        
        finally:
            self.stop()
    
    def stop(self):
        """Stop the pipeline and cleanup"""
        logger.info("Stopping Percepta...")
        self.is_running = False
        
        # Cleanup modules
        self.camera.release()
        self.tts.cleanup()
        
        try:
            cv2.destroyAllWindows()
        except:
            pass  # Ignore if windows weren't created
        
        logger.info("Percepta stopped")


# Main execution
if __name__ == "__main__":
    print("=" * 50)
    print("PERCEPTA - AI Vision Assistant")
    print("=" * 50)
    print("\nInitializing system...")
    
    pipeline = PerceptaVisionPipeline()
    
    if pipeline.initialize_all():
        print("\n✓ All modules ready")
        print("\nStarting vision pipeline...")
        print("\nIMPORTANT: If you see OpenCV GUI errors, the system will run in headless mode.")
        print("Monitor the system via the web dashboard at: http://localhost:5000")
        print("\nPress Ctrl+C to quit\n")
        
        try:
            pipeline.run(show_preview=True)
        except Exception as e:
            logger.error(f"Pipeline error: {e}", exc_info=True)
    else:
        print("\n✗ Initialization failed")
        print("Please check the logs for details")
    
    print("\nPercepta shutdown complete")