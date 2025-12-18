"""
Streamlit Frontend Dashboard for Fraud Detection System
"""
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os

# Configuration
BACKEND_URL = os.getenv('BACKEND_API_URL', 'http://backend:8000')

# Page configuration
st.set_page_config(
    page_title="Fraud Detection Dashboard",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    </style>
""", unsafe_allow_html=True)


def check_backend_health():
    """Check if backend is accessible"""
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False


def get_summary_stats(dt=None):
    """Get summary statistics"""
    try:
        params = {}
        if dt:
            params['dt'] = dt
        response = requests.get(f"{BACKEND_URL}/stats/summary", params=params, timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Error fetching summary: {e}")
        return None


def get_alerts(dt=None, severity_min=None, rule_code=None):
    """Get alerts with filters"""
    try:
        params = {'limit': 1000}
        if dt:
            params['dt'] = dt
        if severity_min:
            params['severity_min'] = severity_min
        if rule_code:
            params['rule_code'] = rule_code
        
        response = requests.get(f"{BACKEND_URL}/alerts", params=params, timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Error fetching alerts: {e}")
        return None


def get_top_merchants(dt, metric='tx_count', n=10):
    """Get top merchants by metric"""
    try:
        params = {'dt': dt, 'metric': metric, 'n': n}
        response = requests.get(f"{BACKEND_URL}/metrics/merchants/top", params=params, timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Error fetching top merchants: {e}")
        return None


def get_merchant_series(merchant_id, from_date, to_date):
    """Get time series for a merchant"""
    try:
        params = {'from': from_date, 'to': to_date}
        response = requests.get(f"{BACKEND_URL}/merchant/{merchant_id}/series", params=params, timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Error fetching merchant series: {e}")
        return None


def run_pipeline(dt):
    """Trigger pipeline execution"""
    try:
        params = {'dt': dt}
        response = requests.post(f"{BACKEND_URL}/pipeline/run", params=params, timeout=600)
        return response
    except Exception as e:
        st.error(f"Error running pipeline: {e}")
        return None


# Main dashboard
def main():
    # Header
    st.markdown('<div class="main-header">🔍 Fraud Detection Dashboard</div>', unsafe_allow_html=True)
    
    # Check backend health
    if not check_backend_health():
        st.error("⚠️ Backend API is not accessible. Please ensure services are running.")
        return
    
    # Sidebar
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Select Page", ["Overview", "Alerts", "Merchant Analytics", "Pipeline Control"])
    
    # Date selector (common)
    st.sidebar.markdown("---")
    st.sidebar.subheader("Date Selection")
    selected_date = st.sidebar.date_input(
        "Select Date",
        value=datetime.strptime("2025-12-18", "%Y-%m-%d"),
        min_value=datetime(2020, 1, 1),
        max_value=datetime.now()
    )
    date_str = selected_date.strftime("%Y-%m-%d")
    
    # Page routing
    if page == "Overview":
        show_overview(date_str)
    elif page == "Alerts":
        show_alerts_page(date_str)
    elif page == "Merchant Analytics":
        show_merchant_analytics(date_str)
    elif page == "Pipeline Control":
        show_pipeline_control(date_str)


def show_overview(date_str):
    """Overview page with key metrics"""
    st.header(f"Overview - {date_str}")
    
    # Get summary stats
    summary = get_summary_stats(date_str)
    
    if not summary:
        st.warning("No data available for this date.")
        return
    
    metrics = summary.get('metrics', {})
    alerts = summary.get('alerts', {})
    
    # Safe metric extraction
    total_merchants = metrics.get('total_merchants') or 0
    total_transactions = metrics.get('total_transactions') or 0
    total_amount = metrics.get('total_amount') or 0
    avg_decline_rate = metrics.get('avg_decline_rate') or 0
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Merchants",
            f"{int(total_merchants):,}"
        )
    
    with col2:
        st.metric(
            "Total Transactions",
            f"{int(total_transactions):,}"
        )
    
    with col3:
        st.metric(
            "Total Amount",
            f"${float(total_amount):,.2f}"
        )
    
    with col4:
        st.metric(
            "Avg Decline Rate",
            f"{float(avg_decline_rate)*100:.2f}%"
        )
    
    st.markdown("---")
    
    # Alerts summary
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Alert Summary")
        alert_data = {
            'Severity': ['High (3)', 'Medium (2)', 'Low (1)'],
            'Count': [
                alerts.get('high_severity', 0) or 0,
                alerts.get('medium_severity', 0) or 0,
                alerts.get('low_severity', 0) or 0
            ]
        }
        fig = px.bar(
            alert_data,
            x='Severity',
            y='Count',
            title=f"Alerts by Severity ({(alerts.get('total_alerts', 0) or 0)} total)",
            color='Count',
            color_continuous_scale='Reds'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Alert Rules Breakdown")
        rule_breakdown = summary.get('rule_breakdown', [])
        if rule_breakdown:
            df_rules = pd.DataFrame(rule_breakdown)
            fig = px.pie(
                df_rules,
                names='rule_code',
                values='count',
                title="Alerts by Rule Type"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No alerts for this date")


def show_alerts_page(date_str):
    """Alerts page with filters"""
    st.header(f"Alerts - {date_str}")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        severity_filter = st.selectbox(
            "Minimum Severity",
            options=[None, 1, 2, 3],
            format_func=lambda x: "All" if x is None else f"Level {x}+"
        )
    
    with col2:
        rule_filter = st.selectbox(
            "Rule Code",
            options=[None, "HIGH_AMOUNT", "BURST", "MULTI_COUNTRY", "HIGH_DECLINE"],
            format_func=lambda x: "All" if x is None else x
        )
    
    with col3:
        merchant_filter = st.text_input("Merchant ID (optional)")
    
    # Fetch alerts
    alerts_data = get_alerts(
        dt=date_str,
        severity_min=severity_filter,
        rule_code=rule_filter
    )
    
    if not alerts_data or not alerts_data.get('alerts'):
        st.warning("No alerts found with the selected filters.")
        return
    
    alerts_list = alerts_data['alerts']
    
    # Filter by merchant if specified
    if merchant_filter:
        alerts_list = [a for a in alerts_list if a.get('merchant_id') == merchant_filter]
    
    st.info(f"Found {len(alerts_list)} alerts")
    
    # Display alerts table
    if alerts_list:
        df_alerts = pd.DataFrame(alerts_list)
        
        # Format columns
        display_columns = ['alert_id', 'dt', 'merchant_id', 'rule_code', 'severity', 'details']
        df_display = df_alerts[display_columns].copy()
        
        st.dataframe(
            df_display,
            use_container_width=True,
            hide_index=True
        )
        
        # Alert details expander
        st.subheader("Alert Details")
        for alert in alerts_list[:10]:  # Show first 10
            with st.expander(f"Alert {str(alert['alert_id'])[:8]}... - {alert['rule_code']} (Severity: {alert['severity']})"):
                st.json(alert)


def show_merchant_analytics(date_str):
    """Merchant analytics page"""
    st.header("Merchant Analytics")
    
    # Top merchants section
    st.subheader(f"Top Merchants - {date_str}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        metric_select = st.selectbox(
            "Metric",
            options=['tx_count', 'sum_amount', 'avg_amount', 'max_amount'],
            format_func=lambda x: {
                'tx_count': 'Transaction Count',
                'sum_amount': 'Total Amount',
                'avg_amount': 'Average Amount',
                'max_amount': 'Maximum Amount'
            }.get(x, x)
        )
    
    with col2:
        top_n = st.slider("Number of merchants", min_value=5, max_value=50, value=10)
    
    # Fetch top merchants
    top_data = get_top_merchants(date_str, metric=metric_select, n=top_n)
    
    if top_data and top_data.get('merchants'):
        df_merchants = pd.DataFrame(top_data['merchants'])
        
        # Bar chart
        fig = px.bar(
            df_merchants,
            x='merchant_id',
            y=metric_select,
            title=f"Top {top_n} Merchants by {metric_select}",
            labels={'merchant_id': 'Merchant ID', metric_select: metric_select.replace('_', ' ').title()},
            color=metric_select,
            color_continuous_scale='Blues'
        )
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)
        
        # Data table
        st.dataframe(df_merchants, use_container_width=True, hide_index=True)
    else:
        st.warning("No merchant data available for this date.")
    
    # Time series section
    st.markdown("---")
    st.subheader("Merchant Time Series")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        merchant_id = st.text_input("Merchant ID", value="MERCHANT_0001")
    
    with col2:
        from_date = st.date_input(
            "From Date",
            value=datetime.strptime(date_str, "%Y-%m-%d") - timedelta(days=7)
        )
    
    with col3:
        to_date = st.date_input(
            "To Date",
            value=datetime.strptime(date_str, "%Y-%m-%d")
        )
    
    if st.button("Load Time Series"):
        series_data = get_merchant_series(
            merchant_id,
            from_date.strftime("%Y-%m-%d"),
            to_date.strftime("%Y-%m-%d")
        )
        
        if series_data and series_data.get('series'):
            df_series = pd.DataFrame(series_data['series'])
            df_series['dt'] = pd.to_datetime(df_series['dt'])
            
            # Multiple metrics chart
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=df_series['dt'],
                y=df_series['tx_count'],
                name='Transaction Count',
                mode='lines+markers'
            ))
            
            fig.add_trace(go.Scatter(
                x=df_series['dt'],
                y=df_series['sum_amount'],
                name='Total Amount',
                mode='lines+markers',
                yaxis='y2'
            ))
            
            fig.update_layout(
                title=f"Time Series for {merchant_id}",
                xaxis_title="Date",
                yaxis_title="Transaction Count",
                yaxis2=dict(
                    title="Total Amount",
                    overlaying='y',
                    side='right'
                ),
                hovermode='x unified'
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Data table
            st.dataframe(df_series, use_container_width=True, hide_index=True)
        else:
            st.error("No data found for this merchant in the selected date range.")


def show_pipeline_control(date_str):
    """Pipeline control page"""
    st.header("Pipeline Control")
    
    st.info("""
    This page allows you to trigger the MapReduce pipeline manually.
    The pipeline will:
    1. Clean and normalize raw transactions (MR1)
    2. Compute merchant daily metrics (MR2)
    3. Generate fraud alerts (MR3)
    4. Load results into PostgreSQL
    """)
    
    st.subheader("Run Pipeline")
    
    col1, col2 = st.columns(2)
    
    with col1:
        pipeline_date = st.date_input(
            "Date to Process",
            value=datetime.strptime(date_str, "%Y-%m-%d")
        )
    
    with col2:
        st.write("")  # Spacer
        st.write("")
        run_button = st.button("🚀 Run Pipeline", type="primary")
    
    if run_button:
        with st.spinner(f"Running pipeline for {pipeline_date.strftime('%Y-%m-%d')}... This may take several minutes."):
            response = run_pipeline(pipeline_date.strftime("%Y-%m-%d"))
            
            if response and response.status_code == 200:
                st.success("✅ Pipeline completed successfully!")
                result = response.json()
                
                with st.expander("View Pipeline Output"):
                    st.code(result.get('output', 'No output available'))
            else:
                st.error("❌ Pipeline execution failed!")
                if response:
                    error_detail = response.json().get('detail', 'Unknown error')
                    st.error(f"Error: {error_detail}")
    
    # Pipeline status info
    st.markdown("---")
    st.subheader("Pipeline Information")
    
    st.markdown("""
    **MapReduce Jobs:**
    - **MR1 (clean_normalize):** Validates and normalizes raw transaction data
    - **MR2 (merchant_metrics):** Aggregates metrics by merchant and date
    - **MR3 (alerts):** Generates fraud alerts based on rules
    
    **Alert Rules:**
    - `HIGH_AMOUNT`: Maximum transaction > $1000 (Severity: 3)
    - `BURST`: More than 30 transactions per day (Severity: 2)
    - `MULTI_COUNTRY`: Transactions from 3+ countries (Severity: 2)
    - `HIGH_DECLINE`: Decline rate > 50% (Severity: 3)
    """)


if __name__ == "__main__":
    main()
