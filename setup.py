import os
import json
from groq import Groq
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import List

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# --- Pydantic Model ---
class NameVariants(BaseModel):
    original_name: str
    english_variants: List[str]
    hindi_variants: List[str]
    all_variants: List[str]


def generate_variants(name: str) -> NameVariants:
    print(f"\n🤖 '{name}' ke liye variants generate ho rahe hain...\n")

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {
                "role": "system",
                "content": """You are a speech recognition expert for Indian names.
Generate all possible mishearings of an Indian name as it might appear in Whisper speech-to-text output.

You must return a valid JSON object with exactly these fields:
{
  "original_name": "the original name",
  "english_variants": ["list", "of", "english", "phonetic", "variants"],
  "hindi_variants": ["हिंदी", "वेरिएंट्स"],
  "all_variants": ["combined", "list", "of", "all", "variants", "lowercase"]
}

Rules:
- english_variants: how the name might be misheard in English
- hindi_variants: how Whisper writes it in Devanagari script  
- all_variants: all combined, all lowercase except Hindi
- No explanation, ONLY the JSON object"""
            },
            {
                "role": "user",
                "content": f"Generate variants for Indian name: {name}"
            }
        ],
        response_format={"type": "json_object"},  # Groq JSON mode
        temperature=0.3
    )

    raw = response.choices[0].message.content.strip()
    print(f"LLM response:\n{raw}\n")

    # Parse into dict first
    data = json.loads(raw)

    # Pydantic se validate karo
    result = NameVariants(
        original_name=data.get("original_name", name),
        english_variants=data.get("english_variants", []),
        hindi_variants=data.get("hindi_variants", []),
        all_variants=data.get("all_variants", [])
    )

    # Original naam bhi add karo
    if name.lower() not in result.all_variants:
        result.all_variants.append(name.lower())

    # Duplicates remove karo
    result.all_variants = list(set(result.all_variants))

    return result


def save_config(result: NameVariants):
    config = {
        "name": result.original_name,
        "english_variants": result.english_variants,
        "hindi_variants": result.hindi_variants,
        "variants": result.all_variants    # main.py ye use karega
    }
    with open("user_config.json", "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    print(f"✅ Saved to user_config.json")


if __name__ == "__main__":
    print("=" * 45)
    print("   Meeting Copilot — First Time Setup")
    print("=" * 45)

    name = input("\nApna naam likho: ").strip()

    if not name:
        print("Naam blank nahi ho sakta!")
        exit()

    # Generate karo
    result = generate_variants(name)

    # Print karo
    print(f"✅ {len(result.all_variants)} total variants mile:\n")
    print(f"📝 English variants:")
    for v in result.english_variants:
        print(f"   → {v}")
    print(f"\n📝 Hindi variants:")
    for v in result.hindi_variants:
        print(f"   → {v}")
    print(f"\n📝 All variants:")
    for v in result.all_variants:
        print(f"   → {v}")

    # Save karo
    save_config(result)

    print(f"\n🎯 Setup complete! Ab main.py run karo.")
    print("=" * 45)