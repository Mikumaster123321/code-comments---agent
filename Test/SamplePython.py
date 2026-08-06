import os
from typing import List, Optional


class TaskManager:
    """任务管理器：管理待办任务的增删改查"""

    def __init__(self, name):
        self.name = name
        self.tasks = []
        self.completed = 0

    def add_task(self, title, priority=0):
        if not title:
            raise ValueError("任务标题不能为空")
        task = {
            "id": len(self.tasks) + 1,
            "title": title,
            "priority": priority,
            "done": False,
        }
        self.tasks.append(task)
        return task["id"]

    def complete_task(self, task_id):
        for task in self.tasks:
            if task["id"] == task_id:
                if task["done"]:
                    return False
                task["done"] = True
                self.completed += 1
                return True
        return False

    def get_pending_tasks(self):
        return [t for t in self.tasks if not t["done"]]

    def get_summary(self):
        total = len(self.tasks)
        pending = total - self.completed
        return f"[{self.name}] 总计 {total} 项，已完成 {self.completed} 项，待办 {pending} 项"


def merge_sorted_lists(left, right):
    result = []
    i = j = 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    result.extend(left[i:])
    result.extend(right[j:])
    return result


def quick_sort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quick_sort(left) + middle + quick_sort(right)


def read_file_lines(path, encoding="utf-8"):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding=encoding) as f:
        return [line.rstrip("\n") for line in f]


def fibonacci(n):
    if n < 0:
        raise ValueError("n 不能为负数")
    if n <= 1:
        return n
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b
