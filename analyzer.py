import os
import re
import io
import base64
import threading
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

MODEL_NAME = os.getenv("MODEL_NAME", "lxyuan/distilbert-base-multilingual-cased-sentiments-student")
VISION_MODEL_NAME = "trpakov/vit-face-expression"

# Global pipeline variables
_pipeline = None
_model_loaded = False

_vision_pipeline = None
_vision_model_loaded = False

def _load_model_thread():
    global _pipeline, _model_loaded, _vision_pipeline, _vision_model_loaded
    
    # 1. Load Text Sentiment Model
    try:
        print("Importing Hugging Face transformers in background thread...")
        from transformers import pipeline
        
        print(f"Loading sentiment analysis model in background thread: {MODEL_NAME}...")
        _pipeline = pipeline("sentiment-analysis", model=MODEL_NAME, device=-1) # force CPU
        _model_loaded = True
        print("Hugging Face text model loaded successfully!")
    except Exception as e:
        print(f"Failed to load Hugging Face text model: {e}")
        _pipeline = None
        _model_loaded = False

    # 2. Load Vision Sentiment Model
    try:
        from transformers import pipeline
        print(f"Loading facial expression ViT model in background thread: {VISION_MODEL_NAME}...")
        # trpakov/vit-face-expression has 7 classes: angry, disgust, fear, happy, sad, surprise, neutral
        _vision_pipeline = pipeline("image-classification", model=VISION_MODEL_NAME, device=-1)
        _vision_model_loaded = True
        print("Hugging Face facial vision model loaded successfully!")
    except Exception as e:
        print(f"Failed to load Hugging Face facial vision model: {e}")
        _vision_pipeline = None
        _vision_model_loaded = False

def init_analyzer():
    thread = threading.Thread(target=_load_model_thread, daemon=True)
    thread.start()

def check_sarcasm_and_pain_points(text):
    text_lower = text.lower()
    
    # 1. Battery/Charging drain pain-points (highly negative context)
    short_time_regex = r"\b(one|two|three|four|five|1|2|3|4|5|half|half\s+an)\s+(hour|hours|hr|hrs|min|mins|minute|minutes)\b"
    battery_patterns = [
        rf"charging\s+(\w+\s+){{0,3}}every\s+{short_time_regex}",
        rf"lasts?\s+(\w+\s+){{0,3}}{short_time_regex}",
        rf"battery\s+dies?\s+(\w+\s+){{0,3}}{short_time_regex}",
        rf"die\s+(\w+\s+){{0,3}}after\s+{short_time_regex}"
    ]
    
    for pattern in battery_patterns:
        if re.search(pattern, text_lower):
            return {
                "sentiment": "negative",
                "confidence": 0.92,
                "method": "Heuristic Filter (Battery/Time Limit)"
            }
            
    # 2. Sarcastic positive conditionals
    pos_words = r"(great|good|excellent|perfect|ideal|awesome|amazing|wonderful|love|best)"
    sarc_verbs = r"(enjoy|like|want|love|prefer)"
    neg_actions = r"(charging|waiting|paying|restarting|rebooting|returning|wasting|fixing|repairing|struggling|fighting|losing|suffering|regretting)"
    
    sarcasm_pattern_1 = rf"\b{pos_words}\s+(\w+\s+){{0,4}}if\s+you\s+{sarc_verbs}\s+(\w+\s+){{0,3}}{neg_actions}\b"
    if re.search(sarcasm_pattern_1, text_lower):
        return {
            "sentiment": "negative",
            "confidence": 0.95,
            "method": "Sarcasm Heuristic Filter (Conditional Pain)"
        }
        
    # 3. Contrastive outcome sarcasm
    neg_outcomes = r"(ruin|destroy|waste|throw|crash|suffer|regret|burn|lose|fail|paperweight)"
    sarcasm_pattern_2 = rf"\b{pos_words}\s+(\w+\s+){{0,4}}if\s+you\s+want\s+to\s+(\w+\s+){{0,3}}{neg_outcomes}\b"
    if re.search(sarcasm_pattern_2, text_lower):
        return {
            "sentiment": "negative",
            "confidence": 0.95,
            "method": "Sarcasm Heuristic Filter (Destructive Outcome)"
        }
        
    return None

def analyze_sentiment(text):
    if not text or not text.strip():
        return {
            "sentiment": "neutral",
            "confidence": 1.0,
            "method": "empty_input"
        }
    
    sarcasm_result = check_sarcasm_and_pain_points(text)
    if sarcasm_result:
        return sarcasm_result
        
    if _model_loaded and _pipeline:
        try:
            results = _pipeline(text[:512])
            if results:
                res = results[0]
                label = res["label"].lower()
                score = float(res["score"])
                
                if label == "label_0" or label == "neg" or label == "negative":
                    mapped_label = "negative"
                elif label == "label_1" or label == "neu" or label == "neutral":
                    mapped_label = "neutral"
                elif label == "label_2" or label == "pos" or label == "positive":
                    mapped_label = "positive"
                else:
                    mapped_label = label if label in ["positive", "neutral", "negative"] else "neutral"
                    
                return {
                    "sentiment": mapped_label,
                    "confidence": round(score, 4),
                    "method": "Hugging Face (" + MODEL_NAME.split("/")[-1] + ")"
                }
        except Exception as e:
            print(f"HF Inference failed: {e}. Using fallback rule-based analyzer.")
            
    return analyze_fallback(text)

def analyze_fallback(text):
    text_lower = text.lower()
    
    # Lexicons
    pos_words = {
        'good', 'great', 'excellent', 'love', 'fantastic', 'amazing', 'awesome', 
        'happy', 'best', 'positive', 'wonderful', 'beautiful', 'helpful', 'outstanding', 
        'like', 'superb', 'satisfied', 'perfect', 'glad', 'enjoy', 'recommend', 'nice',
        'cool', 'brilliant', 'pleased', 'fast'
    }
    neg_words = {
        'bad', 'worst', 'terrible', 'hate', 'awful', 'horrible', 'unhappy', 'fail', 
        'broke', 'slow', 'garbage', 'waste', 'useless', 'poor', 'negative', 'defect', 
        'issue', 'error', 'dislike', 'annoy', 'broken', 'difficult', 'pain', 'scam',
        'disappointed', 'regret', 'hate', 'wasted', 'annoyed', 'useless', 'frustrated'
    }
    
    # Clean text to words
    words = re.findall(r'\b\w+\b', text_lower)
    
    pos_count = sum(1 for w in words if w in pos_words)
    neg_count = sum(1 for w in words if w in neg_words)
    
    total_words = len(words)
    if total_words == 0:
        return {"sentiment": "neutral", "confidence": 1.0, "method": "Rule-based Fallback"}
        
    diff = pos_count - neg_count
    
    if diff > 0:
        sentiment = "positive"
        confidence = 0.5 + (pos_count / (pos_count + neg_count + 1)) * 0.5
    elif diff < 0:
        sentiment = "negative"
        confidence = 0.5 + (neg_count / (pos_count + neg_count + 1)) * 0.5
    else:
        sentiment = "neutral"
        if pos_count > 0:
            confidence = 0.5
        else:
            confidence = 0.75
            
    return {
        "sentiment": sentiment,
        "confidence": round(min(confidence, 1.0), 4),
        "method": "Rule-based Fallback (Lexicon)"
    }

def analyze_face(image_bytes):
    try:
        # Load image via PIL
        image = Image.open(io.BytesIO(image_bytes))
        
        # Convert to RGB if in another mode
        if image.mode != "RGB":
            image = image.convert("RGB")
            
        # Center-crop the image to focus on the face (remove background borders)
        width, height = image.size
        crop_size = min(width, height)
        # Crop to square
        left = (width - crop_size) / 2
        top = (height - crop_size) / 2
        right = (width + crop_size) / 2
        bottom = (height + crop_size) / 2
        image = image.crop((left, top, right, bottom))
        
        # Resize to exactly 224x224 (ViT model input size)
        image = image.resize((224, 224), Image.Resampling.LANCZOS)
        
        # Create thumbnail to return (120x120 pixels, medium quality)
        thumb_io = io.BytesIO()
        thumb_img = image.copy()
        thumb_img.thumbnail((120, 120))
        thumb_img.save(thumb_io, format="JPEG", quality=70)
        thumb_b64 = "data:image/jpeg;base64," + base64.b64encode(thumb_io.getvalue()).decode('utf-8')
    except Exception as e:
        print(f"PIL Face processing failed: {e}")
        return {
            "emotion": "unknown",
            "sentiment": "neutral",
            "confidence": 0.5,
            "method": "Error decoding image",
            "thumbnail": None
        }

    # Run classification
    if _vision_model_loaded and _vision_pipeline:
        try:
            # ViT inference
            results = _vision_pipeline(image)
            if results:
                # Results are sorted by score desc
                top = results[0]
                emotion = top["label"].lower()
                score = float(top["score"])
                
                # Map standard ViT labels: angry, disgust, fear, happy, sad, surprise, neutral
                # Positive: happy, surprise
                # Neutral: neutral
                # Negative: angry, disgust, fear, sad
                if emotion in ["happy", "surprise"]:
                    sentiment = "positive"
                elif emotion in ["angry", "disgust", "fear", "sad"]:
                    sentiment = "negative"
                else:
                    sentiment = "neutral"
                    
                return {
                    "emotion": emotion,
                    "sentiment": sentiment,
                    "confidence": round(score, 4),
                    "method": f"Hugging Face ({VISION_MODEL_NAME.split('/')[-1]})",
                    "thumbnail": thumb_b64
                }
        except Exception as e:
            print(f"ViT Vision inference failed: {e}. Using fallback.")
            
    # Fallback response (e.g. if model is still downloading)
    return {
        "emotion": "neutral (loading model...)",
        "sentiment": "neutral",
        "confidence": 0.5,
        "method": "Vision Fallback (Downloading AI Model...)",
        "thumbnail": thumb_b64
    }

# Run setup in background
init_analyzer()
