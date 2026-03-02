"""
RAG System (Retrieval-Augmented Generation)
Nivel 2: Integración de Base de Conocimiento
"""

import json
import os
from pathlib import Path
from typing import List, Tuple, Dict
import numpy as np
from openai import OpenAI

# ============================================================================
# PARTE 1: CONFIGURACIÓN
# ============================================================================

PROJECT_ROOT = Path(__file__).parent.parent
KNOWLEDGE_BASE_DIR = PROJECT_ROOT / "knowledge_base"
VECTOR_STORE_FILE = PROJECT_ROOT / "vector_store" / "embeddings.json"


# ============================================================================
# PARTE 2: CARGA Y PREPARACIÓN DE DOCUMENTOS
# ============================================================================

class DocumentLoader:
    """Carga documentos de la base de conocimiento"""
    
    @staticmethod
    def load_documents() -> List[Dict]:
        """
        Carga todos los documentos .txt de la carpeta knowledge_base
        
        ¿Qué hace?
          - Lee todos los archivos .txt
          - Los parte en chunks (pedazos pequeños)
          - Retorna lista con metadata
        
        Returns:
            Lista de documentos con formato:
            [
              {
                "id": "politica_reembolso_1",
                "source": "politica_reembolso.txt",
                "content": "Texto del documento...",
                "chunk_num": 1
              },
              ...
            ]
        """
        
        documents = []
        doc_id = 0
        
        # Verificar que carpeta exista
        if not KNOWLEDGE_BASE_DIR.exists():
            print(f"⚠️ Carpeta {KNOWLEDGE_BASE_DIR} no existe")
            return []
        
        # Buscar archivos .txt
        for file_path in KNOWLEDGE_BASE_DIR.glob("*.txt"):
            print(f"📄 Cargando: {file_path.name}")
            
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Partir en chunks de ~1000 caracteres
            chunk_size = 1000
            chunks = [
                content[i:i+chunk_size] 
                for i in range(0, len(content), chunk_size)
            ]
            
            # Crear documento por chunk
            for chunk_num, chunk in enumerate(chunks):
                if chunk.strip():  # Solo si no está vacío
                    documents.append({
                        "id": f"{file_path.stem}_{chunk_num}",
                        "source": file_path.name,
                        "content": chunk,
                        "chunk_num": chunk_num
                    })
                    doc_id += 1
        
        print(f"✅ Cargados {len(documents)} chunks de documentos")
        return documents


# ============================================================================
# PARTE 3: CREAR EMBEDDINGS (Vectores)
# ============================================================================

class EmbeddingGenerator:
    """Genera embeddings (representaciones numéricas) de texto"""
    
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Convierte texto en vector numérico usando OpenAI
        
        ¿Qué hace?
          - Envía texto a OpenAI
          - Recibe vector de 1536 dimensiones
          - Retorna como lista
        
        ¿Por qué?
          - Dos textos similares → vectores cercanos
          - Similitud de coseno → distancia en espacio
        
        Args:
            text: Texto a convertir en embedding
            
        Returns:
            Vector de 1536 números float
        """
        
        response = self.client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        
        return response.data[0].embedding
    
    def generate_embeddings_batch(self, documents: List[Dict]) -> List[Dict]:
        """
        Genera embeddings para múltiples documentos
        
        Args:
            documents: Lista de documentos con "content"
            
        Returns:
            Lista de documentos con "embedding" agregado
        """
        
        docs_with_embeddings = []
        
        for i, doc in enumerate(documents):
            print(f"  Generando embedding {i+1}/{len(documents)}...", end="\r")
            
            embedding = self.generate_embedding(doc["content"])
            doc_copy = doc.copy()
            doc_copy["embedding"] = embedding
            docs_with_embeddings.append(doc_copy)
        
        print(f"✅ Generados {len(docs_with_embeddings)} embeddings            ")
        return docs_with_embeddings


# ============================================================================
# PARTE 4: ALMACENAR Y BUSCAR EN VECTOR STORE
# ============================================================================

class VectorStore:
    """Almacena embeddings y busca por similitud"""
    
    @staticmethod
    def save_embeddings(documents: List[Dict], output_file: Path):
        """
        Guarda embeddings en archivo JSON
        
        ¿Por qué guardamos?
          - Evita regenerar embeddings cada vez
          - Ahorra tokens y dinero
          - Más rápido (solo una vez al setup)
        """
        
        # Convertir a formato serializable (numpy → list)
        docs_serializable = []
        for doc in documents:
            doc_copy = doc.copy()
            # Numpy arrays no se pueden serializar directamente
            if isinstance(doc_copy["embedding"], np.ndarray):
                doc_copy["embedding"] = doc_copy["embedding"].tolist()
            docs_serializable.append(doc_copy)
        
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(docs_serializable, f, indent=2)
        
        print(f"✅ Embeddings guardados en {output_file}")
    
    @staticmethod
    def load_embeddings(input_file: Path) -> List[Dict]:
        """Carga embeddings desde archivo"""
        
        if not input_file.exists():
            return []
        
        with open(input_file, "r", encoding="utf-8") as f:
            documents = json.load(f)
        
        # Convertir listas a numpy arrays para cálculos
        for doc in documents:
            doc["embedding"] = np.array(doc["embedding"])
        
        return documents
    
    @staticmethod
    def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
        """
        Calcula similitud de coseno entre dos vectores
        
        Fórmula: cos(θ) = (A · B) / (||A|| × ||B||)
        
        ¿Qué significa?
          - 1.0 = vectores idénticos
          - 0.5 = medianamente similares
          - 0.0 = perpendiculares (no similares)
          - -1.0 = están opposites
        
        Args:
            vec1, vec2: Vectores numpy arrays
            
        Returns:
            Score de similitud (0-1)
        """
        
        dot_product = np.dot(vec1, vec2)
        norm_vec1 = np.linalg.norm(vec1)
        norm_vec2 = np.linalg.norm(vec2)
        
        if norm_vec1 == 0 or norm_vec2 == 0:
            return 0.0
        
        return float(dot_product / (norm_vec1 * norm_vec2))
    
    @staticmethod
    def search(query_embedding: np.ndarray, documents: List[Dict], k: int = 3) -> List[Tuple[Dict, float]]:
        """
        Busca los k documentos más similares a la query
        
        ¿Qué hace?
          1. Calcula similitud con TODOS los documentos
          2. Ordena por similitud descendente
          3. Retorna top k resultados
        
        Args:
            query_embedding: Vector de la pregunta del usuario
            documents: Lista de documentos con embeddings
            k: Número de resultados a retornar
            
        Returns:
            Lista de (documento, similitud) ordenada por similitud
        """
        
        similarities = []
        
        for doc in documents:
            similarity = VectorStore.cosine_similarity(
                query_embedding,
                np.array(doc["embedding"])
            )
            similarities.append((doc, similarity))
        
        # Ordenar por similitud descendente
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Retornar top k
        return similarities[:k]


# ============================================================================
# PARTE 5: ORQUESTACIÓN RAG COMPLETA
# ============================================================================

class RAGSystem:
    """Sistema RAG completo: carga → embeddings → búsqueda → contexto"""
    
    def __init__(self, api_key: str):
        """
        Inicializa el sistema RAG
        
        ¿Qué pasa aquí?
          1. Abre cliente de OpenAI
          2. Carga documentos de knowledge_base
          3. Carga embeddings guardados (o genera si no existen)
        """
        
        print("\n🚀 Inicializando RAG System...")
        
        self.api_key = api_key
        self.client = OpenAI(api_key=api_key)
        self.embedding_generator = EmbeddingGenerator(api_key)
        
        # Cargar documentos
        self.documents = DocumentLoader.load_documents()
        
        if not self.documents:
            print("⚠️ No hay documentos en knowledge_base")
            self.documents_with_embeddings = []
            return
        
        # Cargar o generar embeddings
        self._initialize_embeddings()
        
        print("✅ RAG System listo\n")
    
    def _initialize_embeddings(self):
        """Carga embeddings existentes o genera nuevos"""
        
        # Intentar cargar embeddings guardados
        self.documents_with_embeddings = VectorStore.load_embeddings(VECTOR_STORE_FILE)
        
        if self.documents_with_embeddings:
            print(f"✅ Cargados {len(self.documents_with_embeddings)} embeddings del archivo")
            return
        
        # Si no existen, generar nuevos
        print("📊 Generando embeddings (primera ejecución, toma 1-2 min)...")
        self.documents_with_embeddings = self.embedding_generator.generate_embeddings_batch(
            self.documents
        )
        
        # Guardar para uso futuro
        VectorStore.save_embeddings(self.documents_with_embeddings, VECTOR_STORE_FILE)
    
    def retrieve_context(self, query: str, k: int = 3) -> str:
        """
        Busca documentos relevantes y devuelve contexto formateado
        
        Flujo:
          1. Generar embedding de la pregunta
          2. Buscar documentos similares
          3. Formatear contexto para LLM
        
        Args:
            query: Pregunta del usuario
            k: Número de documentos a recuperar
            
        Returns:
            String con formato CONTEXTO: [documentos]
        """
        
        if not self.documents_with_embeddings:
            return ""
        
        # Generar embedding de la pregunta
        query_embedding = np.array(
            self.embedding_generator.generate_embedding(query)
        )
        
        # Buscar documentos similares
        results = VectorStore.search(query_embedding, self.documents_with_embeddings, k=k)
        
        # Formatear contexto
        if not results:
            return ""
        
        context_parts = ["=== CONTEXTO DE BASE DE CONOCIMIENTO ===\n"]
        
        for doc, similarity in results:
            context_parts.append(f"\n📄 Desde: {doc['source']}")
            context_parts.append(f"   (Similitud: {similarity:.2%})\n")
            context_parts.append(f"{doc['content'][:500]}...\n")
            context_parts.append("-" * 60)
        
        return "\n".join(context_parts)
    
    def get_rag_prompt(self, user_question: str) -> str:
        """
        Genera prompt completo: sistema + instrucciones + contexto recuperado
        
        ¿Qué hace?
          1. Lee el prompt base
          2. Recupera contexto relevante
          3. Crea prompt final
        
        Args:
            user_question: Pregunta del usuario
            
        Returns:
            Prompt listo para OpenAI
        """
        
        # Cargar prompt base
        prompt_path = PROJECT_ROOT / "prompts" / "main_prompt.txt"
        with open(prompt_path, "r", encoding="utf-8") as f:
            base_prompt = f.read()
        
        # Recuperar contexto
        context = self.retrieve_context(user_question, k=3)
        
        # Agregar contexto al prompt
        if context:
            base_prompt += f"\n\n{context}"
            base_prompt += "\n\nResponde basado en este contexto. Si la información no está en los documentos, indícalo."
        
        return base_prompt


# ============================================================================
# USO: Ejemplo de cómo usar RAG System
# ============================================================================

if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    API_KEY = os.getenv("OPENAI_API_KEY")
    
    if not API_KEY:
        print("ERROR: OPENAI_API_KEY no configurada")
        exit(1)
    
    # Inicializar RAG
    rag = RAGSystem(API_KEY)
    
    # Ejemplo de búsqueda
    query = "¿Cuál es la política de reembolso?"
    context = rag.retrieve_context(query)
    print(context)
