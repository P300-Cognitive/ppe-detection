Feature: US-003 – Detectar pessoas na imagem
  Como responsável pela segurança
  Quero identificar pessoas presentes na cena
  Para que seja possível verificar o uso de EPIs

  Scenario: Detectar pessoa com caixa delimitadora
    Given que um quadro de vídeo com uma pessoa visível está disponível
    When o sistema analisa o quadro
    Then uma caixa delimitadora é desenhada ao redor da pessoa detectada

  Scenario: Detectar pessoa parcialmente visível
    Given que um quadro de vídeo contém uma pessoa parcialmente fora do enquadramento
    When o sistema analisa o quadro
    Then a pessoa parcialmente visível é detectada com caixa delimitadora

  Scenario: Atribuir identificador temporário a cada pessoa
    Given que um quadro de vídeo contém múltiplas pessoas
    When o sistema analisa o quadro
    Then cada pessoa detectada recebe um identificador temporário único
