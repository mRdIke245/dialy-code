"""本地司令模型：理解任务 -> 拆解成运算图 -> 调度多方密态执行 -> 本地合成答案。

当前用表达式解析器做"理解+拆解"（规则驱动）；未来可替换为本地小模型，
只需让它输出同样的运算计划（有向无环图），执行层完全不用改。
"""

import ast
import random
from mpc_core import (P, SCALE, INV_S, encode, decode, share, reconstruct,
                      public_share, add_shares, sub_shares, scale_share,
                      mul_shares, make_triples)


class Commander:
    def __init__(self, n_parties: int = 3, seed: int | None = None):
        self.n = n_parties
        self.rng = random.Random(seed)

    # ---------- 第一层：拆解 ----------
    def _annotate(self, node, secret_names):
        """自底向上标注每个子表达式是否含秘密，并统计需要多少个乘法三元组。"""
        if isinstance(node, ast.Expression):
            return self._annotate(node.body, secret_names)
        if isinstance(node, ast.Constant):
            node._secret = False
            return False
        if isinstance(node, ast.Name):
            node._secret = node.id in secret_names
            return node._secret
        if isinstance(node, ast.UnaryOp):
            node._secret = self._annotate(node.operand, secret_names)
            return node._secret
        if isinstance(node, ast.BinOp):
            ls = self._annotate(node.left, secret_names)
            rs = self._annotate(node.right, secret_names)
            node._secret = ls or rs
            if isinstance(node.op, ast.Mult) and ls and rs:
                self._triple_count += 1
            if isinstance(node.op, ast.Div) and ls and rs:
                raise NotImplementedError("秘密÷秘密 需要比特分解协议，原型暂不支持")
            return node._secret
        raise ValueError(f"不支持的语法: {ast.dump(node)}")

    # ---------- 第二层：调度执行 ----------
    def execute(self, expr: str, secrets: dict):
        """secrets: {变量名: 实数值} —— 只有本地看得见，出场前已被拆成随机份额。"""
        tree = ast.parse(expr, mode='eval')
        self._triple_count = 0
        self._annotate(tree.body, set(secrets.keys()))
        triples = iter(make_triples(self._triple_count, self.n, self.rng))

        # 司令模型把每个秘密拆成 n 份，"API 调用"只携带份额
        env = {k: share(encode(v), self.n, self.rng) for k, v in secrets.items()}
        transcript = [[] for _ in range(self.n)]   # 每个算力方各一份"见闻记录"
        steps = []        # 可读执行计划

        out = self._eval(tree.body, env, triples, steps, transcript)
        answer = decode(reconstruct(out))
        return answer, steps, transcript

    def _log(self, steps, transcript, who, msg, shares=None):
        steps.append(f"{who}: {msg}")
        if shares is not None:
            for pid in range(self.n):
                transcript[pid].append(f"  收到/持有: {shares[pid]}")

    def _eval(self, node, env, triples, steps, transcript):
        if isinstance(node, ast.Expression):
            return self._eval(node.body, env, triples, steps, transcript)

        if isinstance(node, ast.Constant):
            return encode(node.value)

        if isinstance(node, ast.Name):
            if node.id not in env:
                raise NameError(f"未知变量 {node.id}，请放进 secrets 或写成常数")
            self._log(steps, transcript, f"[本地司令]",
                      f"将 {node.id} 拆成 {self.n} 份随机份额分发", env[node.id])
            return env[node.id]

        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            v = self._eval(node.operand, env, triples, steps, transcript)
            return scale_share(v, -1) if isinstance(v, list) else (-v) % P

        if isinstance(node, ast.BinOp):
            l = self._eval(node.left, env, triples, steps, transcript)
            r = self._eval(node.right, env, triples, steps, transcript)
            op = type(node.op).__name__

            # 公开 ⊕ 公开：本地直接算，根本不出网
            if not isinstance(l, list) and not isinstance(r, list):
                if op == 'Add': return (l + r) % P
                if op == 'Sub': return (l - r) % P
                if op == 'Mult': return (l * r * INV_S) % P   # 两个缩放值相乘要除回一个 S
                if op == 'Div':
                    if isinstance(node.right, ast.Constant) and float(node.right.value).is_integer():
                        return (l * pow(int(node.right.value) % P, P - 2, P)) % P
                    raise NotImplementedError("原型只支持除以整数常数")

            # 秘密与公开混合：全部本地完成，零交互
            if op in ('Add', 'Sub'):
                if isinstance(l, list) and not isinstance(r, list):
                    pub = public_share(r if op == 'Add' else (-r) % P, self.n)
                    self._log(steps, transcript, "[算力方]", "份额±常数（本地，无交互）")
                    return add_shares(l, pub)
                if isinstance(r, list) and not isinstance(l, list):
                    pub = public_share(l, self.n)
                    self._log(steps, transcript, "[算力方]", "常数-份额（本地，无交互）")
                    return sub_shares(pub, r) if op == 'Sub' else add_shares(pub, r)
                self._log(steps, transcript, "[算力方]", "份额±份额（本地，无交互）")
                return add_shances_fix(l, r, op)
            if op == 'Mult':
                if isinstance(l, list) and not isinstance(r, list):
                    self._log(steps, transcript, "[算力方]", "份额×常数（本地，无交互）")
                    return scale_share(scale_share(l, r), INV_S)
                if isinstance(r, list) and not isinstance(l, list):
                    self._log(steps, transcript, "[算力方]", "常数×份额（本地，无交互）")
                    return scale_share(scale_share(r, l), INV_S)
                # 秘密 × 秘密：消耗一个三元组，各方广播被掩盖的 d、e
                triple = next(triples)
                d = (reconstruct(l) - reconstruct(triple[0])) % P
                e = (reconstruct(r) - reconstruct(triple[1])) % P
                self._log(steps, transcript, "[算力方×n]",
                          f"秘密×秘密：广播 d={d}, e={e}（被随机数掩盖，泄露为零）")
                for pid in range(self.n):
                    transcript[pid].append(f"  广播 d={d}, e={e}；持有三元组份额 "
                                           f"({triple[0][pid]}, {triple[1][pid]}, {triple[2][pid]})")
                return scale_share(mul_shares(l, r, triple), INV_S)
            if op == 'Div':
                if isinstance(r, list):
                    raise NotImplementedError("秘密÷秘密 需要比特分解协议，原型暂不支持")
                if not float(node.right.value).is_integer():
                    raise NotImplementedError("原型只支持除以整数常数")
                inv = pow(int(node.right.value) % P, P - 2, P)
                self._log(steps, transcript, "[算力方]", "份额÷整数常数（本地，无交互）")
                return scale_share(l, inv)

        raise ValueError(f"不支持的语法: {ast.dump(node)}")


def add_shances_fix(l, r, op):
    return add_shares(l, r) if op == 'Add' else sub_shares(l, r)
