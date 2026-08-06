# -*- coding: utf-8 -*-
"""测试用Python模块：用户管理系统"""
from typing import List, Optional, Dict
from dataclasses import dataclass


@dataclass
class User:
    name: str
    age: int
    email: str


class UserManager:
    def __init__(self, capacity: int = 100):
        self.capacity = capacity
        self._users: Dict[str, User] = {}

    def add_user(self, user: User) -> bool:
        if len(self._users) >= self.capacity:
            return False
        self._users[user.email] = user
        return True

    def remove_user(self, email: str) -> bool:
        if email in self._users:
            del self._users[email]
            return True
        return False

    def find_user(self, email: str) -> Optional[User]:
        return self._users.get(email)

    def list_users_by_age(self, min_age: int = 0, max_age: int = 150) -> List[User]:
        result = []
        for user in self._users.values():
            if min_age <= user.age <= max_age:
                result.append(user)
        return sorted(result, key=lambda u: u.age)

    def get_user_count(self) -> int:
        return len(self._users)


def create_sample_users() -> List[User]:
    return [
        User(name="Alice", age=25, email="alice@example.com"),
        User(name="Bob", age=30, email="bob@example.com"),
        User(name="Charlie", age=22, email="charlie@example.com"),
    ]


if __name__ == "__main__":
    manager = UserManager(capacity=50)
    for u in create_sample_users():
        manager.add_user(u)
    print(f"Total users: {manager.get_user_count()}")
    young_users = manager.list_users_by_age(max_age=25)
    print(f"Young users: {[u.name for u in young_users]}")
