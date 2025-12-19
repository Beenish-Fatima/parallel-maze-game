import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import pandas as pd
import random
from utils import generate_weights, in_bounds

# Optional image support
try:
    from PIL import Image, ImageTk
except Exception:
    Image = None
    ImageTk = None

# Your algorithm modules must exist and return (path, elapsed_seconds)
from algorithms.bfs_sequential import bfs_sequential
from algorithms.bfs_parallel import bfs_parallel
from algorithms.dfs_sequential import dfs_sequential
from algorithms.dfs_parallel import dfs_parallel
from algorithms.dijkstra_sequential import dijkstra_sequential
from algorithms.dijkstra_parallel import dijkstra_parallel
from algorithms.astar_sequential import astar_sequential
from algorithms.astar_parallel import astar_parallel

MAX_GRID_SIZE = 20
MIN_CELL_SIZE = 20
MAX_CELL_SIZE = 50

def center_window(win, width, height):
    win.update_idletasks()
    screen_w = win.winfo_screenwidth()
    screen_h = win.winfo_screenheight()
    x = (screen_w // 2) - (width // 2)
    y = (screen_h // 2) - (height // 2)
    win.geometry(f"{width}x{height}+{x}+{y}")

def make_neon_button(btn, base_bg, hover_glow):
    def on_enter(e):
        try:
            btn.config(background=hover_glow)
        except:
            pass
    def on_leave(e):
        try:
            btn.config(background=base_bg)
        except:
            pass
    btn.bind("<Enter>", on_enter)
    btn.bind("<Leave>", on_leave)

class MazeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Parallel Maze Game — Neon UI")
        self.root.state("zoomed")

        # app state
        self.n = 15
        self.speed = 0.02
        self.weighted_mode = False
        self.weights = {}
        self.start = (0, 0)
        self.goal = (self.n - 1, self.n - 1)
        self.stop_event = threading.Event()
        self.num_threads = 4
        self.walls = set()
        self.results = []  # (algo, mode, time, threads)
        self.cell_size = 36  # Initial cell size
        self.grid_x_offset = 0
        self.grid_y_offset = 0

        # Darker color palette from attached image
        self.dark_blue = "#172026"   # very dark blue for walls
        self.red = "#B84A39"         # deep red
        self.yellow = "#C97D2A"      # deep yellow
        self.teal = "#2B6B63"        # deep teal
        self.cream = "#EEC276"       # cream for maze grid
        self.bg_dark = "#35867D"     # new dark background for main area
        self.bg_light = "#DAB640"    # lighter background for panels

        # UI colors
        self.neon_bg = self.bg_dark   # main background is dark
        self.panel_bg = "#EAC345"  # side panel is dark
        self.glow_cyan = self.yellow
        self.glow_purple = self.dark_blue
        self.button_cyan = self.teal
        self.button_purple = self.yellow
        self.text_light = self.bg_dark # text is cream for contrast
        self.grid_bg =  "#EAC345"   # maze grid is cream

        self.build_ui()

    def build_ui(self):
        self.root.configure(bg=self.neon_bg)
        title_frame = tk.Frame(self.root, bg=self.neon_bg)
        title_frame.pack(fill="x", pady=(8, 6))
        title_lbl = tk.Label(
            title_frame,
            text="PARALLEL MAZE GAME",
            font=("Verdana", 28, "bold"),
            fg=self.bg_light,
            bg=self.neon_bg
        )
        title_lbl.pack(pady=(4,2))
        subtitle = tk.Label(
            title_frame,
            text="Race algorithms — Sequential vs Parallel",
            font=("Segoe UI", 14),
            fg=self.bg_light,
            bg=self.neon_bg
        )
        subtitle.pack()
        topbar = tk.Frame(self.root, bg=self.neon_bg)
        topbar.pack(fill="x", padx=16, pady=(6, 10))
        reset_btn = tk.Button(topbar, text="Reset Maze", font=("Segoe UI", 10, "bold"),
                              bg=self.button_purple, fg="black", bd=0, padx=10, pady=6,
                              activebackground=self.glow_purple, command=self.reset_maze)
        reset_btn.pack(side="left", padx=(0,8))
        reset_btn.config(highlightthickness=2, highlightbackground=self.glow_purple)
        make_neon_button(reset_btn, self.button_purple, self.glow_purple)
        stop_btn = tk.Button(topbar, text="Stop", font=("Segoe UI", 10, "bold"),
                             bg=self.button_cyan, fg="black", bd=0, padx=10, pady=6,
                             activebackground=self.glow_cyan, command=self.stop)
        stop_btn.pack(side="left", padx=(0,8))
        stop_btn.config(highlightthickness=2, highlightbackground=self.glow_cyan)
        make_neon_button(stop_btn, self.button_cyan, self.glow_cyan)
        view_btn = tk.Button(topbar, text="View Results", font=("Segoe UI", 10, "bold"),
                             bg=self.button_purple, fg="black", bd=0, padx=10, pady=6,
                             activebackground=self.glow_cyan, command=self.show_results_table)
        view_btn.pack(side="left", padx=(0,8))
        view_btn.config(highlightthickness=2, highlightbackground=self.glow_purple)
        make_neon_button(view_btn, self.button_purple, self.glow_purple)
        chart_btn = tk.Button(topbar, text="Show Chart", font=("Segoe UI", 10, "bold"),
                              bg=self.button_cyan, fg="black", bd=0, padx=10, pady=6,
                              activebackground=self.glow_purple, command=self.show_chart_in_window)
        chart_btn.pack(side="left", padx=(0,8))
        chart_btn.config(highlightthickness=2, highlightbackground=self.glow_purple)
        make_neon_button(chart_btn, self.button_cyan, self.glow_purple)
        main = tk.Frame(self.root, bg=self.neon_bg)
        main.pack(fill="both", expand=True, padx=14, pady=(6,14))
        panel_width = 260
        left_card_outer = tk.Frame(main, bg=self.panel_bg, width=panel_width)
        left_card_outer.pack_propagate(False)
        left_card_outer.pack(side="left", fill="y", padx=(0,12), pady=6)
        left_card_outer.config(highlightthickness=3, highlightbackground=self.glow_purple)
        left_canvas = tk.Canvas(left_card_outer, bg=self.panel_bg, highlightthickness=0, width=panel_width)
        left_canvas.pack(side="left", fill="y", expand=False)
        scrollbar = tk.Scrollbar(left_card_outer, orient="vertical", command=left_canvas.yview)
        scrollbar.pack(side="right", fill="y")
        left_canvas.configure(yscrollcommand=scrollbar.set)
        left_card = tk.Frame(left_canvas, bg=self.panel_bg, width=panel_width)
        left_card_id = left_canvas.create_window((0,0), window=left_card, anchor="nw", width=panel_width)
        def _on_frame_configure(event):
            left_canvas.configure(scrollregion=left_canvas.bbox("all"))
        left_card.bind("<Configure>", _on_frame_configure)
        def _on_mousewheel(event):
            left_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        left_card.bind_all("<MouseWheel>", _on_mousewheel)
        lbl_title = tk.Label(left_card, text="Controls", font=("Segoe UI", 14, "bold"), fg=self.text_light, bg=self.panel_bg)
        lbl_title.pack(padx=12, pady=(12,6), anchor="w")
        tk.Label(left_card, text="Maze Type", font=("Segoe UI", 11), fg="#25313c", bg=self.panel_bg).pack(anchor="w", padx=12)
        self.maze_type = tk.StringVar(value="simple")
        tk.Radiobutton(left_card, text="Simple", variable=self.maze_type, value="simple",
                       bg=self.panel_bg, fg="#25313c", selectcolor=self.neon_bg, command=self.update_maze_type).pack(anchor="w", padx=18, pady=(2,0))
        tk.Radiobutton(left_card, text="Weighted", variable=self.maze_type, value="weighted",
                       bg=self.panel_bg, fg="#25313c", selectcolor=self.neon_bg, command=self.update_maze_type).pack(anchor="w", padx=18, pady=(0,8))
        tk.Label(left_card, text="Grid Size", font=("Segoe UI", 11), fg="#25313c", bg=self.panel_bg).pack(anchor="w", padx=12)
        self.size_var = tk.IntVar(value=self.n)
        self.size_spin = tk.Spinbox(left_card, from_=6, to=MAX_GRID_SIZE, width=6, font=("Segoe UI",10), textvariable=self.size_var)
        self.size_spin.pack(anchor="w", padx=18, pady=(2,8))
        def on_size_var_change(*args):
            try:
                new_n = self.size_var.get()
                if 6 <= new_n <= MAX_GRID_SIZE and new_n != self.n:
                    self.n = new_n
                    self.goal = (self.n - 1, self.n - 1)
                    if self.weighted_mode:
                        self.weights = generate_weights(self.n)
                    self.walls = {(i, j) for (i, j) in self.walls if i < self.n and j < self.n}
                    self.calculate_cell_size()
                    self.update_canvas_size()
            except Exception:
                pass
        self.size_var.trace_add('write', on_size_var_change)
        tk.Label(left_card, text="Threads", font=("Segoe UI", 11), fg="#25313c", bg=self.panel_bg).pack(anchor="w", padx=12)
        self.thread_spin = tk.Spinbox(left_card, from_=1, to=12, width=6, font=("Segoe UI",10))
        self.thread_spin.delete(0,"end"); self.thread_spin.insert(0,str(self.num_threads))
        self.thread_spin.pack(anchor="w", padx=18, pady=(2,8))
        tk.Label(left_card, text="Animation Speed", font=("Segoe UI", 11), fg="#25313c", bg=self.panel_bg).pack(anchor="w", padx=12, pady=(10,0))
        speed_frame = tk.Frame(left_card, bg=self.panel_bg)
        speed_frame.pack(anchor="w", padx=18, pady=(2,8))
        self.speed_var = tk.DoubleVar(value=self.speed)
        self.speed_slider = tk.Scale(speed_frame, from_=0.001, to=0.1, resolution=0.001, orient="horizontal",
                                    variable=self.speed_var, length=120, 
                                    bg=self.panel_bg, fg="#25313c", highlightthickness=0,
                                    command=self.update_speed)
        self.speed_slider.pack()
        tk.Label(left_card, text="Algorithms", font=("Segoe UI", 11), fg="#25313c", bg=self.panel_bg).pack(anchor="w", padx=12, pady=(6,4))
        btn_cfg = {"width":22, "padx":6, "pady":6, "bd":0}
        def neon_btn(parent, text, cmd, primary=True):
            bg = self.button_purple if primary else self.button_cyan
            hover = self.glow_purple if primary else self.glow_cyan
            b = tk.Button(parent, text=text, bg=bg, fg="black", font=("Segoe UI",10,"bold"),
                          activebackground=hover, command=cmd, **btn_cfg)
            b.pack(padx=12, pady=6)
            b.config(highlightthickness=2, highlightbackground=hover)
            make_neon_button(b, bg, hover)
            return b
        neon_btn(left_card, "Sequential BFS", lambda: self.run("BFS","Sequential",bfs_sequential), primary=True)
        neon_btn(left_card, "Parallel BFS", lambda: self.run("BFS","Parallel",bfs_parallel), primary=False)
        neon_btn(left_card, "Sequential DFS", lambda: self.run("DFS","Sequential",dfs_sequential), primary=True)
        neon_btn(left_card, "Parallel DFS", lambda: self.run("DFS","Parallel",dfs_parallel), primary=False)
        neon_btn(left_card, "Sequential Dijkstra", lambda: self.run("Dijkstra","Sequential",dijkstra_sequential), primary=True)
        neon_btn(left_card, "Parallel Dijkstra", lambda: self.run("Dijkstra","Parallel",dijkstra_parallel), primary=False)
        neon_btn(left_card, "Sequential A*", lambda: self.run("A*","Sequential",astar_sequential), primary=True)
        neon_btn(left_card, "Parallel A*", lambda: self.run("A*","Parallel",astar_parallel), primary=False)
        self.canvas_card = tk.Frame(main, bg=self.neon_bg)
        self.canvas_card.pack(side="right", expand=True, fill="both")
        self.canvas_inner = tk.Frame(self.canvas_card, bg=self.grid_bg, bd=2, relief="raised")
        self.canvas_inner.pack(padx=12, pady=12, expand=True, fill="both")
        self.canvas_inner.config(highlightthickness=6, highlightbackground=self.glow_cyan)
        self.canvas_frame = tk.Frame(self.canvas_inner, bg=self.grid_bg)
        self.canvas_frame.pack(expand=True, fill="both", padx=6, pady=6)
        self.canvas = tk.Canvas(
            self.canvas_frame, 
            bg=self.grid_bg
        )
        self.canvas.pack(expand=True, fill="both")
        self.calculate_cell_size()
        self.root.after(100, self.setup_bindings)
        self.root.after(150, self.initial_draw)

    def calculate_cell_size(self):
        self.canvas_frame.update_idletasks()
        available_width = self.canvas_frame.winfo_width() - 20
        available_height = self.canvas_frame.winfo_height() - 20
        if available_width > 0 and available_height > 0:
            width_based = available_width // self.n
            height_based = available_height // self.n
            new_cell_size = min(width_based, height_based, MAX_CELL_SIZE)
            new_cell_size = max(new_cell_size, MIN_CELL_SIZE)
            if new_cell_size != self.cell_size:
                self.cell_size = new_cell_size
                return True
        return False

    def calculate_grid_position(self):
        self.canvas_frame.update_idletasks()
        canvas_width = self.canvas_frame.winfo_width()
        canvas_height = self.canvas_frame.winfo_height()
        grid_width = self.n * self.cell_size
        grid_height = self.n * self.cell_size
        self.grid_x_offset = (canvas_width - grid_width) // 2
        self.grid_y_offset = (canvas_height - grid_height) // 2
        self.grid_x_offset = max(0, self.grid_x_offset)
        self.grid_y_offset = max(0, self.grid_y_offset)

    def initial_draw(self):
        self.draw_grid()

    def setup_bindings(self):
        def update_size(event=None):
            try:
                new_n = int(self.size_spin.get())
                if 6 <= new_n <= MAX_GRID_SIZE and new_n != self.n:
                    self.n = new_n
                    self.goal = (self.n - 1, self.n - 1)
                    if self.weighted_mode:
                        self.weights = generate_weights(self.n)
                    self.walls = {(i, j) for (i, j) in self.walls if i < self.n and j < self.n}
                    self.calculate_cell_size()
                    self.update_canvas_size()
            except ValueError:
                self.size_spin.delete(0, "end")
                self.size_spin.insert(0, str(self.n))
        def update_threads(event=None):
            try:
                new_threads = int(self.thread_spin.get())
                if 1 <= new_threads <= 12:
                    self.num_threads = new_threads
            except ValueError:
                self.thread_spin.delete(0, "end")
                self.thread_spin.insert(0, str(self.num_threads))
        self.size_spin.bind("<Return>", update_size)
        self.size_spin.bind("<FocusOut>", update_size)
        self.size_spin.bind("<ButtonRelease-1>", update_size)
        self.thread_spin.bind("<Return>", update_threads)
        self.thread_spin.bind("<FocusOut>", update_threads)
        self.canvas_frame.bind("<Configure>", self.on_frame_resize)

    def on_frame_resize(self, event=None):
        if self.calculate_cell_size():
            self.update_canvas_size()
        else:
            self.calculate_grid_position()
            self.draw_grid()

    def update_canvas_size(self):
        self.canvas.config(
            width=self.n * self.cell_size,
            height=self.n * self.cell_size
        )
        self.calculate_grid_position()
        self.draw_grid()

    def update_speed(self, value=None):
        self.speed = self.speed_var.get()

    def update_maze_type(self):
        self.weighted_mode = (self.maze_type.get() == "weighted")
        if self.weighted_mode:
            self.weights = generate_weights(self.n)
        else:
            self.weights = {}
        self.draw_grid()

    def draw_grid(self):
        """Draw the entire grid, ensuring start and goal are never walls."""
        self.canvas.delete("all")
        self.calculate_grid_position()

        for i in range(self.n):
            for j in range(self.n):
                x1 = self.grid_x_offset + j * self.cell_size
                y1 = self.grid_y_offset + i * self.cell_size
                x2 = x1 + self.cell_size
                y2 = y1 + self.cell_size

                # Default fill
                fill = self.cream

                # Start and goal always visible
                if (i, j) == self.start:
                    fill = self.teal
                elif (i, j) == self.goal:
                    fill = self.red
                # Walls (never overwrite start/goal)
                elif (i, j) in self.walls and (i, j) not in (self.start, self.goal):
                    fill = self.dark_blue

                self.canvas.create_rectangle(x1, y1, x2, y2, fill=fill, outline=self.yellow)

                # Draw weight if needed
                if self.weighted_mode and (i, j) not in (self.start, self.goal) and (i, j) not in self.walls:
                    w = self.weights.get((i, j), 1)
                    font_size = max(8, min(14, self.cell_size // 3))
                    self.canvas.create_text(
                        x1 + self.cell_size / 2,
                        y1 + self.cell_size / 2,
                        text=str(w),
                        font=("Arial", font_size, "bold"),
                        fill="#281010"
                    )

        self.canvas.update_idletasks()


    def draw_cell(self, pos, color):
        """Draw a single cell at position pos with the given color."""
        x, y = pos
        if not in_bounds(x, y, self.n):
            return

        # Never allow start/goal to be overwritten by walls
        if pos == self.start:
            color = self.teal
        elif pos == self.goal:
            color = self.red

        x1 = self.grid_x_offset + y * self.cell_size
        y1 = self.grid_y_offset + x * self.cell_size
        x2 = x1 + self.cell_size
        y2 = y1 + self.cell_size

        self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline=self.yellow)

        # Draw weight if applicable
        if self.weighted_mode and pos not in (self.start, self.goal) and pos not in self.walls:
            w = self.weights.get((x, y), 1)
            font_size = max(8, min(14, self.cell_size // 3))
            self.canvas.create_text(
                x1 + self.cell_size / 2,
                y1 + self.cell_size / 2,
                text=str(w),
                font=("Arial", font_size, "bold"),
                fill="#3a0c0c"
            )

        self.canvas.update_idletasks()
        time.sleep(self.speed)

    def highlight_path(self, path):
        for (x, y) in path:
            x1 = self.grid_x_offset + y * self.cell_size
            y1 = self.grid_y_offset + x * self.cell_size
            self.canvas.create_rectangle(
                x1, y1, 
                x1 + self.cell_size, 
                y1 + self.cell_size, 
                fill=self.yellow, 
                outline=self.red
            )
        self.canvas.update_idletasks()

    def get_edge_weight(self, a, b):
        return 1 if not self.weighted_mode else self.weights.get(b, 1)

    def stop(self):
        self.stop_event.set()

    def reset_maze(self):
        # Stop any running algorithms
        self.stop_event.set()
        time.sleep(0.05)
        self.stop_event.clear()

        # Generate all possible cells except start and goal
        all_cells = [(i, j) for i in range(self.n) for j in range(self.n)
                    if (i, j) != self.start and (i, j) != self.goal]

        # Randomly pick ~18% of cells to be walls
        k = int(len(all_cells) * 0.18)
        self.walls = set(random.sample(all_cells, k))

        # Ensure start and goal are never walls (redundant safety)
        self.walls.discard(self.start)
        self.walls.discard(self.goal)

        # Regenerate weights if in weighted mode
        if self.weighted_mode:
            self.weights = generate_weights(self.n)

        # Redraw the grid
        self.draw_grid()

    def run(self, algo_name, mode, func):
        self.stop_event.clear()
        self.draw_grid()
        def task():
            start_time = time.time()
            threads_used = 1
            params = {
                "start": self.start,
                "goal": self.goal,
                "n": self.n,
                "walls": self.walls,
                "get_edge_weight": self.get_edge_weight,
                "draw_cell": self.draw_cell,
                "draw_edge": None,
                "player_update": None,
                "speed": self.speed,
                "stop_event": self.stop_event
            }
            if "Parallel" in mode:
                try:
                    threads_used = int(self.thread_spin.get())
                    if threads_used < 1:
                        threads_used = 1
                    params["num_threads"] = threads_used
                except:
                    threads_used = self.num_threads
                    params["num_threads"] = threads_used
            path, used_time = func(**params)
            elapsed = used_time if used_time else time.time() - start_time
            self.results.append((algo_name, mode, elapsed, threads_used))
            def show_result_window(title, message, success=True):
                win = tk.Toplevel(self.root)
                win.title(title)
                center_window(win, 250, 200)
                win.configure(bg=self.teal)
                win.resizable(False, False)
                icon_frame = tk.Frame(win, bg=self.yellow)
                icon_frame.pack(pady=(10, 0))
                icon_lbl = tk.Label(icon_frame, text="\u2139", font=("Segoe UI", 23, "bold"), fg=self.yellow if success else self.red, bg=self.glow_purple)
                icon_lbl.pack()
                msg_lbl = tk.Label(win, text=message, font=("Segoe UI", 12), fg=self.yellow, bg=self.dark_blue, justify="left")
                msg_lbl.pack(pady=(5, 5))
                ok_btn = tk.Button(win, text="OK", font=("Segoe UI", 12, "bold"), bg=self.yellow, fg=self.dark_blue, bd=0, padx=18, pady=0, command=win.destroy)
                ok_btn.pack(pady=(8,8))
                ok_btn.config(highlightthickness=2, highlightbackground=self.teal)
                make_neon_button(ok_btn, self.yellow, self.teal)
                win.transient(self.root)
                win.grab_set()
            if isinstance(path, list) and path and all(isinstance(p, (tuple, list)) and len(p) == 2 for p in path):
                self.highlight_path(path)
                show_result_window(
                    "Algorithm Complete",
                    f"{algo_name} ({mode})\nTime: {elapsed:.4f} seconds\nThreads used: {threads_used}\nPath length: {len(path)}",
                    success=True
                )
            else:
                show_result_window(
                    "No Path Found",
                    f"{algo_name} ({mode})\nTime: {elapsed:.4f} seconds\nThreads used: {threads_used}\nNo path found from start to goal!",
                    success=False
                )
        threading.Thread(target=task, daemon=True).start()

    def show_results_table(self):
        if not self.results:
            messagebox.showwarning("No Results", "Run some algorithms first!")
            return
        win = tk.Toplevel(self.root)
        win.title("Execution Results")
        center_window(win, 750, 480)
        win.configure(bg=self.teal)
        title_label = tk.Label(
            win,
            text="Algorithm Execution Results",
            font=("Verdana", 16, "bold"),
            fg=self.glow_cyan,
            bg=self.teal
        )
        title_label.pack(pady=(15, 10))
        table_frame = tk.Frame(win, bg=self.panel_bg, bd=2, relief="raised")
        table_frame.pack(padx=20, pady=10, fill="both", expand=True)
        table_frame.config(highlightthickness=3, highlightbackground=self.yellow)
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Custom.Treeview",
                        background=self.panel_bg,
                        foreground=self.text_light,
                        fieldbackground=self.panel_bg,
                        borderwidth=0,
                        rowheight=28,
                        font=("Segoe UI", 10))
        style.configure("Custom.Treeview.Heading",
                        background=self.button_purple,
                        foreground="black",
                        font=("Segoe UI", 10, "bold"),
                        relief="flat")
        style.map("Custom.Treeview.Heading",
                background=[('active', self.glow_purple)])
        style.map("Custom.Treeview",
                background=[('selected', self.glow_cyan)],
                foreground=[('selected', 'black')])
        cols = ("Algorithm", "Mode", "Time (s)", "Threads")
        tree = ttk.Treeview(table_frame, columns=cols, show="headings", style="Custom.Treeview")
        for col in cols:
            tree.heading(col, text=col, anchor="center")
            tree.column(col, anchor="center", width=150, minwidth=100)
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        tree.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        vsb.grid(row=0, column=1, sticky="ns", pady=5)
        hsb.grid(row=1, column=0, sticky="ew", padx=5)
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        for i, (algo, mode, t, th) in enumerate(self.results):
            tag = "evenrow" if i % 2 == 0 else "oddrow"
            tree.insert("", tk.END, values=(algo, mode, f"{t:.4f}", th), tags=(tag,))
        tree.tag_configure("evenrow", background="#1a0f30", foreground="#E6DCC3")
        tree.tag_configure("oddrow", background=self.panel_bg, foreground="#1a0f30")
        btn_frame = tk.Frame(win, bg=self.neon_bg)
        btn_frame.pack(pady=(15, 20))
        clear_btn = tk.Button(btn_frame, text="Clear Results",
                            font=("Segoe UI", 10, "bold"),
                            bg=self.button_purple, fg="black",
                            bd=0, padx=15, pady=8,
                            activebackground=self.glow_purple,
                            command=lambda: (self.results.clear(), tree.delete(*tree.get_children())))
        clear_btn.pack(side="left", padx=10)
        clear_btn.config(highlightthickness=2, highlightbackground=self.glow_purple)
        make_neon_button(clear_btn, self.button_purple, self.glow_purple)
        export_btn = tk.Button(btn_frame, text="Export to CSV",
                            font=("Segoe UI", 10, "bold"),
                            bg=self.yellow, fg="black",
                            bd=0, padx=15, pady=8,
                            activebackground=self.glow_cyan,
                            command=lambda: self.export_results_to_csv())
        export_btn.pack(side="left", padx=10)
        export_btn.config(highlightthickness=2, highlightbackground=self.glow_cyan)
        make_neon_button(export_btn, self.button_cyan, self.glow_cyan)
        close_btn = tk.Button(btn_frame, text="Close",
                            font=("Segoe UI", 10, "bold"),
                            bg=self.panel_bg, fg=self.text_light,
                            bd=0, padx=15, pady=8,
                            activebackground=self.glow_cyan,
                            command=win.destroy)
        close_btn.pack(side="left", padx=10)
        close_btn.config(highlightthickness=2, highlightbackground=self.glow_cyan)
        make_neon_button(close_btn, self.panel_bg, self.glow_cyan)
        total_runs = len(self.results)
        seq_runs = len([r for r in self.results if r[1] == "Sequential"])
        par_runs = len([r for r in self.results if r[1] == "Parallel"])
        stats_label = tk.Label(win,
                            text=f"Total Runs: {total_runs} | Sequential: {seq_runs} | Parallel: {par_runs}",
                            font=("Segoe UI", 9),
                            fg="#bcdcff",
                            bg=self.neon_bg)
        stats_label.pack(pady=(0, 10))
        win.transient(self.root)
        win.grab_set()

    def export_results_to_csv(self):
        if not self.results:
            messagebox.showwarning("No Data", "No results to export!")
            return
        try:
            from tkinter import filedialog
            import csv
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                title="Save Results as CSV"
            )
            if file_path:
                with open(file_path, 'w', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(["Algorithm", "Mode", "Time (s)", "Threads"])
                    for a, m, t, th in self.results:
                        writer.writerow([a, m, f"{t:.4f}", th])
                messagebox.showinfo("Export Successful", f"Results exported to:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export results: {str(e)}")

    def show_chart_in_window(self):
        if not self.results:
            messagebox.showwarning("No Data", "Run at least one algorithm to chart results.")
            return
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
        except ImportError:
            messagebox.showerror("Matplotlib Required", 
                                "Please install matplotlib to view charts:\n\npip install matplotlib")
            return
        chart_win = tk.Toplevel(self.root)
        chart_win.title("Algorithm Performance Chart")
        center_window(chart_win, 900, 600)
        chart_win.configure(bg=self.neon_bg)
        title_label = tk.Label(
            chart_win,
            text="Algorithm Execution Times (Sequential vs Parallel)",
            font=("Verdana", 16, "bold"),
            fg=self.glow_cyan,
            bg=self.neon_bg
        )
        title_label.pack(pady=(10, 5))
        fig, ax = plt.subplots(figsize=(10, 6), facecolor='#050014')
        df = pd.DataFrame(self.results, columns=["Algorithm", "Mode", "Time", "Threads"])
        algorithms = sorted(df["Algorithm"].unique())
        sequential_color = self.button_purple
        parallel_color = self.button_cyan
        x = range(len(algorithms))
        width = 0.35
        sequential_times = []
        parallel_times = []
        for algo in algorithms:
            seq_data = df[(df["Algorithm"] == algo) & (df["Mode"] == "Sequential")]
            par_data = df[(df["Algorithm"] == algo) & (df["Mode"] == "Parallel")]
            if not seq_data.empty:
                sequential_times.append(seq_data["Time"].mean())
            else:
                sequential_times.append(0)
            if not par_data.empty:
                parallel_times.append(par_data["Time"].mean())
            else:
                parallel_times.append(0)
        bars1 = ax.bar([i - width/2 for i in x], sequential_times, width, 
                      label='Sequential', color=sequential_color, edgecolor='white', linewidth=1)
        bars2 = ax.bar([i + width/2 for i in x], parallel_times, width, 
                      label='Parallel', color=parallel_color, edgecolor='white', linewidth=1)
        ax.set_facecolor("#25222B")
        ax.set_xlabel('Algorithm', fontsize=12, color='white')
        ax.set_ylabel('Time (seconds)', fontsize=12, color='white')
        ax.set_title('Algorithm Performance Comparison', fontsize=14, color=self.glow_cyan, pad=20)
        ax.set_xticks(list(x))
        ax.set_xticklabels(algorithms, rotation=45, ha='right', color='white')
        ax.tick_params(axis='y', colors='white')
        for bar in bars1:
            height = bar.get_height()
            if height > 0:
                ax.text(bar.get_x() + bar.get_width()/2., height + 0.001,
                       f'{height:.4f}s', ha='center', va='bottom', 
                       color='white', fontsize=9, fontweight='bold')
        for bar in bars2:
            height = bar.get_height()
            if height > 0:
                ax.text(bar.get_x() + bar.get_width()/2., height + 0.001,
                       f'{height:.4f}s', ha='center', va='bottom', 
                       color='white', fontsize=9, fontweight='bold')
        ax.legend(facecolor='#050014', edgecolor='white', labelcolor='white', loc='upper right')
        ax.grid(True, alpha=0.2, color='white', linestyle='--')
        plt.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=chart_win)
        canvas.draw()
        canvas.get_tk_widget().pack(expand=True, fill='both', padx=10, pady=10)
        try:
            toolbar = NavigationToolbar2Tk(canvas, chart_win)
            toolbar.update()
            canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        except:
            pass
        close_btn = tk.Button(
            chart_win,
            text="Close Chart",
            font=("Segoe UI", 10, "bold"),
            bg=self.button_purple,
            fg="black",
            bd=0,
            padx=15,
            pady=8,
            command=chart_win.destroy
        )
        close_btn.pack(pady=(0, 10))
        make_neon_button(close_btn, self.button_purple, self.glow_purple)
        note_label = tk.Label(
            chart_win,
            text="Note: Chart shows average execution time for each algorithm.",
            font=("Segoe UI", 9),
            fg="#bcdcff",
            bg=self.neon_bg
        )
        note_label.pack(pady=(0, 5))
        chart_win.transient(self.root)
        chart_win.grab_set()
