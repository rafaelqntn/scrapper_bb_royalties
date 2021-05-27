import logging
from argparse import ArgumentParser, RawDescriptionHelpFormatter
from datetime import datetime as dt

import royalties_bb.scrapper as scrapper

filename_output = scrapper.filename_output_format.format(
    stmt="<RECEITA>", frm='<DATA_INICIAL>', to='<DATA_FINAL>', gen='<TIMESTAMP>')
parser = ArgumentParser(
    formatter_class=RawDescriptionHelpFormatter,
    description=f'''Programa para raspar dados dos "extratos bancários"
da url https://www42.bb.com.br/portalbb/daf/beneficiario.bbx.
O beneficiário fixo é o Rio de Janeiro.
O resultado da raspagem dos dados é gravado em um arquivo com o seguinte formato:
{filename_output}
'''
)


def arg_to_date(date: str) -> dt:
    return dt.strptime(date, '%Y-%m-%d')


parser.add_argument(
    '--receita',
    '-r',
    metavar=list(scrapper.statements_map.keys()),
    dest='statement',
    choices=scrapper.statements_map.keys(),
    help='O nome da receita que deseja obter do site.',
    required=True,
)

parser.add_argument(
    '--data_inicial',
    '-dti',
    metavar='YYYY-MM-DD',
    dest='date_start',
    type=arg_to_date,
    help='A data inicial no formato ISO YYYY-MM-DD.',
    required=True,
)

parser.add_argument(
    '--data_final',
    '-dtf',
    metavar='YYYY-MM-DD',
    dest='date_end',
    type=arg_to_date,
    help='A data final no formato ISO YYYY-MM-DD.',
    required=True,
)

parser.add_argument(
    '--log_level',
    '-l',
    metavar='LOG',
    dest='log_level',
    help='O nível de informação apresentada no log.',
    required=False,
)


class Args:
    """Custom 'namespace' class"""
    pass


args = Args()
parser.parse_args(namespace=args)
if args.log_level:
    logging.getLogger().setLevel(args.log_level)
scrapper.scrape(args.statement, args.date_start, args.date_end)
