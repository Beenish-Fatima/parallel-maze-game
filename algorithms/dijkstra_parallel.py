import time, heapq, threading
from utils import neighbors
from queue import PriorityQueue

THREAD_COLORS = [
   "#ff8a65"
]

def dijkstra_parallel(start, goal, n, walls, get_edge_weight,
                      draw_cell, draw_edge, player_update,
                      speed, stop_event, num_threads=4):

    t0 = time.time()
    pq = PriorityQueue()
    pq.put((0, start))
    dist = {start: 0}
    parent = {start: None}
    lock = threading.Lock()

    def worker(tid):
        color = THREAD_COLORS[tid % len(THREAD_COLORS)]
        while not stop_event.is_set():
            try:
                cost, curr = pq.get(timeout=0.1)
            except:
                return

            draw_cell(curr, color)
            time.sleep(speed)
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
                        pq.put((new_cost, nx))
                
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