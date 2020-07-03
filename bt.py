import sys

def is_isomorphic_bt(G1,G2):
    return BTMatcher(G1,G2).is_isomorphic()

class BTMatcher(object):
    def __init__(self, G1, G2, node_match=None, edge_match=None):
        self.G1 = G1
        self.G2 = G2
        self.G1_nodes = set(G1.nodes())
        self.G2_nodes = set(G2.nodes())
        self.G2_node_order = {n: i for i, n in enumerate(G2)}

        # 标签匹配成员
        self.node_match = node_match
        self.edge_match = edge_match
        self.G1_adj = self.G1.adj
        self.G1_adj_set = {k:set(v) for k,v in self.G1.adj.items()}
        self.G2_adj = self.G2.adj
        self.G2_adj_set = {k:set(v) for k,v in self.G2.adj.items()}

        # 设置最大递归深度
        self.old_recursion_limit = sys.getrecursionlimit()
        expected_max_recursion_level = len(self.G2)
        if self.old_recursion_limit < 1.5 * expected_max_recursion_level:
            sys.setrecursionlimit(int(1.5 * expected_max_recursion_level))

        # 初始化状态
        self.initialize()

    def reset_recursion_limit(self):
        sys.setrecursionlimit(self.old_recursion_limit)

    def candidate_pairs_iter(self):
        """生成当前状态下的候选顶点对"""
        G1_nodes = self.G1_nodes
        G2_nodes = self.G2_nodes
        min_key = self.G2_node_order.__getitem__

        # 取不在子图中的其他结点
        T1_inout = [node for node in G1_nodes if node not in self.core_1]
        T2_inout = [node for node in G2_nodes if node not in self.core_2]
        
        # 组成结点对
        if T1_inout and T2_inout:
            node_2 = min(T2_inout, key=min_key)
            for node_1 in T1_inout:
                yield node_1, node_2

    def initialize(self):
        """初始化类状态"""
        self.core_1 = {}
        self.core_2 = {}
        self.state = BTState(self)

        # 保存当前子图映射副本
        self.mapping = self.core_1.copy()

    def is_isomorphic(self):
        """判断G1和G2是否同构"""
        # 检查顶点数
        if self.G1.order() != self.G2.order():
            return False

        # 检查度数序列
        d1 = sorted(d for n, d in self.G1.degree())
        d2 = sorted(d for n, d in self.G2.degree())
        if d1 != d2:
            return False

        # 迭代匹配
        try:
            x = next(self.isomorphisms_iter())
            return True
        except StopIteration:
            return False

    def isomorphisms_iter(self):
        """递归入口"""
        self.initialize()
        for mapping in self.match():
            yield mapping

    def match(self):
        if len(self.core_1) == len(self.G2):
            # 同构，拷贝同构映射并返回
            self.mapping = self.core_1.copy()
            yield self.mapping
        else:
            # 遍历候选顶点对
            for G1_node, G2_node in self.candidate_pairs_iter():
                # 结构
                if self.syntactic_feasibility(G1_node, G2_node):
                    if self.semantic_feasibility(G1_node, G2_node):
                        # 更新状态
                        newstate = self.state.__class__(self, G1_node, G2_node)
                        for mapping in self.match():
                            yield mapping
                        # 恢复状态
                        newstate.restore()

    def semantic_feasibility(self, G1_node, G2_node):
        # 顶点匹配
        if self.node_match is not None:
            nm = self.node_match(self.G1.nodes[G1_node], self.G2.nodes[G2_node])
            if not nm:
                return False

        # 边匹配
        if self.edge_match is not None:
            G1_adj = self.G1_adj
            G2_adj = self.G2_adj
            core_1 = self.core_1
            edge_match = self.edge_match

            for neighbor in G1_adj[G1_node]:
                # 自反检查
                if neighbor == G1_node:
                    if not edge_match(G1_adj[G1_node][G1_node],
                                    G2_adj[G2_node][G2_node]):
                        return False
                # 子图内邻接边检查
                elif neighbor in core_1:
                    if not edge_match(G1_adj[G1_node][neighbor],
                                    G2_adj[G2_node][core_1[neighbor]]):
                        return False

        return True

    def syntactic_feasibility(self, G1_node, G2_node):
        """判断加入后的子图是否同构"""
        # 自环检查
        if self.G1.number_of_edges(G1_node, G1_node) != self.G2.number_of_edges(G2_node, G2_node):
                return False

        # 映射内部连接检查
        for neighbor in self.G1[G1_node]:
            if neighbor in self.core_1:
                if not (self.core_1[neighbor] in self.G2[G2_node]):
                    return False
                elif self.G1.number_of_edges(neighbor, G1_node) != self.G2.number_of_edges(self.core_1[neighbor], G2_node):
                    return False

        # 反向映射内部连接检查
        for neighbor in self.G2[G2_node]:
            if neighbor in self.core_2:
                if not (self.core_2[neighbor] in self.G1[G1_node]):
                    return False
                else:
                    if self.G1.number_of_edges(self.core_2[neighbor], G1_node) != self.G2.number_of_edges(neighbor, G2_node):
                        return False

        # R_new, 外部剩余数检查
        num1 = 0
        for neighbor in self.G1[G1_node]:
            if neighbor not in self.core_1:
                num1 += 1
        num2 = 0
        for neighbor in self.G2[G2_node]:
            if neighbor not in self.core_2:
                num2 += 1
        if not (num1 == num2):
                return False

        return True


class BTState(object):
    def __init__(self, GM, G1_node=None, G2_node=None):
        self.GM = GM

        self.G1_node = None
        self.G2_node = None
        self.depth = len(GM.core_1)

        if G1_node is None or G2_node is None:
            # 初始状态
            GM.core_1 = {}
            GM.core_2 = {}

        # 更新状态
        if G1_node is not None and G2_node is not None:
            # 添加映射
            GM.core_1[G1_node] = G2_node
            GM.core_2[G2_node] = G1_node

            # 记录添加结点
            self.G1_node = G1_node
            self.G2_node = G2_node

            # 保存递归深度
            self.depth = len(GM.core_1)

    def restore(self):
        """恢复状态"""
        # 删除本地递归加入的映射
        if self.G1_node is not None and self.G2_node is not None:
            del self.GM.core_1[self.G1_node]
            del self.GM.core_2[self.G2_node]