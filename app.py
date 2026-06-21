import os
import io
import time
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

# Load env variables
load_dotenv()

# Import database and analyzer
import database
import analyzer

# Set Page Config
st.set_page_config(
    page_title="SentiMind AI - Sentiment Analyzer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Glassmorphic dark aesthetic with high-contrast text readability
st.markdown("""
    <style>
    /* Import fonts */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');
    
    /* General styles */
    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
        background-color: #080a12;
        color: #e5e7eb !important;
    }
    
    /* Force markdown paragraphs and lists to be highly legible */
    [data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] li {
        color: #e5e7eb !important;
        font-size: 0.95rem;
    }
    
    /* Title fonts */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Outfit', sans-serif;
        color: #ffffff !important;
    }
    
    /* Sidebar text color overrides for high-contrast legibility */
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p, 
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] li,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] span {
        color: #e5e7eb !important;
    }
    
    [data-testid="stSidebar"] h3, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h1 {
        color: #ffffff !important;
    }
    
    /* Sidebar background glassmorphism */
    [data-testid="stSidebar"] {
        background-color: rgba(11, 15, 30, 0.95) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.08) !important;
        backdrop-filter: blur(12px);
    }
    
    /* Tab buttons readability and contrast */
    [data-baseweb="tab"] p {
        color: #d1d5db !important;
        font-weight: 500 !important;
        font-size: 0.95rem !important;
    }
    
    [aria-selected="true"] [data-baseweb="tab"] p, 
    [data-baseweb="tab"][aria-selected="true"] p {
        color: #ffffff !important;
        font-weight: 700 !important;
    }
    
    /* Card panel styling */
    .glass-card {
        background: rgba(17, 22, 40, 0.75);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.4);
        backdrop-filter: blur(16px);
        margin-bottom: 1.5rem;
    }
    
    /* Sentiment badges */
    .sentiment-badge {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.8rem;
        text-transform: uppercase;
    }
    .sentiment-badge.positive {
        background: rgba(16, 185, 129, 0.15);
        color: #10b981;
        border: 1px solid rgba(16, 185, 129, 0.35);
    }
    .sentiment-badge.neutral {
        background: rgba(245, 158, 11, 0.15);
        color: #f59e0b;
        border: 1px solid rgba(245, 158, 11, 0.35);
    }
    .sentiment-badge.negative {
        background: rgba(239, 68, 68, 0.15);
        color: #ef4444;
        border: 1px solid rgba(239, 68, 68, 0.35);
    }
    
    /* Header brand */
    .brand-title {
        font-size: 2.2rem;
        font-weight: 800;
        margin: 0;
        line-height: 1.1;
    }
    .brand-accent {
        background: linear-gradient(135deg, #6366f1, #a855f7);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .brand-subtitle {
        font-size: 1rem;
        color: #d1d5db !important;
        margin-bottom: 1.5rem;
        font-weight: 400;
    }
    
    /* KPI block */
    .kpi-container {
        display: flex;
        gap: 1rem;
        flex-wrap: wrap;
        margin-bottom: 1.5rem;
    }
    .kpi-card {
        flex: 1;
        min-width: 180px;
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 12px;
        padding: 1rem;
        display: flex;
        flex-direction: column;
        gap: 0.25rem;
        transition: transform 0.2s;
    }
    .kpi-card:hover {
        transform: translateY(-2px);
        background: rgba(255, 255, 255, 0.05);
        border-color: rgba(99, 102, 241, 0.3);
    }
    .kpi-val {
        font-size: 1.8rem;
        font-weight: 700;
        line-height: 1.1;
        font-family: 'Outfit', sans-serif;
    }
    .kpi-lbl {
        font-size: 0.8rem;
        color: #d1d5db;
    }
    
    /* Connection badge status */
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(255, 255, 255, 0.08);
        padding: 0.35rem 0.85rem;
        border-radius: 20px;
        font-size: 0.75rem;
        color: #f3f4f6;
        margin-right: 0.5rem;
        margin-bottom: 0.5rem;
    }
    .status-indicator {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        display: inline-block;
    }
    .status-indicator.green {
        background-color: #10b981;
        box-shadow: 0 0 6px #10b981;
    }
    .status-indicator.yellow {
        background-color: #f59e0b;
        box-shadow: 0 0 6px #f59e0b;
    }
    
    /* Custom button enhancements */
    .stButton>button {
        border-radius: 10px !important;
        font-weight: 600 !important;
        transition: all 0.2s !important;
    }
    .stButton>button:hover {
        transform: scale(1.02);
    }
    
    /* Result Display */
    .result-text {
        font-size: 0.95rem;
        font-style: italic;
        color: #f3f4f6;
        border-left: 3px solid #6366f1;
        padding-left: 0.75rem;
        margin-top: 0.75rem;
        margin-bottom: 0.75rem;
    }
    </style>
""", unsafe_allow_html=True)

# --- Background Webcam Server ---
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import base64
import threading

class WebcamHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        return # suppress console request logging

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode('utf-8'))
            
            if self.path == '/analyze':
                img_b64 = data['image'].split(',')[1]
                img_bytes = base64.b64decode(img_b64)
                
                # Analyze face
                result = analyzer.analyze_face(img_bytes)
                
                self.send_response(200)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(result).encode('utf-8'))
                
            elif self.path == '/save':
                emotion = data.get('emotion', 'unknown')
                sentiment = data.get('sentiment', 'neutral')
                confidence = data.get('confidence', 0.5)
                thumbnail = data.get('thumbnail', None)
                
                review_text = f"Facial Scan: Detected {emotion.upper()} emotion"
                review_id = database.save_review(
                    text=review_text,
                    sentiment=sentiment,
                    confidence=confidence,
                    media_type="face",
                    image_data=thumbnail
                )
                
                self.send_response(200)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"success": True, "id": review_id}).encode('utf-8'))
                
        except Exception as e:
            self.send_response(500)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(str(e).encode('utf-8'))

# Global lock to start server once per python execution
_server_started_lock = threading.Lock()
_server_started = False

def start_background_server():
    global _server_started
    with _server_started_lock:
        if not _server_started:
            def run_server():
                try:
                    server = HTTPServer(('127.0.0.1', 5001), WebcamHandler)
                    server.serve_forever()
                except Exception as e:
                    print(f"Webcam Server Error: {e}")
            
            thread = threading.Thread(target=run_server, daemon=True)
            thread.start()
            _server_started = True

# Start background server
start_background_server()

# Main Application Title Banner
col_title, col_status = st.columns([2, 1])

with col_title:
    st.markdown('<h1 class="brand-title">SentiMind <span class="brand-accent">AI</span></h1>', unsafe_allow_html=True)
    st.markdown('<p class="brand-subtitle">AI-Powered Sentiment Analyzer & Reporting Dashboard</p>', unsafe_allow_html=True)

# Get status details
db_info = database.get_db_status()
model_loaded = analyzer._model_loaded
model_name = analyzer.MODEL_NAME.split('/')[-1]

with col_status:
    # DB Status badge
    db_class = "green" if db_info["type"] == "MongoDB" else "yellow"
    db_badge_html = f'<div class="status-badge"><span class="status-indicator {db_class}"></span><span>Storage: <b>{db_info["type"]}</b></span></div>'
    
    # Model status badge
    model_class = "green" if model_loaded else "yellow"
    model_label = f"Hugging Face: {model_name}" if model_loaded else "Fallback (Loading HF...)"
    model_badge_html = f'<div class="status-badge"><span class="status-indicator {model_class}"></span><span>Model: <b>{model_label}</b></span></div>'
    
    st.markdown(f'<div style="text-align: right;">{db_badge_html}{model_badge_html}</div>', unsafe_allow_html=True)

# Session state initialization for holding last single query result
if "last_query" not in st.session_state:
    st.session_state.last_query = None

# Sidebar Configuration
st.sidebar.image("https://img.icons8.com/nolan/128/artificial-intelligence.png", width=70)
st.sidebar.markdown("### Dashboard Control Panel")
st.sidebar.write("Configure details or access quick exports.")

# Add model refresh option in sidebar
if st.sidebar.button("🔄 Reload AI Model Connection"):
    with st.spinner("Re-initializing model components..."):
        analyzer.init_analyzer()
        time.sleep(1.5)
        st.rerun()

# DB status description in sidebar
st.sidebar.markdown("---")
st.sidebar.markdown(f"**Database Details**")
st.sidebar.markdown(f"- Type: `{db_info['type']}`")
st.sidebar.markdown(f"- Host/Path: `{db_info['host']}`")
st.sidebar.markdown(f"- Status: `{db_info['status']}`")

# ----------------- Main Layout Tabs -----------------
tab_input, tab_analytics, tab_history = st.tabs([
    "📥 Sentiment Input & Analysis", 
    "📊 Real-time Analytics & Reports", 
    "📜 Historical Database Logs"
])

# Tab 1: Sentiment Input & Analysis
with tab_input:
    st.write("")
    col_entry, col_preview = st.columns([1.1, 0.9])
    
    with col_entry:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("### Analysis Panel")
        
        mode = st.radio("Choose Analysis Type:", ["Single Text Input", "Batch File Upload (CSV/JSON)", "📷 Live Face Sentiment Scan"], horizontal=True)
        
        if mode == "Single Text Input":
            user_text = st.text_area(
                "Review Text:",
                placeholder="Type or paste social media reviews, product feedback, or any text here...",
                max_chars=1000,
                height=150
            )
            
            # Show word count
            words = len(user_text.split()) if user_text else 0
            st.caption(f"Word count: {words} | Characters: {len(user_text)}/1000")
            
            if st.button("🚀 Analyze Sentiment", use_container_width=True):
                if not user_text.strip():
                    st.warning("Please input some text before analyzing.")
                else:
                    with st.spinner("Inference in progress..."):
                        result = analyzer.analyze_sentiment(user_text)
                        # Save to database
                        db_id = database.save_review(user_text, result["sentiment"], result["confidence"])
                        
                        st.session_state.last_query = {
                            "text": user_text,
                            "sentiment": result["sentiment"],
                            "confidence": result["confidence"],
                            "method": result["method"],
                            "id": db_id
                        }
                        st.success("Review successfully analyzed and saved to database!")
                        
        elif mode == "Batch File Upload (CSV/JSON)":
            # Batch Upload mode
            uploaded_file = st.file_uploader(
                "Upload Reviews File:",
                type=["csv", "json", "xlsx", "xls"],
                help="Supports CSV, JSON, and Excel documents. We will scan for text columns like 'review', 'comment', or 'text'."
            )
            
            if uploaded_file:
                # Read file
                filename = uploaded_file.name.lower()
                try:
                    if filename.endswith(".csv"):
                        df = pd.read_csv(uploaded_file)
                    elif filename.endswith(".json"):
                        df = pd.read_json(uploaded_file)
                    else:
                        df = pd.read_excel(uploaded_file)
                        
                    st.success(f"Successfully loaded '{uploaded_file.name}' ({len(df)} rows)")
                    
                    # Columns selector
                    possible_cols = ["text", "review", "content", "body", "comment", "feedback"]
                    default_col = df.columns[0]
                    for col in df.columns:
                        if col.lower() in possible_cols:
                            default_col = col
                            break
                            
                    selected_col = st.selectbox("Select column containing reviews:", df.columns, index=list(df.columns).index(default_col))
                    
                    # Run batch button
                    if st.button("⚡ Run Batch Analysis", use_container_width=True):
                        # Progress bar setup
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        analyzed_count = 0
                        results = []
                        
                        start_time = time.time()
                        
                        total_rows = len(df)
                        for i, row in df.iterrows():
                            val = row[selected_col]
                            if pd.isna(val):
                                continue
                            text = str(val).strip()
                            if not text:
                                continue
                                
                            res = analyzer.analyze_sentiment(text)
                            database.save_review(text, res["sentiment"], res["confidence"])
                            
                            analyzed_count += 1
                            
                            # Update progress
                            pct = int((i + 1) / total_rows * 100)
                            progress_bar.progress(pct)
                            status_text.text(f"Processed: {analyzed_count} / {total_rows} reviews...")
                            
                        duration = time.time() - start_time
                        progress_bar.progress(100)
                        status_text.success(f"Batch complete! Analyzed {analyzed_count} reviews in {duration:.2f}s.")
                        
                        # Trigger fresh stats
                        st.balloons()
                        
                except Exception as e:
                    st.error(f"Error parsing file: {e}")
                    
        elif mode == "📷 Live Face Sentiment Scan":
            st.markdown("#### Real-time live camera feed")
            st.write("Grant camera permissions to start real-time emotion detection. Smile or change facial expressions to see overlays update in real-time!")
            
            webcam_html = """
            <div style="position: relative; width: 400px; margin: 0 auto; background: #111322; padding: 10px; border-radius: 16px; border: 1px solid rgba(255,255,255,0.08);">
                <div style="position: relative; width: 400px; height: 300px; border-radius: 12px; overflow: hidden; background: #000;">
                    <video id="webcam" width="400" height="300" autoplay muted playsinline style="transform: scaleX(-1); object-fit: cover;"></video>
                    <canvas id="overlay" width="400" height="300" style="position: absolute; top:0; left:0; transform: scaleX(-1); pointer-events: none;"></canvas>
                </div>
                <div id="status-text" style="color: #9ca3af; font-size: 0.8rem; margin-top: 8px; font-weight: 500; font-family: sans-serif; text-align: center;">Starting camera...</div>
                <button id="save-btn" style="width: 100%; margin-top: 10px; padding: 10px; background: linear-gradient(135deg, #6366f1, #a855f7); color: white; border: none; border-radius: 8px; font-weight: bold; font-family: sans-serif; cursor: pointer; transition: transform 0.1s;">
                    💾 Save Current Face Scan to Database
                </button>
            </div>
            
            <script>
            const video = document.getElementById('webcam');
            const canvas = document.getElementById('overlay');
            const ctx = canvas.getContext('2d');
            const statusText = document.getElementById('status-text');
            const saveBtn = document.getElementById('save-btn');
            
            let currentResult = null;
            let captureCanvas = document.createElement('canvas');
            captureCanvas.width = 400;
            captureCanvas.height = 300;
            let captureCtx = captureCanvas.getContext('2d');
            
            // Start video with ideal dimensions for near-instant startup
            navigator.mediaDevices.getUserMedia({ video: { width: { ideal: 400 }, height: { ideal: 300 }, facingMode: "user" } })
                .then(stream => {
                    video.srcObject = stream;
                    statusText.textContent = "Camera active. Running real-time emotion detection...";
                    
                    // Start analysis loop (every 800ms)
                    setInterval(analyzeFrame, 800);
                })
                .catch(err => {
                    console.error("Camera access error:", err);
                    statusText.textContent = "Camera access denied or unavailable: " + err.message;
                    statusText.style.color = "#ef4444";
                });
                
            function analyzeFrame() {
                if (video.readyState === video.HAVE_ENOUGH_DATA) {
                    captureCtx.drawImage(video, 0, 0, 400, 300);
                    const dataUrl = captureCanvas.toDataURL('image/jpeg', 0.6);
                    
                    fetch('http://127.0.0.1:5001/analyze', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ image: dataUrl })
                    })
                    .then(res => res.json())
                    .then(data => {
                        currentResult = data;
                        drawOverlay(data);
                    })
                    .catch(err => {
                        console.error("Analysis server connection error:", err);
                    });
                }
            }
            
            function drawOverlay(data) {
                ctx.clearRect(0, 0, 400, 300);
                
                let color = '#f59e0b'; // neutral yellow
                if (data.sentiment === 'positive') color = '#10b981'; // green
                if (data.sentiment === 'negative') color = '#ef4444'; // red
                
                // Draw face guide oval in the center (dotted outline)
                ctx.strokeStyle = 'rgba(255, 255, 255, 0.35)';
                ctx.lineWidth = 2;
                ctx.setLineDash([6, 6]);
                ctx.beginPath();
                ctx.ellipse(200, 150, 90, 120, 0, 0, 2 * Math.PI);
                ctx.stroke();
                ctx.setLineDash([]); // reset to solid
                
                // Draw bounding box border around the screen
                ctx.strokeStyle = color;
                ctx.lineWidth = 6;
                ctx.strokeRect(3, 3, 394, 294);
                
                // Draw emotion tag at the top
                ctx.fillStyle = color;
                ctx.fillRect(15, 15, 180, 35);
                
                ctx.fillStyle = '#ffffff';
                ctx.font = 'bold 14px Arial';
                ctx.fillText(`${data.emotion.toUpperCase()} (${(data.confidence*100).toFixed(0)}%)`, 25, 38);
                
                statusText.textContent = `Live Scan: Mapped to ${data.sentiment.toUpperCase()} sentiment.`;
                statusText.style.color = color;
            }
            
            saveBtn.onclick = () => {
                if (!currentResult) {
                    alert("Awaiting first classification from camera stream...");
                    return;
                }
                
                saveBtn.disabled = true;
                saveBtn.textContent = "Saving to Database...";
                
                fetch('http://127.0.0.1:5001/save', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(currentResult)
                })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        statusText.textContent = "💾 Face scan review saved successfully!";
                        statusText.style.color = "#10b981";
                        setTimeout(() => {
                            saveBtn.disabled = false;
                            saveBtn.textContent = "💾 Save Current Face Scan to Database";
                        }, 2500);
                    } else {
                        alert("Save failed.");
                        saveBtn.disabled = false;
                        saveBtn.textContent = "💾 Save Current Face Scan to Database";
                    }
                })
                .catch(err => {
                    console.error("Save error:", err);
                    alert("Could not connect to backend database endpoint.");
                    saveBtn.disabled = false;
                    saveBtn.textContent = "💾 Save Current Face Scan to Database";
                });
            };
            </script>
            """
            
            st.components.v1.html(webcam_html, height=410)
            st.info("💡 Once saved, you can view your facial expression scans in the 'Historical Database Logs' tab (complete with thumbnails!). Make sure to click 'Refresh Dashboards' under the Analytics tab to update aggregate reports.")
            
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col_preview:
        st.markdown('<div class="glass-card" style="height: 100%;">', unsafe_allow_html=True)
        st.markdown("### Real-time Result Output")
        
        if st.session_state.last_query:
            q = st.session_state.last_query
            sentiment = q["sentiment"].upper()
            confidence_pct = q["confidence"] * 100
            
            # Badge styles
            badge_class = q["sentiment"].lower()
            
            st.markdown(f'<div style="margin-top: 1rem;"><span class="sentiment-badge {badge_class}">{sentiment}</span><span style="font-size: 0.85rem; color: #9ca3af; margin-left: 10px;">({q["method"]})</span></div>', unsafe_allow_html=True)
            
            # Confidence meter
            st.write("")
            st.metric(label="Inference Confidence", value=f"{confidence_pct:.1f}%")
            st.progress(q["confidence"])
            
            # Text Preview
            st.markdown("**Analyzed Review Text:**")
            st.markdown(f'<p class="result-text">"{q["text"]}"</p>', unsafe_allow_html=True)
            
            # Distribution details
            st.caption("Review ID: " + q["id"])
        else:
            st.info("Awaiting input analysis... Type a review or load a batch file to view real-time classifications here.")
            
        st.markdown('</div>', unsafe_allow_html=True)

# Tab 2: Analytics & Reports
with tab_analytics:
    st.write("")
    
    # Reload stats button
    col_sub_title, col_ref = st.columns([3, 1])
    with col_sub_title:
        st.markdown("### Reports and Metrics Summary")
    with col_ref:
        ref_btn = st.button("🔄 Refresh Dashboards", use_container_width=True)
        
    # Get statistics
    stats = database.get_sentiment_statistics()
    
    # Render KPIs
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    
    total_reviews = stats["total"]
    
    if total_reviews > 0:
        pos_p = (stats["counts"]["positive"] / total_reviews) * 100
        neu_p = (stats["counts"]["neutral"] / total_reviews) * 100
        neg_p = (stats["counts"]["negative"] / total_reviews) * 100
    else:
        pos_p = neu_p = neg_p = 0
        
    with kpi1:
        st.markdown(f'<div class="kpi-card"><span class="kpi-val" style="color: #6366f1;">{total_reviews:,}</span><span class="kpi-lbl">Total Reviews Analyzed</span></div>', unsafe_allow_html=True)
    with kpi2:
        st.markdown(f'<div class="kpi-card"><span class="kpi-val" style="color: #10b981;">{pos_p:.1f}%</span><span class="kpi-lbl">Positive Sentiments</span></div>', unsafe_allow_html=True)
    with kpi3:
        st.markdown(f'<div class="kpi-card"><span class="kpi-val" style="color: #f59e0b;">{neu_p:.1f}%</span><span class="kpi-lbl">Neutral Sentiments</span></div>', unsafe_allow_html=True)
    with kpi4:
        st.markdown(f'<div class="kpi-card"><span class="kpi-val" style="color: #ef4444;">{neg_p:.1f}%</span><span class="kpi-lbl">Negative Sentiments</span></div>', unsafe_allow_html=True)
        
    st.write("")
    
    # Render Charts
    col_chart_ratio, col_chart_trend, col_chart_conf = st.columns([0.9, 1.2, 0.9])
    
    with col_chart_ratio:
        st.markdown("#### Sentiment Distribution")
        if total_reviews > 0:
            ratio_df = pd.DataFrame({
                "Sentiment": ["Positive", "Neutral", "Negative"],
                "Count": [stats["counts"]["positive"], stats["counts"]["neutral"], stats["counts"]["negative"]]
            })
            st.bar_chart(ratio_df.set_index("Sentiment"), y="Count", color="#a855f7")
        else:
            st.info("No stats available.")
            
    with col_chart_trend:
        st.markdown("#### Confidence Trends (Last 30 Reviews)")
        trend_list = stats["trend"]
        if trend_list:
            trend_df = pd.DataFrame(trend_list)
            # Map confidence to percentage
            trend_df["Confidence %"] = trend_df["confidence"] * 100
            # Set index to datetime/index
            st.line_chart(trend_df["Confidence %"], y_label="Confidence (%)", color="#6366f1")
        else:
            st.info("Awaiting reviews data to plot trend line.")
            
    with col_chart_conf:
        st.markdown("#### Avg. Confidence by Class")
        if total_reviews > 0:
            avg_df = pd.DataFrame({
                "Sentiment": ["Positive", "Neutral", "Negative"],
                "Avg Confidence %": [
                    stats["averages"]["positive"] * 100, 
                    stats["averages"]["neutral"] * 100, 
                    stats["averages"]["negative"] * 100
                ]
            })
            st.bar_chart(avg_df.set_index("Sentiment"), y="Avg Confidence %", color="#10b981")
        else:
            st.info("No stats available.")

# Tab 3: Historical logs
with tab_history:
    st.write("")
    st.markdown("### Filter & Search Database Logs")
    
    col_fil_search, col_fil_sent = st.columns([2.5, 1.5])
    
    with col_fil_search:
        search_q = st.text_input("Search reviews:", placeholder="Filter by review keyword...")
        
    with col_fil_sent:
        selected_filter = st.selectbox("Filter by Sentiment Category:", ["All", "Positive", "Neutral", "Negative"])
        
    # Pagination state
    if "hist_offset" not in st.session_state:
        st.session_state.hist_offset = 0
        
    # Fetch filtered history
    history_reviews = database.get_reviews_history(
        limit=10,
        offset=st.session_state.hist_offset,
        sentiment_filter=selected_filter.lower(),
        search_query=search_q
    )
    
    # Retrieve all for client-side download
    all_filtered = database.get_reviews_history(
        limit=1000,
        offset=0,
        sentiment_filter=selected_filter.lower(),
        search_query=search_q
    )
    
    # Actions for pagination and export
    col_export, col_pag = st.columns([2, 2])
    
    with col_export:
        if all_filtered:
            # Build download frame
            df_export = pd.DataFrame(all_filtered)
            csv_data = df_export.to_csv(index=False)
            json_data = df_export.to_json(orient="records", indent=2)
            
            st.download_button("📥 Export as CSV", data=csv_data, file_name="sentimind_history.csv", mime="text/csv")
            st.download_button("📥 Export as JSON", data=json_data, file_name="sentimind_history.json", mime="application/json")
        else:
            st.caption("No records available to download.")
            
    with col_pag:
        col_pag_prev, col_pag_next = st.columns(2)
        with col_pag_prev:
            if st.button("⬅️ Previous 10 Rows", disabled=st.session_state.hist_offset == 0, use_container_width=True):
                st.session_state.hist_offset = max(0, st.session_state.hist_offset - 10)
                st.rerun()
        with col_pag_next:
            # Simple check if there might be more rows
            if st.button("Next 10 Rows ➡️", disabled=len(history_reviews) < 10, use_container_width=True):
                st.session_state.hist_offset += 10
                st.rerun()
                
    st.write("")
    
    # Display table with inline delete buttons
    if history_reviews:
        # Create columns headers
        col_th_text, col_th_sent, col_th_conf, col_th_date, col_th_act = st.columns([3, 1, 1, 1.5, 0.75])
        with col_th_text: st.markdown("<b>Review Text Snippet</b>", unsafe_allow_html=True)
        with col_th_sent: st.markdown("<b>Sentiment</b>", unsafe_allow_html=True)
        with col_th_conf: st.markdown("<b>Confidence</b>", unsafe_allow_html=True)
        with col_th_date: st.markdown("<b>Date Added</b>", unsafe_allow_html=True)
        with col_th_act: st.markdown("<b>Delete</b>", unsafe_allow_html=True)
        st.markdown("---")
        
        for r in history_reviews:
            col_tr_text, col_tr_sent, col_tr_conf, col_tr_date, col_tr_act = st.columns([3, 1, 1, 1.5, 0.75])
            
            # Format text length
            snippet = r["text"]
            if len(snippet) > 150:
                snippet = snippet[:150] + "..."
                
            # Date formatting
            try:
                date_clean = r["timestamp"].replace("T", " ")[:16]
            except:
                date_clean = r["timestamp"]
                
            with col_tr_text:
                if r.get("media_type") == "face" and r.get("image_data"):
                    html_layout = f'<div style="display: flex; align-items: center; gap: 10px;"><img src="{r["image_data"]}" style="width: 40px; height: 40px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.1); object-fit: cover;" /><div><span style="font-size: 0.7rem; color: #a855f7; font-weight: bold; text-transform: uppercase;">📷 Face Scan</span><p style="margin: 0; font-size: 0.85rem; color: #e5e7eb; line-height: 1.2;">{snippet}</p></div></div>'
                    st.markdown(html_layout, unsafe_allow_html=True)
                else:
                    html_layout = f'<div style="display: flex; align-items: center; gap: 10px;"><div style="width: 40px; height: 40px; border-radius: 8px; background: rgba(99,102,241,0.15); display: flex; align-items: center; justify-content: center; color: #6366f1; font-weight: bold; font-size: 1.1rem;">📝</div><div><span style="font-size: 0.7rem; color: #6366f1; font-weight: bold; text-transform: uppercase;">📝 Text Review</span><p style="margin: 0; font-size: 0.85rem; color: #e5e7eb; line-height: 1.2;">{snippet}</p></div></div>'
                    st.markdown(html_layout, unsafe_allow_html=True)
            with col_tr_sent:
                badge_class = r["sentiment"].lower()
                st.markdown(f'<span class="sentiment-badge {badge_class}">{r["sentiment"]}</span>', unsafe_allow_html=True)
            with col_tr_conf:
                st.write(f"{r['confidence'] * 100:.1f}%")
            with col_tr_date:
                st.write(date_clean)
            with col_tr_act:
                # Create a key based on review ID so Streamlit can track click actions
                if st.button("🗑️", key=f"del-{r['id']}", help="Delete review from storage"):
                    database.delete_review(r["id"])
                    st.success("Record deleted successfully.")
                    time.sleep(0.5)
                    st.rerun()
    else:
        st.info("No records match your filters.")

# Footer section
st.markdown("---")
st.markdown(
    "<p style='text-align: center; font-size: 0.75rem; color: #6b7280;'>"
    "SentiMind AI Sentiment Analyzer &copy; 2026. Powered by Streamlit & Hugging Face Transformers."
    "</p>",
    unsafe_allow_html=True
)
