# 📱 Percepta Mobile Setup Guide

## Overview

Percepta can run on mobile devices in two ways:
1. **Mobile Web App** (Easiest - for hackathon demo)
2. **Native Mobile App** (Advanced - for production)

This guide covers **Mobile Web App** setup.

---

## 🚀 Quick Start (Same WiFi)

### Step 1: Find Your Computer's IP Address

**Windows:**
```cmd
ipconfig
```
Look for "IPv4 Address" (e.g., `192.168.1.100`)

**Mac/Linux:**
```bash
ifconfig | grep "inet "
```
Look for local IP (e.g., `192.168.1.100`)

### Step 2: Start Backend

```bash
python backend.py
```

Backend will start on: `http://0.0.0.0:5000`

### Step 3: Access from Mobile

On your phone's browser, go to:
```
http://YOUR_COMPUTER_IP:5000/mobile
```

Example: `http://192.168.1.100:5000/mobile`

### Step 4: Allow Camera Access

- Browser will ask for camera permission
- Click "Allow"
- Rear camera will activate

### Step 5: Start Detection

1. Click "📷 Start Camera"
2. Click "▶️ Start"
3. System captures and analyzes every 3 seconds
4. Hear audio narration through phone speaker

---

## 📋 Requirements

### Computer (Backend Server):
- Python 3.8+
- All Percepta modules installed
- Connected to WiFi

### Mobile Phone:
- Modern browser (Chrome, Safari, Firefox)
- Camera access
- Connected to **same WiFi** as computer

---

## 🌐 Network Setup Options

### Option 1: Same WiFi (Easiest)
✅ Both devices on same network
✅ No configuration needed
✅ Good for demos

**Setup:**
1. Computer and phone on same WiFi
2. Use computer's local IP
3. Access: `http://192.168.1.100:5000/mobile`

---

### Option 2: Mobile Hotspot
✅ No WiFi needed
✅ Phone provides internet
✅ Good for outdoor demos

**Setup:**
1. Enable hotspot on phone
2. Connect computer to phone's hotspot
3. Find computer's IP: `ipconfig` or `ifconfig`
4. On phone browser: `http://COMPUTER_IP:5000/mobile`

---

### Option 3: Public Server (Advanced)
✅ Access from anywhere
✅ No same network needed
⚠️ Requires server setup

**Options:**
- **ngrok** (easiest temporary solution)
- **Cloud server** (AWS, Azure, Google Cloud)
- **Your own server** with public IP

---

## 🔧 Using ngrok (Remote Access)

### Step 1: Install ngrok
Download from: https://ngrok.com/download

### Step 2: Start Backend
```bash
python backend.py
```

### Step 3: Start ngrok Tunnel
```bash
ngrok http 5000
```

### Step 4: Use Public URL
ngrok will show:
```
Forwarding: https://abc123.ngrok.io -> localhost:5000
```

Access on phone: `https://abc123.ngrok.io/mobile`

✅ Works from anywhere
✅ No network configuration
⚠️ Free tier has limits

---

## 📱 Mobile Features

### Camera Controls:
- **Start Camera**: Activate rear camera
- **▶️ Start**: Begin auto-capture (every 3s)
- **⏹️ Stop**: Pause auto-capture
- **📸 Capture Now**: Manual single capture

### Settings:
- **Language**: Switch between English/Hindi
- **Capture Interval**: Adjust frequency (1-10 seconds)

### Display:
- **Live camera feed**
- **Speech narration** (top panel)
- **Detected objects** (with urgency scores)
- **Detected text**

---

## 🎯 Mobile Optimization Features

### Battery Saving:
- Configurable capture interval
- Pauses when app in background
- Efficient image compression

### Performance:
- Reduced OCR frequency (30% of captures)
- Image downscaling before upload
- Efficient canvas operations

### User Experience:
- Large touch targets
- Responsive design
- Works in portrait/landscape
- Dark mode friendly

---

## 🔊 Audio on Mobile

### Web Speech API
Mobile app uses browser's **Web Speech Synthesis API**:

**Advantages:**
- Built-in, no installation
- Supports multiple languages
- Good Hindi pronunciation (iOS/Android)

**Language Support:**
- English: `en-US`
- Hindi: `hi-IN`

**Controls:**
- Auto-plays narration
- Cancels previous speech
- Adjustable rate

---

## 🎨 UI Customization

Edit `mobile.html` to customize:

### Change Colors:
```css
background: linear-gradient(135deg, #YOUR_COLOR1 0%, #YOUR_COLOR2 100%);
```

### Adjust Button Sizes:
```css
button {
    padding: 20px 30px; /* Make bigger */
}
```

### Change Capture Interval Default:
```javascript
let captureInterval = 5000; // 5 seconds instead of 3
```

---

## 🐛 Troubleshooting

### Issue: Can't connect to backend

**Check:**
1. Both devices on same network
2. Computer firewall allows port 5000
3. IP address is correct
4. Backend is running

**Solution:**
```bash
# Windows: Allow port in firewall
netsh advfirewall firewall add rule name="Percepta" dir=in action=allow protocol=TCP localport=5000

# Mac: Should work by default
```

---

### Issue: Camera not working

**Check:**
1. Browser permissions granted
2. Camera not in use by another app
3. Using HTTPS or localhost (required for camera access)

**Solution:**
- Use ngrok for HTTPS
- Or access via `localhost` if testing on same device

---

### Issue: Slow performance

**Solutions:**
1. Increase capture interval (5-10 seconds)
2. Reduce image quality in code
3. Use better WiFi connection
4. Close other apps on phone

---

### Issue: No audio narration

**Check:**
1. Phone volume not muted
2. Browser has audio permissions
3. Check browser console for errors

**Test:**
```javascript
// Open browser console, run:
let u = new SpeechSynthesisUtterance("Test");
speechSynthesis.speak(u);
```

---

## 📊 Performance Tips

### For Better Speed:
1. **Use same WiFi** (not cellular)
2. **Increase interval** (5-7 seconds)
3. **Stay close to router**
4. **Close background apps**

### For Better Accuracy:
1. **Good lighting**
2. **Steady hand** (or tripod)
3. **Clear objects** (not too far)
4. **Hold for 2-3 seconds** before capture

---

## 🎓 Demo Tips

### For Hackathon Presentation:

**Setup (5 min before):**
1. Start backend on laptop
2. Connect phone to same WiFi
3. Open mobile app
4. Test camera and audio
5. Prepare test objects

**Demo Flow:**
1. Show mobile interface
2. Point at person → hear narration
3. Show stairs detection (mock-up)
4. Switch to Hindi
5. Show urgency prioritization
6. Explain offline capability

**Talking Points:**
- "Works on any smartphone with a browser"
- "No app installation needed"
- "Real-time AI processing"
- "Multi-language support"
- "Intelligent hazard prioritization"

---

## 🚀 Advanced: Native App

For production deployment, consider:

### Option 1: Progressive Web App (PWA)
- Add to home screen
- Offline support
- App-like experience

**Add to `mobile.html`:**
```html
<link rel="manifest" href="/manifest.json">
<script>
if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/sw.js');
}
</script>
```

### Option 2: React Native
- Cross-platform (iOS + Android)
- Better performance
- Native features

### Option 3: Flutter
- Single codebase
- Beautiful UI
- Fast development

---

## 📱 Installation Instructions for Users

### Quick Access (No Installation):

1. **Open browser** on your phone
2. **Go to:** `http://DEMO_URL/mobile`
3. **Allow camera** when prompted
4. **Start using!**

### Add to Home Screen (Optional):

**iPhone:**
1. Open in Safari
2. Tap Share button
3. "Add to Home Screen"
4. Icon appears on home screen

**Android:**
1. Open in Chrome
2. Tap menu (⋮)
3. "Add to Home screen"
4. Icon appears on home screen

---

## 🔒 Security Notes

### For Public Demo:
- Use HTTPS (ngrok provides this)
- Don't expose on public internet long-term
- No authentication in demo version

### For Production:
- Add user authentication
- Use HTTPS with valid certificate
- Rate limiting on API
- Input validation
- CORS restrictions

---

## 📝 Checklist

Before demo:
- [ ] Backend running
- [ ] Mobile app accessible
- [ ] Camera permissions granted
- [ ] Audio working
- [ ] Test objects ready
- [ ] Both languages tested
- [ ] Good WiFi connection
- [ ] Phone charged
- [ ] Backup plan (local demo)

---

## 🎯 Summary

**Mobile Web App = Perfect for Hackathon:**
- ✅ Quick setup (5 minutes)
- ✅ No app store submission
- ✅ Works on any phone
- ✅ Easy to demo
- ✅ Full feature parity

**Access:** `http://YOUR_IP:5000/mobile`

---

For questions or issues, check the main README.md or TESTING_GUIDE.md