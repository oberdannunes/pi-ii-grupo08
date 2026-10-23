![FastLog](media/fastlog-logo.png)

# Sistema de consulta de entregas para os setores Comercial e Logístico da empresa Doce Festa

Este projeto consiste em o desenvolvimento inicial de um sistema web para consulta do status de entregas na empresa Doce Festa, que atua no ramo de produtos para festas. O principal objetivo do sistema é desenvolver um sistema web que centralize os dados de entrega, permitindo consultas rápidas e confiáveis.

A motivação por trás do desenvolvimento desta ferramenta é dificuldade de comunicação entre os setores Comercial e Logístico, devido ao uso de planilhas e contatos informais, o que gera atrasos, retrabalho e risco de informações desatualizadas.

## Tecnologias Utilizadas

O ecossistema do projeto foi construído utilizando tecnologias robustas e amplamente adotadas no mercado para garantir desempenho e escalabilidade.

- Python
- PostgreSQL
- Django
- Bootstrap
- Git e GitHub
- HTML5 e CSS3

A escolha da stack Python/Django/PostgreSQL baseia-se no equilíbrio entre velocidade de entrega e robustez técnica. O Python fornece uma base sólida e legível para o desenvolvimento; o Django acelera a construção da aplicação com segurança e padrões de projeto consolidados; e o PostgreSQL garante que os dados sejam armazenados em um ambiente performático e extensível.

## Como Funciona (Passo a Passo)

Este guia explica como preparar um computador (com Windows 10 ou 11) para rodar o FastLog, mostrando os programas necessários, o passo a passo da instalação e como o sistema lê planilhas do Excel automaticamente.

### Como o Sistema é Organizado por Dentro (Arquitetura)

O FastLog funciona em três camadas organizadas (chamadas de padrão MVT):

1. **O Banco de Dados (Model)**: Onde ficam guardadas as informações organizadas (País, Estado, Cidade, Transportadora, Cliente e Pedido).

2. **O Visual (Template)**: O que o usuário vê na tela (as páginas do site, os botões de busca).

3. **O Cérebro (View)**: O meio de campo. Quando você clica em um botão, o cérebro processa o pedido, busca a informação no Banco de Dados e mostra na tela do Usuário.

### Passo a Passo para Instalar no Computador

Para colocar o sistema para funcionar no seu computador local, siga as etapas abaixo:

#### Passo 1: Baixar o Código (Clonagem)

Você precisa ter o programa Git instalado. Abra o terminal (prompt de comando) do seu computador e digite:

```bash
git clone https://github.com/oberdannunes/pi-ii-grupo08.git

cd pi-grupo-05
```

Isso vai baixar uma pasta com todos os arquivos do projeto para o seu computador.

#### Passo 2: Criar uma "Caixa de Isolamento" (Ambiente Virtual)

Para que os programas do FastLog não entrem em conflito com outros programas que você já tem no computador, criamos um ambiente isolado. No terminal, digite:

```bash
python -m venv .venv

.venv\Scripts\activate
```

_(Nota: Se o Windows der um aviso de bloqueio, pode ser necessário autorizar a execução de scripts no seu PowerShell). Você saberá que deu certo quando aparecer um (.venv) no início da linha do comando._

#### Passo 3: Instalar os Pacotes Necessários

Com o ambiente isolado ativo, mude para a pasta do código e peça para o Python instalar todos os complementos de uma vez só:

```bash
cd src

pip install -r requirements.txt
```

#### Passo 4: Preparando o Banco de Dados e o Administrador

Agora precisamos criar a estrutura onde as informações serão salvas e a conta do "chefe" do sistema.

**Criar as tabelas:**

```bash
python manage.py migrate
```

**Criar o usuário administrador:**

```bash
python manage.py createsuperuser
```

O sistema vai pedir para você criar um nome de usuário, e-mail e uma senha (que deve ter pelo menos 8 caracteres e não pode ser apenas números).

Como Executar o Sistema

Para executar no seu computador, digite:

```bash
python manage.py runserver
```

Pronto! Agora abra o seu navegador de internet (Chrome, Edge, etc.) e digite o endereço:

http://localhost:8000

### Como Rodar os Testes Unitários

Os testes automatizados usam o **pytest** com o plugin **pytest-django**, que já são instalados no Passo 3 (estão no `requirements.txt`). As configurações ficam no arquivo `src/pytest.ini`, então não é preciso informar nada extra.

Com o ambiente virtual ativo, entre na pasta `src` e rode:

```bash
cd src

pytest
```

O pytest encontra sozinho todos os arquivos de teste (`test_*.py` e `tests.py`) e mostra o resultado de cada um. Ao final, aparece um resumo com quantos testes passaram e quantos falharam.

Também é possível rodar só uma parte dos testes:

```bash
# Apenas um arquivo
pytest tracking/tests/test_api_orders.py

# Apenas os testes cujo nome contém uma palavra
pytest -k cnpj
```

_Nota: os testes criam um banco de dados temporário só para eles, que é apagado ao final. Seus dados não são alterados._

## Como Funciona (Passo a Passo para o usuário comum/cliente)

A jornada de utilização do sistema foi desenhada para ser simples e direta, exigindo poucos comandos por parte do usuário final.

O fluxo se inicia na página inicial da aplicação (http://localhost:8000), onde o usuário visualiza uma interface limpa com um campo centralizado de busca. Para realizar a consulta, o operador ou cliente deve digitar o número de CNPJ da empresa de interesse e o número de controle da nota fiscal (NFE).

Após preencher o campo e acionar o botão de busca, o sistema processa a requisição realizando uma varredura interna no banco de dados. Em poucos segundos, a tela exibe o resultado "Entregue" ou "Entrega em andamento".

Para uma nova consulta, há o botão "Voltar" do navegador aparece na exibição do status

Preenchendo somente CNPJ ou NFE têm a mensagem "Por favor, preencha ambos os campos: CNPJ e NFE.

## Como Funciona (Passo a Passo para o administrador)

Se você for o administrador e quiser gerenciar o sistema, o endereço é http://localhost:8000/admin (onde usará a senha criada no passo “Criar o usuário administrador”).

O administrador visualiza uma interface limpa com um campo centralizado de login e senha. Acessa o sistema, na sessão de pedidos e clica em Visualização. Irá parecer a lista dos pedidos já importados. Há duas possibilidade: cadastrar entrega por entrega ou cadastrar em lote. Por meio do botão "Upload Planilha de Carga", escolhe o arquivo e clica em processar. A validação e verificação de erros será realizada e dará retorno do que foi feito, finalizando o processo e podendo sair.

E se for o caso, apontará linhas inválidas.

### Regras para a Planilha Funcionar:

O arquivo do Excel precisa ter uma aba com o nome exato de "**FRETES CONSOLIDADA**" e deve conter as seguintes colunas obrigatórias:

- **TRANSPORTADORA** (Nome de quem vai levar)
- **DT. PEDIDO** (Data em que a compra foi feita)
- **NFE** (Número da Nota Fiscal)
- **RAZAO SOCIAL** (Nome da empresa do cliente)
- **CIDADE** (Cidade de entrega)
- **UF** (Estado, ex: SP)
- **PAÍS** (Geralmente BRASIL)

_Nota: Outras colunas como valor do frete ou data de entrega são opcionais._

### Como o sistema processa a planilha:

O FastLog lê a planilha linha por linha. Para garantir que nada dê errado, ele usa um sistema de segurança: **se uma linha tiver erro, ela é pulada e registrada em uma lista de erros, mas o restante da planilha continua sendo importado normalmente**.

Ao final, o sistema mostra um relatório: "X linhas foram importadas com sucesso e as linhas Y e Z deram erro". Isso evita que o banco de dados fique bagunçado ou com informações duplicadas. Essa função fica disponível apenas para o administrador dentro do painel de controle.

## Evolução da Ferramenta

Para o projeto Projeto Integrador em Computação II - DRP11 - Turma 001, o FastLog recebeu as seguintes melhorias:

- **API de consulta de pedidos**: api criada na rota `/api/tracking/orders/`, que devolve a lista de pedidos em formato JSON. A API exige autenticação com API Key, o resultado é paginado, e permite ainda o filtro por status, NFe, CNPJ e período.
- **Dashboard**: painel em `/dashboard/` com indicadores das entregas e filtros por período, estado (UF), transportadora e status. Quando ainda não há pedidos cadastrados, aparece uma mensagem avisando.
- **Testes unitários com pytest**: testes automatizados para o dashboard, API, consultas e importação da planilha.
- **Máscara de CNPJ com JavaScript**: na tela de consulta, o campo de CNPJ é formatado sozinho enquanto o usuário digita (`00.000.000/0000-00`). Ele aceita só números e no máximo 14 dígitos.
- **Acessibilidade**: a tela inicial e as telas de status do pedido ("Entregue" e "Entrega em andamento") ficaram mais fáceis de usar para todas as pessoas. Os campos agora têm rótulos e descrições lidos por leitores de tela, e as mensagens de erro são anunciadas automaticamente. Quem navega pelo teclado vê com clareza onde está o foco, e as animações ficam mais leves para quem configurou o sistema para reduzir movimento.

## Como Gerar a API Key

Para usar a API de consulta de pedidos, quem vai consultar precisa de uma chave de acesso (API Key). Só o administrador pode criar essa chave, pelo painel de administração:

1. Acesse http://localhost:8000/admin e entre com o usuário administrador.
2. Na seção **API Key Permissions**, clique em **API keys** e depois em **Adicionar** (ou **Add**).
3. No campo **Name**, informe um nome que identifique quem vai usar a chave (por exemplo, `Sistema Comercial`).
4. Se quiser que a chave pare de valer em uma data específica, preencha **Expires**. Deixe em branco para a chave não expirar.
5. Clique em **Salvar**.

Depois de salvar, aparece uma mensagem no topo da tela com a chave completa:

```
The API key for Sistema Comercial is: AbCdEf12.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx. Please store it somewhere safe: you will not be able to see it again.
```

**Copie e guarde a chave nesse momento.** Por segurança, ela não fica salva no sistema e não pode ser exibida de novo. Se perder a chave, crie uma nova.

Para cancelar uma chave, abra-a na lista de **API keys**, marque **Revoked** e salve. A partir daí, ela deixa de funcionar.

### Como usar a API Key

A chave deve ser enviada no cabeçalho `Authorization` de cada requisição, com o prefixo `Api-Key`:

```bash
curl -H "Authorization: Api-Key SUA_CHAVE_AQUI" http://localhost:8000/api/tracking/orders/
```

Os filtros são passados na própria URL, por exemplo:

```bash
curl -H "Authorization: Api-Key SUA_CHAVE_AQUI" "http://localhost:8000/api/tracking/orders/?status=ENTREGUE&order_date_after=2026-01-01"
```

Filtros disponíveis: `status` (`PENDENTE`, `TRANSITO` ou `ENTREGUE`), `nfe`, `cnpj`, `data_pedido_inicio` e `data_pedido_fim` (datas no formato `AAAA-MM-DD`). Sem a chave, ou com uma chave inválida, a API não devolve os dados.

## Equipe de Desenvolvimento

- Aline Jady Cordeiro
- Bruno Henrique Cavasana
- Helton Cleiton de Souza
- Josse Givan Bombardi Ferreira
- Leandro Agiani Silva
- Mey Fan Porfírio Wai
- Oberdan Borges Nunes
- Wilker David Tosta Pinto