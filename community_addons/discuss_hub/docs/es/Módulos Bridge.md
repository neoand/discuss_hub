# Módulos Bridge - Integración con Aplicaciones Odoo 🔗

> **Guía completa para integrar DiscussHub con CRM, Helpdesk, Project y módulos personalizados**

[🇺🇸 English](../en/Bridge%20Modules.md) | [🇧🇷 Português](../pt-br/Módulos%20Bridge.md) | **🇪🇸 Español**

---

## 📋 Índice

- [Visión General](#visión-general)
- [DiscussHub Mixin](#discusshub-mixin)
- [Módulo CRM](#módulo-crm-discusshub_crm)
- [Módulo Helpdesk](#módulo-helpdesk-discusshub_helpdesk)
- [Módulo Project](#módulo-project-discusshub_project)
- [Crear Tu Propio Bridge](#crear-tu-propio-bridge)
- [Ejemplos Prácticos](#ejemplos-prácticos)

---

## 📖 Visión General

Los **Módulos Bridge** son extensiones que conectan aplicaciones Odoo existentes (CRM, Helpdesk, Project, etc.) con DiscussHub, permitiendo comunicación vía WhatsApp y otros canales directamente desde los registros.

### ✨ ¿Qué Son los Módulos Bridge?

Módulos que extienden aplicaciones Odoo existentes añadiendo:
- Campo para vincular canal WhatsApp
- Contadores de mensajes
- Botones de acción para enviar mensajes
- Historial de conversaciones integrado

### 🎯 Beneficios

- **Contexto Completo**: Ver conversaciones WhatsApp dentro del contexto de Leads, Tickets o Tareas
- **Comunicación Rápida**: Un clic para abrir conversación con cliente
- **Historial Centralizado**: Todos los mensajes grabados en Odoo
- **Automatización**: Triggers basados en eventos (cambios de etapa, etc.)

---

## 🧩 DiscussHub Mixin

El **`discusshub.mixin`** es un modelo abstracto que proporciona funcionalidad lista para usar para añadir mensajería a cualquier modelo Odoo.

### 📦 Lo Que Añade el Mixin

#### Campos Automáticos

```python
# Campo de relación
discusshub_channel_id = fields.Many2one('discuss.channel')
# Enlace al canal WhatsApp/Telegram vinculado a este registro

# Campos computados
discusshub_message_count = fields.Integer(compute='_compute_discusshub_message_count')
# Número de mensajes en el canal vinculado

discusshub_last_message_date = fields.Datetime(compute='_compute_discusshub_message_count')
# Fecha del último mensaje recibido/enviado
```

#### Métodos Automáticos

```python
# Abrir conversación para enviar mensaje
record.action_send_discusshub_message()

# Crear y vincular nuevo canal WhatsApp
record.action_create_discusshub_channel()

# Abrir canal existente
record.action_open_discusshub_channel()
```

#### Métodos Helper (Para Sobrescribir)

```python
# Obtener número de teléfono del registro
def _get_discusshub_destination(self):
    """Devuelve número en formato '5511999999999'"""

# Obtener nombre del canal
def _get_discusshub_channel_name(self):
    """Devuelve nombre como 'WhatsApp: Lead - Cliente XYZ'"""
```

---

## 📦 Módulos Disponibles

### 🎯 Integración CRM (`discusshub_crm`)

**Ubicación**: `community_addons/discusshub_crm/`
**Líneas de Código**: ~450 LOC
**Estado**: ✅ Producción

#### Características

- Vincular canales WhatsApp a Leads y Oportunidades
- Enviar mensajes directamente desde el formulario de Lead
- Rastrear historial de conversaciones
- Auto-detectar teléfono (partner o campos de lead)
- Nomenclatura basada en etapa de lead

#### Uso Básico

```python
# Obtener lead
lead = env['crm.lead'].browse(1)

# Crear canal WhatsApp para lead
lead.action_create_discusshub_channel()
# Esto crea automáticamente un canal vinculado al teléfono del partner

# Enviar mensaje
lead.action_send_discusshub_message()
# Abre el canal para enviar mensaje

# Acceder información
print(lead.discusshub_message_count)      # Ej: 15 mensajes
print(lead.discusshub_last_message_date)  # Ej: 2025-10-17 14:30:00
```

#### Personalización

```python
# Sobrescribir nomenclatura del canal
class Lead(models.Model):
    _inherit = 'crm.lead'

    def _get_discusshub_channel_name(self):
        """Nombre personalizado basado en etapa"""
        stage = self.stage_id.name if self.stage_id else 'Nuevo'
        return f"WhatsApp: [{stage}] {self.name}"

    def _get_discusshub_destination(self):
        """Priorizar móvil del partner"""
        if self.partner_id and self.partner_id.mobile:
            return self.partner_id.mobile
        elif self.phone:
            return self.phone
        return super()._get_discusshub_destination()
```

---

### 🎫 Integración Helpdesk (`discusshub_helpdesk`)

**Ubicación**: `community_addons/discusshub_helpdesk/`
**Líneas de Código**: ~200 LOC
**Estado**: ✅ Producción

#### Características

- Vincular canales WhatsApp a tickets de soporte
- Responder a clientes vía WhatsApp desde formulario de ticket
- Rastrear conversaciones de soporte
- Auto-detectar teléfono del cliente
- Integración con SLA y prioridades

#### Uso Básico

```python
# Obtener ticket
ticket = env['helpdesk.ticket'].browse(1)

# Crear canal WhatsApp
ticket.action_create_discusshub_channel()

# Enviar mensaje al cliente
ticket.action_send_discusshub_message()

# Acceder estadísticas
print(f"Mensajes: {ticket.discusshub_message_count}")
print(f"Último mensaje: {ticket.discusshub_last_message_date}")
```

#### Caso de Uso: Atención al Cliente

```python
# Cuando se crea ticket, crear canal automáticamente
class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    @api.model_create_multi
    def create(self, vals_list):
        tickets = super().create(vals_list)

        for ticket in tickets:
            # Si cliente tiene WhatsApp, crear canal
            if ticket.partner_id and (ticket.partner_id.mobile or ticket.partner_id.phone):
                try:
                    ticket.action_create_discusshub_channel()
                except Exception as e:
                    _logger.warning(f"No se pudo crear canal WhatsApp: {e}")

        return tickets
```

#### Automatización de Mensajes

```python
# Enviar mensaje automático cuando ticket se resuelve
class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    def write(self, vals):
        result = super().write(vals)

        # Si cambió a etapa "Resuelto"
        if vals.get('stage_id'):
            stage = self.env['helpdesk.stage'].browse(vals['stage_id'])
            if stage.is_close:
                self._send_resolution_message()

        return result

    def _send_resolution_message(self):
        """Envía mensaje de ticket resuelto"""
        if not self.discusshub_channel_id:
            return

        message = f"""
🎉 *Ticket Resuelto!*

Hola {self.partner_id.name},

Tu ticket *{self.name}* ha sido resuelto exitosamente.

Si tienes más preguntas, estamos aquí para ayudarte.

Saludos,
{self.env.company.name}
        """

        self.discusshub_channel_id.message_post(
            body=message,
            message_type='comment',
        )
```

---

### 📋 Integración Project (`discusshub_project`)

**Ubicación**: `community_addons/discusshub_project/`
**Líneas de Código**: ~150 LOC
**Estado**: ✅ Producción

#### Características

- Vincular canales WhatsApp a tareas de proyecto
- Comunicar con clientes sobre progreso de tareas
- Rastrear conversaciones relacionadas con tareas
- Notificaciones para asignados/seguidores
- Actualizaciones de estado vía WhatsApp

#### Uso Básico

```python
# Obtener tarea
task = env['project.task'].browse(1)

# Crear canal WhatsApp
task.action_create_discusshub_channel()

# Enviar actualización al cliente
task.action_send_discusshub_message()
```

#### Caso de Uso: Actualizaciones de Progreso

```python
class ProjectTask(models.Model):
    _inherit = 'project.task'

    def write(self, vals):
        result = super().write(vals)

        # Notificar cliente cuando tarea se completa
        if vals.get('stage_id'):
            stage = self.env['project.task.type'].browse(vals['stage_id'])
            if stage.fold:  # Etapa final
                self._notify_task_completion()

        return result

    def _notify_task_completion(self):
        """Notifica cliente vía WhatsApp"""
        if not self.discusshub_channel_id:
            return

        message = f"""
🎉 *Tarea Completada!*

Hola {self.partner_id.name},

La tarea *{self.name}* ha sido completada exitosamente!

📋 *Detalles:*
- Proyecto: {self.project_id.name}
- Responsable: {self.user_ids[0].name if self.user_ids else 'N/A'}
- Fecha de finalización: {fields.Date.today()}

Si tienes alguna pregunta, estamos para ayudarte!

Saludos,
{self.env.company.name}
        """

        self.discusshub_channel_id.message_post(
            body=message,
            message_type='comment',
        )
```

---

## 🛠️ Crear Tu Propio Bridge

Sigue esta guía para integrar DiscussHub con cualquier módulo Odoo.

### Paso 1: Estructura del Módulo

```bash
mkdir community_addons/discusshub_custom
cd community_addons/discusshub_custom

# Crear estructura
mkdir models views
touch __init__.py __manifest__.py README.md
touch models/__init__.py models/custom_model.py
touch views/custom_model_views.xml
```

### Paso 2: Manifiesto (`__manifest__.py`)

```python
{
    'name': 'DiscussHub Custom Integration',
    'version': '18.0.1.0.0',
    'category': 'Discuss',
    'summary': 'Integrar DiscussHub con Módulo Personalizado',
    'depends': [
        'discuss_hub',           # Módulo base DiscussHub
        'your_custom_module',    # Tu módulo a integrar
    ],
    'data': [
        'views/custom_model_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'AGPL-3',
}
```

### Paso 3: Modelo (`models/custom_model.py`)

```python
from odoo import models, api

class CustomModel(models.Model):
    _name = 'your.custom.model'
    _inherit = ['your.custom.model', 'discusshub.mixin']

    # ¡Listo! Tu modelo ahora tiene todos los campos y métodos del mixin

    # (Opcional) Personalizar detección de teléfono
    def _get_discusshub_destination(self):
        """Obtener teléfono personalizado"""
        if self.custom_phone_field:
            return self.custom_phone_field
        return super()._get_discusshub_destination()

    # (Opcional) Personalizar nombre del canal
    def _get_discusshub_channel_name(self):
        """Nombre personalizado del canal"""
        return f"WhatsApp: {self.name} - {self.state}"
```

### Paso 4: Vista (`views/custom_model_views.xml`)

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <record id="view_custom_model_form_inherit_discusshub" model="ir.ui.view">
        <field name="name">your.custom.model.form.inherit.discusshub</field>
        <field name="model">your.custom.model</field>
        <field name="inherit_id" ref="your_module.view_custom_model_form"/>
        <field name="arch" type="xml">

            <!-- Añadir botones en button_box -->
            <xpath expr="//div[@name='button_box']" position="inside">

                <!-- Botón: Crear Canal -->
                <button name="action_create_discusshub_channel"
                        type="object"
                        class="oe_stat_button"
                        icon="fa-whatsapp"
                        attrs="{'invisible': [('discusshub_channel_id', '!=', False)]}">
                    <div class="o_field_widget o_stat_info">
                        <span class="o_stat_text">Crear</span>
                        <span class="o_stat_text">WhatsApp</span>
                    </div>
                </button>

                <!-- Botón: Abrir Canal (con contador) -->
                <button name="action_open_discusshub_channel"
                        type="object"
                        class="oe_stat_button"
                        icon="fa-whatsapp"
                        attrs="{'invisible': [('discusshub_channel_id', '=', False)]}">
                    <field name="discusshub_message_count"
                           widget="statinfo"
                           string="Mensajes"/>
                </button>

            </xpath>

        </field>
    </record>
</odoo>
```

---

## 💡 Ejemplos Prácticos

### Ejemplo 1: Auto-crear Canal al Crear Registro

```python
class CustomModel(models.Model):
    _inherit = 'your.custom.model'

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)

        for record in records:
            # Si tiene partner con teléfono, crear canal automáticamente
            if record.partner_id and record.partner_id.mobile:
                record.action_create_discusshub_channel()

        return records
```

### Ejemplo 2: Enviar Mensaje Automático en Evento

```python
class CustomModel(models.Model):
    _inherit = 'your.custom.model'

    def action_confirm(self):
        """Al confirmar, envía mensaje vía WhatsApp"""
        result = super().action_confirm()

        for record in self:
            if record.discusshub_channel_id:
                message = f"""
Hola {record.partner_id.name}!

Tu solicitud *{record.name}* ha sido confirmada.

Estado: ✅ Confirmado
Fecha: {fields.Date.today()}

¡Gracias!
                """
                record.discusshub_channel_id.message_post(
                    body=message,
                    message_type='comment',
                )

        return result
```

---

## 🎓 Mejores Prácticas

### 1. Siempre Verificar si Existe el Canal

```python
if record.discusshub_channel_id:
    # Hacer algo
else:
    _logger.warning(f"Registro {record} no tiene canal WhatsApp")
```

### 2. Manejo de Errores

```python
try:
    record.action_create_discusshub_channel()
except Exception as e:
    _logger.error(f"Error al crear canal: {e}")
    # No romper flujo principal
```

### 3. Logging Apropiado

```python
import logging
_logger = logging.getLogger(__name__)

_logger.info(f"Canal WhatsApp creado para {record.name}")
_logger.warning(f"Teléfono no encontrado para {record.name}")
_logger.error(f"Fallo al enviar mensaje: {error}")
```

---

## 📚 Referencias

- [Código Fuente DiscussHub Mixin](../../discuss_hub/models/discusshub_mixin.py)
- [Documentación Odoo - Mixins](https://www.odoo.com/documentation/18.0/developer/reference/backend/mixins.html)
- [Guía Completa en Inglés](../en/Bridge%20Modules.md)

---

**Documentación creada el**: 17 de Octubre de 2025
**Versión**: 1.0.0
**Compatibilidad**: Odoo 18.0+, DiscussHub 18.0.1.0.0+
