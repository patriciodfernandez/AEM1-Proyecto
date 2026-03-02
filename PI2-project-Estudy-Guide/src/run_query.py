"""
RUN QUERY - Level 3 AGENTS
Orquesta RAG + Agents + Function Calling
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import our systems
from rag_system import RAGSystem
from agents_system import AgentOrchestrator

# Configuration
CONFIG = {
    "project_dir": Path(__file__).parent.parent,
    "knowledge_base_dir": Path(__file__).parent.parent / "knowledge_base",
    "vector_store_path": Path(__file__).parent.parent / "vector_store" / "embeddings.json",
    "prompt_file": Path(__file__).parent.parent / "prompts" / "main_prompt.txt",
    "metrics_file": Path(__file__).parent.parent / "metrics" / "metrics.json",
}


def load_prompt() -> str:
    """Carga el prompt del archivo"""
    try:
        with open(CONFIG["prompt_file"], 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        raise ValueError(f"Prompt no encontrado en {CONFIG['prompt_file']}")


def initialize_systems():
    """Inicializa RAG System y Agent Orchestrator"""
    print("⏳ Inicializando sistema (primer acceso puede tomar 1-2 min)...")
    
    # Load prompt
    system_prompt = load_prompt()
    
    print("\n🚀 Inicializando RAG System...")
    rag_system = RAGSystem(
        str(CONFIG["knowledge_base_dir"]),
        str(CONFIG["vector_store_path"])
    )
    print("✅ RAG System listo\n")
    
    print("🤖 Inicializando Agent Orchestrator...")
    agent = AgentOrchestrator(system_prompt, rag_system)
    print("✅ Agent Orchestrator listo\n")
    
    return agent


def save_metrics(result: dict):
    """Guarda métricas en JSON"""
    metrics_file = CONFIG["metrics_file"]
    os.makedirs(metrics_file.parent, exist_ok=True)
    
    # Prepare metrics record
    record = {
        "timestamp": datetime.now().isoformat(),
        "user_question": result["user_question"],
        "customer_email": result["customer_email"],
        "response": result["response"],
        "actions_count": len(result["actions_executed"]),
        "actions": [a.get("action") for a in result["actions_executed"]],
        "latency_ms": result["metrics"].get("latency_ms", 0),
        "tokens_prompt": result["metrics"]["tokens_prompt"],
        "tokens_completion": result["metrics"]["tokens_completion"],
        "total_tokens": result["metrics"]["total_tokens"],
        "estimated_cost_usd": result["metrics"]["estimated_cost_usd"],
        "tools_used": result["metrics"]["tools_used"]
    }
    
    # Load existing metrics
    metrics = []
    if metrics_file.exists():
        with open(metrics_file, 'r') as f:
            metrics = json.load(f)
    
    # Append new record
    metrics.append(record)
    
    # Save
    with open(metrics_file, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    print(f"✓ Métricas guardadas")


def display_result(result: dict):
    """Muestra el resultado de forma bonita"""
    print("\n" + "="*70)
    print("📋 RESULTADO FINAL (CON AGENT + FUNCTION CALLING)")
    print("="*70)
    
    output = {
        "response": result["response"],
        "actions_executed": result["actions_executed"],
        "actions_summary": [f"{a['action']}: {a.get('message', 'ejecutada')}" 
                           for a in result["actions_executed"]],
        "metrics": result["metrics"]
    }
    
    print(json.dumps(output, indent=2, ensure_ascii=False))
    print("="*70)


def run_support_query(question: str, customer_email: str = "support@company.com"):
    """
    Función principal: ejecuta el pipeline completo
    1. Carga prompt
    2. Inicializa RAG + Agents
    3. Procesa consulta con function calling
    4. Guarda métricas
    5. Muestra resultado
    """
    try:
        # Initialize systems
        agent = initialize_systems()
        
        print(f"🔄 Procesando pregunta: {question}")
        print(f"📧 Cliente: {customer_email}\n")
        
        # Process query with agent
        result = agent.process_query(question, customer_email)
        
        # Save metrics
        save_metrics(result)
        
        # Display result
        display_result(result)
        
    except ValueError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Get question from command line or use default
    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:])
    else:
        question = "¿Cuál es la política de reembolso?"
    
    run_support_query(question)
