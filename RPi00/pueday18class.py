
import RPi.GPIO as GPIO    #Importamos la libreria RPi.GPIO
from time import sleep 
import grovepi
import threading
import paho.mqtt.client as mqtt
import base64
import picamera

class door(object):
    """Door class, it's possible to open an close"""
    def __init__(self, channel ):
        self.channel = channel
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.channel,GPIO.OUT)
        self.status = 1
        self.close()
         
    def close(self):
        if self.status:
            p = GPIO.PWM(self.channel,50)
            p.start(3.5) 
            sleep(0.5)
            p.stop()
            self.status=0
    
    def open(self):
        if not self.status:
            p = GPIO.PWM(self.channel,50)
            p.start(7.0) 
            sleep(0.5)
            p.stop()
            self.status=1


class doorbell(object):
    """Buzzer and button to simulate doorbeell"""
    def __init__(self,buzzer_channel, button_channel, mqtt_client, topic, photo,qos=0):
        self.buzzer_channel = buzzer_channel
        self.button_channel = button_channel
        self.mqtt_client = mqtt_client
        self.topic = topic
        self.qos=qos
        self.photo = photo
        grovepi.pinMode(self.button_channel, 'INPUT')
        grovepi.pinMode(self.buzzer_channel, 'OUTPUT')
        

    def ring(self):
        self.run = True
        mqtt_not = False
        repeatnot = 0
        delay = 0
        ring = False
        while self.run:
            if grovepi.digitalRead(self.button_channel):
                grovepi.analogWrite(self.buzzer_channel, 30)
                delay = 0
                if not ring:
                    self.mqtt_client.publish(self.topic,'1',self.qos)
                    ring = True
                    self.photo.take()
            else:
                if delay >= 20 and ring :
                    self.mqtt_client.publish(self.topic,'0',self.qos)
                    ring = False
                    delay = 0
                delay = (delay + 1) % 100    
                grovepi.analogWrite(self.buzzer_channel, 0)
            sleep(0.25)

            
    def start_loop_ring(self):
        t1 = threading.Thread(target=self.ring)
        t1.start()
    def stop_loop_ring(self):
        self.run=False

class sensor(object):
    
    def __init__(self,channel,time,mqtt_client,topic,qos=0):
        self.channel=channel
        self.mqtt_client = mqtt_client
        self.topic = topic
        self.qos=qos
        self.time=time
    def get_data(self):
        return 1
    def loop(self):
        self.run = True
        while self.run:
            self.mqtt_client.publish(self.topic,self.get_data(),self.qos)
            sleep(self.time)
    def start_loop(self):
        
        t1 = threading.Thread(target=self.loop)
        t1.start()
    def stop_loop(self):
        self.run=False

class ldr_sensor(sensor):
    def get_data(self):
        return grovepi.analogRead(self.channel)

        
class dht_sensor(object):
    def __init__(self,channel,time,mqtt_client,topic_temp, topic_hum,qos=0):
        self.topic_temp = topic_temp
        self.topic_hum = topic_hum
        self.channel=channel
        self.mqtt_client = mqtt_client

        self.qos=qos
        self.time=time
        grovepi.pinMode(self.channel, 'INPUT')
    def get_data(self):
        return grovepi.dht(self.channel,0)
    def loop(self):
        self.run = True

        while self.run:
            [temp, hum] = self.get_data()
            self.mqtt_client.publish(self.topic_temp,temp,self.qos)
            self.mqtt_client.publish(self.topic_hum,hum,self.qos)
            sleep(self.time)
        
    def start_loop(self):
        
        t1 = threading.Thread(target=self.loop)
        t1.start()
    def stop_loop(self):
        self.run=False

class leds(object):
    def __init__(self, leds: list):
        self.leds_channels= leds
        for l in self.leds_channels:
            grovepi.pinMode(l, 'OUTPUT')
            grovepi.digitalWrite(l,1)
            sleep(1)
            grovepi.digitalWrite(l,0)
    def on(self):
        for l in self.leds_channels:
            grovepi.digitalWrite(l,1)
    def off(self):
        for l in self.leds_channels:
            grovepi.digitalWrite(l,0)
class photo(object):
    def __init__(self,mqtt_client,topic,qos=0):
        self.mqtt_client = mqtt_client
        self.topic = topic
        self.qos = qos
    def take(self):
        with picamera.PiCamera() as picam:
                #picam.resolution = (720, 480)
                picam.capture('/tmp/photo.jpg')
                picam.close()
        byteArray = base64.b64encode(open('/tmp/photo.jpg','rb').read())
        self.mqtt_client.publish(self.topic,byteArray,self.qos)
