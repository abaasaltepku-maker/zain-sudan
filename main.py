from kivy.app import App
from kivy.uix.button import Button
import requests

class GhostApp(App):
    def build(self):
        return Button(text='ACTIVATE SNIPER MODE', background_color=(1,0,0,1))
    
    def send_msg(self, instance):
        url = 'https://discord.com/api/webhooks/1494750497830338594/ZC4tT6St061N9DnKw'
        try:
            requests.post(url, json={'content': '🚀 Sniper Mode Engaged!'})
            instance.text = 'COMMAND SENT!'
        except:
            instance.text = 'ERROR'

if __name__ == '__main__':
    GhostApp().run()
