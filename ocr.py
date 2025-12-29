import easyocr

reader = easyocr.Reader(['en'])

def detect_text(frame):
    results = reader.readtext(frame)
    texts = []

    for (bbox, text, confidence) in results:
        if confidence > 0.5:
            texts.append({
                "content": text,
                "confidence": round(confidence, 2)
            })

    return texts
