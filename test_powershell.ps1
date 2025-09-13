# PowerShell script to test sunflower API endpoints
# Run this in PowerShell: .\test_powershell.ps1

Write-Host "🌻 Testing Sunflower API with PowerShell" -ForegroundColor Green
Write-Host "=" * 50

# Step 1: Login
Write-Host "`n🔐 Step 1: Logging in..." -ForegroundColor Yellow
try {
    $loginResponse = Invoke-RestMethod -Uri "http://localhost:5000/login" -Method POST -ContentType "application/json" -Body '{"email": "test@example.com", "password": "password123"}'
    
    if ($loginResponse.access_token) {
        $token = $loginResponse.access_token
        Write-Host "✅ Login successful!" -ForegroundColor Green
        Write-Host "JWT Token: $($token.Substring(0, 50))..." -ForegroundColor Cyan
        
        # Step 2: Get History
        Write-Host "`n📊 Step 2: Getting prediction history..." -ForegroundColor Yellow
        $headers = @{
            "Authorization" = "Bearer $token"
            "Content-Type" = "application/json"
        }
        
        $historyResponse = Invoke-RestMethod -Uri "http://localhost:5000/history" -Method GET -Headers $headers
        
        if ($historyResponse.status -eq "success") {
            Write-Host "✅ History retrieved successfully!" -ForegroundColor Green
            Write-Host "📈 Total predictions: $($historyResponse.pagination.total)" -ForegroundColor Cyan
            
            if ($historyResponse.history.Count -gt 0) {
                Write-Host "`n🌻 Recent Predictions:" -ForegroundColor Yellow
                for ($i = 0; $i -lt [Math]::Min(3, $historyResponse.history.Count); $i++) {
                    $analysis = $historyResponse.history[$i]
                    Write-Host "  $($i+1). Analysis ID: $($analysis.id)" -ForegroundColor White
                    Write-Host "     Predicted: $($analysis.predicted_class)" -ForegroundColor White
                    Write-Host "     Confidence: $([Math]::Round($analysis.confidence * 100, 2))%" -ForegroundColor White
                    Write-Host "     Image: $($analysis.image_info.filename)" -ForegroundColor White
                    Write-Host "     Date: $($analysis.created_at)" -ForegroundColor White
                    if ($analysis.images.original_image_url) {
                        Write-Host "     Image URL: $($analysis.images.original_image_url)" -ForegroundColor Cyan
                    }
                    Write-Host ""
                }
                
                # Step 3: Get specific analysis
                $firstId = $historyResponse.history[0].id
                Write-Host "🔍 Step 3: Getting specific analysis $firstId..." -ForegroundColor Yellow
                $specificResponse = Invoke-RestMethod -Uri "http://localhost:5000/history/$firstId" -Method GET -Headers $headers
                
                if ($specificResponse.status -eq "success") {
                    Write-Host "✅ Specific analysis retrieved!" -ForegroundColor Green
                    Write-Host "All predictions:" -ForegroundColor Yellow
                    $specificResponse.analysis.all_predictions | ConvertTo-Json -Depth 2
                }
            } else {
                Write-Host "📭 No prediction history found for this user" -ForegroundColor Yellow
            }
        }
    }
} catch {
    if ($_.Exception.Message -like "*ConnectFailure*" -or $_.Exception.Message -like "*connection*") {
        Write-Host "❌ Connection error! Make sure your server is running on http://localhost:5000" -ForegroundColor Red
    } else {
        Write-Host "❌ Error: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host "`n" + "=" * 50
Write-Host "✅ Test completed!" -ForegroundColor Green
