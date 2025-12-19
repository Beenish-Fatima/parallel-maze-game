# dfs_sequential.py
import time
from utils import neighbors

def dfs_sequential(start, goal, n, walls, get_edge_weight,
                   draw_cell, draw_edge, player_update,
                   speed, stop_event, num_threads=None):

    t0 = time.time()
    stack = [start]
    visited = {start: None}

    while stack and not stop_event.is_set():
        curr = stack.pop()
        draw_cell(curr, "#FFC107")  # visited color

        if curr == goal:
            break

        for nx in neighbors(curr, n):
            if nx not in walls and nx not in visited:
                visited[nx] = curr
                stack.append(nx)
        time.sleep(speed)

    # build path
    path = []
    if goal in visited:
        c = goal
        while c:
            path.append(c)
            c = visited[c]
        path.reverse()

    elapsed = time.time() - t0

    # draw final path (do not include in elapsed time)
    for cell in path:
        draw_cell(cell, "#FFEB3B")

    return path, elapsed
