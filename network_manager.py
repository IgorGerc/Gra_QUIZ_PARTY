"""
Moduł zarządzania siecią - obsługuje komunikację między graczami
Używa WebSocket do komunikacji real-time
"""

import asyncio
import websockets
import json
import threading
from typing import Dict, List, Optional, Any
import logging

# Konfiguracja logowania
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NetworkManager:
    """Zarządza komunikacją sieciową między graczami"""
    
    def __init__(self, is_host: bool = False, host_ip: str = None, port: int = 8765):
        self.is_host = is_host
        self.host_ip = host_ip or "localhost"
        self.port = port
        self.players: Dict[str, websockets.WebSocketServerProtocol] = {}  # nazwa -> websocket
        self.player_name = ""
        self.client_websocket = None
        self.server = None
        self.pending_messages = []
        self.message_lock = threading.Lock()
        
    async def start_server(self):
        """Uruchamia serwer WebSocket (tylko host)"""
        if not self.is_host:
            return
        
        try:
            self.server = await websockets.serve(
                self.handle_client_connection,
                "0.0.0.0",  # Nasłuchuj na wszystkich interfejsach
                self.port
            )
            logger.info(f"Serwer uruchomiony na porcie {self.port}")
            
            # Dodaj hosta do listy graczy
            from kivy.app import App
            app = App.get_running_app()
            if hasattr(app, 'player_name'):
                self.players[app.player_name] = None  # Host nie ma websocket
            
            await self.server.wait_closed()
        except Exception as e:
            logger.error(f"Błąd serwera: {e}")
    
    async def handle_client_connection(self, websocket, path):
        """Obsługuje połączenie klienta"""
        player_name = None
        try:
            async for message in websocket:
                data = json.loads(message)
                
                if data['type'] == 'join':
                    player_name = data['player_name']
                    if player_name in self.players:
                        await websocket.send(json.dumps({
                            'type': 'error',
                            'message': 'Gracz o tej nazwie już istnieje!'
                        }))
                        continue
                    
                    self.players[player_name] = websocket
                    logger.info(f"Gracz {player_name} dołączył do gry")
                    
                    # Potwierdź dołączenie
                    await websocket.send(json.dumps({
                        'type': 'join_success',
                        'message': 'Pomyślnie dołączono do gry!'
                    }))
                    
                    # Powiadom wszystkich o nowym graczu
                    await self.broadcast_to_clients({
                        'type': 'player_joined',
                        'player_name': player_name,
                        'players_list': list(self.players.keys())
                    })
                
                elif data['type'] == 'answer':
                    # Przekaż odpowiedź do logiki gry
                    with self.message_lock:
                        self.pending_messages.append(data)
                
                elif data['type'] == 'vote':
                    # Przekaż głos do logiki gry
                    with self.message_lock:
                        self.pending_messages.append(data)
                
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Gracz {player_name} rozłączył się")
        except Exception as e:
            logger.error(f"Błąd obsługi klienta: {e}")
        finally:
            if player_name and player_name in self.players:
                del self.players[player_name]
                # Powiadom pozostałych graczy
                await self.broadcast_to_clients({
                    'type': 'player_left',
                    'player_name': player_name,
                    'players_list': list(self.players.keys())
                })
    
    async def connect_to_host(self, player_name: str) -> bool:
        """Łączy się z hostem (tylko klient)"""
        if self.is_host:
            return False
        
        try:
            uri = f"ws://{self.host_ip}:{self.port}"
            self.client_websocket = await websockets.connect(uri)
            self.player_name = player_name
            
            # Wyślij żądanie dołączenia
            await self.client_websocket.send(json.dumps({
                'type': 'join',
                'player_name': player_name
            }))
            
            # Czekaj na potwierdzenie
            response = await self.client_websocket.recv()
            data = json.loads(response)
            
            if data['type'] == 'join_success':
                # Uruchom nasłuchiwanie wiadomości
                asyncio.create_task(self.listen_for_messages())
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"Błąd połączenia z hostem: {e}")
            return False
    
    async def listen_for_messages(self):
        """Nasłuchuje wiadomości od serwera (tylko klient)"""
        try:
            async for message in self.client_websocket:
                data = json.loads(message)
                with self.message_lock:
                    self.pending_messages.append(data)
        except websockets.exceptions.ConnectionClosed:
            logger.info("Połączenie z serwerem zostało zamknięte")
        except Exception as e:
            logger.error(f"Błąd nasłuchiwania wiadomości: {e}")
    
    def send_message(self, message: Dict[str, Any]):
        """Wysyła wiadomość (klient do serwera)"""
        if not self.is_host and self.client_websocket:
            asyncio.create_task(self._send_message_async(message))
    
    async def _send_message_async(self, message: Dict[str, Any]):
        """Asynchronicznie wysyła wiadomość"""
        try:
            await self.client_websocket.send(json.dumps(message))
        except Exception as e:
            logger.error(f"Błąd wysyłania wiadomości: {e}")
    
    def broadcast_message(self, message: Dict[str, Any]):
        """Wysyła wiadomość do wszystkich klientów (tylko host)"""
        if self.is_host:
            asyncio.create_task(self.broadcast_to_clients(message))
    
    async def broadcast_to_clients(self, message: Dict[str, Any]):
        """Asynchronicznie wysyła wiadomość do wszystkich klientów"""
        if not self.players:
            return
        
        # Wyślij do wszystkich klientów (pomijając hosta)
        disconnected = []
        for player_name, websocket in self.players.items():
            if websocket is None:  # Host
                continue
            try:
                await websocket.send(json.dumps(message))
            except websockets.exceptions.ConnectionClosed:
                disconnected.append(player_name)
            except Exception as e:
                logger.error(f"Błąd wysyłania do {player_name}: {e}")
                disconnected.append(player_name)
        
        # Usuń rozłączonych graczy
        for player_name in disconnected:
            if player_name in self.players:
                del self.players[player_name]
    
    def get_players_list(self) -> List[str]:
        """Zwraca listę graczy"""
        return list(self.players.keys())
    
    def get_pending_messages(self) -> List[Dict[str, Any]]:
        """Pobiera oczekujące wiadomości"""
        with self.message_lock:
            messages = self.pending_messages.copy()
            self.pending_messages.clear()
            return messages
    
    def disconnect(self):
        """Rozłącza się z siecią"""
        try:
            if self.is_host and self.server:
                # Sprawdź czy jest aktywna pętla zdarzeń
                try:
                    loop = asyncio.get_running_loop()
                    asyncio.create_task(self._close_server())
                except RuntimeError:
                    # Brak aktywnej pętli, zamknij synchronicznie
                    if self.server:
                        self.server.close()
            elif not self.is_host and self.client_websocket:
                try:
                    loop = asyncio.get_running_loop()
                    asyncio.create_task(self._close_client())
                except RuntimeError:
                    # Brak aktywnej pętli, nie rób nic
                    pass
        except Exception as e:
            logger.error(f"Błąd podczas rozłączania: {e}")
    
    async def _close_server(self):
        """Zamyka serwer"""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
    
    async def _close_client(self):
        """Zamyka połączenie klienta"""
        if self.client_websocket:
            await self.client_websocket.close()
    
    def get_player_count(self) -> int:
        """Zwraca liczbę graczy"""
        return len(self.players)
    
    def is_connected(self) -> bool:
        """Sprawdza czy jest połączenie"""
        if self.is_host:
            return self.server is not None
        else:
            return self.client_websocket is not None and not self.client_websocket.closed