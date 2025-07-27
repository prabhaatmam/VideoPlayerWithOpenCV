import cv2
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
from ffpyplayer.player import MediaPlayer
import os

class VideoPlayer:
    def __init__(self, root):
        self.root = root
        self.root.title("Video Player")
        
        # Ask user to select a video file
        self.video_path = self.select_video_file()
        if not self.video_path:
            root.destroy()  # Close the app if no file is selected
            return
        
        # Fixed 16:9 aspect ratio
        self.fixed_width = 900
        self.fixed_height = 506
        self.root.geometry(f"{self.fixed_width}x{self.fixed_height+80}")  # Extra space for controls
        
        # Open video file
        self.video = cv2.VideoCapture(self.video_path)
        self.player = MediaPlayer(self.video_path)  # Initialize audio player

        self.video_width = int(self.video.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.video_height = int(self.video.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.total_frames = int(self.video.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = int(self.video.get(cv2.CAP_PROP_FPS))

        # Video Display (Fixed size)
        self.canvas = tk.Canvas(root, width=self.fixed_width, height=self.fixed_height, bg="black")
        self.canvas.pack()

        # Progress Bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Scale(root, from_=0, to=self.total_frames, orient="horizontal",
                                      variable=self.progress_var, command=self.seek_video)
        self.progress_bar.pack(fill="x")

        # Control Bar (Bottom UI)
        control_frame = tk.Frame(root)
        control_frame.pack(fill="x", pady=5)

        # Left Section: Dropdown Menu (Non-editable)
        self.options = ["Normal", "Greyscale", "Negative"]
        self.selected_option = tk.StringVar(value=self.options[0])
        self.dropdown = ttk.Combobox(control_frame, textvariable=self.selected_option, values=self.options, 
                                     width=15, state="readonly")  # 🔥 Non-editable dropdown
        self.dropdown.pack(side="left", padx=10)

        # Middle Section: Buttons (Seek Back, Play/Pause, Seek Forward)
        button_frame = tk.Frame(control_frame)
        button_frame.pack(side="left", expand=True)

        button_size = 3  # Set square buttons
        button_font = ("Arial", 20)

        self.seek_back_btn = tk.Button(button_frame, text="⏪", command=self.seek_back,
                                       width=button_size, height=button_size, font=button_font)
        self.seek_back_btn.pack(side="left", padx=5)

        self.play_pause_btn = tk.Button(button_frame, text="▶", command=self.toggle_play_pause,
                                        width=button_size, height=button_size, font=button_font)
        self.play_pause_btn.pack(side="left", padx=5)

        self.seek_forward_btn = tk.Button(button_frame, text="⏩", command=self.seek_forward,
                                          width=button_size, height=button_size, font=button_font)
        self.seek_forward_btn.pack(side="left", padx=5)

        # Right Section: Timer Label
        self.timer_label = tk.Label(control_frame, text="00:00 / 00:00", font=("Arial", 12))
        self.timer_label.pack(side="right", padx=10)

        # Video Playback Variables
        self.is_playing = False
        self.update_video()

    def select_video_file(self):
        """Open file dialog and return selected video file path."""
        file_path = filedialog.askopenfilename(
            title="Select a Video File",
            filetypes=[
                ("MP4 files", "*.mp4"),
                ("AVI files", "*.avi"),
                ("MOV files", "*.mov"),
                ("MKV files", "*.mkv"),
                ("All Files", "*.*")  # Allow all files but show a warning for unsupported ones
            ]
        )

        if not file_path:  # User canceled file selection
            return None

        # Validate file extension
        valid_extensions = {".mp4", ".avi", ".mov", ".mkv"}
        file_ext = os.path.splitext(file_path)[1].lower()

        if file_ext not in valid_extensions:
            messagebox.showerror("Unsupported File", f"Error: '{file_ext}' is not a supported video format.")
            return None  # Return None if the file is invalid

        return file_path  # Return the valid file path

    def update_video(self):
        if self.is_playing:
            ret, frame = self.video.read()
            audio_frame, val = self.player.get_frame()  # Get audio frame

            if ret:
                frame = self.apply_filter(frame)  # Apply selected filter
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                # Resize frame to fixed size
                frame = cv2.resize(frame, (self.fixed_width, self.fixed_height))

                img = Image.fromarray(frame)
                img_tk = ImageTk.PhotoImage(image=img)
                self.canvas.create_image(0, 0, anchor=tk.NW, image=img_tk)
                self.canvas.image = img_tk

                # Update progress bar
                current_frame = int(self.video.get(cv2.CAP_PROP_POS_FRAMES))
                self.progress_var.set(current_frame)

                # Update timer
                current_time = current_frame / self.fps
                total_time = self.total_frames / self.fps
                self.timer_label.config(text=f"{self.format_time(current_time)} / {self.format_time(total_time)}")

            else:
                self.video.set(cv2.CAP_PROP_POS_FRAMES, 0)  # Loop the video
                self.player.seek(0, relative=False)  # Reset audio

        self.root.after(30, self.update_video)  # Adjust frame rate

    def apply_filter(self, frame):
        selected_filter = self.selected_option.get()
        if selected_filter == "Greyscale":
            return cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        elif selected_filter == "Negative":
            return cv2.bitwise_not(frame)
        return frame

    def format_time(self, seconds):
        """Format time in seconds to MM:SS"""
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02}:{seconds:02}"

    def toggle_play_pause(self):
        self.is_playing = not self.is_playing
        self.play_pause_btn.config(text="⏸" if self.is_playing else "▶")

        if self.is_playing:
            self.player.set_pause(False)  # Resume audio
        else:
            self.player.set_pause(True)   # Pause audio

    def seek_back(self):
        current_frame = max(0, self.progress_var.get() - 30)
        self.video.set(cv2.CAP_PROP_POS_FRAMES, current_frame)
        self.player.seek(current_frame / self.fps, relative=False)
        self.progress_var.set(current_frame)

    def seek_forward(self):
        current_frame = min(self.total_frames, self.progress_var.get() + 30)
        self.video.set(cv2.CAP_PROP_POS_FRAMES, current_frame)
        self.player.seek(current_frame / self.fps, relative=False)
        self.progress_var.set(current_frame)

    def seek_video(self, value):
        self.video.set(cv2.CAP_PROP_POS_FRAMES, float(value))
        self.player.seek(float(value) / self.fps, relative=False)

# Run the application
if __name__ == "__main__":
    root = tk.Tk()
    root.resizable(False, False)  # Disable resizing
    player = VideoPlayer(root)
    root.mainloop()
