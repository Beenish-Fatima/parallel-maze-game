import tkinter as tk
import time
import os
from maze_app import MazeApp

try:
    from PIL import Image, ImageTk
except Exception:
    Image = None
    ImageTk = None

class StartScreen:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Welcome — Parallel Maze Game")
        self.root.state("zoomed")
        self.root.configure(bg="#070820")

        self.image_path = os.path.join(os.path.dirname(__file__), "mazeback.jpg.jpeg")
        self.original_img = None
        if Image is not None:
            try:
                self.original_img = Image.open(self.image_path)
            except Exception:
                self.original_img = None

        self.bg_label = tk.Label(self.root)
        self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        if self.original_img is not None and ImageTk is not None:
            self.root.bind("<Configure>", self.resize_bg)

        self.shadow_border = tk.Frame(self.root, bg="#f8edce")
        self.shadow_border.place(relx=0.507, rely=0.268, anchor="center")
        self.shadow = tk.Label(
            self.shadow_border,
            text="PARALLEL MAZE GAME",
            font=("Courier New", 70, "bold"),
            fg="#ff6b6b",
            bg="#233d49"
        )
        self.shadow.pack(padx=12, pady=8)

        self.outline_border = tk.Frame(self.root, bg="#f8edce")
        self.outline_border.place(relx=0.507, rely=0.260, anchor="center")
        self.outline = tk.Label(
            self.outline_border,
            text="PARALLEL MAZE GAME",
            font=("Courier New", 70, "bold"),
            fg="#cfc30f",
            bg="#233d49"
        )
        self.outline.pack(padx=85, pady=8)

        self.neon = tk.Label(
            self.root,
            text="PARALLEL MAZE GAME",
            font=("Verdana", 68, "bold"),
            fg="#488285",
            bg="#233d49"
        )
        self.neon.place(relx=0.507, rely=0.260, anchor="center")

        self.sub_border = tk.Frame(self.root, bg="#f8edce")
        self.sub_border.place(relx=0.5, rely=0.46, anchor="center")
        self.sub = tk.Label(
            self.sub_border,
            text="Let's race the algorithms — Sequential vs Parallel",
            font=("Segoe UI", 20, "bold"),
            fg="#f8edce",
            bg="#233d49"
        )
        self.sub.pack(padx=12, pady=8)

        btn_border = tk.Frame(self.root, bg="#233d49", highlightthickness=0)
        btn_border.place(relx=0.5, rely=0.75, anchor="center")
        self.start_btn = tk.Button(btn_border, text="LET'S PLAY", font=("Verdana", 15, "bold"),
                                   fg="#00110a", bg="#f1b446", activebackground="#f8edce",
                                   padx=24, pady=12, bd=0, relief="flat", command=self.launch_main)
        self.start_btn.pack(padx=4, pady=4)
        self.colors = ["#488285", "#f8edce", "#ff6b6b", "#ffd84f"]
        self.animate()
        self.root.mainloop()

    def resize_bg(self, event):
        if self.original_img:
            try:
                img = self.original_img.resize((event.width, event.height), Image.LANCZOS)
                self.bg_image = ImageTk.PhotoImage(img)
                self.bg_label.config(image=self.bg_image)
            except Exception:
                pass

    def animate(self):
        color = self.colors[int(time.time() * 2) % len(self.colors)]
        self.neon.config(fg=color)
        jitter = (int(time.time() * 3) % 3) - 1
        self.neon.place_configure(relx=0.5 + jitter * 0.001)
        self.shadow.config(fg="#ff6b6b" if color != "#ff6b6b" else "#ffaa88")
        self.root.after(120, self.animate)

    def launch_main(self):
        try:
            self.root.destroy()
        except:
            pass
        main_root = tk.Tk()
        MazeApp(main_root)
        main_root.mainloop()

if __name__ == "__main__":
    StartScreen()
