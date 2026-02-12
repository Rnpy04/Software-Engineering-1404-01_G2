"""
PDF Generator for Trip Exports
Generates PDF files from Trip data for printing and sharing

TODO: Persian Font Support
Current limitation: Persian text may not render correctly with default fonts.
To fix:
1. Add a Persian font file (e.g., Vazir.ttf, Tahoma.ttf) to project
2. Register it with reportlab:
   from reportlab.pdfbase import pdfmetrics
   from reportlab.pdfbase.ttfonts import TTFont
   pdfmetrics.registerFont(TTFont('Vazir', 'path/to/Vazir.ttf'))
3. Use the font in ParagraphStyle:
   ParagraphStyle(..., fontName='Vazir')
"""
from io import BytesIO
from datetime import datetime
from typing import BinaryIO

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph,
    Spacer, PageBreak, Image
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from data.models import Trip


def generate_trip_pdf(trip: Trip) -> BytesIO:
    """
    Generate PDF from Trip data

    Args:
        trip: Trip model instance with prefetched days and items

    Returns:
        BytesIO: PDF file in memory

    Layout:
    - Header with trip title and dates
    - Trip summary (duration, budget, cost)
    - Timeline by days with items in table format
    - Footer with total cost breakdown
    """
    buffer = BytesIO()

    # Create PDF document
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm,
        title=f"Trip: {trip.title}",
        author="Trip Plan Service"
    )

    # Build document content
    story = []
    styles = getSampleStyleSheet()

    # Add custom RTL style for Persian text
    rtl_style = ParagraphStyle(
        'RTL',
        parent=styles['Normal'],
        alignment=TA_RIGHT,
        fontSize=11,
        leading=14
    )

    title_style = ParagraphStyle(
        'Title_RTL',
        parent=styles['Title'],
        alignment=TA_CENTER,
        fontSize=18,
        leading=22,
        spaceAfter=12
    )

    heading_style = ParagraphStyle(
        'Heading_RTL',
        parent=styles['Heading2'],
        alignment=TA_RIGHT,
        fontSize=14,
        leading=18,
        spaceAfter=8,
        textColor=colors.HexColor('#1a73e8')
    )

    # === HEADER SECTION ===
    title = Paragraph(f"<b>{trip.title}</b>", title_style)
    story.append(title)
    story.append(Spacer(1, 0.5*cm))

    # Trip metadata
    metadata_data = [
        ['مقصد:', f"{trip.province}{f' - {trip.city}' if trip.city else ''}"],
        ['تاریخ شروع:', str(trip.start_date)],
        ['تاریخ پایان:', str(trip.end_date)],
        ['مدت:', f"{(trip.end_date - trip.start_date).days + 1} روز"],
        ['سطح بودجه:', trip.get_budget_level_display()],
        ['هزینه تخمینی:', f"{int(trip.total_estimated_cost):,} تومان"]
    ]

    metadata_table = Table(metadata_data, colWidths=[4*cm, 12*cm])
    metadata_table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, -1), 'Helvetica', 10),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#5f6368')),
        ('TEXTCOLOR', (1, 0), (1, -1), colors.black),
        ('LINEBELOW', (0, 0), (-1, 0), 1, colors.HexColor('#dadce0')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(metadata_table)
    story.append(Spacer(1, 1*cm))

    # === DAYS & ITEMS SECTION ===
    days = trip.days.all().order_by('day_index')

    for day in days:
        # Day header
        day_header = Paragraph(
            f"<b>روز {day.day_index} - {day.specific_date}</b>",
            heading_style
        )
        story.append(day_header)
        story.append(Spacer(1, 0.3*cm))

        # Items table
        items = day.items.all().order_by('sort_order')

        if items.exists():
            # Table header
            table_data = [[
                'هزینه',
                'مدت',
                'زمان',
                'عنوان',
                'نوع'
            ]]

            # Add items
            for item in items:
                duration = item.duration_minutes or 0
                hours = duration // 60
                minutes = duration % 60
                duration_str = f"{hours}س {minutes}د" if hours > 0 else f"{minutes}د"

                table_data.append([
                    f"{int(item.estimated_cost):,}" if item.estimated_cost else "-",
                    duration_str,
                    f"{item.start_time.strftime('%H:%M')} - {item.end_time.strftime('%H:%M')}",
                    item.title[:40] +
                    "..." if len(item.title) > 40 else item.title,
                    item.get_item_type_display()
                ])

            # Create table
            items_table = Table(
                table_data,
                colWidths=[2.5*cm, 2*cm, 3*cm, 7*cm, 2*cm]
            )

            items_table.setStyle(TableStyle([
                # Header row styling
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a73e8')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold', 10),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),

                # Data rows styling
                ('FONT', (0, 1), (-1, -1), 'Helvetica', 9),
                ('ALIGN', (0, 1), (2, -1), 'CENTER'),  # Cost, duration, time
                ('ALIGN', (3, 1), (3, -1), 'RIGHT'),   # Title
                ('ALIGN', (4, 1), (4, -1), 'CENTER'),  # Type

                # Alternating row colors
                ('ROWBACKGROUNDS', (0, 1), (-1, -1),
                 [colors.white, colors.HexColor('#f8f9fa')]),

                # Borders
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dadce0')),
                ('LINEBELOW', (0, 0), (-1, 0), 2, colors.HexColor('#1a73e8')),

                # Padding
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),

                # Vertical alignment
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))

            story.append(items_table)
        else:
            # No items for this day
            no_items_text = Paragraph(
                "<i>هیچ برنامه‌ای برای این روز تعریف نشده است.</i>",
                rtl_style
            )
            story.append(no_items_text)

        story.append(Spacer(1, 0.8*cm))

    # === FOOTER SECTION: Cost Breakdown ===
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph("<b>خلاصه هزینه‌ها</b>", heading_style))
    story.append(Spacer(1, 0.3*cm))

    # Calculate cost breakdown by category
    cost_breakdown = {}
    total_cost = 0

    for day in days:
        for item in day.items.all():
            cost = float(item.estimated_cost or 0)
            category = item.get_category_display() if item.category else 'سایر'

            if category not in cost_breakdown:
                cost_breakdown[category] = 0

            cost_breakdown[category] += cost
            total_cost += cost

    # Breakdown table
    breakdown_data = [['دسته‌بندی', 'مبلغ']]
    for category, cost in sorted(cost_breakdown.items(), key=lambda x: x[1], reverse=True):
        breakdown_data.append([category, f"{int(cost):,} تومان"])

    # Add total row
    breakdown_data.append(['جمع کل', f"{int(total_cost):,} تومان"])

    breakdown_table = Table(breakdown_data, colWidths=[10*cm, 6*cm])
    breakdown_table.setStyle(TableStyle([
        # Header
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e8f0fe')),
        ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold', 10),
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),

        # Data rows
        ('FONT', (0, 1), (-1, -2), 'Helvetica', 10),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2),
         [colors.white, colors.HexColor('#f8f9fa')]),

        # Total row
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#1a73e8')),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.whitesmoke),
        ('FONT', (0, -1), (-1, -1), 'Helvetica-Bold', 11),

        # Borders
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dadce0')),
        ('LINEABOVE', (0, -1), (-1, -1), 2, colors.HexColor('#1a73e8')),

        # Padding
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))

    story.append(breakdown_table)

    # === METADATA FOOTER ===
    story.append(Spacer(1, 1*cm))
    footer_text = Paragraph(
        f"<i>تولید شده در {datetime.now().strftime('%Y-%m-%d %H:%M')} توسط Trip Plan Service</i>",
        ParagraphStyle('Footer', parent=rtl_style, fontSize=8,
                       textColor=colors.HexColor('#5f6368'))
    )
    story.append(footer_text)

    # Build PDF
    doc.build(story)

    # Reset buffer position
    buffer.seek(0)
    return buffer


def get_filename_for_trip(trip: Trip) -> str:
    """
    Generate safe filename for trip PDF

    Args:
        trip: Trip instance

    Returns:
        str: Filename like "trip_2_Isfahan_2026-05-01.pdf"
    """
    # Sanitize title (remove special chars)
    safe_title = "".join(c for c in trip.title if c.isalnum()
                         or c in (' ', '-', '_')).strip()
    safe_title = safe_title.replace(' ', '_')[:30]  # Max 30 chars

    return f"trip_{trip.trip_id}_{safe_title}_{trip.start_date}.pdf"
