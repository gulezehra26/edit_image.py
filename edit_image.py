import cv2
import numpy as np
from tkinter import filedialog
from tkinter import Tk, Button, Scale, HORIZONTAL, Label, Frame, Canvas
from PIL import Image, ImageTk
from rembg import remove
import os
from io import BytesIO

# State
edited_image = None
canvas_photo = None
CANVAS_W, CANVAS_H = 560, 400

# Window
window = Tk()
window.title('Photo Editor')
window.geometry('820x760')
window.configure(bg='#f9f9f9')

header = Label(window, text="Photo Editor",font=("Helvetica", 18, "bold"), bg="#3a3d46", fg="white", pady=14)
header.pack(fill="x")

button_frame = Frame(window, bg='#f9f9f9')
button_frame.pack(pady=15)

canvas = Canvas(window, width=CANVAS_W, height=CANVAS_H, bg='white',highlightthickness=1, highlightbackground='#cccccc')
canvas.pack(pady=12)

status_label = Label(window, text='No image loaded',bg='#f9f9f9', fg='#666', font=('Arial', 10, "italic"))
status_label.pack(pady=6)

# Helpers
def apply_brightness_contrast(img_bgr, brightness, contrast):
    if img_bgr is None:
        return None
    out = cv2.convertScaleAbs(img_bgr, alpha=float(contrast), beta=int(brightness))
    return out

def apply_sepia_intensity(img_bgr, strength):
    """strength [0..100]"""
    if strength == 0:
        return img_bgr
    kernel = np.array([[0.272, 0.534, 0.131],
                       [0.349, 0.686, 0.168],
                       [0.393, 0.769, 0.189]])
    sep = cv2.transform(img_bgr, kernel)
    sep = np.clip(sep, 0, 255).astype(np.uint8)
    alpha = strength / 100.0
    blended = cv2.addWeighted(sep, alpha, img_bgr, 1 - alpha, 0)
    return blended

def show_on_canvas(img_bgr):
    global canvas_photo
    if img_bgr is None:
        return
    h, w = img_bgr.shape[:2]
    scale = min(CANVAS_W / w, CANVAS_H / h)
    new_w, new_h = max(1, int(w * scale)), max(1, int(h * scale))
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(img_rgb).resize((new_w, new_h), resample=Image.LANCZOS)
    canvas_photo = ImageTk.PhotoImage(pil_img)
    canvas.delete("all")
    x0 = (CANVAS_W - new_w) // 2
    y0 = (CANVAS_H - new_h) // 2
    canvas.create_image(x0, y0, anchor='nw', image=canvas_photo)

def re_preview():
    if edited_image is None:
        return
    b = int(brightness_slider.get())
    c = float(contrast_slider.get())
    s = int(sepia_slider.get())
    preview = apply_brightness_contrast(edited_image, b, c)
    preview = apply_sepia_intensity(preview, s)
    show_on_canvas(preview)

# Actions
def open_image():
    global edited_image
    fp = filedialog.askopenfilename(
        filetypes=[('Image files', '*.jpg;*.jpeg;*.png;*.bmp;*.webp')])
    if not fp:
        return
    img = cv2.imread(fp, cv2.IMREAD_COLOR)
    if img is None:
        status_label.config(text='Failed to load image')
        return
    edited_image = img
    status_label.config(text=f'Image loaded: {os.path.basename(fp)}')
    brightness_slider.set(0)
    contrast_slider.set(1.0)
    sepia_slider.set(0)
    re_preview()

def rotate_90():
    global edited_image
    if edited_image is None:
        return
    edited_image = cv2.rotate(edited_image, cv2.ROTATE_90_CLOCKWISE)
    re_preview()

def flip(mode):
    global edited_image
    if edited_image is None:
        return
    if mode == 'H':
        edited_image = cv2.flip(edited_image, 1)
    else:
        edited_image = cv2.flip(edited_image, 0)
    re_preview()

def invert_color():
    global edited_image
    if edited_image is None:
        return
    edited_image = cv2.bitwise_not(edited_image)
    re_preview()

def remove_bg_action():
    global edited_image
    if edited_image is None:
        return
    rgb = cv2.cvtColor(edited_image, cv2.COLOR_BGR2RGB)
    no_bg = remove(rgb)
    if isinstance(no_bg, bytes):
        pil = Image.open(BytesIO(no_bg)).convert('RGBA')
    elif isinstance(no_bg, np.ndarray):
        pil = Image.fromarray(no_bg).convert('RGBA')
    else:
        pil = no_bg.convert('RGBA')
    bg = Image.new('RGBA', pil.size, (255, 255, 255, 255))
    merged = Image.alpha_composite(bg, pil).convert('RGB')
    edited_image = cv2.cvtColor(np.array(merged), cv2.COLOR_RGB2BGR)
    re_preview()

def save_image():
    if edited_image is None:
        status_label.config(text="No image to save")
        return
    b = int(brightness_slider.get())
    c = float(contrast_slider.get())
    s = int(sepia_slider.get())
    final_img = apply_brightness_contrast(edited_image, b, c)
    final_img = apply_sepia_intensity(final_img, s)
    fp = filedialog.asksaveasfilename(defaultextension=".jpg",filetypes=[("JPEG", "*.jpg"), ("PNG", "*.png")])
    if fp:
        cv2.imwrite(fp, final_img)
        status_label.config(text=f"Saved: {os.path.basename(fp)}")

# UI 
btn_style = {"fg": "white", "padx": 10, "pady": 6,
             "relief": "flat", "width": 12, "font": ("Arial", 10, "bold")}

Button(button_frame, text='Open', command=open_image,bg="#5D6D7E", **btn_style).grid(row=0, column=0, padx=6)
Button(button_frame, text='Invert', command=invert_color,bg="#AAB7B8", **btn_style).grid(row=0, column=1, padx=6)
Button(button_frame, text='Rotate 90', command=rotate_90,bg="#73C6B6", **btn_style).grid(row=0, column=2, padx=6)
Button(button_frame, text='Flip H', command=lambda: flip('H'),bg="#85C1E9", **btn_style).grid(row=0, column=3, padx=6)
Button(button_frame, text='Flip V', command=lambda: flip('V'),bg="#F1948A", **btn_style).grid(row=0, column=4, padx=6)
Button(button_frame, text='Remove BG', command=remove_bg_action,bg="#BB8FCE", **btn_style).grid(row=0, column=5, padx=6)
Button(button_frame, text='Save', command=save_image,bg="#58D68D", **btn_style).grid(row=0, column=6, padx=6)

control_frame = Frame(window, bg='#f9f9f9')
control_frame.pack(pady=15)

Label(control_frame, text='Brightness', bg='#f9f9f9',fg='#333', font=("Arial", 11, "bold")).grid(row=0, column=0, padx=10)
brightness_slider = Scale(control_frame, from_=-100, to=100, orient=HORIZONTAL,command=lambda v: re_preview(), length=280)
brightness_slider.set(0)
brightness_slider.grid(row=0, column=1)

Label(control_frame, text='Contrast', bg='#f9f9f9',fg='#333', font=("Arial", 11, "bold")).grid(row=1, column=0, padx=10)
contrast_slider = Scale(control_frame, from_=0.5, to=3.0, resolution=0.1,orient=HORIZONTAL, command=lambda v: re_preview(), length=280)
contrast_slider.set(1.0)
contrast_slider.grid(row=1, column=1)

Label(control_frame, text='Sepia Strength', bg='#f9f9f9',fg='#333', font=("Arial", 11, "bold")).grid(row=2, column=0, padx=10)
sepia_slider = Scale(control_frame, from_=0, to=100, orient=HORIZONTAL,command=lambda v: re_preview(), length=280)
sepia_slider.set(0)
sepia_slider.grid(row=2, column=1)

footer = Label(window, text="Designed with Python | OpenCV + Tkinter",font=("Arial", 9), bg="#3a3d46", fg="white", pady=8)
footer.pack(fill="x", side="bottom")

window.mainloop()
