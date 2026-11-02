# Spec 008: Administração

**Status:** retroativa | **Histórias:** US-020, US-021, US-022 | **Cenários:** [`features/epic8_administracao/`](../../features/epic8_administracao/)

## Contexto

Administradores configuram câmeras, modelos de IA e sensibilidade sem alterar código nem reiniciar o sistema. Os módulos guardam essas configurações, mas ainda não as ligam à detecção.

## Histórias de usuário

**US-020 – Gerenciar câmeras.** Como administrador, quero cadastrar e remover câmeras, para que o ambiente seja configurado facilmente.

**US-021 – Gerenciar modelos de IA.** Como administrador, quero atualizar modelos treinados, para que a precisão possa ser melhorada sem alterar o sistema.

**US-022 – Configurar limiares de confiança.** Como administrador, quero ajustar a sensibilidade das detecções, para que seja possível reduzir falsos positivos e falsos negativos.

## Requisitos funcionais

| ID | Requisito | Origem | Estado | Observação |
|---|---|---|---|---|
| FR-001 | Cadastrar câmera com URL RTSP | US-020 | Parcial | Fica só em memória, a URL não é validada e a câmera cadastrada não passa a ser monitorada |
| FR-002 | Remover câmera | US-020 | Não atendido | Consta na história, mas não há função nem cenário |
| FR-003 | Testar a conectividade da câmera | US-020 | Parcial | Existe no módulo, sem rota nem tela. A latência nunca é preenchida |
| FR-004 | Habilitar câmera e iniciar o monitoramento | US-020 | Parcial | Só muda um campo, sem rota nem tela. O monitoramento não começa |
| FR-005 | Desabilitar câmera e parar o monitoramento | US-020 | Parcial | Só muda um campo, sem rota nem tela. O monitoramento não para |
| FR-006 | Enviar um novo modelo e listá-lo como disponível | US-021 | Parcial | Existe no módulo, sem rota nem tela. A lista se perde ao reiniciar |
| FR-007 | Rejeitar arquivo inválido informando o motivo | US-021 | Parcial | Só verifica a extensão: um arquivo `.pt` de 4 bytes é aceito |
| FR-008 | Trocar o modelo ativo sem reiniciar | US-021 | Não atendido | O modelo é carregado no início do fluxo, que nunca consulta o modelo ativo |
| FR-009 | Definir limiar de confiança por classe de EPI | US-022 | Não atendido | A tela e a rota guardam o valor, mas a detecção não o lê |
| FR-010 | Aplicar limiares diferentes por classe | US-022 | Não atendido | A detecção usa um único valor, `--confidence` |
| FR-011 | Alterar o limiar sem reiniciar | US-022 | Não atendido | O valor muda sem reiniciar, mas não produz efeito |

## Casos de borda

- Modelo ativo removido ou corrompido: o sistema precisa manter o modelo anterior.
- Modelo com classes incompatíveis: precisa ser rejeitado na ativação.
- Limiar fora de 0 a 1: rejeitado (retorna 422 na API).
- Câmera removida enquanto monitorada: o fluxo daquela câmera precisa encerrar corretamente.

## Critérios de sucesso

- Uma câmera cadastrada é monitorada sem reiniciar, e uma desabilitada deixa de ser processada.
- Depois de elevar o limiar de uma classe, detecções abaixo dele deixam de aparecer no quadro seguinte.
- Depois de ativar um modelo, o quadro seguinte usa o novo modelo, sem interromper o vídeo.
- As configurações sobrevivem a uma reinicialização.
- Cada operação tem tela e rota.

## Esclarecimentos pendentes

- [NEEDS CLARIFICATION] Quem pode administrar? O perfil de administrador depende da autenticação de [009/FR-008](../009-orquestracao-plataforma/spec.md).
- [NEEDS CLARIFICATION] Além de `.pt`, o sistema precisa aceitar `.onnx` e `.tflite`? O cenário cita só `.pt`, o código aceita os três, e `.tflite` nunca foi testado.
