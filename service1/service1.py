import time

x = 0

for i in range(100000):
    time.sleep(1)
    for j in range (10000):
        x += i