Feature: US-021 – Gerenciar modelos de IA
  Como administrador
  Quero atualizar modelos treinados
  Para que a precisão possa ser melhorada sem alterar o sistema

  Scenario: Fazer upload de novo modelo de IA
    Given que o administrador acessa o módulo de gerenciamento de modelos
    When realiza upload de um arquivo de modelo válido no formato ".pt"
    Then o modelo é armazenado no sistema e listado como disponível

  Scenario: Validar arquivo de modelo enviado
    Given que o administrador tenta fazer upload de um arquivo inválido
    When o arquivo é submetido ao sistema
    Then o sistema rejeita o arquivo e informa o motivo da invalidade

  Scenario: Trocar modelo ativo sem reinstalar a aplicação
    Given que um novo modelo foi carregado no sistema
    When o administrador ativa o novo modelo
    Then o sistema passa a utilizar o novo modelo nas detecções sem necessidade de reinicialização
