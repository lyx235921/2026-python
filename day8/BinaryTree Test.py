class Node:
    def __init__(self, elem=-1, lchild=None, rchild=None):
        self.elem = elem
        self.lchild = lchild
        self.rchild = rchild


class BinaryTree:

    def __init__(self):
        self.root = None
        self.help_queue = []

    def level_build_tree(self, node: Node):
        if self.root is None:
            self.root = node
            self.help_queue.append(node)
        else:
            self.help_queue.append(node)
            if self.help_queue[0].lchild is None:
                self.help_queue[0].lchild = node
            else:
                self.help_queue[0].rchild = node
                self.help_queue.pop(0)

    def pre_order(self, current_node: Node):
        if current_node:
            print(current_node.elem, end=' ')
            self.pre_order(current_node.lchild)
            self.pre_order(current_node.rchild)


if __name__ == "__main__":
    tree = BinaryTree()
    for i in range(1, 21):
        new_node = Node(i)
        tree.level_build_tree(new_node)
    tree.pre_order(tree.root)
