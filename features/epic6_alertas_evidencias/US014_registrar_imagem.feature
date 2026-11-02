Feature: US-014 – Registrar imagem da ocorrência
  Como responsável pela segurança
  Quero salvar evidências da infração
  Para que seja possível auditoria posterior

  Scenario: Sistema salva imagem ao detectar ocorrência
    Given que uma não conformidade de EPI é detectada
    When o alerta é emitido
    Then o sistema salva uma imagem do quadro em disco

  Scenario: Imagem salva contém data e hora
    Given que uma não conformidade de EPI é detectada
    When o alerta é emitido e a imagem é salva
    Then a imagem contém sobreposição visual com a data e hora do evento
