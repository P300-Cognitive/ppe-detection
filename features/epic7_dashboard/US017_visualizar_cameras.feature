Feature: US-017 – Visualizar câmeras em tempo real
  Como operador
  Quero acompanhar todas as câmeras em um painel único
  Para que o monitoramento seja centralizado

  Scenario: Painel exibe múltiplas câmeras simultaneamente
    Given que "4" câmeras estão cadastradas e ativas no sistema
    When o operador acessa o painel de monitoramento
    Then o painel exibe os streams de todas as "4" câmeras simultaneamente

  Scenario: Alertas são exibidos em tempo real no painel
    Given que o painel de monitoramento está aberto
    When uma não conformidade de EPI é detectada em qualquer câmera
    Then o alerta é exibido no painel em tempo real sem necessidade de atualização manual
