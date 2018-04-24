import time
import paho.mqtt.client as mqtt
import base64
import os
import redis
r = redis.Redis('localhost',db=0)


def on_message(mosq, obj, msg):
	sensor=msg.topic.split("/")[-1]
	if sensor == "photo":
		with open('now.jpg', 'wb') as fd:
			fd.write(base64.b64decode(msg.payload))
			os.rename("now.jpg", "static/photo.jpg")
	else:
		r.set(sensor, str(msg.payload.decode('utf-8')).encode('utf-8'))


client = mqtt.Client()
client.connect("localhost")
client.subscribe("/lego/out/#",1)
client.on_message = on_message
client.loop_start()
try:
	while True:
		time.sleep(1000)
finally:
	client.loop_stop()

