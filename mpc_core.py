"""MPC 核心引擎：素数有限域上的加法秘密分享。

安全性说明（诚实但好奇模型，各方不串通）：
- 任何 n-1 个份额联合分布与秘密无关（信息论安全）
- 乘法通过 Beaver 三元组完成，交互中公开的 d、e 均被随机数掩盖
- 本原型中三元组由"可信第三方"模拟生成；生产环境应改用 OT 等协议离线生成
"""

import random

# 2^61 - 1，梅森素数，64位机器上溢出前可乘两个缩放值
P = 2**61 - 1
SCALE = 10**6                      # 定点小数缩放因子
INV_S = pow(SCALE, P - 2, P)       # SCALE 的模逆，用于公开乘法后的重缩放


def encode(x: float) -> int:
    """实数 -> 域元素（乘以 SCALE 取模）。"""
    return int(round(x * SCALE)) % P


def decode(f: int) -> float:
    """域元素 -> 实数（取中心代表元，除回 SCALE）。"""
    v = f if f <= P // 2 else f - P
    return v / SCALE


def share(secret: int, n: int, rng: random.Random) -> list:
    """加法分享：n 个份额之和 ≡ secret (mod P)，前 n-1 个为均匀随机。"""
    parts = [rng.randrange(P) for _ in range(n - 1)]
    parts.append((secret - sum(parts)) % P)
    return parts


def reconstruct(shares: list) -> int:
    return sum(shares) % P


def public_share(v: int, n: int) -> list:
    """公开值的分享表示：第 0 方持有 v，其余为 0。"""
    return [v % P] + [0] * (n - 1)


# ---- 本地运算（各方无需交互）----
def add_shares(x: list, y: list) -> list:
    return [(a + b) % P for a, b in zip(x, y)]


def sub_shares(x: list, y: list) -> list:
    return [(a - b) % P for a, b in zip(x, y)]


def scale_share(x: list, k: int) -> list:
    return [(k * a) % P for a in x]


# ---- 乘法：消耗一个 Beaver 三元组 (a, b, c=a*b) ----
def mul_shares(x: list, y: list, triple) -> list:
    """秘密 x 秘密。公开 d = x-a, e = y-b（均被随机数 a、b 掩盖，泄露为零），
    则 xy = de + db + ea + ab，各方本地组合自己那份。"""
    a, b, c = triple
    n = len(x)
    d = (reconstruct(x) - reconstruct(a)) % P
    e = (reconstruct(y) - reconstruct(b)) % P
    z = [(c[i] + d * b[i] + e * a[i]) % P for i in range(n)]
    z[0] = (z[0] + d * e) % P
    return z


def make_triples(count: int, n: int, rng: random.Random) -> list:
    """模拟离线阶段的三元组分发（生产环境：OT/同态加密生成，不依赖可信第三方）。"""
    triples = []
    for _ in range(count):
        a, b = rng.randrange(P), rng.randrange(P)
        c = a * b % P
        triples.append((share(a, n, rng), share(b, n, rng), share(c, n, rng)))
    return triples
