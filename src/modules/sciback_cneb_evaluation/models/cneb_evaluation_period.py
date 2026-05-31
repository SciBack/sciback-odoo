# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class CnebEvaluationPeriod(models.Model):
    _name = 'cneb.evaluation.period'
    _description = 'Periodo de evaluación CNEB'
    _order = 'academic_year_id desc, sequence, date_start'

    name = fields.Char(string='Nombre', required=True)
    academic_year_id = fields.Many2one(
        'op.academic.year', string='Año académico', required=True,
    )
    academic_term_id = fields.Many2one(
        'op.academic.term', string='Periodo académico (OpenEduCat)',
        help='Vínculo opcional al término académico de OpenEduCat.',
    )
    sequence = fields.Integer(string='Secuencia', default=10)
    date_start = fields.Date(string='Fecha de inicio')
    date_end = fields.Date(string='Fecha de fin')
    type = fields.Selection(
        [('bimestre', 'Bimestre'), ('trimestre', 'Trimestre')],
        string='Tipo', default='bimestre', required=True,
    )
    state = fields.Selection(
        [('draft', 'Borrador'), ('open', 'Abierto'), ('closed', 'Cerrado')],
        string='Estado', default='draft', required=True,
    )

    @api.constrains('date_start', 'date_end')
    def _check_dates(self):
        for rec in self:
            if rec.date_start and rec.date_end and rec.date_end < rec.date_start:
                raise ValidationError(
                    'La fecha de fin no puede ser anterior a la fecha de inicio.'
                )

    def action_open(self):
        self.write({'state': 'open'})

    def action_close(self):
        self.write({'state': 'closed'})

    def action_draft(self):
        self.write({'state': 'draft'})
