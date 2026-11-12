@echo off
chcp 65001 >nul
title AI 冰箱管家 - 公网隧道
echo ========================================
echo   AI 冰箱管家 - 启动公网访问
echo ========================================
echo.
echo [1/2] 启动应用 (新窗口)...
start "BBB-App" cmd /k "cd /d %~dp0 && python -m streamlit run streamlit_app.py --server.port 8501 --server.headless true"
echo   等待应用启动...
timeout /t 12 /nobreak > nul
echo   应用已启动 (端口8501)
echo.
echo [2/2] 启动公网隧道 (serveo.net)...
echo   ������������������������������������
echo   ↓↓↓ 公网链接将显示在下方 ↓↓↓
echo   ������������������������������������
echo.
ssh -o StrictHostKeyChecking=no -R 80:localhost:8501 serveo.net
echo.
echo 隧道已断开，按任意键退出
pause > nul