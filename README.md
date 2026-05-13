# Ads Analyzer

Analyze ad creatives from a single brand, score their likely performance, surface winning patterns, and generate new creative ideas — all powered by AI.

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) installed on your system
  - **Windows:** Download installer from [UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki)
  - **Mac:** `brew install tesseract`
  - **Linux:** `sudo apt install tesseract-ocr`
- A free [Groq API key](https://console.groq.com)

### Setup

```bash
# Clone / navigate to project
cd ads_analyzer

# Create virtual environment
python -m venv venv
venv\Scripts\activate       # Windows
# source venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

The app will open at `http://localhost:8501`.

> **Note:** If pytesseract/Tesseract is not installed, OCR will silently fail and return empty text. The app still works — OCR is supplementary context for the LLM.

---

## 📁 Project Structure

```
ads_analyzer/
├── app.py              # Main Streamlit application (UI + orchestration)
├── utils.py            # OCR, JSON parsing, image encoding, Groq API client
├── prompts.py          # All LLM prompt templates
├── scoring.py          # Deterministic heuristic scoring engine
├── requirements.txt    # Python dependencies
└── README.md           # This file
```

**Why this flat structure?** This is an MVP. A flat layout means any engineer can understand the entire codebase in 10 minutes. No unnecessary abstractions.

---

## 🧠 How the Heuristic Scoring Works

Each ad is scored out of **100 points** across 8 dimensions:

| Dimension            | Max Points | How It's Scored |
|----------------------|-----------|-----------------|
| **Strong Hook**       | 20        | Hook type classification (pain-point, curiosity, question = max) |
| **Human Face/Emotion**| 15        | Face detected (10pts) + strong emotional trigger (5pts) |
| **Clear CTA**         | 10        | Matches known high-performing CTAs (Shop Now, Get Started, etc.) |
| **Problem-Solution**  | 15        | Pain-point hook + problem/solution keywords in text |
| **Visual Clarity**    | 10        | Low/medium text density + clean visual style |
| **UGC Authenticity**  | 10        | UGC visual style + authentic language signals |
| **Social Proof**      | 10        | Testimonial/review keywords, social-proof hook type |
| **Offer/Urgency**     | 10        | Urgency language, limited-time offers, discount signals |

**The scoring is fully deterministic** — same analysis input always produces the same score. No ML, no randomness. Every point is explainable via the score breakdown view.

### Score Tiers

| Score Range | Tier |
|-------------|------|
| 80–100      | Top Performer |
| 60–79       | Strong |
| 40–59       | Average |
| 0–39        | Weak |

---

## 🔄 Processing Flow

```
Upload Images
     │
     ▼
┌─────────────┐
│ For each ad: │
│  1. OCR      │──→ Extract visible text (pytesseract)
│  2. Encode   │──→ Resize + base64 encode image
│  3. LLM Call │──→ Send image + OCR text to Groq vision model
│  4. Parse    │──→ Extract JSON from response (3-layer fallback)
│  5. Score    │──→ Apply heuristic scoring (deterministic)
└─────────────┘
     │
     ▼
Cross-Creative Insights (single LLM call with all summaries)
     │
     ▼
Creative Recommendations (single LLM call based on patterns)
     │
     ▼
Display Results + CSV Export
```





## ⚖️ Tradeoffs Made

| Decision | Why |
|----------|-----|
| **Groq over OpenAI** | Free tier, fast inference, vision-capable Llama 4 models |
| **Heuristic scoring over ML** | Transparent, explainable, deterministic — better for an MVP |
| **pytesseract for OCR** | Simple, free, good enough for ad text extraction |
| **Single-page Streamlit** | Ships fast, no routing complexity, good enough UX |
| **No database** | Results are per-session. Export via CSV if needed |
| **No authentication** | MVP scope — user provides their own API key |
| **Sequential processing** | Simpler than async. Groq is fast enough for 10-15 images |



---


