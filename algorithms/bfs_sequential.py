import time
from collections import deque
from utils import neighbors

def bfs_sequential(start, goal, n, walls, get_edge_weight,
                   draw_cell, draw_edge, player_update,
                   speed, stop_event, num_threads=None):

    t0 = time.time()

    q = deque([start])
    visited = {start: None}

    while q and not stop_event.is_set():
        curr = q.popleft()

        # slow sequential version
        time.sleep(0.001)

        draw_cell(curr, "#FB9070")

        if curr == goal:
            break

        for nx in neighbors(curr, n):
            if nx in walls: 
                continue
            if nx not in visited:
                visited[nx] = curr
                q.append(nx)

    # reconstruct path
    path = []
    if goal in visited:
        c = goal
        while c:
            path.append(c)
            c = visited[c]
        path.reverse()

    return path, time.time() - t0
