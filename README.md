Maze Pathfinder Project (Python Tkinter)
---------------------------------------
Structure:
  - main.py           : Tkinter UI and runner
  - utils.py          : helper functions
  - algorithms/       : algorithm implementations (seq + parallel)

Run:
  python3 main.py

Notes:
  - Parallel implementations use Python threads (GIL may limit CPU scaling)
  - Visualization is simple: algorithms call draw_cell(pos, color) to show exploration.
