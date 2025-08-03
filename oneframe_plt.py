import cv2
import numpy as np
import os
from torch.utils.tensorboard import SummaryWriter
import glob
from tqdm import tqdm


def frame_to_scalar_curves(image_path):
    """Convert a Bad Apple frame to multiple scalar curves"""
    # Load the image
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise FileNotFoundError(f"Could not load image: {image_path}")

    # Threshold to binary (Bad Apple is high contrast)
    _, binary = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY)

    # Find all black pixels for each x coordinate
    height, width = binary.shape
    x_sample = np.arange(width)
    all_curves = {}  # Dictionary to store multiple curves

    for x in range(width):
        black_pixels = []
        # Find ALL black pixels in this column
        for y in range(height):
            if binary[y, x] == 0:  # Black pixel found
                black_pixels.append(y)

        # Create separate curves for each black pixel in this column
        for i, y_pos in enumerate(black_pixels):
            curve_name = f"curve_{i}"
            if curve_name not in all_curves:
                all_curves[curve_name] = np.full(width, np.nan)
            all_curves[curve_name][x] = y_pos

    return x_sample, all_curves


def log_frame_to_tensorboard(writers, frame_path, frame_number):
    """Log a single Bad Apple frame as scalar curves to TensorBoard"""
    try:
        x_data, all_curves = frame_to_scalar_curves(frame_path)

        # Create unique metric name for this frame
        metric_name = f"frame_{frame_number:04d}"

        # Log each curve to its own run
        for curve_name, y_data in all_curves.items():
            # Get or create writer for this curve
            if curve_name not in writers:
                writers[curve_name] = SummaryWriter(f"runs/badapple/{curve_name}")

            writer = writers[curve_name]

            # Log all xy data for this frame as scalars with x as the step
            for x, y in enumerate(y_data):
                if not np.isnan(y):  # Only log valid points
                    writer.add_scalar(metric_name, -y, x)  # x becomes the step!

        for curve_name, y_data in all_curves.items():
            writer = writers[curve_name]
            for x in x_data:
                writer.add_scalar(metric_name, 0, x)

            break

        print(f"Logged {metric_name} with {len(all_curves)} curves")

    except Exception as e:
        print(f"Error processing frame {frame_path}: {e}")


def log_badapple_sequence(frames_dir, log_dir="runs/badapple"):
    """Log entire Bad Apple sequence to TensorBoard"""

    # Dictionary to hold writers for each curve
    writers = {}

    # Get all frame files
    frame_files = sorted(glob.glob(os.path.join(frames_dir, "*.jpg")))

    if not frame_files:
        print(f"No .jpg files found in {frames_dir}")
        return

    print(f"Found {len(frame_files)} frames")

    try:
        # Process each frame
        for frame_num, frame_path in enumerate(tqdm(frame_files)):
            log_frame_to_tensorboard(writers, frame_path, frame_num)

            # Progress update
            if (frame_num + 1) % 10 == 0:
                print(f"Processed {frame_num + 1}/{len(frame_files)} frames")

    finally:
        # Close all writers
        for writer in writers.values():
            writer.close()
        print(f"\nDone! Created {len(writers)} curve runs")
        print(f"Each run contains {len(frame_files)} frame metrics")
        print(f"View with: tensorboard --logdir={log_dir}")


def log_single_frame_demo(frame_path, log_dir="runs/badapple_demo"):
    """Log a single frame as demo (for testing)"""
    writers = {}

    try:
        # Log just one frame
        log_frame_to_tensorboard(
            writers, frame_path, int(frame_path.split("_")[1].split(".")[0])
        )  # Use actual frame number

    finally:
        # Close all writers
        for writer in writers.values():
            writer.close()
        print(f"Demo logged with {len(writers)} curve runs!")
        print(f"Each run contains the metric '{frame_path.split('_')[1]}'")
        print(f"View with: tensorboard --logdir={log_dir}")


if __name__ == "__main__":
    # Demo with single frame first
    # single_frame = "frames/output_0145.jpg"

    # if os.path.exists(single_frame):
    #     print("Logging single frame demo...")
    #     log_single_frame_demo(single_frame)
    # else:
    #     print(f"Frame {single_frame} not found")

    # Uncomment to process entire sequence:
    frames_directory = "frames"
    if os.path.exists(frames_directory):
        print("Logging entire Bad Apple sequence...")
        log_badapple_sequence(frames_directory)
    else:
        print(f"Frames directory {frames_directory} not found")
