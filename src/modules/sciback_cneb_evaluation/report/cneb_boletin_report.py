# -*- coding: utf-8 -*-
from odoo import models, api, _


class CnebBoletinReport(models.AbstractModel):
    _name = "report.sciback_cneb_evaluation.report_cneb_boletin_document"
    _description = "Boletín de Notas CNEB"

    def _scale_legend(self):
        # Escala oficial CNEB (MINEDU) para la leyenda al pie.
        return [
            ("AD", _("Logro destacado")),
            ("A", _("Logro esperado")),
            ("B", _("En proceso")),
            ("C", _("En inicio")),
        ]

    def _student_full_name(self, student):
        parts = [
            student.last_name or "",
            student.first_name or "",
            student.middle_name or "",
        ]
        return " ".join(p for p in parts if p).strip() or student.name or ""

    def _student_code(self, student):
        """Código SIAGIE de 14 dígitos = '000000' + DNI(8).

        Reutiliza la convención de cneb.area.grade. El DNI vive en
        partner.vat (o l10n_pe_dni). Si no hay DNI válido, cae a gr_no.
        """
        partner = student.partner_id
        dni = ""
        if partner:
            raw = partner.vat or getattr(partner, "l10n_pe_dni", False) or ""
            dni = "".join(ch for ch in raw if ch.isdigit())
        if len(dni) == 8:
            return "000000" + dni
        return student.gr_no or ""

    def _student_section(self, student, batch_id):
        """Devuelve el op.batch (grado/sección) del estudiante."""
        batch = False
        if batch_id:
            batch = self.env["op.batch"].browse(batch_id)
        if not batch:
            enrollment = self.env["op.student.course"].search(
                [("student_id", "=", student.id)], limit=1, order="id desc"
            )
            batch = enrollment.batch_id if enrollment else False
        return batch

    def _get_periods(self, scope, period_id, academic_year_id):
        if scope == "period" and period_id:
            return self.env["cneb.evaluation.period"].browse(period_id)
        domain = []
        if academic_year_id:
            domain.append(("academic_year_id", "=", academic_year_id))
        return self.env["cneb.evaluation.period"].search(domain)

    def _build_student_block(self, student, periods):
        """Arma la estructura de áreas con calificativos del estudiante.

        - scope 'periodo' (un solo periodo): una columna de calificativo.
        - scope 'anual' (varios periodos): una columna por periodo.
        """
        AreaGrade = self.env["cneb.area.grade"]
        period_ids = periods.ids
        grades = AreaGrade.search([
            ("student_id", "=", student.id),
            ("period_id", "in", period_ids),
        ])
        areas = grades.mapped("area_id").sorted(
            key=lambda a: (a.level or "", a.name or "")
        )
        rows = []
        for area in areas:
            area_grades = grades.filtered(lambda g: g.area_id == area)
            per_period = {}
            conclusions = []
            for g in area_grades:
                if g.grading_type == "vigesimal":
                    display = str(g.grade_numeric) if g.grade_numeric else "-"
                else:
                    display = g.grade or "-"
                per_period[g.period_id.id] = display
                if g.descriptive_conclusion:
                    conclusions.append(g.descriptive_conclusion.strip())
            rows.append({
                "area": area,
                "is_literal": area.grading_type != "vigesimal",
                "per_period": per_period,
                "conclusion": conclusions[-1] if conclusions else "",
            })
        return rows

    @api.model
    def _get_report_values(self, docids, data=None):
        data = data or {}
        scope = data.get("scope", "period")
        period_id = data.get("period_id")
        academic_year_id = data.get("academic_year_id")
        batch_id = data.get("batch_id")
        student_ids = data.get("student_ids") or docids

        wizard = False
        if data.get("wizard_id"):
            wizard = self.env["cneb.report.boletin.wizard"].browse(
                data["wizard_id"]
            )
        if wizard and wizard.exists():
            school = wizard._get_school_info()
        else:
            school = {"name": _("Nombre del Colegio"), "code": "", "director": ""}

        periods = self._get_periods(scope, period_id, academic_year_id)
        academic_year = self.env["op.academic.year"].browse(academic_year_id) \
            if academic_year_id else self.env["op.academic.year"]

        students = self.env["op.student"].browse(student_ids).exists()

        docs = []
        for student in students.sorted(
            key=lambda s: (s.last_name or "", s.first_name or "")
        ):
            batch = self._student_section(student, batch_id)
            rows = self._build_student_block(student, periods)
            docs.append({
                "student": student,
                "full_name": self._student_full_name(student),
                "student_code": self._student_code(student),
                "batch": batch,
                "rows": rows,
            })

        return {
            "doc_ids": students.ids,
            "doc_model": "op.student",
            "docs": docs,
            "scope": scope,
            "periods": periods,
            "single_period": periods[:1] if scope == "period" else False,
            "academic_year": academic_year,
            "school": school,
            "scale_legend": self._scale_legend(),
        }
