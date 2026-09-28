"""
Testes da API de listagem de pedidos (GET /api/tracking/orders/).

Esta é a API que sistemas externos usam para consultar os pedidos.
Por isso vale conferir com cuidado três coisas: quem pode acessar
(chave de API), o que é devolvido (campos e ordem) e como a consulta
pode ser refinada (filtros e paginação).
"""
from datetime import date

from django.test import TestCase
from django.urls import reverse
from rest_framework_api_key.models import APIKey

from tracking.models import Country, State, City, Customer, Carrier, Order
from tracking.serializers import OrderSerializer


class OrderListAPITests(TestCase):
    def setUp(self):
        # Um cenário pequeno, mas suficiente para exercitar os filtros:
        # dois clientes, uma transportadora e três pedidos em datas e
        # status diferentes.
        country = Country.objects.create(name="BRASIL")
        state = State.objects.create(id="SP", name="SÃO PAULO", country=country)
        city = City.objects.create(name="SÃO PAULO", state=state)

        self.customer_a = Customer.objects.create(name="Cliente A", cnpj="12345678901234", city=city)
        self.customer_b = Customer.objects.create(name="Cliente B", cnpj="98765432109876", city=city)
        self.carrier = Carrier.objects.create(name="TransX", cnpj="11111111111111", city=city)

        self.create_order("001", date(2026, 7, 1), "ENTREGUE", self.customer_a)
        self.create_order("002", date(2026, 7, 5), "TRANSITO", self.customer_b)
        self.create_order("003", date(2026, 7, 10), "PENDENTE", self.customer_a)

        # Gera uma chave de API de verdade. O create_key devolve o registro
        # e a chave em texto puro, que é o que o cliente envia no cabeçalho.
        _, key = APIKey.objects.create_key(name="test")
        self.auth = {"HTTP_AUTHORIZATION": f"Api-Key {key}"}
        self.url = reverse("core:api_order_list")

    def create_order(self, nfe, order_date, status, customer):
        """Cria um pedido com a transportadora padrão, para não repetir código."""
        return Order.objects.create(
            nfe=nfe,
            order_date=order_date,
            status=status,
            customer=customer,
            carrier=self.carrier,
        )

    def get(self, params=None):
        """Faz a requisição já autenticada, como um cliente legítimo faria."""
        return self.client.get(self.url, params or {}, **self.auth)

    def nfes(self, response):
        """Extrai só os números das NFEs, o que deixa as comparações mais fáceis de ler."""
        return [item["nfe"] for item in response.json()["results"]]

    def test_requires_api_key(self):
        # Sem chave nenhuma, a porta fica fechada.
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_rejects_invalid_api_key(self):
        # Uma chave inventada também não pode passar.
        response = self.client.get(self.url, HTTP_AUTHORIZATION="Api-Key invalida")
        self.assertEqual(response.status_code, 403)

    def test_lists_orders_newest_first(self):
        # Com a chave certa, vêm todos os pedidos, do mais recente para o mais antigo.
        response = self.get()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["count"], 3)
        self.assertEqual(self.nfes(response), ["003", "002", "001"])

    def test_serialized_fields(self):
        # Conferimos o "contrato" da API: exatamente os campos do serializer,
        # sem nada a mais nem a menos, e com os dados de cliente e
        # transportadora já resolvidos (nome e CNPJ, em vez de IDs).
        item = self.get({"nfe": "002"}).json()["results"][0]

        self.assertEqual(set(item), set(OrderSerializer.Meta.fields))
        self.assertEqual(item["status"], "TRANSITO")
        self.assertEqual(item["status_display"], "Em Trânsito")
        self.assertEqual(item["order_date"], "2026-07-05")
        self.assertIsNone(item["delivery_date"])
        self.assertEqual(item["customer_name"], "Cliente B")
        self.assertEqual(item["customer_cnpj"], "98765432109876")
        self.assertEqual(item["carrier_name"], "TransX")

    def test_filters(self):
        # Cada caso mostra um filtro e as NFEs que devem sobrar, já na ordem
        # da API. Os filtros de data incluem o próprio dia informado.
        cases = [
            ({"status": "PENDENTE"}, ["003"]),
            ({"nfe": "001"}, ["001"]),
            ({"customer_cnpj": "12345678901234"}, ["003", "001"]),
            ({"order_date_after": "2026-07-05"}, ["003", "002"]),
            ({"order_date_before": "2026-07-05"}, ["002", "001"]),
            ({"order_date_after": "2026-07-02", "order_date_before": "2026-07-09"}, ["002"]),
        ]
        for params, expected in cases:
            with self.subTest(params=params):
                response = self.get(params)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(self.nfes(response), expected)

    def test_invalid_status_filter(self):
        # Um status que não existe não pode devolver uma lista vazia em
        # silêncio. A API responde 400, para o cliente perceber o erro.
        self.assertEqual(self.get({"status": "CANCELADO"}).status_code, 400)

    def test_pagination(self):
        # A API devolve 20 pedidos por página (PAGE_SIZE nas settings).
        # Somando mais 18 aos 3 do setUp, chegamos a 21: uma página cheia
        # e uma segunda com um único pedido.
        for i in range(4, 22):
            self.create_order(f"{i:03d}", date(2026, 8, i), "PENDENTE", self.customer_a)

        data = self.get().json()

        self.assertEqual(data["count"], 21)
        self.assertEqual(len(data["results"]), 20)
        self.assertIsNotNone(data["next"])

        # Na última página não há próxima.
        last_page = self.get({"page": 2}).json()
        self.assertEqual(len(last_page["results"]), 1)
        self.assertIsNone(last_page["next"])
