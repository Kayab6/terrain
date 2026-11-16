import heapq
from collections import deque


class HashMap(dict):
    pass


class HashSet(set):
    pass


class Queue(deque):
    def enqueue(self, item):
        self.append(item)

    def dequeue(self):
        if not self:
            raise IndexError("queue is empty")
        return self.popleft()


class Stack(list):
    def push(self, item):
        self.append(item)

    def pop(self):
        if not self:
            raise IndexError("stack is empty")
        return super().pop()


class MinHeap:
    def __init__(self):
        self._items = []

    def push(self, priority, item):
        heapq.heappush(self._items, (priority, item))

    def pop(self):
        if not self._items:
            raise IndexError("heap is empty")
        return heapq.heappop(self._items)

    def __bool__(self):
        return bool(self._items)

    def __len__(self):
        return len(self._items)
