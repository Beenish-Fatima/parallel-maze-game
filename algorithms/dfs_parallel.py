import threading, time
from queue import LifoQueue
from utils import neighbors

def dfs_worker(stack, visited, walls, n, draw_cell, stop_event):
    while not stack.empty() and not stop_event.is_set():
        curr = stack.get()

        draw_cell(curr, "#FFEB3B")

        for nx in neighbors(curr, n):
            if nx in walls:
                continue
            if nx not in visited:
                visited[nx] = curr
                stack.put(nx)

        stack.task_done()

def dfs_parallel(start, goal, n, walls, get_edge_weight,
                 draw_cell, draw_edge, player_update,
                 speed, stop_event, num_threads=4):

    t0 = time.time()

    stack = LifoQueue()
    stack.put(start)
    visited = {start: None}

    threads = []
    for _ in range(num_threads):
        th = threading.Thread(target=dfs_worker, args=(stack, visited, walls, n, draw_cell, stop_event))
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
