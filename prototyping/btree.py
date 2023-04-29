from typing import Any, Optional
from dataclasses import dataclass
import random


@dataclass
class Entry:
    "An entry in a Btree"
    key: Any
    value: Any

    def __eq__(self, __o: object) -> bool:
        return self.key == __o.key

    def __lt__(self, __o: object) -> bool:
        return self.key < __o.key

    def __gt__(self, __o: object) -> bool:
        return self.key < __o.key

def _swap(lst: list, i: int, j: int):
    """
    Given an list and 2 indexes swap the values at those indexes

    Args:
        lst: List to mutate
        i: Index of value to swap with value at index j
        j: Index of value to swap with value at index i
    """
    lst[i], lst[j] = lst[j], lst[i]


def _shift_insert(lst: list, index: int, value: Any) -> Any:
    """
    Insert a value into a list at a given index
    shifting all values at and the right of the index to the right

    Args:
        lst: List to mutate
        index: Index to insert the value at
        value: Value to insert into the list
    """
    i = len(lst)
    lst.append(None)

    while i > index:
        _swap(lst, i-1, i)
        i -= 1

    lst[index] = value
    # if the last value is None we can remove the shift None to keep the
    # node the correct length. If not we dont want to pop it off since we
    # need the value for the split
    if lst[-1] is None:
        lst.pop()


def _shift_remove(lst: list, index: int) -> Any:
    i = index

    while i + 1 < len(lst):
        _swap(lst, i, i + 1)
        i += 1

    val = lst.pop()
    lst.append(None)
    return val


class Node:
    """A class representing a Node of a Btree"""
    def __init__(
        self,
        b: int,
        entries: list[Entry],
        edges: list["Node"]
    ):

        # null space for padding entries and edges lists
        null_space = [None for _ in range(b - len(entries))]

        self.entries = entries + null_space
        self.edges = edges + null_space

        self.b = b

    def search(self, entry: Entry) -> tuple[bool, int]:
        """
        Given a key search for the key in this Node returning
        the index the key is found at or the index of the edge
        that should be followed to a deeper node.

        Args:
            entry: An entry to search for in the node

        Returns:
            found -> indicates the actual key was found in the node
            i -> The index the key is at or the search should continue at
        """
        found = False
        for i, node_entry in enumerate(self.entries):

            # If the search key is > than the current entry continue the search
            if entry > node_entry:
                continue
            # If the search key is == to the current entry indicate we found
            # the actual key and return the current index
            if entry == node_entry:
                found = True
                return found, i
            # If we found an entry with a key > the our search key we need
            # to continue down.
            if entry < node_entry:
                return found, i

        # If no entry with a key > our search key is found cotinue down
        # into the right most child
        return found, len(self.entries)

    def _split(self) -> tuple["Node", "Node"]:
        """
        Split a node into 2 nodes giving half the entries
        and edges to each newly created node

        Returns:
            A tuple containg two new nodes from the split
        """
        mid = len(self.entries) // 2 + 1

        # filter out Nones at the new node will repad the lists on creation
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


    def _place(self, entry: Entry) -> tuple[bool, int]:
        """
        Given a key, determine at what index in this node the key would belong

        Args:
            entry: A new entry to place in the node
        Returns:
            exists -> A boolean indicating the key already exists in the node
            idx -> The index at which the key would belong if inserted into
                this node
        """
        idx = 0
        while self.entries[idx] is not None and self.entries[idx] < entry:
            idx += 1
            if idx == len(self.entries):
                return False, idx

        index_entry = self.entries[idx]
        return bool(index_entry) and index_entry == entry, idx
    

    def insert(self, entry: Entry) -> Optional[tuple["Node", "Node"]]:
        """
        Given an entry, find a leaf that the entry can be inserted into and
        insert it. If the leaf becomes overfull upon insertion, handle the
        splitting and bubbling up of entries up to the parent nodes

        Args:
            entry: An entry to insert into the node
        """
        # search for the key in the current node
        exists, insert_index = self._place(entry)

        # If the key exists in this node, set the value and return None
        if exists:
            self.entries[insert_index] = entry
            return None

        # If the value does not exist in this node and this node is not
        # a leaf node we need to traverse down the tree. Get the node at the
        # index found by the _place method and and try to insert the entry
        # into it.
        if not self.is_leaf():
            node = self.edges[insert_index]
            assert node is not None

            new_nodes = node.insert(entry)

            # If no split occured return None to the caller
            if new_nodes is None:
                return None

            # If the node or any node below it was split by the insert
            # we need to handle the bubble up
            left_node, right_node = new_nodes

            # Get the last entry from the left node of the split.
            # This will entry be inserted into the entries for the current node
            entry = left_node.take_last_non_null_entry()

            # replace the node at the insert_index with the left node
            # and insert the right node one to the right of it.
            self.edges[insert_index] = left_node
            _shift_insert(self.edges, insert_index + 1, right_node)

        # Insert the entry into the current node. This handles both the case
        # where the entry is the original entry passed in or if the entry is
        # being inserted as the result of a split
        _shift_insert(self.entries, insert_index, entry)

        # If the node is full split it into two and return the new nodes to the
        # caller
        if self.is_over_full():
            return self._split()

        return None

    def remove(self, entry: Entry):
        """Remove an entry from the Node"""
        found, index = self.search(entry)

        if not found and self.is_leaf():
            raise ValueError("Value not found in tree")
        elif not found:
            node = self.edges[index]
            node.remove(entry)
        else:
            node_with_replacement = self
            while not node_with_replacement.is_leaf():
                node_with_replacement = node_with_replacement.edges[0]

            replacement = _shift_remove(node_with_replacement.entries, 0)
            self.entries[index] = replacement

        if self.is_under_full():
            pass


    def is_over_full(self) -> bool:
        """Determine if the current node is full"""
        return self.b + 1 == len([entry for entry in self.entries if entry])

    def is_under_full(self) -> bool:
        return len([entry for entry in self.entries if entry])  < self.b // 2

    def is_leaf(self) -> bool:
        """Determine if the current node is a leaf"""
        return not any(map(bool, self.edges))

    def take_last_non_null_entry(self) -> Entry:
        """Get the last non null entry from the current node"""
        last_non_null_index = 0
        while (
            last_non_null_index < len(self.entries) - 1 and
            self.entries[last_non_null_index + 1] is not None
        ):
            last_non_null_index += 1

        taken = self.entries[last_non_null_index]
        self.entries[last_non_null_index] = None

        return taken

    def get_node_by_index(self, idx: int) -> "Node":
        """Public interface for retrieving a child node by index"""
        return self.edges[idx]

    def get_entry_by_index(self, idx: int) -> Entry:
        """Public interface for retrieving an entry by index"""
        return self.entries[idx]


class BTree:
    """A class representing a basic BTree map"""

    def __init__(self, root: Node, b: int):
        self.root = root
        self.b = b

    def find(self, key: Any) -> Optional[Any]:
        """
        Given a key, find the key in the map returnong None if it
        does not exist

        Arg:
            key: Key to search the map for
        """
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
        """
        Given a key and a value, insert them into the BTree map

        Args:
            key: Key to insert into the map
            value: Value to store with the key
        """
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

    def height(self) -> int:
        """
        Determine the height of the BTree map
        """
        height = 1
        node = self.root
        while any(node.edges):
            height += 1
            node = node.edges[0]

        return height

    def print_tree(self, nodes=None):
        """Crudely print the Btree Map"""
        height = self.height()
        if nodes is None:
            nodes = [[self.root]]

        max_leaves = (self.b)**(height-1)
        node_witdh = self.b * 6
        paren_padding = (height-1 * self.b + 1 * 3)

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

        layer = '  '.join(formatted_nodes)
        padding = ((leaf_width - len(layer)) // 2) + 1

        print(padding*' '+layer)
        print()
        print()

        new_nodes = []
        for node_list in nodes:
            for node in node_list:
                if not node:
                    continue
                new_nodes.append(node.edges)

        if any(any(node_list) for node_list in new_nodes):
            self.print_tree(new_nodes)


def build_tree(lst: list, b: int) -> BTree:
    tree = BTree(Node(b, [], []), b)
    for item in lst:
        tree.add(item.key, item.value)

    return tree


if __name__ == '__main__':

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
            assert l == [1, 2, 3, 4, 5, 6, 7, None, None]
        except AssertionError:
            print(l)
            raise

    def test_build_tree():
        arr = [
            Entry(i, i) for i in range(0, 21)
        ] + [
            Entry(i, i) for i in range(22, 36)
        ]
        random.shuffle(arr)
        tree = build_tree(arr, 3)
        tree.print_tree()

    test_swap()
    test_shift_insert()
    test_build_tree()
