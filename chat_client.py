import tkinter as tk
from tkinter import scrolledtext, messagebox, simpledialog
import socket
import threading
import time
import json
import pyaudio
import base64
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import os
import datetime

LANG = {
    'tr': {'title': '🔒 Güvenli E2E Sesli Chat', 'connect': '🔗 Bağlan', 'disconnect': '🔌 Kes', 
           'connected': '✅ Bağlı | 🔐 E2E: Aktif', 'disconnected': '❌ Bağlı değil | 🔓 E2E: Pasif',
           'voice_call': '📞 Sesli Ara', 'end_call': '📞 Bitir', 'refresh': '🔄 Yenile', 'send': '📤 Gönder',
           'password_title': '🔒 Şifre', 'password_prompt': 'Şifre girin:', 'error': '❌ Hata',
           'enter_nickname': 'Kullanıcı adı girin!', 'connecting': '🔄 Bağlanılıyor...',
           'password_ok': '✅ Şifre doğru!', 'password_wrong': '❌ Yanlış şifre!',
           'success': '🎉 Bağlantı başarılı!', 'e2e_active': '🔐 E2E aktif!',
           'select_user': 'Kullanıcı seçin!', 'already_calling': 'Zaten aramada!',
           'incoming': 'Gelen Arama', 'incoming_text': ' arıyor!\n\nCevapla?',
           'started': ' ile arama başladı!', 'calling': '📞 Aranıyor...', 'warning': 'Uyarı'},
    'en': {'title': '🔒 Secure E2E Voice Chat', 'connect': '🔗 Connect', 'disconnect': '🔌 Disconnect',
           'connected': '✅ Connected | 🔐 E2E: Active', 'disconnected': '❌ Disconnected | 🔓 E2E: Inactive',
           'voice_call': '📞 Call', 'end_call': '📞 End Call', 'refresh': '🔄 Refresh', 'send': '📤 Send',
           'password_title': '🔒 Password', 'password_prompt': 'Enter password:', 'error': '❌ Error',
           'enter_nickname': 'Enter nickname!', 'connecting': '🔄 Connecting...',
           'password_ok': '✅ Password OK!', 'password_wrong': '❌ Wrong password!',
           'success': '🎉 Connected!', 'e2e_active': '🔐 E2E active!',
           'select_user': 'Select user!', 'already_calling': 'Already in call!',
           'incoming': 'Incoming Call', 'incoming_text': ' is calling!\n\nAnswer?',
           'started': ' call started!', 'calling': '📞 Calling...', 'warning': 'Warning'}
}

class ChatClient:
    def __init__(self):
        self.client = None
        self.nickname = None
        self.connected = False
        self.lang = 'en'
        
        self.private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048, backend=default_backend())
        self.public_key = self.private_key.public_key()
        self.peer_public_keys = {}
        
        self.audio = pyaudio.PyAudio()
        self.is_in_call = False
        self.current_call_id = None
        self.voice_send_thread = None
        self.audio_stream_in = None
        self.audio_stream_out = None
        
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 44100
        
        self.root = tk.Tk()
        self.root.title(LANG[self.lang]['title'])
        self.root.geometry("700x650")
        self.root.configure(bg='#1a1a2e')
        self.setup_gui()
        
    def t(self, k):
        return LANG[self.lang].get(k, k)
    
    def toggle_lang(self):
        self.lang = 'en' if self.lang == 'tr' else 'tr'
        self.root.title(self.t('title'))
        self.lang_btn.config(text=f"🌐 {self.lang.upper()}")
        self.connect_btn.config(text=self.t('disconnect') if self.connected else self.t('connect'))
        self.status_label.config(text=self.t('connected') if self.connected else self.t('disconnected'))
        self.call_btn.config(text=self.t('end_call') if self.is_in_call else self.t('voice_call'))
        self.refresh_btn.config(text=self.t('refresh'))
        self.send_btn.config(text=self.t('send'))
        
    def setup_gui(self):
        top = tk.Frame(self.root, bg='#16213e', relief='raised', bd=2)
        top.pack(fill=tk.X, pady=5, padx=5)
        
        self.lang_btn = tk.Button(top, text=f"🌐 {self.lang.upper()}", command=self.toggle_lang,
                                  bg='#34495e', fg='white', font=('Arial', 9, 'bold'), relief='flat')
        self.lang_btn.pack(pady=5)
        
        sf = tk.Frame(top, bg='#16213e')
        sf.pack(pady=5)
        tk.Label(sf, text="Server IP:", bg='#16213e', fg='white', font=('Arial', 10)).pack(side=tk.LEFT)
        self.server_ip = tk.Entry(sf, width=15)
        self.server_ip.pack(side=tk.LEFT, padx=5)
        self.server_ip.insert(0, "localhost")
        tk.Label(sf, text="Port:", bg='#16213e', fg='white', font=('Arial', 10)).pack(side=tk.LEFT, padx=(10,0))
        self.port = tk.Entry(sf, width=8)
        self.port.pack(side=tk.LEFT, padx=5)
        self.port.insert(0, "12345")
        
        nf = tk.Frame(top, bg='#16213e')
        nf.pack(pady=5)
        tk.Label(nf, text="Nickname:", bg='#16213e', fg='white', font=('Arial', 10)).pack(side=tk.LEFT)
        self.nick = tk.Entry(nf, width=15)
        self.nick.pack(side=tk.LEFT, padx=5)
        self.nick.insert(0, f"User{hash(self)%1000}")
        self.connect_btn = tk.Button(nf, text=self.t('connect'), command=self.toggle_conn,
                                     bg='#27ae60', fg='white', font=('Arial', 10, 'bold'), relief='flat', padx=20)
        self.connect_btn.pack(side=tk.LEFT, padx=10)
        
        self.status_label = tk.Label(self.root, text=self.t('disconnected'), 
                                     bg='#1a1a2e', fg='#e74c3c', font=('Arial', 10, 'bold'))
        self.status_label.pack(pady=5)
        
        main = tk.Frame(self.root, bg='#1a1a2e')
        main.pack(pady=5, padx=10, fill=tk.BOTH, expand=True)
        
        left = tk.Frame(main, bg='#1a1a2e')
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tk.Label(left, text="💬 Chat", bg='#1a1a2e', fg='white', font=('Arial', 12, 'bold')).pack(anchor='w')
        self.chat = scrolledtext.ScrolledText(left, wrap=tk.WORD, width=50, height=20, state=tk.DISABLED,
                                              bg='#0f3460', fg='#00ff00', font=('Consolas', 9))
        self.chat.pack(pady=5, fill=tk.BOTH, expand=True)
        
        right = tk.Frame(main, bg='#16213e', width=200)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(10,0))
        right.pack_propagate(False)
        tk.Label(right, text="👥 Users", bg='#16213e', fg='white', font=('Arial', 11, 'bold')).pack(pady=5)
        self.users = tk.Listbox(right, bg='#0f3460', fg='white', font=('Arial', 10), height=15, selectbackground='#533483')
        self.users.pack(pady=5, padx=5, fill=tk.BOTH, expand=True)
        self.call_btn = tk.Button(right, text=self.t('voice_call'), command=self.call,
                                 bg='#9b59b6', fg='white', font=('Arial', 10, 'bold'), relief='flat', state=tk.DISABLED)
        self.call_btn.pack(pady=5, padx=5, fill=tk.X)
        self.refresh_btn = tk.Button(right, text=self.t('refresh'), command=self.req_users,
                                     bg='#34495e', fg='white', font=('Arial', 9), relief='flat', state=tk.DISABLED)
        self.refresh_btn.pack(pady=2, padx=5, fill=tk.X)
        self.call_status = tk.Label(right, text="", bg='#16213e', fg='#3498db', font=('Arial', 9, 'italic'))
        self.call_status.pack(pady=5)
        
        bottom = tk.Frame(self.root, bg='#16213e', relief='raised', bd=2)
        bottom.pack(fill=tk.X, pady=5, padx=5)
        mf = tk.Frame(bottom, bg='#16213e')
        mf.pack(pady=10, padx=10, fill=tk.X)
        tk.Label(mf, text="✏️", bg='#16213e', fg='white', font=('Arial', 12)).pack(side=tk.LEFT)
        self.msg = tk.Entry(mf, state=tk.DISABLED, font=('Arial', 10), bg='#0f3460', fg='white', insertbackground='white')
        self.msg.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.msg.bind('<Return>', self.send)
        self.send_btn = tk.Button(mf, text=self.t('send'), command=self.send, state=tk.DISABLED,
                                 bg='#3498db', fg='white', font=('Arial', 10, 'bold'), relief='flat')
        self.send_btn.pack(side=tk.RIGHT)
        
        self.root.protocol("WM_DELETE_WINDOW", self.close)
    
    def get_key_pem(self):
        return self.public_key.public_bytes(encoding=serialization.Encoding.PEM,
                                           format=serialization.PublicFormat.SubjectPublicKeyInfo).decode('utf-8')
    
    def load_key(self, pem):
        return serialization.load_pem_public_key(pem.encode('utf-8'), backend=default_backend())
    
    def encrypt(self, msg, peer):
        if peer not in self.peer_public_keys:
            return None
        aes_key = os.urandom(32)
        iv = os.urandom(16)
        cipher = Cipher(algorithms.AES(aes_key), modes.CFB(iv), backend=default_backend())
        enc = cipher.encryptor()
        enc_msg = enc.update(msg.encode('utf-8')) + enc.finalize()
        enc_key = self.peer_public_keys[peer].encrypt(aes_key, padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None))
        return {'encrypted_key': base64.b64encode(enc_key).decode('utf-8'),
                'iv': base64.b64encode(iv).decode('utf-8'),
                'encrypted_message': base64.b64encode(enc_msg).decode('utf-8')}
    
    def decrypt(self, data):
        try:
            enc_key = base64.b64decode(data['encrypted_key'])
            aes_key = self.private_key.decrypt(enc_key, padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None))
            iv = base64.b64decode(data['iv'])
            enc_msg = base64.b64decode(data['encrypted_message'])
            cipher = Cipher(algorithms.AES(aes_key), modes.CFB(iv), backend=default_backend())
            dec = cipher.decryptor()
            return (dec.update(enc_msg) + dec.finalize()).decode('utf-8')
        except Exception as e:
            return f"[Decrypt error: {e}]"
    
    def toggle_conn(self):
        if not self.connected:
            self.connect()
        else:
            self.disconnect()
    
    def connect(self):
        try:
            ip = self.server_ip.get().strip() or "localhost"
            try:
                port = int(self.port.get().strip())
            except:
                port = 12345
            
            self.nickname = self.nick.get().strip()
            if not self.nickname:
                messagebox.showerror(self.t('error'), self.t('enter_nickname'))
                return
            
            if not hasattr(self, 'pwd'):
                pwd = simpledialog.askstring(self.t('password_title'), self.t('password_prompt'), show='*')
                if not pwd:
                    return
                self.pwd = pwd
            
            self.log(self.t('connecting'))
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client.settimeout(15)
            self.client.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            self.client.connect((ip, port))
            
            if self.client.recv(1024).decode('utf-8') == "PASSWORD":
                self.client.send(self.pwd.encode('utf-8'))
                result = self.client.recv(1024).decode('utf-8')
                if result == "AUTH_SUCCESS":
                    self.log(self.t('password_ok'))
                else:
                    self.log(self.t('password_wrong'))
                    self.client.close()
                    if hasattr(self, 'pwd'):
                        delattr(self, 'pwd')
                    return
            
            if self.client.recv(1024).decode('utf-8') == "NICK":
                self.client.send(self.nickname.encode('utf-8'))
            
            self.connected = True
            self.client.settimeout(None)
            
            threading.Thread(target=self.recv, daemon=True).start()
            threading.Thread(target=self.heartbeat, daemon=True).start()
            
            self.client.send((json.dumps({'type': 'public_key', 'nickname': self.nickname,
                                         'public_key': self.get_key_pem()}) + '\n').encode('utf-8'))
            
            self.update_ui()
            self.log(f"{self.t('success')} {ip}:{port}")
            self.log(self.t('e2e_active'))
            time.sleep(1.0)
            self.req_users()
        except Exception as e:
            self.log(f"Connection error: {e}")
    
    def req_users(self):
        if self.connected:
            try:
                self.client.send((json.dumps({'type': 'user_list_request'}) + '\n').encode('utf-8'))
            except:
                pass
    
    def heartbeat(self):
        while self.connected:
            try:
                time.sleep(10)
                if self.connected and self.client:
                    self.client.send("PING\n".encode('utf-8'))
            except:
                if self.connected:
                    self.conn_lost()
                break
    
    def process(self, msg):
        if not msg or msg in ["PING", "PONG"]:
            if msg == "PING":
                try:
                    self.client.send("PONG\n".encode('utf-8'))
                except:
                    pass
            return
        
        try:
            data = json.loads(msg)
            t = data.get('type')
            
            if t == 'public_key':
                nick = data.get('nickname')
                key = data.get('public_key')
                if nick and key:
                    try:
                        self.peer_public_keys[nick] = self.load_key(key)
                        self.log(f"🔑 {nick} - key received")
                    except Exception as e:
                        self.log(f"❌ {nick} key error: {e}")
            elif t == 'encrypted_message':
                self.log(f"🔒 {data.get('sender')}: {self.decrypt(data.get('data'))}")
            elif t == 'user_list':
                self.update_users(data.get('users', []))
            elif t == 'incoming_call':
                self.incoming(data.get('caller'), data.get('call_id'))
            elif t == 'call_response':
                s = data.get('status')
                if s == 'calling':
                    self.call_status.config(text=self.t('calling'))
                elif s in ['user_not_found', 'user_busy']:
                    messagebox.showerror(self.t('error') if s == 'user_not_found' else self.t('warning'), data.get('message'))
                    self.call_status.config(text="")
            elif t == 'call_started':
                self.start_call(data.get('peer'), data.get('call_id'))
            elif t == 'call_ended':
                self.end_call(data.get('reason'))
            elif t == 'voice_data':
                if self.is_in_call and self.audio_stream_out:
                    self.audio_stream_out.write(base64.b64decode(data.get('audio_data')))
        except json.JSONDecodeError:
            if not msg.startswith("{"):
                self.log(msg)
    
    def recv(self):
        buf = ""
        while self.connected:
            try:
                data = self.client.recv(4096).decode('utf-8')
                if not data:
                    self.conn_lost()
                    break
                buf += data
                while '\n' in buf:
                    line, buf = buf.split('\n', 1)
                    if line.strip():
                        self.process(line.strip())
            except:
                if self.connected:
                    pass
                break
    
    def update_users(self, users):
        self.users.delete(0, tk.END)
        for u in users:
            icon = "🟢" if u.get('status', 'idle') == 'idle' else "🔴"
            self.users.insert(tk.END, f"{icon} {u.get('nickname')}")
    
    def call(self):
        sel = self.users.curselection()
        if not sel:
            messagebox.showwarning(self.t('warning'), self.t('select_user'))
            return
        target = self.users.get(sel[0]).split(" ", 1)[1]
        if self.is_in_call:
            messagebox.showwarning(self.t('warning'), self.t('already_calling'))
            return
        try:
            self.client.send(json.dumps({'type': 'call_request', 'target': target}).encode('utf-8'))
            self.call_status.config(text=f"📞 {target} {self.t('calling')}")
        except Exception as e:
            messagebox.showerror(self.t('error'), f"Call error: {e}")
    
    def incoming(self, caller, cid):
        resp = messagebox.askyesno(self.t('incoming'), f"📞 {caller}{self.t('incoming_text')}")
        try:
            self.client.send(json.dumps({'type': 'call_answer', 'call_id': cid,
                                        'action': 'accept' if resp else 'reject'}).encode('utf-8'))
            if resp:
                self.call_status.config(text=f"📞 {caller}...")
        except Exception as e:
            self.log(f"Answer error: {e}")
    
    def start_call(self, peer, cid):
        self.is_in_call = True
        self.current_call_id = cid
        self.log(f"🎙️ {peer}{self.t('started')}")
        self.call_status.config(text=f"🔴 {peer}", fg='#e74c3c')
        self.call_btn.config(text=self.t('end_call'), command=self.end_call_btn, bg='#e74c3c')
        
        try:
            self.audio_stream_in = self.audio.open(format=self.FORMAT, channels=self.CHANNELS, rate=self.RATE,
                                                   input=True, frames_per_buffer=self.CHUNK)
            self.audio_stream_out = self.audio.open(format=self.FORMAT, channels=self.CHANNELS, rate=self.RATE,
                                                    output=True, frames_per_buffer=self.CHUNK)
            self.voice_send_thread = threading.Thread(target=self.send_audio, daemon=True)
            self.voice_send_thread.start()
        except Exception as e:
            self.log(f"Audio error: {e}")
            self.end_call("error")
    
    def send_audio(self):
        while self.is_in_call:
            try:
                if not self.audio_stream_in or not self.is_in_call:
                    break
                data = self.audio_stream_in.read(self.CHUNK, exception_on_overflow=False)
                if not self.is_in_call:
                    break
                if self.connected and self.client:
                    self.client.send((json.dumps({'type': 'voice_data', 'call_id': self.current_call_id,
                                                  'audio_data': base64.b64encode(data).decode('utf-8')}) + '\n').encode('utf-8'))
                else:
                    break
            except:
                break
    
    def end_call_btn(self):
        if self.is_in_call:
            try:
                self.client.send(json.dumps({'type': 'call_end', 'call_id': self.current_call_id}).encode('utf-8'))
            except:
                pass
    
    def end_call(self, reason):
        if not self.is_in_call:
            return
        
        self.is_in_call = False
        
        if self.voice_send_thread and self.voice_send_thread.is_alive():
            try:
                self.voice_send_thread.join(timeout=2.0)
            except:
                pass
        
        if self.audio_stream_in:
            try:
                self.audio_stream_in.stop_stream()
                self.audio_stream_in.close()
            except:
                pass
            self.audio_stream_in = None
        
        if self.audio_stream_out:
            try:
                self.audio_stream_out.stop_stream()
                self.audio_stream_out.close()
            except:
                pass
            self.audio_stream_out = None
        
        reasons = {'ended': 'Call ended', 'rejected': 'Rejected', 'timeout': 'Timeout',
                  'disconnected': 'Disconnected', 'error': 'Error'}
        self.log(f"📞 {reasons.get(reason, 'Call finished')}")
        
        try:
            self.call_status.config(text="", fg='#3498db')
            self.call_btn.config(text=self.t('voice_call'), command=self.call, bg='#9b59b6')
        except:
            pass
        
        self.current_call_id = None
        try:
            if self.connected:
                self.req_users()
        except:
            pass
    
    def send(self, e=None):
        if self.connected and self.client:
            m = self.msg.get().strip()
            if m:
                try:
                    if m.lower() == "/quit":
                        self.disconnect()
                        return
                    self.log(f"🔒 {self.t('you') if self.lang == 'en' else 'Sen'}: {m}")
                    self.msg.delete(0, tk.END)
                    sent = 0
                    for peer in list(self.peer_public_keys.keys()):
                        enc = self.encrypt(m, peer)
                        if enc:
                            self.client.send((json.dumps({'type': 'encrypted_message', 'sender': self.nickname,
                                                         'target': peer, 'data': enc}) + '\n').encode('utf-8'))
                            sent += 1
                    if sent == 0:
                        self.log("⚠️ No keys available!")
                except Exception as e:
                    self.log(f"Send error: {e}")
    
    def conn_lost(self):
        self.log("⚠️ Connection lost!")
        self.connected = False
        if self.is_in_call:
            self.end_call("disconnected")
        self.update_ui()
        if self.client:
            try:
                self.client.close()
            except:
                pass
    
    def disconnect(self):
        self.connected = False
        if self.is_in_call:
            self.end_call("ended")
        if self.client:
            try:
                self.client.shutdown(socket.SHUT_RDWR)
                self.client.close()
            except:
                pass
        self.update_ui()
        self.log("🔌 Disconnected.")
    
    def update_ui(self):
        if self.connected:
            self.connect_btn.config(text=self.t('disconnect'), bg='#e74c3c')
            self.server_ip.config(state=tk.DISABLED)
            self.port.config(state=tk.DISABLED)
            self.nick.config(state=tk.DISABLED)
            self.msg.config(state=tk.NORMAL)
            self.send_btn.config(state=tk.NORMAL)
            self.call_btn.config(state=tk.NORMAL)
            self.refresh_btn.config(state=tk.NORMAL)
            self.msg.focus()
            self.status_label.config(text=self.t('connected'), fg='#27ae60')
        else:
            self.connect_btn.config(text=self.t('connect'), bg='#27ae60')
            self.server_ip.config(state=tk.NORMAL)
            self.port.config(state=tk.NORMAL)
            self.nick.config(state=tk.NORMAL)
            self.msg.config(state=tk.DISABLED)
            self.send_btn.config(state=tk.DISABLED)
            self.call_btn.config(state=tk.DISABLED)
            self.refresh_btn.config(state=tk.DISABLED)
            self.status_label.config(text=self.t('disconnected'), fg='#e74c3c')
    
    def log(self, msg):
        self.chat.config(state=tk.NORMAL)
        self.chat.insert(tk.END, f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {msg}\n")
        self.chat.config(state=tk.DISABLED)
        self.chat.see(tk.END)
    
    def close(self):
        if self.is_in_call:
            self.end_call("ended")
            time.sleep(0.5)
        if self.connected:
            self.disconnect()
            time.sleep(0.2)
        try:
            if hasattr(self, 'audio'):
                self.audio.terminate()
        except:
            pass
        try:
            self.root.destroy()
        except:
            pass
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    ChatClient().run()
