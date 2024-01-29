
# APNG-Gen: iMessage Sticker Pack Generator

## Description
APNG-Gen is a Python script designed for creating animated PNG (APNG) files tailored for iMessage sticker packs. It simplifies the process of transforming image sequences into compliant APNGs for iMessage, offering various resizing options and image optimization. This tool is essential for designers and developers who want to enrich their iMessage sticker collections with ease and efficiency.

## Requirements
- Python 3.x
- PIL (Python Imaging Library) for image processing
- tqdm for progress bar visualization
- uuid for generating unique identifiers
- shutil for file handling
- `pngquant` for image compression
- ffmpeg for APNG creation

## Installation
Make sure Python 3.x is installed on your system. Install the necessary Python packages:
```bash
pip install Pillow tqdm uuid shutil
```
Also, ensure pngquant and ffmpeg are installed and properly set up in your system's PATH.

## Usage
Run the script from the command line by specifying the input folder and the desired output size. Available size options are small, regular, or large.

```bash
python apng-gen.py <input_folder> <size>
```
Replace <input_folder> with the path to your image sequences, and <size> with either small, regular, or large.

## Example
```bash
python apng-gen.py MyPngSequences regular
```

## Features
Adaptive Image Resizing: Customizes image sizes to meet iMessage sticker pack standards.
Optimized Image Compression: Utilizes pngquant for effective size reduction while maintaining quality.
Streamlined APNG Creation: Efficiently converts image sequences into animated PNGs with ffmpeg.
