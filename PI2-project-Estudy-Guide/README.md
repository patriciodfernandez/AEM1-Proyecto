# PI2 Project - Study Guide: Level 3 AGENTS

**Sistema de Soporte Inteligente con Agents y Function Calling**

## 📊 Niveles del Proyecto

```
Level 1: Prompt Engineering + Few-Shot
  → Respuestas clasificadas con confianza

Level 2: RAG (Retrieval-Augmented Generation)
  → Respuestas con contexto de documentos internos

Level 3: AGENTS + Function Calling (ESTE)
  → Respuestas + Acciones automáticas (tickets, escalaciones, reembolsos, etc)
```

## 🎯 Objetivo de Level 3

El agent no solo responde preguntas. Puede **ejecutar acciones automáticas**:

- ✅ **Crear tickets de soporte** - Para problemas que necesitan seguimiento
- ✅ **Escalar a especialistas** - Para problemas fuera de alcance
- ✅ **Agendar llamadas** - Para clientes que prefieren hablar
- ✅ **Enviar emails** - Confirmaciones e instrucciones
- ✅ **Autorizar reembolsos** - Aprobaciones automáticas

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────────────────┐
│ Usuario pregunta: "Compré hace 2 semanas, cambié idea"  │
└──────────────────────┬──────────────────────────────────┘
                       ↓
        ┌──────────────────────────────┐
        │ 1. RAG System                │
        │    (Recupera documentos)     │
        └────────────┬─────────────────┘
                     ↓
        ┌──────────────────────────────┐
        │ 2. Agent Orchestrator        │
        │    (Procesa con contexto)    │
        └────────────┬─────────────────┘
                     ↓
        ┌──────────────────────────────┐
        │ 3. OpenAI Function Calling   │
        │    (decide qué acción usar)  │
        └────────────┬─────────────────┘
                     ↓
        ┌──────────────────────────────┐
        │ 4. ActionExecutor            │
        │ - create_ticket             │
        │ - escalate                  │
        │ - schedule_callback         │
        │ - send_email                │
        │ - approve_refund            │
        └────────────┬─────────────────┘
                     ↓
    ┌────────────────────────────────────┐
    │ Acción ejecutada + Respuesta       │
    │ "Reembolso aprobado #REF-123"      │
    │ Email de confirmación enviado      │
    └────────────────────────────────────┘
```

## 📁 Estructura del Proyecto

```
PI2-project-Estudy-Guide/
├── src/
│   ├── run_query.py          ← Punto de entrada
│   ├── rag_system.py         ← Sistema RAG
│   └── agents_system.py      ← Sistema de Agents con function calling
├── prompts/
│   └── main_prompt.txt       ← Prompt con definición de herramientas
├── knowledge_base/
│   ├── politica_reembolso.txt
│   ├── faq_tecnica.txt
│   └── guia_instalacion.txt
├── metrics/
│   └── metrics.json          ← Historial de ejecuciones
├── vector_store/
│   └── embeddings.json       ← Embeddings cacheados
├── actions_log/
│   └── actions.json          ← Log de acciones ejecutadas
├── tests/
│   └── ...
├── .env                      ← API key (crear localmente)
└── README.md
```

## 🚀 Uso Rápido

### 1. Setup

```powershell
cd "c:\Users\pa7o_\Desktop\AI ENGINEER\AEM1-Proyecto\PI2-project-Estudy-Guide"
```

### 2. Ejecutar con pregunta específica

```powershell
python src/run_query.py "¿Cuál es la política de reembolso?"
```

### 3. Ejemplos que disparan acciones:

```powershell
# Ejemplo 1: Problema que genera ticket
python src/run_query.py "Llevo 3 días sin poder entrar a mi cuenta"

# Ejemplo 2: Reembolso automático
python src/run_query.py "Compré hace 1 semana, cambié de opinión"

# Ejemplo 3: Problema técnico con escalación
python src/run_query.py "Mi app no funciona desde hace 2 horas, es crítico"
```

## 📊 Métricas Capturadas

Cada ejecución registra:

```json
{
  "timestamp": "2026-03-02T12:34:56",
  "user_question": "...",
  "response": "...",
  "actions_executed": [
    {
      "action": "approve_refund",
      "refund_id": "REF-20260302123456",
      "amount": 49.99,
      "message": "Reembolso aprobado"
    }
  ],
  "tokens_prompt": 1290,
  "tokens_completion": 150,
  "total_tokens": 1440,
  "estimated_cost_usd": 0.000324,
  "tools_used": 1
}
```

## 🔧 Herramientas Disponibles

### 1. `create_support_ticket`
**Cuándo:** Problema complejo que necesita seguimiento
**Parámetros:**
- `issue`: Descripción del problema
- `priority`: "low" | "medium" | "high"
- `customer_email`: Email para contacto

**Ejemplo:**
```python
{
  "action": "create_support_ticket",
  "params": {
    "issue": "Usuario no puede acceder desde 3 días",
    "priority": "high",
    "customer_email": "cliente@example.com"
  }
}
```

### 2. `escalate_to_specialist`
**Cuándo:** Problema fuera del alcance del agent
**Parámetros:**
- `reason`: Por qué escalar
- `team`: "technical" | "billing" | "legal"

### 3. `schedule_callback`
**Cuándo:** Cliente prefiere hablar por teléfono
**Parámetros:**
- `customer_phone`: Número de teléfono
- `preferred_time`: HH:MM
- `timezone`: UTC | EST | PST | CST

### 4. `send_notification_email`
**Cuándo:** Enviar instrucciones o confirmaciones
**Parámetros:**
- `email`: Destinatario
- `subject`: Asunto
- `body`: Contenido

### 5. `approve_refund`
**Cuándo:** Cliente cumple criterios de reembolso
**Parámetros:**
- `customer_id`: ID único
- `refund_amount`: Monto USD
- `reason`: Justificación

## 📈 Comparativa: Level 1 vs 2 vs 3

| Aspecto | Level 1 | Level 2 | Level 3 |
|---------|---------|---------|---------|
| **Respuesta** | Genérica | Con contexto | +Acciones auto |
| **Tokens** | ~787 | ~1290 | ~1440 |
| **Latencia** | 3.4 sec | 2.5 sec | 3.2 sec (más acciones) |
| **Costo** | $0.0002 | $0.000315 | $0.000324 |
| **Ejemplos** | Preguntas simples | Políticas | Problemas complejos |
| **Alcance** | 40% problemas | 70% problemas | 95% problemas |

## 🧪 Testing

```powershell
python tests/simple_tests.py
```

Tests incluyen:
- Prompt loading
- JSON validation
- Function call validation  
- Metrics calculation
- Action execution logging

## 📚 Conceptos Clave

### Function Calling
El LLM no solo genera texto. Dado un set de herramientas, **decide cuáles usar**:

```
Sistema: "Aquí tienes estas herramientas: [tool1, tool2, tool3]"
LLM procesa: "Para esta pregunta, necesito usar tool2"
Resultado: LLM retorna {tool_name: "tool2", arguments: {...}}
```

### Action Execution
Una vez el LLM elige la acción, nosotros la **ejecutamos realmente**:

```python
# El LLM dijo: "Debes crear un ticket"
# Nosotros ejecutamos:
action_result = executor.execute_action("create_support_ticket", {
    "issue": "...",
    "priority": "high",
    "customer_email": "..."
})
# Resultado: ticket_id = "TKT-20260302123456"
```

### Action Logging
Todas las acciones se registran para auditoría:

```json
{
  "action": "create_support_ticket",
  "ticket_id": "TKT-20260302123456",
  "timestamp": "2026-03-02T12:34:56",
  "status": "success",
  "message": "Ticket TKT-20260302123456 creado"
}
```

## 🎓 Lecciones Aprendidas

1. **Function Calling es poder:** El LLM decide no solo QUÉ decir, sino QUÉ HACER
2. **RAG + Agents = Máxima efectividad:** Contexto + Acción = Problemas resueltos
3. **Las herramientas deben ser claras:** El LLM solo usa lo que entiende
4. **Logging es crítical:** Necesitas auditoría de TODAS las acciones
5. **Métri

cas definen éxito:** Tokens, costo, tools usados = ROI medible

## ❓ FAQ

**P: ¿El agent realmente crea tickets?**
R: En producción sí. Aquí simula en `actions_log/`.

**P: ¿El reembolso se procesa?**
R: En producción sí. Aquí registra en `actions_log/`.

**P: ¿Puedo agregar más herramientas?**
R: Sí, en `agents_system.py` agrega a `get_tools_definitions()` y `execute_action()`.

**P: ¿Cómo diferencio Level 2 vs Level 3?**
R: Level 2 usa RAG. Level 3 agrega function calling (ejecuta acciones).

---

**Creado con 💡 por tu tutor de AI Engineering**
