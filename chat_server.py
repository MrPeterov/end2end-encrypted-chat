import socket
import threading
import time
import json
import uuid
from datetime import datetime

class ChatServer:
    def __init__(self, host='0.0.0.0', port=12345):
        self.host = host
        self.port = port
        self.clients = []
        self.nicknames = []
        self.client_threads = []
        self.password = "fidelio"  # Chat şifresi
        self.server_running = True
        
        # Sesli arama özellikleri
        self.active_calls = {}  # call_id -> {'caller': client, 'callee': client, 'status': 'ringing/active/ended'}
        self.client_call_status = {}  # client -> {'status': 'idle/calling/in_call', 'call_id': '...'}
        
    def authenticate_client(self, client):
        """Client şifre doğrulaması"""
        try:
            # Şifre iste
            client.send("PASSWORD".encode('utf-8'))
            client.settimeout(30)  # 30 saniye timeout
            received_password = client.recv(1024).decode('utf-8')
            
            if received_password == self.password:
                client.send("AUTH_SUCCESS".encode('utf-8'))
                return True
            else:
                client.send("AUTH_FAILED".encode('utf-8'))
                return False
        except Exception as e:
            print(f"⚠️ Doğrulama hatası: {e}")
            return False
    
    def broadcast(self, message, sender_client=None):
        """Tüm client'lara mesaj gönder"""
        disconnected_clients = []
        
        for client in self.clients[:]:  # Liste kopyası üzerinde çalış
            if client != sender_client:
                try:
                    client.send(message)
                except:
                    disconnected_clients.append(client)
        
        # Bağlantısı kopan client'ları temizle
        for client in disconnected_clients:
            self.remove_client(client)
    
    def send_to_client(self, target_client, message):
        """Belirli bir client'a mesaj gönder"""
        try:
            if isinstance(message, str):
                message = message.encode('utf-8')
            target_client.send(message)
            return True
        except:
            self.remove_client(target_client)
            return False
    
    def get_client_by_nickname(self, nickname):
        """Nickname'e göre client bul"""
        try:
            index = self.nicknames.index(nickname)
            return self.clients[index]
        except:
            return None
    
    def get_nickname_by_client(self, client):
        """Client'a göre nickname bul"""
        try:
            index = self.clients.index(client)
            return self.nicknames[index]
        except:
            return "Bilinmeyen"
    
    def handle_call_request(self, caller_client, data):
        """Arama isteğini işle"""
        try:
            caller_nick = self.get_nickname_by_client(caller_client)
            target_nick = data.get('target')
            target_client = self.get_client_by_nickname(target_nick)
            
            if not target_client:
                # Hedef kullanıcı bulunamadı
                response = {
                    'type': 'call_response',
                    'status': 'user_not_found',
                    'message': f'{target_nick} kullanıcısı bulunamadı'
                }
                self.send_to_client(caller_client, json.dumps(response))
                return
            
            # Hedef kullanıcının durumunu kontrol et
            target_status = self.client_call_status.get(target_client, {}).get('status', 'idle')
            if target_status != 'idle':
                response = {
                    'type': 'call_response',
                    'status': 'user_busy',
                    'message': f'{target_nick} şu anda meşgul'
                }
                self.send_to_client(caller_client, json.dumps(response))
                return
            
            # Arama oluştur
            call_id = str(uuid.uuid4())
            self.active_calls[call_id] = {
                'caller': caller_client,
                'callee': target_client,
                'caller_nick': caller_nick,
                'callee_nick': target_nick,
                'status': 'ringing',
                'start_time': time.time()
            }
            
            # Client durumlarını güncelle
            self.client_call_status[caller_client] = {'status': 'calling', 'call_id': call_id}
            self.client_call_status[target_client] = {'status': 'ringing', 'call_id': call_id}
            
            # Arayan'a arama başladı mesajı
            response = {
                'type': 'call_response',
                'status': 'calling',
                'target': target_nick,
                'call_id': call_id
            }
            self.send_to_client(caller_client, json.dumps(response))
            
            # Aranan'a gelen arama bildirimi
            incoming_call = {
                'type': 'incoming_call',
                'caller': caller_nick,
                'call_id': call_id
            }
            self.send_to_client(target_client, json.dumps(incoming_call))
            
            print(f"📞 Arama başlatıldı: {caller_nick} -> {target_nick}")
            
            # 30 saniye sonra cevaplanmazsa aramayı sonlandır
            timer = threading.Timer(30.0, self.timeout_call, [call_id])
            timer.start()
            
        except Exception as e:
            print(f"⚠️ Arama isteği hatası: {e}")
    
    def handle_call_answer(self, client, data):
        """Arama cevaplama"""
        try:
            call_id = data.get('call_id')
            action = data.get('action')  # 'accept' veya 'reject'
            
            if call_id not in self.active_calls:
                return
            
            call_info = self.active_calls[call_id]
            caller_client = call_info['caller']
            caller_nick = call_info['caller_nick']
            callee_nick = call_info['callee_nick']
            
            if action == 'accept':
                # Aramayı kabul et
                call_info['status'] = 'active'
                self.client_call_status[caller_client]['status'] = 'in_call'
                self.client_call_status[client]['status'] = 'in_call'
                
                # Her iki tarafa da arama başladı bilgisi
                call_started = {
                    'type': 'call_started',
                    'call_id': call_id,
                    'peer': caller_nick if client != caller_client else callee_nick
                }
                
                self.send_to_client(caller_client, json.dumps(call_started))
                call_started['peer'] = callee_nick
                self.send_to_client(client, json.dumps(call_started))
                
                print(f"✅ Arama kabul edildi: {caller_nick} <-> {callee_nick}")
                
            else:  # reject
                # Aramayı reddet
                self.end_call(call_id, 'rejected')
                print(f"❌ Arama reddedildi: {caller_nick} -> {callee_nick}")
                
        except Exception as e:
            print(f"⚠️ Arama cevaplama hatası: {e}")
    
    def handle_call_end(self, client, data):
        """Arama sonlandırma"""
        try:
            call_id = data.get('call_id')
            self.end_call(call_id, 'ended')
        except Exception as e:
            print(f"⚠️ Arama sonlandırma hatası: {e}")
    
    def end_call(self, call_id, reason='ended'):
        """Aramayı sonlandır"""
        try:
            if call_id not in self.active_calls:
                return
            
            call_info = self.active_calls[call_id]
            caller_client = call_info['caller']
            callee_client = call_info['callee']
            
            # Client durumlarını temizle
            if caller_client in self.client_call_status:
                self.client_call_status[caller_client] = {'status': 'idle'}
            if callee_client in self.client_call_status:
                self.client_call_status[callee_client] = {'status': 'idle'}
            
            # Her iki tarafa da arama sonlandı mesajı
            call_ended = {
                'type': 'call_ended',
                'call_id': call_id,
                'reason': reason
            }
            
            self.send_to_client(caller_client, json.dumps(call_ended))
            self.send_to_client(callee_client, json.dumps(call_ended))
            
            # Arama kaydını sil
            del self.active_calls[call_id]
            
            print(f"📞 Arama sonlandı: {call_info['caller_nick']} <-> {call_info['callee_nick']} ({reason})")
            
        except Exception as e:
            print(f"⚠️ Arama sonlandırma hatası: {e}")
    
    def timeout_call(self, call_id):
        """Arama zaman aşımı"""
        if call_id in self.active_calls and self.active_calls[call_id]['status'] == 'ringing':
            self.end_call(call_id, 'timeout')
    
    def handle_voice_data(self, sender_client, data):
        """Sesli arama verilerini aktar"""
        try:
            call_id = data.get('call_id')
            if call_id not in self.active_calls:
                return
            
            call_info = self.active_calls[call_id]
            if call_info['status'] != 'active':
                return
            
            # Ses verisini karşı tarafa gönder
            if sender_client == call_info['caller']:
                target_client = call_info['callee']
            else:
                target_client = call_info['caller']
            
            voice_packet = {
                'type': 'voice_data',
                'call_id': call_id,
                'audio_data': data.get('audio_data')
            }
            
            self.send_to_client(target_client, json.dumps(voice_packet))
            
        except Exception as e:
            print(f"⚠️ Ses verisi aktarım hatası: {e}")
    
    def handle_user_list_request(self, client):
        """Aktif kullanıcı listesi gönder"""
        try:
            current_nick = self.get_nickname_by_client(client)
            user_list = []
            
            for i, nick in enumerate(self.nicknames):
                if nick != current_nick:  # Kendini listede gösterme
                    client_obj = self.clients[i]
                    status = self.client_call_status.get(client_obj, {}).get('status', 'idle')
                    user_list.append({
                        'nickname': nick,
                        'status': status
                    })
            
            response = {
                'type': 'user_list',
                'users': user_list
            }
            
            self.send_to_client(client, json.dumps(response))
            
        except Exception as e:
            print(f"⚠️ Kullanıcı listesi hatası: {e}")
    
    def remove_client(self, client):
        """Client'ı güvenli şekilde kaldır"""
        try:
            # Aktif aramaları sonlandır
            client_status = self.client_call_status.get(client, {})
            if client_status.get('status') in ['calling', 'in_call', 'ringing']:
                call_id = client_status.get('call_id')
                if call_id:
                    self.end_call(call_id, 'disconnected')
            
            # Client durumunu temizle
            if client in self.client_call_status:
                del self.client_call_status[client]
            
            if client in self.clients:
                index = self.clients.index(client)
                self.clients.remove(client)
                
                if index < len(self.nicknames):
                    nickname = self.nicknames[index]
                    self.nicknames.remove(nickname)
                    
                    # Diğerlerine haber ver
                    try:
                        self.broadcast(f"👋 {nickname} chat'ten ayrıldı!".encode('utf-8'))
                        print(f"👋 {nickname} bağlantısı kesildi")
                    except:
                        pass
                
                try:
                    client.close()
                except:
                    pass
                    
        except Exception as e:
            print(f"⚠️ Client kaldırma hatası: {e}")
    
    def handle_client(self, client):
        """Client mesajlarını dinle"""
        nickname = "Bilinmeyen"
        last_activity = time.time()
        
        try:
            # Client'ı idle durumda başlat
            self.client_call_status[client] = {'status': 'idle'}
            
            while self.server_running:
                try:
                    client.settimeout(1.0)  # 1 saniye timeout
                    message = client.recv(8192)  # Buffer boyutu artırıldı
                    
                    if message:
                        decoded_message = message.decode('utf-8')
                        last_activity = time.time()
                        
                        # Heartbeat kontrolü
                        if decoded_message == "PING":
                            client.send("PONG".encode('utf-8'))
                            continue
                        elif decoded_message == "PONG":
                            continue
                        
                        # JSON mesaj kontrolü
                        try:
                            msg_data = json.loads(decoded_message)
                            msg_type = msg_data.get('type')
                            
                            if msg_type == 'call_request':
                                self.handle_call_request(client, msg_data)
                            elif msg_type == 'call_answer':
                                self.handle_call_answer(client, msg_data)
                            elif msg_type == 'call_end':
                                self.handle_call_end(client, msg_data)
                            elif msg_type == 'voice_data':
                                self.handle_voice_data(client, msg_data)
                            elif msg_type == 'user_list_request':
                                self.handle_user_list_request(client)
                            elif msg_type == 'voice':
                                # Ses mesajını diğer client'lara gönder
                                self.broadcast(message, client)
                            else:
                                # Bilinmeyen JSON mesajı - normal mesaj olarak işle
                                self.broadcast(message, client)
                                print(f"📨 JSON Mesaj: {decoded_message[:100]}...")
                            
                        except json.JSONDecodeError:
                            # Normal metin mesajı
                            self.broadcast(message, client)
                            print(f"📨 Mesaj: {decoded_message}")
                        
                    else:
                        # Boş mesaj = client bağlantısı kapandı
                        print(f"⚠️ {nickname} boş mesaj gönderdi (bağlantı koptu)")
                        break
                        
                except socket.timeout:
                    # Timeout normal, devam et
                    # Uzun süre mesaj alınmadıysa kontrol et
                    if time.time() - last_activity > 60:  # 60 saniye
                        print(f"⏰ {nickname} uzun süre pasif, bağlantı kontrol ediliyor")
                        try:
                            client.send("PING".encode('utf-8'))
                            last_activity = time.time()
                        except:
                            print(f"💔 {nickname} heartbeat başarısız")
                            break
                    continue
                    
                except ConnectionResetError:
                    print(f"🔌 {nickname} bağlantısını kapattı")
                    break
                    
                except Exception as e:
                    print(f"⚠️ {nickname} mesaj alma hatası: {e}")
                    break
                    
        except Exception as e:
            print(f"💥 {nickname} için kritik hata: {e}")
        finally:
            self.remove_client(client)
    
    def get_server_ip(self):
        """Server'ın IP adresini al"""
        try:
            # İnternet bağlantısı üzerinden IP'yi al
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "localhost"
    
    def cleanup_disconnected_clients(self):
        """Periyodik olarak kopuk bağlantıları temizle"""
        while self.server_running:
            try:
                time.sleep(30)  # 30 saniyede bir kontrol
                
                disconnected_clients = []
                for client in self.clients[:]:
                    try:
                        # Test mesajı gönder
                        client.send("PING".encode('utf-8'))
                    except:
                        disconnected_clients.append(client)
                
                for client in disconnected_clients:
                    print("🧹 Kopuk bağlantı temizleniyor...")
                    self.remove_client(client)
                    
            except Exception as e:
                print(f"⚠️ Temizlik hatası: {e}")
    
    def start_server(self):
        """Server'ı başlat"""
        try:
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Port yeniden kullanımı
            
            # Keep-alive ayarları
            server.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            
            server.bind((self.host, self.port))
            server.listen(5)  # Max 5 pending connection
            
            server_ip = self.get_server_ip()
            print("="*60)
            print("🚀 ENHANCED VOICE CHAT SERVER BAŞLATILDI")
            print("="*60)
            print(f"📍 Yerel Adres: localhost:{self.port}")
            print(f"🌐 Ağ Adresi: {server_ip}:{self.port}")
            print(f"🔒 Chat Şifresi: {self.password}")
            print("🎙️ Sesli arama desteği aktif")
            print("📞 Gerçek zamanlı ses aktarımı mevcut")
            print("="*60)
            print("📝 Client'lar bu adresleri kullanarak bağlanabilir")
            print("⏳ Bağlantılar bekleniyor...")
            print("="*60)
            
            # Temizlik thread'i başlat
            cleanup_thread = threading.Thread(target=self.cleanup_disconnected_clients)
            cleanup_thread.daemon = True
            cleanup_thread.start()
            
            while self.server_running:
                try:
                    server.settimeout(1.0)  # Accept için timeout
                    client, address = server.accept()
                    
                    print(f"🔄 Yeni bağlantı denemesi: {str(address)}")
                    
                    # Client ayarları
                    client.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
                    
                    # Önce şifre doğrulaması
                    if self.authenticate_client(client):
                        print(f"✅ Şifre doğrulandı: {str(address)}")
                        
                        # Nickname iste
                        client.send("NICK".encode('utf-8'))
                        client.settimeout(30)  # Nickname için timeout
                        nickname = client.recv(1024).decode('utf-8')
                        
                        # Timeout'u kaldır
                        client.settimeout(None)
                        
                        self.nicknames.append(nickname)
                        self.clients.append(client)
                        
                        print(f"👤 Kullanıcı katıldı: {nickname} ({str(address)})")
                        print(f"📊 Aktif kullanıcı sayısı: {len(self.clients)}")
                        
                        # Hoşgeldin mesajları
                        self.broadcast(f"🎉 {nickname} chat'e katıldı!".encode('utf-8'))
                        client.send("✅ Server'a başarıyla bağlandın!".encode('utf-8'))
                        
                        # Client'ı dinlemek için thread başlat
                        thread = threading.Thread(target=self.handle_client, args=(client,))
                        thread.daemon = True
                        thread.start()
                        self.client_threads.append(thread)
                        
                    else:
                        print(f"❌ Yanlış şifre: {str(address)}")
                        try:
                            client.close()
                        except:
                            pass
                            
                except socket.timeout:
                    # Accept timeout - normal, devam et
                    continue
                except Exception as e:
                    if self.server_running:
                        print(f"⚠️ Bağlantı kabul hatası: {e}")
                        
        except Exception as e:
            print(f"💥 Server başlatma hatası: {e}")
        finally:
            self.shutdown_server()
    
    def shutdown_server(self):
        """Server'ı güvenli şekilde kapat"""
        print("\n🛑 Server kapatılıyor...")
        self.server_running = False
        
        # Aktif aramaları sonlandır
        for call_id in list(self.active_calls.keys()):
            self.end_call(call_id, 'server_shutdown')
        
        # Tüm client'lara bilgi ver
        try:
            self.broadcast("🛑 Server kapatılıyor...".encode('utf-8'))
        except:
            pass
        
        # Client'ları kapat
        for client in self.clients[:]:
            try:
                client.close()
            except:
                pass
        
        self.clients.clear()
        self.nicknames.clear()
        self.active_calls.clear()
        self.client_call_status.clear()
        
        print("✅ Server kapatıldı")

if __name__ == "__main__":
    try:
        server = ChatServer()
        server.start_server()
    except KeyboardInterrupt:
        print("\n🛑 Server durduruluyor...")
    except Exception as e:
        print(f"💥 Server başlatılamadı: {e}")
        print("💡 Firewall ayarlarını kontrol edin veya farklı port deneyin")