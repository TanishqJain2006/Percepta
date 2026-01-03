import logging
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ContextFormatter:
    """
    The brain of Percepta - generates contextual, human-readable narration
    from raw detection data with multi-language support
    """
    
    # Translation dictionaries
    TRANSLATIONS = {
        'en': {
            'caution': 'Caution',
            'warning': 'Warning',
            'detected': 'detected',
            'ahead': 'ahead',
            'sign_reads': 'Sign reads',
            'text_reads': 'Text reads',
            'stairs': 'Stairs',
            'door': 'Door',
            'person': 'Person',
            'car': 'Vehicle',
            'truck': 'Truck',
            'bus': 'Bus',
            'bicycle': 'Bicycle',
            'motorcycle': 'Motorcycle',
            'chair': 'chair',
            'couch': 'couch',
            'bench': 'bench',
            'stop sign': 'stop sign',
            'traffic light': 'traffic light',
            'fire hydrant': 'fire hydrant',
            'handbag': 'handbag',
            'backpack': 'backpack',
            'umbrella': 'umbrella',
            'bottle': 'bottle',
            'cup': 'cup',
            'knife': 'knife',
            'cell phone': 'cell phone',
            'laptop': 'laptop',
            'dog': 'dog',
            'cat': 'cat',
        },
        'hi': {
            'caution': 'सावधान',
            'warning': 'चेतावनी',
            'detected': 'का पता चला',
            'ahead': 'सामने',
            'sign_reads': 'साइन पर लिखा है',
            'text_reads': 'टेक्स्ट पर लिखा है',
            'stairs': 'सीढ़ियाँ',
            'door': 'दरवाज़ा',
            'person': 'व्यक्ति',
            'car': 'गाड़ी',
            'truck': 'ट्रक',
            'bus': 'बस',
            'bicycle': 'साइकिल',
            'motorcycle': 'मोटरसाइकिल',
            'chair': 'कुर्सी',
            'couch': 'सोफा',
            'bench': 'बेंच',
            'stop sign': 'स्टॉप साइन',
            'traffic light': 'ट्रैफ़िक लाइट',
            'fire hydrant': 'फायर हाइड्रेंट',
            'handbag': 'हैंडबैग',
            'backpack': 'बैकपैक',
            'umbrella': 'छाता',
            'bottle': 'बोतल',
            'cup': 'कप',
            'knife': 'चाकू',
            'cell phone': 'मोबाइल फोन',
            'laptop': 'लैपटॉप',
            'dog': 'कुत्ता',
            'cat': 'बिल्ली',
        }
    }
    
    def __init__(self, cooldown_seconds=5):
        """
        Initialize formatter
        
        Args:
            cooldown_seconds: Minimum seconds between similar announcements
        """
        self.cooldown_seconds = cooldown_seconds
        self.last_announcements = {}  # Track what was last said and when
    
    def translate(self, key, language='en'):
        """Get translation for a key"""
        translations = self.TRANSLATIONS.get(language, self.TRANSLATIONS['en'])
        return translations.get(key, key)
        
    def format_context(self, objects, texts, language='en'):
        """
        Generate contextual narration from detections
        
        Args:
            objects: List of object detections from detector
            texts: List of text strings from OCR
            language: Language code ('en' or 'hi')
            
        Returns:
            dict: {
                'objects': list of object summaries,
                'text': list of detected text,
                'speech': string to be spoken
            }
        """
        # Filter objects by priority
        priority_objects = self._get_priority_objects(objects)
        
        # Filter important text
        important_texts = self._filter_important_texts(texts)
        
        # Generate speech narration
        speech = self._generate_speech(priority_objects, important_texts, language)
        
        # Check cooldown - avoid repeating same info too quickly
        if not self._check_cooldown(speech):
            speech = None
        
        return {
            'objects': [self._format_object(obj) for obj in priority_objects[:5]],
            'text': important_texts,
            'speech': speech
        }
    
    def _get_priority_objects(self, objects):
        """
        Filter objects intelligently based on urgency
        Only returns the MOST CRITICAL objects that need immediate attention
        """
        if not objects:
            return []
        
        # Objects are already sorted by urgency from detector
        # Get the most urgent object
        most_urgent = objects[0]
        most_urgent_score = most_urgent.get('urgency', 0)
        
        # Only include objects with urgency within 50% of the most urgent
        # This prevents announcing less important objects
        urgency_threshold = most_urgent_score * 0.5
        
        critical_objects = []
        for obj in objects:
            # Must have significant urgency AND high enough priority
            if obj.get('urgency', 0) >= urgency_threshold and obj['priority'] >= 2:
                critical_objects.append(obj)
        
        # Limit to top 3 most urgent to avoid overwhelming the user
        return critical_objects[:3]
    
    def _filter_important_texts(self, texts):
        """Filter for important text only"""
        important_keywords = [
            'exit', 'entrance', 'danger', 'warning', 'caution',
            'stop', 'stairs', 'elevator', 'restroom', 'emergency',
            'no entry', 'room', 'floor', 'open', 'closed'
        ]
        
        important = []
        for text in texts:
            text_lower = text.lower()
            if any(keyword in text_lower for keyword in important_keywords):
                important.append(text)
            elif text.isupper() and len(text) <= 20:
                important.append(text)
        
        return important[:3]  # Max 3 texts to avoid overload
    
    def _format_object(self, obj):
        """Format object for structured output"""
        return {
            'class': obj['class'],
            'confidence': obj['confidence'],
            'priority': obj['priority']
        }
    
    def _generate_speech(self, objects, texts, language='en'):
        """
        Generate natural speech narration with INTELLIGENT prioritization
        Focuses on the MOST CRITICAL hazard first
        
        This is the core "speak what matters most" logic
        """
        if not objects and not texts:
            return None
        
        speech_parts = []
        
        # Handle objects with INTELLIGENT prioritization
        if objects:
            # The first object is the MOST URGENT (sorted by detector)
            most_urgent = objects[0]
            urgency_score = most_urgent.get('urgency', 0)
            distance = most_urgent.get('distance', 1.0)
            
            # Determine if this is CRITICAL (requires immediate attention)
            is_critical = urgency_score >= 5.0  # High urgency threshold
            is_very_close = distance < 0.3  # Very close to user
            
            # Generate warning based on urgency and distance
            class_name = most_urgent['class']
            
            if language == 'hi':
                # Hindi warnings
                if is_critical or is_very_close:
                    # CRITICAL WARNING - very urgent tone
                    if class_name == 'stairs':
                        speech_parts.append(f"{self.translate('caution', language)}! {self.translate('caution', language)}! {self.translate('stairs', language)} {self.translate('detected', language)}!")
                    elif class_name in ['car', 'truck', 'bus', 'train']:
                        vehicle = self.translate(class_name, language)
                        speech_parts.append(f"{self.translate('warning', language)}! {vehicle} {self.translate('detected', language)}!")
                    elif class_name == 'person':
                        speech_parts.append(f"{self.translate('person', language)} {self.translate('ahead', language)}")
                    elif class_name == 'door':
                        speech_parts.append(f"{self.translate('door', language)} {self.translate('ahead', language)}")
                    else:
                        translated = self.translate(class_name, language)
                        speech_parts.append(f"{self.translate('caution', language)}! {translated} {self.translate('detected', language)}")
                else:
                    # Normal priority announcement
                    translated = self.translate(class_name, language)
                    if class_name in ['person', 'chair', 'table']:
                        speech_parts.append(f"{translated} {self.translate('detected', language)}")
                    else:
                        speech_parts.append(f"{translated} {self.translate('ahead', language)}")
            else:
                # English warnings
                if is_critical or is_very_close:
                    # CRITICAL WARNING - very urgent tone
                    if class_name == 'stairs':
                        speech_parts.append("CAUTION! STAIRS AHEAD!")
                    elif class_name in ['car', 'truck', 'bus', 'train']:
                        speech_parts.append(f"WARNING! {class_name.upper()} DETECTED!")
                    elif class_name == 'person':
                        speech_parts.append("Person directly ahead")
                    elif class_name == 'door':
                        speech_parts.append("Door immediately ahead")
                    else:
                        speech_parts.append(f"Caution! {class_name} detected")
                else:
                    # Normal priority announcement
                    if class_name == 'person':
                        speech_parts.append("Person ahead")
                    elif class_name == 'door':
                        speech_parts.append("Door ahead")
                    elif class_name in ['chair', 'table', 'bench']:
                        speech_parts.append(f"{class_name.capitalize()} detected")
                    else:
                        speech_parts.append(f"{class_name.capitalize()} ahead")
            
            # Only add other objects if they're also urgent
            # This prevents information overload
            if len(objects) > 1:
                other_urgent = [obj for obj in objects[1:3] if obj.get('urgency', 0) >= urgency_score * 0.7]
                
                if other_urgent:
                    for obj in other_urgent:
                        obj_class = obj['class']
                        if language == 'hi':
                            translated = self.translate(obj_class, language)
                            speech_parts.append(f"{translated} {self.translate('detected', language)}")
                        else:
                            speech_parts.append(f"{obj_class} detected")
        
        # Handle text with emphasis on important signs
        if texts:
            important_signs = ['exit', 'emergency', 'danger', 'warning', 'caution', 'stop']
            
            is_important = any(keyword in text.lower() for text in texts for keyword in important_signs)
            
            if language == 'hi':
                text_intro = self.translate('sign_reads' if is_important else 'text_reads', language)
            else:
                text_intro = "Sign reads" if is_important else "Text reads"
            
            # Only announce the first 2 texts to avoid overload
            texts_to_announce = texts[:2]
            
            if len(texts_to_announce) == 1:
                speech_parts.append(f"{text_intro}: {texts_to_announce[0]}")
            else:
                speech_parts.append(f"{text_intro}: {', '.join(texts_to_announce)}")
        
        # Combine parts with appropriate pauses
        if speech_parts:
            return ". ".join(speech_parts) + "."
        
        return None
    
    def _check_cooldown(self, speech):
        """
        Check if similar announcement was made recently
        
        Args:
            speech: Speech text to check
            
        Returns:
            bool: True if OK to announce, False if in cooldown
        """
        if speech is None:
            return False
        
        # Create a signature for this speech (simplified)
        # Extract key words (object types)
        signature = self._create_signature(speech)
        
        current_time = datetime.now()
        
        if signature in self.last_announcements:
            last_time = self.last_announcements[signature]
            time_diff = (current_time - last_time).total_seconds()
            
            if time_diff < self.cooldown_seconds:
                logger.debug(f"Cooldown active for: {signature}")
                return False
        
        # Update last announcement time
        self.last_announcements[signature] = current_time
        
        # Clean old entries (older than 2x cooldown)
        self._cleanup_old_announcements(current_time)
        
        return True
    
    def _create_signature(self, speech):
        """Create a simple signature from speech for cooldown checking"""
        # Extract main words (simplified approach)
        words = speech.lower().split()
        # Remove common words
        stop_words = {'detected', 'text', 'reads', 'and', 'the', 'a', 'an'}
        key_words = [w.strip('.,!?') for w in words if w not in stop_words]
        return ' '.join(sorted(key_words[:5]))  # Use first 5 key words
    
    def _cleanup_old_announcements(self, current_time):
        """Remove old announcement records"""
        cutoff_time = current_time - timedelta(seconds=self.cooldown_seconds * 2)
        
        to_remove = []
        for signature, timestamp in self.last_announcements.items():
            if timestamp < cutoff_time:
                to_remove.append(signature)
        
        for signature in to_remove:
            del self.last_announcements[signature]
    
    def reset_cooldowns(self):
        """Reset all cooldowns (useful for testing)"""
        self.last_announcements.clear()
        logger.info("Cooldowns reset")


# Test function
if __name__ == "__main__":
    formatter = ContextFormatter(cooldown_seconds=3)
    
    # Test case 1: Objects only
    objects = [
        {'class': 'person', 'confidence': 0.87, 'priority': 3},
        {'class': 'person', 'confidence': 0.82, 'priority': 3},
        {'class': 'chair', 'confidence': 0.75, 'priority': 2},
    ]
    
    result = formatter.format_context(objects, [])
    print("Test 1 - Objects only:")
    print(f"  Speech: {result['speech']}\n")
    
    # Test case 2: Text only
    texts = ['EXIT', 'EMERGENCY']
    result = formatter.format_context([], texts)
    print("Test 2 - Text only:")
    print(f"  Speech: {result['speech']}\n")
    
    # Test case 3: Both
    result = formatter.format_context(objects, texts)
    print("Test 3 - Objects and text:")
    print(f"  Speech: {result['speech']}\n")
    
    # Test case 4: Cooldown test
    print("Test 4 - Cooldown (should block 2nd call):")
    result1 = formatter.format_context(objects, [])
    print(f"  Call 1: {result1['speech']}")
    
    result2 = formatter.format_context(objects, [])
    print(f"  Call 2 (immediate): {result2['speech']}")
    
    import time
    time.sleep(3.5)
    
    result3 = formatter.format_context(objects, [])
    print(f"  Call 3 (after cooldown): {result3['speech']}")