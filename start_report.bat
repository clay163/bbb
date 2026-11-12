@echo off
chcp 65001 >nul
title AI冰箱管家 - 方案报告公网访问
echo ========================================
echo   AI冰箱管家 方案报告 - 启动公网访问
echo ========================================
echo.
echo [1/2] 启动静态报告服务 (端口8000)...
start "BBB-Report" cmd /k "cd /d %~dp0\report && python -m http.server 8000"
echo   等待服务启动...
timeout /t 4 /nobreak > nul
echo   报告服务已启动 (端口8000)
echo.
echo [2/2] 启动公网隧道 (serveo.net)...
echo   ==================================================
echo   ->  公网链接将显示在下方，复制到浏览器打开  <-
echo   ==================================================
echo.
ssh -o StrictHostKeyChecking=no -R 80:localhost:8000 serveo.net
echo.
echo 隧道已断开，按任意键退出
pause > nul