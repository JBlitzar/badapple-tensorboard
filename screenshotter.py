from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
import time
import os
import zipfile
import argparse
from datetime import datetime
from tqdm import trange
import glob


class FrameCapture:
    def __init__(self, url, headless=False, window_size="1920,1080"):
        self.url = url
        self.headless = headless
        self.window_size = window_size
        self.driver = None
        self.screenshots_taken = 0

    def setup_driver(self):
        """Setup Chrome driver with optimal settings"""
        options = Options()
        if self.headless:
            options.add_argument("--headless")
        options.add_argument(f"--window-size={self.window_size}")
        options.add_argument("--disable-web-security")
        options.add_argument("--disable-features=VizDisplayCompositor")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        self.driver = webdriver.Chrome(options=options)
        return self.driver

    def wait_for_element_update(self, element, expected_value, timeout=5):
        """Wait for element to have the expected value"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if element.get_attribute("value") == expected_value:
                return True
            time.sleep(0.1)
        return False

    def capture_frames(
        self, start_frame=43, max_frame=6571, delay_ms=200, screenshot_delay=0.5
    ):
        """Main frame capture function"""
        self.setup_driver()

        try:
            print(f"Navigating to: {self.url}")
            self.driver.get(self.url)

            # Wait for page to load
            wait = WebDriverWait(self.driver, 10)
            input_element = wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, 'input[placeholder="Filter tags (regex)"]')
                )
            )
            print("Input element found!")

            # Create directory structure
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            frames_dir = "frames_rendered"  # f"frames_{timestamp}"
            os.makedirs(frames_dir, exist_ok=True)

            total_frames = max_frame - start_frame + 1
            print(f"Starting capture of {total_frames} frames...")
            print(f"Range: frame_{start_frame:04d} to frame_{max_frame:04d}")

            start_time = time.time()

            for i in trange(start_frame, max_frame + 1):
                try:
                    padded = str(i).zfill(4)
                    value = f"frame_{padded}"

                    # Clear input and set new value
                    input_element.clear()
                    input_element.send_keys(value)

                    # Trigger events (similar to your original JS)
                    self.driver.execute_script(
                        """
                        arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
                        arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
                    """,
                        input_element,
                    )

                    # Wait for page to update
                    time.sleep(screenshot_delay)

                    # Take screenshot
                    screenshot_path = os.path.join(frames_dir, f"frame_{padded}.png")
                    success = self.driver.save_screenshot(screenshot_path)

                    if success:
                        self.screenshots_taken += 1

                    # Progress updates
                    if i % 50 == 0 or i == max_frame:
                        elapsed = time.time() - start_time
                        progress = ((i - start_frame + 1) / total_frames) * 100
                        rate = self.screenshots_taken / elapsed if elapsed > 0 else 0
                        remaining = (
                            (total_frames - (i - start_frame + 1)) / rate
                            if rate > 0
                            else 0
                        )

                        print(
                            f"Progress: {progress:.1f}% | Frame {i}/{max_frame} | "
                            f"Rate: {rate:.1f} fps | ETA: {remaining / 60:.1f} min"
                        )

                    # Delay between iterations
                    time.sleep(delay_ms / 1000.0)

                except Exception as e:
                    print(f"Error capturing frame {i}: {e}")
                    continue

            print(
                f"\nScreenshot capture complete! {self.screenshots_taken} screenshots taken."
            )

            # compile into video with ffmpeg
            # compile into video with ffmpeg
            print("Compiling frames into video...")
            # Find the lowest frame number from actual files
            frame_files = glob.glob(os.path.join(frames_dir, "frame_*.png"))
            if frame_files:
                frame_numbers = [
                    int(os.path.basename(f).split("_")[1].split(".")[0])
                    for f in frame_files
                ]
                first_frame = min(frame_numbers)
            else:
                first_frame = start_frame

            os.system(
                f"ffmpeg -framerate 30 -start_number {first_frame} -i {frames_dir}/frame_%04d.png -c:v libx264 -pix_fmt yuv420p -vf scale=1920:1080 frames_{timestamp}.mp4"
            )

            # Create zip archive
            self.create_archive(frames_dir, f"frames_{timestamp}.zip")

            return frames_dir

        except Exception as e:
            print(f"Error occurred: {e}")
            return None

        finally:
            if self.driver:
                self.driver.quit()

    def create_archive(self, frames_dir, zip_name):
        """Create zip archive of all screenshots"""
        print(f"Creating zip archive: {zip_name}")

        with zipfile.ZipFile(
            zip_name, "w", zipfile.ZIP_DEFLATED, compresslevel=6
        ) as zipf:
            for root, dirs, files in os.walk(frames_dir):
                for file in files:
                    if file.endswith(".png"):
                        file_path = os.path.join(root, file)
                        zipf.write(file_path, file)

        # Get file size
        zip_size = os.path.getsize(zip_name) / (1024 * 1024)  # MB
        print(f"Archive created: {zip_name} ({zip_size:.1f} MB)")

        import shutil

        shutil.rmtree(frames_dir)
        print("Individual frame files removed.")


def main():
    parser = argparse.ArgumentParser(description="Capture frames using Selenium")
    parser.add_argument("url", help="URL of the page to capture")
    parser.add_argument("--start", type=int, default=2354, help="Starting frame number")
    parser.add_argument("--end", type=int, default=6571, help="Ending frame number")
    parser.add_argument(
        "--delay", type=int, default=200, help="Delay between frames (ms)"
    )
    parser.add_argument(
        "--screenshot-delay",
        type=float,
        default=0.5,
        help="Delay before screenshot (seconds)",
    )
    parser.add_argument("--headless", action="store_true", help="Run in headless mode")
    parser.add_argument(
        "--window-size", default="1920,1080", help="Browser window size"
    )

    args = parser.parse_args()

    capturer = FrameCapture(args.url, args.headless, args.window_size)
    capturer.capture_frames(args.start, args.end, args.delay, args.screenshot_delay)


if __name__ == "__main__":
    # If no command line args, run with defaults
    import sys

    if len(sys.argv) == 1:
        url = "http://localhost:6006/"
        capturer = FrameCapture(url)
        capturer.capture_frames()
    else:
        main()
