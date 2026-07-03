"""
Generates printable PDF documents:
  - Pledge ticket: issued to the customer when a loan is created. This is
    usually the customer's legal proof of pledge -- keep a copy on file too.
  - Repayment receipt: issued every time a payment is recorded.

Uses ReportLab (pure-Python, no system dependencies) so this works without
any extra install steps beyond `pip install reportlab`.
"""

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from reportlab.lib import colors
from reportlab.lib.pagesizes import A5
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from loans.models import Loan, Repayment

SHOP_NAME = "YOUR SHOP NAME HERE"
SHOP_ADDRESS = "Shop address, city, PIN -- update in documents/views.py"
SHOP_PHONE = "Phone: +91-XXXXXXXXXX"


def _styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='ShopTitle', fontSize=16, leading=20, alignment=1, fontName='Helvetica-Bold'))
    styles.add(ParagraphStyle(name='ShopSub', fontSize=9, leading=12, alignment=1, textColor=colors.grey))
    styles.add(ParagraphStyle(name='DocTitle', fontSize=12, leading=16, alignment=1, fontName='Helvetica-Bold', spaceAfter=8))
    return styles


def _header(elements, styles, doc_title):
    elements.append(Paragraph(SHOP_NAME, styles['ShopTitle']))
    elements.append(Paragraph(SHOP_ADDRESS, styles['ShopSub']))
    elements.append(Paragraph(SHOP_PHONE, styles['ShopSub']))
    elements.append(Spacer(1, 10 * mm))
    elements.append(Paragraph(doc_title, styles['DocTitle']))


@login_required
def pledge_ticket_pdf(request, loan_id):
    loan = get_object_or_404(Loan.objects.select_related('customer', 'item'), pk=loan_id)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="pledge_ticket_{loan.loan_number}.pdf"'

    doc = SimpleDocTemplate(response, pagesize=A5, topMargin=15 * mm, bottomMargin=15 * mm)
    styles = _styles()
    elements = []
    _header(elements, styles, f"PLEDGE TICKET - {loan.loan_number}")

    customer_data = [
        ["Customer Name", loan.customer.full_name],
        ["Phone", loan.customer.phone_number],
        ["ID Proof", f"{loan.customer.get_id_proof_type_display()} - {loan.customer.id_proof_number}"],
        ["Address", loan.customer.address],
    ]
    item = loan.item
    item_data = [
        ["Item", item.get_item_type_display()],
        ["Description", item.description],
        ["Metal / Purity", f"{item.get_metal_display()} / {item.purity}"],
        ["Gross Weight", f"{item.gross_weight_grams} g"],
        ["Net Weight", f"{item.net_weight_grams} g"],
        ["Appraised Value", f"Rs. {item.appraised_value}"],
    ]
    loan_data = [
        ["Loan Number", loan.loan_number],
        ["Principal Amount", f"Rs. {loan.principal_amount}"],
        ["Interest Rate", f"{loan.interest_rate_percent}% / month ({loan.get_interest_type_display()})"],
        ["Issue Date", loan.issue_date.strftime('%d-%b-%Y')],
        ["Due Date", loan.due_date.strftime('%d-%b-%Y')],
    ]

    for title, data in [("Customer Details", customer_data), ("Item Details", item_data), ("Loan Terms", loan_data)]:
        elements.append(Paragraph(title, styles['Heading4']))
        table = Table(data, colWidths=[45 * mm, 90 * mm])
        table.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.4, colors.lightgrey),
            ('BACKGROUND', (0, 0), (0, -1), colors.whitesmoke),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 6 * mm))

    elements.append(Spacer(1, 10 * mm))
    elements.append(Paragraph(
        "By pledging this item, the customer agrees to the shop's terms for redemption, "
        "renewal, and auction in the event of default. Please retain this ticket -- it is "
        "required to redeem your item.",
        styles['ShopSub'],
    ))

    doc.build(elements)
    return response


@login_required
def repayment_receipt_pdf(request, repayment_id):
    repayment = get_object_or_404(Repayment.objects.select_related('loan', 'loan__customer'), pk=repayment_id)
    loan = repayment.loan

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="receipt_{repayment.receipt_number}.pdf"'

    doc = SimpleDocTemplate(response, pagesize=A5, topMargin=15 * mm, bottomMargin=15 * mm)
    styles = _styles()
    elements = []
    _header(elements, styles, f"PAYMENT RECEIPT - {repayment.receipt_number}")

    data = [
        ["Loan Number", loan.loan_number],
        ["Customer", loan.customer.full_name],
        ["Payment Date", repayment.payment_date.strftime('%d-%b-%Y')],
        ["Payment Type", repayment.get_payment_type_display()],
        ["Interest Paid", f"Rs. {repayment.interest_component}"],
        ["Principal Paid", f"Rs. {repayment.principal_component}"],
        ["Total Amount Received", f"Rs. {repayment.amount}"],
        ["Outstanding Balance After This Payment", f"Rs. {loan.outstanding_balance}"],
    ]
    table = Table(data, colWidths=[70 * mm, 70 * mm])
    table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.4, colors.lightgrey),
        ('BACKGROUND', (0, 0), (0, -1), colors.whitesmoke),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(table)

    doc.build(elements)
    return response
