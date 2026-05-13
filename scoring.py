# scoring.py — Deterministic heuristic scoring (8 dimensions, 100 pts total)


def score_creative(analysis: dict) -> dict:
    """Score a single ad creative. Returns total_score, breakdown, and explanations."""
    breakdown = {}
    explanations = {}

    # 1. Strong Hook (20 pts)
    hook_type = (analysis.get("hook_type") or "").lower()
    strong_hooks = ["pain-point", "curiosity", "question", "shock", "comparison"]
    moderate_hooks = ["benefit-led", "storytelling", "testimonial"]

    if hook_type in strong_hooks:
        breakdown["strong_hook"] = 20
        explanations["strong_hook"] = f"Strong hook type: '{hook_type}' — high scroll-stop potential"
    elif hook_type in moderate_hooks:
        breakdown["strong_hook"] = 12
        explanations["strong_hook"] = f"Moderate hook type: '{hook_type}' — decent but not top-tier"
    elif hook_type:
        breakdown["strong_hook"] = 6
        explanations["strong_hook"] = f"Weak hook type: '{hook_type}' — lower scroll-stop potential"
    else:
        breakdown["strong_hook"] = 0
        explanations["strong_hook"] = "No hook detected"

    # 2. Human Face / Emotion (15 pts)
    has_face = analysis.get("has_face", False)
    emotional_trigger = (analysis.get("emotional_trigger") or "").lower()
    strong_emotions = ["fear", "fomo", "aspiration", "excitement", "trust", "empathy", "relief"]

    face_score = 0
    if has_face:
        face_score += 10
    if emotional_trigger in strong_emotions:
        face_score += 5
    elif emotional_trigger:
        face_score += 3

    breakdown["human_face_emotion"] = min(face_score, 15)
    if has_face and emotional_trigger:
        explanations["human_face_emotion"] = f"Human face present + '{emotional_trigger}' emotional trigger"
    elif has_face:
        explanations["human_face_emotion"] = "Human face present but weak emotional trigger"
    elif emotional_trigger:
        explanations["human_face_emotion"] = f"No face but '{emotional_trigger}' emotion detected"
    else:
        explanations["human_face_emotion"] = "No face or strong emotion detected"

    # 3. Clear CTA (10 pts)
    cta = (analysis.get("cta") or "").strip().lower()
    strong_ctas = ["shop now", "buy now", "get started", "sign up", "try free",
                   "claim offer", "order now", "start free trial", "download",
                   "learn more", "book now", "get yours"]

    if any(strong in cta for strong in strong_ctas):
        breakdown["clear_cta"] = 10
        explanations["clear_cta"] = f"Strong CTA detected: '{analysis.get('cta', '')}'"
    elif cta:
        breakdown["clear_cta"] = 5
        explanations["clear_cta"] = f"CTA present but not action-oriented: '{analysis.get('cta', '')}'"
    else:
        breakdown["clear_cta"] = 0
        explanations["clear_cta"] = "No CTA detected"

    # 4. Problem-Solution Framing (15 pts)
    strengths = " ".join(analysis.get("predicted_strengths") or []).lower()
    headline = (analysis.get("headline") or "").lower()
    body = (analysis.get("body_copy") or "").lower()
    combined_text = f"{headline} {body} {strengths}"

    problem_keywords = ["problem", "solution", "struggle", "pain", "fix", "solve",
                        "tired of", "frustrated", "stop", "never again", "finally",
                        "before", "after", "transform", "result"]
    problem_matches = sum(1 for kw in problem_keywords if kw in combined_text)

    if hook_type == "pain-point" or problem_matches >= 3:
        breakdown["problem_solution"] = 15
        explanations["problem_solution"] = "Strong problem-solution framing detected"
    elif problem_matches >= 1:
        breakdown["problem_solution"] = 8
        explanations["problem_solution"] = "Some problem-solution elements present"
    else:
        breakdown["problem_solution"] = 0
        explanations["problem_solution"] = "No clear problem-solution framing"

    # 5. Visual Clarity (10 pts)
    text_density = (analysis.get("text_density") or "").lower()
    visual_style = (analysis.get("visual_style") or "").lower()
    clean_styles = ["minimal", "product-shot", "lifestyle", "before-after"]

    visual_score = 0
    if text_density in ["low", "medium"]:
        visual_score += 5
    if visual_style in clean_styles:
        visual_score += 5
    elif visual_style:
        visual_score += 2

    breakdown["visual_clarity"] = min(visual_score, 10)
    explanations["visual_clarity"] = f"Text density: {text_density or 'unknown'}, style: {visual_style or 'unknown'}"

    # 6. UGC Authenticity (10 pts)
    ugc_keywords = ["ugc", "testimonial", "authentic", "real", "user", "review"]
    ugc_signals = sum(1 for kw in ugc_keywords if kw in visual_style or kw in combined_text)

    if visual_style == "ugc" or ugc_signals >= 2:
        breakdown["ugc_authenticity"] = 10
        explanations["ugc_authenticity"] = "Strong UGC/authentic feel detected"
    elif ugc_signals >= 1 or visual_style == "meme-style":
        breakdown["ugc_authenticity"] = 5
        explanations["ugc_authenticity"] = "Some authentic/UGC elements present"
    else:
        breakdown["ugc_authenticity"] = 0
        explanations["ugc_authenticity"] = "No UGC signals detected"

    # 7. Social Proof (10 pts)
    social_keywords = ["review", "rating", "star", "customer", "testimonial",
                       "trust", "proven", "sold", "best-seller", "award",
                       "#1", "million", "thousand", "people"]
    social_matches = sum(1 for kw in social_keywords if kw in combined_text)

    if hook_type == "social-proof" or social_matches >= 2:
        breakdown["social_proof"] = 10
        explanations["social_proof"] = "Strong social proof elements detected"
    elif social_matches >= 1 or hook_type == "testimonial":
        breakdown["social_proof"] = 5
        explanations["social_proof"] = "Some social proof elements present"
    else:
        breakdown["social_proof"] = 0
        explanations["social_proof"] = "No social proof detected"

    # 8. Offer / Urgency (10 pts)
    urgency_keywords = ["limited", "exclusive", "today", "now", "hurry",
                        "last chance", "sale", "off", "discount", "free",
                        "bonus", "offer", "deal", "save", "expires"]
    urgency_matches = sum(1 for kw in urgency_keywords if kw in combined_text)

    if hook_type == "urgency" or urgency_matches >= 2:
        breakdown["offer_urgency"] = 10
        explanations["offer_urgency"] = "Strong urgency/offer elements detected"
    elif urgency_matches >= 1:
        breakdown["offer_urgency"] = 5
        explanations["offer_urgency"] = "Some urgency/offer elements present"
    else:
        breakdown["offer_urgency"] = 0
        explanations["offer_urgency"] = "No urgency or offer detected"

    total = sum(breakdown.values())
    return {"total_score": total, "breakdown": breakdown, "explanations": explanations}


def get_score_tier(score: int) -> tuple[str, str]:
    """Return (tier_label, hex_color) for a score."""
    if score >= 80:
        return "Top Performer", "#22c55e"
    elif score >= 60:
        return "Strong", "#3b82f6"
    elif score >= 40:
        return "Average", "#f59e0b"
    else:
        return "Weak", "#ef4444"
