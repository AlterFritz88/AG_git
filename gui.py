from kivy.lang import Builder
from kivy.app import App
from kivy.uix.anchorlayout import AnchorLayout
import serial
from pynput import keyboard
import threading
import time
from kivy.core.window import Window
Builder.load_file('kivy_ui.kv')
#sudo chmod a+rw /dev/tty
break_program = False
class Main(AnchorLayout):
    pass
#f
def hex2bin(str, lenght):
    """
    Переводчик hex, oct str в bin str
    """
    a = int(str)
    return format(a, '0>{}b'.format(lenght))

class AG398(App):


    serv_adr = '000000'
    serv_data = '00'



    def build(self):
        self.data_mem_read_1 = [{'row_id': x, 'text': str(0x0)} for x in range(32)]
        self.adress_pam_1 = [{'a_number': str(x)} for x in range(0, 32)]
        self.data_mem_read_2 = [{'row_id': x, 'text': str(0x0)} for x in range(32)]
        self.adress_pam_2 = [{'a_number': str(x)} for x in range(32, 64)]
        self.serv_menu_data = [{'row_id': x, 'text': str(0x0)} for x in range(1)]
        return Main()

    def read_mem(self):
        vuo = int(self.root.ids._general_menu.ids._vuo.text)
        abonent = int(self.root.ids._general_menu.ids._abonent.text)
        interface = 0 if self.root.ids._general_menu.ids._posled.active else 1
        vuo = hex2bin(vuo, 5)
        abonent = hex2bin(abonent, 8)
        send = ('10011000', '00'+ str(interface) + '00' + vuo[:3], vuo[3:] + abonent[:6], abonent[6:] + '000000')
        send = [bytes([int(x, 2)]) for x in send]
        ser = serial.Serial('/dev/ttyUSB0', baudrate=1000000, timeout=0.2)
        for dat in send:
            ser.write(dat)
        response_1 = []
        for i in range(32):
            response_1.append(ser.read(4))

        response_2 = []
        for i in range(32):
            response_2.append(ser.read(4))
        response_1 = [str(hex(int.from_bytes(x, 'big'))) for x in response_1]
        response_2 = [str(hex(int.from_bytes(x, 'big'))) for x in response_2]


        for d in range(len(self.data_mem_read_1)):
            self.data_mem_read_1[d].update((k, response_1[d]) for k, v in self.data_mem_read_1[d].items() if k == 'text')
        self.root.ids._mem_info.ids.memory_data_1.refresh_from_data()

        for d in range(len(self.data_mem_read_2)):
            self.data_mem_read_2[d].update((k, response_2[d]) for k, v in self.data_mem_read_2[d].items() if k == 'text')
        self.root.ids._mem_info.ids.memory_data_2.refresh_from_data()


    def read_infinity(self):
        self.root.ids._general_menu.ids.cycle_view_.disabled = True
        global break_program
        def on_press(key):
            global break_program
            print(key)
            if key == keyboard.Key.end:
                print('end pressed')
                break_program = True
                return False

        self.potok = threading.Thread(target=self.read_mem)
        self.potok.start()
        with keyboard.Listener(on_press=on_press) as listener:
            while break_program == False:
                self.read_mem()
                time.sleep(0.1)
                print(1)
            listener.join()
            break_program = False
            self.root.ids._general_menu.ids.cycle_view_.disabled = False

    def erase_mem(self):
        ser = serial.Serial('/dev/ttyUSB0', baudrate=1000000, timeout=0.2)
        ser.write(b'\x81')
        time.sleep(1)

    def write_serv_data(self):
        ser = serial.Serial('/dev/ttyUSB0', baudrate=1000000, timeout=0.5)
        print(self.serv_adr)
        adr1 = bytes([int(self.serv_adr[:2], 16)])
        adr2 = bytes([int(self.serv_adr[2:4], 16)])
        adr3 = bytes([int(self.serv_adr[4:], 16)])
        data = bytes([int(self.serv_data, 16)])
        for inf in [b'\x84', adr1, adr2, adr3, data]:
            ser.write(inf)
            print(inf)
        time.sleep(0.1)
        for inf_r in [b'\x88', adr1, adr2, adr3]:
            ser.write(inf_r)
            print(inf_r)
        ans = []
        for i in range(3):
            ans.append(ser.read(1))
        ans = hex(int.from_bytes(ans[2], 'big'))
        self.serv_menu_data[0].update({'a_number': ans})
        print('ответ', ans)



    def filter_serv_data(self, data):
        alloed_chars = '1234567890ABCDEFabcdef'
        return_data = ''.join([x for x in data if x in alloed_chars])
        if len(return_data) < 2:
            return_data = '0'*(2-len(return_data)) + return_data
        return return_data

    def filter_serv_adr(self, data):
        alloed_chars = '1234567890ABCDEFabcdef'
        return_data = ''.join([x for x in data if x in alloed_chars])
        if len(return_data) < 6:
            return_data = '0'*(6-len(return_data)) + return_data
        return return_data

    def go_potok(self):
        self.potok = threading.Thread(target=self.read_infinity)
        self.potok.start()

    def filter_zup(self, number):
        print(number)
        try:
            return int(number)
        except:
            return number

    def toggle_change_state(self, x1, x2):
        print(x1.state)
        if x1.state == 'normal':
            return 'down'
        else:
            return 'normal'

Window.size = (1366, 1000)

if __name__ == "__main__":
    AG398().run()