# 🔐 E2E Encrypted Voice Chat

<div align="center">

![Python Version](https://img.shields.io/badge/python-3.7%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)
![Encryption](https://img.shields.io/badge/encryption-RSA%202048%20%2B%20AES%20256-red)

**Gerçek zamanlı, uçtan uca şifreli sesli ve metin sohbet uygulaması**

**Real-time, end-to-end encrypted voice and text chat application**

[English](#english) | [Türkçe](#türkçe)

</div>

---

# English

## 📖 About

A secure chat application that provides completely safe and anonymous communication using modern cryptography techniques. The server cannot read any messages - all encryption happens end-to-end between clients.

## ✨ Features

- 🔒 **E2E Encryption**: Military-grade security with RSA 2048 + AES 256
- 🎙️ **Voice Calling**: Real-time P2P voice communication
- 💬 **Text Chat**: Secure instant messaging
- 🌐 **Multi-language**: Turkish and English interface
- 🔑 **Password Protection**: Server access control
- 👥 **User Management**: Real-time user list and status
- 🎨 **Modern UI**: Dark themed, user-friendly interface
- 🔄 **Auto Reconnect**: Automatic connection recovery
- 📱 **Cross-platform**: Windows, Linux, macOS support

## 🔐 Security

- **RSA 2048-bit** for key exchange
- **AES 256-bit CFB** for message encryption
- **Zero-knowledge server**: Server only relays encrypted data
- **Perfect Forward Secrecy**: New AES key for each message
- **Client-side encryption**: All encryption happens on clients

## 🚀 Quick Start

### Automatic Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/e2e-voice-chat.git
cd e2e-voice-chat

# Run setup script
python3 setup.py
```

The setup script will:
- ✅ Check Python version
- ✅ Create virtual environment (recommended)
- ✅ Install all dependencies
- ✅ Create launch scripts
- ✅ Optionally start server and client

### Manual Installation

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install cryptography pyaudio

# For Linux, you may need PortAudio:
sudo apt-get install portaudio19-dev python3-pyaudio  # Ubuntu/Debian
```

## 💻 Usage

### Starting the Server

```bash
# Using launch scripts
./start_server.sh  # Linux/Mac
start_server.bat   # Windows

# Or directly
python3 chat_server.py
```

**Default password:** `fidelio`

### Starting the Client

```bash
# Using launch scripts
./start_client.sh  # Linux/Mac
start_client.bat   # Windows

# Or directly
python3 chat_client.py
```

### Client Interface

1. **Connection**: Enter server IP, port, and nickname
2. **Authentication**: Enter server password when prompted
3. **Messaging**: Type and send encrypted messages
4. **Voice Calls**: Select a user and click "Call" button
5. **Language**: Toggle between English/Turkish with the language button

## 🏗️ Architecture

### Client-Server Model

```
Client A                    Server                     Client B
   |                          |                           |
   |---[RSA Public Key]------>|                           |
   |                          |---[RSA Public Key]------->|
   |                          |                           |
   |<--[Encrypted Message]----|<--[Encrypted Message]----|
   |                          |                           |
   |-----[Voice Data]-------->|-----[Voice Data]--------->|
```

### Encryption Flow

1. **Key Exchange**: Each client generates RSA key pair on startup
2. **Public Key Distribution**: Server relays public keys to all clients
3. **Message Encryption**: Sender encrypts with recipient's public key
4. **AES Encryption**: Random AES key for each message, encrypted with RSA
5. **Voice Data**: Real-time audio transmitted through server relay

## 📁 Project Structure

```
e2e-voice-chat/
├── chat_client.py      # Client application with GUI
├── chat_server.py      # Server application
├── setup.py            # Automatic installation script
├── README.md           # This file
├── LICENSE             # MIT License
└── requirements.txt    # Python dependencies (optional)
```

## ⚙️ Configuration

### Server Settings (chat_server.py)

```python
host = '0.0.0.0'           # Listen on all interfaces
port = 12345               # Server port
password = "fidelio"       # Authentication password
```

### Client Settings

- Configurable through GUI:
  - Server IP address
  - Server port
  - User nickname
  - Language preference

## 🔧 Dependencies

- **Python 3.7+**
- **cryptography**: RSA and AES encryption
- **pyaudio**: Audio input/output for voice calls
- **tkinter**: GUI framework (usually pre-installed)

## 🐛 Troubleshooting

### PyAudio Installation Issues

**Linux:**
```bash
sudo apt-get install portaudio19-dev python3-pyaudio
pip install pyaudio
```

**macOS:**
```bash
brew install portaudio
pip install pyaudio
```

**Windows:**
- Download pre-built wheel from [here](https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio)
- Install with: `pip install PyAudio‑0.2.11‑cp3X‑cp3Xm‑win_amd64.whl`

### Connection Issues

- Check firewall settings
- Ensure server is running before connecting clients
- Verify correct IP address and port
- Check password is correct

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This application is designed for educational purposes and private use. While it implements strong encryption, it has not been audited by security professionals. Use at your own risk for sensitive communications.

## 🌟 Acknowledgments

- Built with Python's cryptography library
- Uses PyAudio for real-time audio streaming
- Inspired by secure messaging principles

---

# Türkçe

## 📖 Hakkında

Modern kriptografi teknikleri kullanarak tamamen güvenli ve anonim iletişim sağlayan bir güvenli sohbet uygulaması. Sunucu hiçbir mesajı okuyamaz - tüm şifreleme istemciler arasında uçtan uca gerçekleşir.

## ✨ Özellikler

- 🔒 **E2E Şifreleme**: RSA 2048 + AES 256 ile askeri seviye güvenlik
- 🎙️ **Sesli Arama**: Gerçek zamanlı P2P sesli iletişim
- 💬 **Metin Sohbet**: Güvenli anlık mesajlaşma
- 🌐 **Çok Dilli**: Türkçe ve İngilizce arayüz
- 🔑 **Şifre Koruması**: Sunucu erişim kontrolü
- 👥 **Kullanıcı Yönetimi**: Gerçek zamanlı kullanıcı listesi ve durumu
- 🎨 **Modern Arayüz**: Koyu temalı, kullanıcı dostu tasarım
- 🔄 **Otomatik Yeniden Bağlanma**: Otomatik bağlantı kurtarma
- 📱 **Çapraz Platform**: Windows, Linux, macOS desteği

## 🔐 Güvenlik

- **RSA 2048-bit** anahtar değişimi için
- **AES 256-bit CFB** mesaj şifreleme için
- **Sıfır bilgi sunucusu**: Sunucu sadece şifreli veriyi aktarır
- **Mükemmel İleriye Dönük Gizlilik**: Her mesaj için yeni AES anahtarı
- **İstemci tarafı şifreleme**: Tüm şifreleme istemcilerde gerçekleşir

## 🚀 Hızlı Başlangıç

### Otomatik Kurulum

```bash
# Depoyu klonlayın
git clone https://github.com/yourusername/e2e-voice-chat.git
cd e2e-voice-chat

# Kurulum scriptini çalıştırın
python3 setup.py
```

Kurulum scripti şunları yapacak:
- ✅ Python sürümünü kontrol eder
- ✅ Sanal ortam oluşturur (önerilir)
- ✅ Tüm bağımlılıkları kurar
- ✅ Başlatma scriptleri oluşturur
- ✅ İsteğe bağlı olarak sunucu ve istemciyi başlatır

### Manuel Kurulum

```bash
# Sanal ortam oluştur
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# veya
venv\Scripts\activate  # Windows

# Bağımlılıkları kur
pip install cryptography pyaudio

# Linux için PortAudio gerekebilir:
sudo apt-get install portaudio19-dev python3-pyaudio  # Ubuntu/Debian
```

## 💻 Kullanım

### Sunucuyu Başlatma

```bash
# Başlatma scriptlerini kullanarak
./start_server.sh  # Linux/Mac
start_server.bat   # Windows

# Veya doğrudan
python3 chat_server.py
```

**Varsayılan şifre:** `fidelio`

### İstemciyi Başlatma

```bash
# Başlatma scriptlerini kullanarak
./start_client.sh  # Linux/Mac
start_client.bat   # Windows

# Veya doğrudan
python3 chat_client.py
```

### İstemci Arayüzü

1. **Bağlantı**: Sunucu IP, port ve kullanıcı adı girin
2. **Kimlik Doğrulama**: İstendiğinde sunucu şifresini girin
3. **Mesajlaşma**: Şifreli mesajlar yazın ve gönderin
4. **Sesli Aramalar**: Bir kullanıcı seçin ve "Ara" düğmesine tıklayın
5. **Dil**: Dil düğmesi ile İngilizce/Türkçe arasında geçiş yapın

## 🏗️ Mimari

### İstemci-Sunucu Modeli

```
İstemci A                  Sunucu                    İstemci B
    |                         |                          |
    |---[RSA Public Key]----->|                          |
    |                         |---[RSA Public Key]------>|
    |                         |                          |
    |<--[Şifreli Mesaj]-------|<--[Şifreli Mesaj]-------|
    |                         |                          |
    |-----[Ses Verisi]------->|-----[Ses Verisi]-------->|
```

### Şifreleme Akışı

1. **Anahtar Değişimi**: Her istemci başlangıçta RSA anahtar çifti oluşturur
2. **Public Key Dağıtımı**: Sunucu public anahtarları tüm istemcilere aktarır
3. **Mesaj Şifreleme**: Gönderen alıcının public anahtarı ile şifreler
4. **AES Şifreleme**: Her mesaj için rastgele AES anahtarı, RSA ile şifrelenir
5. **Ses Verisi**: Gerçek zamanlı ses sunucu röleleme ile iletilir

## 📁 Proje Yapısı

```
e2e-voice-chat/
├── chat_client.py      # GUI ile istemci uygulaması
├── chat_server.py      # Sunucu uygulaması
├── setup.py            # Otomatik kurulum scripti
├── README.md           # Bu dosya
├── LICENSE             # MIT Lisansı
└── requirements.txt    # Python bağımlılıkları (opsiyonel)
```

## ⚙️ Yapılandırma

### Sunucu Ayarları (chat_server.py)

```python
host = '0.0.0.0'           # Tüm arayüzlerde dinle
port = 12345               # Sunucu portu
password = "fidelio"       # Kimlik doğrulama şifresi
```

### İstemci Ayarları

- GUI üzerinden yapılandırılabilir:
  - Sunucu IP adresi
  - Sunucu portu
  - Kullanıcı takma adı
  - Dil tercihi

## 🔧 Bağımlılıklar

- **Python 3.7+**
- **cryptography**: RSA ve AES şifreleme
- **pyaudio**: Sesli aramalar için ses giriş/çıkış
- **tkinter**: GUI framework (genellikle önceden yüklü)

## 🐛 Sorun Giderme

### PyAudio Kurulum Sorunları

**Linux:**
```bash
sudo apt-get install portaudio19-dev python3-pyaudio
pip install pyaudio
```

**macOS:**
```bash
brew install portaudio
pip install pyaudio
```

**Windows:**
- Önceden derlenmiş wheel'i [buradan](https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio) indirin
- Şununla kurun: `pip install PyAudio‑0.2.11‑cp3X‑cp3Xm‑win_amd64.whl`

### Bağlantı Sorunları

- Güvenlik duvarı ayarlarını kontrol edin
- İstemcileri bağlamadan önce sunucunun çalıştığından emin olun
- Doğru IP adresi ve port'u doğrulayın
- Şifrenin doğru olduğunu kontrol edin

## 🤝 Katkıda Bulunma

Katkılar memnuniyetle karşılanır! Lütfen bir Pull Request göndermekten çekinmeyin.

1. Depoyu fork edin
2. Feature branch'inizi oluşturun (`git checkout -b feature/HarikaBirOzellik`)
3. Değişikliklerinizi commit edin (`git commit -m 'Harika bir özellik ekle'`)
4. Branch'inizi push edin (`git push origin feature/HarikaBirOzellik`)
5. Bir Pull Request açın

## 📝 Lisans

Bu proje MIT Lisansı altında lisanslanmıştır - detaylar için [LICENSE](LICENSE) dosyasına bakın.

## ⚠️ Sorumluluk Reddi

Bu uygulama eğitim amaçlı ve özel kullanım için tasarlanmıştır. Güçlü şifreleme uygulasa da, güvenlik profesyonelleri tarafından denetlenmemiştir. Hassas iletişimler için kendi sorumluluğunuzda kullanın.

## 🌟 Teşekkürler

- Python'un cryptography kütüphanesi ile geliştirilmiştir
- Gerçek zamanlı ses akışı için PyAudio kullanır
- Güvenli mesajlaşma prensiplerinden esinlenmiştir

---

<div align="center">

**Made with ❤️ for secure communication**

**Güvenli iletişim için ❤️ ile yapıldı**

</div>
