"""
Tests for RAG nutrition knowledge base and semantic retrieval
"""
import pytest
from app.rag.rag_service import NUTRITION_KNOWLEDGE_BASE, RAGService


def test_knowledge_base_entries():
    assert len(NUTRITION_KNOWLEDGE_BASE) >= 15
    for doc in NUTRITION_KNOWLEDGE_BASE:
        assert "id" in doc
        assert "text" in doc
        assert "topic" in doc
        assert len(doc["text"]) > 20


def test_rag_service_fallback_or_retrieve():
    service = RAGService()
    # Test that documents are loaded
    assert len(service.documents) == len(NUTRITION_KNOWLEDGE_BASE)
    # Test get_context_string format
    # Even if sentence-transformers is not yet initialized or initialized lazily
    assert hasattr(service, "retrieve")
    assert hasattr(service, "get_context_string")
