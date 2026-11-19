import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog

import cv2
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from PIL import Image, ImageTk


root = tk.Tk()
root.title("Mini Image Processing Toolkit")
root.geometry("1180x780")
root.minsize(850, 620)

original_image = None
processed_image = None
original_photo = None
processed_photo = None
camera = None
camera_after_id = None
current_operation = lambda image: image.copy()
histogram_lines = {}


def require_image():
    if original_image is None:
        messagebox.showwarning("Gambar belum dibuka", "Buka gambar terlebih dahulu.")
        return False
    return True


def show_image(image, label):
    global original_photo, processed_photo

    if image is None:
        label.configure(image="", text="Belum ada gambar")
        return

    height, width = image.shape[:2]
    available_width = max(label.winfo_width() - 20, 1)
    available_height = max(label.winfo_height() - 20, 1)
    scale = min(available_width / width, available_height / height)
    size = (max(1, int(width * scale)), max(1, int(height * scale)))
    interpolation = cv2.INTER_AREA if scale < 1 else cv2.INTER_LINEAR
    resized = cv2.resize(image, size, interpolation=interpolation)

    if resized.ndim == 2:
        display_array = resized
    else:
        display_array = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)

    photo = ImageTk.PhotoImage(Image.fromarray(display_array))
    label.configure(image=photo, text="")
    if label is original_panel:
        original_photo = photo
    else:
        processed_photo = photo


def refresh_images(_event=None):
    show_image(original_image, original_panel)
    show_image(processed_image, processed_panel)


def open_image():
    global original_image, processed_image, current_operation

    path = filedialog.askopenfilename(
        title="Buka gambar",
        filetypes=[("Gambar", "*.jpg *.jpeg *.png"), ("Semua file", "*.*")],
    )
    if not path:
        return

    if camera is not None:
        stop_camera()

    try:
        encoded = np.fromfile(path, dtype=np.uint8)
        image = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError("Format gambar tidak didukung atau file rusak.")
        original_image = image
        processed_image = image.copy()
        current_operation = lambda frame: frame.copy()
        refresh_images()
        refresh_histogram(processed_image)
    except (OSError, ValueError, cv2.error) as error:
        messagebox.showerror("Gagal membuka gambar", str(error))


def apply_operation(operation):
    global processed_image, current_operation

    if not require_image():
        return

    try:
        result = operation(original_image.copy())
        processed_image = result
        current_operation = operation
        refresh_images()
        refresh_histogram(result)
    except (cv2.error, ValueError, TypeError, ZeroDivisionError) as error:
        messagebox.showerror("Gagal memproses gambar", str(error))


def to_grayscale(image):
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


def to_blur(image):
    return cv2.GaussianBlur(image, (15, 15), 0)


def to_threshold(image):
    gray = to_grayscale(image)
    _, result = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY)
    return result


def to_edges(image):
    return cv2.Canny(to_grayscale(image), 100, 200)


def change_brightness():
    if not require_image():
        return
    amount = simpledialog.askinteger(
        "Brightness",
        "Masukkan nilai kecerahan (-255 sampai 255):",
        minvalue=-255,
        maxvalue=255,
        parent=root,
    )
    if amount is None:
        return
    apply_operation(
        lambda image: np.clip(image.astype(np.int16) + amount, 0, 255).astype(
            np.uint8
        )
    )


def to_negative(image):
    return 255 - image


def to_sharpen(image):
    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]], dtype=np.float32)
    return cv2.filter2D(image, -1, kernel)


def to_sketch(image):
    gray = to_grayscale(image)
    inverted = 255 - gray
    blurred = cv2.GaussianBlur(inverted, (21, 21), 0)
    denominator = 255 - blurred
    sketch = gray.astype(np.float32) * 255 / np.maximum(denominator, 1)
    return np.clip(sketch, 0, 255).astype(np.uint8)


def to_equalized(image):
    ycrcb = cv2.cvtColor(image, cv2.COLOR_BGR2YCrCb)
    ycrcb[:, :, 0] = cv2.equalizeHist(ycrcb[:, :, 0])
    return cv2.cvtColor(ycrcb, cv2.COLOR_YCrCb2BGR)


def refresh_histogram(image):
    if image is None:
        return

    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB) if image.ndim == 3 else None
    for channel, color in enumerate(("red", "green", "blue")):
        if rgb_image is None:
            histogram = cv2.calcHist([image], [0], None, [256], [0, 256])
        else:
            histogram = cv2.calcHist([rgb_image], [channel], None, [256], [0, 256])
        histogram_lines[color].set_data(np.arange(256), histogram.ravel())
    histogram_axis.relim()
    histogram_axis.autoscale_view(scalex=False, scaley=True)
    histogram_canvas.draw_idle()


def start_camera():
    global camera, camera_after_id, original_image, processed_image

    if camera is not None:
        return

    try:
        camera = cv2.VideoCapture(0)
    except cv2.error as error:
        messagebox.showerror("Kamera tidak tersedia", str(error))
        return
    if not camera.isOpened():
        camera.release()
        camera = None
        messagebox.showerror(
            "Kamera tidak tersedia",
            "Kamera tidak dapat dibuka. Periksa koneksi atau izin kamera.",
        )
        return

    start_camera_button.configure(state=tk.DISABLED)
    stop_camera_button.configure(state=tk.NORMAL)
    update_camera_frame()


def update_camera_frame():
    global camera_after_id, original_image, processed_image

    camera_after_id = None
    if camera is None:
        return

    try:
        success, frame = camera.read()
    except cv2.error as error:
        stop_camera()
        messagebox.showerror("Gagal membaca kamera", str(error))
        return

    if not success:
        stop_camera()
        messagebox.showerror("Kamera terputus", "Gagal membaca frame dari kamera.")
        return

    try:
        original_image = frame
        processed_image = current_operation(frame.copy())
        refresh_images()
        refresh_histogram(processed_image)
    except (cv2.error, ValueError, TypeError, ZeroDivisionError) as error:
        stop_camera()
        messagebox.showerror("Gagal memproses frame kamera", str(error))
        return

    camera_after_id = root.after(30, update_camera_frame)


def stop_camera():
    global camera, camera_after_id

    if camera_after_id is not None:
        root.after_cancel(camera_after_id)
        camera_after_id = None
    if camera is not None:
        camera.release()
        camera = None
    start_camera_button.configure(state=tk.NORMAL)
    stop_camera_button.configure(state=tk.DISABLED)


def save_image():
    if not require_image():
        return

    path = filedialog.asksaveasfilename(
        title="Simpan hasil",
        defaultextension=".png",
        filetypes=[
            ("PNG", "*.png"),
            ("JPEG", "*.jpg *.jpeg"),
        ],
    )
    if not path:
        return

    extension = path.rsplit(".", 1)[-1].lower()
    if extension not in ("png", "jpg", "jpeg"):
        extension = "png"
        path += ".png"

    try:
        success, encoded = cv2.imencode(f".{extension}", processed_image)
        if not success:
            raise ValueError("OpenCV tidak dapat menyimpan gambar dengan format ini.")
        encoded.tofile(path)
        messagebox.showinfo("Berhasil", "Hasil pengolahan berhasil disimpan.")
    except (OSError, ValueError, cv2.error) as error:
        messagebox.showerror("Gagal menyimpan gambar", str(error))


def reset_image():
    global processed_image, current_operation

    if not require_image():
        return
    current_operation = lambda image: image.copy()
    processed_image = original_image.copy()
    refresh_images()
    refresh_histogram(processed_image)


def close_application():
    stop_camera()
    plt.close(histogram_figure)
    root.destroy()


toolbar = tk.Frame(root, padx=10, pady=10)
toolbar.pack(fill=tk.X)
tk.Button(toolbar, text="Open Image", command=open_image, width=16).pack(
    side=tk.LEFT, padx=5
)
start_camera_button = tk.Button(
    toolbar, text="Start Camera", command=start_camera, width=16
)
start_camera_button.pack(side=tk.LEFT, padx=5)
stop_camera_button = tk.Button(
    toolbar, text="Stop Camera", command=stop_camera, width=16, state=tk.DISABLED
)
stop_camera_button.pack(side=tk.LEFT, padx=5)
tk.Button(toolbar, text="Save Image", command=save_image, width=16).pack(
    side=tk.LEFT, padx=5
)
tk.Button(toolbar, text="Reset", command=reset_image, width=12).pack(
    side=tk.LEFT, padx=5
)

content = tk.Frame(root)
content.pack(fill=tk.BOTH, expand=True)

image_area = tk.Frame(content, padx=10, pady=5)
image_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
image_area.columnconfigure(0, weight=1)
image_area.columnconfigure(1, weight=1)
image_area.rowconfigure(1, weight=1)

tk.Label(image_area, text="Original Image", font=("Arial", 12, "bold")).grid(
    row=0, column=0, pady=5
)
tk.Label(image_area, text="Processed Image", font=("Arial", 12, "bold")).grid(
    row=0, column=1, pady=5
)
original_panel = tk.Label(
    image_area, text="Belum ada gambar", bg="#e8e8e8", anchor=tk.CENTER
)
original_panel.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
processed_panel = tk.Label(
    image_area, text="Belum ada gambar", bg="#e8e8e8", anchor=tk.CENTER
)
processed_panel.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)
image_area.bind("<Configure>", refresh_images)

histogram_frame = tk.Frame(content, padx=5, pady=10)
histogram_frame.pack(side=tk.RIGHT, fill=tk.Y)
histogram_figure, histogram_axis = plt.subplots(figsize=(3.3, 3.2))
histogram_axis.set_title("Histogram RGB (hasil)")
histogram_axis.set_xlabel("Intensitas piksel")
histogram_axis.set_ylabel("Jumlah piksel")
histogram_axis.set_xlim(0, 255)
for channel, color in enumerate(("red", "green", "blue")):
    (line,) = histogram_axis.plot([], [], color=color, label=color.capitalize())
    histogram_lines[color] = line
histogram_axis.legend()
histogram_figure.tight_layout()
histogram_canvas = FigureCanvasTkAgg(histogram_figure, master=histogram_frame)
histogram_canvas.draw()
histogram_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

features = tk.Frame(root, padx=10, pady=10)
features.pack(fill=tk.X)
buttons = [
    ("Grayscale", lambda: apply_operation(to_grayscale)),
    ("Blur", lambda: apply_operation(to_blur)),
    ("Threshold", lambda: apply_operation(to_threshold)),
    ("Edge Detection", lambda: apply_operation(to_edges)),
    ("Brightness", change_brightness),
    ("Negative", lambda: apply_operation(to_negative)),
    ("Sharpening", lambda: apply_operation(to_sharpen)),
    ("Mirror Horizontal", lambda: apply_operation(lambda image: cv2.flip(image, 1))),
    ("Mirror Vertical", lambda: apply_operation(lambda image: cv2.flip(image, 0))),
    ("Sketch", lambda: apply_operation(to_sketch)),
    ("Histogram Equalization", lambda: apply_operation(to_equalized)),
]
for index, (text, command) in enumerate(buttons):
    tk.Button(features, text=text, command=command, width=17).grid(
        row=index // 6, column=index % 6, padx=4, pady=4, sticky="ew"
    )

root.protocol("WM_DELETE_WINDOW", close_application)
root.mainloop()
