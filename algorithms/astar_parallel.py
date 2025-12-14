import time, heapq, threading, math
from utils import neighbors

THREAD_COLORS = [
    "#ffd54f", "#4fc3f7", "#ce93d8", "#80cbc4",
    "#ffab91", "#a5d6a7", "#f48fb1", "#bcaaa4",
    "#9fa8da", "#ffcc80", "#b39ddb", "#ff8a65"
]

def heuristic(a, b):
    return math.sqrt((a[0]-b[0])**2 + (a[1]-b[1])**2)

def astar_parallel(start, goal, n, walls, get_edge_weight,
                   draw_cell, draw_edge, player_update,
                   speed, stop_event, num_threads=4):

    t0 = time.time()

    lock = threading.Lock()
    pq = [(0, start)]
    g = {start: 0}
    parent = {start: None}

    active_threads = [True] * num_threads

    def worker(tid):
        color = THREAD_COLORS[tid % len(THREAD_COLORS)]

        while not stop_event.is_set():

            with lock:
                if pq:
                    f, curr = heapq.heappop(pq)
                else:
                    active_threads[tid] = False
                    return

            draw_cell(curr, color)

            if curr == goal:
                stop_event.set()
                return

            for nx in neighbors(curr, n):
                if nx in walls:
                    continue

                w = get_edge_weight(curr, nx)
                new_g = g[curr] + w
                f_new = new_g + heuristic(nx, goal)

                with lock:
                    if nx not in g or new_g < g[nx]:
                        g[nx] = new_g
                        parent[nx] = curr
                        heapq.heappush(pq, (f_new, nx))

    threads = []
    for i in range(num_threads):
        t = threading.Thread(target=worker, args=(i,), daemon=True)
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    # Reconstruct path
    path = []
    if goal in parent:
        c = goal
        while c:
            path.append(c)
            c = parent[c]
        path.reverse()

    return path, time.time() - t0
