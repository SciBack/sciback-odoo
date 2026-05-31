# -*- coding: utf-8 -*-
from odoo import models, fields


class CnebCompetency(models.Model):
    _name = 'cneb.competency'
    _description = 'Competencia CNEB'
    _order = 'area_id, sequence, id'

    name = fields.Char(string='Competencia', required=True)
    code = fields.Char(string='Código')
    area_id = fields.Many2one(
        'cneb.area', string='Área curricular',
        required=True, ondelete='cascade',
    )
    level = fields.Selection(
        related='area_id.level', string='Nivel', store=True, readonly=True,
    )
    sequence = fields.Integer(string='Secuencia', default=10)
    active = fields.Boolean(string='Activo', default=True)
