# utils.py — OCR, JSON parsing, image encoding, Groq API client

import base64
import json
import re
import io
from PIL import Image


def extract_text_ocr(image: Image.Image) -> str:
    """Extract text from image using pytesseract. Returns empty string on failure."""
    try:
        import pytesseract
        text = pytesseract.image_to_string(image)
        return text.strip() if text else ""
    except Exception as e:
        print(f"[OCR] Failed: {e}")
        return ""


def parse_json_safe(text: str) -> dict | list | None:
    """Extract JSON from LLM output with 3-layer fallback."""
    if not text or not text.strip():
        return None

    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Strip markdown code blocks
    code_block_pattern = r"```(?:json)?\s*\n?(.*?)\n?\s*```"
    matches = re.findall(code_block_pattern, text, re.DOTALL)
    for match in matches:
        try:
            return json.loads(match.strip())
        except json.JSONDecodeError:
            continue

    # Find first JSON object or array by bracket matching
    for start_char, end_char in [("{", "}"), ("[", "]")]:
        start_idx = text.find(start_char)
        if start_idx == -1:
            continue
        depth = 0
        for i in range(start_idx, len(text)):
            if text[i] == start_char:
                depth += 1
            elif text[i] == end_char:
                depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start_idx:i + 1])
                except json.JSONDecodeError:
                    break

    return None


def encode_image_base64(image: Image.Image, max_size: int = 1024) -> str:
    """Resize and encode image to base64 for LLM API."""
    if max(image.size) > max_size:
        image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

    if image.mode in ("RGBA", "P"):
        image = image.convert("RGB")

    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=85)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def call_groq_vision(
    api_key: str,
    prompt: str,
    image_base64: str,
    model: str = "meta-llama/llama-4-scout-17b-16e-instruct",
    max_tokens: int = 1500,
    temperature: float = 0.2,
) -> str | None:
    """Call Groq vision model with image + text prompt. Returns raw text or None."""
    try:
        from groq import Groq
        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model=model,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}},
                ],
            }],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"[Groq API] Error: {e}")
        return None


def call_groq_text(
    api_key: str,
    prompt: str,
    model: str = "meta-llama/llama-4-scout-17b-16e-instruct",
    max_tokens: int = 2000,
    temperature: float = 0.3,
) -> str | None:
    """Call Groq for text-only completions. Returns raw text or None."""
    try:
        from groq import Groq
        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"[Groq API] Error: {e}")
        return None


def get_default_analysis() -> dict:
    """Fallback analysis when LLM call or parsing fails."""
    return {
        "headline": "Could not extract",
        "body_copy": "",
        "cta": "Unknown",
        "hook_type": "unknown",
        "emotional_trigger": "unknown",
        "visual_style": "unknown",
        "target_audience": "Unknown",
        "has_face": False,
        "product_focus": False,
        "text_density": "unknown",
        "predicted_strengths": ["Unable to analyze"],
        "weaknesses": ["Analysis failed — retry recommended"],
    }
