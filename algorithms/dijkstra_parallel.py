import time, heapq, threading
from utils import neighbors

THREAD_COLORS = [
    "#ffd54f", "#4fc3f7", "#ce93d8", "#80cbc4",
    "#ffab91", "#a5d6a7", "#f48fb1", "#bcaaa4",
    "#9fa8da", "#ffcc80", "#b39ddb", "#ff8a65"
]

def dijkstra_parallel(start, goal, n, walls, get_edge_weight,
                      draw_cell, draw_edge, player_update,
                      speed, stop_event, num_threads=4):

    t0 = time.time()

    lock = threading.Lock()
    pq = [(0, start)]
    dist = {start: 0}
    parent = {start: None}

    active_threads = [True] * num_threads

    def worker(tid):
        color = THREAD_COLORS[tid % len(THREAD_COLORS)]

        while not stop_event.is_set():

            with lock:
                if pq:
                    cost, curr = heapq.heappop(pq)
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
                new_cost = cost + w

                with lock:
                    if nx not in dist or new_cost < dist[nx]:
                        dist[nx] = new_cost
                        parent[nx] = curr
                        heapq.heappush(pq, (new_cost, nx))

    threads = []
    for i in range(num_threads):
        t = threading.Thread(target=worker, args=(i,), daemon=True)
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    # reconstruct path
    path = []
    if goal in parent:
        c = goal
        while c:
            path.append(c)
            c = parent[c]
        path.reverse()

    return path, time.time() - t0
