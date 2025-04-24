import base64
from PIL import Image
import io
import os
import json
import csv
import requests
import re

# Function to sort filenames in natural (human) order: 1.jpg, 2.jpg, ..., 10.jpg
def natural_sort_key(s):
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]

# Function to describe a list of images using Fireworks API
def describe_satellite_images(images: list) -> str:
    api_key = 'fw_3ZijuLwrUV55JHLkm6e3wnb9'
    if not api_key:
        return "Error: No API key provided in request"

    max_tokens = 4000
    temperature = 0.8

    content = [{
        "type": "text",
        "text": '''
List all recognizable objects in this image. Provide the answer in the list. 
EXAMPLE: ['object1', 'object2', 'object3']'''
    }]

    for img in images:
        if img.mode in ('RGBA', 'LA', 'P'):
            img = img.convert('RGB')
        buffered = io.BytesIO()
        img.save(buffered, format="JPEG", quality=95)
        img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{img_base64}"}
        })

    payload = {
        "model": "accounts/fireworks/models/qwen2-vl-72b-instruct",
        "max_tokens": max_tokens,
        "temperature": temperature,
        "top_p": 1,
        "top_k": 40,
        "messages": [
            {
                "role": "user",
                "content": content
            }
        ]
    }

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    response = requests.post(
        "https://api.fireworks.ai/inference/v1/chat/completions",
        headers=headers,
        json=payload
    )

    if response.status_code == 200:
        return response.json()['choices'][0]['message']['content']
    else:
        return f"Error {response.status_code}: {response.text}"

# Load and sort images from local folder
image_folder = "images/blank"
images = []

image_filenames = sorted(
    [f for f in os.listdir(image_folder) if f.lower().endswith((".jpg", ".jpeg", ".png"))],
    key=natural_sort_key
)

for filename in image_filenames:
    filepath = os.path.join(image_folder, filename)
    try:
        img = Image.open(filepath).convert("RGB")
        images.append((img, filename))
    except Exception as e:
        print(f"Failed to open image {filename}: {e}")

# Analyze each image and store results
image_analysis_results = []
for img, name in images:
    print(f"🔍 Analyzing {name}...")
    description = describe_satellite_images([img])
    image_analysis_results.append({"image_name": name, "description": description})

# Save to CSV
csv_file_path = "image_analysis_results.csv"
with open(csv_file_path, mode='w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=["image_name", "description"])
    writer.writeheader()
    writer.writerows(image_analysis_results)

print(f"\n✅ Done! Results saved to: {csv_file_path}")
