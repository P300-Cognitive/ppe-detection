Feature: US-015 – Registrar vídeo da ocorrência
  Como responsável pela segurança
  Quero armazenar alguns segundos antes e depois do evento
  Para que exista contexto da ocorrência

  Scenario: Vídeo contém período pré-configurável antes do alerta
    Given que o período pré-alerta está configurado como "10" segundos
    When uma ocorrência de não conformidade é registrada
    Then o arquivo de vídeo salvo contém os "10" segundos anteriores ao alerta

  Scenario: Vídeo contém período pós-configurável após o alerta
    Given que o período pós-alerta está configurado como "5" segundos
    When uma ocorrência de não conformidade é registrada
    Then o arquivo de vídeo salvo contém os "5" segundos posteriores ao alerta
