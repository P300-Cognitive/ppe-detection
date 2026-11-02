# Spec 001: Captura e processamento de vídeo

**Status:** retroativa | **Histórias:** US-001, US-002 | **Cenários:** [`features/epic1_captura_video/`](../../features/epic1_captura_video/)

## Contexto

O sistema precisa receber vídeo de câmeras e processá-lo continuamente, sem intervenção manual. Esta é a entrada de todo o restante do fluxo: sem vídeo, nenhuma verificação de EPI acontece.

## Histórias de usuário

**US-001 – Capturar vídeo de uma câmera.** Como operador, quero conectar uma câmera ao sistema, para que as imagens possam ser analisadas automaticamente.

**US-002 – Processar vídeo em tempo real.** Como operador, quero que os quadros sejam processados continuamente, para que a análise de EPI ocorra sem intervenção manual.

## Requisitos funcionais

| ID | Requisito | Origem | Estado | Observação |
|---|---|---|---|---|
| FR-001 | Aceitar câmera USB | US-001 | Atendido | |
| FR-002 | Aceitar stream RTSP | US-001 | Atendido | O cenário de sucesso exige um servidor RTSP local, indisponível na execução |
| FR-003 | Exibir o vídeo em tempo real | US-001 | Atendido | Pelo dashboard ou por janela local. O cenário só verifica que a captura está ativa |
| FR-004 | Informar falha de conexão quando a câmera estiver indisponível | US-001 | Parcial | O módulo gera erro, mas o fluxo só o imprime no console. O dashboard continua em "Aguardando camera..." |
| FR-005 | Iniciar o processamento automaticamente após a conexão | US-002 | Atendido | |
| FR-006 | Manter taxa mínima configurável de FPS | US-002 | Não atendido | O valor configurado funciona como teto. Nada detecta ou informa quando a taxa fica abaixo dele |
| FR-007 | Continuar operando com pequenas perdas de quadros | US-002 | Parcial | Quadros perdidos são ignorados, mas não há reconexão nem aviso em uma queda prolongada. A simulação usada no cenário não faz nada |

## Casos de borda

- A câmera conecta e depois cai: hoje o fluxo pode continuar em espera sem avisar ninguém.
- O índice USB não existe: gera erro de conexão.
- A URL RTSP não responde: gera erro depois de vários segundos (cerca de 14 s na execução dos testes).

## Critérios de sucesso

- O operador vê na interface, sem consultar o console, quando uma câmera está indisponível.
- Com taxa abaixo do mínimo configurado, o sistema sinaliza a degradação.
- Depois de uma queda temporária, a captura volta sem reiniciar a aplicação.

## Esclarecimentos pendentes

- [NEEDS CLARIFICATION] O que o sistema deve fazer quando a taxa fica abaixo do mínimo: apenas avisar, ou reduzir a carga (por exemplo, pular quadros)?
- [NEEDS CLARIFICATION] Qual a política de reconexão: intervalo entre tentativas e momento em que a câmera é declarada offline?
