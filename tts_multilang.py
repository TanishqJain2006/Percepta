"""
Enhanced TTS with Google TTS fallback for better Hindi support
"""
import pyttsx3
import logging
import threading
import queue
import time

# Optional: Google TTS (requires internet)
try:
    from gtts import gTTS
    import os
    import tempfile
    from playsound import playsound
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MultiLanguageTTS:
    """
    Enhanced TTS with multiple backends:
    1. pyttsx3 (offline, fast, limited Hindi)
    2. gTTS (online, slower, excellent Hindi)
    """
    
    def __init__(self, rate=150, volume=1.0, voice_index=0, use_gtts_for_hindi=False):
        """
        Initialize TTS engine
        
        Args:
            rate: Speech rate (pyttsx3 only)
            volume: Volume level (pyttsx3 only)
            voice_index: Voice selection index (pyttsx3 only)
            use_gtts_for_hindi: Use Google TTS for Hindi (requires internet)
        """
        self.rate = rate
        self.volume = volume
        self.voice_index = voice_index
        self.use_gtts_for_hindi = use_gtts_for_hindi and GTTS_AVAILABLE
        self.is_speaking = False
        self._speech_queue = queue.Queue()
        self._worker_thread = None
        self._stop_worker = False
        self._available_voices = []
        self._temp_files = []
        
        if self.use_gtts_for_hindi:
            logger.info("Google TTS enabled for Hindi")
        elif not GTTS_AVAILABLE:
            logger.warning("Google TTS not available. Install: pip install gtts playsound")
        
    def initialize(self):
        """Initialize TTS system"""
        try:
            logger.info("Initializing multi-language TTS...")
            
            # Get available pyttsx3 voices
            try:
                temp_engine = pyttsx3.init()
                self._available_voices = temp_engine.getProperty('voices')
                if self._available_voices and len(self._available_voices) > self.voice_index:
                    logger.info(f"Using voice: {self._available_voices[self.voice_index].name}")
                del temp_engine
                time.sleep(0.2)
            except Exception as e:
                logger.warning(f"Could not get pyttsx3 voices: {e}")
            
            # Start worker thread
            self._stop_worker = False
            self._worker_thread = threading.Thread(target=self._speech_worker, daemon=True)
            self._worker_thread.start()
            
            logger.info("TTS initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"TTS initialization failed: {e}")
            return False
    
    def _create_pyttsx3_engine(self):
        """Create pyttsx3 engine"""
        try:
            engine = pyttsx3.init()
            engine.setProperty('rate', self.rate)
            engine.setProperty('volume', self.volume)
            
            if self._available_voices and len(self._available_voices) > self.voice_index:
                try:
                    engine.setProperty('voice', self._available_voices[self.voice_index].id)
                except Exception as e:
                    logger.warning(f"Could not set voice: {e}")
            
            return engine
        except Exception as e:
            logger.error(f"Failed to create pyttsx3 engine: {e}")
            return None
    
    def _speak_with_gtts(self, text, language='hi'):
        """Speak using Google TTS (online)"""
        try:
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
            temp_file.close()
            self._temp_files.append(temp_file.name)
            
            # Generate speech
            tts = gTTS(text=text, lang=language, slow=False)
            tts.save(temp_file.name)
            
            # Play audio
            playsound(temp_file.name)
            
            # Cleanup
            try:
                os.unlink(temp_file.name)
                self._temp_files.remove(temp_file.name)
            except:
                pass
            
            return True
            
        except Exception as e:
            logger.error(f"Google TTS error: {e}")
            return False
    
    def _speak_with_pyttsx3(self, text):
        """Speak using pyttsx3 (offline)"""
        try:
            engine = self._create_pyttsx3_engine()
            
            if engine:
                engine.say(text)
                engine.runAndWait()
                
                # Cleanup
                try:
                    engine.stop()
                    del engine
                except:
                    pass
                
                time.sleep(0.3)
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"pyttsx3 error: {e}")
            return False
    
    def _speech_worker(self):
        """Background worker thread"""
        while not self._stop_worker:
            try:
                # Get speech request from queue
                item = self._speech_queue.get(timeout=0.5)
                
                if item is None:  # Poison pill
                    break
                
                text, language = item
                
                self.is_speaking = True
                
                try:
                    logger.info(f"🔊 Speaking ({language}): {text}")
                    
                    # Choose TTS backend
                    if language == 'hi' and self.use_gtts_for_hindi:
                        # Use Google TTS for Hindi
                        success = self._speak_with_gtts(text, language='hi')
                        if not success:
                            logger.warning("Google TTS failed, falling back to pyttsx3")
                            self._speak_with_pyttsx3(text)
                    else:
                        # Use pyttsx3 for English or if gTTS not available
                        self._speak_with_pyttsx3(text)
                    
                except Exception as e:
                    logger.error(f"Speech error: {e}")
                finally:
                    self.is_speaking = False
                    
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Worker thread error: {e}")
                self.is_speaking = False
    
    def speak(self, text, language='en', blocking=False):
        """
        Speak the given text
        
        Args:
            text: Text to speak
            language: Language code ('en' or 'hi')
            blocking: If True, wait for speech to complete
            
        Returns:
            bool: True if speech queued successfully
        """
        if not text or len(text.strip()) == 0:
            return False
        
        try:
            # Clear queue if too long
            queue_size = self._speech_queue.qsize()
            if queue_size > 2:
                logger.warning(f"Speech queue has {queue_size} items, clearing")
                while not self._speech_queue.empty():
                    try:
                        self._speech_queue.get_nowait()
                    except queue.Empty:
                        break
            
            # Add to queue
            logger.debug(f"Queueing speech ({language}): {text}")
            self._speech_queue.put((text, language))
            
            # Wait if blocking
            if blocking:
                start_time = time.time()
                timeout = 30
                
                while (self.is_speaking or not self._speech_queue.empty()) and (time.time() - start_time < timeout):
                    time.sleep(0.1)
            
            return True
            
        except Exception as e:
            logger.error(f"Error queueing speech: {e}")
            return False
    
    def stop(self):
        """Stop speech and clear queue"""
        while not self._speech_queue.empty():
            try:
                self._speech_queue.get_nowait()
            except queue.Empty:
                break
        self.is_speaking = False
    
    def cleanup(self):
        """Cleanup TTS engine"""
        try:
            logger.info("Cleaning up TTS...")
            
            self._stop_worker = True
            self.stop()
            
            # Send poison pill
            try:
                self._speech_queue.put(None)
            except:
                pass
            
            # Wait for worker
            if self._worker_thread and self._worker_thread.is_alive():
                self._worker_thread.join(timeout=2.0)
            
            # Cleanup temp files
            for temp_file in self._temp_files:
                try:
                    os.unlink(temp_file)
                except:
                    pass
            
            logger.info("TTS cleaned up")
        except Exception as e:
            logger.error(f"Cleanup error: {e}")


# Test function
if __name__ == "__main__":
    print("\n=== Multi-Language TTS Test ===\n")
    
    # Test with Google TTS enabled
    tts = MultiLanguageTTS(rate=150, use_gtts_for_hindi=True)
    
    if tts.initialize():
        print("✓ TTS initialized\n")
        
        test_phrases = [
            ("Hello. This is an English test.", 'en'),
            ("नमस्ते। यह हिंदी परीक्षण है।", 'hi'),
            ("Person detected ahead.", 'en'),
            ("सावधान! सीढ़ियाँ का पता चला!", 'hi'),
        ]
        
        for text, lang in test_phrases:
            lang_name = "English" if lang == 'en' else "Hindi"
            print(f"Speaking ({lang_name}): {text}")
            tts.speak(text, language=lang, blocking=True)
            print(f"✓ Complete\n")
            time.sleep(0.5)
        
        print("✓ All tests complete!")
        
        tts.cleanup()
    else:
        print("✗ Failed to initialize TTS")