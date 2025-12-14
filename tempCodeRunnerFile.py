# main.py
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import tempfile
import webbrowser
import pandas as pd
import plotly.express as px

# Import your algorithm implementations (they must return (path, elapsed_seconds))
from algorithms.bfs_sequential import bfs_sequential
from algorithms.bfs_parallel import bfs_parallel
from algorithms.dfs_sequential import dfs_sequential
from algorithms.dfs_parallel import dfs_parallel
from algorithms.dijkstra_sequential import dijkstra_sequential
from algorithms.dijkstra_parallel import dijkstra_parallel
from algorithms.astar_sequential import astar_sequential
from algorithms.astar_parallel import astar_parallel
from utils import generate_weights, in_bounds

CELL_SIZE = 36


# ---------------------------
# Utility: center a window
# ---------------------------
def center_window(win, width, height):
    """Place a Tk window in the center of the screen with given width/height."""
    win.update_idletasks()
    screen_w = win.winfo_screenwidth()
    screen_h = win.winfo_screenheight()
    x = (screen_w // 2) - (width // 2)
    y = (screen_h // 2) - (height // 2)
    win.geometry(f"{width}x{height}+{x}+{y}")


# ---------------------------
# Main Maze Application
# ---------------------------
class MazeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Parallel Maze Game")
        # Ensure main window centered (size chosen, later can expand)
        center_window(self.root, 980, 680)

        # Maze / app state
        self.n = 12
        self.speed = 0.02
        self.weighted_mode = False
        self.weights = {}
        self.start = (0, 0)
        self.goal = (self.n - 1, self.n - 1)
        self.stop_event = threading.Event()
        self.num_threads = 4
        self.walls = set()

        # store results: list of tuples (algo, mode, time)
        self.results = []

        # build UI (light-themed)
        self.build_ui()

    def build_ui(self):
        # light background
        self.root.configure(bg="#f4f7fb")

        # Title area
        header = tk.Frame(self.root, bg="#f4f7fb")
        header.pack(fill="x", pady=(10, 4))
        title_lbl = tk.Label(
            header,
            text="Parallel Maze Game",
            font=("Segoe UI", 20, "bold"),
            fg="#1b3b8f",
            bg="#f4f7fb",
        )
        title_lbl.pack()

        # Topbar with action buttons
        topbar = tk.Frame(self.root, bg="#f4f7fb")
        topbar.pack(fill="x", padx=12, pady=(4, 8))

        ttk.Style().configure("Topbar.TButton", font=("Segoe UI", 10, "bold"), padding=6)
        ttk.Button(topbar, text="Reset Maze", command=self.reset_maze, style="Topbar.TButton").pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(topbar, text="Stop", command=self.stop, style="Topbar.TButton").pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(topbar, text="View Results", command=self.show_results_table, style="Topbar.TButton").pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(topbar, text="Show Chart", command=self.show_plotly_chart, style="Topbar.TButton").pack(side=tk.LEFT, padx=(0, 8))

        # Main area: left controls + right canvas
        main = tk.Frame(self.root, bg="#f4f7fb")
        main.pack(fill="both", expand=True, padx=12, pady=8)

        # Left control panel
        left = tk.Frame(main, bg="#f4f7fb")
        left.pack(side=tk.LEFT, fill="y", padx=(0, 12))

        sec_font = ("Segoe UI", 11, "bold")
        lbl_font = ("Segoe UI", 10)

        tk.Label(left, text="Maze Type", font=sec_font, bg="#f4f7fb").pack(anchor="w")
        self.maze_type = tk.StringVar(value="simple")
        tk.Radiobutton(left, text="Simple Maze", variable=self.maze_type, value="simple", command=self.update_maze_type, bg="#f4f7fb").pack(anchor="w")
        tk.Radiobutton(left, text="Weighted Maze", variable=self.maze_type, value="weighted", command=self.update_maze_type, bg="#f4f7fb").pack(anchor="w")

        tk.Label(left, text="Grid Size", font=sec_font, bg="#f4f7fb").pack(anchor="w", pady=(10, 0))
        self.size_spin = tk.Spinbox(left, from_=6, to=30, width=6, font=lbl_font, command=self.resize_grid)
        self.size_spin.delete(0, "end"); self.size_spin.insert(0, str(self.n))
        self.size_spin.pack(anchor="w", pady=(2, 6))

        tk.Label(left, text="Threads", font=sec_font, bg="#f4f7fb").pack(anchor="w")
        self.thread_spin = tk.Spinbox(left, from_=1, to=12, width=6, font=lbl_font, command=self.update_threads)
        self.thread_spin.delete(0, "end"); self.thread_spin.insert(0, str(self.num_threads))
        self.thread_spin.pack(anchor="w", pady=(2, 8))

        tk.Label(left, text="Algorithms", font=sec_font, bg="#f4f7fb").pack(anchor="w", pady=(8, 4))

        # Algorithm buttons (kept same labels)
        btns = [
            ("Sequential BFS", ("BFS","Sequential", bfs_sequential)),
            ("Parallel BFS", ("BFS","Parallel", bfs_parallel)),
            ("Sequential DFS", ("DFS","Sequential", dfs_sequential)),
            ("Parallel DFS", ("DFS","Parallel", dfs_parallel)),
            ("Sequential Dijkstra", ("Dijkstra","Sequential", dijkstra_sequential)),
            ("Parallel Dijkstra", ("Dijkstra","Parallel", dijkstra_parallel)),
            ("Sequential A*", ("A*","Sequential", astar_sequential)),
            ("Parallel A*", ("A*","Parallel", astar_parallel)),
        ]
        for text, args in btns:
            ttk.Button(left, text=text, command=lambda a=args: self.run(a[0], a[1], a[2])).pack(fill="x", pady=3)

        # Right canvas (light)
        right = tk.Frame(main, bg="#272121")
        right.pack(side=tk.RIGHT, expand=True, fill="both")

        canvas_frame = tk.Frame(right, bg="#ffffff", bd=1, relief="solid")
        canvas_frame.pack(padx=6, pady=6, expand=True)
        self.canvas = tk.Canvas(canvas_frame, width=self.n * CELL_SIZE, height=self.n * CELL_SIZE, bg="white")
        self.canvas.pack()

        self.draw_grid()

    # --- basic controls ---
    def update_threads(self):
        try:
            self.num_threads = int(self.thread_spin.get())
        except:
            pass

    def resize_grid(self):
        try:
            self.n = int(self.size_spin.get())
        except:
            pass
        self.goal = (self.n - 1, self.n - 1)
        if self.weighted_mode:
            self.weights = generate_weights(self.n)
        self.canvas.config(width=self.n * CELL_SIZE, height=self.n * CELL_SIZE)
        self.draw_grid()

    def update_maze_type(self):
        self.weighted_mode = (self.maze_type.get() == "weighted")
        if self.weighted_mode:
            self.weights = generate_weights(self.n)
        else:
            self.weights = {}
        self.draw_grid()

    def draw_grid(self):
        self.canvas.delete("all")
        for i in range(self.n):
            for j in range(self.n):
                x1 = j * CELL_SIZE
                y1 = i * CELL_SIZE
                x2 = x1 + CELL_SIZE
                y2 = y1 + CELL_SIZE

                fill = "#ddb8b8"  # light cell
                if (i, j) == self.start:
                    fill = "#8bc34a"
                elif (i, j) == self.goal:
                    fill = "#e57373"
                elif (i, j) in self.walls:
                    fill = "#333333"

                self.canvas.create_rectangle(x1, y1, x2, y2, fill=fill, outline="#cccccc")

                if self.weighted_mode and (i, j) not in (self.start, self.goal):
                    w = self.weights.get((i, j), 1)
                    self.canvas.create_text(x1 + CELL_SIZE / 2, y1 + CELL_SIZE / 2, text=str(w), font=("Arial", 10, "bold"))

    def draw_cell(self, pos, color):
        if not in_bounds(pos[0], pos[1], self.n):
            return
        x, y = pos
        x1 = y * CELL_SIZE
        y1 = x * CELL_SIZE
        x2 = x1 + CELL_SIZE
        y2 = y1 + CELL_SIZE
        self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="black")
        self.root.update_idletasks()

    def highlight_path(self, path):
        for (x, y) in path:
            x1 = y * CELL_SIZE
            y1 = x * CELL_SIZE
            self.canvas.create_rectangle(x1, y1, x1 + CELL_SIZE, y1 + CELL_SIZE, fill="#00e676", outline="black")
        self.root.update_idletasks()

    def get_edge_weight(self, a, b):
        return 1 if not self.weighted_mode else self.weights.get(b, 1)

    def stop(self):
        self.stop_event.set()

    def reset_maze(self):
        self.stop_event.set()
        time.sleep(0.05)
        self.stop_event.clear()
        import random
        all_cells = [(i, j) for i in range(self.n) for j in range(self.n) if (i, j) not in (self.start, self.goal)]
        k = int(len(all_cells) * 0.18)
        self.walls = set(random.sample(all_cells, k))
        if self.weighted_mode:
            self.weights = generate_weights(self.n)
        self.draw_grid()

    # --- run algorithm and store time ---
    def run(self, algo_name, mode, func):
        self.stop_event.clear()
        self.draw_grid()

        def task():
            start_time = time.time()
            path, used_time = func(
                self.start, self.goal, self.n,
                walls=self.walls,
                get_edge_weight=self.get_edge_weight,
                draw_cell=self.draw_cell,
                draw_edge=None,
                player_update=None,
                speed=self.speed,
                stop_event=self.stop_event,
                num_threads=self.num_threads
            )
            elapsed = used_time if used_time else time.time() - start_time
            self.results.append((algo_name, mode, elapsed))
            if path:
                self.highlight_path(path)
            messagebox.showinfo("Execution Time", f"{algo_name} ({mode})\nTime: {elapsed:.4f} sec")

        threading.Thread(target=task, daemon=True).start()

    # --- results table ---
    def show_results_table(self):
        if not self.results:
            messagebox.showwarning("No Results", "Run some algorithms first!")
            return
        win = tk.Toplevel(self.root)
        win.title("Execution Results")
        center_window(win, 600, 420)
        cols = ("Algorithm", "Mode", "Time (s)")
        tree = ttk.Treeview(win, columns=cols, show="headings", height=14)
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, width=180, anchor="center")
        for a, m, t in self.results:
            tree.insert("", tk.END, values=(a, m, f"{t:.4f}"))
        tree.pack(fill="both", expand=True, padx=10, pady=10)
        btn_frame = tk.Frame(win)
        btn_frame.pack(pady=(0, 8))
        ttk.Button(btn_frame, text="Clear Results", command=lambda: (self.results.clear(), tree.delete(*tree.get_children()))).pack(side=tk.LEFT, padx=6)
        ttk.Button(btn_frame, text="Close", command=win.destroy).pack(side=tk.LEFT, padx=6)

    # --- Plotly neon chart (opens in browser) ---
    def show_plotly_chart(self):
        if not self.results:
            messagebox.showwarning("No Data", "Run at least one algorithm to chart results.")
            return

        # Prepare DataFrame
        df = pd.DataFrame(self.results, columns=["Algorithm", "Mode", "Time"])
        # Bar chart grouped by Algorithm with Mode as color
        fig = px.bar(df, x="Algorithm", y="Time", color="Mode", barmode="group",
                     title="Algorithm Execution Times (Sequential vs Parallel)",
                     template="plotly_dark",
                     text=df["Time"].apply(lambda v: f"{v:.4f}"))
        # Neon-style color tweak
        fig.update_layout(
            plot_bgcolor="#0b0b12",
            paper_bgcolor="#0b0b12",
            font=dict(color="#e6f7ff"),
            title=dict(font=dict(size=18, color="#7afcff"))
        )
        fig.update_traces(marker_line_color="#00ffd5", marker_line_width=1.5)
        # Save to temporary HTML and open
        tmp = tempfile.NamedTemporaryFile(suffix=".html", delete=False)
        fig.write_html(tmp.name, include_plotlyjs="cdn")
        webbrowser.open(tmp.name)


# ---------------------------
# Start screen: mix of Neon Glow (A) + Arcade/Retro Pixel (C)
# ---------------------------
class StartScreen:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Welcome — Parallel Maze Game")
        center_window(self.root, 640, 380)
        self.root.configure(bg="#070820")

        # create layered labels to simulate arcade outline + neon glow
        # bottom outline (retro arcade thick outline)
        self.outline = tk.Label(self.root, text="PARALLEL MAZE GAME",
                                font=("Courier New", 28, "bold"),
                                fg="#ffec00", bg="#070820")
        self.outline.place(relx=0.5, rely=0.28, anchor="center")
        # middle shadow (slightly offset)
        self.shadow = tk.Label(self.root, text="PARALLEL MAZE GAME",
                               font=("Courier New", 28, "bold"),
                               fg="#ff6b6b", bg="#070820")
        self.shadow.place(relx=0.5+0.007, rely=0.28+0.006, anchor="center")
        # top neon text
        self.neon = tk.Label(self.root, text="PARALLEL MAZE GAME",
                             font=("Verdana", 26, "bold"),
                             fg="#00f2ff", bg="#070820")
        self.neon.place(relx=0.5, rely=0.28, anchor="center")

        # little subtitle
        sub = tk.Label(self.root, text="Let's race the algorithms — Sequential vs Parallel",
                       font=("Segoe UI", 10), fg="#a8bcd8", bg="#070820")
        sub.place(relx=0.5, rely=0.38, anchor="center")

        # Start button (arcade green)
        self.start_btn = tk.Button(self.root, text="LET'S PLAY", font=("Verdana", 18, "bold"),
                                   fg="#00110a", bg="#00ff66", activebackground="#00ff99",
                                   padx=20, pady=8, command=self.launch_main)
        self.start_btn.place(relx=0.5, rely=0.6, anchor="center")

        # animate both neon color cycling and slight 'pixel jitter' for arcade feel
        self.glow_colors = ["#00f2ff", "#7cffb2", "#ff6b6b", "#ffd84f"]
        self.jitter_phase = 0
        self.animate()

        self.root.mainloop()

    def animate(self):
        # neon color cycle
        color = self.glow_colors[int(time.time() * 2) % len(self.glow_colors)]
        self.neon.config(fg=color)
        # slight jitter for arcade 'pixel' vibe
        jitter = (int(time.time() * 4) % 3) - 1  # -1,0,1
        self.neon.place_configure(relx=0.5 + jitter * 0.001, rely=0.28)
        # shadow and outline sync
        self.shadow.config(fg="#ff6b6b" if color != "#ff6b6b" else "#ffaa88")
        self.outline.config(fg="#ffec00")
        # loop
        self.root.after(140, self.animate)

    def launch_main(self):
        # destroy start screen and open main app centered
        self.root.destroy()
        main_root = tk.Tk()
        app = MazeApp(main_root)
        main_root.mainloop()


# ---------------------------
# Run
# ---------------------------
if __name__ == "__main__":
    StartScreen()
