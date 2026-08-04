"""
测试文件：用于验证代码注释 Agent 的功能
包含多种类型的函数和类，覆盖不同注释场景
"""


def is_prime(n: int) -> bool:
    """判断一个整数是否为素数"""
    if n < 2:
        return False
    for i in range(2, int(n ** 0.5) + 1):
        if n % i == 0:
            return False
    return True


def quick_sort(arr: list) -> list:
    """快速排序算法"""
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quick_sort(left) + middle + quick_sort(right)


def format_currency(amount: float, symbol: str = "￥") -> str:
    """将金额格式化为货币字符串"""
    if amount < 0:
        return f"-{symbol}{abs(amount):,.2f}"
    return f"{symbol}{amount:,.2f}"


class LinkedList:
    """单向链表数据结构"""

    def __init__(self):
        self.head = None
        self.size = 0

    def append(self, value):
        """在链表末尾添加节点"""
        new_node = {"value": value, "next": None}
        if self.head is None:
            self.head = new_node
        else:
            current = self.head
            while current["next"] is not None:
                current = current["next"]
            current["next"] = new_node
        self.size += 1

    def get(self, index: int):
        """获取指定位置的元素"""
        if index < 0 or index >= self.size:
            raise IndexError("链表索引超出范围")
        current = self.head
        for _ in range(index):
            current = current["next"]
        return current["value"]

    def to_list(self) -> list:
        """将链表转换为列表"""
        result = []
        current = self.head
        while current is not None:
            result.append(current["value"])
            current = current["next"]
        return result


def read_config(config_str: str, delimiter: str = "=") -> dict:
    """解析简单的键值对配置字符串"""
    config = {}
    for line in config_str.strip().split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if delimiter not in line:
            raise ValueError(f"配置行格式错误: {line}")
        key, value = line.split(delimiter, 1)
        config[key.strip()] = value.strip()
    return config


def retry(func, max_attempts: int = 3, delay: float = 1.0):
    """装饰器：在函数失败时自动重试"""
    import time

    def wrapper(*args, **kwargs):
        last_error = None
        for attempt in range(max_attempts):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_error = e
                print(f"第 {attempt + 1} 次尝试失败: {e}")
                if attempt < max_attempts - 1:
                    time.sleep(delay)
        raise last_error

    return wrapper


if __name__ == "__main__":
    # 测试素数判断
    print("素数测试:", [n for n in range(20) if is_prime(n)])

    # 测试快速排序
    print("排序测试:", quick_sort([3, 6, 1, 8, 2, 9, 4]))

    # 测试货币格式化
    print(format_currency(1234567.89))
    print(format_currency(-99.5, "$"))

    # 测试链表
    ll = LinkedList()
    ll.append(10)
    ll.append(20)
    ll.append(30)
    print("链表:", ll.to_list(), "第二个元素:", ll.get(1))

    # 测试配置解析
    cfg = read_config("host=127.0.0.1\nport=8080\n# 注释\ndebug=true")
    print("配置:", cfg)
