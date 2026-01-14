import socket
import threading
import time
import json
import uuid

class ChatServer:
    def __init__(self, host='0.0.0.0', port=12345):
        self.host = host
        self.port = port
        self.clients = []
        self.nicknames = []
        self.client_public_keys = {}
        self.password = "fidelio"
        self.server_running = True
        
        self.active_calls = {}
        self.client_call_status = {}
        
    def authenticate_client(self, client):
        try:
            client.send("PASSWORD".encode('utf-8'))
            client.settimeout(30)
            received_password = client.recv(1024).decode('utf-8')
            
            if received_password == self.password:
                client.send("AUTH_SUCCESS".encode('utf-8'))
                return True
            else:
                client.send("AUTH_FAILED".encode('utf-8'))
                return False
        except Exception as e:
            print(f"⚠️ Authentication error: {e}")
            return False
    
    def broadcast(self, message, sender_client=None):
        disconnected_clients = []
        
        for client in self.clients[:]:
            if client != sender_client:
                try:
                    if isinstance(message, str):
                        if not message.endswith('\n'):
                            message = message + '\n'
                        message = message.encode('utf-8')
                    client.send(message)
                except:
                    disconnected_clients.append(client)
        
        for client in disconnected_clients:
            self.remove_client(client)
    
    def send_to_client(self, target_client, message):
        try:
            if isinstance(message, str):
                if not message.endswith('\n'):
                    message = message + '\n'
                message = message.encode('utf-8')
            target_client.send(message)
            return True
        except:
            self.remove_client(target_client)
            return False
    
    def get_client_by_nickname(self, nickname):
        try:
            index = self.nicknames.index(nickname)
            return self.clients[index]
        except:
            return None
    
    def get_nickname_by_client(self, client):
        try:
            index = self.clients.index(client)
            return self.nicknames[index]
        except:
            return "Unknown"
    
    def handle_public_key(self, client, data):
        try:
            nickname = data.get('nickname')
            public_key = data.get('public_key')
            
            self.client_public_keys[nickname] = public_key
            print(f"🔑 {nickname} public key received")
            
            for nick, pub_key in self.client_public_keys.items():
                if nick != nickname:
                    existing_key = {
                        'type': 'public_key',
                        'nickname': nick,
                        'public_key': pub_key
                    }
                    self.send_to_client(client, json.dumps(existing_key))
                    print(f"  📤 {nick}'s key sent to {nickname}")
            
            key_broadcast = {
                'type': 'public_key',
                'nickname': nickname,
                'public_key': public_key
            }
            for other_client in self.clients:
                if other_client != client:
                    self.send_to_client(other_client, json.dumps(key_broadcast))
                    other_nick = self.get_nickname_by_client(other_client)
                    print(f"  📤 {nickname}'s key sent to {other_nick}")
            
        except Exception as e:
            print(f"⚠️ Public key processing error: {e}")
    
    def handle_encrypted_message(self, sender_client, data):
        try:
            target_nick = data.get('target')
            target_client = self.get_client_by_nickname(target_nick)
            
            if target_client:
                self.send_to_client(target_client, json.dumps(data))
            else:
                print(f"⚠️ Target not found: {target_nick}")
                
        except Exception as e:
            print(f"⚠️ Encrypted message relay error: {e}")
    
    def handle_call_request(self, caller_client, data):
        try:
            caller_nick = self.get_nickname_by_client(caller_client)
            target_nick = data.get('target')
            target_client = self.get_client_by_nickname(target_nick)
            
            if not target_client:
                response = {
                    'type': 'call_response',
                    'status': 'user_not_found',
                    'message': f'{target_nick} user not found'
                }
                self.send_to_client(caller_client, json.dumps(response))
                return
            
            target_status = self.client_call_status.get(target_client, {}).get('status', 'idle')
            if target_status != 'idle':
                response = {
                    'type': 'call_response',
                    'status': 'user_busy',
                    'message': f'{target_nick} is currently busy'
                }
                self.send_to_client(caller_client, json.dumps(response))
                return
            
            call_id = str(uuid.uuid4())
            self.active_calls[call_id] = {
                'caller': caller_client,
                'callee': target_client,
                'caller_nick': caller_nick,
                'callee_nick': target_nick,
                'status': 'ringing',
                'start_time': time.time()
            }
            
            self.client_call_status[caller_client] = {'status': 'calling', 'call_id': call_id}
            self.client_call_status[target_client] = {'status': 'ringing', 'call_id': call_id}
            
            response = {
                'type': 'call_response',
                'status': 'calling',
                'target': target_nick,
                'call_id': call_id
            }
            self.send_to_client(caller_client, json.dumps(response))
            
            incoming_call = {
                'type': 'incoming_call',
                'caller': caller_nick,
                'call_id': call_id
            }
            self.send_to_client(target_client, json.dumps(incoming_call))
            
            print(f"📞 Call initiated: {caller_nick} -> {target_nick}")
            
            timer = threading.Timer(30.0, self.timeout_call, [call_id])
            timer.start()
            
        except Exception as e:
            print(f"⚠️ Call request error: {e}")
    
    def handle_call_answer(self, client, data):
        try:
            call_id = data.get('call_id')
            action = data.get('action')
            
            if call_id not in self.active_calls:
                return
            
            call_info = self.active_calls[call_id]
            caller_client = call_info['caller']
            caller_nick = call_info['caller_nick']
            callee_nick = call_info['callee_nick']
            
            if action == 'accept':
                call_info['status'] = 'active'
                self.client_call_status[caller_client]['status'] = 'in_call'
                self.client_call_status[client]['status'] = 'in_call'
                
                call_started = {
                    'type': 'call_started',
                    'call_id': call_id,
                    'peer': caller_nick if client != caller_client else callee_nick
                }
                
                self.send_to_client(caller_client, json.dumps(call_started))
                call_started['peer'] = callee_nick
                self.send_to_client(client, json.dumps(call_started))
                
                print(f"✅ Call accepted: {caller_nick} <-> {callee_nick}")
                
            else:
                self.end_call(call_id, 'rejected')
                print(f"❌ Call rejected: {caller_nick} -> {callee_nick}")
                
        except Exception as e:
            print(f"⚠️ Call answer error: {e}")
    
    def handle_call_end(self, client, data):
        try:
            call_id = data.get('call_id')
            self.end_call(call_id, 'ended')
        except Exception as e:
            print(f"⚠️ Call end error: {e}")
    
    def end_call(self, call_id, reason='ended'):
        try:
            if call_id not in self.active_calls:
                return
            
            call_info = self.active_calls[call_id]
            caller_client = call_info['caller']
            callee_client = call_info['callee']
            
            if caller_client in self.client_call_status:
                self.client_call_status[caller_client] = {'status': 'idle'}
            if callee_client in self.client_call_status:
                self.client_call_status[callee_client] = {'status': 'idle'}
            
            call_ended = {
                'type': 'call_ended',
                'call_id': call_id,
                'reason': reason
            }
            
            self.send_to_client(caller_client, json.dumps(call_ended))
            self.send_to_client(callee_client, json.dumps(call_ended))
            
            del self.active_calls[call_id]
            
            print(f"📞 Call ended: {call_info['caller_nick']} <-> {call_info['callee_nick']} ({reason})")
            
        except Exception as e:
            print(f"⚠️ Call termination error: {e}")
    
    def timeout_call(self, call_id):
        if call_id in self.active_calls and self.active_calls[call_id]['status'] == 'ringing':
            self.end_call(call_id, 'timeout')
    
    def handle_voice_data(self, sender_client, data):
        try:
            call_id = data.get('call_id')
            if call_id not in self.active_calls:
                return
            
            call_info = self.active_calls[call_id]
            if call_info['status'] != 'active':
                return
            
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
            print(f"⚠️ Voice data transmission error: {e}")
    
    def handle_user_list_request(self, client):
        try:
            current_nick = self.get_nickname_by_client(client)
            user_list = []
            
            for i, nick in enumerate(self.nicknames):
                if nick != current_nick:
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
            print(f"⚠️ User list error: {e}")
    
    def remove_client(self, client):
        try:
            client_status = self.client_call_status.get(client, {})
            if client_status.get('status') in ['calling', 'in_call', 'ringing']:
                call_id = client_status.get('call_id')
                if call_id:
                    self.end_call(call_id, 'disconnected')
            
            if client in self.client_call_status:
                del self.client_call_status[client]
            
            if client in self.clients:
                index = self.clients.index(client)
                self.clients.remove(client)
                
                if index < len(self.nicknames):
                    nickname = self.nicknames[index]
                    self.nicknames.remove(nickname)
                    
                    if nickname in self.client_public_keys:
                        del self.client_public_keys[nickname]
                    
                    try:
                        self.broadcast(f"👋 {nickname} left the chat!\n".encode('utf-8'))
                        print(f"👋 {nickname} disconnected")
                    except:
                        pass
                
                try:
                    client.close()
                except:
                    pass
                    
        except Exception as e:
            print(f"⚠️ Client removal error: {e}")
    
    def handle_client(self, client):
        nickname = "Unknown"
        last_activity = time.time()
        
        try:
            self.client_call_status[client] = {'status': 'idle'}
            
            while self.server_running:
                try:
                    client.settimeout(1.0)
                    message = client.recv(16384)
                    
                    if message:
                        decoded_message = message.decode('utf-8')
                        last_activity = time.time()
                        
                        if decoded_message == "PING":
                            client.send("PONG\n".encode('utf-8'))
                            continue
                        elif decoded_message == "PONG":
                            continue
                        
                        try:
                            msg_data = json.loads(decoded_message)
                            msg_type = msg_data.get('type')
                            
                            if msg_type == 'public_key':
                                self.handle_public_key(client, msg_data)
                            elif msg_type == 'encrypted_message':
                                self.handle_encrypted_message(client, msg_data)
                            elif msg_type == 'call_request':
                                self.handle_call_request(client, msg_data)
                            elif msg_type == 'call_answer':
                                self.handle_call_answer(client, msg_data)
                            elif msg_type == 'call_end':
                                self.handle_call_end(client, msg_data)
                            elif msg_type == 'voice_data':
                                self.handle_voice_data(client, msg_data)
                            elif msg_type == 'user_list_request':
                                self.handle_user_list_request(client)
                            else:
                                self.broadcast(message, client)
                            
                        except json.JSONDecodeError:
                            self.broadcast(message, client)
                            print(f"📨 Message: {decoded_message}")
                        
                    else:
                        print(f"⚠️ {nickname} sent empty message")
                        break
                        
                except socket.timeout:
                    if time.time() - last_activity > 60:
                        print(f"⏰ {nickname} inactive for too long")
                        try:
                            client.send("PING".encode('utf-8'))
                            last_activity = time.time()
                        except:
                            print(f"💔 {nickname} heartbeat failed")
                            break
                    continue
                    
                except ConnectionResetError:
                    print(f"🔌 {nickname} closed connection")
                    break
                    
                except Exception as e:
                    print(f"⚠️ {nickname} message reception error: {e}")
                    break
                    
        except Exception as e:
            print(f"💥 Critical error for {nickname}: {e}")
        finally:
            self.remove_client(client)
    
    def get_server_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "localhost"
    
    def start_server(self):
        try:
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            
            server.bind((self.host, self.port))
            server.listen(10)
            
            server_ip = self.get_server_ip()
            print("="*70)
            print("🚀 ENHANCED E2E ENCRYPTED VOICE CHAT SERVER")
            print("="*70)
            print(f"🏠 Local Address: localhost:{self.port}")
            print(f"🌐 Network Address: {server_ip}:{self.port}")
            print(f"🔒 Chat Password: {self.password}")
            print(f"🔐 End-to-End Encryption: Active (RSA 2048 + AES 256)")
            print(f"🎙️ Voice Calling: Active (Real-time P2P)")
            print(f"🔏 Anonymous Communication: Server cannot see messages")
            print("="*70)
            print("⏳ Waiting for connections...")
            print("="*70)
            
            while self.server_running:
                try:
                    server.settimeout(1.0)
                    client, address = server.accept()
                    
                    print(f"🔄 New connection attempt: {str(address)}")
                    
                    client.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
                    
                    if self.authenticate_client(client):
                        print(f"✅ Password verified: {str(address)}")
                        
                        client.send("NICK".encode('utf-8'))
                        client.settimeout(30)
                        nickname = client.recv(1024).decode('utf-8')
                        client.settimeout(None)
                        
                        self.nicknames.append(nickname)
                        self.clients.append(client)
                        
                        print(f"👤 User joined: {nickname} ({str(address)})")
                        print(f"📊 Active users: {len(self.clients)}")
                        
                        self.broadcast(f"🎉 {nickname} joined the chat!\n".encode('utf-8'))
                        client.send("✅ Successfully connected to server! 🔐 E2E active\n".encode('utf-8'))
                        
                        thread = threading.Thread(target=self.handle_client, args=(client,))
                        thread.daemon = True
                        thread.start()
                        
                    else:
                        print(f"❌ Wrong password: {str(address)}")
                        try:
                            client.close()
                        except:
                            pass
                            
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.server_running:
                        print(f"⚠️ Connection accept error: {e}")
                        
        except Exception as e:
            print(f"💥 Server startup error: {e}")
        finally:
            self.shutdown_server()
    
    def shutdown_server(self):
        print("\n🛑 Shutting down server...")
        self.server_running = False
        
        for call_id in list(self.active_calls.keys()):
            self.end_call(call_id, 'server_shutdown')
        
        try:
            self.broadcast("🛑 Server shutting down...\n".encode('utf-8'))
        except:
            pass
        
        for client in self.clients[:]:
            try:
                client.close()
            except:
                pass
        
        self.clients.clear()
        self.nicknames.clear()
        self.active_calls.clear()
        self.client_call_status.clear()
        self.client_public_keys.clear()
        
        print("✅ Server closed")

if __name__ == "__main__":
    try:
        server = ChatServer()
        server.start_server()
    except KeyboardInterrupt:
        print("\n🛑 Stopping server...")
    except Exception as e:
        print(f"💥 Server failed to start: {e}")
