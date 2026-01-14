#!/usr/bin/env python3

import os
import sys
import subprocess
import platform
import time
import shutil

def print_logo():
    print("\n" + "="*70)
    print("  🚀 ENHANCED E2E VOICE CHAT - AUTOMATIC SETUP")
    print("="*70)
    print(f"  💻 OS: {platform.system()}")
    print(f"  🐍 Python: {sys.version_info.major}.{sys.version_info.minor}")
    print("="*70 + "\n")

def check_python():
    if sys.version_info < (3, 7):
        print("❌ Python 3.7+ required!")
        return False
    print("✅ Python version compatible\n")
    return True

def is_venv():
    return hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)

def create_venv():
    venv_path = "venv"
    
    if os.path.exists(venv_path):
        print(f"✅ Virtual environment exists: {venv_path}\n")
        return venv_path
    
    print(f"📦 Creating virtual environment: {venv_path}")
    try:
        subprocess.check_call([sys.executable, "-m", "venv", venv_path])
        print(f"✅ Virtual environment created\n")
        return venv_path
    except subprocess.CalledProcessError:
        print("❌ Could not create virtual environment")
        print("   Solution: sudo apt-get install python3-venv")
        return None

def get_venv_python(venv_path):
    if platform.system() == "Windows":
        return os.path.join(venv_path, "Scripts", "python.exe")
    else:
        return os.path.join(venv_path, "bin", "python")

def get_venv_pip(venv_path):
    if platform.system() == "Windows":
        return os.path.join(venv_path, "Scripts", "pip.exe")
    else:
        return os.path.join(venv_path, "bin", "pip")

def install_package(pip_path, name, import_name=None):
    if import_name is None:
        import_name = name
    
    print(f"📦 Installing {name}...")
    try:
        subprocess.check_call([pip_path, "install", name, "-q"])
        print(f"✅ {name} - Installed")
        return True
    except:
        print(f"❌ {name} - Error")
        return False

def install_pyaudio_linux(pip_path):
    print("\n🐧 Linux - Installing PyAudio...")
    
    print("   Checking for PortAudio...")
    
    distro_commands = {
        'apt': 'sudo apt-get install -y portaudio19-dev python3-pyaudio',
        'dnf': 'sudo dnf install -y portaudio-devel',
        'yum': 'sudo yum install -y portaudio-devel',
        'pacman': 'sudo pacman -S --noconfirm portaudio'
    }
    
    pkg_manager = None
    for pm in distro_commands.keys():
        if shutil.which(pm):
            pkg_manager = pm
            break
    
    if pkg_manager:
        print(f"   📦 Package manager found: {pkg_manager}")
        print(f"   🔧 Installing PortAudio (may require sudo)...")
        
        try:
            if pkg_manager == 'apt':
                subprocess.run(['sudo', 'apt-get', 'update'], check=False)
                subprocess.run(['sudo', 'apt-get', 'install', '-y', 'portaudio19-dev'], check=True)
            elif pkg_manager in ['dnf', 'yum']:
                subprocess.run(['sudo', pkg_manager, 'install', '-y', 'portaudio-devel'], check=True)
            elif pkg_manager == 'pacman':
                subprocess.run(['sudo', 'pacman', '-S', '--noconfirm', 'portaudio'], check=True)
            
            print("   ✅ PortAudio installed")
        except subprocess.CalledProcessError:
            print("   ⚠️ PortAudio installation failed (manual installation may be required)")
        except Exception as e:
            print(f"   ⚠️ Error: {e}")
    else:
        print("   ⚠️ Package manager not found")
        print("   📖 Manual installation:")
        print("      Ubuntu/Debian: sudo apt-get install portaudio19-dev")
        print("      Fedora: sudo dnf install portaudio-devel")
        print("      Arch: sudo pacman -S portaudio")
    
    print("   Installing PyAudio with pip...")
    try:
        subprocess.check_call([pip_path, "install", "pyaudio", "-q"])
        print("✅ PyAudio - Installed\n")
        return True
    except:
        print("❌ PyAudio installation error")
        print("   Please install system packages above and try again\n")
        return False

def install_pyaudio(pip_path):
    os_type = platform.system()
    
    if os_type == "Windows":
        print("\n🪟 Windows - Installing PyAudio...")
        try:
            install_package(pip_path, "pipwin")
            venv_pipwin = pip_path.replace("pip", "pipwin")
            subprocess.check_call([venv_pipwin, "install", "pyaudio", "-q"])
            print("✅ PyAudio - Installed\n")
            return True
        except:
            try:
                subprocess.check_call([pip_path, "install", "pyaudio", "-q"])
                print("✅ PyAudio - Installed\n")
                return True
            except:
                print("❌ PyAudio requires manual installation:")
                print("   https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio\n")
                return False
    
    elif os_type == "Darwin":
        print("\n🍎 macOS - Installing PortAudio...")
        try:
            subprocess.run(["brew", "install", "portaudio"], 
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print("   ✅ PortAudio installed")
        except:
            print("   ⚠️ Homebrew: brew install portaudio")
        
        try:
            subprocess.check_call([pip_path, "install", "pyaudio", "-q"])
            print("✅ PyAudio - Installed\n")
            return True
        except:
            print("❌ PyAudio installation error\n")
            return False
    
    else:
        return install_pyaudio_linux(pip_path)

def create_run_script(venv_path):
    venv_python = get_venv_python(venv_path)
    
    if platform.system() == "Windows":
        with open("start_server.bat", "w", encoding="utf-8") as f:
            f.write("@echo off\n")
            f.write("title Chat Server\n")
            f.write(f'"{venv_python}" chat_server.py\n')
            f.write("pause\n")
        
        with open("start_client.bat", "w", encoding="utf-8") as f:
            f.write("@echo off\n")
            f.write("title Chat Client\n")
            f.write(f'"{venv_python}" chat_client.py\n')
            f.write("pause\n")
        
        print("✅ Windows startup scripts created:")
        print("   - start_server.bat")
        print("   - start_client.bat\n")
    else:
        with open("start_server.sh", "w") as f:
            f.write("#!/bin/bash\n")
            f.write(f'cd "$(dirname "$0")"\n')
            f.write(f'"{venv_python}" chat_server.py\n')
        os.chmod("start_server.sh", 0o755)
        
        with open("start_client.sh", "w") as f:
            f.write("#!/bin/bash\n")
            f.write(f'cd "$(dirname "$0")"\n')
            f.write(f'"{venv_python}" chat_client.py\n')
        os.chmod("start_client.sh", 0o755)
        
        print("✅ Linux/Mac startup scripts created:")
        print("   - start_server.sh")
        print("   - start_client.sh\n")

def main():
    print_logo()
    
    if not check_python():
        input("\nPress Enter to continue...")
        return
    
    in_venv = is_venv()
    venv_path = None
    
    if not in_venv:
        print("⚠️ Not using virtual environment")
        print("   Virtual environment is recommended for modern Linux systems\n")
        
        response = input("🔧 Create virtual environment? (y/n): ")
        if response.lower() in ['e', 'y', 'evet', 'yes']:
            venv_path = create_venv()
            if not venv_path:
                input("\nPress Enter to continue...")
                return
            
            venv_python = get_venv_python(venv_path)
            venv_pip = get_venv_pip(venv_path)
            
            print("\n📝 NOTE: Virtual environment created!")
            print(f"   All installation will be done inside this environment\n")
        else:
            print("⚠️ Continuing without virtual environment...")
            print("   (--break-system-packages may be used but not recommended)\n")
            venv_python = sys.executable
            venv_pip = "pip3"
    else:
        print("✅ You are inside a virtual environment\n")
        venv_python = sys.executable
        venv_pip = "pip"
    
    print("🔄 Upgrading pip...")
    try:
        if venv_path:
            subprocess.check_call([venv_pip, "install", "--upgrade", "pip", "-q"])
        else:
            subprocess.check_call([venv_pip, "install", "--upgrade", "pip", "-q"])
        print("✅ pip upgraded\n")
    except:
        print("⚠️ Could not upgrade pip\n")
    
    print("📚 Installing dependencies...\n")
    
    cryptography_ok = install_package(venv_pip, "cryptography")
    pyaudio_ok = install_pyaudio(venv_pip)
    
    print("\n" + "="*70)
    print("📊 INSTALLATION RESULT")
    print("="*70)
    print(f"{'✅' if cryptography_ok else '❌'} Cryptography (E2E Encryption)")
    print(f"{'✅' if pyaudio_ok else '❌'} PyAudio (Voice Calling)")
    print("="*70 + "\n")
    
    has_server = os.path.exists("chat_server.py")
    has_client = os.path.exists("chat_client.py")
    
    if not has_server or not has_client:
        print("⚠️ Application files not found!")
        print("   Place chat_server.py and chat_client.py in this folder.\n")
    else:
        print("✅ Application files present\n")
        if venv_path:
            create_run_script(venv_path)
    
    if cryptography_ok and pyaudio_ok and has_server and has_client:
        print("🎉 INSTALLATION COMPLETE!\n")
        print("📖 USAGE:")
        print("="*70)
        
        if platform.system() == "Windows":
            print("1️⃣  Start server: start_server.bat")
            print("2️⃣  Start client: start_client.bat")
        else:
            print("1️⃣  Start server: ./start_server.sh")
            print("2️⃣  Start client: ./start_client.sh")
        
        print("\n🔑 Default password: fidelio")
        print("="*70 + "\n")
        
        response = input("🚀 Do you want to start the server now? (y/n): ")
        if response.lower() in ['e', 'y', 'evet', 'yes']:
            print("\n🚀 Starting server...\n")
            try:
                subprocess.Popen([venv_python, "chat_server.py"])
                time.sleep(2)
                
                response = input("\n💻 Do you want to open the client? (y/n): ")
                if response.lower() in ['e', 'y', 'evet', 'yes']:
                    subprocess.Popen([venv_python, "chat_client.py"])
            except Exception as e:
                print(f"❌ Startup error: {e}")
    else:
        print("⚠️ Installation incomplete. Please resolve the errors.\n")
    
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nℹ️ Installation cancelled.")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        input("\nPress Enter to continue...")
