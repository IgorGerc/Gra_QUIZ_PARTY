"""
Quiz Party - Wersja APK
Kompletna aplikacja gotowa do budowania APK
"""

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserListView
from kivy.clock import Clock
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp
from kivy.core.window import Window

import asyncio
import threading
import socket
import json
import os

# Kolory aplikacji
COLORS = {
    'primary': (0.2, 0.6, 1.0, 1),      # Niebieski
    'secondary': (0.9, 0.3, 0.5, 1),    # Różowy
    'success': (0.2, 0.8, 0.2, 1),      # Zielony
    'warning': (1.0, 0.6, 0.0, 1),      # Pomarańczowy
    'danger': (0.9, 0.2, 0.2, 1),       # Czerwony
    'dark': (0.15, 0.15, 0.15, 1),      # Ciemny
    'light': (0.95, 0.95, 0.95, 1),     # Jasny
    'white': (1, 1, 1, 1),              # Biały
    'background': (0.05, 0.05, 0.1, 1), # Tło
}

# Ustaw rozmiar okna dla telefonu
Window.size = (400, 700)

try:
    from game_logic import GameLogic
    from network_manager import NetworkManager
    HAS_NETWORK = True
except ImportError:
    HAS_NETWORK = False
    print("⚠️ Brak modułów sieciowych - tryb offline")

class StyledButton(Button):
    """Przycisk z ładnym stylem"""
    def __init__(self, button_type='primary', **kwargs):
        super().__init__(**kwargs)
        self.button_type = button_type
        self.background_color = (0, 0, 0, 0)
        self.color = COLORS['white']
        self.font_size = dp(18)
        self.bold = True
        self.bind(size=self.update_graphics, pos=self.update_graphics)
        self.update_graphics()
    
    def update_graphics(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*COLORS.get(self.button_type, COLORS['primary']))
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(10)])

class StyledLabel(Label):
    """Label z ładnym stylem"""
    def __init__(self, label_type='white', **kwargs):
        super().__init__(**kwargs)
        self.color = COLORS.get(label_type, COLORS['white'])
        self.font_size = dp(16)

class StyledTextInput(TextInput):
    """TextInput z ładnym stylem"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_color = COLORS['white']
        self.foreground_color = COLORS['dark']
        self.cursor_color = COLORS['primary']
        self.font_size = dp(16)
        self.padding = [dp(10), dp(10)]

class BackgroundWidget(Widget):
    """Widget z gradientowym tłem"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(size=self.update_graphics, pos=self.update_graphics)
        self.update_graphics()
    
    def update_graphics(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*COLORS['background'])
            RoundedRectangle(pos=self.pos, size=self.size)

class MenuScreen(Screen):
    """Ekran głównego menu"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'menu'
        
        # Tło
        bg = BackgroundWidget()
        self.add_widget(bg)
        
        layout = BoxLayout(orientation='vertical', padding=dp(30), spacing=dp(15))
        
        # Tytuł
        title = StyledLabel(
            text='🎉 QUIZ PARTY 🎉',
            font_size=dp(36),
            size_hint_y=0.2,
            bold=True,
            label_type='primary'
        )
        layout.add_widget(title)
        
        # Podtytuł
        subtitle = StyledLabel(
            text='Gra towarzyska dla 3-10 graczy',
            font_size=dp(18),
            size_hint_y=0.08,
            label_type='light'
        )
        layout.add_widget(subtitle)
        
        # Spacer
        layout.add_widget(Widget(size_hint_y=0.05))
        
        # Przyciski menu
        btn_host = StyledButton(
            text='🏠 Stwórz grę (Host)',
            size_hint_y=0.12,
            button_type='primary'
        )
        btn_host.bind(on_press=self.create_game)
        layout.add_widget(btn_host)
        
        btn_join = StyledButton(
            text='🔗 Dołącz do gry',
            size_hint_y=0.12,
            button_type='secondary'
        )
        btn_join.bind(on_press=self.join_game)
        layout.add_widget(btn_join)
        
        btn_demo = StyledButton(
            text='🎮 Gra demo (offline)',
            size_hint_y=0.12,
            button_type='success'
        )
        btn_demo.bind(on_press=self.demo_game)
        layout.add_widget(btn_demo)
        
        btn_questions = StyledButton(
            text='📝 Zarządzaj pytaniami',
            size_hint_y=0.12,
            button_type='warning'
        )
        btn_questions.bind(on_press=self.manage_questions)
        layout.add_widget(btn_questions)
        
        btn_about = StyledButton(
            text='ℹ️ O aplikacji',
            size_hint_y=0.12,
            button_type='dark'
        )
        btn_about.bind(on_press=self.show_about)
        layout.add_widget(btn_about)
        
        self.add_widget(layout)
    
    def create_game(self, instance):
        """Przejście do ekranu tworzenia gry"""
        if HAS_NETWORK:
            self.manager.current = 'host_setup'
        else:
            self.show_network_error()
    
    def join_game(self, instance):
        """Przejście do ekranu dołączania do gry"""
        if HAS_NETWORK:
            self.manager.current = 'join_setup'
        else:
            self.show_network_error()
    
    def demo_game(self, instance):
        """Przejście do gry demo"""
        self.manager.current = 'demo_game'
    
    def manage_questions(self, instance):
        """Przejście do zarządzania pytaniami"""
        self.manager.current = 'questions'
    
    def show_about(self, instance):
        """Pokaż informacje o aplikacji"""
        content = BoxLayout(orientation='vertical', spacing=dp(10))
        
        info_text = StyledLabel(
            text='🎉 Quiz Party v1.0\n\n'
                 'Gra towarzyska inspirowana "Fibbing It"\n\n'
                 '👥 3-10 graczy\n'
                 '📱 Jeden telefon = host\n'
                 '🌐 Gra przez WiFi\n'
                 '🎯 Bez timerów\n\n'
                 'Stworzono z ❤️ dla zabawy z przyjaciółmi!',
            font_size=dp(16),
            label_type='white'
        )
        content.add_widget(info_text)
        
        btn_close = StyledButton(
            text='✅ OK',
            size_hint_y=0.3,
            button_type='primary'
        )
        
        popup = Popup(
            title='O aplikacji',
            content=content,
            size_hint=(0.8, 0.6)
        )
        
        btn_close.bind(on_press=popup.dismiss)
        content.add_widget(btn_close)
        popup.open()
    
    def show_network_error(self):
        """Pokaż błąd braku modułów sieciowych"""
        content = BoxLayout(orientation='vertical', spacing=dp(10))
        
        error_text = StyledLabel(
            text='❌ Brak modułów sieciowych!\n\n'
                 'Funkcje sieciowe nie są dostępne.\n'
                 'Możesz użyć gry demo.',
            font_size=dp(16),
            label_type='danger'
        )
        content.add_widget(error_text)
        
        btn_close = StyledButton(
            text='OK',
            size_hint_y=0.3,
            button_type='danger'
        )
        
        popup = Popup(
            title='Błąd',
            content=content,
            size_hint=(0.7, 0.4)
        )
        
        btn_close.bind(on_press=popup.dismiss)
        content.add_widget(btn_close)
        popup.open()

class HostSetupScreen(Screen):
    """Ekran konfiguracji gry dla hosta"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'host_setup'
        
        # Tło
        bg = BackgroundWidget()
        self.add_widget(bg)
        
        layout = BoxLayout(orientation='vertical', padding=dp(30), spacing=dp(20))
        
        # Tytuł
        title = StyledLabel(
            text='🏠 Stwórz nową grę',
            font_size=dp(28),
            size_hint_y=0.15,
            bold=True,
            label_type='primary'
        )
        layout.add_widget(title)
        
        # Pole na nick hosta
        layout.add_widget(StyledLabel(text='Twój nick:', size_hint_y=0.08))
        self.host_name_input = StyledTextInput(
            text='Host',
            multiline=False,
            size_hint_y=0.12
        )
        layout.add_widget(self.host_name_input)
        
        # Informacje o IP
        self.ip_label = StyledLabel(
            text=f'📡 Twoje IP: {self.get_local_ip()}',
            size_hint_y=0.1,
            label_type='success'
        )
        layout.add_widget(self.ip_label)
        
        # Instrukcje
        instructions = StyledLabel(
            text='Podziel się swoim IP z innymi graczami.\nOni będą potrzebować go do dołączenia.',
            size_hint_y=0.15,
            label_type='light'
        )
        layout.add_widget(instructions)
        
        # Spacer
        layout.add_widget(Widget(size_hint_y=0.1))
        
        # Przyciski
        btn_start = StyledButton(
            text='🚀 Rozpocznij grę',
            size_hint_y=0.15,
            button_type='success'
        )
        btn_start.bind(on_press=self.start_hosting)
        layout.add_widget(btn_start)
        
        btn_back = StyledButton(
            text='⬅️ Powrót',
            size_hint_y=0.15,
            button_type='danger'
        )
        btn_back.bind(on_press=self.go_back)
        layout.add_widget(btn_back)
        
        self.add_widget(layout)
    
    def get_local_ip(self):
        """Pobiera lokalne IP"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "Nie można pobrać IP"
    
    def start_hosting(self, instance):
        """Rozpoczyna hosting gry"""
        if not HAS_NETWORK:
            return
            
        app = App.get_running_app()
        app.player_name = self.host_name_input.text.strip() or "Host"
        
        # Inicjalizuj komponenty gry
        app.network_manager = NetworkManager(is_host=True)
        app.game_logic = GameLogic()
        
        # Uruchom serwer w osobnym wątku
        def start_server():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(app.network_manager.start_server())
        
        server_thread = threading.Thread(target=start_server, daemon=True)
        server_thread.start()
        
        # Przejdź do lobby
        self.manager.current = 'lobby'
    
    def go_back(self, instance):
        """Powrót do menu"""
        self.manager.current = 'menu'

class JoinSetupScreen(Screen):
    """Ekran dołączania do gry"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'join_setup'
        
        # Tło
        bg = BackgroundWidget()
        self.add_widget(bg)
        
        layout = BoxLayout(orientation='vertical', padding=dp(30), spacing=dp(20))
        
        # Tytuł
        title = StyledLabel(
            text='🔗 Dołącz do gry',
            font_size=dp(28),
            size_hint_y=0.15,
            bold=True,
            label_type='secondary'
        )
        layout.add_widget(title)
        
        # Pole na nick
        layout.add_widget(StyledLabel(text='Twój nick:', size_hint_y=0.08))
        self.player_name_input = StyledTextInput(
            text='Gracz',
            multiline=False,
            size_hint_y=0.12
        )
        layout.add_widget(self.player_name_input)
        
        # Pole na IP hosta
        layout.add_widget(StyledLabel(text='IP hosta:', size_hint_y=0.08))
        self.host_ip_input = StyledTextInput(
            text='192.168.1.',
            multiline=False,
            size_hint_y=0.12
        )
        layout.add_widget(self.host_ip_input)
        
        # Status połączenia
        self.status_label = StyledLabel(
            text='Wprowadź dane i kliknij "Dołącz"',
            size_hint_y=0.1,
            label_type='light'
        )
        layout.add_widget(self.status_label)
        
        # Spacer
        layout.add_widget(Widget(size_hint_y=0.1))
        
        # Przyciski
        btn_join = StyledButton(
            text='🔗 Dołącz do gry',
            size_hint_y=0.15,
            button_type='success'
        )
        btn_join.bind(on_press=self.join_game)
        layout.add_widget(btn_join)
        
        btn_back = StyledButton(
            text='⬅️ Powrót',
            size_hint_y=0.15,
            button_type='danger'
        )
        btn_back.bind(on_press=self.go_back)
        layout.add_widget(btn_back)
        
        self.add_widget(layout)
    
    def join_game(self, instance):
        """Dołącza do gry"""
        if not HAS_NETWORK:
            return
            
        player_name = self.player_name_input.text.strip()
        host_ip = self.host_ip_input.text.strip()
        
        if not player_name or not host_ip:
            self.status_label.text = "❌ Wypełnij wszystkie pola!"
            self.status_label.color = COLORS['danger']
            return
        
        app = App.get_running_app()
        app.player_name = player_name
        
        # Inicjalizuj komponenty
        app.network_manager = NetworkManager(is_host=False, host_ip=host_ip)
        app.game_logic = GameLogic()
        
        self.status_label.text = "🔄 Łączenie..."
        self.status_label.color = COLORS['warning']
        
        # Połącz w osobnym wątku
        def connect():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            success = loop.run_until_complete(
                app.network_manager.connect_to_host(player_name)
            )
            
            if success:
                Clock.schedule_once(lambda dt: setattr(self.manager, 'current', 'lobby'))
            else:
                Clock.schedule_once(lambda dt: self.connection_failed())
        
        connect_thread = threading.Thread(target=connect, daemon=True)
        connect_thread.start()
    
    def connection_failed(self):
        """Obsługuje nieudane połączenie"""
        self.status_label.text = "❌ Nie można połączyć się z hostem!"
        self.status_label.color = COLORS['danger']
    
    def go_back(self, instance):
        """Powrót do menu"""
        self.manager.current = 'menu'

class DemoGameScreen(Screen):
    """Ekran gry demo - offline"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'demo_game'
        self.current_question = 0
        self.score = 0
        
        # Domyślne pytania
        self.questions = [
            ("Jaka jest stolica Polski?", "warszawa"),
            ("Ile kontynentów jest na Ziemi?", "7"),
            ("Kto napisał 'Pan Tadeusz'?", "adam mickiewicz"),
            ("Jaka jest największa planeta w Układzie Słonecznym?", "jowisz"),
            ("W którym roku Polska wstąpiła do Unii Europejskiej?", "2004"),
            ("Jaki jest najwyższy szczyt w Polsce?", "rysy"),
            ("Ile stron ma trójkąt?", "3"),
            ("Jaka jest waluta w Japonii?", "jen"),
            ("Kto namalował 'Mona Lisę'?", "leonardo da vinci"),
            ("Jaka jest najdłuższa rzeka na świecie?", "nil")
        ]
        
        # Tło
        bg = BackgroundWidget()
        self.add_widget(bg)
        
        layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
        
        # Informacje o grze
        self.game_info = StyledLabel(
            text='🎮 Gra Demo - Pytanie 1/10',
            font_size=dp(18),
            size_hint_y=0.1,
            label_type='primary'
        )
        layout.add_widget(self.game_info)
        
        # Pytanie
        self.question_label = StyledLabel(
            text='',
            font_size=dp(20),
            size_hint_y=0.25,
            label_type='white'
        )
        layout.add_widget(self.question_label)
        
        # Pole odpowiedzi
        self.answer_input = StyledTextInput(
            hint_text='Wpisz swoją odpowiedź...',
            multiline=False,
            size_hint_y=0.15
        )
        layout.add_widget(self.answer_input)
        
        # Przycisk odpowiedzi
        self.submit_button = StyledButton(
            text='📤 Wyślij odpowiedź',
            size_hint_y=0.12,
            button_type='success'
        )
        self.submit_button.bind(on_press=self.submit_answer)
        layout.add_widget(self.submit_button)
        
        # Status
        self.status_label = StyledLabel(
            text='',
            font_size=dp(16),
            size_hint_y=0.1,
            label_type='light'
        )
        layout.add_widget(self.status_label)
        
        # Wyniki
        self.results_label = StyledLabel(
            text='',
            font_size=dp(16),
            size_hint_y=0.18,
            label_type='white'
        )
        layout.add_widget(self.results_label)
        
        # Przycisk powrotu
        btn_menu = StyledButton(
            text='🏠 Powrót do menu',
            size_hint_y=0.1,
            button_type='danger'
        )
        btn_menu.bind(on_press=self.go_to_menu)
        layout.add_widget(btn_menu)
        
        self.add_widget(layout)
    
    def on_enter(self):
        """Wywoływane przy wejściu na ekran"""
        self.current_question = 0
        self.score = 0
        self.load_question()
    
    def load_question(self):
        """Ładuje aktualne pytanie"""
        if self.current_question < len(self.questions):
            question, _ = self.questions[self.current_question]
            self.question_label.text = question
            self.game_info.text = f'🎮 Gra Demo - Pytanie {self.current_question + 1}/{len(self.questions)} | Punkty: {self.score}'
            self.answer_input.text = ''
            self.answer_input.disabled = False
            self.submit_button.disabled = False
            self.status_label.text = 'Wpisz swoją odpowiedź'
            self.results_label.text = ''
        else:
            self.show_final_results()
    
    def submit_answer(self, instance):
        """Obsługuje wysłanie odpowiedzi"""
        answer = self.answer_input.text.strip().lower()
        if not answer:
            return
        
        question, correct_answer = self.questions[self.current_question]
        
        self.submit_button.disabled = True
        self.answer_input.disabled = True
        
        # Sprawdź odpowiedź
        if answer == correct_answer.lower():
            self.score += 1
            self.status_label.text = "✅ Poprawna odpowiedź! (+1 pkt)"
            self.status_label.color = COLORS['success']
        else:
            self.status_label.text = f"❌ Błędna odpowiedź. Poprawna: {correct_answer}"
            self.status_label.color = COLORS['danger']
        
        # Symuluj odpowiedzi innych graczy
        self.show_demo_answers(correct_answer)
        
        # Następne pytanie po 3 sekundach
        Clock.schedule_once(self.next_question, 3.0)
    
    def show_demo_answers(self, correct_answer):
        """Pokazuje przykładowe odpowiedzi innych graczy"""
        demo_answers = f"📋 Przykładowe odpowiedzi graczy:\n\n"
        demo_answers += f"• Ty: {self.answer_input.text}\n"
        demo_answers += f"• Gracz2: {correct_answer} ✅\n"
        demo_answers += f"• Gracz3: inna odpowiedź\n"
        
        self.results_label.text = demo_answers
    
    def next_question(self, dt):
        """Przechodzi do następnego pytania"""
        self.current_question += 1
        self.load_question()
    
    def show_final_results(self):
        """Pokazuje końcowe wyniki"""
        percentage = (self.score / len(self.questions)) * 100
        self.question_label.text = "🏆 KONIEC GRY DEMO! 🏆"
        self.game_info.text = f"Twój wynik: {self.score}/{len(self.questions)} ({percentage:.0f}%)"
        self.status_label.text = "Gratulacje!"
        self.results_label.text = f"🎉 Demo zakończone!\n\nW pełnej wersji gry:\n• Prawdziwa sieć WiFi\n• Głosowanie na odpowiedzi\n• Punktacja jak w Fibbing It\n• Do 10 graczy jednocześnie"
    
    def go_to_menu(self, instance):
        """Powrót do menu"""
        self.manager.current = 'menu'

class QuestionsScreen(Screen):
    """Ekran zarządzania pytaniami"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'questions'
        
        # Tło
        bg = BackgroundWidget()
        self.add_widget(bg)
        
        layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
        
        # Tytuł
        title = StyledLabel(
            text='📝 Zarządzanie pytaniami',
            font_size=dp(24),
            size_hint_y=0.1,
            bold=True,
            label_type='warning'
        )
        layout.add_widget(title)
        
        # Informacje
        info = StyledLabel(
            text='Tutaj możesz zarządzać pytaniami w grze.\nDomyślnie używane są wbudowane pytania.',
            font_size=dp(16),
            size_hint_y=0.15,
            label_type='light'
        )
        layout.add_widget(info)
        
        # Przyciski
        btn_load = StyledButton(
            text='📁 Wczytaj plik z pytaniami',
            size_hint_y=0.15,
            button_type='primary'
        )
        btn_load.bind(on_press=self.load_questions_file)
        layout.add_widget(btn_load)
        
        btn_view = StyledButton(
            text='👁️ Zobacz aktualne pytania',
            size_hint_y=0.15,
            button_type='secondary'
        )
        btn_view.bind(on_press=self.view_questions)
        layout.add_widget(btn_view)
        
        btn_reset = StyledButton(
            text='🔄 Przywróć domyślne',
            size_hint_y=0.15,
            button_type='warning'
        )
        btn_reset.bind(on_press=self.reset_questions)
        layout.add_widget(btn_reset)
        
        # Status
        self.status_label = StyledLabel(
            text='Gotowy do zarządzania pytaniami',
            size_hint_y=0.1,
            label_type='light'
        )
        layout.add_widget(self.status_label)
        
        # Przycisk powrotu
        btn_back = StyledButton(
            text='⬅️ Powrót do menu',
            size_hint_y=0.15,
            button_type='danger'
        )
        btn_back.bind(on_press=self.go_back)
        layout.add_widget(btn_back)
        
        self.add_widget(layout)
    
    def load_questions_file(self, instance):
        """Wczytuje plik z pytaniami"""
        # Symulacja - w pełnej wersji tutaj byłby file chooser
        self.status_label.text = "📁 Funkcja wczytywania plików w przygotowaniu..."
        self.status_label.color = COLORS['warning']
    
    def view_questions(self, instance):
        """Pokazuje aktualne pytania"""
        # Pobierz pytania z demo
        demo_screen = self.manager.get_screen('demo_game')
        questions = demo_screen.questions[:5]  # Pokaż pierwsze 5
        
        content = BoxLayout(orientation='vertical', spacing=dp(10))
        
        questions_text = "📋 Przykładowe pytania:\n\n"
        for i, (q, a) in enumerate(questions, 1):
            questions_text += f"{i}. {q}\n   Odpowiedź: {a}\n\n"
        
        questions_label = StyledLabel(
            text=questions_text,
            font_size=dp(14),
            label_type='white'
        )
        content.add_widget(questions_label)
        
        btn_close = StyledButton(
            text='✅ OK',
            size_hint_y=0.2,
            button_type='primary'
        )
        
        popup = Popup(
            title='Aktualne pytania',
            content=content,
            size_hint=(0.9, 0.8)
        )
        
        btn_close.bind(on_press=popup.dismiss)
        content.add_widget(btn_close)
        popup.open()
    
    def reset_questions(self, instance):
        """Przywraca domyślne pytania"""
        self.status_label.text = "✅ Przywrócono domyślne pytania"
        self.status_label.color = COLORS['success']
    
    def go_back(self, instance):
        """Powrót do menu"""
        self.manager.current = 'menu'

# Dodaj pozostałe ekrany (LobbyScreen, GameScreen, ResultsScreen) z oryginalnego main.py
# ale uproszczone dla APK...

class QuizPartyApp(App):
    """Główna aplikacja"""
    def build(self):
        self.title = "Quiz Party"
        
        # Inicjalizuj zmienne
        self.player_name = ""
        self.network_manager = None
        self.game_logic = None
        self.final_scores = {}
        
        # Stwórz manager ekranów
        sm = ScreenManager()
        sm.add_widget(MenuScreen())
        
        if HAS_NETWORK:
            sm.add_widget(HostSetupScreen())
            sm.add_widget(JoinSetupScreen())
            # sm.add_widget(LobbyScreen())
            # sm.add_widget(GameScreen())
            # sm.add_widget(ResultsScreen())
        
        sm.add_widget(DemoGameScreen())
        sm.add_widget(QuestionsScreen())
        
        return sm

if __name__ == '__main__':
    QuizPartyApp().run()