"""
Advanced Reporting Engine for Pharmacy Revenue Management System
Version: 2.0
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging
from io import BytesIO
import tempfile
import os
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import matplotlib.pyplot as plt
import seaborn as sns
from sqlalchemy.orm import Session

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ReportGenerator:
    """Advanced report generation engine"""
    
    def __init__(self, db: Session):
        self.db = db
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        ))
        
        self.styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=16,
            spaceAfter=12,
            textColor=colors.darkblue
        ))
        
        self.styles.add(ParagraphStyle(
            name='CustomBody',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=6
        ))
    
    def generate_comprehensive_report(self, 
                                    start_date: datetime, 
                                    end_date: datetime,
                                    user_id: int,
                                    report_type: str = "comprehensive") -> Dict[str, Any]:
        """Generate comprehensive revenue report"""
        try:
            logger.info(f"Generating {report_type} report for user {user_id}")
            
            # Get data
            data = self._get_report_data(start_date, end_date, user_id)
            
            # Generate different report formats
            reports = {}
            
            if report_type in ["comprehensive", "excel"]:
                reports['excel'] = self._generate_excel_report(data, start_date, end_date)
            
            if report_type in ["comprehensive", "pdf"]:
                reports['pdf'] = self._generate_pdf_report(data, start_date, end_date)
            
            if report_type in ["comprehensive", "csv"]:
                reports['csv'] = self._generate_csv_reports(data)
            
            return {
                'success': True,
                'reports': reports,
                'generated_at': datetime.now().isoformat(),
                'period': f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
            }
            
        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'generated_at': datetime.now().isoformat()
            }
    
    def _get_report_data(self, start_date: datetime, end_date: datetime, user_id: int) -> Dict[str, Any]:
        """Get data for report generation"""
        try:
            from app.database import Invoice, MasterMapping, User
            from app.analytics_engine import AnalyticsEngine
            
            # Get user
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError("User not found")
            
            # Initialize analytics engine
            analytics_engine = AnalyticsEngine(self.db, user)
            
            # Get comprehensive data
            dashboard_data = analytics_engine.get_comprehensive_dashboard_data()
            
            # Get detailed data for the period
            invoices = self.db.query(Invoice).filter(
                Invoice.created_at >= start_date,
                Invoice.created_at <= end_date
            ).all()
            
            # Convert to DataFrames
            invoice_df = pd.DataFrame([
                {
                    'pharmacy_id': inv.pharmacy_id,
                    'pharmacy_name': inv.pharmacy_name,
                    'product': inv.product,
                    'quantity': inv.quantity,
                    'amount': float(inv.amount),
                    'invoice_date': inv.invoice_date,
                    'created_at': inv.created_at
                }
                for inv in invoices
            ])
            
            return {
                'dashboard_data': dashboard_data,
                'invoices': invoice_df,
                'period': {
                    'start_date': start_date,
                    'end_date': end_date
                },
                'user': {
                    'username': user.username,
                    'role': user.role,
                    'area': user.area
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting report data: {str(e)}")
            raise
    
    def _generate_excel_report(self, data: Dict[str, Any], start_date: datetime, end_date: datetime) -> str:
        """Generate comprehensive Excel report"""
        try:
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
            temp_filename = temp_file.name
            temp_file.close()
            
            with pd.ExcelWriter(temp_filename, engine='openpyxl') as writer:
                # Summary sheet
                self._create_summary_sheet(writer, data)
                
                # Revenue analytics sheet
                self._create_revenue_analytics_sheet(writer, data)
                
                # Monthly trends sheet
                self._create_trends_sheet(writer, data)
                
                # Detailed invoices sheet
                self._create_invoices_sheet(writer, data)
                
                # Performance metrics sheet
                self._create_performance_sheet(writer, data)
            
            return temp_filename
            
        except Exception as e:
            logger.error(f"Error generating Excel report: {str(e)}")
            raise
    
    def _create_summary_sheet(self, writer, data: Dict[str, Any]):
        """Create summary sheet"""
        summary_data = data['dashboard_data']['summary_metrics']
        
        summary_df = pd.DataFrame([
            {'Metric': 'Total Revenue', 'Value': summary_data['total_revenue']},
            {'Metric': 'Total Invoices', 'Value': summary_data['total_invoices']},
            {'Metric': 'Active Pharmacies', 'Value': summary_data['total_pharmacies']},
            {'Metric': 'Average Order Value', 'Value': summary_data['average_order_value']},
            {'Metric': 'Growth Rate', 'Value': f"{summary_data['growth_rate']:.2f}%"},
            {'Metric': 'Report Period', 'Value': f"{data['period']['start_date'].strftime('%Y-%m-%d')} to {data['period']['end_date'].strftime('%Y-%m-%d')}"},
            {'Metric': 'Generated By', 'Value': data['user']['username']},
            {'Metric': 'Generated At', 'Value': datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        ])
        
        summary_df.to_excel(writer, sheet_name='Summary', index=False)
    
    def _create_revenue_analytics_sheet(self, writer, data: Dict[str, Any]):
        """Create revenue analytics sheet"""
        revenue_data = data['dashboard_data']['revenue_analytics']
        
        # Pharmacy revenue
        if revenue_data['pharmacy_revenue']:
            pharmacy_df = pd.DataFrame(revenue_data['pharmacy_revenue'])
            pharmacy_df.to_excel(writer, sheet_name='Pharmacy Revenue', index=False)
        
        # Doctor revenue
        if revenue_data['doctor_revenue']:
            doctor_df = pd.DataFrame(revenue_data['doctor_revenue'])
            doctor_df.to_excel(writer, sheet_name='Doctor Revenue', index=False)
        
        # Rep revenue
        if revenue_data['rep_revenue']:
            rep_df = pd.DataFrame(revenue_data['rep_revenue'])
            rep_df.to_excel(writer, sheet_name='Rep Revenue', index=False)
    
    def _create_trends_sheet(self, writer, data: Dict[str, Any]):
        """Create trends sheet"""
        monthly_data = data['dashboard_data']['monthly_trends']
        
        if monthly_data:
            trends_df = pd.DataFrame(monthly_data)
            trends_df.to_excel(writer, sheet_name='Monthly Trends', index=False)
    
    def _create_invoices_sheet(self, writer, data: Dict[str, Any]):
        """Create detailed invoices sheet"""
        if not data['invoices'].empty:
            data['invoices'].to_excel(writer, sheet_name='Detailed Invoices', index=False)
    
    def _create_performance_sheet(self, writer, data: Dict[str, Any]):
        """Create performance metrics sheet"""
        performance = data['dashboard_data']['performance_metrics']
        
        performance_data = []
        if performance.get('top_pharmacy'):
            performance_data.append({
                'Metric': 'Top Pharmacy',
                'Value': performance['top_pharmacy']['name'],
                'Revenue': performance['top_pharmacy']['revenue']
            })
        
        if performance.get('averages'):
            performance_data.append({
                'Metric': 'Average Order Value',
                'Value': performance['averages']['order_value'],
                'Revenue': None
            })
            performance_data.append({
                'Metric': 'Average Quantity',
                'Value': performance['averages']['quantity'],
                'Revenue': None
            })
        
        if performance_data:
            performance_df = pd.DataFrame(performance_data)
            performance_df.to_excel(writer, sheet_name='Performance Metrics', index=False)
    
    def _generate_pdf_report(self, data: Dict[str, Any], start_date: datetime, end_date: datetime) -> str:
        """Generate comprehensive PDF report"""
        try:
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
            temp_filename = temp_file.name
            temp_file.close()
            
            # Create PDF document
            doc = SimpleDocTemplate(temp_filename, pagesize=A4)
            story = []
            
            # Title
            title = Paragraph("Pharmacy Revenue Management Report", self.styles['CustomTitle'])
            story.append(title)
            story.append(Spacer(1, 12))
            
            # Report info
            report_info = f"""
            <b>Report Period:</b> {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}<br/>
            <b>Generated By:</b> {data['user']['username']}<br/>
            <b>Generated At:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br/>
            <b>User Role:</b> {data['user']['role'].replace('_', ' ').title()}
            """
            story.append(Paragraph(report_info, self.styles['CustomBody']))
            story.append(Spacer(1, 20))
            
            # Summary metrics
            story.append(Paragraph("Executive Summary", self.styles['CustomHeading']))
            summary_data = data['dashboard_data']['summary_metrics']
            
            summary_table_data = [
                ['Metric', 'Value'],
                ['Total Revenue', f"₹{summary_data['total_revenue']:,.2f}"],
                ['Total Invoices', f"{summary_data['total_invoices']:,}"],
                ['Active Pharmacies', f"{summary_data['total_pharmacies']:,}"],
                ['Average Order Value', f"₹{summary_data['average_order_value']:,.2f}"],
                ['Growth Rate', f"{summary_data['growth_rate']:.2f}%"]
            ]
            
            summary_table = Table(summary_table_data)
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
            
            # Top performers
            story.append(Paragraph("Top Performers", self.styles['CustomHeading']))
            top_performers = data['dashboard_data']['top_performers']
            
            if top_performers.get('top_pharmacies'):
                story.append(Paragraph("Top Pharmacies by Revenue", self.styles['CustomBody']))
                pharmacy_data = [['Rank', 'Pharmacy Name', 'Revenue', 'Orders']]
                
                for i, pharmacy in enumerate(top_performers['top_pharmacies'][:5], 1):
                    pharmacy_data.append([
                        str(i),
                        pharmacy['pharmacy_name'],
                        f"₹{pharmacy['total_revenue']:,.2f}",
                        str(pharmacy['total_orders'])
                    ])
                
                pharmacy_table = Table(pharmacy_data)
                pharmacy_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                
                story.append(pharmacy_table)
                story.append(Spacer(1, 12))
            
            # Build PDF
            doc.build(story)
            
            return temp_filename
            
        except Exception as e:
            logger.error(f"Error generating PDF report: {str(e)}")
            raise
    
    def _generate_csv_reports(self, data: Dict[str, Any]) -> Dict[str, str]:
        """Generate CSV reports for different data categories"""
        try:
            csv_reports = {}
            
            # Revenue by pharmacy
            if data['dashboard_data']['revenue_analytics']['pharmacy_revenue']:
                pharmacy_df = pd.DataFrame(data['dashboard_data']['revenue_analytics']['pharmacy_revenue'])
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.csv')
                pharmacy_df.to_csv(temp_file.name, index=False)
                csv_reports['pharmacy_revenue'] = temp_file.name
            
            # Monthly trends
            if data['dashboard_data']['monthly_trends']:
                trends_df = pd.DataFrame(data['dashboard_data']['monthly_trends'])
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.csv')
                trends_df.to_csv(temp_file.name, index=False)
                csv_reports['monthly_trends'] = temp_file.name
            
            # Detailed invoices
            if not data['invoices'].empty:
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.csv')
                data['invoices'].to_csv(temp_file.name, index=False)
                csv_reports['detailed_invoices'] = temp_file.name
            
            return csv_reports
            
        except Exception as e:
            logger.error(f"Error generating CSV reports: {str(e)}")
            raise
    
    def generate_custom_report(self, 
                             template: str, 
                             filters: Dict[str, Any],
                             user_id: int) -> Dict[str, Any]:
        """Generate custom report based on template and filters"""
        try:
            logger.info(f"Generating custom report with template: {template}")
            
            # This would be expanded to support different report templates
            # For now, return a basic custom report
            return {
                'success': True,
                'message': f"Custom report generated using template: {template}",
                'filters_applied': filters,
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating custom report: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'generated_at': datetime.now().isoformat()
            }
    
    def get_report_templates(self) -> List[Dict[str, Any]]:
        """Get available report templates"""
        return [
            {
                'id': 'comprehensive',
                'name': 'Comprehensive Revenue Report',
                'description': 'Complete revenue analysis with all metrics and trends',
                'formats': ['excel', 'pdf', 'csv']
            },
            {
                'id': 'executive_summary',
                'name': 'Executive Summary',
                'description': 'High-level overview for management',
                'formats': ['pdf', 'excel']
            },
            {
                'id': 'pharmacy_performance',
                'name': 'Pharmacy Performance Report',
                'description': 'Detailed pharmacy-wise performance analysis',
                'formats': ['excel', 'csv']
            },
            {
                'id': 'monthly_trends',
                'name': 'Monthly Trends Report',
                'description': 'Monthly revenue trends and forecasting',
                'formats': ['excel', 'pdf']
            }
        ]
