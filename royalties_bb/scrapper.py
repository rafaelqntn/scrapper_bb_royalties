import csv
import logging
from datetime import datetime, timedelta
from os import path
from typing import List

from bs4 import BeautifulSoup
from requests import Request, Response, Session

# for debug/development
# s = BeautifulSoup(open('./original_samples/01_view_benef_search.html', 'r').read(), 'html.parser')
# s = BeautifulSoup(open('./original_samples/02_view_statement_form.html', 'r').read(), 'html.parser')
# s = BeautifulSoup(open('./original_samples/03_statement.html', 'r').read(), 'html.parser')

logger = logging.getLogger(__name__)

url_base = 'https://www42.bb.com.br'

url_view_benef_search = f'{url_base}/portalbb/daf/beneficiario.bbx'

csv_header = ['DATA', 'PARCELA', 'VALOR', 'MOVIMENTO']

statements_map = {
    'ANP': '28',
    'PEA': '29',
}

max_days_request = 60

filename_output_format = '{stmt}_{frm}_{to}_{gen}.tsv'


def write_page(dest_path: str, content: str):
    with open(dest_path, 'w') as f:
        f.write(content)


def write_csv(statement: str, data: List, date_start: datetime, date_end: datetime):
    frm = date_start.strftime("%Y%m%d")
    to = date_end.strftime("%Y%m%d")
    gen = datetime.now().timestamp()
    fileName = filename_output_format.format(stmt=statement, frm=frm, to=to, gen=gen)
    logger.info(f'Escrevendo o resultado para {path.realpath(fileName)}')
    with open(fileName, 'w', encoding='utf-8', newline='') as outf:
        writer = csv.writer(outf, delimiter='\t')
        writer.writerow(csv_header)
        writer.writerows(data)


def scrape(statement: str, date_start: datetime, date_end: datetime):
    statement_value = statements_map[statement]
    logger.info('Iniciando a raspagem dos dados.')

    with Session() as session:

        res_view_benef_search = get_view_benef_search(session)
        soup_view_benef_search = BeautifulSoup(res_view_benef_search.text, "html.parser")
        view_state = soup_view_benef_search.find('input', attrs={'id': 'javax.faces.ViewState'})['value']

        res_post_benef_search = post_benef_search(session, view_state)
        redirect_location = res_post_benef_search.history[0].headers.get('Location')

        data = []
        param_date_start = date_start
        param_date_end = date_start + timedelta(days=max_days_request)
        statement_location = None

        while param_date_start < date_end:
            res_view_statement_form = get_view_statement_form(session, redirect_location)
            soup_view_statement_form = BeautifulSoup(res_view_statement_form.text, "html.parser")
            view_state = soup_view_statement_form.find('input', attrs={'id': 'javax.faces.ViewState'})['value']
            url_form_action = f'{url_base}{soup_view_statement_form.select_one("#formulario")["action"]}'

            start = param_date_start.strftime('%d/%m/%Y')
            end = param_date_end.strftime('%d/%m/%Y')
            logger.info(f'Requesting dados de {start} a {end}')
            res_post_statement_params = post_statement_params(
                session,
                view_state,
                url_form_action,
                param_date_start,
                param_date_end,
                statement_value
            )
            # it only redirects when there is no cid (first request).
            if res_post_statement_params.history:
                statement_location = res_post_statement_params.history[0].headers.get('Location')

            res_view_statement = get_statement(session, statement_location)
            soap_view_statement = BeautifulSoup(res_view_statement.text, "html.parser")
            normalized = process_statement(soap_view_statement)
            data.extend(normalized)

            param_date_start = param_date_end + timedelta(days=1)
            param_date_end = param_date_start + timedelta(days=max_days_request)

    write_csv(statement, data, date_start, date_end)
    logger.info('Pronto.')


def get_view_benef_search(session: Session) -> Response:
    logger.info('Enviando request para obtenção dos cookies (session id).')
    request = Request(
        method='GET',
        url=url_view_benef_search
    ).prepare()
    response = session.send(request)
    # write_page('01_view_benef_search.html', response.text)
    return response


def get_view_statement_form(session: Session, url_redirect: str) -> Response:
    request = Request(
        method='GET',
        url=url_redirect,
        cookies={
            'JSESSIONID': session.cookies.get("JSESSIONID")
        }
    ).prepare()
    response = session.send(request)
    # write_page('02_view_statement_form.html', response.text)
    return response


def post_benef_search(session: Session, view_state: str) -> Response:
    url = f'{url_view_benef_search};jsessionid={session.cookies.get("JSESSIONID")}'
    request = Request(
        method='POST',
        url=url,
        data={
            'publicadorformvalue': ',802,0,0,2,0,1',
            'formulario:txtBenef': 'Rio de Janeiro',
            'formulario:j_id16': 'Continuar',
            'formulario': 'formulario',
            'autoScroll': '',
            'javax.faces.ViewState': view_state,
        },
        cookies={
            'JSESSIONID': session.cookies.get("JSESSIONID")
        }
    ).prepare()
    response = session.send(request)
    return response


def post_statement_params(
        session: Session,
        view_state: str,
        url_form_action: str,
        param_date_start: datetime,
        param_date_end: datetime,
        statement_value: str) -> Response:
    request = Request(
        method='POST',
        url=url_form_action,
        data={
            'publicadorformvalue': ',802,0,0,2,0,1',
            'formulario:comboBeneficiario': '36',  # Rio de Janeiro - RJ
            'formulario:dataInicial': param_date_start.strftime('%d/%m/%Y'),  # Data
            'formulario:dataFinal': param_date_end.strftime('%d/%m/%Y'),  # Data
            'formulario:comboFundo': statement_value,  # 29 = PEA - PARTICIPACAO ESPECIAL ANP, 28 = ANP - ROYALTIES DA ANP
            'formulario:j_id20': 'Continuar',
            'formulario': 'formulario',
            'autoScroll': '',
            'javax.faces.ViewState': view_state,
        },
        cookies={
            'JSESSIONID': session.cookies.get("JSESSIONID")
        }
    ).prepare()
    response = session.send(request)
    return response


def get_statement(session: Session, redirect_location: str) -> Response:
    request = Request(
        method='GET',
        url=redirect_location,
        cookies={
            'JSESSIONID': session.cookies.get("JSESSIONID")
        }
    ).prepare()
    response = session.send(request)
    # write_page('03_statement.html', response.text)
    return response


def process_statement(soap_view_statement: BeautifulSoup) -> list:
    data = []
    table = soap_view_statement.find('table', attrs={'id': 'formulario:demonstrativoList'})
    table_body = table.find('tbody')
    rows = table_body.find_all('tr')
    for row in rows:
        tds = row.find_all('td')
        #  Gathering values only from the rows with 3 columns.
        values = [td.text.strip() for td in tds if len(tds) == 3]

        # This indicates the end of the statement.
        if values and 'TOTA' in values[0]:
            break

        #  Remove header, totals and empty rows
        if values and ('DATA' in values[0]
                       or 'TOTA' in values[1]
                       or 'FUNDO' in values[1]
                       or 'BENEF' in values[1]
                       or not any([v for v in values if v])
                       ):
            continue

        if values:
            # The normalization could be done here, but the code would be more confusing.
            # Generate and keep the 'last_date' here and pass as a parameter.
            data.append(values)

    normalized = normalize_data(data)
    return normalized


def normalize_data(values: List) -> List:
    last_date = None
    for i, v in enumerate(values):
        row = values[i]
        # fixing the date
        if row[0]:
            last_date = datetime.strptime(row[0], '%d.%m.%Y').strftime('%Y-%m-%d')
        row[0] = last_date

        # creating the D/C column
        row.append(row[2][-1])

        # fixing the value to make it easier to load into a database table.
        row[2] = row[2][2:-1].strip().replace('.', '').replace(',', '.')

    return values
