import time, heapq, math
from utils import neighbors
from utils import heavy_work

def heuristic(a, b):
    # Euclidean distance
    return math.sqrt((a[0]-b[0])**2 + (a[1]-b[1])**2)

def astar_sequential(start, goal, n, walls, get_edge_weight,
                     draw_cell, draw_edge, player_update,
                     speed, stop_event, num_threads=None):

    t0 = time.time()

    pq = [(0, start)]
    g = {start: 0}
    parent = {start: None}

    while pq and not stop_event.is_set():
        f, curr = heapq.heappop(pq)

        heavy_work()  # 🔥 guarantee slow sequential runtime

        draw_cell(curr, "#F5B7B1")

        if curr == goal:
            break

        for nx in neighbors(curr, n):
            if nx in walls:
                continue

            w = get_edge_weight(curr, nx)
            new_g = g[curr] + w

            if nx not in g or new_g < g[nx]:
                g[nx] = new_g
                parent[nx] = curr
                f_new = new_g + heuristic(nx, goal)
                heapq.heappush(pq, (f_new, nx))

    # path reconstruction
    path = []
    if goal in parent:
        c = goal
        while c:
            path.append(c)
            c = parent[c]
        path.reverse()

    return path, time.time() - t0
