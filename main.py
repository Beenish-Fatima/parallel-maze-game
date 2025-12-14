# main.py
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import tempfile
import webbrowser
import pandas as pd
import plotly.express as px

# Your algorithm modules must exist and return (path, elapsed_seconds)
from algorithms.bfs_sequential import bfs_sequential
from algorithms.bfs_parallel import bfs_parallel
from algorithms.dfs_sequential import dfs_sequential
from algorithms.dfs_parallel import dfs_parallel
from algorithms.dijkstra_sequential import dijkstra_sequential
from algorithms.dijkstra_parallel import dijkstra_parallel
from algorithms.astar_sequential import astar_sequential
from algorithms.astar_parallel import astar_parallel
from utils import generate_weights, in_bounds

# Dynamic cell size
MAX_GRID_SIZE = 20
MIN_CELL_SIZE = 20
MAX_CELL_SIZE = 50

# ---------------------------
# Utility: center a window
# ---------------------------
def center_window(win, width, height):
    win.update_idletasks()
    screen_w = win.winfo_screenwidth()
    screen_h = win.winfo_screenheight()
    x = (screen_w // 2) - (width // 2)
    y = (screen_h // 2) - (height // 2)
    win.geometry(f"{width}x{height}+{x}+{y}")

# ---------------------------
# Neon hover helper
# ---------------------------
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

# ---------------------------
# Main Maze Application (Neon Theme C2)
# ---------------------------
class MazeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Parallel Maze Game — Neon UI")
        center_window(self.root, 1100, 720)

        # app state
        self.n = 12
        self.speed = 0.02
        self.weighted_mode = False
        self.weights = {}
        self.start = (0, 0)
        self.goal = (self.n - 1, self.n - 1)
        self.stop_event = threading.Event()
        self.num_threads = 4
        self.walls = set()
        self.results = []  # (algo, mode, time, threads)
        
        # Dynamic cell size
        self.cell_size = 36  # Initial cell size
        
        # Grid positioning
        self.grid_x_offset = 0
        self.grid_y_offset = 0

        # strong neon colors
        self.neon_bg = "#0b0018"
        self.panel_bg = "#0f0428"
        self.glow_cyan = "#00ffd5"
        self.glow_purple = "#7a4bff"
        self.button_cyan = "#00ffd5"
        self.button_purple = "#9b5bff"
        self.text_light = "#e8f7ff"
        
        # Grid background color (dark theme)
        self.grid_bg = "#1a0b2e"

        self.build_ui()

    def build_ui(self):
        self.root.configure(bg=self.neon_bg)

        # Title bar
        title_frame = tk.Frame(self.root, bg=self.neon_bg)
        title_frame.pack(fill="x", pady=(8, 6))

        title_lbl = tk.Label(
            title_frame,
            text="PARALLEL MAZE GAME",
            font=("Verdana", 26, "bold"),
            fg=self.glow_cyan,
            bg=self.neon_bg
        )
        title_lbl.pack(pady=(4,2))
        subtitle = tk.Label(
            title_frame,
            text="Race algorithms — Sequential vs Parallel",
            font=("Segoe UI", 10),
            fg="#bcdcff",
            bg=self.neon_bg
        )
        subtitle.pack()

        # Topbar buttons
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
                             bg=self.panel_bg, fg=self.text_light, bd=0, padx=10, pady=6,
                             activebackground=self.glow_cyan, command=self.show_results_table)
        view_btn.pack(side="left", padx=(0,8))
        view_btn.config(highlightthickness=2, highlightbackground=self.glow_cyan)
        make_neon_button(view_btn, self.panel_bg, self.glow_cyan)

        chart_btn = tk.Button(topbar, text="Show Chart", font=("Segoe UI", 10, "bold"),
                              bg=self.panel_bg, fg=self.text_light, bd=0, padx=10, pady=6,
                              activebackground=self.glow_purple, command=self.show_chart_in_window)
        chart_btn.pack(side="left", padx=(0,8))
        chart_btn.config(highlightthickness=2, highlightbackground=self.glow_purple)
        make_neon_button(chart_btn, self.panel_bg, self.glow_purple)

        # Main area
        main = tk.Frame(self.root, bg=self.neon_bg)
        main.pack(fill="both", expand=True, padx=14, pady=(6,14))

        # Scrollable left control panel
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

        tk.Label(left_card, text="Maze Type", font=("Segoe UI", 11), fg="#dbeeff", bg=self.panel_bg).pack(anchor="w", padx=12)
        self.maze_type = tk.StringVar(value="simple")
        tk.Radiobutton(left_card, text="Simple", variable=self.maze_type, value="simple",
                       bg=self.panel_bg, fg=self.text_light, selectcolor=self.neon_bg, command=self.update_maze_type).pack(anchor="w", padx=18, pady=(2,0))
        tk.Radiobutton(left_card, text="Weighted", variable=self.maze_type, value="weighted",
                       bg=self.panel_bg, fg=self.text_light, selectcolor=self.neon_bg, command=self.update_maze_type).pack(anchor="w", padx=18, pady=(0,8))

        tk.Label(left_card, text="Grid Size", font=("Segoe UI", 11), fg="#dbeeff", bg=self.panel_bg).pack(anchor="w", padx=12)
        
        self.size_spin = tk.Spinbox(left_card, from_=6, to=MAX_GRID_SIZE, width=6, font=("Segoe UI",10))
        self.size_spin.delete(0,"end"); self.size_spin.insert(0,str(self.n))
        self.size_spin.pack(anchor="w", padx=18, pady=(2,8))

        tk.Label(left_card, text="Threads", font=("Segoe UI", 11), fg="#dbeeff", bg=self.panel_bg).pack(anchor="w", padx=12)
        self.thread_spin = tk.Spinbox(left_card, from_=1, to=12, width=6, font=("Segoe UI",10))
        self.thread_spin.delete(0,"end"); self.thread_spin.insert(0,str(self.num_threads))
        self.thread_spin.pack(anchor="w", padx=18, pady=(2,8))
        
        # Add Speed Slider
        tk.Label(left_card, text="Animation Speed", font=("Segoe UI", 11), fg="#dbeeff", bg=self.panel_bg).pack(anchor="w", padx=12, pady=(10,0))
        speed_frame = tk.Frame(left_card, bg=self.panel_bg)
        speed_frame.pack(anchor="w", padx=18, pady=(2,8))
        self.speed_var = tk.DoubleVar(value=self.speed)
        self.speed_slider = tk.Scale(speed_frame, from_=0.001, to=0.1, resolution=0.001, orient="horizontal",
                                    variable=self.speed_var, length=120, 
                                    bg=self.panel_bg, fg=self.text_light, highlightthickness=0,
                                    command=self.update_speed)
        self.speed_slider.pack()

        tk.Label(left_card, text="Algorithms", font=("Segoe UI", 11), fg="#dbeeff", bg=self.panel_bg).pack(anchor="w", padx=12, pady=(6,4))
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

        # Canvas area - NO scrollbars
        self.canvas_card = tk.Frame(main, bg=self.neon_bg)
        self.canvas_card.pack(side="right", expand=True, fill="both")

        self.canvas_inner = tk.Frame(self.canvas_card, bg=self.grid_bg, bd=2, relief="raised")
        self.canvas_inner.pack(padx=12, pady=12, expand=True, fill="both")
        self.canvas_inner.config(highlightthickness=6, highlightbackground=self.glow_cyan)

        # Create canvas frame
        self.canvas_frame = tk.Frame(self.canvas_inner, bg=self.grid_bg)
        self.canvas_frame.pack(expand=True, fill="both", padx=6, pady=6)
        
        # Create canvas (NO scrollbars)
        self.canvas = tk.Canvas(
            self.canvas_frame, 
            bg=self.grid_bg
        )
        self.canvas.pack(expand=True, fill="both")
        
        # Calculate initial cell size
        self.calculate_cell_size()
        
        # Bind events after everything is created
        self.root.after(100, self.setup_bindings)
        self.root.after(150, self.initial_draw)

    def calculate_cell_size(self):
        """Calculate optimal cell size based on available space"""
        self.canvas_frame.update_idletasks()
        
        # Get available space (account for padding)
        available_width = self.canvas_frame.winfo_width() - 20
        available_height = self.canvas_frame.winfo_height() - 20
        
        if available_width > 0 and available_height > 0:
            # Calculate cell size to fit grid
            width_based = available_width // self.n
            height_based = available_height // self.n
            new_cell_size = min(width_based, height_based, MAX_CELL_SIZE)
            new_cell_size = max(new_cell_size, MIN_CELL_SIZE)
            
            # Update if changed
            if new_cell_size != self.cell_size:
                self.cell_size = new_cell_size
                return True
        return False

    def calculate_grid_position(self):
        """Calculate grid position to center it in the canvas"""
        self.canvas_frame.update_idletasks()
        
        # Get canvas dimensions
        canvas_width = self.canvas_frame.winfo_width()
        canvas_height = self.canvas_frame.winfo_height()
        
        # Calculate grid dimensions
        grid_width = self.n * self.cell_size
        grid_height = self.n * self.cell_size
        
        # Calculate centering offsets
        self.grid_x_offset = (canvas_width - grid_width) // 2
        self.grid_y_offset = (canvas_height - grid_height) // 2
        
        # Ensure offsets are not negative
        self.grid_x_offset = max(0, self.grid_x_offset)
        self.grid_y_offset = max(0, self.grid_y_offset)

    def initial_draw(self):
        """Initial grid drawing after UI is ready"""
        self.draw_grid()

    def setup_bindings(self):
        """Set up event bindings for spinboxes and resize"""
        def update_size(event=None):
            try:
                new_n = int(self.size_spin.get())
                if 6 <= new_n <= MAX_GRID_SIZE and new_n != self.n:
                    self.n = new_n
                    self.goal = (self.n - 1, self.n - 1)
                    if self.weighted_mode:
                        self.weights = generate_weights(self.n)
                    
                    # Remove walls that are out of bounds
                    self.walls = {(i, j) for (i, j) in self.walls if i < self.n and j < self.n}
                    
                    # Recalculate and redraw
                    if self.calculate_cell_size():
                        self.update_canvas_size()
                    else:
                        self.draw_grid()
                    
            except ValueError:
                # Reset to current value if invalid
                self.size_spin.delete(0, "end")
                self.size_spin.insert(0, str(self.n))

        def update_threads(event=None):
            try:
                new_threads = int(self.thread_spin.get())
                if 1 <= new_threads <= 12:
                    self.num_threads = new_threads
            except ValueError:
                # Reset to current value if invalid
                self.thread_spin.delete(0, "end")
                self.thread_spin.insert(0, str(self.num_threads))

        # Bind spinbox events
        self.size_spin.bind("<Return>", update_size)
        self.size_spin.bind("<FocusOut>", update_size)
        self.size_spin.bind("<ButtonRelease-1>", update_size)
        
        self.thread_spin.bind("<Return>", update_threads)
        self.thread_spin.bind("<FocusOut>", update_threads)
        
        # Bind window resize
        self.canvas_frame.bind("<Configure>", self.on_frame_resize)

    def on_frame_resize(self, event=None):
        """Handle frame resize to recalculate cell size"""
        if self.calculate_cell_size():
            self.update_canvas_size()
        else:
            # Even if cell size doesn't change, recalc positioning
            self.calculate_grid_position()
            self.draw_grid()

    def update_canvas_size(self):
        """Update canvas dimensions and redraw"""
        # Configure canvas with new size
        self.canvas.config(
            width=self.n * self.cell_size,
            height=self.n * self.cell_size
        )
        self.calculate_grid_position()
        self.draw_grid()
    
    def update_speed(self, value=None):
        """Update animation speed from slider"""
        self.speed = self.speed_var.get()

    def update_maze_type(self):
        self.weighted_mode = (self.maze_type.get() == "weighted")
        if self.weighted_mode:
            self.weights = generate_weights(self.n)
        else:
            self.weights = {}
        self.draw_grid()

    def draw_grid(self):
        """Draw the complete grid centered"""
        self.canvas.delete("all")
        
        # Recalculate grid position
        self.calculate_grid_position()
        
        # Draw all cells
        for i in range(self.n):
            for j in range(self.n):
                x1 = self.grid_x_offset + j * self.cell_size
                y1 = self.grid_y_offset + i * self.cell_size
                x2 = x1 + self.cell_size
                y2 = y1 + self.cell_size

                fill = "#2a1b3d"  # Dark purple background for empty cells
                if (i, j) == self.start:
                    fill = "#8bc34a"  # Green for start
                elif (i, j) == self.goal:
                    fill = "#e57373"  # Red for goal
                elif (i, j) in self.walls:
                    fill = "#333333"  # Dark gray for walls

                self.canvas.create_rectangle(x1, y1, x2, y2, fill=fill, outline="#3a2b4d")
                
                # Draw weight if in weighted mode
                if self.weighted_mode and (i, j) not in (self.start, self.goal) and (i, j) not in self.walls:
                    w = self.weights.get((i, j), 1)
                    # Dynamic font size based on cell size
                    font_size = max(8, min(14, self.cell_size // 3))
                    self.canvas.create_text(
                        x1 + self.cell_size / 2, 
                        y1 + self.cell_size / 2, 
                        text=str(w), 
                        font=("Arial", font_size, "bold"),
                        fill="#ffffff"
                    )
        
        # Force update
        self.canvas.update_idletasks()

    def draw_cell(self, pos, color):
        """Draw a cell with the given color - used by algorithms"""
        if not in_bounds(pos[0], pos[1], self.n):
            return
            
        x, y = pos
        x1 = self.grid_x_offset + y * self.cell_size
        y1 = self.grid_y_offset + x * self.cell_size  # FIXED: Use grid_y_offset for y-coordinate
        x2 = x1 + self.cell_size
        y2 = y1 + self.cell_size
        
        # Draw the cell
        self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="black")
        
        # Redraw weight if needed
        if self.weighted_mode and (x, y) not in (self.start, self.goal) and (x, y) not in self.walls:
            w = self.weights.get((x, y), 1)
            font_size = max(8, min(14, self.cell_size // 3))
            self.canvas.create_text(
                x1 + self.cell_size / 2, 
                y1 + self.cell_size / 2, 
                text=str(w), 
                font=("Arial", font_size, "bold"),
                fill="#ffffff"
            )
        
        # Update display
        self.canvas.update_idletasks()
        time.sleep(self.speed)

    def highlight_path(self, path):
        """Highlight the final path found by algorithm"""
        for (x, y) in path:
            x1 = self.grid_x_offset + y * self.cell_size
            y1 = self.grid_y_offset + x * self.cell_size  # FIXED: Use grid_y_offset for y-coordinate
            # Draw path cell (bright green)
            self.canvas.create_rectangle(
                x1, y1, 
                x1 + self.cell_size, 
                y1 + self.cell_size, 
                fill="#00e676", 
                outline="black"
            )
        
        # Update display
        self.canvas.update_idletasks()

    def get_edge_weight(self, a, b):
        """Get weight for edge between a and b"""
        return 1 if not self.weighted_mode else self.weights.get(b, 1)

    def stop(self):
        """Stop current algorithm execution"""
        self.stop_event.set()

    def reset_maze(self):
        """Reset maze with new random walls"""
        self.stop_event.set()
        time.sleep(0.05)
        self.stop_event.clear()
        import random
        all_cells = [(i, j) for i in range(self.n) for j in range(self.n) 
                    if (i, j) not in (self.start, self.goal)]
        k = int(len(all_cells) * 0.18)
        self.walls = set(random.sample(all_cells, k))
        if self.weighted_mode:
            self.weights = generate_weights(self.n)
        self.draw_grid()

    def run(self, algo_name, mode, func):
        """Run an algorithm in a separate thread"""
        self.stop_event.clear()
        self.draw_grid()  # Reset grid visualization
        
        def task():
            start_time = time.time()
            
            # Determine thread count based on algorithm mode
            threads_used = 1  # Default for sequential
            
            # Prepare parameters
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
                # Get thread count from spinner for parallel algorithms
                try:
                    threads_used = int(self.thread_spin.get())
                    if threads_used < 1:
                        threads_used = 1
                    params["num_threads"] = threads_used
                except:
                    threads_used = self.num_threads
                    params["num_threads"] = threads_used
            
            # Call the algorithm function
            path, used_time = func(**params)
            elapsed = used_time if used_time else time.time() - start_time
            
            # Store result
            self.results.append((algo_name, mode, elapsed, threads_used))
            
            # Show result
            if path:
                self.highlight_path(path)
                messagebox.showinfo(
                    "Algorithm Complete", 
                    f"{algo_name} ({mode})\nTime: {elapsed:.4f} seconds\nThreads used: {threads_used}\nPath length: {len(path)}"
                )
            else:
                messagebox.showwarning(
                    "No Path Found",
                    f"{algo_name} ({mode})\nTime: {elapsed:.4f} seconds\nThreads used: {threads_used}\nNo path found from start to goal!"
                )

        # Run algorithm in separate thread
        threading.Thread(target=task, daemon=True).start()

    # ---------------- Results table (Treeview) ----------------
    def show_results_table(self):
        if not self.results:
            messagebox.showwarning("No Results", "Run some algorithms first!")
            return
        
        # Create new window with neon theme
        win = tk.Toplevel(self.root)
        win.title("Execution Results")
        center_window(win, 750, 480)
        win.configure(bg=self.neon_bg)
        
        # Title
        title_label = tk.Label(
            win,
            text="Algorithm Execution Results",
            font=("Verdana", 16, "bold"),
            fg=self.glow_cyan,
            bg=self.neon_bg
        )
        title_label.pack(pady=(15, 10))
        
        # Create frame for the table with styling
        table_frame = tk.Frame(win, bg=self.panel_bg, bd=2, relief="raised")
        table_frame.pack(padx=20, pady=10, fill="both", expand=True)
        table_frame.config(highlightthickness=3, highlightbackground=self.glow_purple)
        
        # Create a custom style for the Treeview
        style = ttk.Style()
        style.theme_use("clam")  # Use clam theme for better customization
        
        # Configure Treeview colors
        style.configure("Custom.Treeview",
                        background=self.panel_bg,
                        foreground=self.text_light,
                        fieldbackground=self.panel_bg,
                        borderwidth=0)
        
        style.configure("Custom.Treeview.Heading",
                        background=self.button_purple,
                        foreground="black",
                        font=("Segoe UI", 10, "bold"),
                        relief="flat")
        
        style.map("Custom.Treeview.Heading",
                  background=[('active', self.glow_purple)])
        
        # Configure Treeview row colors
        style.map("Custom.Treeview",
                  background=[('selected', self.glow_cyan)],
                  foreground=[('selected', 'black')])
        
        # Create Treeview with custom style
        cols = ("Algorithm", "Mode", "Time (s)", "Threads")
        tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=15, style="Custom.Treeview")
        
        # Configure scrollbars
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        # Grid layout for tree and scrollbars
        tree.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        vsb.grid(row=0, column=1, sticky="ns", pady=5)
        hsb.grid(row=1, column=0, sticky="ew", padx=5)
        
        # Configure grid weights
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        
        # Configure column widths and headings
        tree.heading("Algorithm", text="Algorithm", anchor="center")
        tree.heading("Mode", text="Mode", anchor="center")
        tree.heading("Time (s)", text="Time (s)", anchor="center")
        tree.heading("Threads", text="Threads", anchor="center")
        
        tree.column("Algorithm", width=180, anchor="center", minwidth=150)
        tree.column("Mode", width=120, anchor="center", minwidth=100)
        tree.column("Time (s)", width=180, anchor="center", minwidth=150)
        tree.column("Threads", width=120, anchor="center", minwidth=100)
        
        # Add data to tree
        for a, m, t, th in self.results:
            tree.insert("", tk.END, values=(a, m, f"{t:.4f}", th))
        
        # Add alternating row colors
        for i, item in enumerate(tree.get_children()):
            if i % 2 == 0:
                tree.tag_configure('evenrow', background='#1a0f30')
                tree.item(item, tags=('evenrow',))
            else:
                tree.tag_configure('oddrow', background=self.panel_bg)
                tree.item(item, tags=('oddrow',))
        
        # Button frame
        btn_frame = tk.Frame(win, bg=self.neon_bg)
        btn_frame.pack(pady=(15, 20))
        
        # Clear Results button
        clear_btn = tk.Button(btn_frame, text="Clear Results", font=("Segoe UI", 10, "bold"),
                             bg=self.button_purple, fg="black", bd=0, padx=15, pady=8,
                             activebackground=self.glow_purple,
                             command=lambda: (self.results.clear(), tree.delete(*tree.get_children())))
        clear_btn.pack(side="left", padx=10)
        clear_btn.config(highlightthickness=2, highlightbackground=self.glow_purple)
        make_neon_button(clear_btn, self.button_purple, self.glow_purple)
        
        # Export to CSV button
        export_btn = tk.Button(btn_frame, text="Export to CSV", font=("Segoe UI", 10, "bold"),
                              bg=self.button_cyan, fg="black", bd=0, padx=15, pady=8,
                              activebackground=self.glow_cyan,
                              command=lambda: self.export_results_to_csv())
        export_btn.pack(side="left", padx=10)
        export_btn.config(highlightthickness=2, highlightbackground=self.glow_cyan)
        make_neon_button(export_btn, self.button_cyan, self.glow_cyan)
        
        # Close button
        close_btn = tk.Button(btn_frame, text="Close", font=("Segoe UI", 10, "bold"),
                             bg=self.panel_bg, fg=self.text_light, bd=0, padx=15, pady=8,
                             activebackground=self.glow_cyan, command=win.destroy)
        close_btn.pack(side="left", padx=10)
        close_btn.config(highlightthickness=2, highlightbackground=self.glow_cyan)
        make_neon_button(close_btn, self.panel_bg, self.glow_cyan)
        
        # Add statistics label
        if self.results:
            total_runs = len(self.results)
            seq_runs = len([r for r in self.results if r[1] == "Sequential"])
            par_runs = len([r for r in self.results if r[1] == "Parallel"])
            
            stats_label = tk.Label(
                win,
                text=f"Total Runs: {total_runs} | Sequential: {seq_runs} | Parallel: {par_runs}",
                font=("Segoe UI", 9),
                fg="#bcdcff",
                bg=self.neon_bg
            )
            stats_label.pack(pady=(0, 10))
        
        # Ensure the window stays on top
        win.transient(self.root)
        win.grab_set()
    
    def export_results_to_csv(self):
        """Export results to CSV file"""
        if not self.results:
            messagebox.showwarning("No Data", "No results to export!")
            return
        
        try:
            from tkinter import filedialog
            import csv
            
            # Ask for save location
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                title="Save Results as CSV"
            )
            
            if file_path:
                with open(file_path, 'w', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    # Write header
                    writer.writerow(["Algorithm", "Mode", "Time (s)", "Threads"])
                    # Write data
                    for a, m, t, th in self.results:
                        writer.writerow([a, m, f"{t:.4f}", th])
                
                messagebox.showinfo("Export Successful", f"Results exported to:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export results: {str(e)}")

    # ---------------- Plotly chart in tkinter window ----------------
    def show_chart_in_window(self):
        """Display the chart in a new tkinter window"""
        if not self.results:
            messagebox.showwarning("No Data", "Run at least one algorithm to chart results.")
            return
        
        try:
            # Import matplotlib here to avoid issues if not installed
            import matplotlib
            matplotlib.use('Agg')  # Use non-interactive backend
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
        except ImportError:
            messagebox.showerror("Matplotlib Required", 
                                "Please install matplotlib to view charts:\n\npip install matplotlib")
            return
        
        # Create new window
        chart_win = tk.Toplevel(self.root)
        chart_win.title("Algorithm Performance Chart")
        center_window(chart_win, 900, 600)
        chart_win.configure(bg=self.neon_bg)
        
        # Title
        title_label = tk.Label(
            chart_win,
            text="Algorithm Execution Times (Sequential vs Parallel)",
            font=("Verdana", 16, "bold"),
            fg=self.glow_cyan,
            bg=self.neon_bg
        )
        title_label.pack(pady=(10, 5))
        
        # Create matplotlib figure
        fig, ax = plt.subplots(figsize=(10, 6), facecolor='#050014')
        
        # Prepare data
        df = pd.DataFrame(self.results, columns=["Algorithm", "Mode", "Time", "Threads"])
        
        # Group data by algorithm and mode
        algorithms = sorted(df["Algorithm"].unique())
        
        # Colors for the bars
        sequential_color = self.button_purple
        parallel_color = self.button_cyan
        
        # Set up bar positions
        x = range(len(algorithms))
        width = 0.35
        
        # Prepare data for bars
        sequential_times = []
        parallel_times = []
        
        for algo in algorithms:
            seq_data = df[(df["Algorithm"] == algo) & (df["Mode"] == "Sequential")]
            par_data = df[(df["Algorithm"] == algo) & (df["Mode"] == "Parallel")]
            
            if not seq_data.empty:
                # Use average of all runs for this algorithm/mode
                sequential_times.append(seq_data["Time"].mean())
            else:
                sequential_times.append(0)
                
            if not par_data.empty:
                # Use average of all runs for this algorithm/mode
                parallel_times.append(par_data["Time"].mean())
            else:
                parallel_times.append(0)
        
        # Create bars
        bars1 = ax.bar([i - width/2 for i in x], sequential_times, width, 
                      label='Sequential', color=sequential_color, edgecolor='white', linewidth=1)
        bars2 = ax.bar([i + width/2 for i in x], parallel_times, width, 
                      label='Parallel', color=parallel_color, edgecolor='white', linewidth=1)
        
        # Customize the plot
        ax.set_facecolor('#050014')
        ax.set_xlabel('Algorithm', fontsize=12, color='white')
        ax.set_ylabel('Time (seconds)', fontsize=12, color='white')
        ax.set_title('Algorithm Performance Comparison', fontsize=14, color=self.glow_cyan, pad=20)
        ax.set_xticks(x)
        ax.set_xticklabels(algorithms, rotation=45, ha='right', color='white')
        ax.tick_params(axis='y', colors='white')
        
        # Add value labels on bars
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
        
        # Add legend
        ax.legend(facecolor='#050014', edgecolor='white', labelcolor='white', loc='upper right')
        
        # Add grid for better readability
        ax.grid(True, alpha=0.2, color='white', linestyle='--')
        
        # Adjust layout
        plt.tight_layout()
        
        # Convert matplotlib figure to tkinter canvas
        canvas = FigureCanvasTkAgg(fig, master=chart_win)
        canvas.draw()
        
        # Pack the canvas
        canvas.get_tk_widget().pack(expand=True, fill='both', padx=10, pady=10)
        
        # Add toolbar for navigation (optional)
        try:
            toolbar = NavigationToolbar2Tk(canvas, chart_win)
            toolbar.update()
            canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        except:
            pass  # Toolbar is optional
        
        # Add close button
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
        
        # Add note about data
        note_label = tk.Label(
            chart_win,
            text="Note: Chart shows average execution time for each algorithm.",
            font=("Segoe UI", 9),
            fg="#bcdcff",
            bg=self.neon_bg
        )
        note_label.pack(pady=(0, 5))
        
        # Ensure the chart window stays on top
        chart_win.transient(self.root)
        chart_win.grab_set()

# ---------------------------
# Start Screen (Neon + Arcade mix, strong glow)
# ---------------------------
class StartScreen:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Welcome — Parallel Maze Game")
        center_window(self.root, 640, 380)
        self.root.configure(bg="#070820")

        self.outline = tk.Label(self.root, text="PARALLEL MAZE GAME",
                                font=("Courier New", 28, "bold"),
                                fg="#ffec00", bg="#070820")
        self.outline.place(relx=0.5, rely=0.26, anchor="center")

        self.shadow = tk.Label(self.root, text="PARALLEL MAZE GAME",
                               font=("Courier New", 28, "bold"),
                               fg="#ff6b6b", bg="#070820")
        self.shadow.place(relx=0.5 + 0.007, rely=0.26 + 0.006, anchor="center")

        self.neon = tk.Label(self.root, text="PARALLEL MAZE GAME",
                             font=("Verdana", 26, "bold"),
                             fg="#00f2ff", bg="#070820")
        self.neon.place(relx=0.5, rely=0.26, anchor="center")

        sub = tk.Label(self.root, text="Let's race the algorithms — Sequential vs Parallel",
                       font=("Segoe UI", 10), fg="#a8bcd8", bg="#070820")
        sub.place(relx=0.5, rely=0.36, anchor="center")

        self.start_btn = tk.Button(self.root, text="LET'S PLAY", font=("Verdana", 18, "bold"),
                                   fg="#00110a", bg="#00ff66", activebackground="#00ff99",
                                   padx=18, pady=8, command=self.launch_main, bd=0)
        self.start_btn.place(relx=0.5, rely=0.62, anchor="center")
        make_neon_button(self.start_btn, "#00ff66", "#00ffaa")

        self.colors = ["#00f2ff", "#7cffb2", "#ff6b6b", "#ffd84f"]
        self.animate()
        self.root.mainloop()

    def animate(self):
        color = self.colors[int(time.time() * 2) % len(self.colors)]
        self.neon.config(fg=color)
        jitter = (int(time.time() * 3) % 3) - 1
        self.neon.place_configure(relx=0.5 + jitter * 0.001)
        self.shadow.config(fg="#ff6b6b" if color != "#ff6b6b" else "#ffaa88")
        self.root.after(120, self.animate)

    def launch_main(self):
        self.root.destroy()
        main_root = tk.Tk()
        MazeApp(main_root)
        main_root.mainloop()

# ---------------------------
# Run
# ---------------------------
if __name__ == "__main__":
    StartScreen()