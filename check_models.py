#!/usr/bin/env python3
"""Check which Claude models are accessible with your API key"""

from anthropic import Anthropic
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv("api/.env")

# Get API key
api_key = os.getenv("ANTHROPIC_API_KEY")
if not api_key:
    print("❌ ANTHROPIC_API_KEY not found in environment")
    exit(1)

client = Anthropic(api_key=api_key)

# List of Claude models to test
models = [
    ("Claude 3 Haiku", "claude-3-haiku-20240307"),
    ("Claude 3 Sonnet", "claude-3-sonnet-20240229"),
    ("Claude 3 Opus", "claude-3-opus-20240229"),
    ("Claude 3.5 Sonnet (June)", "claude-3-5-sonnet-20240620"),
    ("Claude 3.5 Sonnet (Oct)", "claude-3-5-sonnet-20241022"),
    ("Claude Sonnet 4", "claude-sonnet-4-20250514"),
    ("Claude 4.5 Sonnet", "claude-4-5-sonnet-20241022"),
]

print("=" * 70)
print("Testing Claude Model Access")
print("=" * 70)
print()

accessible_models = []

for name, model_id in models:
    try:
        response = client.messages.create(
            model=model_id,
            max_tokens=10,
            messages=[{"role": "user", "content": "Hi"}]
        )
        print(f"✅ {name:30} | {model_id}")
        accessible_models.append((name, model_id))
    except Exception as e:
        error_msg = str(e)
        if "not_found_error" in error_msg or "404" in error_msg:
            print(f"❌ {name:30} | {model_id}")
            print(f"   └─ Not accessible (404 - model not found)")
        else:
            print(f"⚠️  {name:30} | {model_id}")
            print(f"   └─ Error: {error_msg[:60]}")
    print()

print("=" * 70)
print(f"Summary: {len(accessible_models)}/{len(models)} models accessible")
print("=" * 70)

if accessible_models:
    print("\n🎉 You have access to:")
    for name, model_id in accessible_models:
        print(f"   • {name} ({model_id})")
    
    print("\n💡 Recommended model for tool usage:")
    if any("3.5 Sonnet" in name for name, _ in accessible_models):
        best = next((name, mid) for name, mid in accessible_models if "3.5 Sonnet" in name)
        print(f"   → {best[0]} ({best[1]})")
    elif any("Opus" in name for name, _ in accessible_models):
        print(f"   → Claude 3 Opus (claude-3-opus-20240229)")
    elif any("3 Sonnet" in name for name, _ in accessible_models):
        print(f"   → Claude 3 Sonnet (claude-3-sonnet-20240229)")
    else:
        print(f"   → Claude 3 Haiku (claude-3-haiku-20240307)")
else:
    print("\n❌ No models accessible - check your API key and billing status")

