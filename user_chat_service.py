from fastapi import HTTPException
import requests
import pickle
import faiss
import numpy as np

from models import GenAIService
from trigger_ai import get_response_from_provider

def load_user_knowledge_base(xt_vox_id):
    """Load the FAISS index and embeddings for a specific user from saved files."""
    faiss_index_file = f"user_kb/{xt_vox_id}/{xt_vox_id}_faiss_index.index"
    embeddings_file = f"user_kb/{xt_vox_id}/{xt_vox_id}_embeddings.pkl"

    try:
        faiss_index = faiss.read_index(faiss_index_file)
        print(f"✅ FAISS index loaded for user {xt_vox_id}.")
    except Exception as e:
        print(f"❌ Error loading FAISS index for user {xt_vox_id}: {e}")
        return None, None

    try:
        with open(embeddings_file, 'rb') as f:
            data = pickle.load(f)
            if isinstance(data, dict) and 'embeddings' in data and 'knowledge_base' in data:
                knowledge_embeddings = data['embeddings']
                knowledge_base = data['knowledge_base']
                print(f"✅ Embeddings and knowledge base loaded for user {xt_vox_id} with {len(knowledge_base)} entries.")
            else:
                print("❌ Invalid embeddings file format.")
                return faiss_index, None, None
        print(f"✅ Embeddings loaded for user {xt_vox_id}.")
    except Exception as e:
        print(f"❌ Error loading embeddings for user {xt_vox_id}: {e}")
        return faiss_index, None

    return faiss_index, knowledge_embeddings, knowledge_base

def retrieve_contextual_documents(query, embedding_model, xt_vox_id, conversation_context="", top_k=2):
    """Retrieve the top-k relevant documents from the knowledge base for the given query."""
    
    # Load the user's knowledge base
    faiss_index, knowledge_embeddings, knowledge_base = load_user_knowledge_base(xt_vox_id)
    
    if faiss_index is None or knowledge_embeddings is None:
        return ["No knowledge base available."]
    
    # Combine conversation context with the query
    full_query = f"{conversation_context} {query}".strip() if conversation_context else query
    full_query = " ".join(full_query.split())  # Clean up extra whitespace
    
    # Encode the combined query with the embedding model
    query_embedding = embedding_model.encode(full_query, show_progress_bar=False)
    query_embedding = np.array([query_embedding])
    
    # Normalize the embedding for cosine similarity (embeddings are normalized, inner product == cosine similarity)
    faiss.normalize_L2(query_embedding)
    
    # Search the FAISS index for the top-k results
    distances, indices = faiss_index.search(query_embedding, top_k)
    
    # Advanced re-ranking: Apply a similarity threshold (adjust this threshold based on your data)
    similarity_threshold = 0.1  # This threshold can be tuned
    retrieved_documents = []
    
    for score, idx in zip(distances[0], indices[0]):
        if score >= similarity_threshold:
            retrieved_documents.append(knowledge_base[idx])
    
    # Fallback: If no document meets the threshold, return the top_k results regardless
    if not retrieved_documents:
        retrieved_documents = [knowledge_base[i] for i in indices[0]]
    
    return retrieved_documents

def get_ai_response(user_query, embedding_model, xt_vox_id, db):
    """Fetch AI-generated response with multiple API keys as fallback."""
    
    try:
        user_preference = db.query(GenAIService).filter(
                GenAIService.user_id == int(xt_vox_id)).first()
        if not user_preference:
            raise HTTPException(status_code=500, detail="Confugure Gen AI Before Queries")
        provider = user_preference.ai_provider
        model = user_preference.ai_model
        key = user_preference.api_key
        if not provider or not model or not key:
            raise HTTPException(status_code=500, detail="Invalid Confuguration for Gen AI")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
    retrieved_docs = retrieve_contextual_documents(user_query, embedding_model, xt_vox_id, top_k=5)
    retrieved_context = " ".join(retrieved_docs)

    prompt_text = (
        "You **must** include as many exact phrases from the document as possible. "
        "Explain in a structured way using bullet points if needed. "
        "Respond for only asked query"
        "Avoid generalizations, do not introduce new terms, and do not omit key details. "
        "If the answer is not found in the document, state: 'I'm sorry, but that information is not available in the provided document.' "
        "Ensure your response is clear, professional, and factually accurate. "
        "Do not greet in every response and ensure clarity. "
        "If the user's input is a simple greeting (e.g., ‘hai’, ‘hey’, ‘hi’, ‘hello’, ‘thank you’, ‘bye’), respond with an appropriate friendly reply without searching the knowledge base. "
        "DO NOT say check section X or refer to the document or refer a page. "
        f"User asked: '{user_query}'. Answer **only** based on the provided knowledge base: \n\n'{retrieved_context}'\n\n"
    )

    """
    Open Router
    """
    # provider = "openrouter"
    # model = "openai/gpt-4o-mini-search-preview" # OpenAI: GPT-4o-mini Search Preview
    # ### model = "anthropic/claude-3.7-sonnet:beta" # Anthropic: Claude 3.7 Sonnet (self-moderated)
    # model = "google/gemini-2.5-pro-exp-03-25:free" # Google: Gemini Pro 2.5 Experimental (free)
    # model = "x-ai/grok-2-vision-1212" # xAI: Grok 2 Vision 1212
    # model = "qwen/qwen2.5-vl-3b-instruct:free" # Qwen: Qwen2.5 VL 3B Instruct (free)
    # model = "mistralai/mistral-small-3.1-24b-instruct:free" # Mistral: Mistral Small 3.1 24B (free)
    # model = "deepseek/deepseek-chat-v3-0324:free" # DeepSeek: DeepSeek V3 0324 (free)
    # model = "meta-llama/llama-3.3-70b-instruct:free"
    
    
    """
    mistral
    Doesn't have API
    """
    # provider = "mistralai"
    # model = "mistral-small-latest"
    
    
    """
    Google API
    """
    # provider = "google"
    # model = "gemini-1.5-flash-latest"
    
    """
    cohereAi API
    """
    # provider = "cohereAi"
    # model = "command-a-03-2025"
    # model = "command-nightly"
    # model = "command-r"
    # model = "command-r7b-12-2024"
    # model = "command-r-plus"
    # model = "c4ai-aya-vision-32b"
    # model = "command-r7b-arabic-02-2025"
    # model = "command-light-nightly"
    # model = "c4ai-aya-expanse-32b"
    # model = "command"
    
    """
    openAI
    No Free models available to test...
    """
    # provider = "openAI"
    # model = "gpt-4o"
    
    
    # provider = "replicate"
    # model = "anthropic/claude-3.7-sonnet"

    response = get_response_from_provider(model, provider, prompt_text, key)
    return response