Feature: US-008 – Associar capacete a uma pessoa
  Como responsável pela segurança
  Quero relacionar cada capacete à pessoa correspondente
  Para que seja possível detectar ausência de proteção

  Scenario: Associar capacete localizado sobre a cabeça da pessoa
    Given que um quadro contém uma pessoa com capacete sobre a cabeça
    When o sistema realiza a associação de EPIs
    Then o capacete é associado à pessoa cuja região da cabeça está imediatamente abaixo

  Scenario: Não associar capacete incorretamente a pessoa próxima
    Given que um quadro contém "2" pessoas próximas, onde apenas uma usa capacete
    When o sistema realiza a associação de EPIs
    Then o capacete é associado apenas à pessoa que o está utilizando
    And a segunda pessoa é identificada como sem capacete
