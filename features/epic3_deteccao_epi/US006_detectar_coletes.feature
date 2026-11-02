Feature: US-006 – Detectar coletes refletivos
  Como responsável pela segurança
  Quero identificar coletes refletivos
  Para que o sistema valide a conformidade dos trabalhadores

  Scenario: Detectar colete independentemente da cor
    Given que um quadro de vídeo contém uma pessoa usando colete refletivo de qualquer cor
    When o sistema analisa o quadro
    Then o colete é detectado com caixa delimitadora

  Scenario: Associar colete à pessoa correta
    Given que um quadro contém "2" pessoas, sendo uma com colete e outra sem
    When o sistema analisa o quadro
    Then o colete é associado apenas à pessoa que está utilizando o equipamento
