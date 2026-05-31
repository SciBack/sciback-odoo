# -*- coding: utf-8 -*-
{
    'name': 'SciBack CNEB - Evaluación',
    'version': '17.0.1.0.0',
    'category': 'Education',
    'summary': 'Evaluación por competencias CNEB (literal AD/A/B/C) para colegios EBR peruanos',
    'description': """
SciBack CNEB - Evaluación
=========================
Implementa la evaluación formativa por competencias según el Currículo Nacional
de la Educación Básica (CNEB) del Perú, para colegios EBR sobre OpenEduCat.

Jerarquía: Nivel (op.course) -> Grado/Sección (op.batch) -> Área curricular
(cneb.area) -> Competencia (cneb.competency).

- Se evalúa el logro POR COMPETENCIA (base pedagógica).
- Se consolida un calificativo POR ÁREA (cneb.area.grade) que es lo que se
  exporta a SIAGIE.
- Escala literal CNEB: AD (logro destacado), A (logro esperado), B (en proceso),
  C (en inicio). Vacío = sin evaluar (NO es C).
- Soporta también escala vigesimal 0-20 configurable por área (no default).
- Inicial: solo conclusiones descriptivas (sin literal).

Base normativa: RVM 048-2024-MINEDU (entre otras). Las abreviaturas SIAGIE
de las áreas son provisionales hasta validar con la plantilla SIAGIE real.
""",
    'author': 'SciBack',
    'website': 'https://sciback.com',
    'license': 'LGPL-3',
    'depends': [
        'openeducat_core',
        'sciback_school_base',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/cneb_area_data.xml',
        'views/cneb_area_views.xml',
        'views/cneb_competency_views.xml',
        'views/cneb_evaluation_period_views.xml',
        'views/cneb_competency_grade_views.xml',
        'views/cneb_area_grade_views.xml',
        'views/cneb_area_final_grade_views.xml',
        'wizard/cneb_bulk_grade_wizard_views.xml',
        'report/cneb_boletin_templates.xml',
        'wizard/cneb_report_boletin_wizard_views.xml',
        'views/cneb_menus.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
