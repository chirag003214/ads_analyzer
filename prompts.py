# prompts.py — LLM prompt templates for ad creative analysis

# Per-ad analysis prompt (sent with each image + OCR text)
ANALYSIS_PROMPT = """You are a senior Meta ads creative strategist with 10+ years of experience analyzing paid social creatives.

Analyze the following ad creative. You are given the image and any text extracted via OCR.

OCR Text from the ad:
\"\"\"
{ocr_text}
\"\"\"

Return your analysis as STRICT JSON with exactly these fields:

{{
  "headline": "The main headline or hook text visible in the ad",
  "body_copy": "Any body/supporting text in the ad",
  "cta": "The call-to-action text (e.g., 'Shop Now', 'Learn More')",
  "hook_type": "One of: pain-point, curiosity, social-proof, urgency, benefit-led, question, storytelling, shock, testimonial, comparison",
  "emotional_trigger": "The primary emotion targeted (e.g., fear, aspiration, FOMO, trust, excitement)",
  "visual_style": "One of: lifestyle, product-shot, UGC, flat-lay, before-after, text-heavy, minimal, collage, meme-style, professional",
  "target_audience": "Best guess of the intended audience demographic/psychographic",
  "has_face": true or false,
  "product_focus": true or false,
  "text_density": "One of: low, medium, high",
  "predicted_strengths": ["strength1", "strength2", "strength3"],
  "weaknesses": ["weakness1", "weakness2"]
}}

Rules:
- Return ONLY the JSON object. No markdown, no explanation, no preamble.
- Every field must be present.
- predicted_strengths should have 2-4 items.
- weaknesses should have 1-3 items.
- Be specific and actionable, not generic.
"""

# Cross-ad insight prompt (sent once after all ads are analyzed)
INSIGHT_PROMPT = """You are a senior creative strategist reviewing a batch of {num_ads} ad creatives from the same brand.

Here is a summary of each ad's analysis:

{ads_summary}

Based on these creatives, provide a structured analysis. Return STRICT JSON:

{{
  "winning_patterns": ["pattern1", "pattern2", "pattern3"],
  "common_hooks": ["hook1", "hook2"],
  "visual_trends": ["trend1", "trend2"],
  "emotional_patterns": ["pattern1", "pattern2"],
  "cta_observations": ["observation1", "observation2"],
  "key_insight": "One paragraph summarizing the brand's creative strategy. Be specific, reference actual patterns. Avoid generic marketing fluff."
}}

Rules:
- Be concrete and analytical. Reference specific patterns from the data.
- Each list should have 2-4 items.
- Return ONLY valid JSON. No markdown, no explanation.
"""

# Creative recommendations prompt (generates new ad ideas from patterns)
RECOMMENDATION_PROMPT = """You are a senior creative director at a top performance marketing agency.

Based on the following creative analysis of a brand's existing ads, generate 3-5 NEW ad concepts for future testing.

Brand creative patterns:
{insights_summary}

Individual ad scores and analysis:
{ads_summary}

Return STRICT JSON array of ad concepts:

[
  {{
    "hook": "The opening line or visual hook",
    "format_style": "Recommended ad format (e.g., UGC testimonial video, static before/after, carousel)",
    "emotional_angle": "The primary emotion to target",
    "cta": "Recommended call-to-action",
    "rationale": "Why this concept should perform well, based on patterns observed"
  }}
]

Rules:
- Generate 3-5 concepts.
- Each concept should be actionable.
- Rationale must reference specific patterns from the analysis.
- Return ONLY the JSON array. No markdown, no explanation.
"""
