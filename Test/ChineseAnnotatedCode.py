# -*- coding: utf-8 -*-
"""
数学运算工具模块
本模块提供常用的数学计算工具函数，包括加减乘除、幂运算、斐波那契数列等。
"""


class MathCalculator:
    """
    数学计算器类
    封装了常用的数学运算方法，支持历史记录查看。
    """

    def __init__(self):
        """
        初始化计算器，创建空的历史记录。
        """
        self.history = []  # 存储每次计算的历史记录

    def add(self, a, b):
        """
        计算两个数的和。

        Args:
            a: 第一个加数
            b: 第二个加数

        Returns:
            两个数的和
        """
        result = a + b
        self.history.append(f"{a} + {b} = {result}")
        return result

    def multiply(self, x, y):
        """
        计算两个数的乘积。

        Args:
            x: 第一个乘数
            y: 第二个乘数

        Returns:
            两数的乘积
        """
        result = x * y
        self.history.append(f"{x} * {y} = {result}")
        return result

    def get_history(self):
        """
        获取所有历史计算记录。

        Returns:
            list: 包含历史记录字符串的列表
        """
        return self.history  # 返回深拷贝防止外部修改


def power(base, exp):
    """
    计算基数的指数次幂。

    Args:
        base: 底数
        exp: 指数，可以是负数或零

    Returns:
        计算结果的浮点数
    """
    return base ** exp  # 使用Python内置幂运算


def fibonacci(n):
    """
    生成斐波那契数列的前n项。

    Args:
        n: 需要生成的项数，必须为正整数

    Returns:
        list: 斐波那契数列列表

    Raises:
        ValueError: 当n小于等于0时抛出异常
    """
    if n <= 0:
        raise ValueError("项数必须为正整数")
    # 初始化数列前两项
    seq = [0, 1]
    for i in range(2, n):
        seq.append(seq[i - 1] + seq[i - 2])  # 每项等于前两项之和
    return seq[:n]
