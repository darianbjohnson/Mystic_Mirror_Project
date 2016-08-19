#!/usr/bin/python
# Writen by Darian Johnson
# this was build leveraging Mario Cannistra's IoT project - https://www.hackster.io/mariocannistra/radio-astronomy-with-rtl-sdr-raspberrypi-and-amazon-aws-iot-45b617

# This python code runs on the raspberry pi and takes a selfie when a message is recieved from the Alexa skill
# this code is part of the Mystic Mirror Project 
# for questions, contact me on Twitter @DarianBJohnson


import paho.mqtt.client as paho
import os
import socket
import ssl
import uuid
import json
import tinys3

#update with the email address used when you linked the Mystic Mirror skill to your Google account
email = '<ENTER THE EMAIL ADDRESS YOU USED FOR AUTHENTICATION - in lower case>'
s3_bucket = 'mysticmirror' #change this if you plan to use your own Alexa skill and IoT

def on_connect(client, userdata, flags, rc):
    print("Connection returned result: " + str(rc) )
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("#" , 1 )

def on_message(client, userdata, msg):
    #print("topic: "+msg.topic)
    #print("payload: "+str(msg.payload))
    
    #Logic to take the selfie
    if msg.topic =="selfie":
        try:
            #delete old photos
            os.system("rm Photos/*.jpg")
            
            #take a photo using the name passed to us from mqtt message
            photo  = "Photos/" + str(msg.payload) + ".jpg"
            photo = photo.replace("/b'","/")
            photo = photo.replace("'","")
            photo = photo.replace("`","")
            os_string = "fswebcam --no-banner " + photo
            os.system(os_string)
            
            #publish a message letting the magic_mirror presentation layer know that the picture was taken. This is so that the picture can be displayed.
            message = 'success'
            payload = json.dumps({'intent':'selfie-taken','message': 'success' ,'photo': photo})
            mqttc.publish(email +'/display', payload, qos=1)
            #print('published')
            
            #use tinyS3 to upload the photo to AWS S3
            #Note this key only allows write access to the mysticmirror bucket; contact Darian Johnson for the key for this access
            S3_SECRET_KEY = '<ENTER YOUR SECRET KEY>' 
            S3_ACCESS_KEY = '<ENTER YOUR ACCESS KEY>'
            
            conn = tinys3.Connection(S3_ACCESS_KEY,S3_SECRET_KEY,tls=True)
            f = open(photo,'rb')
            conn.upload(photo,f,s3_bucket)
            
            
        except:
            payload = json.dumps({'intent':'selfie-taken','message':'error'})
            mqttc.publish(email +'/display', payload, qos=1)
            message = 'error'
            print('did not publish')
            


mqttc = paho.Client()
mqttc.on_connect = on_connect
mqttc.on_message = on_message
#mqttc.on_log = on_log

#variables to connect to AWS IoT
#Note these certs allow access to send IoT messages; contact Darian Johnson for the certs (if you are building a mystic mirror and want to leverage his solution)
awshost = "data.iot.us-east-1.amazonaws.com"
awsport = 8883
clientId = "MyMagicMirror-" + str(uuid.uuid4())
thingName = "MyMagicMirror"
caPath = "ENTER THE LOCATION OF YOUR *CERT.PEM FILE" #SUCH AS "/home/pi/certs/verisign-cert.pem"
certPath = "ENTER THE LOCATION OF YOUR *PEM.CRT FILE" #SUCH AS "/home/pi/certs/certificate.pem.crt"
keyPath = "ENTER THE LOCATION OF YOUR RIVATE PEM.KEY" #SUCH AS "/home/pi/certs/private.pem.key"

mqttc.tls_set(caPath, certfile=certPath, keyfile=keyPath, cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLSv1_2, ciphers=None)

mqttc.connect(awshost, awsport, keepalive=60)

mqttc.loop_forever() 


    
