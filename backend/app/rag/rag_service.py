"""
NutriGuide AI - RAG Knowledge Base and Retrieval Service

Uses Sentence Transformers + FAISS for semantic retrieval over
a curated nutrition knowledge base.
"""
import logging
import os
import json
from typing import List, Optional
import numpy as np

logger = logging.getLogger(__name__)

# Curated nutrition knowledge base
NUTRITION_KNOWLEDGE_BASE = [
    {
        "id": "kcal_def",
        "text": "A calorie (kcal) is a unit of energy. Foods provide energy through macronutrients: carbohydrates provide 4 kcal/g, proteins provide 4 kcal/g, and fats provide 9 kcal/g.",
        "topic": "calories"
    },
    {
        "id": "protein_role",
        "text": "Protein is essential for building and repairing tissues, making enzymes and hormones, and supporting immune function. Good protein sources include meat, fish, eggs, dairy, legumes, and nuts.",
        "topic": "protein"
    },
    {
        "id": "carbs_types",
        "text": "Carbohydrates are the body's primary energy source. Simple carbohydrates (sugars) are digested quickly, while complex carbohydrates (starches, fiber) are digested more slowly. Foods high in complex carbohydrates include whole grains, vegetables, and legumes.",
        "topic": "carbohydrates"
    },
    {
        "id": "dietary_fiber",
        "text": "Dietary fiber is a type of carbohydrate that the body cannot digest. Soluble fiber dissolves in water and can help lower blood glucose and cholesterol. Insoluble fiber adds bulk to stool. High-fiber foods include vegetables, fruits, whole grains, and legumes.",
        "topic": "fiber"
    },
    {
        "id": "fats_types",
        "text": "Dietary fats include saturated fats (found in animal products), unsaturated fats (found in plant oils, nuts, fish), and trans fats (found in some processed foods). Unsaturated fats are generally considered heart-healthy.",
        "topic": "fat"
    },
    {
        "id": "sodium_role",
        "text": "Sodium is an essential mineral that helps regulate fluid balance and blood pressure. Excessive sodium intake is associated with high blood pressure. Most dietary sodium comes from processed and restaurant foods.",
        "topic": "sodium"
    },
    {
        "id": "sugar_effects",
        "text": "Added sugars provide calories without essential nutrients. High sugar intake is associated with tooth decay, weight gain, and metabolic issues. Natural sugars in fruits come packaged with fiber, vitamins, and minerals.",
        "topic": "sugar"
    },
    {
        "id": "bmi_nutrition",
        "text": "A balanced diet generally includes a variety of fruits, vegetables, whole grains, lean proteins, and healthy fats. No single food is perfect - dietary patterns matter more than individual foods.",
        "topic": "balanced diet"
    },
    {
        "id": "allergen_info",
        "text": "The 14 major food allergens recognized in Europe include: celery, cereals containing gluten, crustaceans, eggs, fish, lupin, milk, molluscs, mustard, tree nuts, peanuts, sesame, soybeans, and sulphites. In the US, the major allergens are milk, eggs, fish, shellfish, tree nuts, peanuts, wheat, soybeans, and sesame.",
        "topic": "allergens"
    },
    {
        "id": "gi_index",
        "text": "The Glycemic Index (GI) measures how quickly a food raises blood sugar. Low GI foods (55 or less) include most vegetables, legumes, and whole grains. High GI foods (70+) include white bread, white rice, and sugary drinks.",
        "topic": "glycemic index"
    },
    {
        "id": "vitamins_minerals",
        "text": "Vitamins and minerals are micronutrients essential for health. Vitamin C supports immune function and is found in citrus fruits and peppers. Vitamin D supports bone health. Iron is essential for red blood cells. Calcium supports bone and muscle function.",
        "topic": "vitamins minerals"
    },
    {
        "id": "serving_size",
        "text": "Nutrition labels show values per serving size, which varies by product. Per 100g values allow direct comparison between different foods. When comparing foods, always use the same measurement basis.",
        "topic": "serving size nutrition label"
    },
    {
        "id": "processed_food",
        "text": "Ultra-processed foods typically contain added sugars, unhealthy fats, sodium, and artificial ingredients. They often have low fiber and nutrient density. Examples include fast food, packaged snacks, and sugary beverages.",
        "topic": "processed food"
    },
    {
        "id": "protein_daily",
        "text": "The recommended dietary allowance (RDA) for protein is 0.8g per kg of body weight per day for adults. Athletes and active individuals may need 1.2-2.0g per kg. A 150-pound (68kg) adult needs approximately 55g of protein daily.",
        "topic": "protein requirements"
    },
    {
        "id": "calorie_density",
        "text": "Calorie density refers to the number of calories per gram of food. Vegetables and fruits have low calorie density (0.5-1 kcal/g). Whole grains are moderate (1-4 kcal/g). Fats and oils have high calorie density (8-9 kcal/g).",
        "topic": "calorie density"
    },
    {
        "id": "food101_pizza",
        "text": "Pizza is typically high in calories, carbohydrates, fat, and sodium. A slice of cheese pizza (100g) contains approximately 266 kcal, 10g protein, 33g carbohydrates, and 10g fat. Toppings significantly affect nutritional content.",
        "topic": "pizza nutrition"
    },
    {
        "id": "food101_salad",
        "text": "Caesar salad contains romaine lettuce, croutons, Caesar dressing, and parmesan cheese. The dressing can be high in fat and sodium. Without dressing, salad greens are very low in calories and high in fiber and vitamins.",
        "topic": "caesar salad nutrition"
    },
    {
        "id": "food101_hamburger",
        "text": "A hamburger typically contains a beef patty, bun, and condiments. It provides protein from the beef but can be high in saturated fat and sodium. Adding vegetables like lettuce and tomato increases fiber and micronutrient content.",
        "topic": "hamburger nutrition"
    },
    {
        "id": "food101_sushi",
        "text": "Sushi typically consists of vinegared rice with fish, vegetables, or other ingredients. It provides lean protein from fish, omega-3 fatty acids, and moderate carbohydrates. Sodium can be high due to soy sauce.",
        "topic": "sushi nutrition"
    },
    {
        "id": "food101_steak",
        "text": "Steak is rich in high-quality protein, iron, zinc, and B vitamins, particularly B12. Fat content varies by cut - tenderloin is leaner while ribeye has more fat. Cooking method affects final nutritional content.",
        "topic": "steak nutrition"
    },
]


class RAGService:
    """Semantic retrieval over the nutrition knowledge base using FAISS."""

    def __init__(self):
        self.documents = NUTRITION_KNOWLEDGE_BASE
        self.embeddings = None
        self.index = None
        self._initialized = False
        self._init_error = None

    def initialize(self):
        """Build FAISS index. Call this lazily on first use."""
        if self._initialized:
            return
        try:
            from sentence_transformers import SentenceTransformer
            import faiss

            logger.info("Loading sentence transformer model...")
            self.encoder = SentenceTransformer("all-MiniLM-L6-v2")
            texts = [doc["text"] for doc in self.documents]
            logger.info("Building FAISS index...")
            self.embeddings = self.encoder.encode(texts, show_progress_bar=False)
            d = self.embeddings.shape[1]
            self.index = faiss.IndexFlatL2(d)
            self.index.add(self.embeddings.astype(np.float32))
            self._initialized = True
            logger.info(f"RAG index built with {len(self.documents)} documents.")
        except Exception as e:
            self._init_error = str(e)
            logger.error(f"RAG initialization failed: {e}")

    def _fallback_retrieve(self, query: str, k: int = 3) -> List[str]:
        """Keyword and topic-based fallback retrieval when vector search is unavailable."""
        query_tokens = set(query.lower().replace("?", "").replace(",", "").replace(".", "").split())
        scored_docs = []
        for doc in self.documents:
            score = 0
            topic_tokens = set(doc["topic"].lower().split())
            text_tokens = set(doc["text"].lower().split())
            score += len(query_tokens.intersection(topic_tokens)) * 4
            score += len(query_tokens.intersection(text_tokens)) * 1
            if score > 0:
                scored_docs.append((score, doc["text"]))
        scored_docs.sort(key=lambda x: x[0], reverse=True)
        return [doc_text for _, doc_text in scored_docs[:k]]

    def retrieve(self, query: str, k: int = 3) -> List[str]:
        """Retrieve top-k relevant documents for the query."""
        if not query or not query.strip():
            return []
        k = max(1, min(int(k), len(self.documents)))

        if not self._initialized:
            self.initialize()
        if self._initialized and self.index is not None and hasattr(self, "encoder"):
            try:
                query_embedding = self.encoder.encode([query.strip()]).astype(np.float32)
                distances, indices = self.index.search(query_embedding, k)
                results = []
                for i, idx in enumerate(indices[0]):
                    if idx < len(self.documents) and distances[0][i] < 2.0:
                        results.append(self.documents[idx]["text"])
                if results:
                    return results
            except Exception as e:
                logger.error(f"RAG vector retrieval error: {e}")

        # Seamless fallback
        return self._fallback_retrieve(query.strip(), k)

    def get_context_string(self, query: str, k: int = 3) -> str:
        """Get retrieved context as a formatted string."""
        docs = self.retrieve(query, k)
        if not docs:
            return ""
        return "\n\n".join(f"[{i+1}] {doc}" for i, doc in enumerate(docs))


# Module-level singleton - initialized lazily
_rag_service: Optional[RAGService] = None


def get_rag_service() -> RAGService:
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
