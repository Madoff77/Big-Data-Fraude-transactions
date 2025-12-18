# Startup Verification Script
# Run this after docker-compose up to verify all services are working

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Fraud Detection System - Health Check" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Function to check HTTP endpoint
function Test-Endpoint {
    param($Name, $Url)
    Write-Host "Checking $Name..." -NoNewline
    try {
        $response = Invoke-WebRequest -Uri $Url -TimeoutSec 5 -UseBasicParsing
        if ($response.StatusCode -eq 200) {
            Write-Host " ✓ OK" -ForegroundColor Green
            return $true
        } else {
            Write-Host " ✗ FAILED (Status: $($response.StatusCode))" -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Host " ✗ NOT ACCESSIBLE" -ForegroundColor Red
        return $false
    }
}

# Function to check Docker container
function Test-Container {
    param($Name)
    Write-Host "Checking container $Name..." -NoNewline
    $container = docker ps --filter "name=$Name" --format "{{.Status}}"
    if ($container -match "Up") {
        Write-Host " ✓ RUNNING" -ForegroundColor Green
        return $true
    } else {
        Write-Host " ✗ NOT RUNNING" -ForegroundColor Red
        return $false
    }
}

Write-Host "1. Docker Containers Status" -ForegroundColor Yellow
Write-Host "----------------------------"
$containers = @(
    "zookeeper",
    "kafka",
    "namenode",
    "datanode",
    "resourcemanager",
    "nodemanager",
    "postgres",
    "producer",
    "consumer",
    "backend",
    "frontend"
)

$allRunning = $true
foreach ($container in $containers) {
    if (-not (Test-Container $container)) {
        $allRunning = $false
    }
}

Write-Host ""
Write-Host "2. Service Endpoints" -ForegroundColor Yellow
Write-Host "--------------------"

$endpoints = @{
    "HDFS NameNode" = "http://localhost:9870"
    "YARN ResourceManager" = "http://localhost:8088"
    "Backend API" = "http://localhost:8000/health"
    "Frontend Dashboard" = "http://localhost:8501"
}

$allHealthy = $true
foreach ($endpoint in $endpoints.GetEnumerator()) {
    if (-not (Test-Endpoint $endpoint.Key $endpoint.Value)) {
        $allHealthy = $false
    }
}

Write-Host ""
Write-Host "3. Data Verification" -ForegroundColor Yellow
Write-Host "--------------------"

# Check HDFS data
Write-Host "Checking HDFS data..." -NoNewline
try {
    $hdfsCheck = docker exec namenode hadoop fs -ls /data/raw/transactions/ 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host " ✓ HDFS accessible" -ForegroundColor Green
    } else {
        Write-Host " ⚠ HDFS accessible but no data yet" -ForegroundColor Yellow
    }
} catch {
    Write-Host " ✗ HDFS check failed" -ForegroundColor Red
}

# Check PostgreSQL
Write-Host "Checking PostgreSQL..." -NoNewline
try {
    $pgCheck = docker exec postgres psql -U fraud_user -d frauddb -c "SELECT 1" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host " ✓ Database accessible" -ForegroundColor Green
    } else {
        Write-Host " ✗ Database check failed" -ForegroundColor Red
    }
} catch {
    Write-Host " ✗ Database check failed" -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan

if ($allRunning -and $allHealthy) {
    Write-Host "✓ All systems operational!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "1. Wait 2-3 minutes for data generation"
    Write-Host "2. Open dashboard: http://localhost:8501"
    Write-Host "3. Run pipeline: curl -X POST 'http://localhost:8000/pipeline/run?dt=2025-12-18'"
} else {
    Write-Host "⚠ Some services are not ready" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Troubleshooting:" -ForegroundColor Yellow
    Write-Host "- Wait 2-3 minutes for services to initialize"
    Write-Host "- Check logs: docker-compose logs -f"
    Write-Host "- Restart: docker-compose restart [service-name]"
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
