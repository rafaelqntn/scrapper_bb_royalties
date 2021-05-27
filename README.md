# Raspador de dados contábeis de royalties (Banco do Brasil)

Python script para raspagem de dados contábeis de royalties fornecidos pelo **Banco do Brasil**.

O ponto de entrada da raspagem é a página [https://www42.bb.com.br/portalbb/daf/beneficiario.bbx](https://www42.bb.com.br/portalbb/daf/beneficiario.bbx).

## Funcionamento

A raspagem segue os seguintes passos:

1. envia uma requisição GET para a página inicial, onde o servidor cria sessão, que é mantida via cookies.
1. da página inicial são obtidos os parâmetros para enviar uma requisição POST (o nome do beneficiário é fixo "Rio de Janeiro").
1. a requisição POST inicialmente responde com o código de redirecionamento e URL para o cliente obter a próxima página (header `Location`).
1. a próxima página contém o formulário que define o beneficiário, as datas inicial e final e a receita.
   - A diferença máxima entre as datas é de 60 dias.
1. os parâmetros do formulário são utilizados para fazer novas requisições POST (variando as datas iniciais e finais) e GET em um loop para obter o extrato em si.
1. Os dados de cada página de extrato são transformados/limpos para facilitar os trabalhos das ferramentas _downstream_ (ETL).
1. O resultado é gravado em um arquivo em que a última parte do nome é o _timestamp_ da criação.

## Ambiente

- Python 3.9.2
- As demais dependencias estão listadas no arquivo [requirements.txt](./requirements.txt)

### Sugestão de setup

1. instalar um interpretador python na versão indicada.
1. instalar pip
1. instalar virtualenv
1. fazer o checkout desse repositório
1. na raíz do repositório:
   1. crie o ambiente virtual: `virtualenv venv` (isso vai criar uma pasta chamada `venv` contendo um novo interpretador)
   1. ative o ambiente virtual: `source ./venv/bin/activate` (comando válido para linux)
   1. instale as dependencias: `pip install -r requirements.txt`

## Como utilizar

O programa é um módulo python (com `__main__.py`) que recebe parâmetros da linha de comando.

Para exibir a mensagem de ajuda (que apresenta os parâmetros) execute:

`python -m royalties_bb -h`

### Exemplos

**Atenção:**

- ao formato das datas
- caso esteja usando `virtualenv` (conforme sugerido), passar o caminho completo para o interpretador python criado na pasta `venv`.

A seguinte linha de comando raspa os dados da receita ANP entre janeiro de 2011 e agosto de 2011:

`python -m royalties_bb --receita ANP --data_inicial 2011-01-01 --data_final 2012-08-31`

O parâmetro `--log_level` é opcional (default `INFO`). Pode ser definido como `DEBUG` para obter mais detalhes sobre a execução do programa.

Exemplo:

`python -m royalties_bb --receita ANP --data_inicial 2011-01-01 --data_final 2012-08-31 --log_level DEBUG`

A opção com `DEBUG` em conjunto com a função `write_page` (comentada em pontos específicos do código) é interessante para investigar falhas na execução devido a mudaças na estrutura da página ou no formato dos dados.

As páginas originais utilizadas no desenvolvimento da primeira versão podem ser encontradas na pasta [original_samples](./original_samples) e devem ser utilizadas para comparação com páginas mais recentes que causarem falhas.
