import logging
import json
import requests
from datetime import datetime, timedelta
from requests.structures import CaseInsensitiveDict
from odoo import _, api, fields, models, tools
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

class ResCompanyBillerInherit(models.Model):
    _inherit = "res.company"

    ambiente_biller = fields.Selection([('test','Test'),('prod','Produccion')],'Ambiente Biller',default='test')
    token_biller = fields.Char('Token')

    def _get_header_api(self):

        #We verify token
        if not self.token_biller:
            raise ValidationError('Debe guardar el Token Biller de su compañia antes de utilizar alguna función')
        token = self.token_biller
        headers = CaseInsensitiveDict()
        headers["Accept"] = "application/json"
        headers["Authorization"] = "Bearer " + token

        return headers
    
    def _get_url(self):

        #We verigy url
        if self.ambiente_biller == 'test':
            url = "https://test.biller.uy/v2/"
        else:
            url = " https://biller.uy/v2/"

        return url

    def certificado_unico(self):

        headers = self._get_header_api()
        url = self._get_url() + 'dgi/empresas/certificado-unico?rut=' + self.partner_id.vat

        r = requests.get(url, headers=headers)
        response_json = json.loads(r.text)

        _logger.warning('***** Respuesta: {0}'.format(response_json))

        return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Certificado Unico',
                    'message': response_json,
                    'sticky': True,
                }}

    def datos_entidad(self):
        headers = self._get_header_api()
        url = self._get_url() + 'dgi/empresas/datos-entidad?rut=' + self.partner_id.vat

        r = requests.get(url, headers=headers)
        response_json = json.loads(r.text)

        _logger.warning('***** Respuesta: {0}'.format(response_json))

        return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Datos de entidad',
                    'message': response_json,
                    'sticky': True,
                }}
