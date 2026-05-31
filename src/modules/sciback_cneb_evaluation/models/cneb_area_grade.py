# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError

from .cneb_competency_grade import (
    CNEB_LITERAL_SELECTION,
    CNEB_LITERAL_WEIGHT,
)

EXPORT_STATE_SELECTION = [
    ('draft', 'Borrador'),
    ('generated', 'Generado'),
    ('uploaded', 'Cargado'),
    ('confirmed', 'Confirmado'),
]

# Estrategia de sugerencia del calificativo de área. Configurable por sistema
# (ir.config_parameter 'sciback_cneb.suggestion_strategy').
# - 'last_period': promedio de pesos de las competencias del periodo, mapeado
#   al literal CNEB más cercano (comportamiento por defecto).
# - 'mode': moda (literal más frecuente) de las competencias del periodo.
SUGGESTION_STRATEGY_DEFAULT = 'last_period'


def _literal_from_weight(avg):
    """Mapea un promedio de pesos (1-4) al literal CNEB más cercano."""
    if avg is None:
        return False
    rounded = int(round(avg))
    rounded = max(1, min(4, rounded))
    inverse = {4: 'AD', 3: 'A', 2: 'B', 1: 'C'}
    return inverse[rounded]


class CnebAreaGrade(models.Model):
    _name = 'cneb.area.grade'
    _description = 'Calificación consolidada por área (CNEB / SIAGIE)'
    _order = 'period_id, batch_id, area_id, student_id'

    student_id = fields.Many2one(
        'op.student', string='Estudiante', required=True, ondelete='cascade',
    )
    area_id = fields.Many2one(
        'cneb.area', string='Área curricular', required=True,
        ondelete='restrict',
    )
    period_id = fields.Many2one(
        'cneb.evaluation.period', string='Periodo', required=True,
        ondelete='restrict',
    )
    batch_id = fields.Many2one(
        'op.batch', string='Grado / Sección', ondelete='restrict',
    )
    academic_year_id = fields.Many2one(
        'op.academic.year', string='Año académico',
    )
    level = fields.Selection(
        related='area_id.level', string='Nivel', store=True, readonly=True,
    )
    grading_type = fields.Selection(
        related='area_id.grading_type', string='Tipo de calificación',
        store=True, readonly=True,
    )

    grade = fields.Selection(
        CNEB_LITERAL_SELECTION, string='Calificativo de área (literal)',
        help='Calificativo consolidado del área. Decisión editable del docente '
             '(NO se auto-promedia). Vacío = sin evaluar (NO es C).',
    )
    grade_numeric = fields.Integer(
        string='Calificativo de área (0-20)',
        help='Usar solo cuando el área tiene tipo de calificación vigesimal.',
    )
    descriptive_conclusion = fields.Text(string='Conclusión descriptiva')

    suggested_grade = fields.Selection(
        CNEB_LITERAL_SELECTION, string='Sugerencia',
        compute='_compute_suggested_grade', store=False,
        help='Sugerencia (no vinculante) calculada según la estrategia '
             'configurada. El docente decide el calificativo final.',
    )

    student_code = fields.Char(
        string='Código de estudiante (SIAGIE)',
        compute='_compute_student_code', store=False,
        help='14 dígitos = "000000" + DNI(8). Vacío si el estudiante no tiene '
             'DNI registrado (se debe completar antes de exportar).',
    )
    student_code_warning = fields.Boolean(
        string='Sin código', compute='_compute_student_code', store=False,
    )

    export_state = fields.Selection(
        EXPORT_STATE_SELECTION, string='Estado de exportación',
        default='draft', required=True,
    )
    siagie_observation = fields.Text(
        string='Observación SIAGIE',
        help='Notas u observaciones devueltas por SIAGIE o del proceso de carga.',
    )

    _sql_constraints = [
        ('student_area_period_uniq',
         'unique(student_id, area_id, period_id)',
         'Ya existe un calificativo de esta área para el estudiante en este '
         'periodo.'),
    ]

    # ------------------------------------------------------------------
    # Computes
    # ------------------------------------------------------------------
    def _get_suggestion_strategy(self):
        return self.env['ir.config_parameter'].sudo().get_param(
            'sciback_cneb.suggestion_strategy', SUGGESTION_STRATEGY_DEFAULT,
        )

    @api.depends('student_id', 'area_id', 'period_id')
    def _compute_suggested_grade(self):
        strategy = self._get_suggestion_strategy()
        CompGrade = self.env['cneb.competency.grade']
        for rec in self:
            suggestion = False
            if rec.student_id and rec.area_id and rec.period_id:
                comp_grades = CompGrade.search([
                    ('student_id', '=', rec.student_id.id),
                    ('area_id', '=', rec.area_id.id),
                    ('period_id', '=', rec.period_id.id),
                    ('grade', '!=', False),
                ])
                literals = comp_grades.mapped('grade')
                if literals:
                    if strategy == 'mode':
                        suggestion = max(set(literals), key=literals.count)
                    else:  # 'last_period' -> promedio de pesos del periodo
                        weights = [CNEB_LITERAL_WEIGHT[g] for g in literals]
                        avg = sum(weights) / float(len(weights))
                        suggestion = _literal_from_weight(avg)
            rec.suggested_grade = suggestion

    @api.depends('student_id')
    def _compute_student_code(self):
        for rec in self:
            code = False
            warning = True
            dni = rec._get_student_dni()
            if dni and len(dni) == 8 and dni.isdigit():
                code = ('000000' + dni)  # 14 dígitos
                warning = False
            rec.student_code = code
            rec.student_code_warning = warning

    def _get_student_dni(self):
        """Lee el DNI del estudiante desde su partner.

        SUPOSICIÓN: el DNI vive en partner.vat o en un campo l10n_pe.
        Ajustar cuando se confirme el campo real usado por el cliente alfa.
        """
        self.ensure_one()
        partner = self.student_id.partner_id
        if not partner:
            return False
        raw = partner.vat or getattr(partner, 'l10n_pe_dni', False) or ''
        raw = ''.join(ch for ch in raw if ch.isdigit())
        return raw or False

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------
    @api.constrains('grade', 'descriptive_conclusion', 'level', 'grading_type')
    def _check_descriptive_conclusion(self):
        for rec in self:
            if rec.grading_type == 'vigesimal':
                continue
            needs = False
            if rec.level == 'inicial':
                needs = True
            elif rec.grade in ('C', 'AD'):
                needs = True
            if needs and not (rec.descriptive_conclusion or '').strip():
                raise ValidationError(
                    'La conclusión descriptiva es obligatoria '
                    '(Inicial siempre; Primaria/Secundaria cuando el calificativo '
                    'es C o AD). Estudiante: %s, área: %s.' % (
                        rec.student_id.display_name or '',
                        rec.area_id.display_name or '',
                    )
                )

    @api.constrains('grade', 'grade_numeric', 'grading_type')
    def _check_grading_type_coherence(self):
        for rec in self:
            if rec.grading_type == 'literal' and rec.grade_numeric:
                raise ValidationError(
                    'El área "%s" usa escala LITERAL: no debe tener un '
                    'calificativo vigesimal (0-20).' % (rec.area_id.display_name,)
                )
            if rec.grading_type == 'vigesimal' and rec.grade:
                raise ValidationError(
                    'El área "%s" usa escala VIGESIMAL: no debe tener un '
                    'calificativo literal (AD/A/B/C).' % (rec.area_id.display_name,)
                )

    @api.constrains('grade_numeric', 'grading_type')
    def _check_numeric_range(self):
        for rec in self:
            if rec.grading_type == 'vigesimal' and rec.grade_numeric:
                if not (0 <= rec.grade_numeric <= 20):
                    raise ValidationError(
                        'El calificativo vigesimal debe ser un entero entre 0 y '
                        '20. Estudiante: %s, área: %s.' % (
                            rec.student_id.display_name or '',
                            rec.area_id.display_name or '',
                        )
                    )

    # ------------------------------------------------------------------
    # Acciones
    # ------------------------------------------------------------------
    def action_apply_suggestion(self):
        """Copia la sugerencia al calificativo (solo áreas literales)."""
        for rec in self:
            if rec.grading_type == 'literal' and rec.suggested_grade:
                rec.grade = rec.suggested_grade

    def action_mark_generated(self):
        self.write({'export_state': 'generated'})

    def action_mark_uploaded(self):
        self.write({'export_state': 'uploaded'})

    def action_mark_confirmed(self):
        self.write({'export_state': 'confirmed'})

    def action_reset_draft(self):
        self.write({'export_state': 'draft'})
