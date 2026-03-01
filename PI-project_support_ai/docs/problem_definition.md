# Definición del Problema - Support AI Query

**Proyecto:** Support AI Query
**Fecha:** Marzo 1, 2026
**Fase:** Pasos 1-5 del Flujo de AI Engineering
**Versión:** 1.0

---

## 📋 PASO 1: TRADUCIR EL PROBLEMA DE NEGOCIO EN TAREA DE IA

---

## 🏢 PROBLEMA DE NEGOCIO

### Contexto
Un equipo de soporte técnico en una empresa SaaS experimenta un problema crítico:

**Situación Actual:**
- Alto volumen de tickets de soporte (~100/día)
- Agentes de soporte tardan **en promedio 4 horas** en redactar primera respuesta
- Clientes esperan largo time antes de recibir cualquier comunicación
- Esto afecta **CSAT (Customer Satisfaction) score**

### Impacto Financiero
```
Métrica Actual:
- Tiempo de Primera Respuesta (FRT): 4 horas
- Resolución al Primer Contacto (FCR): 60%
- Costo operativo por ticket: ~$15 en horas de agente

Impacto:
- Clientes insatisfechos → Churn
- Operaciones ineficientes
- Crecimiento limitado
```

### Pregunta Clave
> "¿Cómo podemos reducir significativamente el tiempo de primera respuesta mientras mantenemos calidad?"

---

## 🤖 TAREA DE IA (TRADUCCIÓN)

Convertimos el problema vago en una **tarea de IA clara y medible**:

### Definición de la Tarea

```
NOMBRE: Support AI Query Engine
==================================

ENTRADA:
  - Una pregunta de un cliente sobre soporte técnico
  - Texto libre, sin límite de tamaño (con validación)

SALIDA:
  - Respuesta concisa y útil
  - Estimación de confianza (ALTA/MEDIA/BAJA)
  - Acciones recomendadas para el agente
  - Formato: JSON estructurado

CRITERIOS DE CALIDAD:
  ✓ Respuesta es relevante para la pregunta (>80% casos comunes)
  ✓ Confianza correlaciona con corrección (validado por agente)
  ✓ JSON siempre válido y parseable
  ✓ Latencia < 5 segundos
  ✓ Costo < $0.01 por llamada
```

### Descomposición de Tareas

La tarea principal se compone de **3 sub-tareas**:

| Sub-tarea | Tipo | Entrada | Salida |
|-----------|------|---------|--------|
| **1. Generar Respuesta** | Generación | Pregunta | Respuesta útil (300 chars max) |
| **2. Estimar Confianza** | Clasificación | Respuesta + Contexto | ALTA/MEDIA/BAJA |
| **3. Sugerir Acciones** | Recomendación | Confianza + Contexto | ["respond_to_customer", "escalate", ...] |

---

## 🎯 CRITERIOS DE ÉXITO

### Métricas de Negocio (KPIs)

| KPI | Línea Base | Objetivo | Impacto |
|-----|-----------|----------|--------|
| Tiempo Primera Respuesta | 4 horas | 15 min | -93.75% |
| Resolución Primer Contacto | 60% | 75% | +15% |
| Costo por Respuesta | - | $0.0002 | Rentable |
| CSAT Score | 65% | 85% | +20% |

### Métricas Técnicas

| Métrica | Umbral | Justificación |
|---------|--------|---------------|
| JSON Válido | 100% | Contrato con sistemas downstream |
| Latencia | < 5 seg | Experiencia de usuario aceptable |
| Costo | < $0.01 | Presupuesto operativo viable |
| Confianza válida | 100% (ALTA/MEDIA/BAJA) | Restricción de negocio |

---

## 🔄 LIMITACIONES Y ALCANCE

### Alcance (QUÉ HACEMOS)
✅ Generar respuesta inicial automática
✅ Estimar confianza
✅ Sugerir acciones (responder/escalar)
✅ Registrar métricas

### Fuera de Alcance (QUÉ NO HACEMOS)
❌ Acceso a datos históricos del cliente
❌ Integración con base de datos de tickets (V2)
❌ Envío automático de respuesta (requiere aprobación humana)
❌ Resolución de problemas complejos multi-paso (V2)

### Restricciones Iniciales
- Solo soporte en **texto**, no imágenes/archivos
- Solo **problemas de soporte común** (preguntas FAQ)
- Requiere **validación humana** antes de enviar al cliente
- **No** información customer-specific (privacidad)

---

## 🏗️ SOLUCIÓN PROPUESTA

### Enfoque Alto Nivel

```
Usuario pregunta
       ↓
Load Prompt (System + Instructions + Examples)
       ↓
OpenAI API (gpt-4o-mini)
       ↓
Validar JSON + Campos + Valores
       ↓
Calcular Métricas (tokens, latencia, costo)
       ↓
Guardar en Histórico
       ↓
Retornar JSON al Sistema
```

### Por qué este enfoque

| Aspecto | Decisión | Razón |
|---------|----------|-------|
| **Modelo** | gpt-4o-mini | Bajo costo ($0.0002), latencia aceptable, suficientemente potente |
| **Prompt Engineering** | Few-Shot | Ejemplos claros → respuestas consistentes, bajo costo |
| **Validación** | Strict JSON | Previene errores en sistemas downstream |
| **Métricas** | Registro completo | Detecta problemas, analiza costos |

---

## 📊 PASO 2: SELECCIÓN DE MODELO

### Análisis de Opciones

#### Opción 1: gpt-4o-mini ✅ ELEGIDO

```
Características:
  - Costo: $0.0002 por llamada
  - Latencia: ~3.4 seg
  - Calidad: Buena para tareas simples
  - Tokens: ~789 totales promedio

Pros:
  ✅ Económico (sostenible a escala)
  ✅ Rápido (aceptable para UX)
  ✅ Suficientemente poderoso
  ✅ Perfecto para MVP

Cons:
  ⚠️ Puede alucinar ocasionalmente
  ⚠️ Menos confiable que GPT-4

Recomendación: USAR para producción inicial
Upgrade path: Si necesitamos mejor calidad, cambiar a gpt-4o
```

#### Opción 2: gpt-4o (fallback)

```
Características:
  - Costo: $0.001 por llamada (5x caro)
  - Latencia: ~2.5 seg (más rápido)
  - Calidad: Excelente
  - Tokens: ~850 típicos

Cuándo considerar:
  - Si gpt-4o-mini tiene tasa de error > 20%
  - Si latencia debe ser < 2 seg
  - En fase de escalamiento

Upgrade strategy:
  Mismo código, solo cambiar:
  model="gpt-4o"  # En lugar de gpt-4o-mini
```

---

## 💬 PASO 3: PROMPT ENGINEERING

### Técnica Elegida: FEW-SHOT

#### Justificación

| Criterio | Few-Shot | CoT | Self-Consistency | Winner |
|----------|----------|-----|------------------|--------|
| Tokens | 787 | 1200+ | 2500+ | **Few-Shot** |
| Costo | $0.0002 | $0.0003 | $0.0006 | **Few-Shot** |
| Tarea | Generación + Clasificación simple | - | - | **Few-Shot** |
| Setup | Simple | Intermedio | Complejo | **Few-Shot** |

#### Estructura del Prompt

```
1. SYSTEM PROMPT (Rol)
   → "Eres experto de soporte con 10 años experiencia"
   
2. INSTRUCCIONES (Criterios)
   → "ALTA: 80%+ seguro"
   → "MEDIA: 50-79%"
   → "BAJA: <50%"
   
3. FORMATO (Schema)
   → {"response": "...", "confidence": "...", ...}
   
4. EJEMPLOS (Few-Shot: 3 casos)
   → Caso 1: Problema común (solución directa)
   → Caso 2: Info con incertidumbre (necesita validación)
   → Caso 3: Escalamiento (cliente molesto)
```

---

## 🔧 PASO 4: INTEGRACIÓN

### Arquitectura de Componentes

```
┌─────────────────┐
│   Entrada       │ "Mi contraseña..."
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│ run_query.py            │
│ - load_prompt()         │
│ - call_openai_api()     │
│ - validate_response()   │
│ - calculate_cost()      │
│ - save_metrics()        │
└────────┬────────────────┘
         │
         ▼
┌──────────────────────────┐
│     JSON Estructurado    │
│ {                        │
│   response: "...",       │
│   confidence: "ALTA",    │
│   actions: [...],        │
│   metrics: {...}         │
│ }                        │
└──────────────────────────┘
```

---

## 📊 PASO 5: MÉTRICAS Y MONITOREO

### Métricas Registradas

Cada ejecución captura:

```json
{
  "timestamp": "2026-03-01T19:24:23",
  "user_question": "Mi contraseña...",
  "confidence_returned": "ALTA",
  "latency_ms": 3374.98,
  "tokens_prompt": 787,
  "tokens_completion": 102,
  "total_tokens": 889,
  "estimated_cost_usd": 0.0002
}
```

### Análisis de Datos

**Agregación por período:**

```python
# Latencia promedio
avg_latency = numpy.mean([m["latency_ms"] for m in metrics])

# Costo total
total_cost = sum([m["estimated_cost_usd"] for m in metrics])

# Distribución de confianza
confidences = {
    "ALTA": len([m for m in metrics if m["confidence_returned"] == "ALTA"]),
    "MEDIA": len([m for m in metrics if m["confidence_returned"] == "MEDIA"]),
    "BAJA": len([m for m in metrics if m["confidence_returned"] == "BAJA"])
}
```

### Alertas Recomendadas

| Condición | Acción |
|-----------|--------|
| Costo diario > $50 | Revisar volumen, considerar rate limiting |
| Latencia promedio > 5 seg | Checklist: API congestión, modelo, red |
| Confianza BAJA > 30% | Revisar prompt, posibles alucinaciones |
| JSON inválido > 5% | Fallback a template, revisar validación |

---

## ✅ VALIDACIÓN

### Tests Automatizados (7 suites)

```
TEST 1: Prompt Loading              ✅ 
TEST 2: JSON Validation             ✅
TEST 3: Confidence Values           ✅
TEST 4: Cost Calculation            ✅
TEST 5: Required Fields             ✅
TEST 6: Actions Validation          ✅
TEST 7: Metrics Validation          ✅

RESULTADO: 7/7 PASARON (100%)
```

---

## 🎓 MATRIZ DE DECISIONES

### Decisión 1: Modelo

| Factor | gpt-4o-mini | Decisión |
|--------|------------|----------|
| Costo | $0.0002/llamada | ✅ ELEGIDO (sostenible) |
| Latencia | 3.4 seg | ✅ OK para soporte async |
| Calidad | Buena | ✅ Suficiente MVP |

**Conclusión:** gpt-4o-mini. Upgrade a gpt-4o si calidad insuficiente.

### Decisión 2: Prompt Technique

| Técnica | Tokens | Costo | Decisión |
|---------|--------|-------|----------|
| Few-Shot | 787 | $0.0002 | ✅ ELEGIDO |
| CoT | 1200+ | $0.0003 | ❌ Overkill |

**Conclusión:** Few-Shot. Simple, efectivo, económico.

### Decisión 3: Validación

| Nivel | Beneficio | Costo | Decisión |
|-------|-----------|--------|----------|
| Strict (actual) | Previene errores | Negligente | ✅ HACER |
| None | Rápido | Crashes | ❌ NO HACER |

**Conclusión:** Validación estricta. Mejor prevenir que debuguear.

---

## 🚀 IMPLEMENTACIÓN

### Timeline

```
Semana 1: Diseño (Pasos 1-3)
  - Definir tarea
  - Seleccionar modelo
  - Diseñar prompt

Semana 2: Construcción (Pasos 4-5)
  - Integración código
  - Métricas
  - Tests

Semana 3: Validación
  - Testing con usuarios
  - Ajustes de prompt
  - Documentación
```

### Entregables

| Entregable | Responsable | Deadline |
|-----------|------------|----------|
| Script ejecutable (run_query.py) | Dev | +2 sem |
| Tests (7/7 pasando) | QA | +2 sem |
| Documentación | Tech Writer | +3 sem |
| Reporte técnico | PM | +3 sem |

---

## 📝 CONCLUSIÓN

```
TAREA DE IA BIEN DEFINIDA:
  Input:  Pregunta de soporte
  Output: JSON con respuesta, confianza, acciones + métricas
  Modelo: gpt-4o-mini (costo-efectivo)
  Técnica: Few-Shot (simple y efectivo)
  Validación: Strict (previene errores)
  Impacto: -93.75% en FRT, +15% en FCR

PRÓXIMO PASO: Paso 4 - Integración (código)
```

---

**Documento:** Definición del Problema
**Versión:** 1.0
**Autor:** AI Engineer en Capacitación
**Fecha:** Marzo 1, 2026
