import logging
import requests
import json
from odoo import _, api, fields, models, tools
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

class AccountMoveBillerInherit(models.Model):
    _inherit = "account.move"

    id_biller = fields.Char('Id Biller', copy=False)
    serie_biller = fields.Char('Serie Biller', copy=False)
    numero_biller = fields.Char('Numero Biller', copy=False)
    hash_biller = fields.Char('Hash Biller', copy=False)
    estado_dgi_biller = fields.Char('Estado DGI', copy=False)
    pdf_biller = fields.Binary('PDF Biller', copy=False)
    comprobante_biller = fields.Char('Comprobante Biller | DGI', compute="_compute_comprobante_biller")

    #Referencias para NC
    ref_reversed_serie = fields.Char('Serie de Referencia')
    ref_reversed_numero = fields.Char('Número de Referencia')
    ref_reversed_tipo = fields.Selection([('101','e-Ticket'),('111','e-Factura')], 'Tipo de Referencia')
    ref_reversed_fecha = fields.Date('Fecha de Referencia')

    @api.depends('serie_biller','numero_biller')
    def _compute_comprobante_biller(self):
        for rec in self:
            rec.comprobante_biller = ''
            if rec.serie_biller and rec.numero_biller:
                rec.comprobante_biller = rec.serie_biller + '-' + rec.numero_biller

    def get_pdf_biller(self):
        for rec in self:
            if rec.numero_biller:
                response_json = ''
                status_code = ''

                try:
                    headers = rec.company_id._get_header_api()
                    url = rec.company_id._get_url() + 'comprobantes/pdf?id=' + rec.id_biller
                    _logger.warning('***** url: {0}'.format(url))

                    try:
                        r = requests.get(url, headers=headers)
                    except:
                        raise ValidationError('No se obtuvo conexion con biller, intente mas tarde o escoja otro diario')

                    status_code = r.status_code

                    # Verificar la respuesta de la API
                    if status_code in [200,201]:
                        rec.pdf_biller = r.text
                        return rec
                    else:
                        raise ValidationError()
                except:
                    error = []
                    for rj in response_json:
                        error += rj['message']
                    _logger.warning('***** Respuesta: {0}'.format(response_json))
                    raise ValidationError('Hubo un error, la respuesta de Biller es: {0}'.format(error))
                


    def state_dgi(self):
        for rec in self:
            if rec.numero_biller:

                response_json = ''
                status_code = ''

                try:
                    headers = rec.company_id._get_header_api()
                    url = rec.company_id._get_url() + 'comprobantes/obtener?id=' + rec.id_biller

                    try:
                        r = requests.get(url, headers=headers)
                    except:
                        raise ValidationError('No se obtuvo conexion con biller, intente mas tarde o escoja otro diario')

                    response_json = json.loads(r.text)
                    status_code = r.status_code

                    # Verificar la respuesta de la API
                    if status_code in [200,201]:
                        _logger.warning(r.json())  # Si la respuesta es en formato JSON
                        rec.estado_dgi_biller = response_json[0]['estado']
                        return rec
                    else:
                        raise ValidationError()
                except:
                    error = []

                    if status_code == 422:
                        raise ValidationError('ERROR: {0}, La solicitud está correcta sintácticamente, pero contiene errores en los datos. Respuesta de Biller: {1}'.format(r.status_code, response_json))
                    elif status_code == 400:
                        raise ValidationError('ERROR: {0}, Bad Request - La solicitud contiene sintaxis errónea, no debería repetirse. Respuesta de Biller: {1}'.format(r.status_code, response_json))
                    for rj in response_json:
                        error += rj['message']
                    _logger.warning('***** Respuesta: {0}'.format(response_json))
                    raise ValidationError('Hubo un error, la respuesta de Biller es: {0}'.format(error))


    def action_post(self):
        for record in self:
            rec = super(AccountMoveBillerInherit, record).action_post()

            #Verificamos que el diario sea para Biller
            if not record.journal_id.is_biller:
                return rec

            response_json = ''
            status_code = ''

            #Completamos data
            if record.forma_pago == 'credito':
                forma_pago = 2
            else:
                forma_pago = 1

            indicador_facturacio = 0

            #Items
            items = []
            for line in record.invoice_line_ids:
                if len(line.tax_ids):
                    indicador_facturacio = line.tax_ids[0].tax_group_id.code_uy
                items.append({
                        "cantidad": line.quantity,
                        "concepto": line.name,
                        "precio": line.price_unit,
                        "indicador_facturacion": indicador_facturacio
                    })
                if line.discount != 0:
                    items[-1]['descuento_tipo'] = '%'
                    items[-1]['descuento_cantidad'] = line.discount
            _logger.warning('***** items: {0}'.format(items))

            data = {
                "tipo_comprobante": record.l10n_latam_document_type_id.code,
                "numero_interno": record.name,
                "forma_pago": forma_pago, 
                "sucursal": record.journal_id.id_suc_biller, 
                "moneda": record.currency_id.name,
                "montos_brutos": 0,
                "cliente": {
                    "tipo_documento": record.partner_id.l10n_latam_identification_type_id.l10n_uy_code, 
                    "documento": record.partner_id.vat,
                    "razon_social": record.partner_id.name,
                    "nombre_fantasia": record.partner_id.name_fantasy,
                    "sucursal": {
                        "direccion": record.partner_id.street,
                        "ciudad": record.partner_id.city,
                        "departamento": record.partner_id.state_id.name,
                        "pais": record.partner_id.country_id.code,
                        "emails": [record.partner_id.email],
                    }
                },
                "items": items
                }


            # Referencia necesaria para NC
            if record.move_type == "out_refund":
                if record.reversed_entry_id:
                    if record.reversed_entry_id.id_biller:
                        data['referencias'] = [record.reversed_entry_id.id_biller]
                if not record.reversed_entry_id or not record.reversed_entry_id.id_biller:
                    data['referencias'] = [{
                        "tipo": record.ref_reversed_tipo,
                        "serie": record.ref_reversed_serie,
                        "numero": record.ref_reversed_numero
                    }]
                    if record.ref_reversed_fecha:
                        data['referencias'][0]['fecha'] = record.ref_reversed_fecha.strftime("%Y-%m-%d")

            
            _logger.warning('***** data: {0}'.format(data))
            
            try:
                headers = record.company_id._get_header_api()
                url = record.company_id._get_url() + 'comprobantes/crear'

                r = requests.get(url, headers=headers, json=data)

                response_json = json.loads(r.text)
                status_code = r.status_code

                _logger.warning('***** Respuesta: {0}'.format(response_json))
                _logger.warning('***** status_code: {0}'.format(r.status_code))

                # Verificar la respuesta de la API
                if status_code in [200,201]:
                    _logger.warning(r.json())  # Si la respuesta es en formato JSON
                    record.id_biller = response_json['id']
                    record.serie_biller = response_json['serie']
                    record.numero_biller = response_json['numero']
                    record.hash_biller = response_json['hash']
                    _logger.warning('********* Solicitud exitosa.')
                    record.state_dgi()
                    record.get_pdf_biller()
                    return rec
                else:
                    raise ValidationError()
            except:
                error = []

                if status_code == 422:
                    raise ValidationError('ERROR: {0}, La solicitud está correcta sintácticamente, pero contiene errores en los datos. Respuesta de Biller: {1}'.format(r.status_code, response_json))
                elif status_code == 400:
                    raise ValidationError('ERROR: {0}, Bad Request - La solicitud contiene sintaxis errónea, no debería repetirse. Respuesta de Biller: {1}'.format(r.status_code, response_json))
                for rj in response_json:
                    error += rj['message']
                _logger.warning('***** Respuesta: {0}'.format(response_json))
                raise ValidationError('Hubo un error, la respuesta de Biller es: {0}'.format(error))


    def _get_formatted_sequence(self, number=0):
        return "%s %03d-%010d" % (self.l10n_latam_document_type_id.doc_code_prefix,
                                 self.journal_id.l10n_uy_cod_sucursal, number)

    def _get_starting_sequence(self):
        if self.journal_id.l10n_latam_use_documents and self.company_id.account_fiscal_country_id.code == "UY":
            if self.l10n_latam_document_type_id:
                return self._get_formatted_sequence()
        return super()._get_starting_sequence()

    def _get_last_sequence_domain(self, relaxed=False):
        where_string, param = super(AccountMoveBillerInherit, self)._get_last_sequence_domain(relaxed)
        if self.company_id.account_fiscal_country_id.code == "UY" and self.l10n_latam_use_documents:
            where_string += " AND l10n_latam_document_type_id = %(l10n_latam_document_type_id)s"
            param['l10n_latam_document_type_id'] = self.l10n_latam_document_type_id.id or 0
        return where_string, param