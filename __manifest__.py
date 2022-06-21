# -*- coding: utf-8 -*-
{
    'name': "Financial Report Branch Wise",
    'author':
        'Enzapps',
    'summary': """
This module will help to Get Report Financial Branch Wise Report.
""",

    'description': """
        This module will help to Get Report Financial Branch Wise Report.
    """,
    'website': "",
    'category': 'base',
    'version': '14.0',
    'depends': ['base','hr','account','ohrms_loan','accounts_bankfee_statements','boraq_company_branches'],
    "images": ['static/description/icon.png'],
    'data': [
       'security/ir.model.access.csv',
       'views/financial.xml',
       'report/collection.xml',
       'report/ledger.xml'
    ],
    'demo': [
    ],
    'installable': True,
    'application': True,
}
