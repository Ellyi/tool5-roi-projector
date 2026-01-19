"""
CIP Engine for ROI Projector
Learns from actual vs projected ROI to improve predictions
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import os
import json
from datetime import datetime

class CIPEngineROI:
    """
    Learning system that:
    1. Logs ROI projection patterns
    2. Analyzes trends across projections
    3. Generates intelligence about which processes have best ROI
    4. Identifies market opportunities
    """
    
    def __init__(self):
        self.conn = self._get_connection()
    
    def _get_connection(self):
        database_url = os.getenv('DATABASE_URL')
        if database_url:
            return psycopg2.connect(database_url, cursor_factory=RealDictCursor)
        else:
            return psycopg2.connect(
                host=os.getenv('DB_HOST'),
                database=os.getenv('DB_NAME', 'railway'),
                user=os.getenv('DB_USER', 'postgres'),
                password=os.getenv('DB_PASSWORD'),
                port=os.getenv('DB_PORT', 5432),
                cursor_factory=RealDictCursor
            )
    
    def log_patterns(self, projection_data):
        """
        Called after each ROI projection
        Logs patterns for learning
        """
        cur = self.conn.cursor()
        
        # Log industry ROI patterns
        industry = projection_data.get('industry')
        annual_savings = projection_data.get('annual_savings')
        roi_percentage = projection_data.get('roi_percentage')
        
        if industry and annual_savings and roi_percentage:
            cur.execute("""
                INSERT INTO roi_patterns (pattern_type, pattern_data, frequency, avg_savings, avg_roi, last_updated)
                VALUES ('industry_roi', %s, 1, %s, %s, NOW())
                ON CONFLICT (pattern_type, pattern_data)
                DO UPDATE SET 
                    frequency = roi_patterns.frequency + 1,
                    avg_savings = (roi_patterns.avg_savings * roi_patterns.frequency + EXCLUDED.avg_savings) / (roi_patterns.frequency + 1),
                    avg_roi = (roi_patterns.avg_roi * roi_patterns.frequency + EXCLUDED.avg_roi) / (roi_patterns.frequency + 1),
                    last_updated = NOW()
            """, (json.dumps({'industry': industry}), annual_savings, roi_percentage))
        
        # Log process type patterns
        process_name = projection_data.get('process_name')
        if process_name and annual_savings:
            cur.execute("""
                INSERT INTO roi_patterns (pattern_type, pattern_data, frequency, avg_savings, avg_roi, last_updated)
                VALUES ('process_savings', %s, 1, %s, %s, NOW())
                ON CONFLICT (pattern_type, pattern_data)
                DO UPDATE SET 
                    frequency = roi_patterns.frequency + 1,
                    avg_savings = (roi_patterns.avg_savings * roi_patterns.frequency + EXCLUDED.avg_savings) / (roi_patterns.frequency + 1),
                    avg_roi = (roi_patterns.avg_roi * roi_patterns.frequency + EXCLUDED.avg_roi) / (roi_patterns.frequency + 1),
                    last_updated = NOW()
            """, (json.dumps({'process': process_name}), annual_savings, roi_percentage))
        
        # Log high-value opportunities (>$50K savings)
        if annual_savings and annual_savings > 50000:
            cur.execute("""
                INSERT INTO roi_patterns (pattern_type, pattern_data, frequency, avg_savings, avg_roi, last_updated)
                VALUES ('high_value', %s, 1, %s, %s, NOW())
                ON CONFLICT (pattern_type, pattern_data)
                DO UPDATE SET 
                    frequency = roi_patterns.frequency + 1,
                    avg_savings = (roi_patterns.avg_savings * roi_patterns.frequency + EXCLUDED.avg_savings) / (roi_patterns.frequency + 1),
                    avg_roi = (roi_patterns.avg_roi * roi_patterns.frequency + EXCLUDED.avg_roi) / (roi_patterns.frequency + 1),
                    last_updated = NOW()
            """, (json.dumps({'type': 'high_value', 'threshold': 50000}), annual_savings, roi_percentage))
        
        self.conn.commit()
        cur.close()
        
        # Check if we should run analysis (every 10 projections)
        self._check_analysis_trigger()
    
    def _check_analysis_trigger(self):
        """
        Runs pattern analysis every 10 projections
        """
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) as count FROM roi_projections")
        count = cur.fetchone()['count']
        cur.close()
        
        if count % 10 == 0:
            self.analyze_patterns()
    
    def analyze_patterns(self):
        """
        Analyzes accumulated ROI data
        Generates insights about best opportunities
        """
        cur = self.conn.cursor()
        
        # Find processes with best ROI
        cur.execute("""
            SELECT 
                process_name,
                COUNT(*) as frequency,
                AVG(annual_savings) as avg_savings,
                AVG(roi_percentage) as avg_roi
            FROM roi_projections
            GROUP BY process_name
            HAVING COUNT(*) >= 3
            ORDER BY avg_roi DESC
            LIMIT 5
        """)
        top_processes = cur.fetchall()
        
        # Find industries with highest savings potential
        cur.execute("""
            SELECT 
                industry,
                AVG(annual_savings) as avg_savings,
                AVG(roi_percentage) as avg_roi,
                COUNT(*) as count
            FROM roi_projections
            WHERE industry IS NOT NULL
            GROUP BY industry
            HAVING COUNT(*) >= 3
            ORDER BY avg_savings DESC
            LIMIT 5
        """)
        top_industries = cur.fetchall()
        
        # Generate insights
        if top_processes:
            best_process = top_processes[0]
            insight = f"Best ROI process: {best_process['process_name']} (avg {best_process['avg_roi']:.1f}% ROI, ${best_process['avg_savings']:,.0f} annual savings, {best_process['frequency']} cases)"
            
            cur.execute("""
                INSERT INTO roi_insights (
                    insight_type, insight_text, confidence, supporting_data, generated_at
                ) VALUES (%s, %s, %s, %s, NOW())
            """, (
                'best_roi_process',
                insight,
                0.95,
                json.dumps({
                    'process': best_process['process_name'],
                    'avg_roi': float(best_process['avg_roi']),
                    'avg_savings': float(best_process['avg_savings']),
                    'frequency': int(best_process['frequency'])
                })
            ))
        
        if top_industries:
            best_industry = top_industries[0]
            insight = f"Highest savings industry: {best_industry['industry']} (avg ${best_industry['avg_savings']:,.0f} annual savings, {best_industry['avg_roi']:.1f}% ROI, {best_industry['count']} cases)"
            
            cur.execute("""
                INSERT INTO roi_insights (
                    insight_type, insight_text, confidence, supporting_data, generated_at
                ) VALUES (%s, %s, %s, %s, NOW())
            """, (
                'best_savings_industry',
                insight,
                0.90,
                json.dumps({
                    'industry': best_industry['industry'],
                    'avg_savings': float(best_industry['avg_savings']),
                    'avg_roi': float(best_industry['avg_roi']),
                    'sample_size': int(best_industry['count'])
                })
            ))
        
        self.conn.commit()
        cur.close()
    
    def generate_monthly_report(self):
        """
        Generates comprehensive intelligence report
        Shows what we learned from all projections
        """
        cur = self.conn.cursor()
        
        # Total projections
        cur.execute("SELECT COUNT(*) as total FROM roi_projections")
        total_projections = cur.fetchone()['total']
        
        # Average savings
        cur.execute("SELECT AVG(annual_savings) as avg_savings, AVG(roi_percentage) as avg_roi FROM roi_projections")
        averages = cur.fetchone()
        avg_savings = float(averages['avg_savings']) if averages['avg_savings'] else 0
        avg_roi = float(averages['avg_roi']) if averages['avg_roi'] else 0
        
        # Top processes by ROI
        cur.execute("""
            SELECT 
                process_name,
                AVG(annual_savings) as avg_savings,
                AVG(roi_percentage) as avg_roi,
                COUNT(*) as frequency
            FROM roi_projections
            GROUP BY process_name
            ORDER BY avg_roi DESC
            LIMIT 10
        """)
        top_processes = cur.fetchall()
        
        # Market opportunities (high-frequency, high-ROI = templates to build)
        opportunities = []
        for process in top_processes[:3]:
            if process['frequency'] >= 5:
                opportunities.append({
                    'opportunity': f"Build {process['process_name']} AI template",
                    'market_size': int(process['frequency']),
                    'avg_savings': float(process['avg_savings']),
                    'avg_roi': float(process['avg_roi']),
                    'potential_revenue': int(process['frequency']) * 8000  # $8K per template sale
                })
        
        # Recent insights
        cur.execute("""
            SELECT insight_type, insight_text, confidence, supporting_data
            FROM roi_insights
            WHERE generated_at >= NOW() - INTERVAL '30 days'
            ORDER BY confidence DESC, generated_at DESC
            LIMIT 5
        """)
        recent_insights = cur.fetchall()
        
        cur.close()
        
        return {
            'period': 'Last 30 days',
            'total_projections': int(total_projections),
            'avg_annual_savings': avg_savings,
            'avg_roi_percentage': avg_roi,
            'top_processes': [
                {
                    'process': p['process_name'],
                    'frequency': int(p['frequency']),
                    'avg_savings': float(p['avg_savings']),
                    'avg_roi': float(p['avg_roi'])
                }
                for p in top_processes
            ],
            'market_opportunities': opportunities,
            'insights': [
                {
                    'type': i['insight_type'],
                    'text': i['insight_text'],
                    'confidence': float(i['confidence'])
                }
                for i in recent_insights
            ],
            'recommendations': self._generate_recommendations(opportunities)
        }
    
    def _generate_recommendations(self, opportunities):
        """
        Generates actionable recommendations based on patterns
        """
        recommendations = []
        
        if opportunities:
            top_opp = opportunities[0]
            recommendations.append(
                f"BUILD: {top_opp['opportunity']} - {top_opp['market_size']} companies need this (${top_opp['potential_revenue']:,} potential revenue)"
            )
        
        return recommendations
    
    def close(self):
        if self.conn:
            self.conn.close()