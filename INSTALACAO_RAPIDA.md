# 🚀 Instalação Rápida - Instância Ativa em Produção

> **Guia prático para instalar DiscussHub em seu Odoo 18 que já está rodando**

---

## ✅ Situação: Odoo 18 Ativo com Outros Módulos

**Você tem**:
- ✅ Odoo 18.0 rodando em produção
- ✅ Outros módulos já instalados e funcionando
- ✅ Clientes usando o sistema

**Você quer**:
- ✅ Adicionar DiscussHub sem afetar módulos existentes
- ✅ Zero downtime (ou mínimo)
- ✅ Sem riscos

**Garantia**: DiscussHub **NÃO** interfere com outros módulos!

---

## ⚡ Instalação em 15 Minutos

### Método A: Script Automatizado (MAIS FÁCIL)

```bash
# 1. Download do repositório
cd /tmp
git clone https://github.com/neoand/discuss_hub.git

# 2. Executar script de instalação
sudo bash discuss_hub/install_discuss_hub.sh SEU_DATABASE_NAME /opt/odoo/custom_addons

# 3. Aguardar
# O script faz:
# - Backup automático
# - Instala dependências Python
# - Copia módulos
# - Instala no Odoo
# - Reinicia serviço

# 4. Pronto!
```

**Tempo**: 10-15 minutos

---

### Método B: Manual (MAIS CONTROLE)

#### Passo 1: Instalar Dependências Python (3 min)

```bash
# Descobrir qual Python o Odoo usa
ps aux | grep odoo | head -1

# Instalar (ajuste o caminho do python se necessário)
sudo pip3 install google-generativeai textblob SpeechRecognition pydub Pillow

# Download corpus TextBlob
python3 -m textblob.download_corpora
```

#### Passo 2: Copiar Módulos (2 min)

```bash
# Clonar repositório
cd /tmp
git clone https://github.com/neoand/discuss_hub.git

# Copiar para addons (ajuste o caminho)
sudo cp -r discuss_hub/community_addons/discuss_hub /opt/odoo/custom_addons/
sudo cp -r discuss_hub/community_addons/discusshub_crm /opt/odoo/custom_addons/
sudo cp -r discuss_hub/community_addons/discusshub_helpdesk /opt/odoo/custom_addons/
sudo cp -r discuss_hub/community_addons/discusshub_project /opt/odoo/custom_addons/

# Permissões
sudo chown -R odoo:odoo /opt/odoo/custom_addons/discuss_hub*
sudo chmod -R 755 /opt/odoo/custom_addons/discuss_hub*
```

#### Passo 3: Instalar no Odoo (10 min)

**Opção A: Via Interface (SEM downtime)**

```
1. Login como Admin
2. Apps → Update Apps List (aguardar)
3. Remover filtro "Apps"
4. Buscar "discuss_hub"
5. Clicar "Install"
6. Aguardar (1-2 minutos)
7. Pronto!
```

**Opção B: Via CLI (COM pequeno downtime)**

```bash
# Parar Odoo
sudo systemctl stop odoo

# Instalar
sudo su - odoo
odoo -c /etc/odoo/odoo.conf -d SEU_DATABASE -i discuss_hub --stop-after-init
exit

# Reiniciar
sudo systemctl start odoo
```

---

## 🎯 Instalação dos Bridges (Opcional)

**Se você usa CRM**:
```
Apps → Buscar "DiscussHub CRM" → Install
```

**Se você usa Helpdesk**:
```
Apps → Buscar "DiscussHub Helpdesk" → Install
```

**Se você usa Project**:
```
Apps → Buscar "DiscussHub Project" → Install
```

---

## ✅ Verificação Pós-Instalação

### Checklist Rápido

```markdown
Login no Odoo e verificar:

- [ ] Menu "Discuss Hub" aparece
- [ ] Submenu "Connectors" acessível
- [ ] Submenu "Configuration" com "AI Responders"
- [ ] Submenu "Analytics" com dashboards
- [ ] Sem erros no log
```

### Teste Simples

```
1. Discuss Hub → Connectors → Create
2. Name: "Teste"
3. Type: Example Plugin
4. Save
5. ✅ Se salvar sem erro, instalação OK!
```

---

## 🔧 Configuração Inicial (5 min)

### 1. Configurar WhatsApp (Evolution API)

```
Se você JÁ TEM Evolution API rodando:

1. Discuss Hub → Connectors → Create
2. Name: "WhatsApp Principal"
3. Type: Evolution
4. URL: http://seu-evolution:8080
5. API Key: sua_chave
6. Save
7. Click "Start Instance"
8. Scan QR Code
9. ✅ Pronto para receber mensagens!
```

### 2. Configurar Telegram (MAIS FÁCIL)

```
1. Discuss Hub → Connectors → Setup Telegram Bot (button)
2. Seguir wizard:
   - Ir no Telegram → @BotFather
   - /newbot
   - Copiar token
   - Colar no wizard
3. ✅ Pronto!
```

### 3. Configurar AI (Opcional)

```
1. Discuss Hub → Configuration → AI Responders → Setup Wizard
2. Escolher HuggingFace (grátis ilimitado)
3. Obter token: https://huggingface.co/settings/tokens
4. Colar token
5. Testar
6. Criar
7. ✅ AI funcionando!
```

---

## ❓ FAQ - Perguntas Comuns

### P: Vai afetar meus módulos existentes?

**R**: NÃO! DiscussHub:
- ✅ Não modifica models existentes
- ✅ Não altera tabelas de outros módulos
- ✅ Funciona de forma independente
- ✅ Apenas adiciona campo `phone` sanitized no res.partner (não quebra nada)

### P: Preciso parar o Odoo?

**R**: NÃO se instalar via interface web!
- ✅ Via Apps: ZERO downtime
- ⚠️ Via CLI: ~2-3 minutos de downtime

### P: E se der erro?

**R**: Script faz backup automático
```bash
# Restaurar backup
sudo su - postgres
pg_restore -U odoo -d SEU_DB /backup/discuss_hub_install_*/database.backup
```

### P: Funciona com meu setup atual?

**R**: SIM se você tem:
- ✅ Odoo 18.0 (Community ou Enterprise)
- ✅ PostgreSQL
- ✅ Acesso para instalar pacotes Python

**NÃO funciona se**:
- ❌ Odoo SaaS (odoo.com)
- ❌ Odoo 17 ou anterior
- ❌ Sem permissão para instalar Python packages

### P: Posso testar antes de produção?

**R**: SIM! RECOMENDADO!
```bash
# Criar cópia do banco
createdb odoo_test
pg_restore -d odoo_test /backup/seu_backup.backup

# Instalar no test
odoo -d odoo_test -i discuss_hub --stop-after-init

# Testar à vontade
# Depois dropar: dropdb odoo_test
```

### P: Quanto custa?

**R**:
- ✅ Módulo: GRÁTIS (AGPL-3)
- ✅ HuggingFace AI: GRÁTIS (ilimitado)
- ✅ Evolution API: GRÁTIS (self-hosted)
- ✅ Telegram: GRÁTIS
- 🟡 Google Gemini: FREE TIER (60 req/min) depois pago
- 🟡 WhatsApp Cloud API: Pago

**Pode usar 100% grátis com HuggingFace + Evolution + Telegram!**

---

## 🎯 Resumo Executivo

### Instalação

| Método | Downtime | Dificuldade | Tempo |
|--------|----------|-------------|-------|
| **Script** | ~3 min | Fácil | 15 min |
| **Web Interface** | 0 min | Muito fácil | 10 min |
| **CLI Manual** | ~3 min | Média | 20 min |

### Compatibilidade

| Seu Setup | Compatível? |
|-----------|-------------|
| Odoo 18.0 on-premise | ✅ SIM |
| Odoo 18.0 Docker | ✅ SIM |
| Com módulos custom | ✅ SIM |
| Multi-company | ✅ SIM |
| Odoo SaaS | ❌ NÃO |
| Odoo 17 ou anterior | ❌ NÃO |

---

## 🚀 Próximos Passos Após Instalação

1. **Dia 1**: Configurar 1 connector e testar
2. **Dia 2**: Criar templates de mensagens
3. **Dia 3**: Configurar AI (opcional)
4. **Dia 4**: Instalar bridges (CRM/Helpdesk)
5. **Semana 2**: Treinar equipe e expandir uso

---

## 📞 Precisa de Ajuda?

- **Documentação**: https://github.com/neoand/discuss_hub/tree/main/community_addons/discuss_hub/docs
- **Issues**: https://github.com/neoand/discuss_hub/issues
- **Tutorial em vídeo**: (em breve)

---

**Pronto para instalar? Execute o script ou siga o guia manual!** ✅
