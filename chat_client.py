import tkinter as tk
from tkinter import scrolledtext, messagebox, simpledialog
import socket
import threading
import time

class ChatClient:
    def __init__(self):
        self.client = None
        self.nickname = None
        self.connected = False
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        self.heartbeat_thread = None
        self.receive_thread = None
        
        # Ana pencere
        self.root = tk.Tk()
        self.root.title("🔒 Secure Python Chat Client")
        self.root.geometry("600x500")
        self.root.configure(bg='#2c3e50')
        
        self.setup_gui()
        
    def setup_gui(self):
        # Üst frame - bağlantı ayarları
        top_frame = tk.Frame(self.root, bg='#34495e', relief='raised', bd=1)
        top_frame.pack(fill=tk.X, pady=5, padx=5)
        
        # Server IP ve Port
        server_frame = tk.Frame(top_frame, bg='#34495e')
        server_frame.pack(pady=5)
        
        tk.Label(server_frame, text="Server IP:", bg='#34495e', fg='white', font=('Arial', 10)).pack(side=tk.LEFT)
        self.server_ip_entry = tk.Entry(server_frame, width=15)
        self.server_ip_entry.pack(side=tk.LEFT, padx=5)
        self.server_ip_entry.insert(0, "localhost")
        
        tk.Label(server_frame, text="Port:", bg='#34495e', fg='white', font=('Arial', 10)).pack(side=tk.LEFT, padx=(10,0))
        self.port_entry = tk.Entry(server_frame, width=8)
        self.port_entry.pack(side=tk.LEFT, padx=5)
        self.port_entry.insert(0, "12345")
        
        # Nickname
        nick_frame = tk.Frame(top_frame, bg='#34495e')
        nick_frame.pack(pady=5)
        
        tk.Label(nick_frame, text="Nickname:", bg='#34495e', fg='white', font=('Arial', 10)).pack(side=tk.LEFT)
        self.nickname_entry = tk.Entry(nick_frame, width=15)
        self.nickname_entry.pack(side=tk.LEFT, padx=5)
        self.nickname_entry.insert(0, f"User{hash(self) % 1000}")
        
        self.connect_btn = tk.Button(nick_frame, text="🔗 Bağlan", command=self.toggle_connection,
                                   bg='#27ae60', fg='white', font=('Arial', 10, 'bold'),
                                   relief='flat', padx=20)
        self.connect_btn.pack(side=tk.LEFT, padx=10)
        
        # Auto-reconnect checkbox
        self.auto_reconnect_var = tk.BooleanVar(value=True)
        auto_reconnect_cb = tk.Checkbutton(nick_frame, text="🔄 Otomatik yeniden bağlan", 
                                         variable=self.auto_reconnect_var,
                                         bg='#34495e', fg='white', selectcolor='#34495e')
        auto_reconnect_cb.pack(side=tk.LEFT, padx=10)
        
        # Status label
        self.status_label = tk.Label(self.root, text="❌ Bağlı değil", 
                                   bg='#2c3e50', fg='#e74c3c', font=('Arial', 10, 'bold'))
        self.status_label.pack(pady=5)
        
        # Chat alanı
        chat_frame = tk.Frame(self.root, bg='#2c3e50')
        chat_frame.pack(pady=5, padx=10, fill=tk.BOTH, expand=True)
        
        tk.Label(chat_frame, text="💬 Chat", bg='#2c3e50', fg='white', 
                font=('Arial', 12, 'bold')).pack(anchor='w')
        
        self.chat_display = scrolledtext.ScrolledText(
            chat_frame, 
            wrap=tk.WORD, 
            width=70, 
            height=20,
            state=tk.DISABLED,
            bg='#ecf0f1',
            fg='#2c3e50',
            font=('Consolas', 10)
        )
        self.chat_display.pack(pady=5, fill=tk.BOTH, expand=True)
        
        # Alt frame - mesaj gönderme
        bottom_frame = tk.Frame(self.root, bg='#34495e', relief='raised', bd=1)
        bottom_frame.pack(fill=tk.X, pady=5, padx=5)
        
        msg_frame = tk.Frame(bottom_frame, bg='#34495e')
        msg_frame.pack(pady=10, padx=10, fill=tk.X)
        
        tk.Label(msg_frame, text="✍️", bg='#34495e', fg='white', font=('Arial', 12)).pack(side=tk.LEFT)
        
        self.message_entry = tk.Entry(msg_frame, state=tk.DISABLED, font=('Arial', 10))
        self.message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.message_entry.bind('<Return>', self.send_message)
        
        self.send_btn = tk.Button(msg_frame, text="📤 Gönder", command=self.send_message, 
                                state=tk.DISABLED, bg='#3498db', fg='white', 
                                font=('Arial', 10, 'bold'), relief='flat')
        self.send_btn.pack(side=tk.RIGHT)
        
        # Pencere kapatma
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def toggle_connection(self):
        if not self.connected:
            self.connect_to_server()
        else:
            self.disconnect()
    
    def get_password(self):
        """Kullanıcıdan şifre al"""
        password = simpledialog.askstring("🔒 Chat Şifresi", 
                                        "Chat'e girmek için şifre girin:", 
                                        show='*')
        return password
    
    def connect_to_server(self):
        try:
            # Bağlantı bilgilerini al
            server_ip = self.server_ip_entry.get().strip()
            if not server_ip:
                server_ip = "localhost"
            
            try:
                port = int(self.port_entry.get().strip())
            except:
                port = 12345
            
            self.nickname = self.nickname_entry.get().strip()
            if not self.nickname:
                messagebox.showerror("❌ Hata", "Lütfen bir nickname girin!")
                return
            
            # Şifre al (sadece ilk bağlantıda)
            if not hasattr(self, 'saved_password'):
                password = self.get_password()
                if not password:
                    return
                self.saved_password = password
            
            self.add_message("🔄 Server'a bağlanılıyor...")
            
            # Socket bağlantısı
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client.settimeout(15)  # Timeout artırıldı
            
            # Keep-alive ayarları (bağlantının canlı kalması için)
            self.client.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            
            self.client.connect((server_ip, port))
            
            # Şifre doğrulaması
            auth_response = self.client.recv(1024).decode('utf-8')
            if auth_response == "PASSWORD":
                self.client.send(self.saved_password.encode('utf-8'))
                
                auth_result = self.client.recv(1024).decode('utf-8')
                if auth_result == "AUTH_SUCCESS":
                    self.add_message("✅ Şifre doğrulandı!")
                elif auth_result == "AUTH_FAILED":
                    self.add_message("❌ Yanlış şifre!")
                    self.client.close()
                    # Şifreyi sıfırla, tekrar girilsin
                    if hasattr(self, 'saved_password'):
                        delattr(self, 'saved_password')
                    return
            
            self.connected = True
            self.reconnect_attempts = 0  # Başarılı bağlantıda sıfırla
            self.update_ui()
            
            # Timeout'u kaldır (bağlantı kurulduktan sonra)
            self.client.settimeout(None)
            
            # Mesaj dinleyici thread
            self.receive_thread = threading.Thread(target=self.receive_messages)
            self.receive_thread.daemon = True
            self.receive_thread.start()
            
            # Heartbeat thread (bağlantı kontrolü için)
            self.heartbeat_thread = threading.Thread(target=self.heartbeat)
            self.heartbeat_thread.daemon = True
            self.heartbeat_thread.start()
            
            self.add_message(f"🎉 {server_ip}:{port} adresine başarıyla bağlandı!")
            
        except socket.timeout:
            self.add_message("⏰ Zaman aşımı - Server'a bağlantı zaman aştı!")
            self.try_reconnect()
        except ConnectionRefusedError:
            self.add_message(f"🚫 Bağlantı reddedildi - {server_ip}:{port} aktif değil")
            self.try_reconnect()
        except Exception as e:
            self.add_message(f"💥 Bağlantı hatası: {str(e)}")
            self.try_reconnect()
    
    def heartbeat(self):
        """Bağlantının canlı olup olmadığını kontrol et"""
        while self.connected:
            try:
                time.sleep(10)  # 10 saniyede bir kontrol
                if self.connected and self.client:
                    # Küçük bir test mesajı gönder
                    self.client.send("PING".encode('utf-8'))
            except:
                if self.connected:
                    self.add_message("💔 Heartbeat başarısız - Bağlantı sorunu tespit edildi")
                    self.handle_connection_lost()
                break
    
    def receive_messages(self):
        while self.connected:
            try:
                message = self.client.recv(1024).decode('utf-8')
                
                if not message:  # Boş mesaj = bağlantı kapandı
                    self.handle_connection_lost()
                    break
                
                if message == "NICK":
                    # Server nickname istiyor
                    self.client.send(self.nickname.encode('utf-8'))
                elif message == "PING":
                    # Heartbeat'e cevap ver
                    self.client.send("PONG".encode('utf-8'))
                elif message != "PONG":  # PONG mesajlarını gösterme
                    # Normal mesaj
                    self.add_message(message)
                    
            except socket.error as e:
                if self.connected:
                    self.add_message(f"📡 Veri alma hatası: {str(e)}")
                    self.handle_connection_lost()
                break
            except Exception as e:
                if self.connected:
                    self.add_message(f"⚠️ Beklenmeyen hata: {str(e)}")
                    self.handle_connection_lost()
                break
    
    def handle_connection_lost(self):
        """Bağlantı kaybedildiğinde yapılacaklar"""
        self.add_message("⚠️ Bağlantı kesildi!")
        self.connected = False
        self.update_ui()
        
        if self.client:
            try:
                self.client.close()
            except:
                pass
        
        # Otomatik yeniden bağlanma
        if self.auto_reconnect_var.get():
            self.try_reconnect()
    
    def try_reconnect(self):
        """Otomatik yeniden bağlanma"""
        if self.reconnect_attempts < self.max_reconnect_attempts:
            self.reconnect_attempts += 1
            wait_time = min(5 * self.reconnect_attempts, 30)  # 5, 10, 15, 20, 25, 30 saniye
            
            self.add_message(f"🔄 {wait_time} saniye sonra yeniden bağlanma denemesi ({self.reconnect_attempts}/{self.max_reconnect_attempts})")
            
            # Non-blocking wait
            self.root.after(wait_time * 1000, self.connect_to_server)
        else:
            self.add_message("❌ Maksimum yeniden bağlanma denemesi aşıldı")
            self.reconnect_attempts = 0
    
    def send_message(self, event=None):
        if self.connected and self.client:
            message = self.message_entry.get().strip()
            if message:
                try:
                    if message.lower() == "/quit":
                        self.disconnect()
                        return
                    
                    full_message = f"{self.nickname}: {message}"
                    self.client.send(full_message.encode('utf-8'))
                    self.add_message(f"🗨️ {full_message}")
                    self.message_entry.delete(0, tk.END)
                        
                except socket.error as e:
                    self.add_message(f"❌ Mesaj gönderilemedi: {str(e)}")
                    self.handle_connection_lost()
                except Exception as e:
                    self.add_message(f"❌ Beklenmeyen hata: {str(e)}")
    
    def disconnect(self):
        self.connected = False
        self.reconnect_attempts = 0
        
        if self.client:
            try:
                self.client.shutdown(socket.SHUT_RDWR)  # Güvenli kapatma
                self.client.close()
            except:
                pass
        
        self.update_ui()
        self.add_message("🔌 Bağlantı kesildi.")
    
    def update_ui(self):
        if self.connected:
            self.connect_btn.config(text="🔌 Bağlantıyı Kes", bg='#e74c3c')
            self.server_ip_entry.config(state=tk.DISABLED)
            self.port_entry.config(state=tk.DISABLED)
            self.nickname_entry.config(state=tk.DISABLED)
            self.message_entry.config(state=tk.NORMAL)
            self.send_btn.config(state=tk.NORMAL)
            self.message_entry.focus()
            self.status_label.config(text="✅ Bağlı", fg='#27ae60')
        else:
            self.connect_btn.config(text="🔗 Bağlan", bg='#27ae60')
            self.server_ip_entry.config(state=tk.NORMAL)
            self.port_entry.config(state=tk.NORMAL)
            self.nickname_entry.config(state=tk.NORMAL)
            self.message_entry.config(state=tk.DISABLED)
            self.send_btn.config(state=tk.DISABLED)
            self.status_label.config(text="❌ Bağlı değil", fg='#e74c3c')
    
    def add_message(self, message):
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, f"[{self.get_timestamp()}] {message}\n")
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)
    
    def get_timestamp(self):
        import datetime
        return datetime.datetime.now().strftime("%H:%M:%S")
    
    def on_closing(self):
        if self.connected:
            self.disconnect()
        self.root.destroy()
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    client = ChatClient()
    client.run()