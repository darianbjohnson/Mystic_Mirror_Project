

from __future__ import print_function

import json
import urllib
import base64
import urllib2
import boto3
import time
import datetime
import uuid

from datetime import date
from datetime import datetime
from datetime import timedelta
from boto3.dynamodb.conditions import Key, Attr

dynamodb = boto3.client('dynamodb')
dynamodb2 = boto3.resource('dynamodb')
sns = boto3.client('sns')
s3 = boto3.client('s3')

def lambda_handler(event, context):

    print(event['email'])
    print(event['time'])
    
    response = dynamodb.get_item(TableName = 'Magic_Mirror_IOT',
            Key={
                 'Email' : {
                  "S" : event['email']
                    }})  

    TopicArn = response['Item']['TopicArn']['S']

    MM_time = datetime.strptime(event['time'], '%m/%d/%Y, %I:%M:%S %p')
    
    table = dynamodb2.Table('Magic_Mirror_Reminders')
    response = table.query(KeyConditionExpression=Key('Email').eq(event['email']))
   
    Reminder_text = "  "
    
    for i in response['Items']:
        Reminder_time = datetime.strptime(i['DateStr'], '%Y-%m-%d %H:%M')
        time_difference = Reminder_time - MM_time
        time_difference_in_minutes = time_difference.total_seconds() / 60
        print(i['Reminder'])
        print(time_difference_in_minutes)
        
        if time_difference_in_minutes < 60:
            if len(Reminder_text)<3:
                Reminder_text = "Reminders:"
                
            response = table.update_item(
                Key={
                        'Email': event['email'],
                        'Reminder': i['Reminder']
                    },
                    UpdateExpression="set Display = :y",
                    ExpressionAttributeValues={
                        ':y': 'yes'
                }
            )
            
            Reminder_text = Reminder_text + " " + i['Reminder'] + " at " + Reminder_time.strftime('%I:%M %p') + ";"
            
    Reminder_text = Reminder_text[:-1]
    
    payload = json.dumps({'intent':'remindersprint','reminders':Reminder_text})
    sns_message = json.dumps({'topic': event['email'] + '/display' ,'payload':payload})
    response = sns.publish(
        TopicArn=TopicArn,
        Message=sns_message)

         