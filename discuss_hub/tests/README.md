# Testes do Discuss Hub

Este diretório contém os testes automatizados para o módulo Discuss Hub.

## Estrutura de Testes

Os testes estão organizados da seguinte forma:

- `test_models.py`: Testes unitários para os modelos principais
- `test_controller.py`: Testes para os controladores HTTP
- `test_routing_manager.py`: Testes específicos para o sistema de roteamento
- `test_base.py`: Testes base e utilitários compartilhados

## Execução dos Testes

Para executar os testes, utilize o framework de testes do Odoo:

```bash
python3 odoo-bin -d YOUR_DATABASE -i discuss_hub --test-enable --stop-after-init
```

## Tags de Testes

Os testes utilizam as seguintes tags:

- `discuss_hub`: Testes gerais do módulo
- `connector`: Testes específicos dos conectores
- `integration`: Testes de integração que podem precisar de serviços externos mockados

## Melhores Práticas

Ao adicionar novos testes ou modificar os existentes, siga estas diretrizes:

1. Use mocks para serviços externos (API Evolution, etc.)
2. Mantenha testes unitários isolados uns dos outros
3. Documente cenários de teste com comentários claros
4. Garanta que os testes sejam determinísticos (sem dependências de estado)
5. Cubra tanto casos de sucesso quanto casos de erro

## Cobertura de Testes

Áreas críticas que devem ser bem testadas:

- Processamento de webhooks
- Roteamento de mensagens
- Sincronização de contatos
- Tratamento de erros