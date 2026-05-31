# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from ..models.cneb_competency_grade import CNEB_LITERAL_SELECTION


class CnebBulkGradeWizard(models.TransientModel):
    _name = "cneb.bulk.grade.wizard"
    _description = "Carga masiva de calificativos por sección CNEB"

    period_id = fields.Many2one(
        "cneb.evaluation.period", string="Periodo", required=True
    )
    batch_id = fields.Many2one(
        "op.batch", string="Grado/Sección", required=True
    )
    area_id = fields.Many2one(
        "cneb.area", string="Área curricular", required=True
    )
    academic_year_id = fields.Many2one(
        "op.academic.year",
        string="Año académico",
        related="period_id.academic_year_id",
        store=False,
        readonly=True,
    )
    grading_type = fields.Selection(
        related="area_id.grading_type", string="Tipo de calificación", readonly=True
    )
    level = fields.Selection(
        related="area_id.level", string="Nivel", readonly=True
    )
    line_ids = fields.One2many(
        "cneb.bulk.grade.line", "wizard_id", string="Estudiantes"
    )

    @api.onchange("batch_id", "period_id", "area_id")
    def _onchange_reset_lines(self):
        # Limpiar líneas cuando cambian los selectores para evitar
        # mezclar estudiantes de secciones/periodos distintos.
        if self.line_ids:
            self.line_ids = [(5, 0, 0)]

    def _get_enrolled_students(self):
        """Devuelve los op.student matriculados en la sección/año seleccionados."""
        self.ensure_one()
        if not self.batch_id:
            return self.env["op.student"]
        domain = [("batch_id", "=", self.batch_id.id)]
        if self.academic_year_id:
            domain.append(("academic_years_id", "=", self.academic_year_id.id))
        enrollments = self.env["op.student.course"].search(domain)
        students = enrollments.mapped("student_id")
        if not students and self.academic_year_id:
            # Reintento sin filtro de año por si la matrícula no lo tiene seteado.
            enrollments = self.env["op.student.course"].search(
                [("batch_id", "=", self.batch_id.id)]
            )
            students = enrollments.mapped("student_id")
        return students

    def action_load_students(self):
        """Rellena las líneas con los estudiantes de la sección, precargando
        cualquier calificativo ya existente para (estudiante, área, periodo)."""
        self.ensure_one()
        if not (self.period_id and self.batch_id and self.area_id):
            raise UserError(
                _("Selecciona periodo, grado/sección y área antes de cargar.")
            )
        students = self._get_enrolled_students()
        if not students:
            raise UserError(
                _(
                    "No se encontraron estudiantes matriculados en la sección "
                    "'%s' para el año seleccionado."
                )
                % (self.batch_id.display_name,)
            )
        AreaGrade = self.env["cneb.area.grade"]
        lines = [(5, 0, 0)]
        for student in students.sorted(key=lambda s: (s.last_name or "", s.first_name or "")):
            existing = AreaGrade.search(
                [
                    ("student_id", "=", student.id),
                    ("area_id", "=", self.area_id.id),
                    ("period_id", "=", self.period_id.id),
                ],
                limit=1,
            )
            lines.append((0, 0, {
                "student_id": student.id,
                "grade": existing.grade or False,
                "grade_numeric": existing.grade_numeric or 0,
                "descriptive_conclusion": existing.descriptive_conclusion or "",
            }))
        self.line_ids = lines
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }

    def _validate_conclusion(self, line):
        """Conclusión descriptiva obligatoria para Inicial y para los
        calificativos C y AD (criterio MINEDU/SIAGIE)."""
        is_inicial = self.level == "inicial"
        needs_conclusion = is_inicial or (line.grade in ("C", "AD"))
        if needs_conclusion and not (line.descriptive_conclusion or "").strip():
            raise ValidationError(
                _(
                    "El estudiante '%(name)s' requiere conclusión descriptiva "
                    "(obligatoria en Inicial y para los calificativos C y AD)."
                )
                % {"name": line.student_name}
            )

    def action_save_grades(self):
        """Upsert de cada línea en cneb.area.grade respetando la constraint
        única (student, area, period)."""
        self.ensure_one()
        if not self.line_ids:
            raise UserError(_("No hay estudiantes cargados para guardar."))
        AreaGrade = self.env["cneb.area.grade"]
        is_literal = self.grading_type != "vigesimal"
        saved = 0
        for line in self.line_ids:
            has_value = bool(line.grade) if is_literal else bool(line.grade_numeric)
            has_conclusion = bool((line.descriptive_conclusion or "").strip())
            if not has_value and not has_conclusion:
                # Línea vacía: se omite (docente aún no califica a ese alumno).
                continue
            self._validate_conclusion(line)
            vals = {
                "descriptive_conclusion": line.descriptive_conclusion or False,
            }
            if is_literal:
                vals["grade"] = line.grade or False
            else:
                vals["grade_numeric"] = line.grade_numeric or 0
            existing = AreaGrade.search(
                [
                    ("student_id", "=", line.student_id.id),
                    ("area_id", "=", self.area_id.id),
                    ("period_id", "=", self.period_id.id),
                ],
                limit=1,
            )
            if existing:
                existing.write(vals)
            else:
                vals.update({
                    "student_id": line.student_id.id,
                    "area_id": self.area_id.id,
                    "period_id": self.period_id.id,
                    "batch_id": self.batch_id.id,
                    "academic_year_id": self.academic_year_id.id,
                })
                AreaGrade.create(vals)
            saved += 1
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Calificativos guardados"),
                "message": _("Se registraron %s calificativos.") % saved,
                "type": "success",
                "sticky": False,
                "next": {"type": "ir.actions.act_window_close"},
            },
        }


class CnebBulkGradeLine(models.TransientModel):
    _name = "cneb.bulk.grade.line"
    _description = "Línea de carga masiva de calificativos CNEB"
    _order = "student_name"

    wizard_id = fields.Many2one(
        "cneb.bulk.grade.wizard", string="Asistente", ondelete="cascade"
    )
    student_id = fields.Many2one(
        "op.student", string="Estudiante", required=True, readonly=True
    )
    student_name = fields.Char(
        string="Estudiante", compute="_compute_student_name", store=True
    )
    grade = fields.Selection(
        CNEB_LITERAL_SELECTION, string="Calificativo literal"
    )
    grade_numeric = fields.Integer(string="Calificativo vigesimal")
    descriptive_conclusion = fields.Text(string="Conclusión descriptiva")
    grading_type = fields.Selection(
        related="wizard_id.grading_type", string="Tipo de calificación"
    )

    @api.depends("student_id")
    def _compute_student_name(self):
        for line in self:
            student = line.student_id
            if student:
                parts = [
                    student.last_name or "",
                    student.first_name or "",
                    student.middle_name or "",
                ]
                line.student_name = " ".join(p for p in parts if p).strip()
            else:
                line.student_name = ""
