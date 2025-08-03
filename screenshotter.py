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
from tqdm import tqdm
import glob
import concurrent.futures
import threading
from queue import Queue


class FrameCapture:
    def __init__(self, url, headless=False, window_size="1920,1080", max_workers=4):
        self.url = url
        self.headless = headless
        self.window_size = window_size
        self.max_workers = max_workers
        self.screenshots_taken = 0
        self.lock = threading.Lock()

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
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-plugins")

        return webdriver.Chrome(options=options)

    def capture_single_frame(self, frame_num, frames_dir, screenshot_delay=0.5):
        """Capture a single frame in a separate browser instance"""
        driver = None
        try:
            driver = self.setup_driver()
            driver.get(self.url)

            # Wait for page to load
            wait = WebDriverWait(driver, 10)
            input_element = wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, 'input[placeholder="Filter tags (regex)"]')
                )
            )

            padded = str(frame_num).zfill(4)
            value = f"frame_{padded}"

            # Clear input and set new value
            input_element.clear()
            input_element.send_keys(value)

            # Trigger events
            driver.execute_script(
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
            success = driver.save_screenshot(screenshot_path)

            if success:
                with self.lock:
                    self.screenshots_taken += 1

            return frame_num, success

        except Exception as e:
            print(f"Error capturing frame {frame_num}: {e}")
            return frame_num, False

        finally:
            if driver:
                driver.quit()

    def capture_frames(
        self, start_frame=43, max_frame=6571, delay_ms=200, screenshot_delay=0.5
    ):
        """Main frame capture function with concurrent execution"""

        # Create directory structure
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        frames_dir = "frames_rendered"
        os.makedirs(frames_dir, exist_ok=True)

        total_frames = max_frame - start_frame + 1
        print(f"Starting concurrent capture of {total_frames} frames...")
        print(f"Range: frame_{start_frame:04d} to frame_{max_frame:04d}")
        print(f"Using {self.max_workers} concurrent workers")

        start_time = time.time()
        frame_range = range(start_frame, max_frame + 1)

        # Use ThreadPoolExecutor for concurrent execution
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=self.max_workers
        ) as executor:
            # Submit all frame capture tasks
            future_to_frame = {
                executor.submit(
                    self.capture_single_frame, frame_num, frames_dir, screenshot_delay
                ): frame_num
                for frame_num in frame_range
            }

            # Process completed tasks with progress bar
            completed = 0
            with tqdm(
                total=total_frames, desc="Capturing frames", unit="frame"
            ) as pbar:
                for future in concurrent.futures.as_completed(future_to_frame):
                    frame_num = future_to_frame[future]
                    try:
                        frame_result, success = future.result()
                        completed += 1
                        pbar.update(1)

                        # Update progress info
                        elapsed = time.time() - start_time
                        rate = completed / elapsed if elapsed > 0 else 0
                        pbar.set_postfix(
                            {
                                "rate": f"{rate:.1f} fps",
                                "completed": completed,
                                "success": self.screenshots_taken,
                            }
                        )

                    except Exception as exc:
                        print(f"Frame {frame_num} generated an exception: {exc}")
                        completed += 1
                        pbar.update(1)

        elapsed_total = time.time() - start_time
        print(f"\nScreenshot capture complete!")
        print(f"Successfully captured: {self.screenshots_taken}/{total_frames} frames")
        print(f"Total time: {elapsed_total:.1f} seconds")
        print(f"Average rate: {self.screenshots_taken / elapsed_total:.1f} fps")

        # Compile into video with ffmpeg
        print("Compiling frames into video...")
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
    parser.add_argument("--start", type=int, default=3228, help="Starting frame number")
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
    parser.add_argument(
        "--workers", type=int, default=8, help="Number of concurrent workers"
    )

    args = parser.parse_args()

    capturer = FrameCapture(args.url, args.headless, args.window_size, args.workers)
    capturer.capture_frames(args.start, args.end, args.delay, args.screenshot_delay)


if __name__ == "__main__":
    # If no command line args, run with defaults
    import sys

    if len(sys.argv) == 1:
        url = "http://localhost:6006/"
        capturer = FrameCapture(url, max_workers=4)
        capturer.capture_frames()
    else:
        main()
