# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class CnebReportBoletinWizard(models.TransientModel):
    _name = "cneb.report.boletin.wizard"
    _description = "Asistente de Boletín de Notas CNEB"

    academic_year_id = fields.Many2one(
        "op.academic.year", string="Año académico", required=True
    )
    batch_id = fields.Many2one("op.batch", string="Grado/Sección")
    period_id = fields.Many2one(
        "cneb.evaluation.period",
        string="Periodo",
        help="Déjalo vacío para emitir un boletín consolidado de todos los "
             "periodos del año académico.",
    )
    scope = fields.Selection(
        [("period", "Un periodo"), ("year", "Consolidado del año")],
        string="Alcance", default="period", required=True,
    )
    student_ids = fields.Many2many(
        "op.student", string="Estudiantes",
        help="Déjalo vacío para emitir el boletín de toda la sección.",
    )

    @api.onchange("scope")
    def _onchange_scope(self):
        if self.scope == "year":
            self.period_id = False

    @api.onchange("academic_year_id", "batch_id")
    def _onchange_filters(self):
        # Limitar selección de estudiantes a la sección/año elegidos.
        self.student_ids = False
        domain = []
        if self.batch_id:
            enrollments = self.env["op.student.course"].search(
                [("batch_id", "=", self.batch_id.id)]
            )
            domain = [("id", "in", enrollments.mapped("student_id").ids)]
        return {"domain": {"student_ids": domain}}

    def _resolve_students(self):
        self.ensure_one()
        if self.student_ids:
            return self.student_ids
        if not self.batch_id:
            raise UserError(
                _("Selecciona una sección o uno o más estudiantes.")
            )
        domain = [("batch_id", "=", self.batch_id.id)]
        if self.academic_year_id:
            domain.append(("academic_years_id", "=", self.academic_year_id.id))
        enrollments = self.env["op.student.course"].search(domain)
        students = enrollments.mapped("student_id")
        if not students:
            raise UserError(
                _("No se encontraron estudiantes para los filtros indicados.")
            )
        return students

    def action_print_boletin(self):
        self.ensure_one()
        if self.scope == "period" and not self.period_id:
            raise UserError(_("Selecciona un periodo o cambia el alcance a anual."))
        students = self._resolve_students()
        data = {
            "wizard_id": self.id,
            "scope": self.scope,
            "academic_year_id": self.academic_year_id.id,
            "batch_id": self.batch_id.id if self.batch_id else False,
            "period_id": self.period_id.id if self.period_id else False,
            "student_ids": students.ids,
        }
        report = self.env.ref(
            "sciback_cneb_evaluation.action_report_cneb_boletin"
        )
        return report.report_action(students, data=data)

    # ------------------------------------------------------------------
    # Helpers usados desde el AbstractModel del reporte
    # ------------------------------------------------------------------
    def _get_school_info(self):
        """Lee la configuración del colegio (sciback.school.config del módulo
        sciback_school_base). Devuelve placeholders si el modelo no existe o
        aún no se configuró el singleton."""
        info = {
            "name": _("Nombre del Colegio"),
            "code": "",
            "director": "",
        }
        if "sciback.school.config" not in self.env:
            return info
        config_model = self.env["sciback.school.config"]
        # get_config() lanza ValidationError si no hay singleton; no debe
        # romper la generación del boletín.
        config = config_model.search([], limit=1)
        if not config:
            return info
        info["name"] = config.name or info["name"]
        info["code"] = config.codigo_modular or ""
        if config.director_id:
            info["director"] = config.director_id.name or ""
        return info
