import matplotlib.pyplot as plt
from matplotlib.widgets import Button
from PIL import Image
import pandas as pd
import os
import ast
import csv
from collections import defaultdict

# Globals for interaction state
click_points = []
current_annotation = {}
ax_img = None
fig = None
circles = []
grouped_annotations = defaultdict(list)

def load_csv(csv_file):
    df = pd.read_csv(csv_file)
    return df.to_dict("records")

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

def annotate_images(image_folder, csv_file, start=1, end=None):
    global ax_img, fig, current_annotation, click_points, circles, grouped_annotations

    data = load_csv(csv_file)
    data = data[start-1:end]  # Apply range

    for entry in data:
        image_name = entry["image_name"]
        try:
            object_list = ast.literal_eval(entry["description"])
        except:
            print(f"Skipping {image_name} due to invalid object list.")
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

            fig.canvas.mpl_connect('button_press_event', on_click)
            plt.show()

            if click_points:
                key = (image_name, str(object_list), obj)
                grouped_annotations[key].extend(click_points)

    # Save grouped annotations
    if grouped_annotations:
        with open(f'''pixel_annotations_{str(start)}_{str(end)}.csv''', mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["image_name", "object_request", "object", "coordinates"])

            for (image_name, object_request, obj), coords in grouped_annotations.items():
                writer.writerow([image_name, object_request, obj, coords])

        print(f"✅ Saved grouped results to 'pixel_annotations_{str(start)}_{str(end)}.csv'")
    else:
        print("❌ No annotations were made.")

# === Example run ===
image_folder = 'images/blank'
csv_file = 'image_analysis_results.csv'
annotate_images(image_folder, csv_file, start=2, end=2)

