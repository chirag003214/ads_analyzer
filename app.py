import streamlit as st
import pandas as pd
from PIL import Image
import time
import json
import os
from dotenv import load_dotenv

from utils import (
    extract_text_ocr, parse_json_safe, encode_image_base64,
    call_groq_vision, call_groq_text, get_default_analysis,
)
from prompts import ANALYSIS_PROMPT, INSIGHT_PROMPT, RECOMMENDATION_PROMPT
from scoring import score_creative, get_score_tier

# ── Load API key from .env ───────────────────────────────────
# Use the script's own directory so .env is found regardless of cwd
_script_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(_script_dir, ".env"), override=True)
API_KEY = os.getenv("GROQ_API_KEY", "").strip().strip('"').strip("'")
MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"

# ── Page Config ──────────────────────────────────────────────
st.set_page_config(
    page_title="CreativeLens — Ads Creative Analyzer",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Premium Dark CSS ─────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* ── Global ── */
html, body, .main, .stApp {
    font-family: 'Inter', sans-serif !important;
}
.main .block-container {
    padding: 2rem 3rem;
    max-width: 1280px;
}

/* ── Hero Header ── */
.hero {
    text-align: center;
    padding: 3rem 1rem 2rem;
}
.hero h1 {
    font-size: 3rem;
    font-weight: 800;
    background: linear-gradient(135deg, #818cf8, #c084fc, #f472b6);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.25rem;
    letter-spacing: -1px;
}
.hero p {
    font-size: 1.1rem;
    opacity: 0.6;
    max-width: 520px;
    margin: 0 auto;
    line-height: 1.6;
}

/* ── Stat Cards Row ── */
.stats-row {
    display: flex;
    gap: 16px;
    margin: 1.5rem 0 2rem;
    justify-content: center;
    flex-wrap: wrap;
}
.stat-card {
    background: linear-gradient(145deg, rgba(99,102,241,0.12), rgba(139,92,246,0.06));
    border: 1px solid rgba(129,140,248,0.15);
    border-radius: 16px;
    padding: 20px 28px;
    text-align: center;
    min-width: 160px;
    backdrop-filter: blur(10px);
}
.stat-card .num {
    font-size: 2rem;
    font-weight: 800;
    background: linear-gradient(135deg, #818cf8, #c084fc);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.stat-card .label {
    font-size: 0.8rem;
    opacity: 0.5;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-top: 4px;
}

/* ── Score Badge ── */
.score-badge {
    display: inline-flex;
    align-items: center;
    padding: 6px 18px;
    border-radius: 24px;
    font-weight: 700;
    font-size: 1rem;
    color: white;
    margin: 8px 0;
    letter-spacing: -0.3px;
}

/* ── Ad Card ── */
.ad-card {
    background: linear-gradient(160deg, rgba(30,27,55,0.6), rgba(20,18,40,0.4));
    border: 1px solid rgba(129,140,248,0.1);
    border-radius: 16px;
    padding: 20px;
    margin-bottom: 20px;
    transition: border-color 0.3s, transform 0.2s;
}
.ad-card:hover {
    border-color: rgba(129,140,248,0.3);
    transform: translateY(-2px);
}

/* ── Tag Pills ── */
.tag-pill {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 500;
    margin: 3px 3px;
    letter-spacing: 0.2px;
}
.tag-green {
    background: rgba(52,211,153,0.12);
    color: #6ee7b7;
    border: 1px solid rgba(52,211,153,0.2);
}
.tag-red {
    background: rgba(248,113,113,0.12);
    color: #fca5a5;
    border: 1px solid rgba(248,113,113,0.2);
}
.tag-blue {
    background: rgba(129,140,248,0.12);
    color: #a5b4fc;
    border: 1px solid rgba(129,140,248,0.2);
}

/* ── Insight Box ── */
.insight-box {
    background: linear-gradient(145deg, rgba(99,102,241,0.08), rgba(192,132,252,0.06));
    border: 1px solid rgba(129,140,248,0.15);
    border-radius: 16px;
    padding: 24px;
    margin: 16px 0;
    font-size: 1rem;
    line-height: 1.7;
}

/* ── Recommendation Card ── */
.rec-card {
    background: linear-gradient(145deg, rgba(52,211,153,0.06), rgba(99,102,241,0.06));
    border: 1px solid rgba(52,211,153,0.15);
    border-radius: 16px;
    padding: 24px;
    margin: 16px 0;
    transition: border-color 0.3s;
}
.rec-card:hover {
    border-color: rgba(52,211,153,0.35);
}

/* ── Section Header ── */
.section-header {
    font-size: 1.6rem;
    font-weight: 700;
    margin: 2.5rem 0 0.5rem;
    padding-bottom: 12px;
    border-bottom: 2px solid rgba(129,140,248,0.15);
    letter-spacing: -0.5px;
}

/* ── Divider ── */
.divider {
    border: none;
    border-top: 1px solid rgba(129,140,248,0.08);
    margin: 2.5rem 0;
}

/* ── Empty State ── */
.empty-state {
    text-align: center;
    padding: 4rem 2rem;
    opacity: 0.7;
}
.empty-state h3 {
    font-size: 1.4rem;
    margin-bottom: 1rem;
}

/* ── Steps ── */
.step-row {
    display: flex;
    gap: 16px;
    justify-content: center;
    flex-wrap: wrap;
    margin-top: 1.5rem;
}
.step-item {
    background: rgba(129,140,248,0.06);
    border: 1px solid rgba(129,140,248,0.1);
    border-radius: 14px;
    padding: 20px;
    width: 200px;
    text-align: center;
}
.step-num {
    font-size: 1.6rem;
    font-weight: 800;
    background: linear-gradient(135deg, #818cf8, #c084fc);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.step-label {
    font-size: 0.85rem;
    margin-top: 6px;
    opacity: 0.7;
    line-height: 1.4;
}

/* ── Metric row ── */
.metric-label {
    font-size: 0.8rem;
    opacity: 0.5;
    margin-bottom: 2px;
}
.metric-value {
    font-size: 0.95rem;
    font-weight: 500;
}

/* ── Hide Streamlit Chrome ── */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
.stDeployButton {display: none;}

/* ── File uploader styling ── */
[data-testid="stFileUploader"] {
    border: 2px dashed rgba(129,140,248,0.2) !important;
    border-radius: 16px !important;
    padding: 1rem !important;
}
[data-testid="stFileUploader"]:hover {
    border-color: rgba(129,140,248,0.4) !important;
}

/* ── Button ── */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 0.7rem 2rem !important;
    font-weight: 600 !important;
    font-size: 1rem !important;
    letter-spacing: 0.3px !important;
    transition: transform 0.2s, box-shadow 0.2s !important;
}
.stButton > button[kind="primary"]:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 8px 25px rgba(99,102,241,0.3) !important;
}

/* ── Dataframe ── */
[data-testid="stDataFrame"] {
    border-radius: 12px !important;
    overflow: hidden;
}

/* ── Expander ── */
[data-testid="stExpander"] {
    border: 1px solid rgba(129,140,248,0.1) !important;
    border-radius: 12px !important;
}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
# SECTION 1: Hero + Upload
# ══════════════════════════════════════════════════════════════

st.markdown("""
<div class="hero">
    <h1>Ads-Analyzer</h1>
    <p>Upload ad creatives from any brand. Get AI-powered scoring, pattern analysis, and fresh creative ideas — instantly.</p>
</div>
""", unsafe_allow_html=True)

# Check for API key
if not API_KEY or API_KEY == "gsk_your_key_here":
    st.error("⚠️ **Groq API key not found.** Add your key to the `.env` file:  \n`GROQ_API_KEY=gsk_your_actual_key`  \nGet a free key → [console.groq.com](https://console.groq.com)")
    st.stop()

# File uploader
uploaded_files = st.file_uploader(
    "Drop your ad creatives here",
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=True,
    help="Upload 10–15 ad images from a single brand for best results.",
    label_visibility="collapsed",
)

# Upload area placeholder when empty
if not uploaded_files:
    st.markdown("""
    <div class="empty-state">
        <h3>📤 Upload 10–15 ad creatives to get started</h3>
        <p>Drag & drop JPG/PNG files above. Works best with ads from a single brand.</p>
        <div class="step-row">
            <div class="step-item">
                <div class="step-num">01</div>
                <div class="step-label">Upload ads</div>
            </div>
            <div class="step-item">
                <div class="step-num">02</div>
                <div class="step-label">AI analyzes each creative</div>
            </div>
            <div class="step-item">
                <div class="step-num">03</div>
                <div class="step-label">Score & rank performance</div>
            </div>
            <div class="step-item">
                <div class="step-num">04</div>
                <div class="step-label">Get new creative ideas</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ── Show uploaded previews ───────────────────────────────────
st.markdown(f"**{len(uploaded_files)} creatives uploaded**")
preview_cols = st.columns(min(len(uploaded_files), 6))
for idx, file in enumerate(uploaded_files[:12]):
    with preview_cols[idx % 6]:
        img = Image.open(file)
        st.image(img, caption=file.name[:18], use_container_width=True)
        file.seek(0)

if len(uploaded_files) > 12:
    st.caption(f"+ {len(uploaded_files) - 12} more")

st.markdown('<hr class="divider">', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
# Analysis Engine
# ══════════════════════════════════════════════════════════════

def analyze_single_ad(image, filename):
    """Full pipeline: OCR → encode → LLM → parse → score."""
    ocr_text = extract_text_ocr(image)
    image_b64 = encode_image_base64(image)
    prompt = ANALYSIS_PROMPT.format(ocr_text=ocr_text if ocr_text else "(No text detected)")
    raw = call_groq_vision(API_KEY, prompt, image_b64, model=MODEL)

    analysis = get_default_analysis()
    if raw:
        parsed = parse_json_safe(raw)
        if parsed and isinstance(parsed, dict):
            analysis = parsed

    return {
        "filename": filename,
        "ocr_text": ocr_text,
        "analysis": analysis,
        "score": score_creative(analysis),
        "raw_response": raw,
    }


# ══════════════════════════════════════════════════════════════
# SECTION 2: Run Analysis
# ══════════════════════════════════════════════════════════════

if st.button("🚀 Analyze All Creatives", type="primary", use_container_width=True):
    results = []
    progress = st.progress(0, text="Starting analysis...")

    for idx, file in enumerate(uploaded_files):
        progress.progress(idx / len(uploaded_files),
                          text=f"Analyzing {file.name} ({idx+1}/{len(uploaded_files)})...")
        try:
            result = analyze_single_ad(Image.open(file), file.name)
            results.append(result)
        except Exception as e:
            st.warning(f"⚠️ Failed: {file.name} — {e}")
            results.append({
                "filename": file.name, "ocr_text": "", "raw_response": None,
                "analysis": get_default_analysis(),
                "score": score_creative(get_default_analysis()),
            })
        if idx < len(uploaded_files) - 1:
            time.sleep(1)

    progress.progress(1.0, text="✅ Analysis complete!")
    st.session_state["results"] = results
    st.session_state["uploaded_files"] = uploaded_files
    # Clear cached insights/recs so they regenerate
    st.session_state.pop("insights", None)
    st.session_state.pop("recommendations", None)


# ══════════════════════════════════════════════════════════════
# Display Results
# ══════════════════════════════════════════════════════════════

if "results" not in st.session_state:
    st.stop()

results = st.session_state["results"]
uploaded_files_stored = st.session_state.get("uploaded_files", uploaded_files)
sorted_results = sorted(results, key=lambda x: x["score"]["total_score"], reverse=True)

# ── Stats Row ────────────────────────────────────────────────
avg_score = sum(r["score"]["total_score"] for r in results) // len(results)
top_score = sorted_results[0]["score"]["total_score"]
top_hooks = {}
for r in results:
    h = r["analysis"].get("hook_type", "?")
    top_hooks[h] = top_hooks.get(h, 0) + 1
most_common_hook = max(top_hooks, key=top_hooks.get) if top_hooks else "—"

st.markdown(f"""
<div class="stats-row">
    <div class="stat-card">
        <div class="num">{len(results)}</div>
        <div class="label">Ads Analyzed</div>
    </div>
    <div class="stat-card">
        <div class="num">{avg_score}</div>
        <div class="label">Avg Score</div>
    </div>
    <div class="stat-card">
        <div class="num">{top_score}</div>
        <div class="label">Top Score</div>
    </div>
    <div class="stat-card">
        <div class="num" style="font-size:1.2rem">{most_common_hook}</div>
        <div class="label">Top Hook Type</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Summary Table ────────────────────────────────────────────
st.markdown('<div class="section-header">📊 Performance Ranking</div>', unsafe_allow_html=True)

summary = []
for r in sorted_results:
    tier, _ = get_score_tier(r["score"]["total_score"])
    summary.append({
        "Ad": r["filename"][:28],
        "Score": r["score"]["total_score"],
        "Tier": tier,
        "Hook": r["analysis"].get("hook_type", "—"),
        "CTA": (r["analysis"].get("cta") or "—")[:30],
        "Style": r["analysis"].get("visual_style", "—"),
        "Emotion": r["analysis"].get("emotional_trigger", "—"),
    })
st.dataframe(pd.DataFrame(summary), use_container_width=True, hide_index=True)

st.markdown('<hr class="divider">', unsafe_allow_html=True)

# ── Detailed Cards ───────────────────────────────────────────
st.markdown('<div class="section-header">🃏 Detailed Breakdown</div>', unsafe_allow_html=True)

for i in range(0, len(sorted_results), 2):
    cols = st.columns(2)
    for j, col in enumerate(cols):
        idx = i + j
        if idx >= len(sorted_results):
            break
        r = sorted_results[idx]
        a = r["analysis"]
        sc = r["score"]
        tier_label, tier_color = get_score_tier(sc["total_score"])

        with col:
            st.markdown('<div class="ad-card">', unsafe_allow_html=True)

            # Show image
            for f in (uploaded_files_stored or []):
                if f.name == r["filename"]:
                    try:
                        f.seek(0)
                        st.image(Image.open(f), use_container_width=True)
                    except Exception:
                        pass
                    break

            st.markdown(
                f'<span class="score-badge" style="background:{tier_color}">'
                f'{sc["total_score"]}/100 — {tier_label}</span>',
                unsafe_allow_html=True)

            st.markdown(f"**{r['filename']}**")
            st.markdown(f"🪝 **Hook:** {a.get('hook_type','—')} — _{(a.get('headline') or '')[:80]}_")
            st.markdown(f"📣 **CTA:** {a.get('cta','—')}")
            st.markdown(f"🎨 **Style:** {a.get('visual_style','—')}  ·  💬 Density: {a.get('text_density','—')}")
            st.markdown(f"🎯 **Audience:** {a.get('target_audience','—')}")
            st.markdown(f"😊 **Emotion:** {a.get('emotional_trigger','—')}  ·  👤 Face: {'Yes' if a.get('has_face') else 'No'}")

            # Strength tags
            strengths = a.get("predicted_strengths", [])
            weaknesses = a.get("weaknesses", [])
            if strengths:
                st.markdown(" ".join(f'<span class="tag-pill tag-green">✓ {s}</span>' for s in strengths[:4]), unsafe_allow_html=True)
            if weaknesses:
                st.markdown(" ".join(f'<span class="tag-pill tag-red">✗ {w}</span>' for w in weaknesses[:3]), unsafe_allow_html=True)

            # Score breakdown expander
            with st.expander("📈 Score Breakdown"):
                max_map = {"strong_hook":20,"human_face_emotion":15,"clear_cta":10,
                           "problem_solution":15,"visual_clarity":10,"ugc_authenticity":10,
                           "social_proof":10,"offer_urgency":10}
                for dim, pts in sc["breakdown"].items():
                    mx = max_map.get(dim, 10)
                    st.progress(pts/mx if mx else 0, text=f"{dim.replace('_',' ').title()}: {pts}/{mx}")
                    st.caption(sc["explanations"].get(dim, ""))

            st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<hr class="divider">', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# SECTION 3: Cross-Creative Insights
# ══════════════════════════════════════════════════════════════

st.markdown('<div class="section-header">💡 Key Insights</div>', unsafe_allow_html=True)

# Build summary text for LLM
ads_summary_parts = []
for r in sorted_results:
    a, s = r["analysis"], r["score"]
    ads_summary_parts.append(
        f"- '{r['filename']}' (Score:{s['total_score']}): hook={a.get('hook_type','?')}, "
        f"emotion={a.get('emotional_trigger','?')}, style={a.get('visual_style','?')}, "
        f"cta='{a.get('cta','?')}', face={a.get('has_face',False)}, density={a.get('text_density','?')}"
    )
ads_summary_text = "\n".join(ads_summary_parts)

if "insights" not in st.session_state:
    with st.spinner("🧠 Generating cross-creative insights..."):
        raw = call_groq_text(API_KEY, INSIGHT_PROMPT.format(num_ads=len(results), ads_summary=ads_summary_text), model=MODEL)
        parsed = parse_json_safe(raw) if raw else None
        st.session_state["insights"] = parsed if isinstance(parsed, dict) else None
        if not st.session_state["insights"]:
            st.warning("⚠️ Could not parse insights.")

insights = st.session_state.get("insights")
if insights:
    if insights.get("key_insight"):
        st.markdown(f'<div class="insight-box">📌 <strong>Key Insight:</strong> {insights["key_insight"]}</div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### 🏆 Winning Patterns")
        for p in insights.get("winning_patterns", []): st.markdown(f"- {p}")
        st.markdown("#### 🪝 Common Hooks")
        for h in insights.get("common_hooks", []): st.markdown(f"- {h}")
        st.markdown("#### 😊 Emotional Patterns")
        for e in insights.get("emotional_patterns", []): st.markdown(f"- {e}")
    with c2:
        st.markdown("#### 🎨 Visual Trends")
        for t in insights.get("visual_trends", []): st.markdown(f"- {t}")
        st.markdown("#### 📣 CTA Observations")
        for o in insights.get("cta_observations", []): st.markdown(f"- {o}")

st.markdown('<hr class="divider">', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# SECTION 4: Creative Recommendations
# ══════════════════════════════════════════════════════════════

st.markdown('<div class="section-header">🚀 Creative Recommendations</div>', unsafe_allow_html=True)
st.markdown("New ad concepts generated from the patterns in your creatives.")

if "recommendations" not in st.session_state and insights:
    with st.spinner("✨ Generating new creative ideas..."):
        raw = call_groq_text(API_KEY, RECOMMENDATION_PROMPT.format(
            insights_summary=json.dumps(insights, indent=2), ads_summary=ads_summary_text), model=MODEL)
        parsed = parse_json_safe(raw) if raw else None
        st.session_state["recommendations"] = parsed if isinstance(parsed, list) else None

recs = st.session_state.get("recommendations")
if recs:
    for i, rec in enumerate(recs):
        st.markdown('<div class="rec-card">', unsafe_allow_html=True)
        st.markdown(f"### 💡 Idea {i+1}")
        c1, c2 = st.columns([2, 1])
        with c1:
            st.markdown(f'<span class="tag-pill tag-blue">🪝 Hook</span> {rec.get("hook","—")}', unsafe_allow_html=True)
            st.markdown(f'<span class="tag-pill tag-blue">🎬 Format</span> {rec.get("format_style","—")}', unsafe_allow_html=True)
            st.markdown(f'<span class="tag-pill tag-blue">😊 Emotion</span> {rec.get("emotional_angle","—")}', unsafe_allow_html=True)
            st.markdown(f'<span class="tag-pill tag-blue">📣 CTA</span> {rec.get("cta","—")}', unsafe_allow_html=True)
        with c2:
            st.markdown(f"**📝 Rationale**")
            st.markdown(f"_{rec.get('rationale','—')}_")
        st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<hr class="divider">', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# Export
# ══════════════════════════════════════════════════════════════

st.markdown('<div class="section-header">📥 Export</div>', unsafe_allow_html=True)

export = []
for r in sorted_results:
    a, s = r["analysis"], r["score"]
    export.append({
        "filename": r["filename"], "score": s["total_score"],
        "headline": a.get("headline",""), "hook_type": a.get("hook_type",""),
        "cta": a.get("cta",""), "emotional_trigger": a.get("emotional_trigger",""),
        "visual_style": a.get("visual_style",""), "target_audience": a.get("target_audience",""),
        "has_face": a.get("has_face",False), "text_density": a.get("text_density",""),
        "strengths": "; ".join(a.get("predicted_strengths",[])),
        "weaknesses": "; ".join(a.get("weaknesses",[])),
    })

st.download_button(
    "⬇️ Download CSV Report",
    pd.DataFrame(export).to_csv(index=False),
    "creativelens_analysis.csv", "text/csv",
    use_container_width=True,
)

st.markdown('<p style="text-align:center;opacity:0.3;margin-top:3rem;font-size:0.8rem">Built with CreativeLens · Powered by Groq</p>', unsafe_allow_html=True)
