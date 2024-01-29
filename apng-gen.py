import os
import argparse
import subprocess
import csv
from PIL import Image
from tqdm import tqdm
import uuid
import shutil
from datetime import datetime

# Set up argument parsing
parser = argparse.ArgumentParser(description='Process and compress images.')
parser.add_argument('input_folder', help='Input folder containing image sequences')
parser.add_argument('size', choices=['small', 'regular', 'large'], help='Output size: small, regular, or large')
args = parser.parse_args()

# Define output sizes and file size limit
output_sizes = {
    'small': (300, 300),
    'regular': (408, 408),
    'large': (618, 618)
}
file_size_limit_kb = 500

# Function to get folder size
def get_folder_size(folder_path):
    total_size = 0
    for dirpath, _, filenames in os.walk(folder_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    return total_size

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
size_label = args.size
output_size = output_sizes[args.size]
output_folder = f"{timestamp}_{size_label}"
temp_folder = os.path.join(output_folder, 'temp')
static_folder = os.path.join(output_folder, 'static')
animated_folder = os.path.join(output_folder, 'animated')

# Create necessary directories
for folder in [temp_folder, static_folder, animated_folder]:
    if not os.path.exists(folder):
        os.makedirs(folder)

# Process images
total_files = sum(len(files) for _, _, files in os.walk(args.input_folder))
pbar = tqdm(total=total_files, desc='Processing Images', unit='file')

for subdir, _, files in os.walk(args.input_folder):
    for filename in files:
        pbar.set_postfix(file=filename, refresh=False)
        if not filename.endswith('.png'):
            continue

        input_file_path = os.path.join(subdir, filename)
        relative_path = os.path.relpath(subdir, args.input_folder)
        temp_dir = os.path.join(temp_folder, relative_path)

        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)

        with Image.open(input_file_path) as img:
            width, height = img.size

            if width < output_size[0] and height < output_size[1]:
                new_width, new_height = width, height  # Keep original size
            else:
                # Resize logic (maintains aspect ratio)
                if width > height:
                    new_width = min(output_size[0], width)
                    new_height = int((new_width / width) * height)
                else:
                    new_height = min(output_size[1], height)
                    new_width = int((new_height / height) * width)
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

            # Create new image with transparent background
            new_img = Image.new('RGBA', output_size, (0, 0, 0, 0))

            # Calculate position to paste the original/resized image
            paste_x = (output_size[0] - new_width) // 2
            paste_y = (output_size[1] - new_height) // 2

            # Paste the original/resized image onto the new image
            new_img.paste(img, (paste_x, paste_y), img if img.mode == 'RGBA' else None)

        # Save the processed image
        temp_file_path = os.path.join(temp_dir, filename)
        new_img.save(temp_file_path)
        pbar.update(1)

pbar.close()
print('Processing complete.')

# Compress images
def compress_pngs(root_folder, quality_range=(15, 30)):
    file_count = 0
    for folder, _, files in os.walk(root_folder):
        for f in files:
            if f.endswith('.png'):
                file_count += 1

    print(f"Found {file_count} PNG files in the folder tree. Starting compression...")

    processed_files = 0
    with tqdm(total=file_count, desc="Compressing", unit="file") as pbar:
        for folder, _, files in os.walk(root_folder):
            png_files = [os.path.join(folder, f) for f in files if f.endswith('.png')]
            
            if not png_files:
                continue

            quality = f"{quality_range[0]}-{quality_range[1]}"
            for file in png_files:
                try:
                    subprocess.run(['pngquant', '--force', '--quality', quality, '--output', file, '--speed', "1", '--', file], check=True)
                    processed_files += 1
                    pbar.update(1)
                except subprocess.CalledProcessError as e:
                    print(f"\nError processing file {file}: {e}. Skipping this file.")

    print(f"Compression complete. {processed_files}/{file_count} files processed.")

compress_pngs(temp_folder)

# Function to calculate additional optimization required
def calculate_additional_optimization(apng_size):
    if apng_size > file_size_limit_kb * 1024:
        return apng_size - (file_size_limit_kb * 1024)
    return 0

# Prepare data for CSV
csv_data = []

# Copy the first image from each folder to static folder and create animations
for subdir, _, files in os.walk(temp_folder):
    sorted_files = sorted([f for f in files if f.endswith('.png')])
    if sorted_files:
        # Copy first image to static folder
        first_image = sorted_files[0]
        source_path = os.path.join(subdir, first_image)
        dest_path = os.path.join(static_folder, os.path.basename(subdir) + '.png')
        shutil.copy(source_path, dest_path)

        # Rename files to ensure consistent naming convention for ffmpeg
        for i, file in enumerate(sorted_files):
            os.rename(os.path.join(subdir, file), os.path.join(subdir, f"{os.path.basename(subdir)}_{i:05d}.png"))

        unique_id = str(uuid.uuid4())

        # Run ffmpeg command
        ffmpeg_command = f"ffmpeg -r 8 -i {os.path.join(subdir, os.path.basename(subdir) + '_%05d.png')} -plays 0 -vf format=rgba -f apng {os.path.join(animated_folder, os.path.basename(subdir) + '_' + unique_id + '.png')}"
        subprocess.run(ffmpeg_command, shell=True)

        # Calculate file sizes and additional optimization
        original_size = get_folder_size(subdir)
        compressed_size = get_folder_size(temp_folder)
        apng_file = os.path.join(animated_folder, os.path.basename(subdir) + '_' + unique_id + '.png')
        apng_size = os.path.getsize(apng_file)
        meets_limit = apng_size <= file_size_limit_kb * 1024
        additional_opt = calculate_additional_optimization(apng_size)

        # Append data to CSV data list
        csv_data.append([os.path.basename(subdir), original_size, compressed_size, apng_size, meets_limit, additional_opt])

print('Final processing complete.')

# Write CSV file
csv_file_name = os.path.join(output_folder, 'report.csv')
with open(csv_file_name, 'w', newline='') as csvfile:
    csvwriter = csv.writer(csvfile)
    csvwriter.writerow(['name', 'original_combined_size', 'compressed_combined_size', 'apng_size', 'meets_500kb_limit', 'additional_opt_req'])
    csvwriter.writerows(csv_data)

print(f'Report generated: {csv_file_name}')

