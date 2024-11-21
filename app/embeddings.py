from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

model = SentenceTransformer(
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)


def generate_embedding(text):
    embedding = model.encode(text)
    return embedding.tolist()


def perform_faiss_similarity_search(embeddings, metadata, query_embedding, top_k):
    """
    Performs a similarity search using FAISS and returns the results.
    """
    # Create FAISS index and add embeddings
    dimension = len(query_embedding)
    index = faiss.IndexFlatL2(dimension)
    embeddings_matrix = np.vstack(embeddings).astype(np.float32)
    index.add(embeddings_matrix)

    # Perform similarity search using FAISS
    query_vector = np.array([query_embedding], dtype=np.float32)
    distances, indices = index.search(query_vector, top_k)

    # Prepare response based on search results
    response = []
    for i in range(len(indices[0])):
        if indices[0][i] == -1:
            continue
        result = metadata[indices[0][i]]

        l2_distance = float(distances[0][i])
        similarity = 1 / (1 + l2_distance)
        result["similarity"] = round(similarity, 4)

        response.append(result)
    return response
