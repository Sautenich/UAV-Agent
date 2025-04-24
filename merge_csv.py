import pandas as pd
import glob
import re

# Match all relevant files
csv_files = glob.glob("pixel_annotation*.csv") + glob.glob("pixel_annotations*.csv")

if not csv_files:
    print("❌ No matching files found.")
else:
    print(f"🔍 Found {len(csv_files)} files to merge.")

    # Load and merge all found CSVs
    merged_df = pd.concat((pd.read_csv(f) for f in csv_files), ignore_index=True)

    # Function to sort filenames in natural (human) order: 1.jpg, 2.jpg, ..., 10.jpg
    def natural_sort_key(s):
        return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]

    # Sort by image_name using natural order
    merged_df = merged_df.sort_values(by="image_name", key=lambda x: x.apply(natural_sort_key))

    # Save merged result
    merged_df.to_csv("pixel_annotations_merged_sorted.csv", index=False)
    print("✅ Merged and sorted into 'pixel_annotations_merged_sorted.csv'")
