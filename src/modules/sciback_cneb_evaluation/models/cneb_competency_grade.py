# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


# Escala literal CNEB. NO incluir opción vacía artificial: el "sin evaluar"
# se representa con el campo grade vacío (False), que NO equivale a C.
CNEB_LITERAL_SELECTION = [
    ('AD', 'AD - Logro destacado'),
    ('A', 'A - Logro esperado'),
    ('B', 'B - En proceso'),
    ('C', 'C - En inicio'),
]

# Peso pedagógico de cada literal (referencia CNEB). Útil para sugerencias.
CNEB_LITERAL_WEIGHT = {'AD': 4, 'A': 3, 'B': 2, 'C': 1}


class CnebCompetencyGrade(models.Model):
    _name = 'cneb.competency.grade'
    _description = 'Calificación por competencia (CNEB)'
    _order = 'period_id, area_id, student_id'

    student_id = fields.Many2one(
        'op.student', string='Estudiante', required=True, ondelete='cascade',
    )
    competency_id = fields.Many2one(
        'cneb.competency', string='Competencia', required=True,
        ondelete='cascade',
    )
    area_id = fields.Many2one(
        'cneb.area', related='competency_id.area_id', string='Área curricular',
        store=True, readonly=True,
    )
    level = fields.Selection(
        related='area_id.level', string='Nivel', store=True, readonly=True,
    )
    period_id = fields.Many2one(
        'cneb.evaluation.period', string='Periodo', required=True,
        ondelete='restrict',
    )
    grade = fields.Selection(
        CNEB_LITERAL_SELECTION, string='Logro (literal)',
        help='Vacío = sin evaluar (NO equivale a C).',
    )
    descriptive_conclusion = fields.Text(
        string='Conclusión descriptiva',
        help='Obligatoria en Inicial siempre, y en Primaria/Secundaria cuando '
             'el logro es C o AD.',
    )

    _sql_constraints = [
        ('student_competency_period_uniq',
         'unique(student_id, competency_id, period_id)',
         'Ya existe una calificación de esta competencia para el estudiante en '
         'este periodo.'),
    ]

    @api.constrains('grade', 'descriptive_conclusion', 'level')
    def _check_descriptive_conclusion(self):
        for rec in self:
            needs = False
            if rec.level == 'inicial':
                needs = True
            elif rec.grade in ('C', 'AD'):
                needs = True
            if needs and not (rec.descriptive_conclusion or '').strip():
                raise ValidationError(
                    'La conclusión descriptiva es obligatoria '
                    '(Inicial siempre; Primaria/Secundaria cuando el logro es '
                    'C o AD). Estudiante: %s, competencia: %s.' % (
                        rec.student_id.display_name or '',
                        rec.competency_id.display_name or '',
                    )
                )
