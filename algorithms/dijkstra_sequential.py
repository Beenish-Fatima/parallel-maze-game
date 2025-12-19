import time, heapq
from utils import neighbors
from utils import heavy_work

def dijkstra_sequential(start, goal, n, walls, get_edge_weight,
                        draw_cell, draw_edge, player_update,
                        speed, stop_event, num_threads=None):

    t0 = time.time()

    pq = [(0, start)]
    dist = {start: 0}
    parent = {start: None}

    while pq and not stop_event.is_set():
        cost, curr = heapq.heappop(pq)

        heavy_work()  # 🔥 guarantees slow sequential execution

        draw_cell(curr, "#92F1CE")

        if curr == goal:
            break

        for nx in neighbors(curr, n):
            if nx in walls:
                continue

            w = get_edge_weight(curr, nx)
            new_cost = cost + w

            if nx not in dist or new_cost < dist[nx]:
                dist[nx] = new_cost
                parent[nx] = curr
                heapq.heappush(pq, (new_cost, nx))

    path = []
    if goal in parent:
        c = goal
        while c:
            path.append(c)
            c = parent[c]
        path.reverse()

    return path, time.time() - t0
