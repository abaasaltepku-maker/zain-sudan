from kivy.app import App
from kivy.uix.button import Button
import requests

class GhostApp(App):
    def build(self):
        btn = Button(text='ACTIVATE')
        btn.bind(on_press=self.send_msg)
        return btn

    def send_msg(self, instance):
        url = 'https://discord.com/api/webhooks/YOUR_ID'
        try:
            # تم تصحيح طريقة الإرسال هنا لضمان عدم تعليق التطبيق
            response = requests.post(url, json={'content': 'COMMAND EXECUTED'}, timeout=5)
            if response.status_code == 204 or response.status_code == 200:
                instance.text = 'SENT SUCCESS'
            else:
                instance.text = f'ERROR: {response.status_code}'
        except Exception as e:
            instance.text = 'NETWORK ERROR'

if __name__ == '__main__':
    GhostApp().run()
