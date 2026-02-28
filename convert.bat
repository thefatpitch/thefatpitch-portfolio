@echo off
echo ====================================
echo IBKR to Dashboard Converter v2.2
echo ====================================
echo.
echo Converting IBKR files to CSV format...
echo.
python convert_ibkr_to_csv.py
if ERRORLEVEL 1 (
    echo.
    echo ERROR occurred during conversion!
) else (
    echo.
    echo Conversion Complete!
)
echo.
pause
