from itertools import permutations

def is_isomorphic_bf(G1,G2):
    return BFMatcher(G1,G2).is_isomorphic()

class BFMatcher(object):
    def __init__(self, G1, G2, node_match=None, edge_match=None):
        self.G1 = G1
        self.G2 = G2
        self.G1_nodes = list(G1.nodes())
        self.G2_nodes = list(G2.nodes())
        self.G2_node_order = {n: i for i, n in enumerate(G2)}

        self.node_match = node_match
        self.edge_match = edge_match

    def candidate_pairs_iter(self):
        """生成当前状态下的候选顶点对"""
        G2_nodes = self.G2_nodes
        perm = permutations(self.G1_nodes)
        for G1_nodes in perm:
            yield dict(zip(G1_nodes,G2_nodes)),dict(zip(G2_nodes,G1_nodes))

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
        for mapping in self.match():
            yield mapping

    def match(self):
        for G1_mapping,G2_mapping in self.candidate_pairs_iter():
            if self.syntactic_feasibility(G1_mapping,G2_mapping):
                    self.mapping = G2_mapping
                    yield G2_mapping

    def semantic_feasibility(self, G1_node,G2_node):
        if self.node_match is not None and self.edge_match is not None:
            if not self.node_match(G1_node,G2_node) or not self.edge_match(G1_node,G2_node):
                return False
        elif self.node_match is not None:
            if not self.node_match(G1_node,G2_node):
                return False
        elif self.edge_match is not None:
            if not self.edge_match(G1_node,G2_node):
                return False

        return True

    def syntactic_feasibility(self, G1_mapping, G2_mapping):
        """判断图是否同构"""

        for G1_node in self.G1_nodes:
            G2_node = G1_mapping[G1_node]
            for G1_neighbor in self.G1[G1_node]:
                G2_neighbor = G1_mapping[G1_neighbor]
                if not (G2_neighbor in self.G2[G2_node]):
                    return False
                elif not self.semantic_feasibility(G1_node,G2_node):
                    return False

        for G2_node in self.G2_nodes:
            G1_node = G2_mapping[G2_node]
            for G2_neighbor in self.G2[G2_node]:
                G1_neighbor = G2_mapping[G2_neighbor]
                if not (G1_neighbor in self.G1[G1_node]):
                    return False
                elif not self.semantic_feasibility(G1_node,G2_node):
                    return False
        return True