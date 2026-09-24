import json
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer

from src.data import event_key, load_events

MODEL_NAME = "cointegrated/rubert-tiny2"
EMBEDDINGS_PATH = Path("data/event_embeddings.npy")
KEYS_PATH = Path("data/event_embeddings_keys.json")


def main() -> None:
    events = load_events()
    if not events:
        print("Нет событий для эмбеддинга — сначала соберите data/events.json.")
        return

    texts = [f"{e.title}. {e.description}" for e in events]
    keys = [list(event_key(e)) for e in events]

    model = SentenceTransformer(MODEL_NAME)
    embeddings = model.encode(texts, show_progress_bar=True)

    np.save(EMBEDDINGS_PATH, embeddings)
    with KEYS_PATH.open("w", encoding="utf-8") as f:
        json.dump(keys, f, ensure_ascii=False, indent=2)

    print(f"Сохранено {len(events)} эмбеддингов в {EMBEDDINGS_PATH} (размерность {embeddings.shape[1]})")


if __name__ == "__main__":
    main()
