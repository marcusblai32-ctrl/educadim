import io

from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext as _
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.utils import simpleSplit
from reportlab.pdfgen import canvas

from .models import PointsUtilisateur


PERIOD_FIELDS = {
    "total": "total",
    "semaine": "semaine",
    "mois": "mois",
}

PERIOD_LABELS = {
    "total": _("Classement général"),
    "semaine": _("Classement de la semaine"),
    "mois": _("Classement du mois"),
}


def normalize_period(period):
    return period if period in PERIOD_FIELDS else "total"


def get_ranked_users(period="total", limit=20):
    """Use the same stored point totals as the on-screen leaderboard."""
    period = normalize_period(period)
    return (
        PointsUtilisateur.objects.select_related("utilisateur")
        .order_by(
            f"-{PERIOD_FIELDS[period]}",
            "utilisateur__last_name",
            "utilisateur__first_name",
            "pk",
        )[:limit]
    )


def render_palmares_pdf(period="total", entries=None):
    """Render a compact, printable PDF of the current points leaderboard."""
    period = normalize_period(period)
    entries = list(entries if entries is not None else get_ranked_users(period))
    page_width, page_height = landscape(A4)
    output = io.BytesIO()
    pdf = canvas.Canvas(
        output,
        pagesize=(page_width, page_height),
        pageCompression=1,
    )
    pdf.setTitle(f"{settings.SITE_NAME} — {PERIOD_LABELS[period]}")
    pdf.setAuthor(settings.SITE_NAME)

    navy = colors.HexColor("#14223d")
    gold = colors.HexColor("#bf9655")
    muted = colors.HexColor("#536176")
    paper = colors.HexColor("#fbf9f4")
    margin = 38

    pdf.setFillColor(paper)
    pdf.rect(0, 0, page_width, page_height, stroke=0, fill=1)
    pdf.setStrokeColor(navy)
    pdf.setLineWidth(1.8)
    pdf.roundRect(
        22,
        22,
        page_width - 44,
        page_height - 44,
        7,
        stroke=1,
        fill=0,
    )
    pdf.setFillColor(navy)
    pdf.setFont("Times-Bold", 13)
    pdf.drawCentredString(page_width / 2, page_height - 62, settings.SITE_NAME.upper())
    pdf.setStrokeColor(gold)
    pdf.setLineWidth(1)
    pdf.line(page_width / 2 - 80, page_height - 73, page_width / 2 + 80, page_height - 73)
    pdf.setFillColor(navy)
    pdf.setFont("Times-Bold", 23)
    pdf.drawCentredString(page_width / 2, page_height - 108, "PALMARÈS")
    pdf.setFillColor(muted)
    pdf.setFont("Helvetica", 10)
    pdf.drawCentredString(
        page_width / 2,
        page_height - 127,
        str(PERIOD_LABELS[period]),
    )
    pdf.drawCentredString(
        page_width / 2,
        page_height - 143,
        f"{len(entries)} apprenant(s) — généré le "
        f"{timezone.localtime().strftime('%d/%m/%Y à %H:%M')}",
    )

    table_left = margin
    table_right = page_width - margin
    header_top = page_height - 163
    row_height = 17
    rank_x = table_left + 13
    name_x = table_left + 72
    points_x = table_right - 72

    pdf.setFillColor(navy)
    pdf.roundRect(
        table_left,
        header_top - row_height,
        table_right - table_left,
        row_height,
        4,
        stroke=0,
        fill=1,
    )
    pdf.setFillColor(colors.white)
    pdf.setFont("Helvetica-Bold", 8)
    pdf.drawString(rank_x, header_top - 11.5, "RANG")
    pdf.drawString(name_x, header_top - 11.5, "ÉTUDIANT")
    pdf.drawRightString(points_x, header_top - 11.5, "POINTS")

    current_top = header_top - row_height - 2
    for index, entry in enumerate(entries, start=1):
        row_bottom = current_top - row_height
        if index % 2 == 0:
            pdf.setFillColor(colors.HexColor("#f0eee8"))
            pdf.rect(
                table_left + 1,
                row_bottom,
                table_right - table_left - 2,
                row_height,
                stroke=0,
                fill=1,
            )
        pdf.setFillColor(gold if index <= 3 else navy)
        pdf.setFont("Helvetica-Bold", 9)
        pdf.drawString(rank_x, row_bottom + 5.5, f"#{index}")

        student_name = entry.utilisateur.get_full_name().strip()
        if not student_name:
            student_name = entry.utilisateur.email
        available_name_width = points_x - name_x - 22
        while (
            student_name
            and pdf.stringWidth(student_name, "Helvetica", 9) > available_name_width
        ):
            student_name = student_name[:-4].rstrip() + "..."
        pdf.setFillColor(navy)
        pdf.setFont("Helvetica", 9)
        pdf.drawString(name_x, row_bottom + 5.5, student_name)
        pdf.setFont("Helvetica-Bold", 9)
        pdf.drawRightString(
            points_x,
            row_bottom + 5.5,
            f"{getattr(entry, PERIOD_FIELDS[period])} pts",
        )
        pdf.setStrokeColor(colors.HexColor("#d9dce2"))
        pdf.setLineWidth(0.35)
        pdf.line(table_left, row_bottom, table_right, row_bottom)
        current_top = row_bottom

    if not entries:
        pdf.setFillColor(muted)
        pdf.setFont("Helvetica-Oblique", 10)
        pdf.drawCentredString(
            page_width / 2,
            current_top - 25,
            "Aucun point enregistré pour le moment.",
        )

    pdf.save()
    return output.getvalue()
