import numpy as np
from app.rag.rag_service import get_rag_service

rag = get_rag_service()
rag.initialize()

queries = ["what is 2+2?", "hello", "who is the president?", "is pizza healthy?", "how much protein in chicken breast?"]
for q in queries:
    q_emb = rag.encoder.encode([q]).astype(np.float32)
    dist, ind = rag.index.search(q_emb, 3)
    print(f"=== Query: '{q}' ===")
    for d, i in zip(dist[0], ind[0]):
        print(f"  Dist: {d:.4f} | Topic: {rag.documents[i]['topic']}")
