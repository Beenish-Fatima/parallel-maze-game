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

        time.sleep(0.001)  # slower sequential
        draw_cell(curr, "#FFC107")

        if curr == goal:
            break

        for nx in neighbors(curr, n):
            if nx in walls:
                continue
            if nx not in visited:
                visited[nx] = curr
                stack.append(nx)

    path = []
    if goal in visited:
        c = goal
        while c:
            path.append(c)
            c = visited[c]
        path.reverse()

    return path, time.time() - t0
