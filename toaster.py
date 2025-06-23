import cv2
import numpy as np
import mss
import keyboard
import threading
import time
import os
import platform
from collections import deque
import tkinter as tk

# === USER SETTINGS ===
FPS = 60                # Recording FPS (set as high as your machine allows)
CLIP_LENGTH = 15        # Length of each clip (seconds)
SAVE_FOLDER = os.path.abspath('.')  # Change this to any folder you want


# === Popup Notification ===
def show_popup(filename, duration=2):
    def popup():
        root = tk.Tk()
        root.overrideredirect(True)
        root.attributes('-topmost', True)
        root.attributes('-alpha', 0.93)
        w, h = 320, 62
        screen_w = root.winfo_screenwidth()
        screen_h = root.winfo_screenheight()
        x = screen_w - w - 42
        y = screen_h - h - 60
        root.geometry(f"{w}x{h}+{x}+{y}")
        frame = tk.Frame(root, bg="#222", bd=2)
        frame.pack(fill="both", expand=True)
        label = tk.Label(
            frame,
            text=f"Clip Saved!\n{os.path.basename(filename)}",
            fg="#fff", bg="#222", font=("Segoe UI", 13, "bold"), justify="center"
        )
        label.pack(expand=True)
        root.after(int(duration * 1000), root.destroy)
        root.mainloop()
    threading.Thread(target=popup).start()

# === Clipper Logic ===
def grab_screen(monitor):
    img = np.array(mss.mss().grab(monitor))
    img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
    return img

def open_folder(path):
    try:
        if platform.system() == "Windows":
            os.startfile(path)
        elif platform.system() == "Darwin":
            os.system(f'open "{path}"')
        else:
            os.system(f'xdg-open "{path}"')
    except Exception as e:
        print("Could not open folder:", e)

def main():
    mss_instance = mss.mss()
    monitor = mss_instance.monitors[1]
    width, height = monitor["width"], monitor["height"]
    frame_buffer = deque()
    timestamp_buffer = deque()
    clip_count = 1

    print(f"Toaster is running (no GUI). Press F8 to save the last {CLIP_LENGTH} seconds. Ctrl+C to exit.")
    print(f"Clips will be saved to: {SAVE_FOLDER}")
    print("Tip: Press Ctrl+Break or close this window to stop.")

    while True:
        try:
            now = time.time()
            frame = grab_screen(monitor)
            frame_buffer.append(frame)
            timestamp_buffer.append(now)
            # Only keep last N seconds
            while timestamp_buffer and (now - timestamp_buffer[0] > CLIP_LENGTH):
                frame_buffer.popleft()
                timestamp_buffer.popleft()

            # Listen for hotkey
            if keyboard.is_pressed("f8"):
                # Actual FPS for the segment
                if len(timestamp_buffer) > 1:
                    duration = timestamp_buffer[-1] - timestamp_buffer[0]
                    actual_fps = len(timestamp_buffer) / duration if duration > 0 else FPS
                else:
                    actual_fps = FPS
                print(f"Saving {len(frame_buffer)} frames at {actual_fps:.2f} FPS")
                # File name and save
                if not os.path.exists(SAVE_FOLDER):
                    os.makedirs(SAVE_FOLDER)
                filename = os.path.join(SAVE_FOLDER, f"clip_{clip_count:02d}.mp4")
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                out = cv2.VideoWriter(filename, fourcc, actual_fps, (width, height))
                for f in frame_buffer:
                    out.write(f)
                out.release()
                print(f"Saved to {filename}")
                show_popup(filename)
                clip_count += 1
                time.sleep(1)  # debounce

            time.sleep(max(0, 1/FPS - (time.time() - now)))
        except KeyboardInterrupt:
            print("Stopped.")
            break
        except Exception as e:
            print("Error:", e)

if __name__ == "__main__":
    main()
