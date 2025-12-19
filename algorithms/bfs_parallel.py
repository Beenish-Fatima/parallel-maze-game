import time, threading
from queue import Queue
from utils import neighbors

def worker(q, visited, walls, n, draw_cell, stop_event):
    while not q.empty() and not stop_event.is_set():
        curr = q.get()

        draw_cell(curr, "#FB9070")

        for nx in neighbors(curr, n):
            if nx in walls:
                continue
            if nx not in visited:
                visited[nx] = curr
                q.put(nx)

        q.task_done()

def bfs_parallel(start, goal, n, walls, get_edge_weight,
                 draw_cell, draw_edge, player_update,
                 speed, stop_event, num_threads=4):

    t0 = time.time()

    q = Queue()
    q.put(start)
    visited = {start: None}

    threads = []
    for _ in range(num_threads):
        th = threading.Thread(target=worker, args=(q, visited, walls, n, draw_cell, stop_event))
        th.daemon = True
        th.start()
        threads.append(th)

    for th in threads:
        th.join()

    path = []
    if goal in visited:
        c = goal
        while c:
            path.append(c)
            c = visited[c]
        path.reverse()

    return path, time.time() - t0
