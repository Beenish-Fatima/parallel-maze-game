import threading, time
from queue import LifoQueue
from utils import neighbors

def dfs_worker(stack, visited, walls, n, draw_cell, stop_event, lock, visited_order, speed_per_thread, goal):
    while not stack.empty() and not stop_event.is_set():
        try:
            curr = stack.get(timeout=0.05)
        except:
            break

        if curr == goal:
            stop_event.set()
            stack.task_done()
            return

        for nx in neighbors(curr, n):
            if nx in walls:
                continue
            with lock:
                if nx not in visited:
                    visited[nx] = curr  # store parent for path
                    visited_order.append(nx)
                    stack.put(nx)

        # Draw the cell (simulate traversal)
        draw_cell(curr, "#A48CE8")
        time.sleep(speed_per_thread)
        stack.task_done()


def dfs_parallel(start, goal, n, walls, get_edge_weight,
                 draw_cell, draw_edge, player_update,
                 speed, stop_event, num_threads=4):

    t0 = time.time()
    stack = LifoQueue()
    stack.put(start)
    visited = {start: None}
    visited_order = [start]
    lock = threading.Lock()

    # Animation speed: ensure minimum reasonable delay
    # Make animation slower: minimum 0.12 seconds per step, or user speed / threads
    speed_per_thread = max(0.10, speed / max(1, num_threads))

    threads = []
    for _ in range(num_threads):
        th = threading.Thread(target=dfs_worker,
                              args=(stack, visited, walls, n, draw_cell, stop_event, lock, visited_order, speed_per_thread, goal))
        th.daemon = True
        th.start()
        threads.append(th)

    for th in threads:
        th.join()

    # Build path
    path = []
    if goal in visited:
        c = goal
        while c is not None:
            path.append(c)
            c = visited[c]
        path.reverse()

    return path, time.time() - t0
