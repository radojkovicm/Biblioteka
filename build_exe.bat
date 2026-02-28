@echo off
echo ============================================
echo   Biblioteka — Build EXE
echo ============================================
echo.

pip install pyinstaller pystray pillow

pyinstaller --onefile --name Biblioteka ^
    --add-data "frontend;frontend" ^
    --add-data "config;config" ^
    --icon=NONE ^
    --hidden-import=uvicorn.logging ^
    --hidden-import=uvicorn.loops ^
    --hidden-import=uvicorn.loops.auto ^
    --hidden-import=uvicorn.protocols ^
    --hidden-import=uvicorn.protocols.http ^
    --hidden-import=uvicorn.protocols.http.auto ^
    --hidden-import=uvicorn.protocols.websockets ^
    --hidden-import=uvicorn.protocols.websockets.auto ^
    --hidden-import=uvicorn.lifespan ^
    --hidden-import=uvicorn.lifespan.on ^
    --hidden-import=app.main ^
    --hidden-import=app.routes.auth ^
    --hidden-import=app.routes.books ^
    --hidden-import=app.routes.members ^
    --hidden-import=app.routes.loans ^
    --hidden-import=app.routes.reservations ^
    --hidden-import=app.routes.reports ^
    --hidden-import=app.routes.settings ^
    --hidden-import=app.routes.import_export ^
    launcher.py

echo.
echo Build zavrsen! EXE je u dist/Biblioteka.exe
echo.
pause
