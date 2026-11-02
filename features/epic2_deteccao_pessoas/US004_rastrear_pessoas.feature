Feature: US-004 – Rastrear pessoas entre quadros
  Como responsável pela segurança
  Quero acompanhar a mesma pessoa ao longo do vídeo
  Para que alertas não sejam gerados repetidamente

  Scenario: Atribuir ID persistente a uma pessoa
    Given que uma pessoa é detectada no quadro atual
    When o sistema processa o quadro seguinte com a mesma pessoa
    Then a pessoa mantém o mesmo ID entre os dois quadros

  Scenario: Manter ID estável enquanto pessoa está visível
    Given que uma pessoa com ID "42" está sendo rastreada
    When a pessoa permanece visível por "30" quadros consecutivos
    Then o ID "42" permanece associado à mesma pessoa durante todos os quadros

  Scenario: Rastrear múltiplas pessoas simultaneamente
    Given que um quadro de vídeo contém "3" pessoas detectadas
    When o sistema processa os quadros seguintes
    Then cada uma das "3" pessoas mantém seu próprio ID persistente e distinto
