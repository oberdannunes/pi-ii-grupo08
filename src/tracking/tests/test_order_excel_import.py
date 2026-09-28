"""
Testes do serviço de importação de planilhas de frete (OrderExcelImportService).

A ideia aqui é garantir que a planilha enviada pelo admin vire dados
consistentes no banco: país, estados, cidades, clientes, transportadoras
e pedidos. As planilhas são montadas em memória em cada teste, então não
precisamos manter nenhum arquivo .xlsx de exemplo no repositório.
"""
from datetime import date, datetime
from io import BytesIO

import pandas as pd
from django.test import SimpleTestCase, TestCase

from tracking.models import Country, State, City, Customer, Carrier, Order
from tracking.services.order_excel_import import OrderExcelImportService


def make_row(**overrides):
    """
    Monta uma linha de planilha que passa em todas as validações.

    Cada teste só precisa informar o que quer mudar. Por exemplo,
    make_row(UF='XX') gera uma linha idêntica à padrão, mas com UF inválida.
    Colunas com espaço ou acento no nome entram via **{'NOME': valor}.
    """
    row = {
        'TRANSPORTADORA': 'TransX',
        'DT. PEDIDO': datetime(2026, 7, 1),
        'DT. COLETA': None,
        'DT. ENTREGA': None,
        'NFE': 1001,
        'RAZAO SOCIAL': 'Cliente A',
        'CNPJ PARC.': '12345678000199',
        'CIDADE': 'São Paulo',
        'UF': 'SP',
        'PAÍS': 'BRASIL',
    }
    row.update(overrides)
    return row


def make_xlsx(rows, sheet_name='FRETES CONSOLIDADA'):
    """
    Transforma uma lista de linhas em um arquivo .xlsx em memória.

    O serviço só lê a aba 'FRETES CONSOLIDADA'; o parâmetro sheet_name
    existe para conseguirmos simular uma planilha com a aba errada.
    """
    buffer = BytesIO()
    pd.DataFrame(rows).to_excel(buffer, sheet_name=sheet_name, index=False)
    # Volta o "cursor" para o início, senão o pandas lê um arquivo vazio.
    buffer.seek(0)
    return buffer


class ValidateRowTests(SimpleTestCase):
    """
    Regras de validação aplicadas a cada linha, isoladamente.

    Usamos SimpleTestCase porque essas regras não tocam no banco,
    o que deixa os testes bem mais rápidos.
    """

    def setUp(self):
        self.service = OrderExcelImportService()

    def assertHasError(self, row, expected):
        """Confere se a linha foi reprovada e se o motivo esperado aparece entre os erros."""
        is_valid, errors = self.service._validate_row(0, row)
        self.assertFalse(is_valid)
        self.assertTrue(
            any(expected in e for e in errors),
            f'"{expected}" não encontrado em {errors}',
        )

    def test_valid_row(self):
        # Ponto de partida: a linha padrão precisa ser aceita sem nenhum erro.
        self.assertEqual(self.service._validate_row(0, make_row()), (True, None))

    def test_required_columns(self):
        # Testa cada coluna obrigatória com os três jeitos comuns de "vazio"
        # numa planilha: célula sem valor, texto vazio e só espaços.
        for col in self.service.required_columns:
            for empty in (None, '', '   '):
                with self.subTest(col=col, value=empty):
                    self.assertHasError(make_row(**{col: empty}), f'Campo obrigatório vazio: {col}')

    def test_invalid_uf(self):
        # A UF sempre tem exatamente duas letras (SP, RJ, MG...).
        self.assertHasError(make_row(UF='SPO'), 'UF inválido')

    def test_invalid_country(self):
        # Por enquanto só trabalhamos com pedidos dentro do Brasil.
        self.assertHasError(make_row(**{'PAÍS': 'ARGENTINA'}), 'País inválido')

    def test_country_case_insensitive(self):
        # Quem preenche a planilha nem sempre usa maiúsculas; "brasil" também vale.
        is_valid, _ = self.service._validate_row(0, make_row(**{'PAÍS': 'brasil'}))
        self.assertTrue(is_valid)

    def test_invalid_cnpj(self):
        # O CNPJ deve vir só com números: nada de pontuação, letras
        # ou mais de 14 dígitos.
        for cnpj in ('12.345.678/0001-99', 'ABC123', '123456789012345'):
            with self.subTest(cnpj=cnpj):
                self.assertHasError(make_row(**{'CNPJ PARC.': cnpj}), 'CNPJ inválido')

    def test_invalid_dates(self):
        # As três colunas de data passam pela mesma validação.
        for col in ('DT. PEDIDO', 'DT. COLETA', 'DT. ENTREGA'):
            with self.subTest(col=col):
                self.assertHasError(make_row(**{col: 'data-invalida'}), f'Data inválida na coluna {col}')

    def test_invalid_nfe(self):
        # O número da nota fiscal precisa ser numérico.
        self.assertHasError(make_row(NFE='ABC'), 'NFE inválido')


class NormalizeCnpjTests(SimpleTestCase):
    """
    Normalização do CNPJ.

    O Excel costuma "comer" os zeros à esquerda quando a célula é numérica,
    então o serviço precisa recolocá-los para o CNPJ ficar com 14 dígitos.
    """

    def setUp(self):
        self.service = OrderExcelImportService()

    def test_pads_with_leading_zeros(self):
        # Vale tanto para texto quanto para número (como o Excel entrega).
        self.assertEqual(self.service._normalize_cnpj('1234567000199'), '01234567000199')
        self.assertEqual(self.service._normalize_cnpj(1234567000199), '01234567000199')
        # Um CNPJ que já está completo não deve ser alterado.
        self.assertEqual(self.service._normalize_cnpj('12345678000199'), '12345678000199')

    def test_invalid_values_return_empty(self):
        # Valores vazios ou com letras viram string vazia, e o serviço
        # entende isso como "não dá para cadastrar este cliente".
        for value in (None, float('nan'), '', 'ABC123'):
            with self.subTest(value=value):
                self.assertEqual(self.service._normalize_cnpj(value), '')


class ImportFileTests(TestCase):
    """
    Fluxo completo de importação: da planilha até os registros no banco.

    Aqui usamos TestCase, porque cada teste roda numa transação
    que é desfeita no final. Assim um teste não interfere no outro.
    """

    def import_rows(self, rows, **kwargs):
        """Atalho: gera a planilha e já manda para o serviço importar."""
        return OrderExcelImportService().importfile(make_xlsx(rows, **kwargs))

    def test_no_file_raises(self):
        # Sem arquivo não há o que importar, e o serviço avisa com um erro.
        with self.assertRaises(ValueError):
            OrderExcelImportService().importfile(None)

    def test_happy_path(self):
        # Três pedidos, um em cada etapa da entrega:
        #   NFE 1: só foi feito o pedido          -> PENDENTE
        #   NFE 2: já foi coletado                -> TRANSITO
        #   NFE 3: já foi entregue, em outra UF   -> ENTREGUE
        # O pedido 3 também traz UF minúscula e CNPJ sem o zero inicial,
        # para conferir que o serviço normaliza esses dados.
        rows = [
            make_row(NFE=1),
            make_row(NFE=2, **{'DT. COLETA': datetime(2026, 7, 2)}),
            make_row(
                NFE=3,
                TRANSPORTADORA='TransY',
                CIDADE='Rio de Janeiro',
                UF='rj',
                **{
                    'RAZAO SOCIAL': 'Cliente B',
                    'CNPJ PARC.': '1234567000199',
                    'DT. COLETA': datetime(2026, 7, 2),
                    'DT. ENTREGA': datetime(2026, 7, 5),
                },
            ),
        ]

        result = self.import_rows(rows)

        # O resumo devolvido pelo serviço bate com o que foi enviado.
        self.assertTrue(result['success'])
        self.assertEqual(result['rows_valid'], 3)
        self.assertEqual(result['rows_invalid'], 0)
        self.assertEqual(result['orders_data'], {'orders_created': 3, 'orders_errors': 0})

        # O status de cada pedido é deduzido pelas datas preenchidas.
        self.assertEqual(Order.objects.get(nfe='1').status, 'PENDENTE')
        self.assertEqual(Order.objects.get(nfe='2').status, 'TRANSITO')
        order_3 = Order.objects.get(nfe='3')
        self.assertEqual(order_3.status, 'ENTREGUE')
        self.assertEqual(order_3.order_date, date(2026, 7, 1))
        self.assertEqual(order_3.delivery_date, date(2026, 7, 5))

        # Hierarquia geográfica: um país, dois estados e duas cidades,
        # com os nomes gravados sempre em maiúsculas.
        self.assertEqual(Country.objects.count(), 1)
        self.assertEqual(set(State.objects.values_list('id', flat=True)), {'SP', 'RJ'})
        self.assertEqual(set(City.objects.values_list('name', flat=True)), {'SÃO PAULO', 'RIO DE JANEIRO'})
        self.assertEqual(Customer.objects.count(), 2)
        self.assertEqual(Carrier.objects.count(), 2)

        # O CNPJ de 13 dígitos ganhou o zero à esquerda,
        # e o cliente ficou ligado à cidade certa.
        self.assertEqual(order_3.customer.cnpj, '01234567000199')
        self.assertEqual(order_3.customer.city.name, 'RIO DE JANEIRO')

    def test_deduplicates_customers_and_carriers(self):
        # É comum o mesmo cliente e a mesma transportadora aparecerem em
        # várias linhas. Os pedidos são dois, mas os cadastros não se repetem.
        result = self.import_rows([make_row(NFE=1), make_row(NFE=2)])

        self.assertTrue(result['success'])
        self.assertEqual(Customer.objects.count(), 1)
        self.assertEqual(Carrier.objects.count(), 1)
        self.assertEqual(Order.objects.count(), 2)

    def test_reimport_updates_existing_order(self):
        # Cenário do dia a dia: a planilha é reenviada com informações novas.
        # Primeiro importamos o pedido ainda em trânsito...
        self.import_rows([make_row(NFE=1, **{'DT. COLETA': datetime(2026, 7, 2)})])
        self.assertEqual(Order.objects.get(nfe='1').status, 'TRANSITO')

        # ...e depois a mesma NFE já com data de entrega e o cliente com outro nome.
        result = self.import_rows([
            make_row(
                NFE=1,
                **{
                    'RAZAO SOCIAL': 'Cliente A Renomeado',
                    'DT. COLETA': datetime(2026, 7, 2),
                    'DT. ENTREGA': datetime(2026, 7, 5),
                },
            )
        ])

        # O pedido é atualizado, não duplicado, e nenhum pedido "novo" é contado.
        self.assertTrue(result['success'])
        self.assertEqual(result['orders_data']['orders_created'], 0)
        self.assertEqual(Order.objects.count(), 1)
        order = Order.objects.get(nfe='1')
        self.assertEqual(order.status, 'ENTREGUE')
        self.assertEqual(order.delivery_date, date(2026, 7, 5))
        self.assertEqual(order.customer.name, 'Cliente A Renomeado')

    def test_duplicate_nfe_flagged_as_invalid(self):
        # Duas linhas com a mesma NFE indicam erro de preenchimento.
        # As duas são apontadas, com o número da linha como aparece no Excel
        # (a linha 1 é o cabeçalho, então os dados começam na 2).
        result = self.import_rows([make_row(NFE=1), make_row(NFE=1)])

        self.assertEqual(result['rows_invalid'], 2)
        self.assertEqual([e['linha'] for e in result['validation_errors']], [2, 3])
        for error in result['validation_errors']:
            self.assertIn('NFE duplicada: 1', error['erros'])

    def test_invalid_cnpj_skips_customer_and_order(self):
        # Sem um CNPJ válido não dá para identificar o cliente. Então nem o
        # cliente nem o pedido são criados, e a linha entra na contagem de erros.
        result = self.import_rows([make_row(**{'CNPJ PARC.': 'ABC123'})])

        self.assertEqual(result['rows_invalid'], 1)
        self.assertEqual(result['orders_data'], {'orders_created': 0, 'orders_errors': 1})
        self.assertEqual(Customer.objects.count(), 0)
        self.assertEqual(Order.objects.count(), 0)

    def test_wrong_sheet_name(self):
        # Se a aba não se chamar 'FRETES CONSOLIDADA', o serviço não acha os
        # dados. Ele deve devolver falha, sem lançar exceção e sem gravar nada.
        result = self.import_rows([make_row()], sheet_name='Planilha1')

        self.assertFalse(result['success'])
        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(Customer.objects.count(), 0)
