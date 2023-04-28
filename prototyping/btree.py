from typing import Any, Optional
from dataclasses import dataclass


@dataclass
class Entry:
    key: Any
    value: Any


def _swap(arr: list, i1: int, i2: int):
    tmp = arr[i2]
    arr[i2] = arr[i1]
    arr[i1] = tmp


def _shift_insert(arr: list, index: int, value: Any) -> Any:

    idx = arr_len = len(arr)
    arr.append(None)

    while idx > index:
        _swap(arr, idx-1, idx)
        idx -= 1

    arr[index] = value
    # if the last value is None we can remove the shift None to keep the
    # node the correct length. If not we dont want to pop it off since we
    # need the value for the split
    if arr[-1] is None:
        arr.pop()


class Node:
    def __init__(
        self,
        b: int,
        entries: list[Entry],
        edges: list["Node"]
    ):
        assert len(entries) <= b

        if edges:
            assert len(edges) == len(entries) + 1

        null_space = [None for _ in range(b - len(entries))]
        self.entries = entries + null_space
        self.edges = edges + null_space
        self.b = b
        self._is_leaf = not any(map(bool, self.edges))

    def search(self, key: Any) -> tuple[bool, int]:
        idx = -1
        found = False
        for i, entry in enumerate(self.entries):
            if entry is None:
                break

            if key < entry.key:
                continue
            elif key == entry.key:
                found = True
                idx = i
                return found, idx
            elif key > entry.key:
                idx = i
                return found, idx

        idx = len(self.entries)
        return found, idx

    def split(self) -> tuple["Node", "Node"]:
        mid = len(self.entries) // 2 + 1

        filtered_entries = [
            entry for entry in self.entries if entry is not None
        ]
        filtered_edges = [edge for edge in self.edges if edge is not None]

        left_entries, right_entries = (
            filtered_entries[:mid], filtered_entries[mid:]
        )
        left_edges, right_edges = filtered_edges[:mid], filtered_edges[mid:]

        return (
            Node(self.b, left_entries, left_edges),
            Node(self.b, right_entries, right_edges),
        )

    def insert(self, entry: Entry) -> Optional[tuple["Node", "Node"]]:
        found, insert_index = self.search(entry.key)

        if found:
            self.entries[insert_index] = entry
            return None

        if not self.is_leaf():
            node = self.edges[insert_index]
            assert node is not None
            new_nodes = node.insert(entry)

            if new_nodes is None:
                return None

            left_node, right_node = new_nodes
            entry = left_node.take_last_non_null_entry()

            self.edges[insert_index] = left_node
            _shift_insert(self.edges, insert_index + 1, right_node)

        _shift_insert(self.entries, insert_index, entry)
        if self.is_full():
            return self.split()

        return None

    def is_full(self) -> bool:
        return self.b == len(self.entries)

    def is_leaf(self) -> bool:
        return self._is_leaf

    def take_last_non_null_entry(self) -> Entry:
        last_non_null_index = 0
        while self.entries[last_non_null_index + 1] is not None:
            last_non_null_index += 1

        taken = self.entries[last_non_null_index]
        self.entries[last_non_null_index] = None

        return taken

    def get_node_by_index(self, idx: int) -> "Node":
        return self.edges[idx]

    def get_entry_by_index(self, idx: int) -> Entry:
        return self.entries[idx]


class BTree:

    def __init__(self, root: Node, b: int):
        self.root = root
        self.b = b

    def find(self, key: Any) -> Optional[Any]:
        found = False
        node = self.root

        while True:
            found, idx = node.search(key)
            if found:
                return node.get_entry_by_index(idx).value

            if idx == -1:
                return None

            node = node.get_node_by_index(idx)

    def add(self, key: Any, value: Any):
        entry =  Entry(key, value)
        split = self.root.insert(entry)

        if split:
            left_node, right_node = split
            entry = left_node.take_last_non_null_entry()
            new_root = Node(
                b=self.b,
                entries=[entry],
                edges=[left_node, right_node]
            )

            self.root = new_root
    
    def height(self):
        height = 1
        node = self.root
        while node.edges:
            height += 1
            node = node.edges[0]

        return height

    def print_tree(self, nodes=None):
        height = self.height()
        if nodes is None:
            nodes = [[self.root]]


        max_leaves = (self.b)**(height-1)
        node_witdh = self.b * 4
        paren_padding = (height-1 * self.b + 1 *3)

        leaf_width = (max_leaves * node_witdh) + paren_padding

        formatted_nodes = []
        for node_list in nodes:
            formatted_node_list = []
            for node in node_list:
                if not node:
                    continue
                fmted = [
                    f'{entry.key:02}' if entry else 'xx'
                    for entry in node.entries
                ]
                fmt_string = f'{fmted}'
                formatted_node_list.append(fmt_string)
            formatted_node = f'({"-".join(formatted_node_list)})'
            formatted_nodes.append(formatted_node)

        layer = ' '.join(formatted_nodes)
        padding = (leaf_width - len(layer)) + 1

        print(padding*' '+layer+padding*' ')
        print()
        print()

        new_nodes = []
        for node_list in nodes:
            for node in node_list:
                if not node:
                    continue
                new_node_list = [n for n in node.edges]
                new_nodes.append(new_node_list)

        if any(new_nodes):
            self.print_tree(new_nodes)


def build_tree(arr: list, b: int) -> BTree:
    root = Node(b, [], [])
    tree = BTree(root, b)

    for item in arr:
        tree.add(item.key, item.value)
        tree.print_tree()

    return tree


if __name__ == '__main__':
    # tree = build_tree(arr, 3)


    # tests
    def test_swap():
        l = [1, 2, 3]
        _swap(l, 2, 0)

        try:
            assert l == [3, 2, 1]
        except AssertionError:
            print(l)
            raise

    def test_shift_insert():
        l = [1, 2, 3, 5, 6, 7, None, None, None]
        _shift_insert(l, 3, 4)

        try:
            assert l == [1, 2 ,3, 4, 5, 6, 7, None, None]
        except AssertionError:
            print(l)
            raise

    def test_print_tree():
        left = Node(3, [Entry(i, i) for i in [0,1,2]], [])
        mid = Node(3, [Entry(i, i) for i in [4,5,6]], [])
        right = Node(3, [Entry(i, i) for i in [8,9,10]], [])

        root = Node(
            3, [Entry(3,3), Entry(7,7)], [left, mid, right]
        )

        tree = BTree(root, 3)
        tree.print_tree()

    def test_build_tree():
        arr = [
            Entry(i, i) for i in range(0, 21)
        ] + [
            Entry(i, i) for i in range(22, 25)
        ]
        build_tree(arr, 3)

    test_swap()
    test_shift_insert()
    # test_print_tree()
    test_build_tree()
