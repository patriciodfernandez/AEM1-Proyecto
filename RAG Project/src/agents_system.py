"""
Agents System - Level 3
Sistema de herramientas que el LLM puede usar para tomar acciones.
Implementa 5 herramientas de soporte: tickets, escalamiento, callbacks, emails, reembolsos.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List


# ============================================================================
# HERRAMIENTAS DISPONIBLES PARA EL LLM
# ============================================================================

class AgentTools:
    """
    Conjunto de herramientas que el LLM puede usar.
    Cada herramienta retorna un resultado que se envía de vuelta al LLM.
    """

    def __init__(self):
        self.tickets_file = Path(__file__).parent.parent / "data" / "tickets.json"
        self.emails_file = Path(__file__).parent.parent / "data" / "emails_log.json"
        self.callbacks_file = Path(__file__).parent.parent / "data" / "callbacks.json"
        
        # Crear directorios si no existen
        self.tickets_file.parent.mkdir(exist_ok=True)
        
        # Inicializar archivos si no existen
        for f in [self.tickets_file, self.emails_file, self.callbacks_file]:
            if not f.exists():
                f.write_text(json.dumps([], indent=2))

    # ─────────────────────────────────────────────────────────────────────
    # HERRAMIENTA 1: CREATE SUPPORT TICKET
    # ─────────────────────────────────────────────────────────────────────
    
    def create_support_ticket(self, issue: str, priority: str = "medium", category: str = "general") -> Dict[str, Any]:
        """
        Crea un ticket de soporte en el sistema.
        
        Args:
            issue: Descripción del problema
            priority: Prioridad (low, medium, high)
            category: Categoría (general, technical, billing, account)
        
        Returns:
            Dict con ticket_id, status, message
        """
        try:
            # Validar prioridad
            if priority not in ["low", "medium", "high"]:
                return {
                    "success": False,
                    "error": f"Prioridad inválida: {priority}. Usa: low, medium, high"
                }
            
            # Generar ID único
            ticket_id = f"TKT-{uuid.uuid4().hex[:8].upper()}"
            
            # Crear registro
            ticket = {
                "ticket_id": ticket_id,
                "created_at": datetime.now().isoformat(),
                "issue": issue,
                "priority": priority,
                "category": category,
                "status": "open",
                "assigned_to": None
            }
            
            # Guardar
            with open(self.tickets_file) as f:
                tickets = json.load(f)
            tickets.append(ticket)
            with open(self.tickets_file, 'w') as f:
                json.dump(tickets, f, indent=2)
            
            return {
                "success": True,
                "ticket_id": ticket_id,
                "status": "open",
                "message": f"✅ Ticket creado: {ticket_id} (Prioridad: {priority})"
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ─────────────────────────────────────────────────────────────────────
    # HERRAMIENTA 2: ESCALATE
    # ─────────────────────────────────────────────────────────────────────
    
    def escalate_to_specialist(self, reason: str, department: str = "technical_support") -> Dict[str, Any]:
        """
        Escala el caso a un especialista.
        
        Args:
            reason: Razón de escalamiento
            department: Departamento (technical_support, billing, account_recovery, management)
        
        Returns:
            Dict con status de escalamiento
        """
        try:
            # Validar departamento
            valid_departments = ["technical_support", "billing", "account_recovery", "management"]
            if department not in valid_departments:
                return {
                    "success": False,
                    "error": f"Departamento inválido: {department}"
                }
            
            escalation = {
                "escalation_id": f"ESC-{uuid.uuid4().hex[:8].upper()}",
                "timestamp": datetime.now().isoformat(),
                "reason": reason,
                "department": department,
                "status": "pending_assignment"
            }
            
            return {
                "success": True,
                "escalation_id": escalation["escalation_id"],
                "message": f"⬆️ Caso escalado a: {department}",
                "reason": reason,
                "estimated_response_time": "15 minutos"
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ─────────────────────────────────────────────────────────────────────
    # HERRAMIENTA 3: SCHEDULE CALLBACK
    # ─────────────────────────────────────────────────────────────────────
    
    def schedule_callback(self, phone: str, preferred_time: str, customer_name: str = "Customer") -> Dict[str, Any]:
        """
        Agenda una llamada de callback.
        
        Args:
            phone: Teléfono del cliente (ej: "+1234567890")
            preferred_time: Hora preferida (ej: "14:30" o "Tomorrow 10:00")
            customer_name: Nombre del cliente
        
        Returns:
            Dict con confirmación de callback
        """
        try:
            # Validar formato de teléfono básico
            if not phone.startswith("+") and len(phone) < 10:
                return {
                    "success": False,
                    "error": "Formato de teléfono inválido. Usa +[país][número]"
                }
            
            # Crear callback
            callback = {
                "callback_id": f"CB-{uuid.uuid4().hex[:8].upper()}",
                "customer_name": customer_name,
                "phone": phone,
                "preferred_time": preferred_time,
                "scheduled_at": datetime.now().isoformat(),
                "status": "confirmed"
            }
            
            # Guardar
            with open(self.callbacks_file) as f:
                callbacks = json.load(f)
            callbacks.append(callback)
            with open(self.callbacks_file, 'w') as f:
                json.dump(callbacks, f, indent=2)
            
            return {
                "success": True,
                "callback_id": callback["callback_id"],
                "message": f"📞 Callback agendado para: {preferred_time}",
                "phone": phone,
                "confirmation_details": "Te llamaremos al número proporcionado. Confirma que esté disponible."
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ─────────────────────────────────────────────────────────────────────
    # HERRAMIENTA 4: SEND EMAIL
    # ─────────────────────────────────────────────────────────────────────
    
    def send_email(self, recipient: str, subject: str, template: str = "generic") -> Dict[str, Any]:
        """
        Envía un email al cliente.
        
        Args:
            recipient: Email del destinatario
            subject: Asunto del email
            template: Tipo de email (password_reset, refund_confirmation, ticket_created, general)
        
        Returns:
            Dict con confirmación de envío
        """
        try:
            # Validar email básico
            if "@" not in recipient or "." not in recipient.split("@")[-1]:
                return {
                    "success": False,
                    "error": "Dirección de email inválida"
                }
            
            # Validar template
            valid_templates = ["password_reset", "refund_confirmation", "ticket_created", "general"]
            if template not in valid_templates:
                template = "general"
            
            # Crear registro de email
            email_record = {
                "email_id": f"EMAIL-{uuid.uuid4().hex[:8].upper()}",
                "recipient": recipient,
                "subject": subject,
                "template": template,
                "sent_at": datetime.now().isoformat(),
                "status": "sent"
            }
            
            # Guardar
            with open(self.emails_file) as f:
                emails = json.load(f)
            emails.append(email_record)
            with open(self.emails_file, 'w') as f:
                json.dump(emails, f, indent=2)
            
            return {
                "success": True,
                "email_id": email_record["email_id"],
                "message": f"✉️ Email enviado a: {recipient}",
                "subject": subject,
                "template_used": template
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ─────────────────────────────────────────────────────────────────────
    # HERRAMIENTA 5: REFUND APPROVAL
    # ─────────────────────────────────────────────────────────────────────
    
    def approve_refund(self, reason: str, amount: float = None, days_since_purchase: int = None) -> Dict[str, Any]:
        """
        Aprueba un reembolso automáticamente si cumple criterios.
        
        Args:
            reason: Razón del reembolso (quality_issue, duplicate_charge, customer_request, etc)
            amount: Monto en USD. Si None, reembolso completo
            days_since_purchase: Días desde la compra
        
        Returns:
            Dict con aprobación o rechazo
        """
        try:
            # Validar criterios automáticos
            if days_since_purchase and days_since_purchase > 30:
                return {
                    "success": False,
                    "approved": False,
                    "message": "❌ Reembolso fuera del período (30 días)",
                    "reason": "Política de reembolso: máximo 30 días desde compra"
                }
            
            # Aprobación automática con criterios
            approval_status = "approved"
            if reason in ["customer_request", "duplicate_charge", "quality_issue"]:
                approval_status = "approved"
            elif reason == "special_case":
                approval_status = "pending_manager_review"
            
            refund_record = {
                "refund_id": f"REF-{uuid.uuid4().hex[:8].upper()}",
                "timestamp": datetime.now().isoformat(),
                "reason": reason,
                "amount": amount,
                "days_since_purchase": days_since_purchase,
                "status": approval_status,
                "processing_time": "3-5 días hábiles" if approval_status == "approved" else "pendiente"
            }
            
            if approval_status == "approved":
                return {
                    "success": True,
                    "approved": True,
                    "refund_id": refund_record["refund_id"],
                    "message": "✅ Reembolso aprobado automáticamente",
                    "amount": amount,
                    "processing_time": "3-5 días hábiles",
                    "details": f"Tu reembolso (${amount}) será procesado al método de pago original."
                }
            else:
                return {
                    "success": True,
                    "approved": False,
                    "refund_id": refund_record["refund_id"],
                    "message": "⏳ Reembolso requiere revisión de gerente",
                    "next_steps": "Un especialista contactará a breve"
                }
        
        except Exception as e:
            return {"success": False, "error": str(e)}


# ============================================================================
# DEFINICIÓN DE TOOLS PARA OPENAI API
# ============================================================================

def get_openai_tools_definition() -> List[Dict[str, Any]]:
    """
    Define las herramientas en formato OpenAI function calling.
    Se envía al modelo para que "conozca" qué puede hacer.
    """
    return [
        {
            "type": "function",
            "function": {
                "name": "create_support_ticket",
                "description": "Crea un nuevo ticket de soporte en el sistema. Úsalo cuando el cliente tiene un problema que requiere seguimiento.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "issue": {
                            "type": "string",
                            "description": "Descripción clara del problema del cliente"
                        },
                        "priority": {
                            "type": "string",
                            "enum": ["low", "medium", "high"],
                            "description": "Prioridad del ticket"
                        },
                        "category": {
                            "type": "string",
                            "enum": ["general", "technical", "billing", "account"],
                            "description": "Categoría del problema"
                        }
                    },
                    "required": ["issue", "priority"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "escalate_to_specialist",
                "description": "Escala el caso a un especialista de un departamento específico. Úsalo cuando el problema está fuera de tu alcance.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "reason": {
                            "type": "string",
                            "description": "Por qué necesita escalamiento"
                        },
                        "department": {
                            "type": "string",
                            "enum": ["technical_support", "billing", "account_recovery", "management"],
                            "description": "Departamento al que escalar"
                        }
                    },
                    "required": ["reason", "department"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "schedule_callback",
                "description": "Agenda una llamada de callback para que un especialista contacte al cliente. Úsalo cuando el cliente prefiere hablar por teléfono.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "phone": {
                            "type": "string",
                            "description": "Número de teléfono en formato +[país][número]"
                        },
                        "preferred_time": {
                            "type": "string",
                            "description": "Hora/fecha preferida (ej: 'Tomorrow 14:00', 'Today 10:30')"
                        },
                        "customer_name": {
                            "type": "string",
                            "description": "Nombre del cliente"
                        }
                    },
                    "required": ["phone", "preferred_time"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "send_email",
                "description": "Envía un email al cliente con instrucciones o confirmaciones. Úsalo para comunicar soluciones por email.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "recipient": {
                            "type": "string",
                            "description": "Dirección de email del destinatario"
                        },
                        "subject": {
                            "type": "string",
                            "description": "Asunto del email"
                        },
                        "template": {
                            "type": "string",
                            "enum": ["password_reset", "refund_confirmation", "ticket_created", "general"],
                            "description": "Tipo de email a enviar"
                        }
                    },
                    "required": ["recipient", "subject"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "approve_refund",
                "description": "Aprueba automáticamente un reembolso si cumple con los criterios. Úsalo cuando el cliente solicita un reembolso válido.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "reason": {
                            "type": "string",
                            "enum": ["quality_issue", "duplicate_charge", "customer_request", "special_case"],
                            "description": "Razón del reembolso"
                        },
                        "amount": {
                            "type": "number",
                            "description": "Monto en USD. Si no se proporciona, reembolso completo"
                        },
                        "days_since_purchase": {
                            "type": "integer",
                            "description": "Días desde la compra (máximo 30 para aprobación automática)"
                        }
                    },
                    "required": ["reason"]
                }
            }
        }
    ]


# ============================================================================
# FUNCIÓN PARA PROCESAR TOOL CALLS
# ============================================================================

def execute_tool_call(tool_name: str, tool_input: Dict[str, Any], agent_tools: AgentTools) -> Dict[str, Any]:
    """
    Ejecuta una herramienta llamada por el LLM.
    
    Args:
        tool_name: Nombre de la herramienta a ejecutar
        tool_input: Argumentos para la herramienta
        agent_tools: Instancia de AgentTools
    
    Returns:
        Resultado de la ejecución
    """
    
    if tool_name == "create_support_ticket":
        return agent_tools.create_support_ticket(**tool_input)
    
    elif tool_name == "escalate_to_specialist":
        return agent_tools.escalate_to_specialist(**tool_input)
    
    elif tool_name == "schedule_callback":
        return agent_tools.schedule_callback(**tool_input)
    
    elif tool_name == "send_email":
        return agent_tools.send_email(**tool_input)
    
    elif tool_name == "approve_refund":
        return agent_tools.approve_refund(**tool_input)
    
    else:
        return {"success": False, "error": f"Herramienta desconocida: {tool_name}"}
