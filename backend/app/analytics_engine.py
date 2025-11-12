"""
Advanced Analytics Engine for Pharmacy Revenue Management System
Version: 2.0
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, extract, desc
from datetime import datetime, timedelta, date
from decimal import Decimal
import logging
import redis
import json
from collections import defaultdict

from app.database import Invoice, MasterMapping, Allocation, User
from app.auth import mask_sensitive_data

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Redis connection for caching
redis_client = redis.Redis(host='redis', port=6379, decode_responses=True)

class AnalyticsEngine:
    """Advanced analytics engine with comprehensive revenue calculations"""
    
    def __init__(self, db: Session, user: User):
        self.db = db
        self.user = user
        self.cache_prefix = f"analytics_{user.id}"
        
    def get_comprehensive_dashboard_data(self) -> Dict[str, Any]:
        """
        Get comprehensive dashboard analytics data
        
        Returns:
            Dictionary with all dashboard analytics
        """
        try:
            logger.info(f"Generating comprehensive dashboard data for user {self.user.username}")
            
            # Check cache first
            cache_key = f"{self.cache_prefix}_dashboard"
            cached_data = redis_client.get(cache_key)
            
            if cached_data and self.user.role != 'super_admin':  # Don't cache for super admin (real-time data)
                return json.loads(cached_data)
            
            # Generate fresh analytics
            dashboard_data = {
                'summary_metrics': self.get_summary_metrics(),
                'revenue_analytics': self.get_revenue_analytics(),
                'trend_analysis': self.get_trend_analysis(),
                'performance_metrics': self.get_performance_metrics(),
                'allocation_breakdown': self.get_allocation_breakdown(),
                'top_performers': self.get_top_performers(),
                'monthly_trends': self.get_monthly_trends(),
                'generated_at': datetime.now().isoformat()
            }
            
            # Apply data masking based on user role
            if self.user.role == 'user':
                dashboard_data = self.apply_data_masking(dashboard_data)
            
            # Cache for 15 minutes
            redis_client.setex(cache_key, 900, json.dumps(dashboard_data, default=str))
            
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Error generating dashboard data: {str(e)}")
            return self.get_empty_dashboard_data()
    
    def get_summary_metrics(self) -> Dict[str, Any]:
        """Get high-level summary metrics"""
        try:
            # Base query with area filtering
            query = self.get_filtered_invoice_query()
            
            # Calculate metrics
            total_revenue = query.with_entities(func.sum(Invoice.amount)).scalar() or 0
            total_invoices = query.count()
            total_pharmacies = query.with_entities(func.count(func.distinct(Invoice.pharmacy_id))).scalar() or 0
            
            # Average order value
            avg_order_value = float(total_revenue / total_invoices) if total_invoices > 0 else 0
            
            # Growth calculations (vs previous period)
            previous_period_revenue = self.get_previous_period_revenue()
            growth_rate = self.calculate_growth_rate(float(total_revenue), previous_period_revenue)
            
            return {
                'total_revenue': float(total_revenue),
                'total_invoices': total_invoices,
                'total_pharmacies': total_pharmacies,
                'average_order_value': avg_order_value,
                'growth_rate': growth_rate,
                'period': 'Current Month'
            }
            
        except Exception as e:
            logger.error(f"Error calculating summary metrics: {str(e)}")
            return {
                'total_revenue': 0.0,
                'total_invoices': 0,
                'total_pharmacies': 0,
                'average_order_value': 0.0,
                'growth_rate': 0.0,
                'period': 'Current Month'
            }
    
    def get_revenue_analytics(self) -> Dict[str, Any]:
        """Get detailed revenue analytics"""
        try:
            # Revenue by pharmacy
            pharmacy_revenue = self.get_revenue_by_pharmacy()
            
            # Revenue by doctor
            doctor_revenue = self.get_revenue_by_doctor()
            
            # Revenue by rep
            rep_revenue = self.get_revenue_by_rep()
            
            # Revenue by HQ
            hq_revenue = self.get_revenue_by_hq()
            
            # Revenue by area
            area_revenue = self.get_revenue_by_area()
            
            # Revenue by product
            product_revenue = self.get_revenue_by_product()
            
            return {
                'pharmacy_revenue': pharmacy_revenue,
                'doctor_revenue': doctor_revenue,
                'rep_revenue': rep_revenue,
                'hq_revenue': hq_revenue,
                'area_revenue': area_revenue,
                'product_revenue': product_revenue
            }
            
        except Exception as e:
            logger.error(f"Error calculating revenue analytics: {str(e)}")
            return {
                'pharmacy_revenue': [],
                'doctor_revenue': [],
                'rep_revenue': [],
                'hq_revenue': [],
                'area_revenue': [],
                'product_revenue': []
            }
    
    def get_revenue_by_pharmacy(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get revenue breakdown by pharmacy"""
        try:
            query = (
                self.get_filtered_invoice_query()
                .with_entities(
                    Invoice.pharmacy_name,
                    Invoice.pharmacy_id,
                    func.sum(Invoice.amount).label('total_revenue'),
                    func.count(Invoice.id).label('total_orders'),
                    func.sum(Invoice.quantity).label('total_quantity')
                )
                .group_by(Invoice.pharmacy_name, Invoice.pharmacy_id)
                .order_by(desc('total_revenue'))
                .limit(limit)
            )
            
            results = query.all()
            
            return [
                {
                    'pharmacy_name': result.pharmacy_name,
                    'pharmacy_id': result.pharmacy_id,
                    'total_revenue': float(result.total_revenue),
                    'total_orders': result.total_orders,
                    'total_quantity': result.total_quantity,
                    'avg_order_value': float(result.total_revenue / result.total_orders) if result.total_orders > 0 else 0
                }
                for result in results
            ]
            
        except Exception as e:
            logger.error(f"Error getting pharmacy revenue: {str(e)}")
            return []
    
    def get_revenue_by_doctor(self, limit: int = 15) -> List[Dict[str, Any]]:
        """Get revenue breakdown by doctor"""
        try:
            query = (
                self.db.query(Invoice, MasterMapping)
                .join(MasterMapping, Invoice.pharmacy_id == MasterMapping.pharmacy_id)
                .filter(self.get_area_filter(MasterMapping))
                .with_entities(
                    MasterMapping.doctor_names,
                    MasterMapping.doctor_id,
                    func.sum(Invoice.amount).label('total_revenue'),
                    func.count(Invoice.id).label('total_orders'),
                    func.count(func.distinct(Invoice.pharmacy_id)).label('pharmacy_count')
                )
                .group_by(MasterMapping.doctor_names, MasterMapping.doctor_id)
                .order_by(desc('total_revenue'))
                .limit(limit)
            )
            
            results = query.all()
            
            return [
                {
                    'doctor_name': result.doctor_names,
                    'doctor_id': result.doctor_id,
                    'total_revenue': float(result.total_revenue),
                    'total_orders': result.total_orders,
                    'pharmacy_count': result.pharmacy_count,
                    'avg_revenue_per_pharmacy': float(result.total_revenue / result.pharmacy_count) if result.pharmacy_count > 0 else 0
                }
                for result in results
            ]
            
        except Exception as e:
            logger.error(f"Error getting doctor revenue: {str(e)}")
            return []
    
    def get_revenue_by_rep(self, limit: int = 15) -> List[Dict[str, Any]]:
        """Get revenue breakdown by sales rep"""
        try:
            query = (
                self.db.query(Invoice, MasterMapping)
                .join(MasterMapping, Invoice.pharmacy_id == MasterMapping.pharmacy_id)
                .filter(self.get_area_filter(MasterMapping))
                .with_entities(
                    MasterMapping.rep_names,
                    func.sum(Invoice.amount).label('total_revenue'),
                    func.count(Invoice.id).label('total_orders'),
                    func.count(func.distinct(Invoice.pharmacy_id)).label('pharmacy_count'),
                    func.count(func.distinct(MasterMapping.doctor_id)).label('doctor_count')
                )
                .group_by(MasterMapping.rep_names)
                .order_by(desc('total_revenue'))
                .limit(limit)
            )
            
            results = query.all()
            
            return [
                {
                    'rep_name': result.rep_names,
                    'total_revenue': float(result.total_revenue),
                    'total_orders': result.total_orders,
                    'pharmacy_count': result.pharmacy_count,
                    'doctor_count': result.doctor_count,
                    'avg_revenue_per_pharmacy': float(result.total_revenue / result.pharmacy_count) if result.pharmacy_count > 0 else 0
                }
                for result in results
            ]
            
        except Exception as e:
            logger.error(f"Error getting rep revenue: {str(e)}")
            return []
    
    def get_revenue_by_hq(self) -> List[Dict[str, Any]]:
        """Get revenue breakdown by HQ"""
        try:
            query = (
                self.db.query(Invoice, MasterMapping)
                .join(MasterMapping, Invoice.pharmacy_id == MasterMapping.pharmacy_id)
                .filter(self.get_area_filter(MasterMapping))
                .with_entities(
                    MasterMapping.hq,
                    func.sum(Invoice.amount).label('total_revenue'),
                    func.count(Invoice.id).label('total_orders'),
                    func.count(func.distinct(Invoice.pharmacy_id)).label('pharmacy_count')
                )
                .group_by(MasterMapping.hq)
                .order_by(desc('total_revenue'))
            )
            
            results = query.all()
            
            return [
                {
                    'hq': result.hq,
                    'total_revenue': float(result.total_revenue),
                    'total_orders': result.total_orders,
                    'pharmacy_count': result.pharmacy_count,
                    'percentage': 0  # Will be calculated on frontend
                }
                for result in results
            ]
            
        except Exception as e:
            logger.error(f"Error getting HQ revenue: {str(e)}")
            return []
    
    def get_revenue_by_area(self) -> List[Dict[str, Any]]:
        """Get revenue breakdown by area"""
        try:
            query = (
                self.db.query(Invoice, MasterMapping)
                .join(MasterMapping, Invoice.pharmacy_id == MasterMapping.pharmacy_id)
                .filter(self.get_area_filter(MasterMapping))
                .with_entities(
                    MasterMapping.area,
                    func.sum(Invoice.amount).label('total_revenue'),
                    func.count(Invoice.id).label('total_orders'),
                    func.count(func.distinct(Invoice.pharmacy_id)).label('pharmacy_count')
                )
                .group_by(MasterMapping.area)
                .order_by(desc('total_revenue'))
            )
            
            results = query.all()
            
            return [
                {
                    'area': result.area,
                    'total_revenue': float(result.total_revenue),
                    'total_orders': result.total_orders,
                    'pharmacy_count': result.pharmacy_count,
                    'percentage': 0  # Will be calculated on frontend
                }
                for result in results
            ]
            
        except Exception as e:
            logger.error(f"Error getting area revenue: {str(e)}")
            return []
    
    def get_revenue_by_product(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get revenue breakdown by product"""
        try:
            query = (
                self.get_filtered_invoice_query()
                .with_entities(
                    Invoice.product,
                    func.sum(Invoice.amount).label('total_revenue'),
                    func.sum(Invoice.quantity).label('total_quantity'),
                    func.count(Invoice.id).label('total_orders')
                )
                .group_by(Invoice.product)
                .order_by(desc('total_revenue'))
                .limit(limit)
            )
            
            results = query.all()
            
            return [
                {
                    'product_name': result.product,
                    'total_revenue': float(result.total_revenue),
                    'total_quantity': result.total_quantity,
                    'total_orders': result.total_orders,
                    'avg_price': float(result.total_revenue / result.total_quantity) if result.total_quantity > 0 else 0
                }
                for result in results
            ]
            
        except Exception as e:
            logger.error(f"Error getting product revenue: {str(e)}")
            return []
    
    def get_monthly_trends(self, months: int = 12) -> List[Dict[str, Any]]:
        """Get monthly revenue trends"""
        try:
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=months * 30)
            
            query = (
                self.get_filtered_invoice_query()
                .filter(Invoice.invoice_date >= start_date)
                .with_entities(
                    extract('year', Invoice.invoice_date).label('year'),
                    extract('month', Invoice.invoice_date).label('month'),
                    func.sum(Invoice.amount).label('total_revenue'),
                    func.count(Invoice.id).label('total_orders'),
                    func.sum(Invoice.quantity).label('total_quantity')
                )
                .group_by('year', 'month')
                .order_by('year', 'month')
            )
            
            results = query.all()
            
            monthly_data = []
            for result in results:
                month_name = datetime(int(result.year), int(result.month), 1).strftime('%B %Y')
                monthly_data.append({
                    'month': month_name,
                    'year': int(result.year),
                    'month_num': int(result.month),
                    'total_revenue': float(result.total_revenue),
                    'total_orders': result.total_orders,
                    'total_quantity': result.total_quantity,
                    'avg_order_value': float(result.total_revenue / result.total_orders) if result.total_orders > 0 else 0
                })
            
            return monthly_data
            
        except Exception as e:
            logger.error(f"Error getting monthly trends: {str(e)}")
            return []
    
    def get_trend_analysis(self) -> Dict[str, Any]:
        """Get trend analysis with growth rates and forecasting"""
        try:
            monthly_data = self.get_monthly_trends(6)  # Last 6 months
            
            if len(monthly_data) < 2:
                return {'growth_trends': [], 'forecast': None}
            
            # Calculate month-over-month growth
            growth_trends = []
            for i in range(1, len(monthly_data)):
                current = monthly_data[i]
                previous = monthly_data[i-1]
                
                growth_rate = self.calculate_growth_rate(
                    current['total_revenue'], 
                    previous['total_revenue']
                )
                
                growth_trends.append({
                    'month': current['month'],
                    'revenue': current['total_revenue'],
                    'growth_rate': growth_rate,
                    'orders_growth': self.calculate_growth_rate(
                        current['total_orders'], 
                        previous['total_orders']
                    )
                })
            
            # Simple forecast for next month
            if len(monthly_data) >= 3:
                recent_growth_rates = [trend['growth_rate'] for trend in growth_trends[-3:]]
                avg_growth_rate = sum(recent_growth_rates) / len(recent_growth_rates)
                
                last_month_revenue = monthly_data[-1]['total_revenue']
                forecasted_revenue = last_month_revenue * (1 + avg_growth_rate / 100)
                
                forecast = {
                    'next_month_revenue': forecasted_revenue,
                    'confidence': 'Medium' if abs(avg_growth_rate) < 20 else 'Low',
                    'based_on_months': len(recent_growth_rates)
                }
            else:
                forecast = None
            
            return {
                'growth_trends': growth_trends,
                'forecast': forecast
            }
            
        except Exception as e:
            logger.error(f"Error calculating trend analysis: {str(e)}")
            return {'growth_trends': [], 'forecast': None}
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics and KPIs"""
        try:
            query = self.get_filtered_invoice_query()
            
            # Top performing pharmacy
            top_pharmacy = (
                query.with_entities(
                    Invoice.pharmacy_name,
                    func.sum(Invoice.amount).label('total_revenue')
                )
                .group_by(Invoice.pharmacy_name)
                .order_by(desc('total_revenue'))
                .first()
            )
            
            # Average metrics
            avg_metrics = query.with_entities(
                func.avg(Invoice.amount).label('avg_order_value'),
                func.avg(Invoice.quantity).label('avg_quantity')
            ).first()
            
            # Distribution metrics
            revenue_distribution = self.calculate_revenue_distribution()
            
            return {
                'top_pharmacy': {
                    'name': top_pharmacy.pharmacy_name if top_pharmacy else 'N/A',
                    'revenue': float(top_pharmacy.total_revenue) if top_pharmacy else 0
                },
                'averages': {
                    'order_value': float(avg_metrics.avg_order_value) if avg_metrics.avg_order_value else 0,
                    'quantity': float(avg_metrics.avg_quantity) if avg_metrics.avg_quantity else 0
                },
                'distribution': revenue_distribution
            }
            
        except Exception as e:
            logger.error(f"Error calculating performance metrics: {str(e)}")
            return {
                'top_pharmacy': {'name': 'N/A', 'revenue': 0},
                'averages': {'order_value': 0, 'quantity': 0},
                'distribution': {}
            }
    
    def get_allocation_breakdown(self) -> Dict[str, Any]:
        """Get revenue allocation breakdown"""
        try:
            # This would typically involve complex allocation logic
            # For now, we'll provide a simplified version
            
            total_revenue = self.get_filtered_invoice_query().with_entities(func.sum(Invoice.amount)).scalar() or 0
            
            # Example allocation percentages (configurable in production)
            doctor_allocation = float(total_revenue) * 0.60  # 60% to doctors
            rep_allocation = float(total_revenue) * 0.40     # 40% to reps
            
            return {
                'total_revenue': float(total_revenue),
                'doctor_allocation': doctor_allocation,
                'rep_allocation': rep_allocation,
                'allocation_percentages': {
                    'doctors': 60,
                    'reps': 40
                }
            }
            
        except Exception as e:
            logger.error(f"Error calculating allocation breakdown: {str(e)}")
            return {
                'total_revenue': 0,
                'doctor_allocation': 0,
                'rep_allocation': 0,
                'allocation_percentages': {'doctors': 0, 'reps': 0}
            }
    
    def get_top_performers(self) -> Dict[str, Any]:
        """Get top performers across different categories"""
        try:
            return {
                'top_pharmacies': self.get_revenue_by_pharmacy(5),
                'top_doctors': self.get_revenue_by_doctor(5),
                'top_reps': self.get_revenue_by_rep(5),
                'top_products': self.get_revenue_by_product(5)
            }
            
        except Exception as e:
            logger.error(f"Error getting top performers: {str(e)}")
            return {
                'top_pharmacies': [],
                'top_doctors': [],
                'top_reps': [],
                'top_products': []
            }
    
    def get_filtered_invoice_query(self):
        """Get base invoice query with area filtering"""
        query = self.db.query(Invoice)
        
        if self.user.role != 'super_admin' and self.user.area:
            # Join with master mapping to filter by area
            query = (
                query.join(MasterMapping, Invoice.pharmacy_id == MasterMapping.pharmacy_id)
                .filter(MasterMapping.area == self.user.area)
            )
        
        return query
    
    def get_area_filter(self, model):
        """Get area filter condition"""
        if self.user.role != 'super_admin' and self.user.area:
            return model.area == self.user.area
        return True  # No filter for super admin
    
    def get_previous_period_revenue(self) -> float:
        """Get previous period revenue for growth calculation"""
        try:
            # Get revenue from previous month
            current_month = datetime.now().replace(day=1)
            previous_month = (current_month - timedelta(days=1)).replace(day=1)
            previous_month_end = current_month - timedelta(days=1)
            
            query = (
                self.get_filtered_invoice_query()
                .filter(Invoice.invoice_date >= previous_month)
                .filter(Invoice.invoice_date <= previous_month_end)
                .with_entities(func.sum(Invoice.amount))
            )
            
            return float(query.scalar() or 0)
            
        except Exception as e:
            logger.error(f"Error getting previous period revenue: {str(e)}")
            return 0.0
    
    def calculate_growth_rate(self, current: float, previous: float) -> float:
        """Calculate growth rate percentage"""
        if previous == 0:
            return 100.0 if current > 0 else 0.0
        return ((current - previous) / previous) * 100
    
    def calculate_revenue_distribution(self) -> Dict[str, Any]:
        """Calculate revenue distribution statistics"""
        try:
            revenues = [
                float(result.amount) 
                for result in self.get_filtered_invoice_query().with_entities(Invoice.amount).all()
            ]
            
            if not revenues:
                return {}
            
            revenues_array = np.array(revenues)
            
            return {
                'min': float(np.min(revenues_array)),
                'max': float(np.max(revenues_array)),
                'mean': float(np.mean(revenues_array)),
                'median': float(np.median(revenues_array)),
                'std_dev': float(np.std(revenues_array)),
                'percentiles': {
                    '25th': float(np.percentile(revenues_array, 25)),
                    '75th': float(np.percentile(revenues_array, 75)),
                    '90th': float(np.percentile(revenues_array, 90))
                }
            }
            
        except Exception as e:
            logger.error(f"Error calculating revenue distribution: {str(e)}")
            return {}
    
    def apply_data_masking(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply data masking for user role"""
        try:
            # Mask sensitive revenue data for regular users
            if 'summary_metrics' in data:
                data['summary_metrics']['total_revenue'] = "***"
            
            # Mask individual revenue amounts in analytics
            for category in ['pharmacy_revenue', 'doctor_revenue', 'rep_revenue']:
                if category in data.get('revenue_analytics', {}):
                    for item in data['revenue_analytics'][category]:
                        if 'total_revenue' in item:
                            item['total_revenue'] = "***"
            
            # Mask allocation breakdown
            if 'allocation_breakdown' in data:
                data['allocation_breakdown']['doctor_allocation'] = "***"
                data['allocation_breakdown']['rep_allocation'] = "***"
            
            return data
            
        except Exception as e:
            logger.error(f"Error applying data masking: {str(e)}")
            return data
    
    def get_empty_dashboard_data(self) -> Dict[str, Any]:
        """Return empty dashboard data structure"""
        return {
            'summary_metrics': {
                'total_revenue': 0.0,
                'total_invoices': 0,
                'total_pharmacies': 0,
                'average_order_value': 0.0,
                'growth_rate': 0.0,
                'period': 'Current Month'
            },
            'revenue_analytics': {
                'pharmacy_revenue': [],
                'doctor_revenue': [],
                'rep_revenue': [],
                'hq_revenue': [],
                'area_revenue': [],
                'product_revenue': []
            },
            'trend_analysis': {'growth_trends': [], 'forecast': None},
            'performance_metrics': {
                'top_pharmacy': {'name': 'N/A', 'revenue': 0},
                'averages': {'order_value': 0, 'quantity': 0},
                'distribution': {}
            },
            'allocation_breakdown': {
                'total_revenue': 0,
                'doctor_allocation': 0,
                'rep_allocation': 0,
                'allocation_percentages': {'doctors': 0, 'reps': 0}
            },
            'top_performers': {
                'top_pharmacies': [],
                'top_doctors': [],
                'top_reps': [],
                'top_products': []
            },
            'monthly_trends': [],
            'generated_at': datetime.now().isoformat()
        }
