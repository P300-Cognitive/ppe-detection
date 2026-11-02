Feature: US-009 – Associar colete a uma pessoa
  Como responsável pela segurança
  Quero relacionar cada colete à pessoa correspondente
  Para que seja possível validar o uso correto do equipamento

  Scenario: Associar colete localizado na região do tronco
    Given que um quadro contém uma pessoa com colete na região do tronco
    When o sistema realiza a associação de EPIs
    Then o colete é associado à pessoa cuja região do tronco está sobreposta ao colete detectado

  Scenario: Não associar colete incorretamente entre pessoas próximas
    Given que um quadro contém "2" pessoas próximas, onde apenas uma usa colete
    When o sistema realiza a associação de EPIs
    Then o colete é associado apenas à pessoa que o está utilizando
    And a segunda pessoa é identificada como sem colete
