import type { Language } from "./api";

export const SAMPLES: { label: string; language: Language; code: string }[] = [
  {
    label: "Binary search tree (C++)",
    language: "cpp",
    code: `#include <iostream>
using namespace std;

struct Node {
    int data;
    Node* left;
    Node* right;
    Node(int value) : data(value), left(nullptr), right(nullptr) {}
};

// Insert a value, keeping smaller values on the left
Node* insert(Node* root, int value) {
    if (root == nullptr) {
        return new Node(value);
    }
    if (value < root->data) {
        root->left = insert(root->left, value);
    } else {
        root->right = insert(root->right, value);
    }
    return root;
}

// Visit left subtree, then the node, then the right subtree
void inorder(Node* root) {
    if (root == nullptr) {
        return;
    }
    inorder(root->left);
    cout << root->data << " ";
    inorder(root->right);
}

int main() {
    Node* root = nullptr;
    int values[] = {50, 30, 70, 20, 40, 60, 80};
    for (int value : values) {
        root = insert(root, value);
    }

    cout << "Sorted: ";
    inorder(root);
    cout << endl;
    return 0;
}`,
  },
  {
    label: "Word counter (Python)",
    language: "python",
    code: `from collections import Counter


def clean(text):
    """Lowercase the text and keep only letters and spaces."""
    return "".join(ch for ch in text.lower() if ch.isalpha() or ch.isspace())


def top_words(text, limit=3):
    words = clean(text).split()
    return Counter(words).most_common(limit)


if __name__ == "__main__":
    sample = "The cat and the hat. The cat sat!"
    for word, count in top_words(sample):
        print(word, count)`,
  },
];

export const LANGUAGES: { value: Language; label: string; monaco: string }[] = [
  { value: "cpp", label: "C++", monaco: "cpp" },
  { value: "c", label: "C", monaco: "c" },
  { value: "python", label: "Python", monaco: "python" },
  { value: "java", label: "Java", monaco: "java" },
  { value: "javascript", label: "JavaScript", monaco: "javascript" },
  { value: "other", label: "Other", monaco: "plaintext" },
];

export function monacoLanguage(language: Language): string {
  return LANGUAGES.find((l) => l.value === language)?.monaco ?? "plaintext";
}
