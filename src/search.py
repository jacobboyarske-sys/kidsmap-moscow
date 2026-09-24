import json
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from src.data import event_key
from src.embed_events import EMBEDDINGS_PATH, KEYS_PATH, MODEL_NAME
from src.models import Event


def load_model() -> SentenceTransformer:
    return SentenceTransformer(MODEL_NAME)


def load_embeddings(
    embeddings_path: Path = EMBEDDINGS_PATH, keys_path: Path = KEYS_PATH
) -> tuple[np.ndarray, dict[tuple, int]]:
    if not embeddings_path.exists() or not keys_path.exists():
        raise FileNotFoundError(
            "Эмбеддинги не найдены — сначала запустите `python -m src.embed_events`."
        )

    embeddings = np.load(embeddings_path)
    with keys_path.open(encoding="utf-8") as f:
        keys = [tuple(k) for k in json.load(f)]

    key_to_index = {key: i for i, key in enumerate(keys)}
    return embeddings, key_to_index


def search_events(
    query: str,
    events: list[Event],
    model: SentenceTransformer,
    embeddings: np.ndarray,
    key_to_index: dict[tuple, int],
    top_n: int = 10,
) -> list[Event]:
    candidates = [e for e in events if event_key(e) in key_to_index]
    if not candidates:
        return []

    indices = [key_to_index[event_key(e)] for e in candidates]
    candidate_vectors = embeddings[indices]

    query_vector = model.encode([query])
    similarities = cosine_similarity(query_vector, candidate_vectors)[0]

    ranked = sorted(zip(candidates, similarities), key=lambda pair: pair[1], reverse=True)
    return [event for event, _ in ranked[:top_n]]
