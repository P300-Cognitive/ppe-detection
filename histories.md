# Épico 1 - Captura e Processamento de Vídeo

### US-001 – Capturar vídeo de uma câmera

**Como** operador do sistema
**Quero** conectar uma câmera ao sistema
**Para que** as imagens possam ser analisadas automaticamente.

**Critérios de Aceitação**

* O sistema aceita câmera USB.
* O sistema aceita stream RTSP.
* O sistema exibe o vídeo em tempo real.
* O sistema informa falha de conexão quando a câmera estiver indisponível.

---

### US-002 – Processar vídeo em tempo real

**Como** operador do sistema
**Quero** que os quadros sejam processados continuamente
**Para que** a análise de EPI ocorra sem intervenção manual.

**Critérios de Aceitação**

* O processamento ocorre automaticamente após a conexão da câmera.
* O sistema mantém taxa mínima configurável de FPS.
* O sistema continua operando mesmo com pequenas perdas de quadros.

---

# Épico 2 - Detecção de Pessoas

### US-003 – Detectar pessoas na imagem

**Como** responsável pela segurança
**Quero** identificar pessoas presentes na cena
**Para que** seja possível verificar o uso de EPIs.

**Critérios de Aceitação**

* O sistema desenha uma caixa delimitadora em cada pessoa detectada.
* Pessoas parcialmente visíveis também podem ser detectadas.
* Cada pessoa recebe um identificador temporário.

---

### US-004 – Rastrear pessoas entre quadros

**Como** responsável pela segurança
**Quero** acompanhar a mesma pessoa ao longo do vídeo
**Para que** alertas não sejam gerados repetidamente.

**Critérios de Aceitação**

* Cada pessoa recebe um ID persistente.
* O ID permanece estável enquanto a pessoa estiver visível.
* O sistema suporta múltiplas pessoas simultaneamente.

---

# Épico 3 - Detecção de EPI

### US-005 – Detectar capacetes

**Como** responsável pela segurança
**Quero** identificar capacetes na imagem
**Para que** o sistema valide o uso correto do EPI.

**Critérios de Aceitação**

* Capacetes são detectados com caixa delimitadora.
* O sistema exibe a confiança da detecção.
* Capacetes de diferentes cores são reconhecidos.

---

### US-006 – Detectar coletes refletivos

**Como** responsável pela segurança
**Quero** identificar coletes refletivos
**Para que** o sistema valide a conformidade dos trabalhadores.

**Critérios de Aceitação**

* Coletes são detectados independentemente da cor.
* O sistema identifica o colete associado à pessoa correta.

---

### US-007 – Detectar outros EPIs

**Como** responsável pela segurança
**Quero** detectar óculos, máscaras, luvas e botas
**Para que** a inspeção seja mais completa.

**Critérios de Aceitação**

* Cada EPI é identificado individualmente.
* O sistema informa quais EPIs foram encontrados.

---

# Épico 4 - Associação Pessoa x EPI

### US-008 – Associar capacete a uma pessoa

**Como** responsável pela segurança
**Quero** relacionar cada capacete à pessoa correspondente
**Para que** seja possível detectar ausência de proteção.

**Critérios de Aceitação**

* O capacete deve estar localizado sobre a região da cabeça.
* Capacetes próximos de outras pessoas não devem ser associados incorretamente.

---

### US-009 – Associar colete a uma pessoa

**Como** responsável pela segurança
**Quero** relacionar cada colete à pessoa correspondente
**Para que** seja possível validar o uso correto do equipamento.

**Critérios de Aceitação**

* O colete deve estar localizado na região do tronco.
* O sistema evita associações incorretas entre pessoas próximas.

---

# Épico 5 - Regras de Segurança

### US-010 – Identificar ausência de capacete

**Como** responsável pela segurança
**Quero** ser alertado quando uma pessoa estiver sem capacete
**Para que** riscos sejam reduzidos.

**Critérios de Aceitação**

* O alerta é exibido somente após confirmação configurável.
* O sistema identifica qual pessoa está sem capacete.

---

### US-011 – Identificar ausência de colete

**Como** responsável pela segurança
**Quero** ser alertado quando uma pessoa estiver sem colete
**Para que** medidas corretivas sejam tomadas.

**Critérios de Aceitação**

* O alerta ocorre apenas após validação da ausência.
* O sistema registra o evento.

---

### US-012 – Configurar regras por ambiente

**Como** administrador
**Quero** definir quais EPIs são obrigatórios em cada local
**Para que** o sistema reflita as normas da operação.

**Critérios de Aceitação**

* Cada câmera pode possuir regras próprias.
* É possível exigir diferentes combinações de EPIs.

---

# Épico 6 - Alertas e Evidências

### US-013 – Exibir alerta visual

**Como** operador
**Quero** visualizar imediatamente uma não conformidade
**Para que** eu possa agir rapidamente.

**Critérios de Aceitação**

* A pessoa aparece destacada em vermelho.
* O motivo do alerta é exibido.

---

### US-014 – Registrar imagem da ocorrência

**Como** responsável pela segurança
**Quero** salvar evidências da infração
**Para que** seja possível auditoria posterior.

**Critérios de Aceitação**

* O sistema salva uma imagem da ocorrência.
* A imagem contém data e hora.

---

### US-015 – Registrar vídeo da ocorrência

**Como** responsável pela segurança
**Quero** armazenar alguns segundos antes e depois do evento
**Para que** exista contexto da ocorrência.

**Critérios de Aceitação**

* O vídeo contém período pré-configurável antes do alerta.
* O vídeo contém período pós-configurável após o alerta.

---

### US-016 – Enviar notificação automática

**Como** responsável pela segurança
**Quero** receber alertas instantâneos
**Para que** possa agir rapidamente.

**Critérios de Aceitação**

* O sistema suporta Telegram.
* O sistema suporta e-mail.
* O alerta inclui imagem da ocorrência.

---

# Épico 7 - Dashboard e Monitoramento

### US-017 – Visualizar câmeras em tempo real

**Como** operador
**Quero** acompanhar todas as câmeras em um painel único
**Para que** o monitoramento seja centralizado.

**Critérios de Aceitação**

* O painel suporta múltiplas câmeras.
* Os alertas são exibidos em tempo real.

---

### US-018 – Consultar histórico de ocorrências

**Como** responsável pela segurança
**Quero** pesquisar ocorrências passadas
**Para que** possa realizar auditorias.

**Critérios de Aceitação**

* Filtro por data.
* Filtro por câmera.
* Filtro por tipo de EPI.

---

### US-019 – Gerar relatórios

**Como** gestor de segurança
**Quero** visualizar indicadores de conformidade
**Para que** possa acompanhar a evolução da operação.

**Critérios de Aceitação**

* Relatório por período.
* Quantidade de infrações.
* Taxa de conformidade.
* Exportação para PDF e Excel.

---

# Épico 8 - Administração

### US-020 – Gerenciar câmeras

**Como** administrador
**Quero** cadastrar e remover câmeras
**Para que** o ambiente seja configurado facilmente.

**Critérios de Aceitação**

* Cadastro de RTSP.
* Teste de conectividade.
* Habilitar e desabilitar câmeras.

---

### US-021 – Gerenciar modelos de IA

**Como** administrador
**Quero** atualizar modelos treinados
**Para que** a precisão possa ser melhorada sem alterar o sistema.

**Critérios de Aceitação**

* Upload de novo modelo.
* Validação do arquivo.
* Troca sem reinstalação da aplicação.

---

### US-022 – Configurar limiares de confiança

**Como** administrador
**Quero** ajustar a sensibilidade das detecções
**Para que** seja possível reduzir falsos positivos e falsos negativos.

**Critérios de Aceitação**

* Configuração por classe de EPI.
* Alteração sem reinicializar o sistema.
