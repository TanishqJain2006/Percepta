from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import logging
from datetime import datetime
import io
from PIL import Image
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for web dashboard

# Store latest vision data
latest_data = {
    'objects': [],
    'text': [],
    'speech': None,
    'timestamp': None
}

# Store current language setting
current_language = 'en'  # Default: English

# Import vision modules (for mobile endpoint)
try:
    from detector import ObjectDetector
    from ocr import TextRecognizer
    from formatter import ContextFormatter
    
    # Initialize modules for mobile endpoint
    detector = ObjectDetector(confidence_threshold=0.5)
    ocr_reader = TextRecognizer()
    formatter = ContextFormatter(cooldown_seconds=5)
    
    # Load models
    detector.load_model()
    ocr_reader.load_model()
    
    VISION_AVAILABLE = True
    logger.info("Vision modules loaded for mobile endpoint")
except Exception as e:
    VISION_AVAILABLE = False
    logger.warning(f"Vision modules not available: {e}")


@app.route('/mobile')
def mobile():
    """Serve mobile web app"""
    # Embedded mobile HTML with improved camera compatibility
    return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <title>Percepta Mobile</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #fff;
            min-height: 100vh;
            padding: 15px;
        }
        .camera-container {
            position: relative;
            width: 100%;
            aspect-ratio: 4/3;
            background: #000;
            border-radius: 15px;
            overflow: hidden;
            margin-bottom: 15px;
        }
        #video { width: 100%; height: 100%; object-fit: cover; }
        #canvas { display: none; }
        .camera-overlay {
            position: absolute;
            inset: 0;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            background: rgba(0,0,0,0.7);
            padding: 20px;
            text-align: center;
        }
        .camera-overlay.hidden { display: none; }
        button {
            padding: 15px 25px;
            font-size: 1em;
            font-weight: 600;
            border: none;
            border-radius: 12px;
            cursor: pointer;
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
            margin: 5px;
        }
        .btn-primary { background: #10b981; color: white; }
        .btn-danger { background: #ef4444; color: white; }
        .btn-secondary { background: #fbbf24; color: #000; }
        .hidden { display: none; }
        .panel {
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 15px;
            margin-bottom: 15px;
        }
        .status { 
            padding: 10px; 
            background: rgba(255,255,255,0.2); 
            border-radius: 8px; 
            margin-bottom: 15px;
            font-size: 0.9em;
        }
        h1 { text-align: center; margin-bottom: 15px; font-size: 1.8em; }
        h3 { margin-bottom: 10px; }
        .error { background: rgba(239, 68, 68, 0.2); padding: 15px; border-radius: 10px; margin-bottom: 15px; }
        .info { font-size: 0.85em; opacity: 0.8; margin-top: 10px; }
        input[type="file"] { 
            padding: 10px; 
            background: rgba(255,255,255,0.2); 
            border: 1px solid rgba(255,255,255,0.3);
            border-radius: 8px;
            color: white;
            width: 100%;
            margin-bottom: 15px;
        }
    </style>
</head>
<body>
    <h1>👁️ Percepta Mobile</h1>
    
    <div class="camera-container">
        <video id="video" autoplay playsinline></video>
        <canvas id="canvas"></canvas>
        <div class="camera-overlay" id="overlay">
            <button class="btn-primary" onclick="startCamera()">📷 Start Camera</button>
            <div class="info" id="cameraInfo">Requesting camera access...</div>
        </div>
    </div>
    
    <!-- File upload fallback -->
    <div id="fileUpload" class="hidden">
        <input type="file" id="fileInput" accept="image/*" capture="environment" onchange="uploadImage()">
        <p style="font-size: 0.85em; opacity: 0.8; text-align: center;">
            Camera not available? Upload/take a photo instead
        </p>
    </div>
    
    <div>
        <button class="btn-primary" id="startBtn" onclick="start()">▶️ Start</button>
        <button class="btn-danger hidden" id="stopBtn" onclick="stop()">⏹️ Stop</button>
        <button class="btn-primary" onclick="capture()">📸 Capture</button>
        <button class="btn-secondary" onclick="toggleFileUpload()">📁 Upload Image</button>
    </div>
    
    <div class="status" id="status">Ready to start</div>
    
    <div class="panel">
        <h3>🔊 Narration</h3>
        <div id="speech">Waiting for detection...</div>
    </div>
    
    <div class="panel">
        <h3>👀 Objects</h3>
        <div id="objects">None detected</div>
    </div>
    
    <div class="panel">
        <h3>📝 Text</h3>
        <div id="texts">None detected</div>
    </div>

    <script>
        let video, canvas, ctx, stream, running = false, interval;
        let cameraAvailable = false;
        
        window.onload = () => {
            video = document.getElementById('video');
            canvas = document.getElementById('canvas');
            ctx = canvas.getContext('2d');
            
            // Check camera availability
            checkCameraSupport();
        };
        
        function checkCameraSupport() {
            const info = document.getElementById('cameraInfo');
            
            // Check if getUserMedia is supported
            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                info.innerHTML = `
                    <div class="error">
                        ⚠️ Camera API not supported<br>
                        <small>Your browser doesn't support camera access.</small><br>
                        <small>Try: Chrome, Safari, or Firefox</small><br>
                        <small>Or use HTTPS connection</small>
                    </div>
                `;
                cameraAvailable = false;
                document.getElementById('fileUpload').classList.remove('hidden');
                return;
            }
            
            // Check HTTPS (required for camera on most browsers)
            if (window.location.protocol !== 'https:' && window.location.hostname !== 'localhost') {
                info.innerHTML = `
                    <div style="color: #fbbf24;">
                        ⚠️ HTTPS Required<br>
                        <small>Camera needs secure connection</small><br>
                        <small>Use file upload instead, or:</small><br>
                        <small>- Use localhost, or</small><br>
                        <small>- Use ngrok for HTTPS</small>
                    </div>
                `;
                document.getElementById('fileUpload').classList.remove('hidden');
            }
            
            cameraAvailable = true;
            info.textContent = 'Tap button to start camera';
        }
        
        async function startCamera() {
            const info = document.getElementById('cameraInfo');
            
            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                alert('Camera not supported. Use file upload instead.');
                document.getElementById('fileUpload').classList.remove('hidden');
                return;
            }
            
            try {
                info.textContent = 'Requesting camera permission...';
                
                // Try rear camera first, fallback to any camera
                const constraints = {
                    video: { 
                        facingMode: { ideal: 'environment' },
                        width: { ideal: 1280 },
                        height: { ideal: 720 }
                    }
                };
                
                stream = await navigator.mediaDevices.getUserMedia(constraints);
                video.srcObject = stream;
                
                // Wait for video to load
                video.onloadedmetadata = () => {
                    document.getElementById('overlay').classList.add('hidden');
                    document.getElementById('status').textContent = 'Camera ready - tap Start';
                };
                
            } catch (error) {
                console.error('Camera error:', error);
                
                let errorMsg = 'Camera access failed. ';
                if (error.name === 'NotAllowedError') {
                    errorMsg += 'Permission denied. Allow camera in browser settings.';
                } else if (error.name === 'NotFoundError') {
                    errorMsg += 'No camera found on device.';
                } else if (error.name === 'NotReadableError') {
                    errorMsg += 'Camera is in use by another app.';
                } else {
                    errorMsg += error.message || 'Unknown error';
                }
                
                info.innerHTML = `
                    <div class="error">
                        ⚠️ ${errorMsg}
                    </div>
                `;
                
                // Show file upload as alternative
                document.getElementById('fileUpload').classList.remove('hidden');
            }
        }
        
        function start() {
            if (!stream) { 
                alert('Start camera first, or use file upload'); 
                return; 
            }
            running = true;
            document.getElementById('startBtn').classList.add('hidden');
            document.getElementById('stopBtn').classList.remove('hidden');
            document.getElementById('status').textContent = '✓ Active - Capturing every 3s';
            interval = setInterval(capture, 3000);
            capture();
        }
        
        function stop() {
            running = false;
            document.getElementById('startBtn').classList.remove('hidden');
            document.getElementById('stopBtn').classList.add('hidden');
            document.getElementById('status').textContent = '⏸ Paused';
            if (interval) clearInterval(interval);
        }
        
        async function capture() {
            if (!stream) { 
                alert('Start camera first'); 
                return; 
            }
            
            try {
                document.getElementById('status').textContent = '📸 Capturing...';
                
                canvas.width = video.videoWidth;
                canvas.height = video.videoHeight;
                ctx.drawImage(video, 0, 0);
                
                const blob = await new Promise(r => canvas.toBlob(r, 'image/jpeg', 0.8));
                await analyzeImage(blob);
                
            } catch (e) {
                console.error('Capture error:', e);
                document.getElementById('status').textContent = '❌ Capture failed';
            }
        }
        
        function toggleFileUpload() {
            const upload = document.getElementById('fileUpload');
            upload.classList.toggle('hidden');
        }
        
        async function uploadImage() {
            const fileInput = document.getElementById('fileInput');
            const file = fileInput.files[0];
            
            if (!file) return;
            
            document.getElementById('status').textContent = '📤 Uploading...';
            await analyzeImage(file);
        }
        
        async function analyzeImage(blob) {
            try {
                const formData = new FormData();
                formData.append('image', blob, 'frame.jpg');
                formData.append('language', 'en');
                
                const res = await fetch(window.location.origin + '/analyze', {
                    method: 'POST',
                    body: formData
                });
                
                if (res.ok) {
                    const data = await res.json();
                    
                    // Update narration
                    if (data.speech) {
                        document.getElementById('speech').innerHTML = `<strong>${data.speech}</strong>`;
                        speak(data.speech);
                    } else {
                        document.getElementById('speech').textContent = 'No significant objects detected';
                    }
                    
                    // Update objects
                    if (data.objects && data.objects.length > 0) {
                        document.getElementById('objects').innerHTML = 
                            data.objects.map((o, i) => {
                                const highlight = i === 0 ? 'style="background: rgba(251,191,54,0.3);"' : '';
                                const urgency = o.urgency ? ` ⚡${o.urgency.toFixed(1)}` : '';
                                return `<div ${highlight}>• ${o.class}${urgency} (${(o.confidence*100).toFixed(0)}%)</div>`;
                            }).join('');
                    } else {
                        document.getElementById('objects').textContent = 'None detected';
                    }
                    
                    // Update texts
                    if (data.text && data.text.length > 0) {
                        document.getElementById('texts').innerHTML = 
                            data.text.map(t => `<div>• ${t}</div>`).join('');
                    } else {
                        document.getElementById('texts').textContent = 'None detected';
                    }
                    
                    document.getElementById('status').textContent = '✓ Analysis complete';
                    
                } else {
                    throw new Error('Analysis failed: ' + res.status);
                }
                
            } catch (e) {
                console.error('Analysis error:', e);
                document.getElementById('status').textContent = '❌ Analysis failed: ' + e.message;
            }
        }
        
        function speak(text) {
            if (!('speechSynthesis' in window)) {
                console.log('Speech not supported');
                return;
            }
            
            const u = new SpeechSynthesisUtterance(text);
            u.lang = 'en-US';
            u.rate = 0.9;
            speechSynthesis.cancel();
            speechSynthesis.speak(u);
        }
    </script>
</body>
</html>'''


@app.route('/analyze', methods=['POST'])
def analyze_image():
    """
    Analyze image from mobile device
    
    Expected: multipart/form-data with 'image' file and 'language' field
    """
    if not VISION_AVAILABLE:
        return jsonify({'error': 'Vision modules not available'}), 503
    
    try:
        # Get image from request
        if 'image' not in request.files:
            return jsonify({'error': 'No image provided'}), 400
        
        image_file = request.files['image']
        language = request.form.get('language', 'en')
        
        # Read image
        image_bytes = image_file.read()
        image = Image.open(io.BytesIO(image_bytes))
        
        # Convert to numpy array (OpenCV format)
        frame = np.array(image)
        
        # RGB to BGR for OpenCV
        if len(frame.shape) == 3 and frame.shape[2] == 3:
            frame = frame[:, :, ::-1]
        
        # Run detection
        objects = detector.detect(frame)
        
        # Run OCR (less frequently to save resources)
        texts = []
        # Only run OCR randomly (30% chance) to reduce load
        import random
        if random.random() < 0.3:
            ocr_results = ocr_reader.recognize_text(frame, confidence_threshold=0.6)
            texts = ocr_reader.get_all_text(ocr_results)
        
        # Format context
        result = formatter.format_context(objects, texts, language=language)
        
        # Update global data
        global latest_data
        latest_data = {
            'objects': result['objects'],
            'text': result['text'],
            'speech': result['speech'],
            'timestamp': datetime.now().isoformat(),
            'language': language
        }
        
        logger.info(f"Mobile analysis: {len(objects)} objects, {len(texts)} texts")
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Analysis error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500
    """Serve the web dashboard"""
    return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Percepta - Vision Assistant Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #fff;
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
        }

        header {
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        }

        h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
        }

        .subtitle {
            font-size: 1.2em;
            opacity: 0.9;
        }

        .status-bar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 15px 25px;
            background: rgba(255, 255, 255, 0.15);
            backdrop-filter: blur(10px);
            border-radius: 10px;
            margin-bottom: 20px;
            flex-wrap: wrap;
            gap: 15px;
        }

        .status-indicator {
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .status-dot {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #4ade80;
            animation: pulse 2s ease-in-out infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        .language-selector {
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .language-selector label {
            font-weight: 600;
        }

        .language-selector select {
            padding: 8px 15px;
            border-radius: 8px;
            border: 1px solid rgba(255, 255, 255, 0.3);
            background: rgba(255, 255, 255, 0.2);
            color: white;
            font-size: 1em;
            cursor: pointer;
            font-weight: 600;
            outline: none;
        }

        .language-selector select option {
            background: #764ba2;
            color: white;
        }

        .dashboard-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }

        .panel {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }

        .panel h2 {
            font-size: 1.5em;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .icon {
            font-size: 1.2em;
        }

        .speech-panel {
            grid-column: 1 / -1;
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.2), rgba(255, 255, 255, 0.1));
        }

        .speech-text {
            font-size: 1.3em;
            line-height: 1.6;
            padding: 20px;
            background: rgba(0, 0, 0, 0.2);
            border-radius: 10px;
            min-height: 80px;
            display: flex;
            align-items: center;
            justify-content: center;
            text-align: center;
        }

        .empty-state {
            opacity: 0.5;
            font-style: italic;
        }

        .item-list {
            display: flex;
            flex-direction: column;
            gap: 10px;
            max-height: 300px;
            overflow-y: auto;
        }

        .item {
            padding: 12px 15px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 8px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: transform 0.2s, background 0.2s;
        }

        .item:hover {
            transform: translateX(5px);
            background: rgba(255, 255, 255, 0.15);
        }

        .item-name {
            font-weight: 600;
            text-transform: capitalize;
        }

        .item-badge {
            padding: 4px 10px;
            background: rgba(255, 255, 255, 0.2);
            border-radius: 20px;
            font-size: 0.85em;
        }

        .priority-high {
            background: rgba(239, 68, 68, 0.3);
            border: 1px solid rgba(239, 68, 68, 0.5);
        }

        .priority-medium {
            background: rgba(251, 191, 36, 0.3);
            border: 1px solid rgba(251, 191, 36, 0.5);
        }

        .priority-low {
            background: rgba(59, 130, 246, 0.3);
            border: 1px solid rgba(59, 130, 246, 0.5);
        }

        .text-item {
            padding: 12px 15px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 8px;
            border-left: 4px solid #fbbf24;
            font-weight: 500;
        }

        .controls {
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
        }

        button {
            padding: 12px 25px;
            font-size: 1em;
            font-weight: 600;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
        }

        .btn-primary {
            background: #10b981;
            color: white;
        }

        .btn-primary:hover {
            background: #059669;
            transform: translateY(-2px);
            box-shadow: 0 6px 16px rgba(0, 0, 0, 0.3);
        }

        .btn-secondary {
            background: rgba(255, 255, 255, 0.2);
            color: white;
            border: 1px solid rgba(255, 255, 255, 0.3);
        }

        .btn-secondary:hover {
            background: rgba(255, 255, 255, 0.3);
        }

        .timestamp {
            font-size: 0.9em;
            opacity: 0.8;
        }

        .item-list::-webkit-scrollbar {
            width: 8px;
        }

        .item-list::-webkit-scrollbar-track {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 4px;
        }

        .item-list::-webkit-scrollbar-thumb {
            background: rgba(255, 255, 255, 0.3);
            border-radius: 4px;
        }

        .item-list::-webkit-scrollbar-thumb:hover {
            background: rgba(255, 255, 255, 0.5);
        }

        @media (max-width: 768px) {
            h1 {
                font-size: 2em;
            }

            .dashboard-grid {
                grid-template-columns: 1fr;
            }

            .status-bar {
                flex-direction: column;
                gap: 15px;
                text-align: center;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>👁️ Percepta</h1>
            <p class="subtitle">AI-Powered Vision Assistant for the Visually Impaired</p>
        </header>

        <div class="status-bar">
            <div class="status-indicator">
                <div class="status-dot"></div>
                <span><strong>System Active</strong></span>
            </div>
            
            <div class="language-selector">
                <label for="languageSelect">🌐 Language:</label>
                <select id="languageSelect" onchange="changeLanguage()">
                    <option value="en">English</option>
                    <option value="hi">हिंदी (Hindi)</option>
                </select>
            </div>
            
            <div class="timestamp" id="lastUpdate">Waiting for data...</div>
            
            <div class="controls">
                <button class="btn-secondary" onclick="refreshData()">🔄 Refresh</button>
            </div>
        </div>

        <div class="panel speech-panel">
            <h2><span class="icon">🔊</span> Current Narration</h2>
            <div class="speech-text" id="speechText">
                <span class="empty-state">No active narration</span>
            </div>
        </div>

        <div class="dashboard-grid">
            <div class="panel">
                <h2><span class="icon">👀</span> Detected Objects</h2>
                <div class="item-list" id="objectsList">
                    <div class="empty-state">No objects detected</div>
                </div>
            </div>

            <div class="panel">
                <h2><span class="icon">📝</span> Detected Text</h2>
                <div class="item-list" id="textList">
                    <div class="empty-state">No text detected</div>
                </div>
            </div>
        </div>
    </div>

    <script>
        const API_URL = window.location.origin;
        let updateInterval;
        let currentLanguage = 'en';

        async function fetchData() {
            try {
                const response = await fetch(`${API_URL}/data`);
                const data = await response.json();
                updateDashboard(data);
            } catch (error) {
                console.error('Error fetching data:', error);
            }
        }

        function updateDashboard(data) {
            if (data.timestamp) {
                const time = new Date(data.timestamp).toLocaleTimeString();
                document.getElementById('lastUpdate').textContent = `Last update: ${time}`;
            }

            const speechText = document.getElementById('speechText');
            if (data.speech) {
                speechText.innerHTML = data.speech;
                speechText.classList.remove('empty-state');
            } else {
                speechText.innerHTML = '<span class="empty-state">No active narration</span>';
            }

            const objectsList = document.getElementById('objectsList');
            if (data.objects && data.objects.length > 0) {
                objectsList.innerHTML = data.objects.map((obj, index) => {
                    const priorityClass = obj.priority >= 4 ? 'priority-high' : 
                                         obj.priority >= 3 ? 'priority-medium' : 
                                         'priority-low';
                    
                    // Show urgency badge for top detection
                    const urgencyBadge = obj.urgency ? 
                        `<span class="urgency-badge" style="background: rgba(255,255,255,0.15); padding: 3px 8px; border-radius: 10px; font-size: 0.8em; margin-left: 5px;">
                            ⚡ ${obj.urgency.toFixed(1)}
                        </span>` : '';
                    
                    // Distance indicator
                    const distanceIndicator = obj.distance !== undefined ?
                        `<span style="opacity: 0.7; font-size: 0.85em; margin-left: 5px;">
                            ${obj.distance < 0.3 ? '🔴 Very Close' : obj.distance < 0.6 ? '🟡 Close' : '🟢 Far'}
                        </span>` : '';
                    
                    // Highlight most urgent (first in list)
                    const highlightStyle = index === 0 ? 'border: 2px solid #fbbf24; box-shadow: 0 0 10px rgba(251, 191, 36, 0.5);' : '';
                    
                    return `
                        <div class="item" style="${highlightStyle}">
                            <div>
                                <span class="item-name">${obj.class}</span>
                                ${urgencyBadge}
                                ${distanceIndicator}
                            </div>
                            <span class="item-badge ${priorityClass}">
                                ${(obj.confidence * 100).toFixed(0)}%
                            </span>
                        </div>
                    `;
                }).join('');
            } else {
                objectsList.innerHTML = '<div class="empty-state">No objects detected</div>';
            }

            const textList = document.getElementById('textList');
            if (data.text && data.text.length > 0) {
                textList.innerHTML = data.text.map(text => 
                    `<div class="text-item">${text}</div>`
                ).join('');
            } else {
                textList.innerHTML = '<div class="empty-state">No text detected</div>';
            }
        }

        async function changeLanguage() {
            const select = document.getElementById('languageSelect');
            currentLanguage = select.value;
            
            console.log(`Language changed to: ${currentLanguage}`);
            
            // Send language change to backend
            try {
                const response = await fetch(`${API_URL}/set_language`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ language: currentLanguage })
                });
                
                if (response.ok) {
                    console.log('Language updated on backend');
                    // Show brief notification
                    const originalText = select.options[select.selectedIndex].text;
                    alert(`Language changed to ${originalText}`);
                }
            } catch (error) {
                console.error('Error changing language:', error);
            }
        }

        function refreshData() {
            fetchData();
        }

        function startAutoRefresh() {
            fetchData();
            updateInterval = setInterval(fetchData, 1000);
        }

        window.addEventListener('load', () => {
            console.log('Percepta Dashboard initialized');
            startAutoRefresh();
        });

        window.addEventListener('beforeunload', () => {
            if (updateInterval) {
                clearInterval(updateInterval);
            }
        });
    </script>
</body>
</html>'''


@app.route('/')
def index():
    """Serve the web dashboard"""
    return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Percepta - Vision Assistant Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #fff;
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
        }

        header {
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        }

        h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
        }

        .subtitle {
            font-size: 1.2em;
            opacity: 0.9;
        }

        .status-bar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 15px 25px;
            background: rgba(255, 255, 255, 0.15);
            backdrop-filter: blur(10px);
            border-radius: 10px;
            margin-bottom: 20px;
        }

        .status-indicator {
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .status-dot {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #4ade80;
            animation: pulse 2s ease-in-out infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        .dashboard-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }

        .panel {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }

        .panel h2 {
            font-size: 1.5em;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .icon {
            font-size: 1.2em;
        }

        .speech-panel {
            grid-column: 1 / -1;
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.2), rgba(255, 255, 255, 0.1));
        }

        .speech-text {
            font-size: 1.3em;
            line-height: 1.6;
            padding: 20px;
            background: rgba(0, 0, 0, 0.2);
            border-radius: 10px;
            min-height: 80px;
            display: flex;
            align-items: center;
            justify-content: center;
            text-align: center;
        }

        .empty-state {
            opacity: 0.5;
            font-style: italic;
        }

        .item-list {
            display: flex;
            flex-direction: column;
            gap: 10px;
            max-height: 300px;
            overflow-y: auto;
        }

        .item {
            padding: 12px 15px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 8px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: transform 0.2s, background 0.2s;
        }

        .item:hover {
            transform: translateX(5px);
            background: rgba(255, 255, 255, 0.15);
        }

        .item-name {
            font-weight: 600;
            text-transform: capitalize;
        }

        .item-badge {
            padding: 4px 10px;
            background: rgba(255, 255, 255, 0.2);
            border-radius: 20px;
            font-size: 0.85em;
        }

        .priority-high {
            background: rgba(239, 68, 68, 0.3);
            border: 1px solid rgba(239, 68, 68, 0.5);
        }

        .priority-medium {
            background: rgba(251, 191, 36, 0.3);
            border: 1px solid rgba(251, 191, 36, 0.5);
        }

        .priority-low {
            background: rgba(59, 130, 246, 0.3);
            border: 1px solid rgba(59, 130, 246, 0.5);
        }

        .text-item {
            padding: 12px 15px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 8px;
            border-left: 4px solid #fbbf24;
            font-weight: 500;
        }

        .controls {
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
        }

        button {
            padding: 12px 25px;
            font-size: 1em;
            font-weight: 600;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
        }

        .btn-primary {
            background: #10b981;
            color: white;
        }

        .btn-primary:hover {
            background: #059669;
            transform: translateY(-2px);
            box-shadow: 0 6px 16px rgba(0, 0, 0, 0.3);
        }

        .btn-secondary {
            background: rgba(255, 255, 255, 0.2);
            color: white;
            border: 1px solid rgba(255, 255, 255, 0.3);
        }

        .btn-secondary:hover {
            background: rgba(255, 255, 255, 0.3);
        }

        .timestamp {
            font-size: 0.9em;
            opacity: 0.8;
        }

        .item-list::-webkit-scrollbar {
            width: 8px;
        }

        .item-list::-webkit-scrollbar-track {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 4px;
        }

        .item-list::-webkit-scrollbar-thumb {
            background: rgba(255, 255, 255, 0.3);
            border-radius: 4px;
        }

        .item-list::-webkit-scrollbar-thumb:hover {
            background: rgba(255, 255, 255, 0.5);
        }

        @media (max-width: 768px) {
            h1 {
                font-size: 2em;
            }

            .dashboard-grid {
                grid-template-columns: 1fr;
            }

            .status-bar {
                flex-direction: column;
                gap: 15px;
                text-align: center;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>👁️ Percepta</h1>
            <p class="subtitle">AI-Powered Vision Assistant for the Visually Impaired</p>
        </header>

        <div class="status-bar">
            <div class="status-indicator">
                <div class="status-dot"></div>
                <span><strong>System Active</strong></span>
            </div>
            <div class="timestamp" id="lastUpdate">Waiting for data...</div>
            <div class="controls">
                <button class="btn-secondary" onclick="refreshData()">🔄 Refresh</button>
            </div>
        </div>

        <div class="panel speech-panel">
            <h2><span class="icon">🔊</span> Current Narration</h2>
            <div class="speech-text" id="speechText">
                <span class="empty-state">No active narration</span>
            </div>
        </div>

        <div class="dashboard-grid">
            <div class="panel">
                <h2><span class="icon">👀</span> Detected Objects</h2>
                <div class="item-list" id="objectsList">
                    <div class="empty-state">No objects detected</div>
                </div>
            </div>

            <div class="panel">
                <h2><span class="icon">📝</span> Detected Text</h2>
                <div class="item-list" id="textList">
                    <div class="empty-state">No text detected</div>
                </div>
            </div>
        </div>
    </div>

    <script>
        const API_URL = window.location.origin;
        let updateInterval;

        async function fetchData() {
            try {
                const response = await fetch(`${API_URL}/data`);
                const data = await response.json();
                updateDashboard(data);
            } catch (error) {
                console.error('Error fetching data:', error);
            }
        }

        function updateDashboard(data) {
            if (data.timestamp) {
                const time = new Date(data.timestamp).toLocaleTimeString();
                document.getElementById('lastUpdate').textContent = `Last update: ${time}`;
            }

            const speechText = document.getElementById('speechText');
            if (data.speech) {
                speechText.innerHTML = data.speech;
                speechText.classList.remove('empty-state');
            } else {
                speechText.innerHTML = '<span class="empty-state">No active narration</span>';
            }

            const objectsList = document.getElementById('objectsList');
            if (data.objects && data.objects.length > 0) {
                objectsList.innerHTML = data.objects.map(obj => {
                    const priorityClass = obj.priority >= 4 ? 'priority-high' : 
                                         obj.priority >= 3 ? 'priority-medium' : 
                                         'priority-low';
                    return `
                        <div class="item">
                            <span class="item-name">${obj.class}</span>
                            <span class="item-badge ${priorityClass}">
                                ${(obj.confidence * 100).toFixed(0)}%
                            </span>
                        </div>
                    `;
                }).join('');
            } else {
                objectsList.innerHTML = '<div class="empty-state">No objects detected</div>';
            }

            const textList = document.getElementById('textList');
            if (data.text && data.text.length > 0) {
                textList.innerHTML = data.text.map(text => 
                    `<div class="text-item">${text}</div>`
                ).join('');
            } else {
                textList.innerHTML = '<div class="empty-state">No text detected</div>';
            }
        }

        function refreshData() {
            fetchData();
        }

        function startAutoRefresh() {
            fetchData();
            updateInterval = setInterval(fetchData, 1000);
        }

        window.addEventListener('load', () => {
            console.log('Percepta Dashboard initialized');
            startAutoRefresh();
        });

        window.addEventListener('beforeunload', () => {
            if (updateInterval) {
                clearInterval(updateInterval);
            }
        });
    </script>
</body>
</html>'''


@app.route('/set_language', methods=['POST'])
def set_language():
    """
    Set the current language for narration
    
    Expected payload:
    {
        'language': 'en' or 'hi'
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'language' not in data:
            return jsonify({'error': 'No language provided'}), 400
        
        global current_language
        current_language = data['language']
        
        logger.info(f"Language changed to: {current_language}")
        
        return jsonify({
            'status': 'success',
            'language': current_language
        }), 200
        
    except Exception as e:
        logger.error(f"Language change error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/get_language', methods=['GET'])
def get_language():
    """Get current language setting"""
    return jsonify({'language': current_language}), 200


@app.route('/update', methods=['POST'])
def update_data():
    """
    Receive updates from vision pipeline
    
    Expected payload:
    {
        'objects': [...],
        'text': [...],
        'speech': "...",
        'language': 'en' or 'hi'  # Optional: language used for this speech
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Update global data
        global latest_data
        latest_data = {
            'objects': data.get('objects', []),
            'text': data.get('text', []),
            'speech': data.get('speech'),
            'timestamp': datetime.now().isoformat(),
            'language': data.get('language', current_language)
        }
        
        logger.debug(f"Data updated: {len(latest_data['objects'])} objects, "
                    f"{len(latest_data['text'])} texts")
        
        return jsonify({'status': 'success', 'current_language': current_language}), 200
        
    except Exception as e:
        logger.error(f"Update error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/data', methods=['GET'])
def get_data():
    """
    Get latest vision data for web dashboard
    
    Returns:
    {
        'objects': [...],
        'text': [...],
        'speech': "...",
        'timestamp': "..."
    }
    """
    return jsonify(latest_data), 200


@app.route('/status', methods=['GET'])
def get_status():
    """Get system status"""
    return jsonify({
        'status': 'running',
        'has_data': latest_data['timestamp'] is not None,
        'last_update': latest_data['timestamp']
    }), 200


@app.route('/reset', methods=['POST'])
def reset_data():
    """Reset stored data"""
    global latest_data
    latest_data = {
        'objects': [],
        'text': [],
        'speech': None,
        'timestamp': None
    }
    logger.info("Data reset")
    return jsonify({'status': 'reset'}), 200


if __name__ == '__main__':
    print("=" * 50)
    print("PERCEPTA BACKEND API")
    print("=" * 50)
    print("\nEndpoints:")
    print("  POST /update    - Receive vision data")
    print("  GET  /data      - Get latest data")
    print("  GET  /status    - Get system status")
    print("  POST /reset     - Reset data")
    print("  GET  /          - Web dashboard")
    print("\nStarting server on http://localhost:5000")
    print("=" * 50)
    print()
    
    app.run(host='0.0.0.0', port=5000, debug=False)