# Constituição do Projeto PPE Detection

**Versão:** 1.0.0 | **Status:** proposta, aguardando ratificação pelo time | **Data:** 2026-11-02

Este documento define as regras que valem para todo o desenvolvimento do projeto. Quando uma spec, um plano ou um trecho de código entrar em conflito com ele, a constituição prevalece, ou então é emendada conforme a seção [Governança](#governança).

Os princípios foram derivados do código existente, dos critérios de aceitação e das lacunas encontradas na migração. Nenhum deles foi decidido formalmente pelo time ainda.

## Propósito

O sistema monitora câmeras, verifica o uso de EPIs e aciona as pessoas responsáveis quando há não conformidade. Um resultado errado pode ter consequência física: um relatório de conformidade falso ou um alerta que não chega deixam um risco real sem tratamento. Os princípios abaixo partem dessa premissa.

## Princípios

### I. Spec antes do código

Toda mudança de comportamento segue a ordem **spec → plano → tarefas → código**.

- A `spec.md` descreve o quê e por quê, sem detalhes de implementação.
- O `plan.md` descreve como, incluindo módulos e decisões técnicas.
- O `tasks.md` lista o trabalho rastreável até um requisito (`FR-xxx`).
- Correções que não mudam o comportamento especificado dispensam spec nova, mas continuam precisando de tarefa.

### II. Aceitação executável

Todo requisito funcional tem pelo menos um cenário Gherkin em `features/`, e o cenário precisa exercitar o comportamento real.

- É proibido validar só a existência de atributo, valor de configuração ou metadado quando o requisito fala de um efeito observável.
- Um cenário de detecção usa um quadro que contém o objeto a ser detectado, nunca um quadro vazio.
- Um cenário de integração usa os mesmos tipos que a produção usa. Objetos falsos (`SimpleNamespace`) não substituem o modelo real em fronteiras entre módulos.
- Cenários que dependem de hardware ou de serviço externo recebem uma tag e têm alternativa sem essa dependência (arquivo de vídeo, servidor local).

### III. Estado honesto

- Uma tarefa só é marcada como concluída quando o comportamento funciona **integrado ao fluxo de produção** e o cenário correspondente passa.
- Código sem chamador em produção conta como não entregue.
- Valores fixos nunca são apresentados como resultado. Uma métrica sem dados reais aparece como indisponível, e nunca com um valor padrão favorável como 100%.
- Stubs ficam explícitos em uma tarefa aberta.

### IV. Falha segura e visível

- Falhas que reduzem a proteção precisam chegar ao operador pela interface, e não apenas ao console. Exemplos: câmera offline, modelo ausente, notificação não entregue.
- Sem capacidade de verificar EPIs, o sistema informa "não verificado". Ele não declara conformidade nem violação.
- Exceções não são engolidas em silêncio, e um envio só é dado como bem-sucedido depois que o destino confirma.

### V. Tempo real não bloqueante

O laço de vídeo não pode depender de operações lentas. Rede, envio de e-mail e gravação de evidências rodam fora do laço, com limites definidos de fila e de uso de recursos.

### VI. Privacidade e proteção de evidências

Imagens de trabalhadores são dados pessoais e devem ser tratadas como tal.

- Evidências, relatórios gerados e modelos não são versionados no Git.
- O acesso ao dashboard, aos streams e às evidências exige autenticação antes de qualquer implantação fora de ambiente local.
- A retenção é definida e aplicada automaticamente. O prazo ainda depende de decisão, registrada em [specs/006-alertas-evidencias/spec.md](../specs/006-alertas-evidencias/spec.md).

### VII. Segredos fora do código

Credenciais vêm de variáveis de ambiente ou de um cofre, e nunca são versionadas. Logs e mensagens de erro não expõem tokens nem URLs de câmera com credenciais.

### VIII. Módulos coesos e substituíveis

- Cada etapa do fluxo fica em um módulo de `src/` com uma responsabilidade.
- Tipos compartilhados ficam em `src/core/models.py`.
- A orquestração fica em um único lugar, e os módulos de domínio não conhecem a interface web.
- Não coexistem duas implementações da mesma responsabilidade.

### IX. Configuração sem reinício

Regras por câmera, limiares e modelo ativo são alterados em tempo de execução e passam a valer na detecção seguinte, sem interromper o vídeo. Alterar um valor armazenado não basta: a mudança precisa surtir efeito na detecção.

### X. Dependências enxutas

`requirements.txt` declara tudo o que o código importa e nada além disso. Toda dependência nova é justificada no `plan.md`.

## Glossário canônico

O código usa nomes em inglês e a documentação usa português. Toda fronteira (cenários, API, interface) precisa usar o identificador canônico da tabela ou converter para ele explicitamente.

| Identificador canônico | Português |
|---|---|
| `helmet` | capacete |
| `vest` | colete refletivo |
| `glasses` | óculos de proteção |
| `mask` | máscara de proteção |
| `gloves` | luvas de proteção |
| `boots` | botas de segurança |

| Termo | Significado |
|---|---|
| Não conformidade | Pessoa sem um EPI obrigatório naquela câmera |
| Confirmação | N quadros **consecutivos** de ausência do mesmo EPI, para a mesma pessoa |
| Alerta | Aviso gerado uma vez quando a ausência é confirmada |
| Ocorrência | Registro persistente do alerta, com pessoa, câmera, EPI e horário |
| Evidência | Imagem ou vídeo associado a uma ocorrência |

## Stack

- **Linguagem:** Python 3.10 ou superior
- **Visão computacional:** OpenCV, Ultralytics YOLOv8 e ByteTrack (`supervision`)
- **Web:** Flask, com stream MJPEG e API REST
- **Relatórios:** ReportLab (PDF) e openpyxl (Excel)
- **Aceitação:** behave (Gherkin)

## Convenções

- Documentação, cenários e mensagens ao usuário ficam em português do Brasil.
- Identificadores de código ficam em inglês.
- Specs ficam em `specs/NNN-nome-curto/`, cada uma com `spec.md`, `plan.md` e `tasks.md`.
- Requisitos usam `FR-NNN` e tarefas usam `TNNN`, ambos numerados por spec. Em referências entre specs, use o formato `005/FR-009`.
- Dúvidas sem decisão ficam marcadas com `[NEEDS CLARIFICATION]` na spec.

## Definição de pronto

Uma tarefa está pronta quando:

1. O requisito de origem está identificado.
2. O comportamento funciona pelo fluxo de produção (`main.py`), e não apenas pelo módulo isolado.
3. O cenário de aceitação exercita o comportamento real e passa.
4. Toda a suíte de cenários foi executada, sem novas falhas.
5. A spec, o plano, as tarefas e o README refletem o estado atual.

## Governança

- Alterações nesta constituição são feitas por pull request, com justificativa e aprovação do time.
- O versionamento segue SemVer:
  - **MAJOR** quando um princípio é removido ou redefinido.
  - **MINOR** quando um princípio ou seção é adicionado.
  - **PATCH** quando há ajuste de redação.
- Cada `plan.md` traz uma verificação contra esta constituição. Uma violação aceita temporariamente precisa ter tarefa aberta.
- Os arquivos de `features/` continuam sendo os critérios de aceitação executáveis. `histories.md` é mantido como referência histórica.
