"""本地司令模型 MPC 原型：端到端演示。

运行:  python demo.py
"""

from commander import Commander
from mpc_core import share, P
import random


def banner(t):
    print("\n" + "=" * 64 + f"\n {t}\n" + "=" * 64)


def demo_linear():
    banner("场景 A：税后月均（纯线性 —— 各方全程零交互，只见随机数）")
    expr = "((salary - deduct) * 0.8 - 5000) / 12"
    secrets = {"salary": 38500.0, "deduct": 6000.0}   # 仅本地可见
    print(f"你的提问：{expr}")
    print(f"秘密输入：salary=38500, deduct=6000（司令模型本地持有，从不出网）\n")

    cmd = Commander(n_parties=3, seed=7)
    ans, steps, _ = cmd.execute(expr, secrets)
    for s in steps:
        print("  " + s)
    print(f"\n本地合成答案：{ans:.2f} 元/月")
    print(f"明文凭条核对：{((38500 - 6000) * 0.8 - 5000) / 12:.2f} 元/月  ✓")


def demo_mul():
    banner("场景 B：秘密单价 × 秘密数量（真正的一次密态乘法）")
    expr = "unit_price * quantity * 1.13 + 200"
    secrets = {"unit_price": 13.5, "quantity": 2400.0}
    print(f"你的提问：{expr}")
    print(f"秘密输入：unit_price=13.5, quantity=2400\n")

    cmd = Commander(n_parties=3, seed=42)
    ans, steps, transcript = cmd.execute(expr, secrets)
    for s in steps:
        print("  " + s)
    print(f"\n本地合成答案：{ans:.2f}")
    print(f"明文凭条核对：{13.5 * 2400 * 1.13 + 200:.2f}  ✓")

    print("\n--- 算力方 0 号的全部见闻（它真的什么都不知道）---")
    for line in transcript[0]:
        print(line)


def demo_privacy():
    banner("隐私性验证：同一秘密，两次拆份，某一方看到的份额毫不相关")
    secret = 38500
    rng1, rng2 = random.Random(1), random.Random(2)
    s1 = share(secret, 3, rng1)
    s2 = share(secret, 3, rng2)
    print(f"秘密 salary = {secret}")
    print(f"第 1 次拆份，0 号方拿到: {s1[0]}")
    print(f"第 2 次拆份，0 号方拿到: {s2[0]}")
    print("两次毫不相关 —— 且每个份额都均匀分布于 0 ~ 2^61 的域上，")
    print("对单方而言，拿到 38500 和拿到 0 的概率完全一样（信息论安全）。")


if __name__ == "__main__":
    demo_linear()
    demo_mul()
    demo_privacy()
