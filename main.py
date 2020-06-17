import os
import sys
import webbrowser 

from kivy.lang import Builder
from kivy.utils import platform
from kivy.logger import Logger
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.floatlayout import FloatLayout
from kivy.utils import get_color_from_hex
from kivy.core.clipboard import Clipboard
from kivy.properties import (
    StringProperty,
    NumericProperty,
    ListProperty,
    OptionProperty,
    BooleanProperty,
)
from kivy.metrics import dp
from kivy.clock import Clock

from kivymd.app import MDApp
from kivymd.theming import ThemableBehavior
from kivymd.uix.behaviors import RectangularRippleBehavior
import kivymd.material_resources as m_res
from kivymd.font_definitions import theme_font_styles
from kivymd.toast import toast
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton, MDRaisedButton

from libs.baseclass.dialog_change_theme import KitchenSinkDialogChangeTheme
from libs.baseclass.list_items import KitchenSinkOneLineLeftIconItem

from datetime import datetime
from threading import Thread
import requests
from urllib import parse
from queue import Empty, Queue
from hurry.filesize import alternative, size
import time
import sqlite3
from ago import human
from functools import partial
from libs.baseclass.dialog_change_theme import PSTDialogInput
from database import MyDb

dbRW = MyDb()
dbRW.create()

__version__ = "1.4"
Logger.info(f"App Version: v{__version__}")

if platform == "android":
    from kivmob import KivMob, TestIds
    from android.runnable import run_on_ui_thread
    from jnius import autoclass

    Color = autoclass("android.graphics.Color")
    WindowManager = autoclass('android.view.WindowManager$LayoutParams')
    activity = autoclass('org.kivy.android.PythonActivity').mActivity
else:
    def run_on_ui_thread(d):
        # print(f"nice! {d}")
        pass


if getattr(sys, "frozen", False):  # bundle mode with PyInstaller
    os.environ["KITCHEN_SINK_ROOT"] = sys._MEIPASS
    os.environ["KITCHEN_SINK_ASSETS"] = os.path.join(
    os.environ["KITCHEN_SINK_ROOT"], f"assets{os.sep}"
    )
    Logger.info("___one___")
else:
    sys.path.append(os.path.abspath(__file__).split("ProxySpeedTestV2")[0])
    os.environ["KITCHEN_SINK_ROOT"] = os.path.dirname(os.path.abspath(__file__))
    os.environ["KITCHEN_SINK_ASSETS"] = os.path.join(
    os.environ["KITCHEN_SINK_ROOT"], f"assets{os.sep}"
    )
    Logger.info("___two___")
# from kivy.core.window import Window
# Window.softinput_mode = "below_target"
# _small = 2
# Window.size = (1080/_small, 1920/_small)

class adMobIds:

    """ Test AdMob App ID """
    APP = "ca-app-pub-3940256099942544~3347511713"

    """ Test Banner Ad ID """
    BANNER = "ca-app-pub-3940256099942544/6300978111"
    
    # """ Test Interstitial Ad ID """
    # INTERSTITIAL = "ca-app-pub-3940256099942544/1033173712"

    # """ Test Interstitial Video Ad ID """
    # INTERSTITIAL_VIDEO = "ca-app-pub-3940256099942544/8691691433"

    # """ Test Rewarded Video Ad ID """
    # REWARDED_VIDEO = "ca-app-pub-3940256099942544/5224354917"


class ProxyShowList(ThemableBehavior, RectangularRippleBehavior, ButtonBehavior, FloatLayout):
    """A one line list item."""

    _txt_top_pad = NumericProperty("16dp")
    _txt_bot_pad = NumericProperty("15dp")  # dp(20) - dp(5)
    _height = NumericProperty()
    _num_lines = 1
    
    text = StringProperty()
    text1 = StringProperty()
    text2 = StringProperty()
    text3 = StringProperty()

    text_color = ListProperty(None)

    theme_text_color = StringProperty("Primary", allownone=True)

    font_style = OptionProperty("Caption", options=theme_font_styles)


    divider = OptionProperty(
        "Full", options=["Full", "Inset", None], allownone=True
    )

    bg_color = ListProperty()

    _txt_left_pad = NumericProperty("16dp")
    _txt_top_pad = NumericProperty()
    _txt_bot_pad = NumericProperty()
    _txt_right_pad = NumericProperty(m_res.HORIZ_MARGINS)
    _num_lines = 3
    _no_ripple_effect = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.height = dp(48) if not self._height else self._height

def sec_to_mins(seconds):
    a = str(round((seconds % 3600)//60))
    b = str(round((seconds % 3600) % 60))
    d = f"{a} m {b} s"
    return d

def agoConv(datetimeStr):
    if datetimeStr:
        _ago = human(datetime.strptime(datetimeStr, '%Y-%m-%d %H:%M:%S.%f'),
        abbreviate=True)
        if 's' in _ago[:3]:
            return 'now' 
        else:
            return _ago
    else:
        return 'Pic a list'

def open_link(link):
    webbrowser.open(link)
    return True

class ProxySpeedTestApp(MDApp):
    icon = f"{os.environ['KITCHEN_SINK_ASSETS']}icon.png"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.version = __version__
        self.theme_cls.primary_palette = "LightBlue"
        self.dialog_change_theme = None
        self.toolbar = None
        self.scaning = Queue()
        self.running = Queue()
        self.currentSpeed = Queue()

        self.pbar0 = Queue()
        self.pbar1 = Queue()
        self.pbar2 = Queue()

          
        configs = dbRW.getAllConfigs()
        mirrors = dbRW.getAllMirrors()

        self.selLId = configs[0][2]
        if self.selLId:
            getips = dbRW.getAllCurrentProxys(self.selLId)
            protocol = getips[0][4]

        self.scan_list = []
        if self.selLId:
            for l in getips:
                if not None in l:
                    self.scan_list.append({"IP": l[0], "SIZE": l[1], "TIME": l[2], "SPEED": l[3]})

        self.theme_cls.theme_style = configs[0][0]
        
        miInx = configs[0][1]
        self.configs = {
            'protocol': protocol if self.selLId else 'http',
            'mirror': mirrors[miInx][0],
            'timeout': int(configs[0][3]),
            'fileSize': int(configs[0][4]),
            'miInx': miInx,
            'proxysInx': [],
            'mirrors': mirrors,
            'proxys': [ip[0] for ip in getips] if self.selLId else []
            }

    def on_resume(self):
        self.ads.request_interstitial()

    def changeThemeMode(self, inst):
        self.theme_cls.theme_style = inst

        dbRW.updateThemeMode(inst)


    def checkUpdates(self, ava=False, d=False):
        # print(ava)
        upCURL = 'https://raw.githubusercontent.com/biplobsd/proxySpeedTestApp/master/updates.json'
        # from json import load
        # with open('updates.json', 'r') as read:
        #     updateinfo = load(read)
        toast("Checking for any updates ...")
        try:
            updateinfo = requests.get(upCURL).json()
        except:
            updateinfo = {
                "version": float(self.version),
                "messages": "",
                "changelogs": "",
                "force": "false",
                "release": {
                    "win": "",
                    "linux": "",
                    "android": "",
                    "macosx": "",
                    "unknown": "",
                    "kivy_build": ""
                }
            }
            # toast("Faild app update check!")
        if updateinfo:
            try:
                appLink = updateinfo["release"][platform]
            except KeyError:
                return
            title = f"App update v{updateinfo['version']}" 
            msg = "You are already in latest version!"
            b1 = "CENCEL"
            force = False

            if updateinfo['version'] > float(self.version) and appLink != "":
                if updateinfo['messages']:title = updateinfo['messages']
                msg = ""
                b2 = "DOWNLOAD"
                force = bool(updateinfo['force'])
                if force:
                    b1 = "EXIT"
                ava = True
            else:
                b2 = "CHECK"

            self.updateDialog = MDDialog(
                title=title,
                text=msg+updateinfo['changelogs']+f"\n\n[size=15]Force update: {force}[/size]",
                auto_dismiss=False,
                buttons=[
                    MDFlatButton(
                        text=b1, 
                        text_color=self.theme_cls.primary_color,
                        on_release=lambda x: self.updateDialog.dismiss() if b1 == "CENCEL" else self.stop()
                    ),
                    MDRaisedButton(
                        text=b2,
                        on_release=lambda x:open_link(appLink) if b2 == "DOWNLOAD" else self.FCU(self.updateDialog),
                        text_color=self.theme_cls.primary_color
                    ),
                ],
            )
            self.updateDialog.ids.title.theme_text_color = "Custom"
            self.updateDialog.ids.title.text_color = self.theme_cls.primary_light
            if ava:self.updateDialog.open()

    def FCU(self, inst):
        inst.dismiss()
        Clock.schedule_once(partial(self.checkUpdates, True))


    def on_pause(self):
        return True

    def save_Update(self, l=[], filename='scan_data.json'):
        import json
        if l:
            with open(filename, 'w') as write:
                json.dump(l, write, indent=4)
        else:
            if os.path.exists(filename):
                with open(filename, 'r') as read:
                    return json.load(read)
            else:
                return False
    
    def save_UpdateDB(self, l=[]):
        dbRW = MyDb()
        if l:dbRW.updateScanList(l)

    def build(self):
        if platform == "android":
            self._statusBarColor()
        Builder.load_file(
            f"{os.environ['KITCHEN_SINK_ROOT']}/libs/kv/list_items.kv"
        )
        Builder.load_file(
            f"{os.environ['KITCHEN_SINK_ROOT']}/libs/kv/dialog_change_theme.kv"
        )
        
        return Builder.load_file(
            f"{os.environ['KITCHEN_SINK_ROOT']}/libs/kv/start_screen.kv"
        )

    @run_on_ui_thread
    def _statusBarColor(self, color="#03A9F4"):
        
        window = activity.getWindow()
        window.clearFlags(WindowManager.FLAG_TRANSLUCENT_STATUS)
        window.addFlags(WindowManager.FLAG_DRAWS_SYSTEM_BAR_BACKGROUNDS)
        window.setStatusBarColor(Color.parseColor(color)) 
        window.setNavigationBarColor(Color.parseColor(color))


    def show_dialog_change_theme(self):
        if not self.dialog_change_theme:
            self.dialog_change_theme = KitchenSinkDialogChangeTheme()
            self.dialog_change_theme.set_list_colors_themes()
        self.dialog_change_theme.open()

    def on_start(self):
        """Creates a list of items with examples on start screen."""

        unsort = self.scan_list
        # print(unsort)
        if unsort:
            sort = sorted(unsort, key=lambda x: x['SPEED'], reverse=True)
            self.show_List(sort)
            self.root.ids.Tproxys.text = f"Total proxys: {len(sort)}"
        else:
            self.root.ids.Tproxys.text = f"Total proxys: 0"
        self.root.ids.Sprotocol.text = f"Protocol: {self.configs['protocol'].upper()}"
        self.root.ids.Smirror.text = f"Mirror: {parse.urlparse(self.configs['mirror']).netloc}".upper()
        # self.root.ids.backdrop._front_layer_open=True
        Logger.info(f"Platform: {platform}")
        if platform == 'android':
            self.ads = KivMob(adMobIds.APP)
            self.ads.new_banner(adMobIds.BANNER, top_pos=False)
            self.ads.request_banner()
            self.ads.show_banner()

            self.root.ids.adsShow.size = (self.root.ids.backdrop_front_layer.width, 110)
        
        self.mirrorPic()
        self.protPic()
        self.listPic()
        Clock.schedule_once(partial(self.checkUpdates, False))

    def listPic(self):

        proxysInx = dbRW.getProxysInx()
        self.selLId = dbRW.getConfig('proxysInx')[0]
        Logger.debug(self.selLId)
        self.configs['proxysInx'] = proxysInx
        
        if proxysInx:
            selLIdindxDict = {}
            self.ListItems = []
            i = 0
            for Inx in proxysInx:
                self.ListItems.append({"icon": "playlist-remove", "text": f'#{i} '+agoConv(Inx[0])})
                selLIdindxDict[Inx[0]] = i
                i += 1
        else:
            self.ListItems = [{"icon": "playlist-remove", "text": "None"}]
        
        if proxysInx:
            self.selLIdindx = selLIdindxDict[self.selLId]
        self.root.ids.Slist.text = f"list : #{self.selLIdindx} {agoConv(self.selLId)}".upper() if proxysInx else "list :"

        self.listSel = MDDropdownMenu(
            caller=self.root.ids.Slist, items=self.ListItems, width_mult=3,
            opening_time=0.2,
            use_icon_item=False,
            position='auto',
            max_height=0,
            callback=self.set_list,
        )

    def set_list(self, ins):
        import re
        self.selLIdindx = int(re.search(r'#(\d)\s', ins.text).group(1))
        # withoutHash = re.search(r'#\d\s(.+)', ins.text).group(1)
        Logger.debug(self.selLIdindx)

        proxysInx = dbRW.getProxysInx()
        self.selLId = proxysInx[self.selLIdindx][0]
        proxys = dbRW.getAllCurrentProxys(self.selLId)
        protocol = proxys[0][4]
        dbRW.updateConfig("proxysInx", self.selLId)
        scan_list = proxys

        self.scan_list = []
        if self.selLId:
            for l in scan_list:
                if not None in l:
                    self.scan_list.append({"IP": l[0], "SIZE": l[1], "TIME": l[2], "SPEED": l[3]})

        unsort = self.scan_list
        if unsort:
            sort = sorted(unsort, key=lambda x: x['SPEED'], reverse=True)
            # print(sort)
            self.show_List(sort)

        self.configs['proxys'] = [ip[0] for ip in proxys]
        self.configs['protocol'] = protocol

        self.root.ids.Slist.text = f"list : {ins.text}".upper()
        self.root.ids.Sprotocol.text = f"Protocol: {self.configs['protocol'].upper()}"
        self.root.ids.Tproxys.text = f"Total proxys: {len(self.configs['proxys'])}"
        
        # print(getips)
        toast(ins.text)
        # print(indx)
        self.listSel.dismiss()


    def protPic(self):
        items = [{"icon": "protocol", "text": protocol.upper()} for protocol in ['http', 'https', 'socks4', 'socks5']]
        self.protSel = MDDropdownMenu(
            caller=self.root.ids.Sprotocol, items=items, width_mult=2,
            opening_time=0.2,
            use_icon_item=False,
            position='auto',
            callback=self.set_protocol
        )

    def set_protocol(self, ins):
        self.configs['protocol'] = ins.text.lower()
        self.root.ids.Sprotocol.text = f"Protocol: {self.configs['protocol'].upper()}"
        
        toast(self.configs['protocol'])
        self.protSel.dismiss()

    def mirrorPic(self):

        mirrors = dbRW.getAllMirrors()

        self.configs['mirrors'] = mirrors
        items = [{"icon": "web", "text": parse.urlparse(mirror[0]).netloc} for mirror in mirrors]
        self.mirrSel = MDDropdownMenu(
            caller=self.root.ids.Smirror, items=items, width_mult=5,
            opening_time=0.2,
            use_icon_item=False,
            position='auto',
            max_height=0,
            callback=self.set_mirror,
        )

    def set_mirror(self, ins):
        miInx = 0
        for l in self.configs['mirrors']:
            if ins.text in l[0]:
                break
            miInx += 1
        
        self.configs['mirror'] = self.configs['mirrors'][miInx][0]
        self.root.ids.Smirror.text = f"Mirror: {ins.text}".upper()
        
  
        dbRW.updateConfig("proxysInx", self.selLId)
        dbRW.updateConfig("miInx", self.configs['miInx'])
        
        toast(self.configs['mirror'])
        self.mirrSel.dismiss()
    
    def update_screen(self, dt):
        try:
            while not self.pbar0.empty():
                sp = self.pbar0.get_nowait()
                if sp != 0:
                    self.root.ids.progressBar1.value += sp
                else:
                    self.root.ids.progressBar1.value = 0
        except Empty:
            pass
        
        try:
            while not self.pbar1.empty():
                sp = self.pbar1.get_nowait()
                if sp != 0:
                    self.root.ids.progressBar2.value += sp
                else:
                    self.root.ids.progressBar2.value = 0
        except Empty:
            pass
        
        try:
            while not self.pbar2.empty():
                sp = self.pbar2.get_nowait()
                if sp != 0:
                    self.root.ids.progressBar3.value += sp
                else:
                    self.root.ids.progressBar3.value = 0
        except Empty:
            pass
        
        self.speedcal()

        self.root.ids.Slist.text = f"list : #{self.selLIdindx} {agoConv(self.selLId)}".upper()


    def start_scan(self, instance):
        # print("Clicked!!")
        if instance.text == "Start":
            self.mirrorPic()
            self.listPic()

            self.root.ids.Tproxys.text = f"Total proxys: {len(self.configs['proxys'])}"
            if len(self.configs['proxys']) == 0:
                try:
                    if self.configs['proxysInx']:
                        self.listSel.open()
                        toast("Pick that list!")        
                        return
                except:
                    pass
                PSTDialogInput().open()
                toast("First input proxys ip:port list then start scan.")
                return

            instance.text = "Stop"
            color = "#f44336"
            instance.md_bg_color = get_color_from_hex(color)
            self.theme_cls.primary_palette = "Red"
            if platform == "android":self._statusBarColor(color)
            self.scaning.put_nowait(1)
            self.running.put_nowait(1)
            

            IndexTime = datetime.now()
            dbRW.updateConfig('proxysInx', IndexTime)
            dbRW.updateProxysInx(IndexTime, self.selLId)
            dbRW.updateProxys(IndexTime, self.selLId)

            configs = dbRW.getAllConfigs()

            self.configs['timeout'] = int(configs[0][3])
            self.configs['fileSize'] = int(configs[0][4])
            self.selLId = str(IndexTime)

            self.upScreen = Clock.schedule_interval(self.update_screen, 0.1)

            Thread(target=self.proxySpeedTest, args=(
                self.configs['proxys'],
                self.configs['protocol'],
                self.configs['mirror'],
                )).start()
        
            # self.proxySpeedTest('start')
        elif instance.text == "Stoping":
            toast(f"Waiting for finish {self.root.ids.currentIP.text[8:]}!")
        else:
            while not self.scaning.empty():
                self.scaning.get_nowait()
            

            if not self.running.empty():
                instance.text = "Stoping"
                # instance.text_color
                color = "#757575"
                instance.md_bg_color = get_color_from_hex(color)
                self.theme_cls.primary_palette = "Gray"
                if platform == "android":self._statusBarColor(color)
            
    
    def downloadChunk(self, idx, proxy_ip, filename, mirror, protocol):
        Logger.info(f'Scaning {idx} : Started')
        try:
            if protocol == 'http':
                proxies = {
                    'http': f'http://{proxy_ip}',
                    'https': f'http://{proxy_ip}'
                }
            elif protocol == 'https':
                proxies = {
                    'http': f'https://{proxy_ip}',
                    'https': f'https://{proxy_ip}'
                }
            elif protocol == 'socks4':
                proxies = {
                    'http': f'socks4://{proxy_ip}',
                    'https': f'socks4://{proxy_ip}'
                }
            elif protocol == 'socks5':
                proxies = {
                    'http': f'socks5://{proxy_ip}',
                    'https': f'socks5://{proxy_ip}'
                }

            req = requests.get(
                mirror,
                headers={"Range": "bytes=%s-%s" % (0, self.configs['fileSize'])},
                stream=True,
                proxies=proxies,
                timeout=self.configs['timeout']
            )
            with(open(f'{filename}{idx}', 'ab')) as f:
                start = datetime.now()
                chunkSize = 0
                oldSpeed = 0
                chunkSizeUp = 1024
                for chunk in req.iter_content(chunk_size=chunkSizeUp):
                    end = datetime.now()
                    if 0.1 <= (end-start).seconds:
                        delta = round(float((end - start).seconds) +
                                    float(str('0.' + str((end -
                                                            start).microseconds))), 3)
                        speed = round((chunkSize) / delta)
                        # if oldSpeed < speed:
                            # chunkSizeUp *= 3
                        # else:
                        #     chunkSizeUp = speed
                        oldSpeed = speed
                        start = datetime.now()
                        self.currentSpeed.put_nowait(speed)
                        chunkSize = 0
                    if chunk:
                        chunkSize += sys.getsizeof(chunk)
                        self.showupdate(idx)
                        f.write(chunk)
        except requests.exceptions.ProxyError:
            self.showupdate(idx, 'd')
            Logger.info(f"Thread {idx} : Could not connect to {proxy_ip}")
            return False
        except requests.exceptions.ConnectionError:
            self.showupdate(idx, 'd')
            Logger.info(f"Thread {idx} : Could not connect to {proxy_ip}")
            return False
        except IndexError:
            self.showupdate(idx, 'd')
            Logger.info(f'Thread {idx} : You must provide a testing IP:PORT proxy')
            return False
        except requests.exceptions.ConnectTimeout:
            self.showupdate(idx, 'd')
            Logger.info(f"Thread {idx} : ConnectTimeou for {proxy_ip}")
            return False
        except requests.exceptions.ReadTimeout:
            self.showupdate(idx, 'd')
            Logger.info(f"Thread {idx} : ReadTimeout for {proxy_ip}")
            return False
        except RuntimeError:
            self.showupdate(idx, 'd')
            Logger.info(f"Thread {idx} : Set changed size during iteration. {proxy_ip}")
            return False
        except KeyboardInterrupt:
            self.showupdate(idx, 'd')
            Logger.info(f"Thread no {idx} : Exited by User.")
        
        self.showupdate(idx, 'd')
    
    def showupdate(self, idx, mode='u', error=True):
        if mode == 'u':
            if idx == 0:
                self.pbar0.put_nowait(1)
            elif idx == 1:
                self.pbar1.put_nowait(1)
            elif idx == 2:
                self.pbar2.put_nowait(1)
        elif mode == 'd':
            # color = "#f44336"
            if idx == 0:
                self.pbar0.put_nowait(0)
            elif idx == 1:
                self.pbar1.put_nowait(0)
            elif idx == 2:
                self.pbar2.put_nowait(0)
            
            self.root.ids.top_text.text = "0 KB/s"
    
    def proxySpeedTest(self, proxys, protocol, mirror):
        filename = 'chunk'
        unsort = list()
        sort = list ()
        self.root.ids.totalpb.max = len(proxys)
        self.root.ids.totalpb.value = 0
        Logger.debug(proxys)
        for part in proxys:
            if self.scaning.empty():break        
            proxy_ip = part.strip()
            self.root.ids.currentIP.text = f"CURRENT: {proxy_ip}"
            # Removing before test chunk file
            for i in range(3):
                if os.path.exists(f'{filename}{i}'):
                    os.remove(f'{filename}{i}')

            # Starting chunk file downloading
            timeStart = datetime.now()
            Logger.info("Scan : Starting ....")
            downloaders = [
            Thread(
                target=self.downloadChunk,
                args=(idx, proxy_ip, filename, mirror, protocol),
            )
            for idx in range(3)]
            for _ in downloaders:_.start()
            for _ in downloaders:_.join()
            timeEnd = datetime.now()

            filesize = 0
            for i in range(3):
                try:
                    filesize = filesize + os.path.getsize(f'{filename}{i}')
                except FileNotFoundError:
                    continue

            filesizeM = round(filesize / pow(1024, 2), 2)
            delta = round(float((timeEnd - timeStart).seconds) +
                        float(str('0.' + str((timeEnd -
                                                timeStart).microseconds))), 3)
            speed = round(filesize) / delta

            for i in range(3):
                if os.path.exists(f'{filename}{i}'):
                    os.remove(f'{filename}{i}')

            unsort.append(
                {'IP': proxy_ip,
                'SIZE': filesizeM, 
                'TIME': delta,
                'SPEED': int(speed)}
                )
            sort = self.sort_Type(unsort)
            self.save_UpdateDB(sort)
            self.root.ids.totalpb.value += 1
            comP = (self.root.ids.totalpb.value/len(proxys))*100
            self.root.ids.totalpbText.text = f"{round(comP)}%"
            # return True
        
        self.upScreen.cancel()
        self.root.ids.start_stop.text = "Start"
        self.theme_cls.primary_palette = "LightBlue"
        self.root.ids.start_stop.md_bg_color = self.theme_cls.primary_color
        if platform == "android":self._statusBarColor()
        while not self.running.empty():
            self.running.get_nowait()
        Logger.info("Scan : Finished!")

    def sort_Change(self, inst, ckid):
        if ckid and inst.active:
            self.sort_Type(self.data_lists, mode=inst.text, reverse=False)
            inst.active = False
        elif ckid and inst.active == False:
            self.sort_Type(self.data_lists, mode=inst.text, reverse=True)
            inst.active = True


    def sort_Type(self, unsort, mode='SPEED', reverse=True):
        if mode == 'SERVER':mode = 'IP'

        sort = sorted(unsort, key=lambda x: x[mode], reverse=reverse)
        self.show_List(sort)
        return sort

    def show_List(self, data): 
        self.root.ids.backdrop_front_layer.data = []
        for parServer in data:
            self.root.ids.backdrop_front_layer.data.append(
                {
                    "viewclass": "ProxyShowList",
                    "text": parServer['IP'],
                    "text1": f"{parServer['SIZE']} MB",
                    "text2": sec_to_mins(float(parServer['TIME'])),
                    "text3": f"{size(parServer['SPEED'], system=alternative)}/s",
                    "on_release": lambda x=parServer['IP']: self.copy_proxyip(x),
                }
                )
        self.data_lists = data
    def copy_proxyip(self, data):
        toast(f"Copied: {data}")
        Clipboard.copy(data)
    
    def speedcal(self):
        speed = 0
        try:
            while not self.currentSpeed.empty():
                speed += self.currentSpeed.get_nowait()
        except Empty:
            pass
        
        if speed != 0:
            self.root.ids.top_text.text = f"{size(speed, system=alternative)}/s"
        

if __name__ == "__main__":
    ProxySpeedTestApp().run()