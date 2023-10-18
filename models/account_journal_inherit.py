from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, RedirectWarning


class AccountJournalInherit(models.Model):
    _inherit = "account.journal"

    is_biller = fields.Boolean("Diario Biller", helper="Si se marca como verdadero, al validarse un documento con este diario se enviaran los datos a Biller")
    id_suc_biller = fields.Integer("Id Biller", helper="Id de sucursal en Biller")