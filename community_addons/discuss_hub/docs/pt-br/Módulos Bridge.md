# Módulos Bridge - Integração com Aplicações Odoo 🔗

## 📋 Índice

- [Visão Geral](#visão-geral)
- [DiscussHub Mixin](#discusshub-mixin)
- [Módulo CRM](#módulo-crm-discusshub_crm)
- [Módulo Helpdesk](#módulo-helpdesk-discusshub_helpdesk)
- [Módulo Project](#módulo-project-discusshub_project)
- [Como Criar Seu Próprio Bridge](#como-criar-seu-próprio-bridge)
- [Exemplos Práticos](#exemplos-práticos)

---

## 📖 Visão Geral

Os **Módulos Bridge** são extensões que conectam aplicações Odoo (CRM, Helpdesk, Project, etc.) com o DiscussHub, permitindo comunicação via WhatsApp e outros canais diretamente de dentro dos registros.

### ✨ O Que São Módulos Bridge?

Módulos que estendem aplicações Odoo existentes adicionando:
- Campo para vincular canal WhatsApp
- Contadores de mensagens
- Botões de ação para enviar mensagens
- Histórico de conversas integrado

### 🎯 Benefícios

- **Contexto Completo**: Veja conversas WhatsApp dentro do contexto do Lead, Ticket ou Task
- **Comunicação Rápida**: Um clique para abrir conversa com cliente
- **Histórico Centralizado**: Todas mensagens gravadas no Odoo
- **Automação**: Gatilhos baseados em eventos (mudança de estágio, etc.)

---

## 🧩 DiscussHub Mixin

O **`discusshub.mixin`** é um modelo abstrato que fornece funcionalidade pronta para adicionar mensagens a qualquer modelo Odoo.

### 📦 O Que o Mixin Adiciona?

#### Campos Automáticos

```python
# Campo de relacionamento
discusshub_channel_id = fields.Many2one('discuss.channel')
# Link para o canal WhatsApp/Telegram vinculado a este registro

# Campos computados
discusshub_message_count = fields.Integer(compute='_compute_discusshub_message_count')
# Número de mensagens no canal vinculado

discusshub_last_message_date = fields.Datetime(compute='_compute_discusshub_message_count')
# Data da última mensagem recebida/enviada
```

#### Métodos Automáticos

```python
# Abrir conversa para enviar mensagem
record.action_send_discusshub_message()

# Criar e vincular novo canal WhatsApp
record.action_create_discusshub_channel()

# Abrir canal existente
record.action_open_discusshub_channel()
```

#### Métodos Helper (Para Sobrescrever)

```python
# Obter número de telefone do registro
def _get_discusshub_destination(self):
    """Retorna número no formato '5511999999999'"""

# Obter nome do canal
def _get_discusshub_channel_name(self):
    """Retorna nome como 'WhatsApp: Lead - Cliente XYZ'"""
```

---

## 📦 Módulos Disponíveis

### 🎯 CRM Integration (`discusshub_crm`)

**Localização**: `community_addons/discusshub_crm/`
**Linhas de Código**: ~450 LOC
**Status**: ✅ Produção

#### Funcionalidades

- Vincular canais WhatsApp a Leads e Oportunidades
- Enviar mensagens diretamente do formulário de Lead
- Rastrear histórico de conversas
- Detecção automática de telefone (partner ou campos do lead)
- Nomenclatura baseada no estágio do lead

#### Arquivos

```
community_addons/discusshub_crm/
├── __init__.py
├── __manifest__.py
├── README.md
├── models/
│   ├── __init__.py
│   └── crm_lead.py          # Extensões do modelo crm.lead
└── views/
    └── crm_lead_views.xml   # Botões e campos na view
```

#### Instalação

```bash
# Via interface Odoo
Apps → Buscar "DiscussHub CRM" → Instalar

# Via linha de comando
odoo -u discusshub_crm -d nome_database
```

#### Uso Básico

```python
# Obter lead
lead = env['crm.lead'].browse(1)

# Criar canal WhatsApp para o lead
lead.action_create_discusshub_channel()
# Isso cria automaticamente um canal vinculado ao telefone do partner

# Enviar mensagem
lead.action_send_discusshub_message()
# Abre o canal para enviar mensagem

# Acessar informações
print(lead.discusshub_message_count)      # Ex: 15 mensagens
print(lead.discusshub_last_message_date)  # Ex: 2025-10-17 14:30:00
```

#### Personalização

```python
# Sobrescrever nomenclatura do canal
class Lead(models.Model):
    _inherit = 'crm.lead'

    def _get_discusshub_channel_name(self):
        """Nome customizado baseado no estágio"""
        stage = self.stage_id.name if self.stage_id else 'Novo'
        return f"WhatsApp: [{stage}] {self.name}"

    def _get_discusshub_destination(self):
        """Priorizar mobile do partner"""
        if self.partner_id and self.partner_id.mobile:
            return self.partner_id.mobile
        elif self.phone:
            return self.phone
        return super()._get_discusshub_destination()
```

#### View XML

O módulo adiciona um botão no formulário de Lead:

```xml
<xpath expr="//div[@name='button_box']" position="inside">
    <button name="action_create_discusshub_channel"
            type="object"
            class="oe_stat_button"
            icon="fa-whatsapp"
            attrs="{'invisible': [('discusshub_channel_id', '!=', False)]}">
        <div class="o_field_widget o_stat_info">
            <span class="o_stat_text">Criar Canal</span>
            <span class="o_stat_text">WhatsApp</span>
        </div>
    </button>

    <button name="action_open_discusshub_channel"
            type="object"
            class="oe_stat_button"
            icon="fa-whatsapp"
            attrs="{'invisible': [('discusshub_channel_id', '=', False)]}">
        <field name="discusshub_message_count" widget="statinfo" string="Mensagens"/>
    </button>
</xpath>
```

---

### 🎫 Helpdesk Integration (`discusshub_helpdesk`)

**Localização**: `community_addons/discusshub_helpdesk/`
**Linhas de Código**: ~200 LOC
**Status**: ✅ Produção

#### Funcionalidades

- Vincular canais WhatsApp a tickets de suporte
- Responder clientes via WhatsApp do formulário de ticket
- Rastrear conversas de suporte
- Detecção automática de telefone do cliente
- Integração com SLA e prioridades

#### Arquivos

```
community_addons/discusshub_helpdesk/
├── __init__.py
├── __manifest__.py
├── README.md
├── models/
│   ├── __init__.py
│   └── helpdesk_ticket.py    # Extensões do modelo helpdesk.ticket
└── views/
    └── helpdesk_ticket_views.xml
```

#### Instalação

```bash
# Pré-requisito: módulo helpdesk instalado
# Apps → Buscar "DiscussHub Helpdesk" → Instalar

odoo -u discusshub_helpdesk -d nome_database
```

#### Uso Básico

```python
# Obter ticket
ticket = env['helpdesk.ticket'].browse(1)

# Criar canal WhatsApp
ticket.action_create_discusshub_channel()

# Enviar mensagem ao cliente
ticket.action_send_discusshub_message()

# Acessar estatísticas
print(f"Mensagens: {ticket.discusshub_message_count}")
print(f"Última mensagem: {ticket.discusshub_last_message_date}")
```

#### Caso de Uso: Atendimento ao Cliente

```python
# Quando ticket é criado, criar canal automaticamente
class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    @api.model_create_multi
    def create(self, vals_list):
        tickets = super().create(vals_list)

        for ticket in tickets:
            # Se cliente tem WhatsApp, criar canal
            if ticket.partner_id and (ticket.partner_id.mobile or ticket.partner_id.phone):
                try:
                    ticket.action_create_discusshub_channel()
                except Exception as e:
                    _logger.warning(f"Não foi possível criar canal WhatsApp: {e}")

        return tickets
```

#### Automação de Mensagens

```python
# Enviar mensagem automática quando ticket é resolvido
class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    def write(self, vals):
        result = super().write(vals)

        # Se mudou para estágio "Resolvido"
        if vals.get('stage_id'):
            stage = self.env['helpdesk.stage'].browse(vals['stage_id'])
            if stage.is_close:
                self._send_resolution_message()

        return result

    def _send_resolution_message(self):
        """Envia mensagem de ticket resolvido"""
        if not self.discusshub_channel_id:
            return

        # Usar template
        template = self.env.ref('discusshub_helpdesk.template_ticket_resolved')
        message = template.render(ticket=self)

        # Enviar via channel
        self.discusshub_channel_id.message_post(
            body=message,
            message_type='comment',
            subtype_xmlid='mail.mt_comment',
        )
```

---

### 📋 Project Integration (`discusshub_project`)

**Localização**: `community_addons/discusshub_project/`
**Linhas de Código**: ~150 LOC
**Status**: ✅ Produção

#### Funcionalidades

- Vincular canais WhatsApp a tarefas de projeto
- Comunicar com clientes sobre progresso de tarefas
- Rastrear conversas relacionadas a tarefas
- Notificações para assignees/followers
- Atualizações de status via WhatsApp

#### Arquivos

```
community_addons/discusshub_project/
├── __init__.py
├── __manifest__.py
├── README.md
├── models/
│   ├── __init__.py
│   └── project_task.py       # Extensões do modelo project.task
└── views/
    └── project_task_views.xml
```

#### Instalação

```bash
# Apps → Buscar "DiscussHub Project" → Instalar
odoo -u discusshub_project -d nome_database
```

#### Uso Básico

```python
# Obter tarefa
task = env['project.task'].browse(1)

# Criar canal WhatsApp
task.action_create_discusshub_channel()

# Enviar atualização ao cliente
task.action_send_discusshub_message()
```

#### Caso de Uso: Atualizações de Progresso

```python
class ProjectTask(models.Model):
    _inherit = 'project.task'

    def write(self, vals):
        result = super().write(vals)

        # Notificar cliente quando tarefa é concluída
        if vals.get('stage_id'):
            stage = self.env['project.task.type'].browse(vals['stage_id'])
            if stage.fold:  # Estágio final
                self._notify_task_completion()

        return result

    def _notify_task_completion(self):
        """Notifica cliente via WhatsApp"""
        if not self.discusshub_channel_id:
            return

        message = f"""
🎉 *Tarefa Concluída!*

Olá {self.partner_id.name},

A tarefa *{self.name}* foi concluída com sucesso!

📋 *Detalhes:*
- Projeto: {self.project_id.name}
- Responsável: {self.user_ids[0].name if self.user_ids else 'N/A'}
- Data de conclusão: {fields.Date.today()}

Se tiver alguma dúvida, estamos à disposição!

Atenciosamente,
{self.env.company.name}
        """

        self.discusshub_channel_id.message_post(
            body=message,
            message_type='comment',
        )
```

---

## 🛠️ Como Criar Seu Próprio Bridge

Siga este guia para integrar DiscussHub com qualquer módulo Odoo.

### Passo 1: Estrutura do Módulo

```bash
mkdir community_addons/discusshub_custom
cd community_addons/discusshub_custom

# Criar estrutura
mkdir models views
touch __init__.py __manifest__.py README.md
touch models/__init__.py models/custom_model.py
touch views/custom_model_views.xml
```

### Passo 2: Manifest (`__manifest__.py`)

```python
{
    'name': 'DiscussHub Custom Integration',
    'version': '18.0.1.0.0',
    'category': 'Discuss',
    'summary': 'Integrate DiscussHub with Custom Module',
    'depends': [
        'discuss_hub',           # Módulo base DiscussHub
        'your_custom_module',    # Seu módulo a ser integrado
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

### Passo 3: Modelo (`models/custom_model.py`)

```python
from odoo import models, api

class CustomModel(models.Model):
    _name = 'your.custom.model'
    _inherit = ['your.custom.model', 'discusshub.mixin']

    # Pronto! Seu modelo agora tem todos os campos e métodos do mixin

    # (Opcional) Customizar detecção de telefone
    def _get_discusshub_destination(self):
        """Obter telefone customizado"""
        if self.custom_phone_field:
            return self.custom_phone_field
        return super()._get_discusshub_destination()

    # (Opcional) Customizar nome do canal
    def _get_discusshub_channel_name(self):
        """Nome customizado do canal"""
        return f"WhatsApp: {self.name} - {self.state}"
```

### Passo 4: View (`views/custom_model_views.xml`)

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <record id="view_custom_model_form_inherit_discusshub" model="ir.ui.view">
        <field name="name">your.custom.model.form.inherit.discusshub</field>
        <field name="model">your.custom.model</field>
        <field name="inherit_id" ref="your_module.view_custom_model_form"/>
        <field name="arch" type="xml">

            <!-- Adicionar botões no button_box -->
            <xpath expr="//div[@name='button_box']" position="inside">

                <!-- Botão: Criar Canal -->
                <button name="action_create_discusshub_channel"
                        type="object"
                        class="oe_stat_button"
                        icon="fa-whatsapp"
                        attrs="{'invisible': [('discusshub_channel_id', '!=', False)]}">
                    <div class="o_field_widget o_stat_info">
                        <span class="o_stat_text">Criar</span>
                        <span class="o_stat_text">WhatsApp</span>
                    </div>
                </button>

                <!-- Botão: Abrir Canal (com contador) -->
                <button name="action_open_discusshub_channel"
                        type="object"
                        class="oe_stat_button"
                        icon="fa-whatsapp"
                        attrs="{'invisible': [('discusshub_channel_id', '=', False)]}">
                    <field name="discusshub_message_count"
                           widget="statinfo"
                           string="Mensagens"/>
                </button>

            </xpath>

            <!-- (Opcional) Adicionar campos no formulário -->
            <xpath expr="//sheet" position="inside">
                <group string="DiscussHub">
                    <field name="discusshub_channel_id" readonly="1"/>
                    <field name="discusshub_message_count" readonly="1"/>
                    <field name="discusshub_last_message_date" readonly="1"/>
                </group>
            </xpath>

        </field>
    </record>
</odoo>
```

### Passo 5: Inicialização (`__init__.py`)

```python
from . import models
```

```python
# models/__init__.py
from . import custom_model
```

### Passo 6: Instalação

```bash
# Reiniciar Odoo
docker compose restart odoo

# Instalar módulo
# Apps → Atualizar Lista de Apps → Buscar "DiscussHub Custom" → Instalar
```

---

## 💡 Exemplos Práticos

### Exemplo 1: Auto-criar Canal ao Criar Registro

```python
class CustomModel(models.Model):
    _inherit = 'your.custom.model'

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)

        for record in records:
            # Se tem partner com telefone, criar canal automaticamente
            if record.partner_id and record.partner_id.mobile:
                record.action_create_discusshub_channel()

        return records
```

### Exemplo 2: Enviar Mensagem Automática em Evento

```python
class CustomModel(models.Model):
    _inherit = 'your.custom.model'

    def action_confirm(self):
        """Ao confirmar, envia mensagem via WhatsApp"""
        result = super().action_confirm()

        for record in self:
            if record.discusshub_channel_id:
                message = f"""
Olá {record.partner_id.name}!

Sua solicitação *{record.name}* foi confirmada.

Status: ✅ Confirmado
Data: {fields.Date.today()}

Obrigado!
                """
                record.discusshub_channel_id.message_post(
                    body=message,
                    message_type='comment',
                )

        return result
```

### Exemplo 3: Usar Templates Jinja2

```python
class CustomModel(models.Model):
    _inherit = 'your.custom.model'

    def send_status_update(self):
        """Envia atualização usando template"""
        template = self.env.ref('discusshub_custom.template_status_update')

        for record in self:
            if not record.discusshub_channel_id:
                continue

            # Renderizar template
            message = template.render(
                record=record,
                partner=record.partner_id,
                company=self.env.company,
            )

            # Enviar
            record.discusshub_channel_id.message_post(
                body=message,
                message_type='comment',
            )
```

### Exemplo 4: Integração com Automated Triggers

```python
# Criar trigger automático via código
trigger = env['discuss_hub.automated_trigger'].create({
    'name': 'Notificar Mudança de Estágio - Custom',
    'model_id': env.ref('your_module.model_your_custom_model').id,
    'trigger_type': 'on_stage_change',
    'stage_to_id': env.ref('your_module.stage_done').id,
    'template_id': env.ref('discusshub_custom.template_stage_done').id,
    'active': True,
})
```

### Exemplo 5: Widget Customizado

```xml
<!-- Adicionar widget de chat inline -->
<xpath expr="//sheet" position="after">
    <div class="oe_chatter">
        <field name="discusshub_channel_id" widget="mail_thread"
               options="{'display_log_button': True}"/>
    </div>
</xpath>
```

---

## 🎓 Boas Práticas

### 1. Sempre Verificar se Canal Existe

```python
if record.discusshub_channel_id:
    # Fazer algo
else:
    _logger.warning(f"Registro {record} não tem canal WhatsApp")
```

### 2. Tratamento de Erros

```python
try:
    record.action_create_discusshub_channel()
except Exception as e:
    _logger.error(f"Erro ao criar canal: {e}")
    # Não quebrar fluxo principal
```

### 3. Verificar Telefone Antes de Criar Canal

```python
def create_channel_if_phone_exists(self):
    if not self._get_discusshub_destination():
        raise UserError("Registro não possui número de telefone válido")
    return self.action_create_discusshub_channel()
```

### 4. Usar Contexto para Controle

```python
# Criar sem notificar
record.with_context(no_discusshub_notification=True).write({'state': 'done'})
```

### 5. Logging Adequado

```python
import logging
_logger = logging.getLogger(__name__)

_logger.info(f"Canal WhatsApp criado para {record.name}")
_logger.warning(f"Telefone não encontrado para {record.name}")
_logger.error(f"Falha ao enviar mensagem: {error}")
```

---

## 📚 Referências

- [DiscussHub Mixin - Código Fonte](../../discuss_hub/models/discusshub_mixin.py)
- [Documentação Odoo - Mixins](https://www.odoo.com/documentation/18.0/developer/reference/backend/mixins.html)
- [Automated Triggers](./Automated%20Triggers.md)
- [Message Templates](./Message%20Templates.md)

---

## ❓ FAQ

### P: Posso usar o mixin em modelos transient?

**R**: Não recomendado. O mixin foi projetado para modelos persistentes (models.Model), não para wizards (models.TransientModel).

### P: Como adicionar campos extras ao canal?

**R**: Sobrescreva `action_create_discusshub_channel()`:

```python
def action_create_discusshub_channel(self):
    res = super().action_create_discusshub_channel()

    # Adicionar campos extras
    self.discusshub_channel_id.write({
        'custom_field': self.custom_value,
    })

    return res
```

### P: Posso ter múltiplos canais por registro?

**R**: O mixin padrão suporta apenas um canal. Para múltiplos canais, você precisaria criar campos One2many customizados.

### P: Como desativar criação automática de canal?

**R**: Remova a chamada `action_create_discusshub_channel()` do método `create()` ou adicione condição:

```python
if not self.env.context.get('skip_discusshub_creation'):
    record.action_create_discusshub_channel()
```

---

**Documentação criada em**: 17 de Outubro de 2025
**Versão**: 1.0.0
**Compatibilidade**: Odoo 18.0+, DiscussHub 18.0.1.0.0+
