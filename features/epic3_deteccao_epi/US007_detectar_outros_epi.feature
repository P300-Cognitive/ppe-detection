Feature: US-007 – Detectar outros EPIs
  Como responsável pela segurança
  Quero detectar óculos, máscaras, luvas e botas
  Para que a inspeção seja mais completa

  Scenario: Detectar óculos de proteção
    Given que um quadro de vídeo contém uma pessoa usando óculos de proteção
    When o sistema analisa o quadro
    Then o EPI "óculos" é identificado individualmente com caixa delimitadora

  Scenario: Detectar máscara de proteção
    Given que um quadro de vídeo contém uma pessoa usando máscara de proteção
    When o sistema analisa o quadro
    Then o EPI "máscara" é identificado individualmente com caixa delimitadora

  Scenario: Detectar luvas de proteção
    Given que um quadro de vídeo contém uma pessoa usando luvas de proteção
    When o sistema analisa o quadro
    Then o EPI "luvas" é identificado individualmente com caixa delimitadora

  Scenario: Detectar botas de segurança
    Given que um quadro de vídeo contém uma pessoa usando botas de segurança
    When o sistema analisa o quadro
    Then o EPI "botas" é identificado individualmente com caixa delimitadora

  Scenario: Informar lista de EPIs encontrados
    Given que um quadro de vídeo contém uma pessoa usando múltiplos EPIs
    When o sistema analisa o quadro
    Then o sistema informa quais EPIs foram encontrados para cada pessoa detectada
