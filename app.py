from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import datetime
import json
import secrets
from cip_engine_roi import CIPEngineROI

app = Flask(__name__)
CORS(app)

# Database connection
def get_db():
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        return psycopg2.connect(database_url)
    else:
        return psycopg2.connect(
            host=os.getenv('DB_HOST'),
            database=os.getenv('DB_NAME', 'railway'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD'),
            port=os.getenv('DB_PORT', 5432)
        )

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'service': 'tool5-roi-projector'})

@app.route('/api/calculate', methods=['POST'])
def calculate_roi():
    """
    Receives workflow details, calculates ROI projection
    Conservative estimates to build trust
    """
    data = request.json
    
    # Extract data
    company_name = data.get('company_name', 'Anonymous')
    industry = data.get('industry')
    email = data.get('email')
    process_name = data.get('process_name')
    hours_per_week = int(data.get('hours_per_week', 0))
    people_count = int(data.get('people_count', 1))
    hourly_cost = float(data.get('hourly_cost', 0))
    current_tools_cost = float(data.get('current_tools_cost', 0))
    timeline_expectation = data.get('timeline_expectation')
    
    if not process_name or hours_per_week == 0 or hourly_cost == 0:
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Calculate current annual cost
    weekly_cost = hours_per_week * hourly_cost * people_count
    annual_labor_cost = weekly_cost * 52
    annual_tools_cost = current_tools_cost * 12
    annual_cost_current = annual_labor_cost + annual_tools_cost
    
    # AI automation assumptions (CONSERVATIVE)
    # Assume AI can handle 60-70% of work (not 100%)
    # Humans still needed for edge cases, oversight
    automation_percentage = 0.65  # 65% automation (conservative)
    
    # AI costs (realistic)
    # Implementation: $8K-18K depending on complexity
    # Ongoing: API costs + maintenance
    
    # Complexity scoring (determines implementation cost)
    complexity_score = 0
    if hours_per_week > 40:
        complexity_score += 2  # High volume
    if people_count > 5:
        complexity_score += 2  # Multiple stakeholders
    if 'data' in process_name.lower() or 'analysis' in process_name.lower():
        complexity_score += 1  # Data complexity
    if 'customer' in process_name.lower() or 'support' in process_name.lower():
        complexity_score += 1  # Customer-facing
    
    # Implementation cost (conservative)
    if complexity_score <= 2:
        implementation_cost = 8000  # Simple automation
    elif complexity_score <= 4:
        implementation_cost = 12000  # Medium complexity
    else:
        implementation_cost = 18000  # Complex system
    
    # Ongoing AI costs (API + maintenance)
    monthly_ai_cost = 0
    if hours_per_week < 20:
        monthly_ai_cost = 200  # Light usage
    elif hours_per_week < 40:
        monthly_ai_cost = 400  # Medium usage
    else:
        monthly_ai_cost = 800  # Heavy usage
    
    annual_ai_cost = monthly_ai_cost * 12
    
    # Calculate savings
    # Labor savings = automated hours * cost
    hours_automated_weekly = hours_per_week * automation_percentage
    annual_labor_savings = hours_automated_weekly * hourly_cost * people_count * 52
    
    # Total annual cost with AI
    annual_cost_with_ai = annual_ai_cost
    
    # Net annual savings
    annual_savings = annual_cost_current - annual_cost_with_ai
    
    # ROI calculation
    roi_percentage = ((annual_savings - implementation_cost) / implementation_cost) * 100
    
    # Break-even calculation (minimum 1 month, rounded)
    if annual_savings > 0:
        breakeven_months = max(1, round((implementation_cost / annual_savings) * 12))
    else:
        breakeven_months = 999
    
    # Risk assessment
    if automation_percentage > 0.8:
        risk_level = "High"  # Over-optimistic automation
    elif breakeven_months > 18:
        risk_level = "High"  # Too long to ROI
    elif complexity_score > 5:
        risk_level = "Medium"  # Complex implementation
    elif annual_savings < implementation_cost:
        risk_level = "High"  # Doesn't pay for itself in year 1
    else:
        risk_level = "Low"
    
    # Generate recommendation
    if roi_percentage > 200 and breakeven_months <= 12:
        recommendation = f"Strong ROI case. This automation pays for itself in {breakeven_months} months and delivers ${annual_savings:,.0f} annual savings. Let's build it."
        next_steps = [
            "Schedule discovery call to validate assumptions",
            "Review process documentation",
            "Create detailed technical architecture",
            "Start with pilot (1-2 workflows) before full rollout"
        ]
    elif roi_percentage > 100 and breakeven_months <= 18:
        recommendation = f"Good ROI potential. {breakeven_months}-month break-even is reasonable. Worth exploring if process is well-documented and stable."
        next_steps = [
            "Document current process in detail",
            "Identify edge cases AI will struggle with",
            "Consider starting with subset of work",
            "Plan for human oversight layer"
        ]
    elif roi_percentage > 50:
        recommendation = f"Moderate ROI. ${annual_savings:,.0f} annual savings is meaningful but {breakeven_months}-month break-even requires careful execution."
        next_steps = [
            "Start with smallest viable automation",
            "Prove ROI with pilot before full implementation",
            "Consider process optimization first (cheaper than AI)",
            "Ensure team is ready for change"
        ]
    else:
        recommendation = f"ROI concerns. With {breakeven_months}-month break-even and {risk_level.lower()} risk, this may not be the best automation target right now."
        next_steps = [
            "Look for higher-ROI processes first",
            "Consider process improvement before automation",
            "Revisit when process volume increases",
            "Explore simpler no-code tools first"
        ]
    
    # Industry-specific adjustments
    industry_note = ""
    if industry:
        if industry.lower() in ['healthcare', 'finance', 'legal']:
            industry_note = f"Note: {industry} has compliance requirements that may add 20-30% to implementation cost and timeline."
        elif industry.lower() in ['logistics', 'manufacturing']:
            industry_note = f"Note: {industry} automation typically sees 70-80% efficiency gains - your projection may be conservative."
        elif industry.lower() in ['retail', 'ecommerce']:
            industry_note = f"Note: {industry} AI automation has proven ROI - fast implementation typical."
    
    # Store in database
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    cur.execute("""
        INSERT INTO roi_projections (
            company_name, industry, email, process_name,
            hours_per_week, people_count, hourly_cost, current_tools_cost,
            timeline_expectation, annual_cost_current, annual_cost_with_ai,
            annual_savings, implementation_cost, breakeven_months,
            roi_percentage, risk_level, recommendation, created_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
        RETURNING id
    """, (
        company_name, industry, email, process_name,
        hours_per_week, people_count, hourly_cost, current_tools_cost,
        timeline_expectation, annual_cost_current, annual_cost_with_ai,
        annual_savings, implementation_cost, breakeven_months,
        roi_percentage, risk_level, recommendation
    ))
    
    projection_id = cur.fetchone()['id']
    
    # Generate session for Nuru handoff
    session_id = secrets.token_urlsafe(32)
    
    user_context = {
        'company_name': company_name,
        'industry': industry,
        'process_name': process_name,
        'annual_savings': float(annual_savings),
        'roi_percentage': float(roi_percentage),
        'breakeven_months': breakeven_months,
        'implementation_cost': float(implementation_cost),
        'risk_level': risk_level,
        'recommendation': recommendation,
        'projection_completed_at': datetime.now().isoformat()
    }
    
    cur.execute("""
        INSERT INTO sessions (session_id, projection_id, user_context)
        VALUES (%s, %s, %s)
    """, (session_id, projection_id, json.dumps(user_context)))
    
    conn.commit()
    cur.close()
    conn.close()
    
    # CIP: Log patterns
    cip = CIPEngineROI()
    cip.log_patterns({
        'industry': industry,
        'process_name': process_name,
        'annual_savings': annual_savings,
        'roi_percentage': roi_percentage
    })
    cip.close()
    
    return jsonify({
        'projection_id': projection_id,
        'session_id': session_id,
        'current_state': {
            'annual_labor_cost': round(annual_labor_cost, 2),
            'annual_tools_cost': round(annual_tools_cost, 2),
            'total_annual_cost': round(annual_cost_current, 2),
            'hours_per_week': hours_per_week,
            'people_count': people_count
        },
        'with_ai': {
            'annual_ai_cost': round(annual_ai_cost, 2),
            'implementation_cost': round(implementation_cost, 2),
            'automation_percentage': automation_percentage * 100,
            'hours_automated_weekly': round(hours_automated_weekly, 1)
        },
        'savings': {
            'annual_savings': round(annual_savings, 2),
            'monthly_savings': round(annual_savings / 12, 2),
            'breakeven_months': breakeven_months,
            'roi_percentage': round(roi_percentage, 1),
            'three_year_savings': round((annual_savings * 3) - implementation_cost, 2)
        },
        'assessment': {
            'risk_level': risk_level,
            'complexity_score': complexity_score,
            'recommendation': recommendation,
            'next_steps': next_steps,
            'industry_note': industry_note
        }
    })

@app.route('/api/session/<session_id>', methods=['GET'])
def get_session(session_id):
    """API endpoint for Nuru to fetch projection context"""
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    cur.execute("""
        SELECT user_context, projection_id, created_at
        FROM sessions
        WHERE session_id = %s AND expires_at > NOW()
    """, (session_id,))
    
    session = cur.fetchone()
    
    if not session:
        cur.close()
        conn.close()
        return jsonify({'error': 'Session not found or expired'}), 404
    
    # Update access tracking
    cur.execute("""
        UPDATE sessions
        SET accessed_count = accessed_count + 1,
            last_accessed = NOW()
        WHERE session_id = %s
    """, (session_id,))
    
    conn.commit()
    cur.close()
    conn.close()
    
    return jsonify(session['user_context'])

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """
    Get aggregate statistics
    """
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # Total projections
    cur.execute("SELECT COUNT(*) as total FROM roi_projections")
    total = cur.fetchone()['total']
    
    # Average savings
    cur.execute("SELECT AVG(annual_savings) as avg_savings, AVG(roi_percentage) as avg_roi FROM roi_projections")
    averages = cur.fetchone()
    
    # Top industries by savings
    cur.execute("""
        SELECT industry, AVG(annual_savings) as avg_savings, COUNT(*) as count
        FROM roi_projections
        WHERE industry IS NOT NULL
        GROUP BY industry
        ORDER BY avg_savings DESC
        LIMIT 5
    """)
    top_industries = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return jsonify({
        'total_projections': int(total),
        'avg_annual_savings': float(averages['avg_savings']) if averages['avg_savings'] else 0,
        'avg_roi_percentage': float(averages['avg_roi']) if averages['avg_roi'] else 0,
        'top_industries': [
            {
                'industry': row['industry'],
                'avg_savings': float(row['avg_savings']),
                'count': int(row['count'])
            }
            for row in top_industries
        ]
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 8080)))