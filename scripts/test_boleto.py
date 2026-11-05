import unittest
from datetime import date

from boleto import comparar, dv_modulo10, dv_modulo11, ler_linha, alertas, vencimento

ORIGINAL = "34191.79001 10435.100473 91020.150008 9 16050000184750"
SUSPEITO = "03399.57318 02881.300004 00007.701014 1 16050000184750"
# Exemplo público de boleto do Banco do Brasil, usado em várias documentações.
EXEMPLO_BB = "00190.50095 40144.816069 06809.350314 3 37370000000100"


class TestBoleto(unittest.TestCase):
    def test_exemplo_publico_confere(self):
        b = ler_linha(EXEMPLO_BB)
        self.assertEqual(b["codigo_barras"], "00193373700000001000500940144816060680935031")
        self.assertTrue(b["dv_geral_ok"])

    def test_le_banco_valor_e_vencimento(self):
        b = ler_linha(ORIGINAL)
        self.assertEqual(b["banco"], "341")
        self.assertEqual(b["valor"], 1847.50)
        self.assertEqual(b["vencimento"], date(2026, 10, 20))

    def test_dv_errado_gera_alerta(self):
        adulterada = ORIGINAL.replace(" 9 ", " 8 ")
        self.assertFalse(ler_linha(adulterada)["dv_geral_ok"])
        self.assertTrue(alertas(ler_linha(adulterada)))

    def test_banco_diferente_do_logo(self):
        avisos = alertas(ler_linha(SUSPEITO), banco_esperado="341")
        self.assertTrue(any("033" in a for a in avisos))

    def test_comparacao_mostra_o_que_mudou(self):
        diferencas = {c for c, _, _ in comparar(ler_linha(ORIGINAL), ler_linha(SUSPEITO))}
        self.assertIn("banco", diferencas)
        self.assertNotIn("valor", diferencas)
        self.assertNotIn("vencimento", diferencas)

    def test_fator_depois_da_virada_de_2025(self):
        self.assertEqual(vencimento(1000, hoje=date(2026, 1, 1)), date(2025, 2, 22))

    def test_tamanho_errado(self):
        with self.assertRaises(ValueError):
            ler_linha("1234")

    def test_modulos(self):
        self.assertEqual(dv_modulo10("001905009"), 5)
        self.assertEqual(dv_modulo11("0019373700000001000500940144816060680935031"), 3)


if __name__ == "__main__":
    unittest.main()
