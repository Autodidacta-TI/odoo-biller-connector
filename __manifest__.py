{
    "name": "Biller Connector",
    "summary": """
        Conector de Biller con Odoo para Facturacion Electronica""",
    "category": "Administration",
    "version": "16.0.0.0.1",
    "author": "Autodidacta TI",
    "license": "LGPL-3",
    "depends": [
        "account",
        "base",
        "contacts",
        "l10n_latam_invoice_document",
        "l10n_latam_base",
    ],
    "data": [
        'data/account_tax_group_data.xml',
        'views/res_company_view_inherit.xml',
        'views/account_journal_view_inherit.xml',
        'views/account_move_view_inherit.xml'
    ],
    "installable": True,
    "application": True,
    "auto_install": False,
}
