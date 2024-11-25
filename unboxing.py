import os
import argparse
from PIL import Image
import bordercrop
import io


def is_pixel_black(pixel: tuple, black_threshold: int) -> bool:
    if isinstance(pixel, int):  # Grayscale pixel (single channel)
        return pixel < black_threshold
    else:  # Color pixel (tuple of RGB)
        r, g, b = pixel
        return r <= black_threshold and g <= black_threshold and b <= black_threshold



def detect_top_border(image: Image.Image, black_threshold: int = 0) -> int:
    width, height = image.size
    for y in range(height):
        row_pixels = image.crop((0, y, width, y + 1)).getdata()
        if all(is_pixel_black(pixel, black_threshold) for pixel in row_pixels):
            continue
        return y
    return height


def detect_bottom_border(image: Image.Image, black_threshold: int = 0) -> int:
    width, height = image.size
    for y in range(height - 1, -1, -1):
        row_pixels = image.crop((0, y, width, y + 1)).getdata()
        if all(is_pixel_black(pixel, black_threshold) for pixel in row_pixels):
            continue
        return height - y - 1
    return height


def detect_left_border(image: Image.Image, black_threshold: int = 0) -> int:
    width, height = image.size
    for x in range(width):
        col_pixels = image.crop((x, 0, x + 1, height)).getdata()
        if all(is_pixel_black(pixel, black_threshold) for pixel in col_pixels):
            continue
        return x
    return width


def detect_right_border(image: Image.Image, black_threshold: int = 0) -> int:
    width, height = image.size
    for x in range(width - 1, -1, -1):
        col_pixels = image.crop((x, 0, x + 1, height)).getdata()
        if all(is_pixel_black(pixel, black_threshold) for pixel in col_pixels):
            continue
        return width - x - 1
    return width


def unletterbox(file_path: str, black_threshold: int = 0) -> bytes:
    with Image.open(file_path) as image:
        grayscale_image = image.convert("L")  # Convert to grayscale
        top = detect_top_border(grayscale_image, black_threshold)
        bottom = detect_bottom_border(grayscale_image, black_threshold)
        left = detect_left_border(grayscale_image, black_threshold)
        right = detect_right_border(grayscale_image, black_threshold)

        width, height = image.size
        cropped_img = image.crop((left, top, width - right, height - bottom))

        with io.BytesIO() as buffer:
            cropped_img.save(buffer, format=image.format)
            return buffer.getvalue()


# Workflow for comparing results
def setup_output_directories(base_dir="unletterbox_test"):
    dirs = {
        "output_yours": os.path.join(base_dir, "unletterboxed_your_function"),
        "output_bordercrop": os.path.join(base_dir, "unletterboxed_bordercrop"),
    }
    for path in dirs.values():
        os.makedirs(path, exist_ok=True)
    return dirs


def process_with_your_function(input_file, output_dir, black_threshold=10):
    try:
        output_path = os.path.join(output_dir, os.path.basename(input_file))
        with open(output_path, "wb") as f:
            f.write(unletterbox(input_file, black_threshold))
        print(f"Processed with your function: {output_path}")
    except Exception as e:
        print(f"Error processing with your function: {e}")


def process_with_bordercrop(input_file, output_dir, threshold=10):
    try:
        output_path = os.path.join(output_dir, os.path.basename(input_file))
        cropped_image = bordercrop.crop(
            input_file,
            THRESHOLD=threshold,           # Set the black threshold
            MINIMUM_THRESHOLD_HITTING=0,  # Default, can be adjusted
            MINIMUM_ROWS=0                 # Default, can be adjusted
        )
        cropped_image.save(output_path)
        print(f"Processed with bordercrop: {output_path}")
    except Exception as e:
        print(f"Error processing with bordercrop: {e}")


def compare_images(dir1, dir2):
    print("\nComparison Results:")
    for file_name in os.listdir(dir1):
        path1 = os.path.join(dir1, file_name)
        path2 = os.path.join(dir2, file_name)

        if os.path.exists(path2):
            img1 = Image.open(path1)
            img2 = Image.open(path2)

            # Check for size differences
            if img1.size != img2.size:
                print(f"Size mismatch for {file_name}: {img1.size} vs {img2.size}")

            # Check pixel differences
            diff = sum(1 for p1, p2 in zip(img1.getdata(), img2.getdata()) if p1 != p2)
            print(f"Pixel differences for {file_name}: {diff}")
        else:
            print(f"File {file_name} not found in {dir2}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Unletterbox images using your function and bordercrop.")
    parser.add_argument("image", type=str, help="Path to the image file.")
    parser.add_argument("black_threshold", type=int, help="Black threshold (0-255).")
    args = parser.parse_args()

    input_file = args.image
    black_threshold = args.black_threshold

    if not os.path.exists(input_file):
        print(f"Input file '{input_file}' does not exist.")
        exit(1)

    # Setup output directories
    dirs = setup_output_directories()

    # Process the image with both methods
    process_with_your_function(input_file, dirs["output_yours"], black_threshold)
    process_with_bordercrop(input_file, dirs["output_bordercrop"], threshold=black_threshold)

    # Compare the outputs
    compare_images(dirs["output_yours"], dirs["output_bordercrop"])
