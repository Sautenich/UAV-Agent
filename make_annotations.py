import matplotlib.pyplot as plt
from matplotlib.widgets import Button
from PIL import Image
import pandas as pd
import os
import ast
import csv
from collections import defaultdict

# === Globals for interaction state ===
click_points = []
current_annotation = {}
ax_img = None
fig = None
circles = []
grouped_annotations = defaultdict(list)
skipped_annotations = []

# === Functions ===

def load_csv(csv_file):
    data = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)  # Skip header
        for row in reader:
            if len(row) >= 2:
                image_name = str(int(row[0].split('.')[0])) + '.jpg'
                description = row[1].strip('"').strip("'")
                data.append({
                    "image_name": image_name,
                    "description": description
                })
    return data

def draw_circle(x, y):
    circle = plt.Circle((x, y), radius=2, color='red')
    ax_img.add_patch(circle)
    circles.append(circle)
    fig.canvas.draw()

def on_click(event):
    if event.inaxes == ax_img:
        x, y = int(event.xdata), int(event.ydata)
        if x is not None and y is not None:
            print(f"Clicked at ({x}, {y})")
            click_points.append((x, y))
            draw_circle(x, y)

def undo_click(event):
    if click_points:
        click_points.pop()
    if circles:
        circle = circles.pop()
        circle.remove()
        fig.canvas.draw()

def next_object(event):
    plt.close()

def skip_object(event):
    global skipped_annotations
    skipped_annotations.append(current_annotation)
    plt.close()

def annotate_images(image_folder, csv_file, start=1, end=None):
    global ax_img, fig, current_annotation, click_points, circles, grouped_annotations, skipped_annotations

    data = load_csv(csv_file)
    data = data[start-1:end]  # Apply range

    for entry in data:
        image_name = entry["image_name"]
        try:
            # Clean up the description string before parsing
            desc = entry["description"].strip('[]').replace("'", '"')
            object_list = ast.literal_eval(f"[{desc}]")
        except Exception as e:
            print(f"Skipping {image_name} due to invalid object list: {e}")
            continue
        if not object_list:
            continue

        for obj in object_list:
            click_points = []
            circles = []
            current_annotation = {
                "image_name": image_name,
                "object_request": object_list,
                "object": obj
            }

            # Load image
            image_path = os.path.join(image_folder, image_name)
            if not os.path.exists(image_path):
                print(f"Image not found: {image_path}")
                continue
            img = Image.open(image_path)

            # Setup plot
            fig, ax_img = plt.subplots(figsize=(10, 10))
            ax_img.imshow(img)
            ax_img.set_title(f"Mark object: " + r"$\bf{" + obj + r"}$" + f" in {image_name}")
            ax_img.axis("off")

            # Buttons
            ax_next = plt.axes([0.81, 0.01, 0.1, 0.05])
            btn_next = Button(ax_next, 'Next')
            btn_next.on_clicked(next_object)

            ax_undo = plt.axes([0.7, 0.01, 0.1, 0.05])
            btn_undo = Button(ax_undo, 'Undo')
            btn_undo.on_clicked(undo_click)

            ax_skip = plt.axes([0.59, 0.01, 0.1, 0.05])
            btn_skip = Button(ax_skip, 'Skip')
            btn_skip.on_clicked(skip_object)

            fig.canvas.mpl_connect('button_press_event', on_click)
            plt.show()

            if click_points:
                key = (image_name, str(object_list), obj)
                grouped_annotations[key].extend(click_points)

    # === Save annotations ===
    if grouped_annotations:
        output_file = f"pixel_annotations_{str(start)}_{str(end)}.csv"
        with open(output_file, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["image_name", "object_request", "object", "coordinates"])

            for (image_name, object_request, obj), coords in grouped_annotations.items():
                writer.writerow([image_name, object_request, obj, coords])

        print(f"✅ Saved grouped annotations to '{output_file}'")
    else:
        print("❌ No annotations were made.")

    # === Save skipped objects ===
    if skipped_annotations:
        skipped_file = f"skipped_annotations_{str(start)}_{str(end)}.csv"
        with open(skipped_file, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["image_name", "object_request", "object"])

            for item in skipped_annotations:
                writer.writerow([item["image_name"], item["object_request"], item["object"]])

        print(f"⚠️ Saved skipped annotations to '{skipped_file}'")

# === Example run ===
if __name__ == "__main__":
    image_folder = 'images/dataset_images'  # <-- Set your images folder path
    csv_file = 'image_analysis_results.csv'  # <-- Set your CSV file path
    annotate_images(image_folder, csv_file, start=1, end=3)
