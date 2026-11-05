# Checklist: "estão mandando boleto falso em nosso nome"

Roteiro que uso quando um cliente desconfia que o e-mail da empresa foi usado num golpe. A ordem importa: primeiro se proteger, depois provar o que aconteceu.

## 1. Conter (primeiros minutos)

- [ ] Avisar quem recebeu pra **não pagar** nada até a confirmação.
- [ ] Pedir o e-mail suspeito **como anexo** (.eml), não encaminhado. Encaminhar perde os cabeçalhos originais.
- [ ] Pedir também o e-mail original, se o cliente tiver.

## 2. Analisar o boleto

- [ ] O código do banco na linha digitável (3 primeiros dígitos) é o mesmo banco do logo?
- [ ] O CNPJ e o nome do beneficiário são os da empresa?
- [ ] Rodar `python scripts/boleto.py --comparar ORIGINAL SUSPEITO`.

DV correto não quer dizer boleto legítimo. O golpista consegue gerar um boleto válido em outro banco.

## 3. Analisar o cabeçalho do e-mail suspeito

Colar o cabeçalho no [Google Admin Toolbox Messageheader](https://toolbox.googleapps.com/apps/messageheader/).

- [ ] **Message-ID:** é igual ao de algum e-mail legítimo? Se for, a mensagem foi copiada de uma caixa que recebeu o original.
- [ ] **Received:** por quais servidores passou? Algum fora do provedor da empresa?
- [ ] **SPF, DKIM e DMARC:** passaram ou falharam? Falha indica envio por servidor não autorizado.
- [ ] **Return-Path e Reply-To:** apontam pra outro domínio?

## 4. Conferir o lado da empresa (Google Workspace)

- [ ] **Pesquisa de registros de e-mail:** a mensagem saiu do domínio na data do e-mail suspeito?
- [ ] **Logins da conta remetente:** acessos de IP, país ou dispositivo fora do padrão? Falhas de senha em sequência?
- [ ] **Regras de encaminhamento e filtros** da conta: alguém criou regra pra copiar ou esconder e-mails?
- [ ] **Apps com acesso OAuth** à conta: algum desconhecido?
- [ ] **Delegação de caixa:** alguém recebeu acesso recentemente?

## 5. Concluir e orientar

| O que os logs mostram | Conclusão provável |
|---|---|
| Envio saiu do domínio + login suspeito | Conta da empresa comprometida |
| Nenhum envio + Message-ID igual ao original | Caixa de quem recebeu foi comprometida |
| Nenhum envio + SPF/DKIM falhando | E-mail forjado de servidor externo (spoofing) |

- [ ] Relatório pro cliente com as evidências (prints ou exportações dos logs).
- [ ] Recomendações pros dois lados: troca de senha, 2FA, confirmação de boleto por telefone.
- [ ] Se o domínio não tem DMARC com política `quarantine` ou `reject`, incluir isso nas recomendações.
