from nxt.sensor import PORT_1, PORT_2, PORT_3, PORT_4, Touch, Color20, Ultrasonic, Type, Sound, Light
from nxt.usbsock import USBSock, ID_VENDOR_LEGO, ID_PRODUCT_NXT
import usb
import time

NXT_SENSOR_PORTS = {1: PORT_1, 2: PORT_2, 3: PORT_3, 4: PORT_4}
NXT_SENSORS = [('button'), ('distance'), ('color'), ('light'), ('sound'), ('gray')]

ERROR = -1

class NxtSensorPlugin():
    def __init__(self):
        self._bricks = []
        self.active_nxt = 0
        self.refresh()

    def getLight(self, port):
        if self._bricks:
            try:
                port = int(port)
            except:
                pass
            if (port in NXT_SENSOR_PORTS):
                res = ERROR
                #try:
                port_aux = NXT_SENSOR_PORTS[port]
                sensor = Light(self._bricks[self.active_nxt], port_aux)
                sensor.set_illuminated(False)
                res = sensor.get_lightness()
                #except:
                    #pass
                print port
                print res
                return res
            else:
                pass
        else:
            pass

    def getLightColor(self, port):
        if self._bricks:
            try:
                port = int(port)
            except:
                pass
            if (port in NXT_SENSOR_PORTS):
                res = ERROR
                try:
                    port_aux = NXT_SENSOR_PORTS[port]
                    sensor = Light(self._bricks[self.active_nxt], port_aux)
                    res = sensor.get_lightness()
                except:
                    pass
                return res
            else:
                pass
        else:
            pass

    def getGray(self, port):
        if self._bricks:
            try:
                port = int(port)
            except:
                pass
            if (port in NXT_SENSOR_PORTS):
                res = ERROR
                try:
                    port_aux = NXT_SENSOR_PORTS[port]
                    sensor = Light(self._bricks[self.active_nxt], port_aux)
                    sensor.set_illuminated(True)
                    res = sensor.get_lightness()
                except:
                    pass
                return res
            else:
                pass
        else:
            pass

    def getButton(self, port):
        if self._bricks:
            try:
                port = int(port)
            except:
                pass
            if (port in NXT_SENSOR_PORTS):
                res = ERROR
                try:
                    port_aux = NXT_SENSOR_PORTS[port]
                    sensor = Touch(self._bricks[self.active_nxt], port_aux)
                    res = sensor.get_sample()
                except:
                    pass
                return res
            else:
                pass
        else:
            pass

    def getDistance(self, port):
        if self._bricks:
           time.sleep(0.5)
           try:
               port = int(port)
           except:
               pass
           if (port in NXT_SENSOR_PORTS):
               res = ERROR
               #try:
               port_aux = NXT_SENSOR_PORTS[port]
               sensor = Ultrasonic(self._bricks[self.active_nxt], port_aux)
               res = sensor.get_sample()
               #except:
                   #pass
               return res
           else:
               pass
        else:
            pass

    def getColor(self, port):
        if self._bricks:
            try:
                port = int(port)
            except:
                pass
            if (port in NXT_SENSOR_PORTS):
                res = ERROR
                try:
                    port_aux = NXT_SENSOR_PORTS[port]
                    sensor = Color20(self._bricks[self.active_nxt], port_aux)
                    res = colors[sensor.get_sample()]
                except:
                    pass
                return res
            else:
                pass
        else:
            pass

    def getSound(self, port):
        if self._bricks:
            try:
                port = int(port)
            except:
                pass
            if (port in NXT_SENSOR_PORTS):
                res = ERROR
                try:
                    port_aux = NXT_SENSOR_PORTS[port]
                    sensor = Sound(self._bricks[self.active_nxt], port_aux)
                    res = sensor.get_sample()
                except:
                    pass
                return res
            else:
                pass
        else:
            pass

    def refresh(self):
        print 'refreshing'
        self.nxt_find()

    def _nxt_search(self):
        ret = []
        devices = []
        try:
            devices = usb.core.find(find_all=True, idVendor=ID_VENDOR_LEGO, idProduct=ID_PRODUCT_NXT)
            print 'devices: '
            print devices
        except:
            print "No devices"
            pass
        for dev in devices:
            ret.append(USBSock(dev))
        print ret
        return ret

    def nxt_find(self):
        self._close_bricks()
        print 'close bricks'
        for dev in self._nxt_search():
            #try:
            b = dev.connect()
            print '***** b *****'
            self._bricks.append(b)
            #except:
                #print 'Could not append'
                #pass

    def select(self, i):
        # The list index begin in 0
        self.refresh()
        try:
            i = int(i)
            i = i - 1
        except:
            pass
        if (i < len(self._bricks)) and (i >= 0):
            self.active_nxt = i
            print 'seleccionado 1'
        else:
            pass

    def _close_bricks(self):
        for b in self._bricks:
            try:
                b.__del__()
            except:
                pass
        self._bricks = []
        self.active_nxt = 0
