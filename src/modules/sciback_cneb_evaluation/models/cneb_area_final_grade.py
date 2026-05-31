# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError

from .cneb_competency_grade import CNEB_LITERAL_SELECTION
from .cneb_area_grade import EXPORT_STATE_SELECTION


class CnebAreaFinalGrade(models.Model):
    _name = 'cneb.area.final.grade'
    _description = 'Nota final por área (hoja NF - CNEB / SIAGIE)'
    _order = 'academic_year_id, batch_id, area_id, student_id'

    student_id = fields.Many2one(
        'op.student', string='Estudiante', required=True, ondelete='cascade',
    )
    area_id = fields.Many2one(
        'cneb.area', string='Área curricular', required=True,
        ondelete='restrict',
    )
    batch_id = fields.Many2one(
        'op.batch', string='Grado / Sección', ondelete='restrict',
    )
    academic_year_id = fields.Many2one(
        'op.academic.year', string='Año académico', required=True,
    )
    level = fields.Selection(
        related='area_id.level', string='Nivel', store=True, readonly=True,
    )
    grading_type = fields.Selection(
        related='area_id.grading_type', string='Tipo de calificación',
        store=True, readonly=True,
    )

    final_grade = fields.Selection(
        CNEB_LITERAL_SELECTION, string='Nota final (literal)',
        help='Calificativo final del área en el año. Decisión del docente.',
    )
    final_grade_numeric = fields.Integer(
        string='Nota final (0-20)',
        help='Usar solo cuando el área tiene escala vigesimal.',
    )
    final_descriptive_conclusion = fields.Text(
        string='Conclusión descriptiva final',
    )

    export_state = fields.Selection(
        EXPORT_STATE_SELECTION, string='Estado de exportación',
        default='draft', required=True,
    )
    siagie_observation = fields.Text(string='Observación SIAGIE')

    # La situación final (PROMOVIDO/REQUIERE RECUPERACIÓN/etc.) la calcula SIAGIE.
    # Aquí es SOLO informativa y de solo lectura.
    siagie_situation = fields.Char(
        string='Situación final (SIAGIE)', readonly=True,
        help='Informativo. La situación final la determina SIAGIE; este campo '
             'solo refleja lo devuelto/registrado manualmente para referencia.',
    )

    _sql_constraints = [
        ('student_area_year_uniq',
         'unique(student_id, area_id, academic_year_id)',
         'Ya existe una nota final de esta área para el estudiante en este año.'),
    ]

    @api.constrains('final_grade', 'final_descriptive_conclusion', 'level',
                    'grading_type')
    def _check_descriptive_conclusion(self):
        for rec in self:
            if rec.grading_type == 'vigesimal':
                continue
            needs = False
            if rec.level == 'inicial':
                needs = True
            elif rec.final_grade in ('C', 'AD'):
                needs = True
            if needs and not (rec.final_descriptive_conclusion or '').strip():
                raise ValidationError(
                    'La conclusión descriptiva final es obligatoria '
                    '(Inicial siempre; Primaria/Secundaria cuando la nota final '
                    'es C o AD). Estudiante: %s, área: %s.' % (
                        rec.student_id.display_name or '',
                        rec.area_id.display_name or '',
                    )
                )

    @api.constrains('final_grade', 'final_grade_numeric', 'grading_type')
    def _check_grading_type_coherence(self):
        for rec in self:
            if rec.grading_type == 'literal' and rec.final_grade_numeric:
                raise ValidationError(
                    'El área "%s" usa escala LITERAL: no debe tener nota final '
                    'vigesimal.' % (rec.area_id.display_name,)
                )
            if rec.grading_type == 'vigesimal' and rec.final_grade:
                raise ValidationError(
                    'El área "%s" usa escala VIGESIMAL: no debe tener nota final '
                    'literal.' % (rec.area_id.display_name,)
                )

    @api.constrains('final_grade_numeric', 'grading_type')
    def _check_numeric_range(self):
        for rec in self:
            if rec.grading_type == 'vigesimal' and rec.final_grade_numeric:
                if not (0 <= rec.final_grade_numeric <= 20):
                    raise ValidationError(
                        'La nota final vigesimal debe ser un entero entre 0 y 20.'
                    )

    def action_mark_generated(self):
        self.write({'export_state': 'generated'})

    def action_mark_uploaded(self):
        self.write({'export_state': 'uploaded'})

    def action_mark_confirmed(self):
        self.write({'export_state': 'confirmed'})

    def action_reset_draft(self):
        self.write({'export_state': 'draft'})
