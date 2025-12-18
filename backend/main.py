"""
FastAPI Backend for Fraud Detection System
Provides REST API endpoints for querying metrics and alerts
"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
from datetime import datetime, date
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import subprocess
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'postgres')
POSTGRES_PORT = os.getenv('POSTGRES_PORT', '5432')
POSTGRES_DB = os.getenv('POSTGRES_DB', 'frauddb')
POSTGRES_USER = os.getenv('POSTGRES_USER', 'fraud_user')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'fraud_password_123')

# Create FastAPI app
app = FastAPI(
    title="Fraud Detection API",
    description="Big Data fraud detection system API",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db_connection():
    """Create database connection"""
    try:
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            database=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            cursor_factory=RealDictCursor
        )
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise HTTPException(status_code=500, detail="Database connection failed")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        conn.close()
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "database": "connected"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }


@app.get("/metrics/merchants/top")
async def get_top_merchants(
    dt: str = Query(..., description="Date in YYYY-MM-DD format"),
    metric: str = Query("tx_count", description="Metric to sort by: tx_count, sum_amount, avg_amount, max_amount"),
    n: int = Query(10, description="Number of top merchants to return", ge=1, le=100)
):
    """
    Get top N merchants by specified metric for a given date
    """
    # Validate date format
    try:
        datetime.strptime(dt, '%Y-%m-%d')
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    # Validate metric
    valid_metrics = ['tx_count', 'sum_amount', 'avg_amount', 'max_amount']
    if metric not in valid_metrics:
        raise HTTPException(status_code=400, detail=f"Invalid metric. Choose from: {valid_metrics}")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = f"""
        SELECT 
            merchant_id,
            tx_count,
            sum_amount,
            avg_amount,
            max_amount,
            unique_countries,
            unique_devices,
            decline_rate
        FROM merchant_daily_metrics
        WHERE dt = %s
        ORDER BY {metric} DESC
        LIMIT %s
    """
    
    cursor.execute(query, (dt, n))
    results = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return {
        "date": dt,
        "metric": metric,
        "top_n": n,
        "merchants": results
    }


@app.get("/alerts")
async def get_alerts(
    dt: Optional[str] = Query(None, description="Date in YYYY-MM-DD format"),
    severity_min: Optional[int] = Query(None, description="Minimum severity level (1-3)", ge=1, le=3),
    rule_code: Optional[str] = Query(None, description="Filter by rule code"),
    merchant_id: Optional[str] = Query(None, description="Filter by merchant ID"),
    limit: int = Query(100, description="Maximum number of alerts to return", ge=1, le=1000)
):
    """
    Get alerts with optional filters
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Build dynamic query
    conditions = []
    params = []
    
    if dt:
        try:
            datetime.strptime(dt, '%Y-%m-%d')
            conditions.append("dt = %s")
            params.append(dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    if severity_min:
        conditions.append("severity >= %s")
        params.append(severity_min)
    
    if rule_code:
        conditions.append("rule_code = %s")
        params.append(rule_code)
    
    if merchant_id:
        conditions.append("merchant_id = %s")
        params.append(merchant_id)
    
    where_clause = " AND ".join(conditions) if conditions else "1=1"
    
    query = f"""
        SELECT 
            alert_id,
            dt,
            merchant_id,
            customer_id,
            rule_code,
            severity,
            details,
            created_at
        FROM alerts
        WHERE {where_clause}
        ORDER BY created_at DESC, severity DESC
        LIMIT %s
    """
    
    params.append(limit)
    cursor.execute(query, params)
    results = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return {
        "filters": {
            "date": dt,
            "severity_min": severity_min,
            "rule_code": rule_code,
            "merchant_id": merchant_id
        },
        "count": len(results),
        "alerts": results
    }


@app.get("/merchant/{merchant_id}/series")
async def get_merchant_time_series(
    merchant_id: str,
    from_date: str = Query(..., alias="from", description="Start date (YYYY-MM-DD)"),
    to_date: str = Query(..., alias="to", description="End date (YYYY-MM-DD)")
):
    """
    Get time series data for a specific merchant
    """
    # Validate dates
    try:
        datetime.strptime(from_date, '%Y-%m-%d')
        datetime.strptime(to_date, '%Y-%m-%d')
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = """
        SELECT 
            dt,
            merchant_id,
            tx_count,
            sum_amount,
            avg_amount,
            max_amount,
            unique_countries,
            unique_devices,
            decline_rate
        FROM merchant_daily_metrics
        WHERE merchant_id = %s AND dt BETWEEN %s AND %s
        ORDER BY dt ASC
    """
    
    cursor.execute(query, (merchant_id, from_date, to_date))
    results = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    if not results:
        raise HTTPException(status_code=404, detail=f"No data found for merchant {merchant_id} in date range")
    
    return {
        "merchant_id": merchant_id,
        "from": from_date,
        "to": to_date,
        "data_points": len(results),
        "series": results
    }


@app.post("/pipeline/run")
async def run_pipeline(
    dt: str = Query(..., description="Date to process (YYYY-MM-DD)")
):
    """
    Trigger the MapReduce pipeline for a specific date
    Runs MR1 -> MR2 -> MR3 and loads results to PostgreSQL
    """
    # Validate date
    try:
        datetime.strptime(dt, '%Y-%m-%d')
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    logger.info(f"Starting pipeline for date: {dt}")
    
    try:
        # Execute the pipeline script
        result = subprocess.run(
            ["/bin/bash", "/app/scripts/run_pipeline.sh", dt],
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout
        )
        
        if result.returncode == 0:
            logger.info(f"Pipeline completed successfully for {dt}")
            return {
                "status": "success",
                "date": dt,
                "message": "Pipeline executed successfully",
                "output": result.stdout
            }
        else:
            logger.error(f"Pipeline failed for {dt}: {result.stderr}")
            raise HTTPException(
                status_code=500,
                detail={
                    "status": "failed",
                    "date": dt,
                    "error": result.stderr,
                    "output": result.stdout
                }
            )
    
    except subprocess.TimeoutExpired:
        logger.error(f"Pipeline timeout for {dt}")
        raise HTTPException(status_code=504, detail="Pipeline execution timeout")
    except Exception as e:
        logger.error(f"Pipeline error for {dt}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats/summary")
async def get_summary_stats(
    dt: Optional[str] = Query(None, description="Date in YYYY-MM-DD format, or latest if not specified")
):
    """
    Get summary statistics for dashboard
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # If no date specified, get the latest
    if not dt:
        cursor.execute("SELECT MAX(dt) FROM merchant_daily_metrics")
        result = cursor.fetchone()
        if result and result['max']:
            dt = result['max'].strftime('%Y-%m-%d')
        else:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=404, detail="No data available")
    
    # Get metrics summary
    cursor.execute("""
        SELECT 
            COUNT(*) as total_merchants,
            SUM(tx_count) as total_transactions,
            SUM(sum_amount) as total_amount,
            AVG(decline_rate) as avg_decline_rate
        FROM merchant_daily_metrics
        WHERE dt = %s
    """, (dt,))
    metrics_summary = cursor.fetchone()
    
    # Get alerts summary
    cursor.execute("""
        SELECT 
            COUNT(*) as total_alerts,
            COUNT(*) FILTER (WHERE severity = 3) as high_severity,
            COUNT(*) FILTER (WHERE severity = 2) as medium_severity,
            COUNT(*) FILTER (WHERE severity = 1) as low_severity
        FROM alerts
        WHERE dt = %s
    """, (dt,))
    alerts_summary = cursor.fetchone()
    
    # Get rule breakdown
    cursor.execute("""
        SELECT 
            rule_code,
            COUNT(*) as count
        FROM alerts
        WHERE dt = %s
        GROUP BY rule_code
        ORDER BY count DESC
    """, (dt,))
    rule_breakdown = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return {
        "date": dt,
        "metrics": metrics_summary,
        "alerts": alerts_summary,
        "rule_breakdown": rule_breakdown
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
