import pyttsx3
import logging
import threading
import queue
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TextToSpeech:
    """
    Offline text-to-speech engine using pyttsx3
    Windows-compatible version with engine re-initialization workaround
    """
    
    def __init__(self, rate=150, volume=1.0, voice_index=0):
        """
        Initialize TTS engine
        
        Args:
            rate: Speech rate (words per minute)
            volume: Volume level (0.0 to 1.0)
            voice_index: Voice selection index
        """
        self.rate = rate
        self.volume = volume
        self.voice_index = voice_index
        self.is_speaking = False
        self._speech_queue = queue.Queue()
        self._worker_thread = None
        self._stop_worker = False
        self._available_voices = []
        
    def initialize(self):
        """Initialize TTS system"""
        try:
            logger.info("Initializing TTS engine...")
            
            # Get available voices using temporary engine
            try:
                temp_engine = pyttsx3.init()
                self._available_voices = temp_engine.getProperty('voices')
                if self._available_voices and len(self._available_voices) > self.voice_index:
                    logger.info(f"Using voice: {self._available_voices[self.voice_index].name}")
                del temp_engine
                time.sleep(0.2)  # Let it cleanup
            except Exception as e:
                logger.warning(f"Could not get voices: {e}")
            
            # Start worker thread
            self._stop_worker = False
            self._worker_thread = threading.Thread(target=self._speech_worker, daemon=True)
            self._worker_thread.start()
            
            logger.info("TTS engine initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"TTS initialization failed: {e}")
            return False
    
    def _create_engine(self):
        """Create and configure a new engine instance (Windows workaround)"""
        try:
            engine = pyttsx3.init()
            engine.setProperty('rate', self.rate)
            engine.setProperty('volume', self.volume)
            
            # Set voice if available
            if self._available_voices and len(self._available_voices) > self.voice_index:
                try:
                    engine.setProperty('voice', self._available_voices[self.voice_index].id)
                except Exception as e:
                    logger.warning(f"Could not set voice: {e}")
            
            return engine
        except Exception as e:
            logger.error(f"Failed to create engine: {e}")
            return None
    
    def _speech_worker(self):
        """
        Background worker thread that processes speech queue
        Creates a FRESH engine for each speech (Windows compatibility fix)
        """
        while not self._stop_worker:
            try:
                # Get text from queue with timeout
                text = self._speech_queue.get(timeout=0.5)
                
                if text is None:  # Poison pill to stop worker
                    break
                
                # Mark as speaking
                self.is_speaking = True
                
                try:
                    logger.info(f"🔊 Speaking: {text}")
                    
                    # Create fresh engine for this speech (Windows fix)
                    engine = self._create_engine()
                    
                    if engine:
                        engine.say(text)
                        engine.runAndWait()
                        
                        # Cleanup this engine instance
                        try:
                            engine.stop()
                            del engine
                        except:
                            pass
                        
                        # Small delay to ensure cleanup
                        time.sleep(0.3)
                    else:
                        logger.error("Failed to create engine for speech")
                        
                except Exception as e:
                    logger.error(f"Speech error: {e}")
                finally:
                    self.is_speaking = False
                    
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Worker thread error: {e}")
                self.is_speaking = False
    
    def speak(self, text, blocking=False):
        """
        Speak the given text
        
        Args:
            text: Text to speak
            blocking: If True, wait for speech to complete
            
        Returns:
            bool: True if speech queued successfully
        """
        if not text or len(text.strip()) == 0:
            return False
        
        try:
            # Clear queue if it's getting too long (avoid buildup)
            queue_size = self._speech_queue.qsize()
            if queue_size > 2:
                logger.warning(f"Speech queue has {queue_size} items, clearing old items")
                while not self._speech_queue.empty():
                    try:
                        self._speech_queue.get_nowait()
                    except queue.Empty:
                        break
            
            # Add to queue
            logger.debug(f"Queueing speech: {text}")
            self._speech_queue.put(text)
            
            # If blocking, wait for completion
            if blocking:
                start_time = time.time()
                timeout = 30  # 30 second timeout
                
                while (self.is_speaking or not self._speech_queue.empty()) and (time.time() - start_time < timeout):
                    time.sleep(0.1)
                
                if time.time() - start_time >= timeout:
                    logger.warning("Speech blocking timeout")
            
            return True
            
        except Exception as e:
            logger.error(f"Error queueing speech: {e}")
            return False
    
    def stop(self):
        """Stop current speech and clear queue"""
        # Clear the queue
        while not self._speech_queue.empty():
            try:
                self._speech_queue.get_nowait()
            except queue.Empty:
                break
        self.is_speaking = False
        logger.info("Speech stopped and queue cleared")
    
    def set_rate(self, rate):
        """Change speech rate"""
        self.rate = rate
        logger.info(f"Speech rate set to {rate}")
    
    def set_volume(self, volume):
        """Change volume"""
        self.volume = max(0.0, min(1.0, volume))
        logger.info(f"Volume set to {self.volume}")
    
    def list_voices(self):
        """List available voices"""
        return self._available_voices
    
    def cleanup(self):
        """Cleanup TTS engine"""
        try:
            logger.info("Cleaning up TTS engine...")
            
            # Stop worker thread
            self._stop_worker = True
            
            # Clear queue
            self.stop()
            
            # Send poison pill
            try:
                self._speech_queue.put(None)
            except:
                pass
            
            # Wait for worker thread
            if self._worker_thread and self._worker_thread.is_alive():
                self._worker_thread.join(timeout=2.0)
            
            logger.info("TTS engine cleaned up")
        except Exception as e:
            logger.error(f"Cleanup error: {e}")


# Test function
if __name__ == "__main__":
    import time
    
    print("\n=== TTS Test (Windows Compatible) ===\n")
    
    tts = TextToSpeech(rate=150)
    
    if tts.initialize():
        print("✓ TTS initialized\n")
        
        test_phrases = [
            "Percepta activated. Vision assistance ready.",
            "Person detected ahead.",
            "Warning. Stairs detected.",
            "Sign reads: Exit.",
            "Caution. Vehicle detected."
        ]
        
        for i, phrase in enumerate(test_phrases, 1):
            print(f"[{i}] Speaking: {phrase}")
            tts.speak(phrase, blocking=True)
            print(f"    ✓ Complete\n")
            time.sleep(0.5)  # Brief pause between phrases
        
        print("✓ All test phrases complete!")
        
        tts.cleanup()
        print("\n✓ Test finished")
    else:
        print("✗ Failed to initialize TTS")


# Test function
if __name__ == "__main__":
    import time
    
    tts = TextToSpeech(rate=160)
    
    if tts.initialize():
        print("\n=== TTS Test ===")
        
        # List available voices
        print("\nAvailable voices:")
        tts.list_voices()
        
        # Test 1: Simple speech
        print("\nTest 1: Speaking...")
        tts.speak("Hello, this is Percepta, your vision assistant.", blocking=True)
        
        # Test 2: Non-blocking speech
        print("\nTest 2: Non-blocking speech...")
        tts.speak("Detected person ahead. Text reads: Exit.", blocking=False)
        
        # Wait for speech to complete
        time.sleep(3)
        
        # Test 3: Context-aware narration
        print("\nTest 3: Realistic scenario...")
        tts.speak("Detected 2 persons and chair. Text reads: Emergency Exit.", blocking=True)
        
        # Test 4: Rate adjustment
        print("\nTest 4: Faster speech...")
        tts.set_rate(200)
        tts.speak("This is faster speech.", blocking=True)
        
        tts.cleanup()
        print("\nTTS test complete")
    else:
        print("Failed to initialize TTS")