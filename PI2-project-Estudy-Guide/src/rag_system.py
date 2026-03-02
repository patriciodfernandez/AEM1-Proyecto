"""
RAG SYSTEM - Retrieval Augmented Generation
Carga documentos, genera embeddings y recupera contexto relevante
"""

import os
import json
import math
from pathlib import Path
from typing import List, Dict, Tuple
from openai import OpenAI

client = OpenAI()

class DocumentLoader:
    """Carga y divide documentos en chunks"""
    
    def __init__(self, knowledge_base_dir: str, chunk_size: int = 1000):
        self.knowledge_base_dir = knowledge_base_dir
        self.chunk_size = chunk_size
        self.documents = []
    
    def load_documents(self) -> List[Dict]:
        """Carga todos los .txt y divide en chunks"""
        chunks = []
        doc_id = 0
        
        for file_path in Path(self.knowledge_base_dir).glob("*.txt"):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Dividir en chunks
            for i in range(0, len(content), self.chunk_size):
                chunk = content[i:i + self.chunk_size]
                chunks.append({
                    "id": doc_id,
                    "source": file_path.name,
                    "content": chunk
                })
                doc_id += 1
        
        self.documents = chunks
        return chunks


class EmbeddingGenerator:
    """Genera embeddings usando OpenAI API"""
    
    def generate_embedding(self, text: str) -> List[float]:
        """Genera embedding para un texto"""
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding


class VectorStore:
    """Almacena embeddings y busca por similitud"""
    
    def __init__(self, vector_store_path: str):
        self.vector_store_path = vector_store_path
        self.embeddings = []
    
    @staticmethod
    def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """Calcula similitud coseno entre dos vectores"""
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot_product / (norm1 * norm2)
    
    def save_embeddings(self, embeddings: List[Dict]):
        """Guarda embeddings en disco"""
        os.makedirs(os.path.dirname(self.vector_store_path), exist_ok=True)
        with open(self.vector_store_path, 'w') as f:
            json.dump(embeddings, f)
    
    def load_embeddings(self) -> List[Dict]:
        """Carga embeddings del disco"""
        if os.path.exists(self.vector_store_path):
            with open(self.vector_store_path, 'r') as f:
                return json.load(f)
        return []
    
    def search(self, query_embedding: List[float], top_k: int = 3) -> List[Tuple[Dict, float]]:
        """Busca los top-k documentos más similares"""
        results = []
        
        for embedding_item in self.embeddings:
            similarity = self.cosine_similarity(query_embedding, embedding_item['embedding'])
            results.append((embedding_item, similarity))
        
        # Ordenar por similitud y retornar top-k
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]


class RAGSystem:
    """Orquesta todo el pipeline de RAG"""
    
    def __init__(self, knowledge_base_dir: str, vector_store_path: str):
        self.knowledge_base_dir = knowledge_base_dir
        self.vector_store_path = vector_store_path
        self.vector_store = VectorStore(vector_store_path)
        self.embedding_generator = EmbeddingGenerator()
        
        self._initialize()
    
    def _initialize(self):
        """Inicializa el sistema RAG"""
        # Intentar cargar embeddings existentes
        self.vector_store.embeddings = self.vector_store.load_embeddings()
        
        if not self.vector_store.embeddings:
            # Generar embeddings nuevos
            print("📊 Generando embeddings (primera ejecución, toma 1-2 min)...")
            loader = DocumentLoader(self.knowledge_base_dir)
            documents = loader.load_documents()
            
            embeddings = []
            for doc in documents:
                embedding = self.embedding_generator.generate_embedding(doc['content'])
                embeddings.append({
                    'id': doc['id'],
                    'source': doc['source'],
                    'content': doc['content'],
                    'embedding': embedding
                })
            
            self.vector_store.embeddings = embeddings
            self.vector_store.save_embeddings(embeddings)
            print("✅ Embeddings guardados")
        else:
            print("✅ Cargados embeddings del archivo")
    
    def retrieve_context(self, query: str, top_k: int = 3) -> str:
        """Recupera contexto relevante para una consulta"""
        # Generar embedding de la consulta
        query_embedding = self.embedding_generator.generate_embedding(query)
        
        # Buscar documentos similares
        results = self.vector_store.search(query_embedding, top_k=top_k)
        
        # Formatear contexto
        context_parts = []
        for doc, similarity in results:
            if similarity > 0.3:  # Solo incluir si similitud > 0.3
                context_parts.append(f"[Fuente: {doc['source']}]\n{doc['content'][:500]}")
        
        return "\n\n".join(context_parts) if context_parts else ""
    
    def get_rag_prompt(self, user_question: str, system_prompt: str) -> str:
        """Construye el prompt con contexto RAG"""
        context = self.retrieve_context(user_question)
        
        if not context:
            return f"{system_prompt}\n\nPregunta: {user_question}"
        
        return f"""{system_prompt}

[CONTEXTO INTERNO DE LA EMPRESA]
{context}

[PREGUNTA DEL CLIENTE]
{user_question}"""
