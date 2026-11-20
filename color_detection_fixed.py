import os
import cv2
import numpy as np
import tkinter as tk
from tkinter import filedialog, messagebox


# Common colors in BGR format (used by OpenCV)
COLORS = {
    "Red": (0, 0, 255),
    "Green": (0, 255, 0),
    "Blue": (255, 0, 0),
    "Yellow": (0, 255, 255),
    "Orange": (0, 165, 255),
    "Pink": (203, 192, 255),
    "Purple": (128, 0, 128),
    "Black": (0, 0, 0),
    "White": (255, 255, 255),
    "Gray": (128, 128, 128),
    "Brown": (42, 42, 165),
    "Cyan": (255, 255, 0),
    "Magenta": (255, 0, 255),
    "Violet": (238, 130, 238),
    "Gold": (0, 215, 255),
    "Silver": (192, 192, 192),
    "Navy Blue": (128, 0, 0),
    "Sky Blue": (235, 206, 135),
    "Maroon": (0, 0, 128),
    "Turquoise": (208, 224, 64),
    "Coral": (80, 127, 255),
    "Chocolate": (30, 105, 210),
}


class ColorDetectionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Color Detection System")
        self.root.configure(bg="#202030")

        self.current_frame = None
        self.camera = None
        self.camera_running = False
        self.photo = None
        self.canvas_image = None

        title = tk.Label(
            root,
            text="COLOR DETECTION SYSTEM",
            font=("Arial", 20, "bold"),
            fg="white",
            bg="#202030",
        )
        title.pack(pady=(15, 10))

        buttons = tk.Frame(root, bg="#202030")
        buttons.pack(pady=5)

        tk.Button(
            buttons, text="Choose Image", command=self.choose_image,
            width=16, bg="#2196F3", fg="white", font=("Arial", 12)
        ).grid(row=0, column=0, padx=6)

        tk.Button(
            buttons, text="Open Camera", command=self.open_camera,
            width=16, bg="#4CAF50", fg="white", font=("Arial", 12)
        ).grid(row=0, column=1, padx=6)

        tk.Button(
            buttons, text="Stop Camera", command=self.stop_camera,
            width=16, bg="#F44336", fg="white", font=("Arial", 12)
        ).grid(row=0, column=2, padx=6)

        result_row = tk.Frame(root, bg="#202030")
        result_row.pack(pady=10)

        self.swatch = tk.Label(result_row, width=4, height=2, bg="#202030")
        self.swatch.pack(side="left", padx=10)

        self.result_label = tk.Label(
            result_row,
            text="Choose an image or open the camera, then click a color.",
            font=("Arial", 11),
            fg="white",
            bg="#202030",
            wraplength=600,
            justify="left",
        )
        self.result_label.pack(side="left")

        self.canvas = tk.Canvas(
            root, width=640, height=400, bg="#101018", highlightthickness=0
        )
        self.canvas.pack(padx=10, pady=(0, 10))
        self.canvas.bind("<Button-1>", self.detect_color)

        self.root.protocol("WM_DELETE_WINDOW", self.close)

    def show_frame(self, frame):
        """Show an OpenCV (BGR) frame inside the Tkinter canvas."""
        height, width = frame.shape[:2]
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        header = f"P6 {width} {height} 255\n".encode()
        self.photo = tk.PhotoImage(data=header + rgb.tobytes())

        self.canvas.config(width=width, height=height)
        if self.canvas_image is None:
            self.canvas_image = self.canvas.create_image(
                0, 0, anchor="nw", image=self.photo
            )
        else:
            self.canvas.itemconfig(self.canvas_image, image=self.photo)

    def choose_image(self):
        path = filedialog.askopenfilename(
            title="Select an image",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp")]
        )
        if not path:
            return

        # np.fromfile + imdecode also works with non-English file paths
        try:
            data = np.fromfile(path, dtype=np.uint8)
            image = cv2.imdecode(data, cv2.IMREAD_COLOR)
        except Exception:
            image = None

        if image is None:
            messagebox.showerror("Error", "Could not open this image.")
            return

        height, width = image.shape[:2]
        scale = min(900 / width, 600 / height, 1)
        new_size = (max(1, int(width * scale)), max(1, int(height * scale)))
        image = cv2.resize(image, new_size)

        self.stop_camera()
        self.current_frame = image.copy()
        self.show_frame(self.current_frame)

    def open_camera(self):
        self.stop_camera()

        if os.name == "nt":
            self.camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        else:
            self.camera = cv2.VideoCapture(0)

        if not self.camera.isOpened():
            self.camera.release()
            self.camera = None
            messagebox.showerror(
                "Camera Error",
                "Camera could not be opened. Check that it is connected and not in use."
            )
            return

        self.camera_running = True
        self.update_camera()

    def update_camera(self):
        if not self.camera_running or self.camera is None:
            return

        success, frame = self.camera.read()
        if not success:
            self.stop_camera()
            messagebox.showerror("Camera Error", "Could not read from the camera.")
            return

        self.current_frame = frame.copy()
        self.show_frame(self.current_frame)
        self.root.after(30, self.update_camera)

    def detect_color(self, event):
        if self.current_frame is None:
            return

        frame = self.current_frame
        height, width = frame.shape[:2]
        x, y = event.x, event.y
        if not (0 <= x < width and 0 <= y < height):
            return

        b, g, r = [int(value) for value in frame[y, x]]

        nearest_name = "Unknown"
        nearest_distance = float("inf")
        pixel = np.array([b, g, r], dtype=float)

        for name, bgr in COLORS.items():
            distance = np.linalg.norm(pixel - np.array(bgr, dtype=float))
            if distance < nearest_distance:
                nearest_distance = distance
                nearest_name = name

        hex_code = f"#{r:02X}{g:02X}{b:02X}"
        self.swatch.config(bg=hex_code)
        self.result_label.config(
            text=f"Color: {nearest_name}   RGB: ({r}, {g}, {b})   HEX: {hex_code}"
        )

    def stop_camera(self):
        self.camera_running = False
        if self.camera is not None:
            self.camera.release()
            self.camera = None

    def close(self):
        self.stop_camera()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = ColorDetectionApp(root)
    root.mainloop()
