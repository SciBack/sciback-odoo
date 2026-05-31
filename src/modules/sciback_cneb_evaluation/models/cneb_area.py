# -*- coding: utf-8 -*-
from odoo import models, fields, api


# Selección de nivel EBR. Se usa como clasificación rápida del área.
# Se mantiene también course_id (op.course) por si el colegio modela los
# niveles como cursos OpenEduCat. El selection es el discriminador pedagógico
# que decide reglas (p.ej. Inicial = solo descriptivo, sin literal).
CNEB_LEVEL_SELECTION = [
    ('inicial', 'Inicial'),
    ('primaria', 'Primaria'),
    ('secundaria', 'Secundaria'),
]

GRADING_TYPE_SELECTION = [
    ('literal', 'Literal AD/A/B/C'),
    ('vigesimal', 'Vigesimal 0-20'),
]


class CnebArea(models.Model):
    _name = 'cneb.area'
    _description = 'Área curricular CNEB'
    _order = 'level, name'

    name = fields.Char(string='Área curricular', required=True, translate=False)
    code = fields.Char(string='Código', help='Código interno del área.')
    siagie_abbr = fields.Char(
        string='Abreviatura SIAGIE',
        help='Abreviatura usada al exportar a SIAGIE '
             '(ej. MATE, COMU_LM, CCAA, PPSS, CCSS). PROVISIONAL: '
             'ajustar contra la plantilla SIAGIE real.',
    )
    level = fields.Selection(
        CNEB_LEVEL_SELECTION,
        string='Nivel',
        required=True,
        help='Nivel EBR al que pertenece el área. En Inicial la evaluación es '
             'solo descriptiva (sin literal).',
    )
    course_id = fields.Many2one(
        'op.course',
        string='Nivel (OpenEduCat)',
        help='Vínculo opcional al curso OpenEduCat que representa el nivel.',
    )
    grading_type = fields.Selection(
        GRADING_TYPE_SELECTION,
        string='Tipo de calificación',
        default='literal',
        required=True,
        help='Literal (AD/A/B/C) es el estándar CNEB. Vigesimal (0-20) es un '
             'caso configurable por área (no es el comportamiento por defecto).',
    )
    competency_ids = fields.One2many(
        'cneb.competency', 'area_id', string='Competencias',
    )
    competency_count = fields.Integer(
        string='Nº competencias', compute='_compute_competency_count',
    )
    active = fields.Boolean(string='Activo', default=True)

    _sql_constraints = [
        ('code_uniq', 'unique(code)',
         'El código del área curricular debe ser único.'),
    ]

    @api.depends('competency_ids')
    def _compute_competency_count(self):
        for area in self:
            area.competency_count = len(area.competency_ids)

    def name_get(self):
        result = []
        for area in self:
            if area.siagie_abbr:
                label = '%s [%s]' % (area.name, area.siagie_abbr)
            else:
                label = area.name
            result.append((area.id, label))
        return result
