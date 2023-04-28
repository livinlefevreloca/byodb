use std::sync::{RwLock, Arc, RwLockReadGuard};
use std::ops::Deref;
use std::fmt::Debug;

#[derive(Debug, Clone)]
pub struct Node<T, V, const N: usize> {
    inner: Arc<RwLock<Inner<T, V, N>>>
}


pub enum SearchResult {
    Found(usize),
    Continue(usize)
}


impl<T: Debug + Clone + Ord, V: Debug + Clone, const N: usize> Node<T, V, N> { 


    fn new() -> Self {
        let children = Vec::with_capacity(N);
        let data = Vec::with_capacity(N);

        let inner = Inner {
            data,
            children
        };

        Node {
            inner: Arc::new(RwLock::new(inner))
        }
    }

    fn new_leaf() -> Self {
        let children = Vec::new();
        let data = Vec::with_capacity(N);

        let inner = Inner {
            data,
            children
        };

        Node {
            inner: Arc::new(RwLock::new(inner))
        }
    }

    fn keys(&self) -> ValueRefData<'_, T, V, N> {
        let guard = self.inner.read().expect("Should not be poisined");
        ValueRefData(guard)
    }

    fn children(&self) -> ValueRefChildren<'_, T, V, N> {
        let guard = self.inner.read().expect("Should not be poisined");
        ValueRefChildren(guard)
    }

    fn get_node_by_index(&self, index: usize) -> ValueRefChild<T, V, N> {
        let guard = self.inner.read().expect("Should not be poisined");
        ValueRefChild(guard, index)
    }
    
    fn get_pair_by_index(&self, index: usize) -> ValueRefPair<T, V, N> {
        let guard = self.inner.read().expect("Should not be poisined");
        ValueRefPair(guard, index)
    }

    fn clone_children(&self) -> Vec<Node<T, V, N>> {
        let gaurd = self.inner.read().expect("Should not be poisined");
        gaurd.children.iter().map(|n| Node { inner: Arc::clone(&n.inner) }).collect()
    }

    fn size(&self) -> usize {
        self.inner.read().expect("Should not be poisined").children.len()
    }

    fn capacity(&self) -> usize {
        self.inner.read().expect("Should not be poisined").children.capacity()
    }

    fn is_full(&self) -> bool {
        self.size() == self.capacity()
    }

    fn is_leaf(&self) -> bool {
        self.capacity() == 0
    }

    fn replace(&mut self, new: Node<T, V, N>) {
        let mut gaurd = self.inner.write().expect("Should not be poisined");
        *gaurd = new.take_inner()
    }

    fn take_inner(self) -> Inner<T, V, N> {
        Arc::try_unwrap(self.inner).expect("Value exists").into_inner().unwrap()
    }

    fn split(self) -> (Node<T, V, N>, Node<T, V, N>) {
        let size = self.size();
        let mid = size / 2 + 1;
        let inner = self.take_inner();

        let (left_data, right_data) = inner.data.split_at(mid);
        let (left_children, right_children) =  inner.children.split_at(mid);    
        
        let left = Node::new();
        let right =  Node::new();
        
        {
            let mut left_node = left.inner.write().expect("Should not be poisined");
            left_node.data.extend_from_slice(left_data);
            left_node.children.extend_from_slice(left_children);
        };
        { 
            let mut right_node = right.inner.write().expect("Should not be poisined");
            right_node.data.extend_from_slice(right_data);
            right_node.children.extend_from_slice(right_children);
        };

        (left, right)
    }

    fn search(&self, key: &T) -> SearchResult {
        for (i, pair) in self.inner.read().expect("Should not be poisined").data.iter().enumerate() {
            match pair.0.cmp(key) {
                std::cmp::Ordering::Less => {},
                std::cmp::Ordering::Equal => return SearchResult::Found(i),
                std::cmp::Ordering::Greater=> return SearchResult::Continue(i)
            }
        }
        SearchResult::Continue(self.size())
    }
}



#[derive(Debug)]
struct Inner<T: Sized, V: Sized, const N: usize> {
    data: Vec<(T, V)>,
    children: Vec<Node<T, V, N>>
}


pub struct ValueRefData<'a, T, V, const N: usize>(RwLockReadGuard<'a, Inner<T, V, N>>);

impl<'a, T: Sized, V: Sized, const N: usize> Deref for ValueRefData<'a, T, V, N> {
    type Target = [(T, V)];

    fn deref(& self) -> & Self::Target {
        self.0.data.as_slice()
    }
}

pub struct ValueRefChildren<'a, T, V, const N: usize>(RwLockReadGuard<'a, Inner<T, V, N>>);

impl<'a, T: Sized, V: Sized, const N: usize> Deref for ValueRefChildren<'a, T, V, N> {
    type Target = [Node<T, V, N>];

    fn deref(& self) -> & Self::Target {
        self.0.children.as_slice()
    }
}

pub struct ValueRefChild<'a, T, V, const N: usize>(RwLockReadGuard<'a, Inner<T, V, N>>, usize);

impl<'a, T: Sized, V: Sized, const N: usize> Deref for ValueRefChild<'a, T, V, N> {
    type Target = Node<T, V, N>;

    fn deref(&self) -> &Self::Target {
        &self.0.children.as_slice()[self.1]
    }
}

pub struct ValueRefPair<'a, T, V: Sized, const N: usize>(RwLockReadGuard<'a, Inner<T, V, N>>, usize);

impl<'a, T: Sized, V: Sized, const N: usize> Deref for ValueRefPair<'a, T, V, N> {
    type Target = (T, V);

    fn deref(&self) -> &Self::Target {
        &self.0.data.as_slice()[self.1]
    }
}

