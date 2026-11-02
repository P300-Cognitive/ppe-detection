Feature: US-016 – Enviar notificação automática
  Como responsável pela segurança
  Quero receber alertas instantâneos
  Para que possa agir rapidamente

  Scenario: Enviar notificação via Telegram
    Given que a integração com Telegram está configurada
    When uma não conformidade de EPI é detectada
    Then o sistema envia uma mensagem de alerta para o canal do Telegram configurado

  Scenario: Enviar notificação via e-mail
    Given que a integração com e-mail está configurada
    When uma não conformidade de EPI é detectada
    Then o sistema envia um e-mail de alerta para o destinatário configurado

  Scenario: Notificação inclui imagem da ocorrência
    Given que a integração de notificação está configurada
    When uma não conformidade de EPI é detectada e o alerta é enviado
    Then a notificação inclui a imagem capturada da ocorrência como anexo ou inline
