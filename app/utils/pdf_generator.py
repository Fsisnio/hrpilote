#!/usr/bin/env python3
"""
PDF Generation Utility for Payroll Reports
"""

import os
from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from typing import Dict, List, Any


class PayrollPDFGenerator:
    """Generate PDF reports for payroll data"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        ))
        
        # Subtitle style
        self.styles.add(ParagraphStyle(
            name='CustomSubtitle',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        ))
        
        # Header style
        self.styles.add(ParagraphStyle(
            name='CustomHeader',
            parent=self.styles['Heading3'],
            fontSize=12,
            spaceAfter=15,
            textColor=colors.darkblue
        ))
        
        # Normal text style
        self.styles.add(ParagraphStyle(
            name='CustomNormal',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=6
        ))
    
    def generate_summary_report(self, data: Dict[str, Any]) -> BytesIO:
        """Generate summary payroll report PDF"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
        
        # Build the story
        story = []
        
        # Title
        story.append(Paragraph("PAYROLL SUMMARY REPORT", self.styles['CustomTitle']))
        story.append(Spacer(1, 12))
        
        # Report details
        story.append(Paragraph(f"Period: {data['period']}", self.styles['CustomSubtitle']))
        story.append(Paragraph(f"Generated: {datetime.fromisoformat(data['generated_at']).strftime('%B %d, %Y at %I:%M %p')}", self.styles['CustomNormal']))
        story.append(Spacer(1, 20))
        
        # Summary statistics
        story.append(Paragraph("Summary Statistics", self.styles['CustomHeader']))
        
        summary_data = [
            ['Metric', 'Value'],
            ['Total Employees', str(data['summary']['total_employees'])],
            ['Total Gross Pay', f"${data['summary']['total_gross_pay']:,.2f}"],
            ['Total Net Pay', f"${data['summary']['total_net_pay']:,.2f}"],
            ['Total Deductions', f"${data['summary']['total_deductions']:,.2f}"],
            ['Average Salary', f"${data['summary']['average_salary']:,.2f}"]
        ]
        
        summary_table = Table(summary_data, colWidths=[2*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 20))
        
        # Department breakdown
        if 'department_stats' in data:
            story.append(Paragraph("Department Breakdown", self.styles['CustomHeader']))
            
            dept_headers = ['Department', 'Employees', 'Total Gross', 'Total Net', 'Avg Salary']
            dept_data = [dept_headers]
            
            for dept_name, dept_info in data['department_stats'].items():
                dept_data.append([
                    dept_name,
                    str(dept_info['employee_count']),
                    f"${dept_info['total_gross']:,.2f}",
                    f"${dept_info['total_net']:,.2f}",
                    f"${dept_info['avg_salary']:,.2f}"
                ])
            
            dept_table = Table(dept_data, colWidths=[1.5*inch, 0.8*inch, 1.2*inch, 1.2*inch, 1.2*inch])
            dept_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightblue),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 9)
            ]))
            
            story.append(dept_table)
        
        # Footer
        story.append(Spacer(1, 30))
        story.append(Paragraph("This report was generated automatically by the HR Pilot System", self.styles['CustomNormal']))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer
    
    def generate_detailed_report(self, data: Dict[str, Any]) -> BytesIO:
        """Generate detailed payroll report PDF"""
        buffer = BytesIO()
        # Use landscape orientation and reduce margins for better table fit
        doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), rightMargin=36, leftMargin=36, topMargin=72, bottomMargin=18)
        
        story = []
        
        # Title
        story.append(Paragraph("PAYROLL DETAILED REPORT", self.styles['CustomTitle']))
        story.append(Spacer(1, 12))
        
        # Report details
        story.append(Paragraph(f"Period: {data['period']}", self.styles['CustomSubtitle']))
        story.append(Paragraph(f"Generated: {datetime.fromisoformat(data['generated_at']).strftime('%B %d, %Y at %I:%M %p')}", self.styles['CustomNormal']))
        story.append(Paragraph(f"Total Records: {data['total_records']}", self.styles['CustomNormal']))
        story.append(Spacer(1, 20))
        
        # Employee details table
        story.append(Paragraph("Employee Payroll Details", self.styles['CustomHeader']))
        
        # Simplified headers to fit better
        headers = ['Employee', 'Dept', 'Basic', 'Allow', 'Bonus', 'OT', 'Gross', 'Deduct', 'Net', 'Status']
        table_data = [headers]
        
        for record in data['records']:
            # Truncate long names and departments to fit (with more space in landscape)
            employee_name = record['employee_name'][:20] + "..." if len(record['employee_name']) > 20 else record['employee_name']
            department = record['department'][:18] + "..." if len(record['department']) > 18 else record['department']
            
            table_data.append([
                employee_name,
                department,
                f"${record['basic_salary']:,.0f}",
                f"${record['allowances']:,.0f}",
                f"${record['bonuses']:,.0f}",
                f"${record['overtime']:,.0f}",
                f"${record['gross_pay']:,.0f}",
                f"${record['deductions']:,.0f}",
                f"${record['net_pay']:,.0f}",
                record['status']
            ])
        
        # Optimized column widths for landscape A4 page
        # Total width: A4 landscape width (11.69") - margins (0.5" each side) = 10.69"
        col_widths = [1.5*inch, 1.0*inch, 1.0*inch, 0.9*inch, 0.9*inch, 0.8*inch, 1.0*inch, 0.9*inch, 1.0*inch, 0.8*inch]
        table = Table(table_data, colWidths=col_widths)
        
        # Apply table styling with smaller fonts
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 7),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightblue),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 6),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.lightblue, colors.white]),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 2),
            ('RIGHTPADDING', (0, 0), (-1, -1), 2)
        ]))
        
        story.append(table)
        
        # Add page break if table is too long (more records per page in landscape)
        records_per_page = 35  # Landscape allows more records per page
        if len(data['records']) > records_per_page:
            story.append(PageBreak())
            story.append(Paragraph("Employee Payroll Details (Continued)", self.styles['CustomHeader']))
            story.append(Spacer(1, 10))
            
            # Continue with remaining records
            remaining_data = [headers] + table_data[records_per_page + 1:]  # Skip header and first page rows
            remaining_table = Table(remaining_data, colWidths=col_widths)
            remaining_table.setStyle(table.getStyle())
            story.append(remaining_table)
        
        # Footer
        story.append(Spacer(1, 30))
        story.append(Paragraph("This report was generated automatically by the HR Pilot System", self.styles['CustomNormal']))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer
    
    def generate_tax_report(self, data: Dict[str, Any]) -> BytesIO:
        """Generate tax report PDF"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
        
        story = []
        
        # Title
        story.append(Paragraph("PAYROLL TAX REPORT", self.styles['CustomTitle']))
        story.append(Spacer(1, 12))
        
        # Report details
        story.append(Paragraph(f"Period: {data['period']}", self.styles['CustomSubtitle']))
        story.append(Paragraph(f"Generated: {datetime.fromisoformat(data['generated_at']).strftime('%B %d, %Y at %I:%M %p')}", self.styles['CustomNormal']))
        story.append(Spacer(1, 20))
        
        # Tax summary
        story.append(Paragraph("Tax Summary", self.styles['CustomHeader']))
        
        tax_data = [
            ['Tax Component', 'Amount'],
            ['Total Income Tax', f"${data['tax_summary']['total_income_tax']:,.2f}"],
            ['Total Insurance', f"${data['tax_summary']['total_insurance']:,.2f}"],
            ['Total Pension', f"${data['tax_summary']['total_pension']:,.2f}"],
            ['Total Tax Liability', f"${data['tax_summary']['total_tax_liability']:,.2f}"]
        ]
        
        tax_table = Table(tax_data, colWidths=[2*inch, 2*inch])
        tax_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkred),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightcoral),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(tax_table)
        story.append(Spacer(1, 20))
        
        # Tax brackets
        story.append(Paragraph("Tax Bracket Analysis", self.styles['CustomHeader']))
        
        bracket_data = [
            ['Bracket', 'Employee Count', 'Total Tax'],
            ['Low Income (<$50K)', str(data['tax_brackets']['low']['count']), f"${data['tax_brackets']['low']['total_tax']:,.2f}"],
            ['Medium Income ($50K-$100K)', str(data['tax_brackets']['medium']['count']), f"${data['tax_brackets']['medium']['total_tax']:,.2f}"],
            ['High Income (>$100K)', str(data['tax_brackets']['high']['count']), f"${data['tax_brackets']['high']['total_tax']:,.2f}"]
        ]
        
        bracket_table = Table(bracket_data, colWidths=[2*inch, 1.5*inch, 1.5*inch])
        bracket_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgreen),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(bracket_table)
        
        # Footer
        story.append(Spacer(1, 30))
        story.append(Paragraph("This report was generated automatically by the HR Pilot System", self.styles['CustomNormal']))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer
    
    def generate_benefits_report(self, data: Dict[str, Any]) -> BytesIO:
        """Generate benefits report PDF"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
        
        story = []
        
        # Title
        story.append(Paragraph("PAYROLL BENEFITS REPORT", self.styles['CustomTitle']))
        story.append(Spacer(1, 12))
        
        # Report details
        story.append(Paragraph(f"Period: {data['period']}", self.styles['CustomSubtitle']))
        story.append(Paragraph(f"Generated: {datetime.fromisoformat(data['generated_at']).strftime('%B %d, %Y at %I:%M %p')}", self.styles['CustomNormal']))
        story.append(Spacer(1, 20))
        
        # Benefits summary
        story.append(Paragraph("Benefits Summary", self.styles['CustomHeader']))
        
        benefits_data = [
            ['Benefit Type', 'Amount'],
            ['Total Allowances', f"${data['benefits_summary']['total_allowances']:,.2f}"],
            ['Total Bonuses', f"${data['benefits_summary']['total_bonuses']:,.2f}"],
            ['Total Overtime', f"${data['benefits_summary']['total_overtime']:,.2f}"],
            ['Total Insurance', f"${data['benefits_summary']['total_insurance']:,.2f}"],
            ['Total Pension', f"${data['benefits_summary']['total_pension']:,.2f}"],
            ['Total Benefits', f"${data['benefits_summary']['total_benefits']:,.2f}"]
        ]
        
        benefits_table = Table(benefits_data, colWidths=[2*inch, 2*inch])
        benefits_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.purple),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lavender),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(benefits_table)
        
        # Footer
        story.append(Spacer(1, 30))
        story.append(Paragraph("This report was generated automatically by the HR Pilot System", self.styles['CustomNormal']))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer
    
    def generate_report(self, report_type: str, data: Dict[str, Any]) -> BytesIO:
        """Generate PDF report based on type"""
        if report_type == "summary":
            return self.generate_summary_report(data)
        elif report_type == "detailed":
            return self.generate_detailed_report(data)
        elif report_type == "tax":
            return self.generate_tax_report(data)
        elif report_type == "benefits":
            return self.generate_benefits_report(data)
        else:
            raise ValueError(f"Unknown report type: {report_type}")


# Utility function for easy access
def generate_payroll_pdf(report_type: str, data: Dict[str, Any]) -> BytesIO:
    """Generate payroll PDF report"""
    generator = PayrollPDFGenerator()
    return generator.generate_report(report_type, data)
