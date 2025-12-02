import socket
import os
import subprocess

def get_local_ip():
    try:
        # Connect to a public DNS server to determine the most appropriate local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

if __name__ == "__main__":
    ip = get_local_ip()
    port = 8501
    
    print("\n" + "="*60)
    print(f"🚀 Uygulama Başlatılıyor...")
    print(f"📱 Android cihazınızdan bağlanmak için şu adresi kullanın:")
    print(f"\n    http://{ip}:{port}\n")
    print(f"⚠️  NOT: Bilgisayarınız ve telefonunuz aynı Wi-Fi ağında olmalıdır.")
    print("="*60 + "\n")
    
    # Run Streamlit
    cmd = f"streamlit run app.py --server.address 0.0.0.0 --server.port {port}"
    os.system(cmd)
