import math
import re
from collections import Counter
from pathlib import Path


TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_]+|[\u4e00-\u9fff]{2,}")
CHINESE_PATTERN = re.compile(r"[\u4e00-\u9fff]+")


def tokenize(text):
    tokens = [token.lower() for token in TOKEN_PATTERN.findall(text)]
    for match in CHINESE_PATTERN.findall(text):
        tokens.extend(match[index : index + 2] for index in range(len(match) - 1))
    return tokens


def chunk_text(text, max_chars=700, overlap=100):
    clean_text = re.sub(r"\s+", " ", text).strip()
    if not clean_text:
        return []
    if max_chars <= overlap:
        raise ValueError("max_chars must be greater than overlap")

    chunks = []
    start = 0
    while start < len(clean_text):
        end = min(start + max_chars, len(clean_text))
        chunk = clean_text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == len(clean_text):
            break
        start = end - overlap
    return chunks


def build_knowledge_base(root, max_chars=700, overlap=100):
    root = Path(root)
    if not root.exists():
        return []

    chunks = []
    for path in sorted(root.glob("*.md")) + sorted(root.glob("*.txt")):
        text = path.read_text(encoding="utf-8")
        for index, chunk in enumerate(chunk_text(text, max_chars=max_chars, overlap=overlap), start=1):
            tokens = tokenize(chunk)
            chunks.append(
                {
                    "id": f"{path.name}#{index}",
                    "source": path.name,
                    "text": chunk,
                    "tokens": tokens,
                    "vector": Counter(tokens),
                }
            )
    return chunks


def cosine_similarity(left, right):
    if not left or not right:
        return 0.0

    shared = set(left) & set(right)
    dot = sum(left[token] * right[token] for token in shared)
    left_norm = math.sqrt(sum(value * value for value in left.values()))
    right_norm = math.sqrt(sum(value * value for value in right.values()))
    if not left_norm or not right_norm:
        return 0.0
    return dot / (left_norm * right_norm)


def retrieve_relevant_chunks(question, chunks, limit=3, min_score=0.05):
    query_vector = Counter(tokenize(question))
    scored = []
    for chunk in chunks:
        score = cosine_similarity(query_vector, chunk["vector"])
        if score >= min_score:
            scored.append((score, chunk))

    scored.sort(key=lambda item: item[0], reverse=True)
    return [
        {
            "id": chunk["id"],
            "source": chunk["source"],
            "text": chunk["text"],
            "score": round(score, 4),
        }
        for score, chunk in scored[:limit]
    ]
