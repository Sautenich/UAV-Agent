import csv
import json
import random
from collections import defaultdict

# === CONFIGURATION ===
CSV_FILE = 'pixel_annotations_merged_sorted.csv'
OUTPUT_FILE = 'qwen2.5_multimodal_randomized.jsonl'

NUM_SAMPLES_TOTAL = 10000   # Total instruction samples to generate
MIN_OBJECTS = 3             # Minimum number of object types per instruction
MAX_OBJECTS = 10             # Maximum number of object types per instruction

random.seed(42)  # Optional: reproducibility

# === LOAD CSV & GROUP BY IMAGE ===
image_data = defaultdict(lambda: {"objects": defaultdict(list)})

with open(CSV_FILE, newline='', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        image_name = row["image_name"]
        obj_label = row["object"].strip()
        coords = eval(row["coordinates"])
        image_data[image_name]["objects"][obj_label].append(coords)

# === BUILD ALL POSSIBLE IMAGES WITH RANDOMIZED INSTRUCTIONS ===
image_names = list(image_data.keys())
jsonl_data = []

for _ in range(NUM_SAMPLES_TOTAL):
    # Randomly pick an image
    image_name = random.choice(image_names)
    objects = image_data[image_name]["objects"]

    available_labels = list(objects.keys())
    if not available_labels:
        continue

    # Randomly pick number of object types to include in instruction
    num_labels = random.randint(MIN_OBJECTS, min(MAX_OBJECTS, len(available_labels)))
    sampled_labels = random.sample(available_labels, num_labels)

    instruction = f"This is the satellite image. Pixelpoint the key points of all the {', '.join(sampled_labels)}. Provide the answer in json."

    output = []
    for label in sampled_labels:
        for coords in objects[label]:
            output.append({
                "label": label,
                "coordinates": coords
            })

    jsonl_data.append({
        "image": image_name,
        "instruction": instruction,
        "output": output
    })

# === SAVE TO JSONL ===
with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    for item in jsonl_data:
        json.dump(item, f)
        f.write('\n')

print(f"Generated and saved {len(jsonl_data)} instruction samples to {OUTPUT_FILE}")
