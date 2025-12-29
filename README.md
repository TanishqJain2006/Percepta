# Percepta 👁️🔊  
### AI Vision-to-Voice Assistant for the Visually Impaired

## 🧠 Overview
Percepta is an AI-powered assistive system designed to help visually impaired individuals navigate their surroundings safely and independently. The system converts real-time visual input into **context-aware voice guidance**, enabling users to understand obstacles, people, and important signs in their environment.

Unlike traditional solutions that narrate everything, EchoVision intelligently **prioritizes critical information**, reducing cognitive overload and improving usability.

---

## 🎯 Problem Statement
Visually impaired individuals face challenges in:
- Identifying obstacles and people in real time  
- Reading signboards, labels, and warnings  
- Navigating unfamiliar environments safely  

Existing assistive tools are often expensive, limited in scope, or overwhelm users with excessive information.

---

## 💡 Proposed Solution
Percepta captures live visual input through a camera, processes it using AI-based computer vision and text recognition, and delivers **prioritized audio feedback** to the user for safer navigation.

---

## ✨ Key Features
- 🔍 Real-time object detection using YOLOv8  
- 📝 Text recognition (OCR) for signboards and labels  
- 🧠 Context-aware prioritization using rule-based NLP  
- 🔊 Text-to-speech voice guidance  
- 💻📱 Cross-platform support (Laptop & Mobile Browser)  
- ⚡ Low-cost and scalable design  

---

## 🏗️ System Workflow
1. Camera captures real-time visual input  
2. Vision processing extracts objects and text  
3. Context & priority logic filters critical information  
4. NLP module generates meaningful narration  
5. Text-to-speech delivers audio output to the user  

---

## 🛠️ Technologies Used

### AI & Vision
- YOLOv8 (Object Detection)  
- OpenCV  

### Text Processing
- EasyOCR / Tesseract  

### Language Logic
- Rule-based NLP  

### Voice Output
- Text-to-Speech (pyttsx3 / gTTS)  

### Backend & UI
- Python  
- Flask  
- Streamlit / Web Interface  

---

## 🧪 Methodology
- Use pre-trained AI models to ensure fast development and reliability  
- Process live video frames for object and text detection  
- Apply prioritization logic to reduce unnecessary narration  
- Deliver real-time audio guidance through a cross-platform interface  

---

## 📊 Feasibility & Viability
- **Technically Feasible:** Uses open-source tools and pre-trained models for real-time performance on standard devices  
- **Cost-Effective & Scalable:** Requires only a camera-enabled device and lightweight software  

---

## 🌍 Impact & Benefits
- Enhances independence for visually impaired users  
- Improves safety and environmental awareness  
- Provides an inclusive, affordable, and scalable assistive solution  

---

## 🚧 Future Enhancements
- Distance and direction-based alerts  
- Multi-language voice support  
- Edge-device deployment  
- Advanced semantic understanding of surroundings  

---

## 👥 Team
**Team Name:** Percepta  
Built by a team of 3 members as part of an AI-based hackathon.

---

## 📌 Note
This project is a prototype developed for hackathon purposes and demonstrates the potential of AI-driven assistive technology for accessibility.

---

⭐ If you find this project impactful, consider giving it a star!
