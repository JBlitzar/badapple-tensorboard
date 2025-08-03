import cv2
import numpy as np
import matplotlib.pyplot as plt
from scipy import ndimage


def frame_to_scalar_curves(image_path):
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


def plot_scalar_curves(x_data, all_curves, original_image_path):
    # Load image to get dimensions
    img = cv2.imread(original_image_path, cv2.IMREAD_GRAYSCALE)
    height, width = img.shape

    # Calculate aspect ratio and determine padding needed
    aspect_ratio = width / height
    target_width = max(width, int(height * 1.5))  # Assume target aspect ratio ~1.5

    if target_width > width:
        # Need to pad horizontally
        pad_total = target_width - width
        pad_left = pad_total // 2
        pad_right = pad_total - pad_left

        # Create padded x_data
        x_padded = np.arange(-pad_left, width + pad_right)

        # Pad all curves with zeros (top of image)
        padded_curves = {}
        for curve_name, y_data in all_curves.items():
            padded_y = np.full(len(x_padded), 0.0)  # Fill with zeros (top edge)
            # Copy original data to center
            padded_y[pad_left : pad_left + width] = np.nan_to_num(y_data, nan=0.0)
            padded_curves[curve_name] = padded_y
    else:
        x_padded = x_data
        padded_curves = all_curves

    # Create subplot
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))

    # Show original image with correct aspect ratio
    ax1.imshow(img, cmap="gray", aspect="equal")
    ax1.set_title("Original Bad Apple Frame")
    ax1.axis("off")

    # Plot all scalar curves with padding
    colors = plt.cm.tab10(np.linspace(0, 1, len(padded_curves)))
    for (curve_name, y_data), color in zip(padded_curves.items(), colors):
        # Only plot non-zero values (since zeros are padding)
        valid_mask = y_data > 0
        if np.any(valid_mask):
            ax2.plot(
                x_padded[valid_mask],
                y_data[valid_mask],
                color=color,
                linewidth=1,
                alpha=0.7,
                label=curve_name,
            )

    ax2.set_xlabel("X Position (pixels)")
    ax2.set_ylabel("Y Position (pixels)")
    ax2.set_title(f"Multiple Scalar Curves ({len(padded_curves)} curves)")
    ax2.grid(True, alpha=0.3)

    # Set equal aspect ratio for the curve plot too
    ax2.set_aspect("equal")

    # Flip y-axis to match image coordinates
    ax2.invert_yaxis()

    # Add legend if not too many curves
    if len(padded_curves) <= 10:
        ax2.legend(bbox_to_anchor=(1.05, 1), loc="upper left")

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    image_path = "frames/output_0145.jpg"

    try:
        x_data, all_curves = frame_to_scalar_curves(image_path)

        if x_data is not None and all_curves:
            plot_scalar_curves(x_data, all_curves, image_path)

            # Print some sample values for TensorBoard format
            print(f"\nFound {len(all_curves)} scalar curves")
            print("\nSample scalar values for TensorBoard:")

            # Show sample from first few curves
            for curve_name, y_data in list(all_curves.items())[:3]:
                print(f"\n{curve_name}:")
                valid_indices = ~np.isnan(y_data)
                sample_indices = np.where(valid_indices)[0][:: len(x_data) // 10]
                for i in sample_indices[:5]:  # Show first 5 samples
                    print(f"  {curve_name}_x{i:03d}: {y_data[i]:.1f}")
        else:
            print("Failed to extract curves from image")

    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Make sure the image file exists at the specified path")
