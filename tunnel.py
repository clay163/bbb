import subprocess, time, os

st = subprocess.Popen(
    ["python", "-m", "streamlit", "run", "streamlit_app.py",
     "--server.port", "8501", "--server.headless", "true"],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
)
time.sleep(12)

import urllib.request
try:
    urllib.request.urlopen("http://localhost:8501", timeout=5)
    print("✅ Streamlit 运行中 (localhost:8501)")
except Exception:
    print("❌ Streamlit 启动失败")
    st.kill()
    exit(1)

tunnels = [
    ("serveo.net", ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10",
                    "-R", "80:localhost:8501", "serveo.net"]),
    ("localhost.run", ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10",
                       "-R", "80:localhost:8501", "nokey@localhost.run"]),
]

for name, cmd in tunnels:
    print(f"\n尝试 {name}...")
    open("tunnel.log", "w").close()
    tunnel = subprocess.Popen(cmd, stdout=open("tunnel.log", "w"),
                              stderr=subprocess.STDOUT)
    time.sleep(10)

    if tunnel.poll() is not None:
        with open("tunnel.log") as f:
            err = f.read()
        print(f"  失败: {err[:150]}")
        continue

    with open("tunnel.log") as f:
        output = f.read().strip()

    if output and ("https://" in output or "http://" in output):
        print(f"🎉 公网链接: {output}")
        print(f"\n链接有效期内任何人都能访问，10分钟后自动关闭。")
        time.sleep(600)
        st.kill()
        tunnel.kill()
        exit(0)
    else:
        print(f"  输出: {output[:150] if output else '(空)'}")
        tunnel.kill()

print("\n❌ 隧道服务均失败，将使用 Streamlit 社区云方案")
st.kill()