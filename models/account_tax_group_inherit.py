# -*- encoding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, RedirectWarning


class AccountTaxGroupInherit(models.Model):
    _inherit = "account.tax.group"

    code_uy = fields.Integer('Codigo Impuesto')

    @api.model
    def _update_code_core_uy(self):
        tasa_minima = self.env['account.tax.group'].search([('name','=','IVA 10%')])
        tasa_minima.write({
            'code_uy' : 2
        })
        tasa_basica = self.env['account.tax.group'].search([('name','=','IVA 22%')])
        tasa_basica.write({
            'code_uy' : 3
        })
        exento = self.env['account.tax.group'].search([('name','=','EXENTOS')])
        exento.write({
            'code_uy' : 1
        })