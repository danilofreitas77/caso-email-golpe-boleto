"""
Lê a linha digitável de um boleto bancário (47 dígitos) e mostra o que ela diz
de verdade: banco, valor, vencimento e se os dígitos verificadores batem.

Serve pra conferir rapidamente se o banco do logo é o mesmo banco do código,
e pra comparar dois boletos que deveriam ser iguais.

Uso:
    python boleto.py "34191.79001 01043.510047 91020.150008 1 96130000150000"
    python boleto.py LINHA --banco-esperado 341
    python boleto.py --comparar LINHA_ORIGINAL LINHA_SUSPEITA

Só cobre boleto bancário (começa com o código do banco). Boleto de
concessionária (água, luz, tributo) começa com 8 e tem outro formato.
"""

import argparse
import re
import sys
from datetime import date, timedelta

BANCOS = {
    "001": "Banco do Brasil",
    "033": "Santander",
    "104": "Caixa Econômica Federal",
    "237": "Bradesco",
    "341": "Itaú",
    "260": "Nu Pagamentos (Nubank)",
    "077": "Banco Inter",
    "336": "C6 Bank",
    "748": "Sicredi",
    "756": "Sicoob",
}

# O fator de vencimento conta dias a partir de 07/10/1997. Ele chegou em 9999
# em 21/02/2025 e voltou pra 1000 em 22/02/2025. Por isso um mesmo fator pode
# apontar pra duas datas; o script fica com a mais próxima de hoje.
BASE_ANTIGA = date(1997, 10, 7)
BASE_NOVA = date(2025, 2, 22) - timedelta(days=1000)


def so_digitos(texto):
    return re.sub(r"\D", "", texto)


def dv_modulo10(numero):
    soma = 0
    peso = 2
    for d in reversed(numero):
        produto = int(d) * peso
        soma += produto // 10 + produto % 10
        peso = 1 if peso == 2 else 2
    return (10 - soma % 10) % 10


def dv_modulo11(numero):
    soma = 0
    peso = 2
    for d in reversed(numero):
        soma += int(d) * peso
        peso = 2 if peso == 9 else peso + 1
    resto = 11 - soma % 11
    return 1 if resto in (0, 10, 11) else resto


def vencimento(fator, hoje=None):
    if fator == 0:
        return None
    hoje = hoje or date.today()
    candidatas = [BASE_ANTIGA + timedelta(days=fator), BASE_NOVA + timedelta(days=fator)]
    return min(candidatas, key=lambda d: abs((d - hoje).days))


def ler_linha(linha):
    """Quebra a linha digitável nos campos e confere os três DVs de campo e o DV geral."""
    n = so_digitos(linha)
    if len(n) != 47:
        raise ValueError(f"A linha digitável precisa ter 47 dígitos, veio com {len(n)}.")
    if n[0] == "8":
        raise ValueError("Isso é boleto de concessionária ou tributo, não boleto bancário.")

    campo1, dv1 = n[0:9], int(n[9])
    campo2, dv2 = n[10:20], int(n[20])
    campo3, dv3 = n[21:31], int(n[31])
    dv_geral = int(n[32])
    fator, valor = int(n[33:37]), int(n[37:47])

    # Código de barras (44 posições) montado a partir da linha digitável.
    barras = n[0:4] + n[32] + n[33:47] + campo1[4:9] + campo2 + campo3

    banco = n[0:3]
    return {
        "linha": n,
        "banco": banco,
        "banco_nome": BANCOS.get(banco, "desconhecido"),
        "moeda": n[3],
        "valor": valor / 100,
        "fator_vencimento": fator,
        "vencimento": vencimento(fator),
        "campo_livre": barras[19:44],
        "codigo_barras": barras,
        "dv_campo1_ok": dv_modulo10(campo1) == dv1,
        "dv_campo2_ok": dv_modulo10(campo2) == dv2,
        "dv_campo3_ok": dv_modulo10(campo3) == dv3,
        "dv_geral_ok": dv_modulo11(barras[0:4] + barras[5:44]) == dv_geral,
    }


def alertas(boleto, banco_esperado=None):
    avisos = []
    if not all(boleto[k] for k in ("dv_campo1_ok", "dv_campo2_ok", "dv_campo3_ok", "dv_geral_ok")):
        avisos.append("Dígito verificador não confere. Linha digitada errada ou adulterada.")
    if boleto["moeda"] != "9":
        avisos.append("Código de moeda diferente de 9 (real).")
    if banco_esperado and boleto["banco"] != banco_esperado.zfill(3):
        esperado = BANCOS.get(banco_esperado.zfill(3), banco_esperado)
        avisos.append(
            f"O código é do banco {boleto['banco']} ({boleto['banco_nome']}), "
            f"mas o esperado era {banco_esperado.zfill(3)} ({esperado})."
        )
    return avisos


def comparar(original, suspeito):
    campos = ["banco", "banco_nome", "valor", "vencimento", "campo_livre"]
    return [(c, original[c], suspeito[c]) for c in campos if original[c] != suspeito[c]]


def mostrar(boleto, banco_esperado=None):
    venc = boleto["vencimento"].strftime("%d/%m/%Y") if boleto["vencimento"] else "sem vencimento"
    print(f"Banco:       {boleto['banco']} ({boleto['banco_nome']})")
    print(f"Valor:       R$ {boleto['valor']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    print(f"Vencimento:  {venc}")
    print(f"Campo livre: {boleto['campo_livre']}")
    ok = all(boleto[k] for k in ("dv_campo1_ok", "dv_campo2_ok", "dv_campo3_ok", "dv_geral_ok"))
    print(f"DVs:         {'ok' if ok else 'COM ERRO'}")
    for aviso in alertas(boleto, banco_esperado):
        print(f"ALERTA:      {aviso}")


def main(argv=None):
    p = argparse.ArgumentParser(description="Confere a linha digitável de um boleto bancário.")
    p.add_argument("linha", nargs="?", help="linha digitável (com ou sem pontos e espaços)")
    p.add_argument("--banco-esperado", help="código do banco que aparece no logo, ex.: 341")
    p.add_argument("--comparar", nargs=2, metavar=("ORIGINAL", "SUSPEITO"))
    args = p.parse_args(argv)

    try:
        if args.comparar:
            original, suspeito = (ler_linha(x) for x in args.comparar)
            print("== Original ==")
            mostrar(original)
            print("\n== Suspeito ==")
            mostrar(suspeito, banco_esperado=original["banco"])
            diferencas = comparar(original, suspeito)
            print("\n== Diferenças ==")
            if not diferencas:
                print("Nenhuma. Os dois boletos apontam pro mesmo pagamento.")
            for campo, a, b in diferencas:
                print(f"{campo}: {a}  ->  {b}")
            return 1 if diferencas else 0

        if not args.linha:
            p.error("informe a linha digitável ou use --comparar")
        boleto = ler_linha(args.linha)
        mostrar(boleto, args.banco_esperado)
        return 1 if alertas(boleto, args.banco_esperado) else 0
    except ValueError as erro:
        print(f"Erro: {erro}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
