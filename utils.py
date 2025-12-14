import random
def neighbors(pos, n):
    x, y = pos
    for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
        nx, ny = x+dx, y+dy
        if 0<=nx<n and 0<=ny<n:
            yield (nx, ny)
def generate_weights(n):
    weights = {}
    for i in range(n):
        for j in range(n):
            if random.random() < 0.2:
                weights[(i,j)] = random.randint(1,9)
    return weights

def in_bounds(x,y,n):
    return 0<=x<n and 0<=y<n

def heavy_work():
    x = 1.0
    for _ in range(50000):  # increase number for even slower sequential
        x = x * 1.0000001
    return x
