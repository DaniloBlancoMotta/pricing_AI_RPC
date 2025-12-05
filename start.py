import subprocess
import time
import sys
import os

def main():
    print("🚀 Iniciando Sistema Completo (Backend + Frontend)...")


    root_dir = os.path.dirname(os.path.abspath(__file__))
    frontend_dir = os.path.join(root_dir, "frontend")

    print("📡 Iniciando Backend (Porta 8000)...")
    backend = subprocess.Popen(
        [sys.executable, "server.py"],
        cwd=root_dir
    )

    time.sleep(2)

    npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
    
    print("🎨 Iniciando Frontend (Porta 5173)...")
    frontend = subprocess.Popen(
        [npm_cmd, "run", "dev"],
        cwd=frontend_dir
    )

    print("\n✅ Ambos os serviços estão rodando!")
    print("   - Backend: http://localhost:8000/docs")
    print("   - Frontend: http://localhost:5173")
    print("\n🛑 Pressione Ctrl+C para parar tudo.\n")

    try:
        while True:
            time.sleep(1)

            if backend.poll() is not None:
                print("❌ O Backend parou inesperadamente.")
                break
            if frontend.poll() is not None:
                print("❌ O Frontend parou inesperadamente.")
                break
    except KeyboardInterrupt:
        print("\n🛑 Parando serviços...")
    finally:

        try:
            backend.terminate()
            frontend.terminate()
        except:
            pass
            
        print("👋 Sistema encerrado.")

if __name__ == "__main__":
    main()
