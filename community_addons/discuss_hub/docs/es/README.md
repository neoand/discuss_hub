# DiscussHub - Documentación en Español 🇪🇸🇲🇽🇦🇷

> **Integración completa de WhatsApp, Telegram y otros canales de mensajería en Odoo 18**

[🇺🇸 English](../en/README.md) | [🇧🇷 Português](../pt-br/README.md) | **🇪🇸 Español**

---

## 📋 Índice

- [Visión General](#visión-general)
- [Inicio Rápido](#inicio-rápido)
- [Arquitectura](#arquitectura)
- [Módulos](#módulos)
- [Documentación Completa](#documentación-completa)

---

## 🎯 Visión General

**DiscussHub** es un addon completo para Odoo 18 que integra canales de mensajería externos (WhatsApp, Telegram, etc.) directamente en la aplicación Discuss nativa de Odoo.

### ✨ Características Principales

- **Comunicación Bidireccional**: Envía y recibe mensajes directamente desde Odoo
- **Integración Multi-Módulo**: Extiende CRM, Helpdesk, Proyectos con capacidades de mensajería
- **Arquitectura de Plugins**: Añade fácilmente nuevos proveedores de mensajería
- **Funciones Empresariales**: Mensajería masiva, analíticas, triggers automáticos, plantillas

### 🎬 ¿Qué Puedes Hacer?

- 💬 Chatear con clientes vía WhatsApp directamente en Odoo Discuss
- 📊 Rastrear todas las conversaciones vinculadas a Leads CRM, Tickets de Soporte o Tareas de Proyecto
- 🤖 Automatizar mensajes basados en eventos de registros (cambios de etapa, creación, etc.)
- 📱 Enviar campañas masivas de WhatsApp usando plantillas
- 📈 Monitorear métricas y analíticas de mensajería
- 🔌 Extender para soportar cualquier plataforma de mensajería mediante plugins

---

## 🚀 Inicio Rápido

### Prerequisitos

- Docker & Docker Compose
- Git

### ⚡ Configuración en 3 Minutos

```bash
# 1. Clonar el repositorio
git clone https://github.com/neoand/discuss_hub.git
cd discuss_hub

# 2. Iniciar servicios (Odoo + PostgreSQL + Evolution API + N8N + Redis)
docker compose -f compose-dev.yaml up -d

# 3. Esperar a que los servicios inicien (~30 segundos)
sleep 30

# 4. Cargar workflows de N8N (automatización opcional)
docker compose -f compose-dev.yaml exec -u node -it n8n sh -c "n8n import:workflow --input=/n8n-workflows.yaml"
docker compose -f compose-dev.yaml exec -u node -it n8n sh -c "n8n update:workflow --all --active=true"
docker compose -f compose-dev.yaml restart n8n

# 5. Acceder a Odoo
# URL: http://localhost:8069/?debug=1
# Email: admin
# Contraseña: admin
```

### 📱 Conectar WhatsApp

1. Navegar a **Discuss Hub → Connectors**
2. Abrir el conector Evolution por defecto
3. Hacer clic en **"Start Instance"**
4. Escanear el código QR con WhatsApp
5. ¡Empezar a recibir mensajes!

---

## 🏗️ Arquitectura

### Componentes Clave

| Componente | Descripción | Líneas de Código |
|-----------|-------------|------------------|
| **discuss_hub** | Módulo core con sistema de conector & plugins | ~2,936 |
| **discusshub_mixin** | Mixin abstracto para integración de cualquier modelo | 266 |
| **automated_trigger** | Automatización de mensajes basada en eventos | 423 |
| **message_template** | Sistema de plantillas Jinja2 | ~200 |
| **bulk_send_wizard** | Mensajería masiva con limitación de tasa | ~200 |
| **analytics** | Vistas SQL para métricas | ~150 |

---

## 📦 Módulos

### Módulo Core

#### `discuss_hub` (Módulo Base)
La base del sistema de integración de mensajería.

**Características Principales:**
- Gestión de conectores (iniciar/detener/configurar instancias)
- Arquitectura basada en plugins
- Procesamiento de webhooks
- Enrutamiento de mensajes a discuss.channel
- Soporte para todos los tipos de mensajes (texto, media, ubicación, contactos, reacciones)

---

### Módulos Bridge (Integraciones de Aplicaciones)

Estos módulos extienden aplicaciones Odoo con capacidades de mensajería WhatsApp usando `discusshub.mixin`.

#### `discusshub_crm` - Integración CRM

Añade canales WhatsApp a Leads y Oportunidades CRM.

**Características:**
- Vincular canales WhatsApp a leads/oportunidades
- Enviar mensajes directamente desde el formulario de lead
- Rastrear historial de conversaciones
- Auto-detectar teléfono desde partner o campos de lead
- Nombrado de canal personalizado basado en etapa de lead

**Ejemplo de Uso:**
```python
# Crear lead con canal WhatsApp
lead = env['crm.lead'].create({
    'name': 'Oportunidad Juan Pérez',
    'partner_id': partner.id,
})

# Crear canal WhatsApp
lead.action_create_discusshub_channel()

# Enviar mensaje
lead.action_send_discusshub_message()
```

---

#### `discusshub_helpdesk` - Integración Helpdesk

Integra tickets de soporte con WhatsApp para comunicación con clientes.

**Características:**
- Vincular canales WhatsApp a tickets de soporte
- Responder a clientes vía WhatsApp desde el formulario de ticket
- Rastrear conversaciones de tickets
- Auto-detectar teléfono del cliente

**Ejemplo de Uso:**
```python
# Crear ticket con WhatsApp
ticket = env['helpdesk.ticket'].create({
    'name': 'Problema del Cliente #123',
    'partner_id': partner.id,
})

# Vincular canal WhatsApp
ticket.action_create_discusshub_channel()
```

---

#### `discusshub_project` - Integración de Proyectos

Conecta tareas de proyecto con comunicación del equipo vía WhatsApp.

**Características:**
- Vincular canales WhatsApp a tareas de proyecto
- Comunicar con clientes sobre progreso de tareas
- Rastrear conversaciones relacionadas con tareas
- Soporte para notificaciones de asignados/seguidores

**Ejemplo de Uso:**
```python
# Crear tarea con WhatsApp
task = env['project.task'].create({
    'name': 'Rediseño de Sitio Web',
    'partner_id': partner.id,
})

# Crear canal WhatsApp para tarea
task.action_create_discusshub_channel()
```

---

### Usando el DiscussHub Mixin

El `discusshub.mixin` es un **modelo abstracto** que puede ser heredado por CUALQUIER modelo Odoo para añadir capacidades de mensajería.

#### Guía de Integración Rápida

```python
from odoo import models, fields

class MiModeloPersonalizado(models.Model):
    _name = 'mi.modelo.personalizado'
    _inherit = ['mi.modelo.personalizado', 'discusshub.mixin']

    # ¡Listo! Tu modelo ahora tiene:
    # - campo discusshub_channel_id
    # - campo discusshub_message_count
    # - campo discusshub_last_message_date
    # - método action_send_discusshub_message()
    # - método action_create_discusshub_channel()
    # - método action_open_discusshub_channel()
```

#### Personalización (Opcional)

Sobrescribir métodos helper para comportamiento personalizado:

```python
def _get_discusshub_destination(self):
    """Detección de número de teléfono personalizado."""
    if self.campo_telefono_personalizado:
        return self.campo_telefono_personalizado
    return super()._get_discusshub_destination()

def _get_discusshub_channel_name(self):
    """Nombre de canal personalizado."""
    return f"WhatsApp: {self.name} - {self.stage_id.name}"
```

---

## 📚 Documentación Completa

### Guías Completas

- 🇺🇸 **[Complete English Documentation](../en/README.md)**
- 🇧🇷 **[Documentação Completa em Português](../pt-br/README.md)**
- 🇪🇸 **Documentación en Español** (esta página)

### Guías Especializadas

- 🔗 **[Módulos Bridge](./Módulos%20Bridge.md)** - Integración CRM, Helpdesk, Project
- 🔥 **[Guía Plugin Evolution](../en/Evolution%20Plugin.md)** - Integración WhatsApp Baileys (English)
- 🛠️ **[Desarrollo de Plugins](../en/Plugin%20Development.md)** - Crear plugins personalizados (English)
- 🔧 **[Solución de Problemas](../pt-br/Troubleshooting.md)** - Problemas comunes & soluciones (Português)

### Documentación Técnica

- **[Documentación de Tests](../../tests/README.md)** - Ejecutar y escribir tests (English)
- **[Configuración Docker](../../compose.yaml)** - Despliegue en producción
- **[Configuración de Desarrollo](../../compose-dev.yaml)** - Desarrollo local

---

## 🧪 Testing

El proyecto incluye cobertura de tests completa (3,388 líneas de código de tests).

### Ejecutar Tests

```bash
# Ejecutar todos los tests
docker compose -f compose-dev.yaml exec odoo odoo -c /etc/odoo/odoo.conf \
  --test-enable --stop-after-init -u discuss_hub

# Ejecutar test específico
docker compose -f compose-dev.yaml exec odoo odoo -c /etc/odoo/odoo.conf \
  --test-enable --stop-after-init -u discuss_hub \
  --test-tags /discuss_hub:TestEvolutionPlugin.test_send_text_message
```

---

## 🗺️ Hoja de Ruta

### Fase 1 ✅ (Completado)
- [x] Framework core de conectores
- [x] Plugin Evolution API (WhatsApp Baileys)
- [x] Mensajería bidireccional
- [x] DiscussHub mixin para extensibilidad

### Fase 2 ✅ (Completado)
- [x] Integración CRM (discusshub_crm)
- [x] Integración Helpdesk (discusshub_helpdesk)
- [x] Integración Project (discusshub_project)

### Fase 3 ✅ (Completado)
- [x] Plantillas de mensajes con Jinja2
- [x] Wizard de mensajería masiva
- [x] Dashboard de analíticas
- [x] Triggers automáticos

### Fase 4 🚧 (En Progreso)
- [ ] Mejoras WhatsApp Cloud API
- [ ] Plugin de Telegram
- [ ] Soporte multi-idioma para plantillas
- [ ] Algoritmos de enrutamiento avanzados

### Fase 5 📋 (Planificado)
- [ ] Auto-respuestas con IA
- [ ] Integración de chatbots
- [ ] Análisis de sentimientos
- [ ] Soporte para mensajes de voz

---

## 🤝 Contribuir

¡Damos la bienvenida a contribuciones! Por favor sigue estos pasos:

1. **Hacer Fork del repositorio**
2. **Crear una rama de feature**: `git checkout -b feature/caracteristica-increible`
3. **Commit tus cambios**: `git commit -m 'Añadir característica increíble'`
4. **Push a la rama**: `git push origin feature/caracteristica-increible`
5. **Abrir un Pull Request**

---

## 📄 Licencia

Este proyecto está licenciado bajo **AGPL-3.0**. Ver archivo [LICENSE](../../LICENSE) para detalles.

Cada módulo puede tener su propia licencia según se especifica en su archivo `__manifest__.py`.

---

## 🙏 Agradecimientos

- **Odoo Community Association (OCA)** - Por los módulos comunitarios y estándares
- **Evolution API** - Por la excelente integración WhatsApp Baileys
- **Contribuidores** - Gracias a todos los contribuidores que han ayudado a mejorar este proyecto

---

## 📞 Soporte

- **Documentación**: [docs/](../)
- **Issues**: [GitHub Issues](https://github.com/neoand/discuss_hub/issues)
- **Discusiones**: [GitHub Discussions](https://github.com/neoand/discuss_hub/discussions)

---

**Hecho con ❤️ por el equipo DiscussHub**

*Empoderando negocios con comunicación multi-canal perfecta en Odoo*
