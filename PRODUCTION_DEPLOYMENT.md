# Guia de Implementação em Produção - DiscussHub 🚀

> **Como instalar DiscussHub em uma instância Odoo 18 ativa em produção**

**Versão**: 18.0.4.0.0
**Data**: 18 de Outubro de 2025
**Odoo**: 18.0 APENAS

---

## 📋 Índice

1. [Pré-Requisitos](#pré-requisitos)
2. [Preparação](#preparação)
3. [Instalação Passo-a-Passo](#instalação-passo-a-passo)
4. [Configuração Pós-Instalação](#configuração-pós-instalação)
5. [Verificação e Testes](#verificação-e-testes)
6. [Troubleshooting](#troubleshooting)
7. [Rollback Plan](#rollback-plan)

---

## ⚠️ IMPORTANTE - Leia Antes de Começar

### Sobre Instâncias em Produção

✅ **SEGURO**: DiscussHub pode ser instalado em instância ativa
✅ **NÃO INVASIVO**: Não altera models existentes (exceto res.partner)
✅ **MODULAR**: Funciona independente de outros módulos
✅ **TESTADO**: 127+ tests garantem estabilidade

### Precauções

⚠️ **SEMPRE faça backup antes**
⚠️ **Teste em ambiente de staging primeiro**
⚠️ **Leia o guia completo antes de executar**
⚠️ **Tenha um plano de rollback**

---

## 🎯 Pré-Requisitos

### 1. Requisitos de Sistema

```bash
# Odoo
Odoo 18.0 (Community ou Enterprise)

# Python
Python 3.10+

# Banco de Dados
PostgreSQL 12+

# Sistema Operacional
Ubuntu 20.04+, Debian 11+, ou similar
```

### 2. Dependências Python

```bash
# Instalar ANTES da instalação do módulo
pip3 install google-generativeai
pip3 install textblob
pip3 install SpeechRecognition
pip3 install pydub
pip3 install Pillow

# Baixar corpus do TextBlob
python3 -m textblob.download_corpora
```

### 3. Módulos Odoo Necessários

```python
# Dependências (instaladas automaticamente se não existirem)
- base (core Odoo)
- mail (messaging)
- base_automation (automations)
- crm (para bridge CRM - opcional)
```

### 4. Acesso ao Servidor

```bash
# Você precisa de:
- SSH access ao servidor
- Permissão sudo para instalar pacotes
- Acesso ao usuário odoo
- Acesso aos diretórios de addons
```

---

## 📦 Preparação

### Passo 1: Backup COMPLETO

```bash
# 1. Backup do banco de dados
sudo su - postgres
pg_dump -U odoo -F c -b -v -f /backup/odoo_db_$(date +%Y%m%d_%H%M%S).backup nome_do_banco
exit

# 2. Backup do filestore
sudo cp -r /var/lib/odoo/.local/share/Odoo/filestore/nome_do_banco /backup/filestore_$(date +%Y%m%d_%H%M%S)

# 3. Backup dos addons (se houver custom)
sudo tar -czf /backup/custom_addons_$(date +%Y%m%d_%H%M%S).tar.gz /opt/odoo/custom_addons/
```

### Passo 2: Criar Ambiente de Staging (RECOMENDADO)

```bash
# Opção A: Duplicar banco para teste
sudo su - postgres
createdb odoo_staging
pg_restore -U odoo -d odoo_staging /backup/odoo_db_latest.backup
exit

# Opção B: Usar Docker para staging
docker run -d --name odoo-staging \
  -e POSTGRES_DB=odoo_staging \
  -e POSTGRES_USER=odoo \
  -e POSTGRES_PASSWORD=odoo \
  postgres:16

docker run -d --name odoo-app-staging \
  --link odoo-staging:db \
  -p 8070:8069 \
  -v /caminho/para/discuss_hub:/mnt/extra-addons/discuss_hub \
  odoo:18.0
```

### Passo 3: Verificar Estrutura de Diretórios

```bash
# Identificar onde ficam os addons
# Opção 1: Diretório padrão
/usr/lib/python3/dist-packages/odoo/addons/

# Opção 2: Custom addons path (comum)
/opt/odoo/custom_addons/
/var/lib/odoo/addons/
/home/odoo/addons/

# Verificar no odoo.conf
cat /etc/odoo/odoo.conf | grep addons_path
```

---

## 🚀 Instalação Passo-a-Passo

### Método 1: Git Clone (RECOMENDADO)

```bash
# 1. Ir para diretório de custom addons
cd /opt/odoo/custom_addons/
# OU
cd /caminho/para/seu/custom_addons/

# 2. Clonar o repositório
sudo git clone https://github.com/neoand/discuss_hub.git

# 3. Ajustar permissões
sudo chown -R odoo:odoo discuss_hub/
sudo chmod -R 755 discuss_hub/

# 4. Verificar estrutura
ls -la discuss_hub/community_addons/
# Deve ver: discuss_hub, discusshub_crm, discusshub_helpdesk, discusshub_project
```

### Método 2: Download Manual

```bash
# 1. Download ZIP do GitHub
wget https://github.com/neoand/discuss_hub/archive/refs/heads/main.zip

# 2. Extrair
unzip main.zip

# 3. Mover para addons
sudo mv discuss_hub-main/community_addons/* /opt/odoo/custom_addons/
sudo chown -R odoo:odoo /opt/odoo/custom_addons/discuss_hub*

# 4. Limpar
rm main.zip
rm -rf discuss_hub-main
```

### Método 3: Symlink (Desenvolvimento)

```bash
# Se você quer manter o repo em outro local
ln -s /caminho/completo/discuss_hub/community_addons/discuss_hub /opt/odoo/custom_addons/discuss_hub
ln -s /caminho/completo/discuss_hub/community_addons/discusshub_crm /opt/odoo/custom_addons/discusshub_crm
ln -s /caminho/completo/discuss_hub/community_addons/discusshub_helpdesk /opt/odoo/custom_addons/discusshub_helpdesk
ln -s /caminho/completo/discuss_hub/community_addons/discusshub_project /opt/odoo/custom_addons/discusshub_project
```

---

## 🔧 Instalação no Odoo

### Opção A: Via Interface Web (RECOMENDADO para Produção)

```
1. Login como Administrador
2. Apps → Update Apps List
3. Remover filtro "Apps" para ver todos os módulos
4. Buscar "discuss_hub"
5. Verificar dependências mostradas
6. Clicar "Install"
7. Aguardar instalação (pode levar 1-2 minutos)
8. Verificar log para erros
```

### Opção B: Via Linha de Comando

```bash
# 1. Parar Odoo (se necessário)
sudo systemctl stop odoo

# 2. Instalar módulo
sudo su - odoo
/usr/bin/odoo -c /etc/odoo/odoo.conf \
  -d nome_do_banco \
  -i discuss_hub \
  --stop-after-init \
  --log-level=info

# Verificar output para erros

# 3. Reiniciar Odoo
exit
sudo systemctl start odoo
sudo systemctl status odoo
```

### Opção C: Modo de Atualização (Se já instalado antes)

```bash
# Atualizar módulo
sudo su - odoo
/usr/bin/odoo -c /etc/odoo/odoo.conf \
  -d nome_do_banco \
  -u discuss_hub \
  --stop-after-init

exit
sudo systemctl restart odoo
```

---

## 🔌 Instalação de Módulos Bridge (Opcional)

### CRM Integration

```bash
# Via interface:
Apps → Buscar "DiscussHub CRM" → Install

# Via CLI:
odoo -d nome_db -i discusshub_crm --stop-after-init
```

### Helpdesk Integration

```bash
# Pré-requisito: módulo 'helpdesk' deve estar instalado

# Via interface:
Apps → Buscar "DiscussHub Helpdesk" → Install

# Via CLI:
odoo -d nome_db -i discusshub_helpdesk --stop-after-init
```

### Project Integration

```bash
# Via interface:
Apps → Buscar "DiscussHub Project" → Install

# Via CLI:
odoo -d nome_db -i discusshub_project --stop-after-init
```

---

## ⚙️ Configuração Pós-Instalação

### 1. Verificar Instalação

```
Settings → Apps → Installed Apps → Buscar "discuss_hub"
Deve aparecer: discuss_hub (18.0.4.0.0)
```

### 2. Configurar Primeiro Conector

#### WhatsApp via Evolution API

```
1. Discuss Hub → Connectors → Create
2. Name: "WhatsApp Principal"
3. Type: Evolution
4. URL: http://seu-evolution-api:8080
5. API Key: sua_api_key
6. Save
7. Click "Start Instance"
8. Scan QR Code
```

#### Telegram

```
Opção A: Wizard
1. Discuss Hub → Connectors → Setup Telegram Bot (button)
2. Seguir wizard 4 passos

Opção B: Manual
1. Discuss Hub → Connectors → Create
2. Type: Telegram
3. API Key: seu_bot_token (do @BotFather)
4. Save
```

### 3. Configurar AI (Opcional)

```
Opção A: Wizard
1. Discuss Hub → Configuration → AI Responders → Setup Wizard
2. Escolher provider (Gemini ou HuggingFace)
3. Inserir API key
4. Configurar prompts
5. Testar e criar

Opção B: Manual
1. Discuss Hub → Configuration → AI Responders → Create
2. Name: "Customer Service AI"
3. AI Provider: Gemini (ou HuggingFace)
4. API Key: sua_chave
5. Configure threshold e temperature
6. Save
```

---

## 🧪 Verificação e Testes

### Checklist de Validação

```markdown
Após instalação, verificar:

Core:
- [ ] Menu "Discuss Hub" aparece
- [ ] Submenu "Connectors" acessível
- [ ] Pode criar novo connector
- [ ] Tipos disponíveis: Evolution, WhatsApp Cloud, NotificaMe, Telegram

Bridges (se instalados):
- [ ] CRM: Botão WhatsApp em crm.lead
- [ ] Helpdesk: Botão WhatsApp em helpdesk.ticket
- [ ] Project: Botão WhatsApp em project.task

AI Features:
- [ ] Menu "AI Responders" em Configuration
- [ ] Menu "AI Response History" em Analytics
- [ ] Menu "Sentiment Analysis" em Analytics
- [ ] Menu "Voice Messages" em Analytics
- [ ] Menu "Image Analysis" em Analytics

Templates:
- [ ] Menu "WhatsApp Templates"
- [ ] Menu "Automated Triggers"

Analytics:
- [ ] Dashboard acessível
- [ ] Gráficos carregam

Security:
- [ ] Usuário normal vê menus mas não edita
- [ ] Admin tem acesso total
```

### Teste Funcional Básico

```python
# Teste 1: Criar connector
connector = env['discuss_hub.connector'].create({
    'name': 'Test',
    'type': 'example',
    'enabled': True,
})
# ✅ Deve criar sem erros

# Teste 2: Criar AI responder (se API key disponível)
ai = env['discuss_hub.ai_responder'].create({
    'name': 'Test AI',
    'ai_provider': 'huggingface',  # Grátis
    'api_key': 'seu_token_hf',
    'hf_model': 'google/flan-t5-large',
})
# ✅ Deve criar sem erros

# Teste 3: Templates
template = env['discuss_hub.message_template'].create({
    'name': 'Teste',
    'body': 'Olá {{partner.name}}!',
})
# ✅ Deve criar sem erros
```

---

## 🔒 Configurações de Segurança

### Grupos de Usuários

```
Odoo cria automaticamente:
- discuss_hub.group_discuss_hub_user (via base.group_user)
- discuss_hub.group_discuss_hub_manager (via base.group_system)

Permissões:
- Users: Ver connectors, templates, analytics (read-only)
- Managers: Full access (create/edit/delete)
```

### Ajustar Permissões (se necessário)

```
Settings → Users & Companies → Groups
→ Buscar "Discuss Hub"
→ Ajustar usuários em cada grupo
```

---

## 🔧 Configurações Avançadas

### 1. Parâmetros do Sistema (Opcional)

```
Settings → Technical → Parameters → System Parameters

Adicionar (se quiser centralizar API keys):

Key: google_ai_api_key
Value: AIzaSy...

Key: hf_api_token
Value: hf_...
```

### 2. Configurar Webhooks

#### Para Evolution API

```bash
# URL do webhook (substituir UUID pelo do seu connector)
https://seu-dominio.com/discuss_hub/connector/SEU-UUID-AQUI

# Configurar no Evolution:
POST http://evolution-api:8080/webhook/set/INSTANCIA
{
  "url": "https://seu-dominio.com/discuss_hub/connector/UUID",
  "webhook_by_events": false,
  "webhook_base64": false,
  "events": ["messages.upsert"]
}
```

#### Para Telegram

```python
# Automático via wizard OU manualmente:
connector = env['discuss_hub.connector'].browse(ID_DO_CONNECTOR)
plugin = connector.get_plugin()
plugin.set_webhook("https://seu-dominio.com/discuss_hub/connector/UUID")
```

### 3. Configurar Proxy/Nginx (se aplicável)

```nginx
# /etc/nginx/sites-available/odoo

location /discuss_hub {
    proxy_pass http://localhost:8069;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;

    # Timeout maior para AI requests
    proxy_read_timeout 90s;
}
```

---

## 🚨 Troubleshooting Comum

### Problema 1: Módulo não aparece em Apps

**Causa**: Odoo não leu o addon path

**Solução**:
```bash
# Verificar addons_path no odoo.conf
cat /etc/odoo/odoo.conf | grep addons_path

# Deve incluir o diretório onde colocou discuss_hub
addons_path = /usr/lib/python3/dist-packages/odoo/addons,/opt/odoo/custom_addons

# Se não incluir, adicionar:
sudo nano /etc/odoo/odoo.conf
# Adicionar caminho

# Reiniciar
sudo systemctl restart odoo

# Update Apps List no Odoo
```

### Problema 2: Erro de Dependência Python

**Erro**: `ModuleNotFoundError: No module named 'google.generativeai'`

**Solução**:
```bash
# Descobrir qual Python o Odoo usa
ps aux | grep odoo | grep python

# Instalar no Python correto
sudo /usr/bin/python3 -m pip install google-generativeai textblob SpeechRecognition pydub Pillow

# OU se usar venv:
sudo su - odoo
source /opt/odoo/venv/bin/activate
pip install google-generativeai textblob SpeechRecognition pydub Pillow
exit

# Reiniciar Odoo
sudo systemctl restart odoo
```

### Problema 3: Erro de Permissão

**Erro**: `PermissionError: [Errno 13] Permission denied`

**Solução**:
```bash
# Corrigir ownership
sudo chown -R odoo:odoo /opt/odoo/custom_addons/discuss_hub*

# Corrigir permissões
sudo chmod -R 755 /opt/odoo/custom_addons/discuss_hub*
```

### Problema 4: Conflito com Módulo Existente

**Erro**: `Module discuss_hub: conflict with module X`

**Solução**:
```
1. Verificar se já existe módulo com nome similar
2. DiscussHub NÃO deve conflitar com:
   - discuss (core Odoo)
   - mail_* modules
   - crm_* modules
3. Se houver conflito real, reportar issue no GitHub
```

---

## 🔄 Rollback Plan

### Se algo der errado:

#### Opção A: Desinstalar Módulo

```
1. Apps → Buscar "discuss_hub"
2. Uninstall
3. Confirmar
4. Aguardar desinstalação
```

#### Opção B: Restaurar Backup

```bash
# 1. Parar Odoo
sudo systemctl stop odoo

# 2. Restaurar banco
sudo su - postgres
dropdb nome_do_banco
createdb nome_do_banco
pg_restore -U odoo -d nome_do_banco /backup/odoo_db_TIMESTAMP.backup
exit

# 3. Restaurar filestore
sudo rm -rf /var/lib/odoo/.local/share/Odoo/filestore/nome_do_banco
sudo cp -r /backup/filestore_TIMESTAMP /var/lib/odoo/.local/share/Odoo/filestore/nome_do_banco
sudo chown -R odoo:odoo /var/lib/odoo/.local/share/Odoo/filestore/

# 4. Reiniciar
sudo systemctl start odoo
```

---

## 📊 Cenários de Instalação

### Cenário 1: Odoo SaaS (Odoo.com / Odoo.sh)

**Limitações**:
- Não pode instalar dependências Python customizadas
- Apenas módulos aprovados pela Odoo

**Solução**:
- ❌ Não é possível instalar discuss_hub em Odoo SaaS
- ✅ Precisa de instância self-hosted

### Cenário 2: Odoo On-Premise (Servidor Próprio)

**Situação**: Acesso completo ao servidor

**Passos**:
1. ✅ Seguir guia completo acima
2. ✅ Instalar dependências Python
3. ✅ Clonar repositório
4. ✅ Instalar módulo
5. ✅ Configurar

**Complexidade**: Média

### Cenário 3: Odoo Docker

**Situação**: Odoo rodando em container

**Passos**:
```dockerfile
# Opção A: Extend imagem oficial
FROM odoo:18.0

# Instalar dependências
USER root
RUN pip3 install google-generativeai textblob SpeechRecognition pydub Pillow

# Copiar addons
COPY ./discuss_hub/community_addons/ /mnt/extra-addons/

USER odoo
```

```yaml
# docker-compose.yml
services:
  odoo:
    image: seu-odoo-customizado:18.0
    volumes:
      - ./discuss_hub/community_addons:/mnt/extra-addons
    environment:
      - ADDONS_PATH=/mnt/extra-addons,/usr/lib/python3/dist-packages/odoo/addons
```

**Complexidade**: Baixa

### Cenário 4: Odoo com Outros Custom Modules

**Situação**: Já tem vários módulos customizados

**Compatibilidade**:
- ✅ DiscussHub é independente
- ✅ Não modifica models de outros módulos
- ✅ Usa apenas: res.partner (adiciona campo phone safe)
- ✅ Funciona com qualquer módulo

**Passos**:
1. Instalar discuss_hub normalmente
2. Se usar CRM → instalar discusshub_crm
3. Se usar Helpdesk → instalar discusshub_helpdesk
4. Se usar Project → instalar discusshub_project

---

## 🎯 Instalação Gradual (RECOMENDADO)

### Fase 1: Core (Dia 1)

```
1. Instalar apenas discuss_hub (base module)
2. Configurar 1 connector (Evolution ou Telegram)
3. Testar envio/recebimento
4. Validar funcionamento
```

### Fase 2: Templates (Dia 2-3)

```
1. Criar templates de mensagens
2. Testar bulk send
3. Configurar automated triggers (se necessário)
```

### Fase 3: AI (Dia 4-5)

```
1. Configurar AI Responder (começar com HuggingFace - grátis)
2. Testar auto-responses
3. Ajustar confidence threshold
4. Monitorar performance
```

### Fase 4: Bridges (Dia 6-7)

```
1. Instalar bridge modules (CRM/Helpdesk/Project)
2. Configurar em alguns registros piloto
3. Treinar equipe
4. Expandir uso
```

### Fase 5: Analytics (Ongoing)

```
1. Monitorar dashboards
2. Ajustar routing strategies
3. Revisar sentiment analysis
4. Otimizar templates
```

---

## 💡 Melhores Práticas

### 1. Começar Pequeno

```
❌ NÃO: Instalar tudo + ativar AI + 1000 templates no dia 1
✅ SIM: Instalar core → Testar → Expandir gradualmente
```

### 2. Ambiente de Staging

```
✅ Testar TUDO em staging antes de produção
✅ Simular carga real
✅ Validar integrações
```

### 3. Monitoramento

```bash
# Logs do Odoo
sudo tail -f /var/log/odoo/odoo.log | grep discuss_hub

# Performance
htop  # Verificar uso de CPU/RAM

# Banco de dados
sudo su - postgres
psql -d nome_db -c "SELECT COUNT(*) FROM mail_message WHERE model='discuss.channel';"
```

### 4. API Keys Seguras

```
❌ NÃO: Hardcode API keys
❌ NÃO: Commitar keys no git

✅ SIM: Usar ir.config_parameter
✅ SIM: Variáveis de ambiente
✅ SIM: Secrets manager (Docker/K8s)
```

### 5. Backup Regular

```bash
# Automatizar backups
crontab -e

# Backup diário às 2am
0 2 * * * pg_dump -U odoo nome_db | gzip > /backup/odoo_$(date +\%Y\%m\%d).sql.gz
```

---

## 📈 Escalabilidade

### Para Alto Volume de Mensagens

```yaml
# docker-compose.yml (exemplo)
services:
  odoo:
    deploy:
      replicas: 3  # Multiple instances
    environment:
      - WORKERS=4

  postgres:
    command: postgres -c max_connections=200

  redis:
    image: redis:7-alpine
    # Para cache de AI responses

  nginx:
    # Load balancer
```

### Otimizações

```python
# odoo.conf
[options]
workers = 4
max_cron_threads = 2
limit_time_cpu = 600
limit_time_real = 720

# Para AI requests longos
proxy_mode = True
```

---

## 🔐 Segurança em Produção

### 1. HTTPS Obrigatório

```
✅ Webhooks precisam de HTTPS
✅ Usar Let's Encrypt ou certificado válido
```

### 2. Firewall

```bash
# Liberar apenas portas necessárias
sudo ufw allow 80/tcp    # HTTP (redirect to HTTPS)
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 8069/tcp  # Odoo (se não usar proxy)
```

### 3. Rate Limiting

```nginx
# Nginx rate limit para webhooks
limit_req_zone $binary_remote_addr zone=webhook:10m rate=10r/s;

location /discuss_hub {
    limit_req zone=webhook burst=20;
    proxy_pass http://odoo;
}
```

---

## 📞 Suporte e Ajuda

### Se precisar de ajuda:

1. **Documentação**: https://github.com/neoand/discuss_hub/tree/main/community_addons/discuss_hub/docs
2. **Issues**: https://github.com/neoand/discuss_hub/issues
3. **Discussions**: https://github.com/neoand/discuss_hub/discussions

### Reportar Problema

Incluir sempre:
- Versão Odoo: 18.0
- Versão discuss_hub: 18.0.4.0.0
- Modo de instalação: (Docker/On-Premise/etc)
- Logs relevantes
- Passos para reproduzir

---

## ✅ Checklist Final de Produção

```markdown
Antes de ir para produção, confirmar:

Preparação:
- [ ] Backup completo realizado
- [ ] Testado em staging
- [ ] Dependências Python instaladas
- [ ] API keys obtidas e testadas

Instalação:
- [ ] Módulo instalado sem erros
- [ ] Logs verificados (sem warnings críticos)
- [ ] Menus aparecem corretamente
- [ ] Permissões configuradas

Configuração:
- [ ] Pelo menos 1 connector configurado e funcionando
- [ ] Templates criados
- [ ] AI configurado (opcional)
- [ ] Bridges instalados (se necessário)

Testes:
- [ ] Envio de mensagem funciona
- [ ] Recebimento de mensagem funciona
- [ ] Mídias (foto/vídeo) funcionam
- [ ] Templates renderizam corretamente
- [ ] AI responde (se ativado)

Monitoramento:
- [ ] Logs sendo coletados
- [ ] Métricas disponíveis
- [ ] Alertas configurados
- [ ] Equipe treinada

Documentação:
- [ ] Equipe sabe como usar
- [ ] Processos documentados
- [ ] Contato de suporte definido
```

---

## 🎓 Treinamento da Equipe

### Para Usuários

```
1. Como criar/enviar mensagem via DiscussHub
2. Como usar templates
3. Como ver histórico de conversas
4. Como escalar para supervisor
```

### Para Administradores

```
1. Como configurar connectors
2. Como gerenciar AI responders
3. Como criar templates
4. Como monitorar analytics
5. Como ajustar routing
```

---

## 📊 Monitoramento Pós-Instalação

### KPIs para Acompanhar

```
- Mensagens enviadas/recebidas por dia
- Taxa de auto-resposta AI (se ativado)
- Taxa de escalação para humanos
- Tempo médio de resposta
- Satisfação (sentiment analysis)
- Uso por canal (WhatsApp/Telegram)
```

### Dashboards

```
Discuss Hub → Analytics:
- Sentiment Analysis (tendências)
- AI Response History (taxa de sucesso)
- Dashboard (métricas gerais)
```

---

## 🎉 Conclusão

DiscussHub pode ser instalado em **qualquer instância Odoo 18 ativa** seguindo este guia.

**Complexidade**: Média
**Tempo**: 2-4 horas (primeira instalação)
**Risco**: Baixo (com backup e staging)
**Impacto**: Alto (messaging + AI integrados)

**Pronto para instalar em produção!** 🚀

---

**Próximo Passo**: Quer que eu crie scripts de instalação automatizada?
