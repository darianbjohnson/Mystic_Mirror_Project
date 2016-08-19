"""
Darian Johnson
http://darianbjohnson.com

This is the main function for the mystic mirror skill. 
This skill takes the users intent and, in addition to replying, sends a message, via SNS, to a second lamba function.
The second lambda function sends details, via mgtt, to the physical device (raspberry pi)
"""

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

#user defined variables
TopicARN = '<Change this to the topic ARN for SNS topic>'
bucket = "<Change this to your bucket name>" 

def lambda_handler(event, context):
    """ Route the incoming request based on type (LaunchRequest, IntentRequest,
    etc.) The JSON body of the request is provided in the event parameter.
    """
    print("event.session.application.applicationId=" +
           event['session']['application']['applicationId'])

    """
    Uncomment this if statement and populate with your skill's application ID to
    prevent someone else from configuring a skill that sends requests to this
    function.
    """
    if (event['session']['application']['applicationId'] !=
             "<Enter Your App ID>"):
         return wrong_AppID()
         

    if event['session']['new']:
        on_session_started({'requestId': event['request']['requestId']},
                           event['session'])

    #initialize session attributes
    session_attributes = {}
    
    if 'attributes' in event['session']:
        data = event['session']['attributes']
        for key, value in data.items():
            session_attributes.update({key :value})
    
    #this checks to see if the user has lined their Google account   
    if 'accessToken' in event['session']['user']:
        session_attributes = get_profile(event['session']['user']['accessToken'], session_attributes)
    else:
        session_attributes.update({'user_linked' :False})
        session_attributes.update({'saved_location' :False})
        session_attributes.update({'IOTEnabled' :False})
            
    
    #routes based on the request
    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'], event['session'], session_attributes)
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'],session_attributes)
    elif event['request']['type'] == "SessionEndedRequest":
        return on_session_ended(event['request'], event['session'])
        

def on_session_started(session_started_request, session):
    """ Called when the session starts """
        
    print("on_session_started requestId=" + session_started_request['requestId']
          + ", sessionId=" + session['sessionId'])


def on_launch(launch_request, session, session_attributes):
    """ Called when the user launches the skill without specifying what they
    want
    """

    print("on_launch requestId=" + launch_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # Dispatch to your skill's launch
    return get_welcome_response(session_attributes)

#routes based on the intent
def on_intent(intent_request, session, session_attributes):
    """ Called when the user specifies an intent for this skill """

    print("on_intent requestId=" + intent_request['requestId'] +
          ", sessionId=" + session['sessionId'])


    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']
    quotes_list = ["snowwhite", "rightsaidfred", "zoolander"]
    
    #this logic will force the user to cancel or stop if in a multi-turn request
    if intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent" or intent_name == "CustomCancel" or intent_name=="SessionEndedRequest":
        return handle_session_end_request()
        
    #this logic will route the user to the correct intent if this is a multi-turn request
    if session.get('attributes', {}) and "active_intent_name" in session.get('attributes', {}):
        intent_name = session['attributes']['active_intent_name']

    # Dispatch to your skill's intent handlers
    #Weather
    if intent_name == "weather":
        return get_weather(intent, session, session_attributes)
        
    #Show Again    
    elif intent_name == "show":
        return show_again(intent, session, session_attributes)
    
    #Set Brush Teeth Timer
    elif intent_name == "teeth":
        return teeth_timer(intent, session, session_attributes)
    
    #Reminder logic
    elif intent_name == "remind_me":
        return remind_me(intent, session, session_attributes)
    elif intent_name == "remind_me_freq":
        return remind_me_freq(intent, session, session_attributes)
    elif intent_name == "remind_me_day":
        return remind_me_day(intent, session, session_attributes)
    elif intent_name == "remind_me_time":
        return remind_me_time(intent, session, session_attributes)
    elif intent_name == "clear_reminders":
        return clear_reminders(intent, session, session_attributes)
    elif intent_name == "delete_reminders":
        return delete_reminders(intent, session, session_attributes)           
    
    #Get a quote (inspire me)
    elif intent_name == "inspiration":
        return get_inspiration(intent, session, session_attributes)
        
    #Get the news   
    elif intent_name == "news":
        return get_news(intent, session, session_attributes)
        
    #Selfie logic
    elif intent_name == "takeselfie":
        return take_selfie(intent, session, session_attributes)
    elif intent_name == "sendselfie_contact":
        return send_selfie_contact(intent, session, session_attributes)      
    elif intent_name == "sendselfie_publish":
        return send_selfie_publish(intent, session, session_attributes)           
    
    #Add contact and send message logic
    elif intent_name == "addcontactname":
        return add_contact_name(intent, session, session_attributes)
    elif intent_name == "addcontactnumber":
        return add_contact_number(intent, session, session_attributes)
    elif intent_name == "sms":
        return send_message(intent, session, session_attributes)
        
    #Get the Time
    elif intent_name == "gettime":
        return get_time(intent, session, session_attributes)
        
    #Save default location
    elif intent_name == "location" or intent_name == "from_weather":
        return save_location(intent, session, session_attributes)
        
    #Get easter egg quotes
    elif intent_name in quotes_list:
        return get_quote(intent, session, session_attributes)
        
    #Get Traffic
    elif intent_name == "traffic":
        return get_traffic(intent, session, session_attributes)
        
    #Get Help
    elif intent_name == "AMAZON.HelpIntent" or intent_name == "CustomHelp":
        return get_help_response(session_attributes)
    
    #Stop or Cancel
    elif intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent" or intent_name == "CustomCancel" or intent_name=="SessionEndedRequest":
        return handle_session_end_request()
        
    #Misunderstood request
    else:
        return misunderstood()


def on_session_ended(session_ended_request, session):
    """ Called when the user ends the session.
    Is not called when the skill returns should_end_session=true
    """
    print("on_session_ended requestId=" + session_ended_request['requestId'] +
          ", sessionId=" + session['sessionId'])



# --------------- Functions that control the skill's behavior ------------------

#This is called if the app is started without a specific intent
def get_welcome_response(session_attributes):

    card_title = "Welcome"
    speech_output = "Welcome to the Mystic Mirror skill. This skill will provide information or take actions to help you prepare for your day. " \
                    "You can ask me,'how do I look, or 'what is the weather'. For more help, say 'help'."
    card_output = "Welcome to the Mystic Mirror skill. This skill will provide information or take actions to help you prepare for your day. " \
                    "You can ask me: \n How do I look?\n What is the weather?\n Tell John to get ready for school.\n What is traffic like?\n\n For more help, say 'help'."
    card_type = 'Simple'
    topic = "display"
    message = "Welcome to the Mystic Mirror skill. This skill will provide information or take actions to assist you as you start your day. " \
                    "You can ask me: <li>How do I look?</li><li>What is the weather?</li><li>Tell John to get ready for school.</li><li>What is traffic like?</li>"
    payload = json.dumps({'intent':'welcome','message':message})
    reprompt_text = "For more help, say 'help'."
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response2(
        card_title, speech_output, reprompt_text, should_end_session,card_output, card_type, topic,payload,session_attributes ))
       
#Help      
def get_help_response(session_attributes):

    card_title = "Help"
    speech_output = "This skill will provide information or take actions to help you prepare for your day. " \
                    "You can ask me a number of things, such as 'how do I look', 'what is the weather', 'what is traffic like', or 'what time is it'. Check your Alexa app for a full list of questions that you can ask. " \
					"You should link your Google account so that I can save your default location. This will help me to provide traffic and weather for you. "\
					"You can also send a message to someone after saving their contact information. You can do that by telling me to save the name as a contact. " \
					"For example, you could say save John as a contact."
    card_output = "This skill will provide information or take actions to help you prepare for your day. " \
                    "You can ask me a number of things, such as: " \
                    "\n-how do I look" \
                    "\n-what is the weather" \
                    "\n-what is traffic like" \
                    "\n-what time is it" \
                    "\n-inspire me" \
                    "\n-how do I look" \
                    "\n-am I too sexy for this shirt" \
                    "\n-who is the fairest of them all" \
                    "\n\nYou should link your Google account so that I can save your default location. This will help me to provide traffic and weather for you. "\
                    "\n\nYou can also send a message to someone after saving their contact information. You can do that by telling me to save the name as a contact. " \
                    "For example, you could say save John as a contact."
    card_type = 'Simple'
    topic = "display"
    message = "This skill will provide information or take actions to help you prepare for your day. " \
                    "You can ask me a number of things, such as 'how do I look', 'what is the weather', 'what is traffic like', or 'what time is it'. " \
					"<p>You should link your Google account so that I can save your default location. This will help me to provide traffic and weather for you."\
					"<p>You can also send a message to someone after saving their contact information. You can do that by telling me to save the name as a contact. " \
					"For example, you could say save John as a contact."
    payload = json.dumps({'intent':'help','message':message})
    reprompt_text = "Ask me 'what is the weather' or 'what is the time'."
    should_end_session = True
    return build_response(session_attributes, build_speechlet_response2(
        card_title, speech_output, reprompt_text, should_end_session,card_output, card_type, topic,payload,session_attributes ))

#This is called if the skill is not linked to a Google account. 
def on_NoLink():
    """ If we wanted to initialize the session to have some attributes we could
    add those here
    """
    session_attributes = {}
    card_title = "Link Account"
    speech_output = "You must have a linked Google account to use this skill. You can do this from the Home section of the Alexa app."
    reprompt_text = "Use the Alexa app to link your Google Account with this skill."
    should_end_session = True
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))
        
#This is called if the has the incorrect application id.         
def wrong_AppID():
    """ If we wanted to initialize the session to have some attributes we could
    add those here
    """
    session_attributes = {}
    card_title = "Unauthorized Access"
    speech_output = "You are attempting to use this application from an unauthorized endpoint."
    reprompt_text = "You are attempting to use this application from an unauthorized endpoint."
    should_end_session = True
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))
        
#Returns a funny quote from a movie or song          
def get_quote(intent, session, session_attributes):
    
    reprompt_text = ""
    speech_output = ""
    
    first_name = ", "
    if 'first_name' in session_attributes:
        first_name = session_attributes['first_name'] + first_name

    card_title = "Mystic Mirror on the wall..."
    card_type = 'Simple'
    topic = "display"
    should_end_session = True
    
    if intent['name'] == "rightsaidfred":
        speech_output = "Yes " + first_name + "you are too sexy for that shirt."
        card_output = speech_output
        message = speech_output
        reprompt_text = speech_output
    
    if intent['name'] == "snowwhite":
        speech_output = "You are, my dear."
        card_output = speech_output
        message = speech_output
        reprompt_text = speech_output
        
    if intent['name'] == "zoolander":
        speech_output = "You look great " + first_name + "but remember, I'm pretty sure there's a lot more to life than being really, really, ridiculously good looking."
        card_output = speech_output
        message = speech_output
        reprompt_text = speech_output
    
    payload = json.dumps({'intent':'quote','message':message})
    return build_response(session_attributes, build_speechlet_response2(
        card_title, speech_output, reprompt_text, should_end_session,card_output, card_type, topic,payload,session_attributes ))


#Returns the time based on the users location            
def get_time(intent, session, session_attributes):
    #first we save in our attributes the intent
    session_attributes.update({'active_intent_name' : "time"})
    
    card_title = "What time is it"
    should_end_session = True
    
    speech_output = ""
    card_output = ""
    card_type = 'Simple'
    topic = "display"
    message = ""
    payload = ""
    reprompt_text = ""
    
    
    #check to see if default location is saved
    default_saved = False
    if "city" in session_attributes:
        default_saved = True
    if "state" in session_attributes:
        default_saved = True    

    if default_saved == False:
        speech_output = "You need to set a default location before I can give you the time. You can set your default location by saying 'Set Default Location' to the preferred city and state."
        card_output = "You need to set a default location before I can give you the time. You can set your default location by saying 'Set Default Location' to the preferred city and state."
        reprompt_text = "You need to set a default location before I can give you the time. You can set your default location by saying 'Set Default Location' to the preferred city and state."
        should_end_session = True
    
    else:
        #next we get the lat and long for the provided location
        loc_results = get_location(session, intent, session_attributes)
        parsed_loc_results = json.loads(loc_results)
        
        #set variables
        lat = parsed_loc_results['lat']
        lng = parsed_loc_results['lng']
        loc_status = parsed_loc_results['loc_status']
        session_attributes = parsed_loc_results['session_attributes']
        
        #initialize variables
        speech_output = ""
        reprompt_text = ""
        should_end_session = True
        
        #then we get the time for the lat and long
                
        if loc_status == 0: #one record was found, we can proceed
            
            current_time = get_current_time(lat,lng)
            
            if current_time != 'unknown':
                current_time_obj = datetime.strptime(current_time, '%Y-%m-%d %H:%M')
                print(str(current_time_obj))
                
                current_time_hour = current_time_obj.strftime('%I')
                if current_time_hour[:1] == "0":
                    current_time_hour = current_time_hour.replace("0", "")
                

                current_time_day = current_time_obj.strftime('%A')
                current_time_date = current_time_obj.strftime('%B %-d, %Y')
                
                current_time_minute = current_time_obj.strftime('%M')
                
                current_time_ampm_write = current_time_obj.strftime('%p')
                current_time_ampm = current_time_ampm_write.replace("M", ".M.")              
                
                
                current_time = current_time_hour +":" +current_time_minute + " " + current_time_ampm
                current_time_card = current_time_hour +":" +current_time_minute + " " + current_time_ampm_write
                speech_output = "The current time is " +  current_time
                card_output = "The current time is " +  current_time_card
                reprompt_text = "The current time is " +  current_time
                payload = json.dumps({'intent':'time','message': 'success', 'cur_day': current_time_day, 'cur_date': current_time_date, 'cur_time': current_time_card})
                should_end_session = True
                
            else: #other errors
    
                speech_output = "I was unable to ascertain the current time. There might be a problem with the system. Please try again in a few minutes."
                reprompt_text = "I was unable to ascertain the current time. There might be a problem with the system. Please try again in a few minutes."
                card_output = "I was unable to ascertain the current time. There might be a problem with the system. Please try again in a few minutes."
                payload = json.dumps({'intent':'time','message':'error'})
                should_end_session = True
                    
        else:
            speech_output = "I was unable to ascertain the current time. There might be a problem with the system. Please try again in a few minutes."
            reprompt_text = "I was unable to ascertain the current time. There might be a problem with the system. Please try again in a few minutes."
            card_output = "I was unable to ascertain the current time. There might be a problem with the system. Please try again in a few minutes."
            payload = json.dumps({'intent':'time','message':card_output})
            should_end_session = True
    
    #build the response and return to handler
        
    return build_response(session_attributes, build_speechlet_response2(
        card_title, speech_output, reprompt_text, should_end_session,card_output, card_type, topic,payload,session_attributes )) 

#Returns the weather based on the users location.          
def get_weather(intent, session, session_attributes):
    """ If we wanted to initialize the session to have some attributes we could
    add those here
    """
    card_title = "What is the weather"
    should_end_session = True
    
    speech_output = ""
    card_output = ""
    card_type = 'Simple'
    topic = "display"
    message = ""
    payload = ""
    reprompt_text = ""
    message_details = {}
    
    #first we save in our attributes the intent
    session_attributes.update({'active_intent_name' : "weather"})
    
    #next we get the lat and long for the provided location
    loc_results = get_location(session, intent, session_attributes)
    parsed_loc_results = json.loads(loc_results)
    
    #set variables
    city = parsed_loc_results['city']
    state = parsed_loc_results['state']
    lat = parsed_loc_results['lat']
    lng = parsed_loc_results['lng']
    loc_status = parsed_loc_results['loc_status']
    session_attributes = parsed_loc_results['session_attributes']
    
    message_details.update({'city': city})
    message_details.update({'state': state})
    
    if session.get('attributes', {}) and "second_time_in_location" in session.get('attributes', {}):
        if session['attributes']['second_time_in_location'] == True and loc_status == 2: 
            loc_status = 3
            
    #then we get the forecast for the lat and long
            
    if loc_status == 4:     #there was an error looking for the weather forecast
        speech_output = "I could not find the weather for the location. There might be a problem with the system. Please try again in a few minutes."
        reprompt_text = "I could not find the weather for the location. There might be a problem with the system. Please try again in a few minutes."
        card_output = "I could not find the weather for the location. There might be a problem with the system. Please try again in a few minutes."
        payload = json.dumps({'intent':'weather','message':'error','message_details':card_output})
        should_end_session = True
        
    elif loc_status == 3:   #the location could not be found
    
        if 'state' in session_attributes:
            session_attributes.pop('state')
        if 'city' in session_attributes:
            session_attributes.pop('city')
    
        speech_output = "Either you did not provide a valid location, or I could not find the provided location. Please specify the city."
        reprompt_text = "Either you did not provide a valid location, or I could not find the provided location. Please specify the city."
        card_output = "Either you did not provide a valid location, or I could not find the provided location. Please specify the city."
        payload = json.dumps({'intent':'weather','message':'error','message_details':card_output})
        
        session_attributes.update({'second_time_in_location' : False})
        should_end_session = False
        
    elif loc_status == 2:   #we found more than 1 record, we need to get more specific
        speech_output = "I found more than one record for " + city + ". Please tell me the state."
        reprompt_text = "I found more than one record for " + city + ". Please tell me the state."
        card_output = "I found more than one record for " + city + ". Please tell me the state."
        payload = json.dumps({'intent':'weather','message':'error','message_details':card_output})
        
        #this tells is that we have been in this loop before
        session_attributes.update({'second_time_in_location' : True})
        session_attributes.update({'city' : city})
        
        should_end_session = False
         
    elif loc_status == 1:  #there was an error looking for the location      
        speech_output = "I could not find the location. There might be a problem with the system. Please try again in a few minutes."
        reprompt_text = "I could not find the location. There might be a problem with the system. Please try again in a few minutes."
        card_output = "I could not find the location. There might be a problem with the system. Please try again in a few minutes."
        payload = json.dumps({'intent':'weather','message':'error','message_details':card_output})
        should_end_session = True
        
    elif loc_status == 0: #one record was found, we can proceed
        
        #URL = "http://api.openweathermap.org/data/2.5/forecast?lat=" + str(lat) + "&lon=" + str(lng) + "&appid=fdef51d5593d23d9180b5aeb68ff5e88"
        URL = "http://api.apixu.com/v1/forecast.json?key=3b007aab55254d93992182416162806&days=5&q=" + str(lat) + "," + str(lng)
        req = urllib2.Request(URL)
                
        print(URL)
        #Add the headers
        req.add_header('Content-Type', 'application/x-www-form-urlencoded')
                
        #Fire off the request
        try:
            response = urllib2.urlopen(req, timeout=3)
            FullResponse = response.read()
            parsed_response = json.loads(FullResponse)

            localtime = parsed_response['location']['localtime']
            current_time_obj = datetime.strptime(localtime, '%Y-%m-%d %H:%M')
            
            current_time_hour = current_time_obj.strftime('%I')
            if current_time_hour[:1] == "0":
                current_time_hour = current_time_hour.replace("0", "")
                    
            current_time_minute = current_time_obj.strftime('%M')
            current_time_ampm = current_time_obj.strftime('%p')
            #current_time_ampm = current_time_ampm.replace("M", ".M.")
            current_time = current_time_hour +":" +current_time_minute + " " + current_time_ampm

            message_details.update({'time': current_time})
            
            temp = int(parsed_response['current']['temp_f'])
            temp_str =  str(temp)
            description = parsed_response['current']['condition']['text']
            icon = parsed_response['current']['condition']['icon']
            feels_like = str(int(parsed_response['current']['feelslike_f']))
            
             
            message_details.update({'temp': temp_str})
            message_details.update({'description': description})
            message_details.update({'icon': icon})
            message_details.update({'feels_like': feels_like})
            
            
            forecast_hi = str(int(parsed_response['forecast']['forecastday'][0]['day']['maxtemp_f']))
            forecast_low = str(int(parsed_response['forecast']['forecastday'][0]['day']['mintemp_f']))
            forecast_decs = parsed_response['forecast']['forecastday'][0]['day']['condition']['text']
            forecast_icon = parsed_response['forecast']['forecastday'][0]['day']['condition']['icon']
            forecast_day = current_time_obj.strftime('%A')
            
            forecast_hi1 = str(int(parsed_response['forecast']['forecastday'][1]['day']['maxtemp_f']))
            forecast_low1 = str(int(parsed_response['forecast']['forecastday'][1]['day']['mintemp_f']))
            forecast_decs1 = parsed_response['forecast']['forecastday'][1]['day']['condition']['text']
            forecast_icon1 = parsed_response['forecast']['forecastday'][1]['day']['condition']['icon']
            current_time1 = datetime.strptime(parsed_response['forecast']['forecastday'][1]['date'], '%Y-%m-%d')            
            forecast_day1 = current_time1.strftime('%a')
            
            forecast_hi2 = str(int(parsed_response['forecast']['forecastday'][2]['day']['maxtemp_f']))
            forecast_low2 = str(int(parsed_response['forecast']['forecastday'][2]['day']['mintemp_f']))
            forecast_decs2 = parsed_response['forecast']['forecastday'][2]['day']['condition']['text']
            forecast_icon2 = parsed_response['forecast']['forecastday'][2]['day']['condition']['icon']
            current_time2 = datetime.strptime(parsed_response['forecast']['forecastday'][2]['date'], '%Y-%m-%d')            
            forecast_day2 = current_time2.strftime('%a')
            
            forecast_hi3 = str(int(parsed_response['forecast']['forecastday'][3]['day']['maxtemp_f']))
            forecast_low3 = str(int(parsed_response['forecast']['forecastday'][3]['day']['mintemp_f']))
            forecast_decs3 = parsed_response['forecast']['forecastday'][3]['day']['condition']['text']
            forecast_icon3 = parsed_response['forecast']['forecastday'][3]['day']['condition']['icon']
            current_time3 = datetime.strptime(parsed_response['forecast']['forecastday'][3]['date'], '%Y-%m-%d')            
            forecast_day3 = current_time3.strftime('%a')
            
            forecast_hi4 = str(int(parsed_response['forecast']['forecastday'][4]['day']['maxtemp_f']))
            forecast_low4 = str(int(parsed_response['forecast']['forecastday'][4]['day']['mintemp_f']))
            forecast_decs4 = parsed_response['forecast']['forecastday'][4]['day']['condition']['text']
            forecast_icon4 = parsed_response['forecast']['forecastday'][4]['day']['condition']['icon']
            current_time4 = datetime.strptime(parsed_response['forecast']['forecastday'][4]['date'], '%Y-%m-%d')            
            forecast_day4 = current_time4.strftime('%a')
            
            
            message_details.update({'intent': 'weather'})
            message_details.update({'message': 'success'})
            message_details.update({'forecast_hi': forecast_hi})
            message_details.update({'forecast_low': forecast_low})
            message_details.update({'forecast_decs': forecast_decs})
            message_details.update({'forecast_icon': forecast_icon})
            message_details.update({'forecast_day': forecast_day})
            
            message_details.update({'forecast_hi1': forecast_hi1})
            message_details.update({'forecast_low1': forecast_low1})
            message_details.update({'forecast_decs1': forecast_decs1})
            message_details.update({'forecast_icon1': forecast_icon1})
            message_details.update({'forecast_day1': forecast_day1})
            
            message_details.update({'forecast_hi2': forecast_hi2})
            message_details.update({'forecast_low2': forecast_low2})
            message_details.update({'forecast_decs2': forecast_decs2})
            message_details.update({'forecast_icon2': forecast_icon2})
            message_details.update({'forecast_day2': forecast_day2})
            
            message_details.update({'forecast_hi3': forecast_hi3})
            message_details.update({'forecast_low3': forecast_low3})
            message_details.update({'forecast_decs3': forecast_decs3})
            message_details.update({'forecast_icon3': forecast_icon3})
            message_details.update({'forecast_day3': forecast_day3})
            
            message_details.update({'forecast_hi4': forecast_hi4})
            message_details.update({'forecast_low4': forecast_low4})
            message_details.update({'forecast_decs4': forecast_decs4})
            message_details.update({'forecast_icon4': forecast_icon4})
            message_details.update({'forecast_day4': forecast_day4})
            
            message_details.update({'save': ""})
            
            #finally, we get the local time based on the lat and long
                                
            speech_output = "The current temperature is " + temp_str + " degrees Fahrenheit. Today's forecast is " + forecast_decs + " with a high of " + forecast_hi + " and a low of " + forecast_low + "."
            reprompt_text = "The current temperature is " + temp_str + " degrees Fahrenheit. Today's forecast is " + forecast_decs + " with a high of " + forecast_hi + " and a low of " + forecast_low + "."
            card_output = "The current temperature is " + temp_str + " degrees Fahrenheit. Today's forecast is " + forecast_decs +" with a high of " + forecast_hi + " and a low of " + forecast_low + "."
            payload = json.dumps(message_details)
            should_end_session = True
            
            if session_attributes['user_linked'] == True and session_attributes['saved_location'] == False:
                speech_output = speech_output + " I noticed that you don't have a default location saved. Would you like to use this as your default?"
                reprompt_text = reprompt_text + " I noticed that you don't have a default location saved. Would you like to use this as your default?"
                card_output = reprompt_text
                message_details.update({'save': "I noticed that you don't have a default location saved. Would you like to use this as your default?"})
                payload = json.dumps(message_details)
                should_end_session = False
                
                session_attributes.update({'active_intent_name' : "from_weather"})
                
            
        except urllib2.URLError as e:
            speech_output = "I could not find the weather for the location. There might be a problem with the system. Please try again in a few minutes."
            reprompt_text = "I could not find the weather for the location. There might be a problem with the system. Please try again in a few minutes."
            card_output = "I could not find the weather for the location. There might be a problem with the system. Please try again in a few minutes."
            payload = json.dumps({'intent':'weather','message':'error','message_details':card_output})
            should_end_session = True
            
        except socket.timeout as e:
            speech_output = "I could not find the weather for the location. There might be a problem with the system. Please try again in a few minutes."
            reprompt_text = "I could not find the weather for the location. There might be a problem with the system. Please try again in a few minutes."
            card_output = "I could not find the weather for the location. There might be a problem with the system. Please try again in a few minutes."
            payload = json.dumps({'intent':'weather','message':'error','message_details':card_output})
            should_end_session = True
    
    
    return build_response(session_attributes, build_speechlet_response2(
        card_title, speech_output, reprompt_text, should_end_session,card_output, card_type, topic,payload,session_attributes ))       

#Saves the users default location 
def save_location(intent, session, session_attributes):

    #add this to route the state_propt correctly to this intent
    session_attributes.update({'active_intent_name' : "location"})
    
    if session_attributes['user_linked'] == False:
        card_title = "Link Account"
        speech_output = "You must have a linked Google account to use this skill. You can do this from the Home section of the Alexa app."
        reprompt_text = "Use the Alexa app to link your Google Account with this skill."
        should_end_session = True
    
        return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))  
    
    #delete any old values in the table
    table = 'Magic_Mirror'
    response = dynamodb.delete_item(TableName = table,
            Key={
                 'Email' : {
                  "S" :session_attributes['email']
            }})  
    
    #start DynamoDB update statement
    details = {}
    email = session_attributes['email']
    email_str = {'S' : email}
    details.update({"Email": email_str})
    
    card_title = "Save Location"
    should_end_session = True
    
    speech_output = ""
    card_output = ""
    card_type = 'Simple'
    topic = "display"
    message = ""
    payload = ""
    reprompt_text = ""
    message_details = {}
    
    
    #if the response is negative, exit
    if 'slots' in intent:
        if 'YesNo' in intent['slots']:
            if 'value' in intent['slots']['YesNo'] and "yes" not in intent['slots']['YesNo']['value']:              
                
                speech_output = "Ok, the location was not saved."
                reprompt_text = "Ok, the location was not saved."
                card_output = "Ok, the location was not saved."
                payload = json.dumps({'intent':'location','message':card_output})
                
                should_end_session = True
        
                return build_response(session_attributes, build_speechlet_response2(
                    card_title, speech_output, reprompt_text, should_end_session,card_output, card_type, topic,payload,session_attributes )) 
            
            
            
    #validate if we need to check if the location is valid
    if session.get('attributes', {}) and "active_intent_name" in session.get('attributes', {}):
        if session['attributes']['active_intent_name'] == "from_weather": #we already checked the location in the weather intent and it is ok; get variables from session
        
            city = ""
            state = ""
            if session.get('attributes', {}) and "city" in session.get('attributes', {}):        
                if len(session['attributes']['city'])>0:
                    city_str = {'S' : session['attributes']['city']}
                    details.update({"City": city_str})
                    city = session['attributes']['city']
            if session.get('attributes', {}) and "state" in session.get('attributes', {}):  
                if len(session['attributes']['state'])>0:
                    state_str = {'S' : session['attributes']['state']}
                    details.update({"State": state_str})
                    state = session['attributes']['state']
                
            #Save to DynamoDB
            response = update_table('Magic_Mirror',details)
            
            speech_output = city + " " + state + " is now set as your default location. You no longer need to specify a location when asking about weather. You can change it at any time by saying 'Save my default location', such as 'Save my default location as Dallas, Texas'."
            reprompt_text = city + " " + state + " is now set as your default location. You no longer need to specify a location when asking about weather."
            card_output = city + " " + state + " is now set as your default location."
            payload = json.dumps({'intent':'location','message':card_output})
            
            should_end_session = True
            
            return build_response(session_attributes, build_speechlet_response2(
                card_title, speech_output, reprompt_text, should_end_session,card_output, card_type, topic,payload,session_attributes )) 
        
        #if session['attributes']['active_intent_name'] == "location": #we already have the city, we need the state
            #no action needed, handle at the end
        
    #else: #check if the location is ok
    
        #if 'city' in session_attributes:
            #session_attributes.pop('city')
            
        #if 'state' in session_attributes:
            #session_attributes.pop('state')

    loc_results = get_location(session, intent, session_attributes)
    parsed_loc_results = json.loads(loc_results)
            
    #set variables
    city = parsed_loc_results['city']
    state = parsed_loc_results['state']
    lat = parsed_loc_results['lat']
    lng = parsed_loc_results['lng']
    loc_status = parsed_loc_results['loc_status']
    session_attributes = parsed_loc_results['session_attributes']
        
        
    if session.get('attributes', {}) and "second_time_in_location" in session.get('attributes', {}):
        if session['attributes']['second_time_in_location'] == True and loc_status == 2: 
            loc_status = 3
        
    if loc_status == 4:     #there was an error looking for the weather forecast
           
        speech_output = "I could not save your default location. There might be a problem with the system. Please try again in a few minutes."
        reprompt_text = "I could not save your default location. There might be a problem with the system. Please try again in a few minutes."
        card_output = "I could not save your default location. There might be a problem with the system. Please try again in a few minutes."
        payload = json.dumps({'intent':'location','message':card_output})
            
        should_end_session = True
            
            
    elif loc_status == 3:   #the location could not be found
            
        if 'state' in session_attributes:
            session_attributes.pop('state')
        if 'city' in session_attributes:
            session_attributes.pop('city')
            
        speech_output = "Either you did not provide a valid location, or I could not find the provided location. Please tell me the city for your preferred default location."
        reprompt_text = "Tell me the city for your preferred default location."
        card_output = "Either you did not provide a valid location, or I could not find the provided location. Please tell me the city for your preferred default location."
        payload = json.dumps({'intent':'location','message':card_output})
        session_attributes.update({'second_time_in_location' : False})
            
        should_end_session = False
                
    elif loc_status == 2:   #we found more than 1 record, we need to get more specific
              
        speech_output = "I found more than one record for " + city + ". Please tell me the state that the city is located in."
        reprompt_text = "I found more than one record for " + city + ". Please tell me the state that the city is located in."
        card_output = "I found more than one record for " + city + ". Please tell me the state that the city is located in."
        payload = json.dumps({'intent':'location','message':card_output})
            
        #this tells is that we have been in this loop before
        session_attributes.update({'second_time_in_location' : True})
        session_attributes.update({'city' : city})
            
        should_end_session = False
                 
    elif loc_status == 1:  #there was an error looking for the location      
            
        speech_output = "I could not find the location. There might be a problem with the system. Please try again in a few minutes."
        reprompt_text = "I could not find the location. There might be a problem with the system. Please try again in a few minutes."
        card_output = "I could not find the location. There might be a problem with the system. Please try again in a few minutes."
        payload = json.dumps({'intent':'location','message':card_output})
            
        should_end_session = True
                
    elif loc_status == 0: #one record was found, we can proceed
        
        if len(city)>0:
            city_str = {'S' : city}
            details.update({"City": city_str})
                    
        if len(state)>0:
            state_str = {'S' : state}
            details.update({"State": state_str})

        #Save to DynamoDB
        response = update_table('Magic_Mirror',details)
                
        speech_output = city + " " + state + " is now set as your default location. You no longer need to specify a location when asking about weather. You can change it at any time by saying 'set my default location', such as 'set my default location as Dallas, Texas'."
        reprompt_text = city + " " + state + " is now set as your default location. You no longer need to specify a location when asking about weather."
        card_output = city + " " + state + " is now set as your default location."
        payload = json.dumps({'intent':'location','message':card_output})
    
    #build the response and return to handler
    
    return build_response(session_attributes, build_speechlet_response2(
        card_title, speech_output, reprompt_text, should_end_session,card_output, card_type, topic,payload,session_attributes )) 

#Returns the traffic based on the users location 
def get_traffic(intent, session, session_attributes):
    
    if session_attributes['user_linked'] == False:
        card_title = "Link Account"
        speech_output = "You must have a linked Google account to use this skill. You can do this from the Home section of the Alexa app."
        reprompt_text = "Use the Alexa app to link your Google Account with this skill."
        should_end_session = True
    
        return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))  
    
    
    card_title = "Get Traffic"
    should_end_session = True
    
    speech_output = ""
    card_output = ""
    card_type = 'Simple'
    topic = "display"
    message = ""
    payload = ""
    reprompt_text = ""
    message_details = {}

    default_saved = False
    if "city" in session_attributes:
        default_saved = True
    if "state" in session_attributes:
        default_saved = True    

    if default_saved == False: #no default location saved
       
        speech_output = "You need to set a default location before I can give you the traffic. You can set your default location by saying 'Set Default Location' to the preferred city and state."
        reprompt_text = "You need to set a default location before I can give you the traffic. You can set your default location by saying 'Set Default Location' to the preferred city and state."
        card_output = "You need to set a default location before I can give you the traffic. You can set your default location by saying 'Set Default Location' to the preferred city and state."
        payload = json.dumps({'intent':'traffic','message':'error','details': card_output})
        should_end_session = True
    
    else:
        #next we get the lat and long for the provided location
        loc_results = get_location(session, intent, session_attributes)
        parsed_loc_results = json.loads(loc_results)
        
        #set variables
        lat = parsed_loc_results['lat']
        lng  = parsed_loc_results['lng']
        lat_ne = parsed_loc_results['lat_ne']
        lng_ne = parsed_loc_results['lng_ne']
        lat_sw = parsed_loc_results['lat_sw']
        lng_sw = parsed_loc_results['lng_sw']
        loc_status = parsed_loc_results['loc_status']
        session_attributes = parsed_loc_results['session_attributes']
        
        if loc_status == 0: #one record was found, we can proceed
            
            coordinates = str(lat_ne) + "," + str(lng_ne) + "," + str(lat_sw) + "," + str(lng_sw)
            URL="http://www.mapquestapi.com/traffic/v2/incidents?key=eYAOfKUt6PeANY5gYUNWa7GWTFLobPGz&callback=handleIncidentsResponse&boundingBox=" + coordinates + "&filters=incidents&inFormat=kvp&outFormat=json"
            print(URL)
            req = urllib2.Request(URL)
            req.add_header('Content-Type', 'application/x-www-form-urlencoded')
                    
            #Fire off the request
            try:
                response = urllib2.urlopen(req, timeout=3)
                FullResponse = response.read()
                #print(FullResponse)
                FullResponse = FullResponse.replace('}});','}}')
                FullResponse = FullResponse.replace('handleIncidentsResponse(','')
                print(FullResponse)
                parsed_response = json.loads(FullResponse)
                
                
                incident_count = 0
                incident_count = len(parsed_response['incidents'])
                
                incident_str = str(incident_count)
                incident_details_card = ""
                incident_details_mm = ""
                additional_detail = ""
                true_count = 0
                
                if incident_count == 0:
                    incident_str = 'no';
                else:
                    i = 0
                    while (i < incident_count):
                        if parsed_response['incidents'][i]['impacting'] == True:
                            true_count = true_count + 1
                            incident_details_card = incident_details_card + '\n' + str(true_count) + '. ' + parsed_response['incidents'][i]['fullDesc']
                            incident_details_mm = incident_details_mm + '<li>' + parsed_response['incidents'][i]['fullDesc'] + '</li>'
                            additional_detail = "Check the card in the Alexa app for details on the accidents."
                        i = i + 1
                    
                
                map = "http://www.mapquestapi.com/traffic/v2/flow?key=eYAOfKUt6PeANY5gYUNWa7GWTFLobPGz&mapLat=" + str(lat) + "&mapLng=" + str(lng) + "&mapHeight=300&mapWidth=300&mapScale=108335&imageType=png"
                
                speech_output = "There are " + str(true_count) + " major incidents impacting traffic in your location. " + additional_detail
                reprompt_text = "There are " + str(true_count) + " major incidents impacting traffic in your location. " + additional_detail
                card_output = "There are " + str(true_count) + " major incidents impacting traffic in your location." + incident_details_card
                payload = json.dumps({'intent':'traffic','message':'success', 'details': "There are " + str(true_count) + " major incidents impacting traffic in your location. <ol type='1'>" + incident_details_mm + '</ol>', 'map': map})
                should_end_session = True
               
            except urllib2.URLError as e:
                
                speech_output = "I was unable to obtain traffic in your area. There might be a problem with the system. Please try again in a few minutes."
                reprompt_text = "I was unable to obtain traffic in your area. There might be a problem with the system. Please try again in a few minutes."
                card_output = "I was unable to obtain traffic in your area. There might be a problem with the system. Please try again in a few minutes."
                payload = json.dumps({'intent':'traffic','message':'error','details': card_output})
                should_end_session = True
                
            except socket.timeout as e:
            
                speech_output = "I was unable to obtain traffic in your area. There might be a problem with the system. Please try again in a few minutes."
                reprompt_text = "I was unable to obtain traffic in your area. There might be a problem with the system. Please try again in a few minutes."
                card_output = "I was unable to obtain traffic in your area. There might be a problem with the system. Please try again in a few minutes."
                payload = json.dumps({'intent':'traffic','message':'error','details': card_output})
                should_end_session = True
                    
        else:
                speech_output = "I was unable to obtain traffic in your area. There might be a problem with the system. Please try again in a few minutes."
                reprompt_text = "I was unable to obtain traffic in your area. There might be a problem with the system. Please try again in a few minutes."
                card_output = "I was unable to obtain traffic in your area. There might be a problem with the system. Please try again in a few minutes."
                payload = json.dumps({'intent':'traffic','message':'error','details': card_output})
                should_end_session = True
    
    #build the response and return to handler
    
    return build_response(session_attributes, build_speechlet_response2(
        card_title, speech_output, reprompt_text, should_end_session,card_output, card_type, topic,payload,session_attributes )) 
        

#Returns the news headlines and a snippet         
def get_news(intent, session, session_attributes):

    card_title = "Get News Headlines"
    should_end_session = True
    
    speech_output = ""
    card_output = ""
    card_type = 'Simple'
    topic = "display"
    message = ""
    payload = ""
    reprompt_text = ""
    
    URL="https://api.cognitive.microsoft.com/bing/v5.0/news/"
    req = urllib2.Request(URL)
    req.add_header('Content-Type', 'application/x-www-form-urlencoded')
    req.add_header('Ocp-Apim-Subscription-Key', '5d66630076364f68b3f2c79df531b1e8')
                    
    #Fire off the request
    try:
        response = urllib2.urlopen(req, timeout=3)
        FullResponse = response.read()
        print(FullResponse)
        parsed_response = json.loads(FullResponse)
        print(parsed_response)    

        news_count = len(parsed_response['value'])      
        print(parsed_response['value'][0]['name'])  
        

        news_details_card = ""  
        news_details_mm = FullResponse        
        if news_count == 0:
            news_details_card = "There are no stories to report"
            speech_output = "There are no stories to report"
        else:
            news_details_card = "Here are today's major headlines: "
            speech_output = "Here is one of today's major headlines: " + parsed_response['value'][0]['name'] + "."
            i = 0
            while (i < 5):
                news_details_card = news_details_card + '\n' + parsed_response['value'][i]['name']
                #news_details_mm = incident_details_mm + '<li>' + parsed_response['value'][i]['name'] + '<br>' + parsed_response['value'][i]['name']  + '</li>'
                i = i + 1        
                     
        reprompt_text = "Check the Alexa App to read the major headlines for today."
        card_output = news_details_card
        payload = json.dumps({'intent':'news','message':'success','news_stories':news_details_mm})
        should_end_session = True
               
    except urllib2.URLError as e:
                
        speech_output = "There was a problem retrieving today's headlines. Please try again in a few minutes."
        reprompt_text = "There was a problem retrieving today's headlines. Please try again in a few minutes."
        card_output = "There was a problem retrieving today's headlines. Please try again in a few minutes."
        payload = json.dumps({'intent':'news','message':'error'})
        should_end_session = True
        
    except socket.timeout as e:
        speech_output = "There was a problem retrieving today's headlines. Please try again in a few minutes."
        reprompt_text = "There was a problem retrieving today's headlines. Please try again in a few minutes."
        card_output = "There was a problem retrieving today's headlines. Please try again in a few minutes."
        payload = json.dumps({'intent':'news','message':'error'})
        should_end_session = True
    
    return build_response(session_attributes, build_speechlet_response2(
        card_title, speech_output, reprompt_text, should_end_session,card_output, card_type, topic,payload,session_attributes )) 


#Adds a contact name to the users contact list
def add_contact_name(intent, session, session_attributes):
    """ If we wanted to initialize the session to have some attributes we could
    add those here
    """
    
    if session_attributes['user_linked'] == False:
        card_title = "Link Account"
        speech_output = "You must have a linked Google account to use this skill. You can do this from the Home section of the Alexa app."
        reprompt_text = "Use the Alexa app to link your Google Account with this skill."
        should_end_session = True
    
        return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))  
    
    name_to_ping = ""
    if 'slots' in intent:
        if 'Name' in intent['slots']:
            if 'value' in intent['slots']['Name']:  
                name_to_ping = intent['slots']['Name']['value']
                session_attributes.update({'name_to_ping':name_to_ping})
    
    if len(name_to_ping) > 0 :
        speech_output = "Thank you. Now tell me the contact number."
        reprompt_text = "Thank you. Now tell me the contact number."
        session_attributes.update({'active_intent_name':'addcontactnumber'})
        should_end_session = False
    
    else:
        speech_output = "I did not understand the name. Please start over by saying 'add name as contact'."
        reprompt_text = "I did not understand the name. Please start over by saying 'add name as contact'."
        should_end_session = True
    
    card_title = "Save Contact Name"
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))
        
#Adds a contact number to a contact name
def add_contact_number(intent, session, session_attributes):
    """ If we wanted to initialize the session to have some attributes we could
    add those here
    """
    if session_attributes['user_linked'] == False:
        card_title = "Link Account"
        speech_output = "You must have a linked Google account to use this skill. You can do this from the Home section of the Alexa app."
        reprompt_text = "Use the Alexa app to link your Google Account with this skill."
        should_end_session = True
    
        return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session)) 
        
    number_to_ping = ""
    if session.get('attributes', {}) and "active_intent_name" in session.get('attributes', {}):
        if session['attributes']['active_intent_name'] == "addcontactnumber": #this was routed from the add_name intent, so it is ok to procees
        
            if 'InputNumber' in intent['slots']:
                number_to_ping = intent['slots']['InputNumber']['value']
                session_attributes.update({'number_to_ping':number_to_ping})
    
            if len(number_to_ping) == 10:
                
                #create SNS topic
                response = sns.create_topic(
                        Name=number_to_ping + "Magic_Mirror"
                )
                
                topic_arn = response['TopicArn']
                
                response = sns.subscribe(
                    TopicArn=topic_arn,
                    Protocol='sms',
                    Endpoint='1'+ number_to_ping
                )
                
                details = {}
                email = session_attributes['email']
                email_str = {'S' : email}
                details.update({"Email": email_str})
                
                number_str = {'S' : number_to_ping}
                details.update({"ContactNumber": number_str})
                
                arn_str = {'S' : topic_arn}
                details.update({"TopicArn": arn_str})
                
                if session.get('attributes', {}) and "name_to_ping" in session.get('attributes', {}):        
                    if len(session['attributes']['name_to_ping'])>0:
                        name_str = {'S' : session['attributes']['name_to_ping']}
                        details.update({"ContactName": name_str})
                
                response = update_table('Magic_Mirror_Contact',details)
                 
                speech_output = "Thank you. You can now send messages to " + session['attributes']['name_to_ping'] +". For example, you can ask me to tell " + session['attributes']['name_to_ping'] + ", good morning."
                reprompt_text = speech_output
                should_end_session = True
        
            else:
                speech_output = "The number must be ten digits. Please tell me the phone number again, making sure it is only ten digits."
                reprompt_text = speech_output
                should_end_session = False
                session_attributes.update({'active_intent_name':'addcontactnumber'})
                
        else:
            session_attributes = {}
            card_title = "I Do Not Understand" 
            speech_output = "I did not understand your request. Can you try again, or rephrase."
            # If the user either does not reply to the welcome message or says something
            # that is not understood, they will be prompted again with this text.
            reprompt_text = "I did not understand your request. Can you try again, or rephrase."
            should_end_session = True
            return build_response(session_attributes, build_speechlet_response(
                card_title, speech_output, reprompt_text, should_end_session))

    else:
        session_attributes = {}
        card_title = "I Do Not Understand" 
        speech_output = "I did not understand your request. Can you try again, or rephrase."
        # If the user either does not reply to the welcome message or says something
        # that is not understood, they will be prompted again with this text.
        reprompt_text = "I did not understand your request. Can you try again, or rephrase."
        should_end_session = True
        return build_response(session_attributes, build_speechlet_response(
            card_title, speech_output, reprompt_text, should_end_session))
    
    card_title = "Save Contact Number"
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))
 
#Sends a mesage to a named contact
def send_message(intent, session, session_attributes):
    """ If we wanted to initialize the session to have some attributes we could
    add those here
    """
    
    if session_attributes['user_linked'] == False:
        card_title = "Link Account"
        speech_output = "You must have a linked Google account to use this skill. You can do this from the Home section of the Alexa app."
        reprompt_text = "Use the Alexa app to link your Google Account with this skill."
        should_end_session = True
    
        return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session)) 
    
    card_title = "Send Message"
    should_end_session = True
    
    speech_output = ""
    card_output = ""
    card_type = 'Simple'
    topic = "display"
    message = ""
    payload = ""
    reprompt_text = ""
    name_to_ping = ""
    message_to_ping = ""

    if 'Name' in intent['slots']:
        if 'value' in intent['slots']['Name']:
            name_to_ping = intent['slots']['Name']['value']

    if 'Message' in intent['slots']:
        if 'value' in intent['slots']['Message']: 
            message_to_ping = intent['slots']['Message']['value']

    if len(name_to_ping) > 0 and len(message_to_ping) > 0 :
        table = 'Magic_Mirror_Contact'
        response = dynamodb.get_item(TableName = table,
            Key={
                 'Email' : {
                  "S" : session_attributes['email']
                },
                'ContactName' : {
                  "S" : name_to_ping
                }

            })
            
                    
        if 'Item' in response:
            
            if 'TopicArn' in response['Item']:

                sns_message = session_attributes['first_name'] + " says '" + message_to_ping  + "'."
                response = sns.publish(
                    TopicArn= response['Item']['TopicArn']['S'],
                    Message=sns_message)
                
                speech_output = "The message was sent to " + name_to_ping + "."
                reprompt_text = "The message was sent to " + name_to_ping + "."
                card_output = "The message was sent to " + name_to_ping + "."
                payload = json.dumps({'intent':'message','message':'success','name': name_to_ping, 'details': message_to_ping})
                should_end_session = True
            else:
                speech_output = "There was a problem trying to send a message to this contact. Can you please add or re-create the contact by saying 'add " + name_to_ping + " to contacts'?"
                reprompt_text = "There was a problem trying to send a message to this contact. Can you please add or re-create the contact by saying 'add " + name_to_ping + " to contacts'?"
                card_output = "There was a problem trying to send a message to this contact. Can you please add or re-create the contact by saying 'add " + name_to_ping + " to contacts'?"
                payload = json.dumps({'intent':'message','message':'error','details': card_output})
                should_end_session = False
                
        else: #did not find a name
            
            speech_output = "I did not find the name " + name_to_ping + " in your contact list. If I misheard you, please repeat yourself. Otherwise, please add the contact by saying add " + name_to_ping + " to contacts."
            reprompt_text = "I did not find the name " + name_to_ping + " in your contact list. If I misheard you, please repeat yourself. Otherwise, please add the contact by saying add " + name_to_ping + " to contacts."
            card_output = "I did not find the name " + name_to_ping + " in your contact list. If I misheard you, please repeat yourself. Otherwise, please add the contact by saying add " + name_to_ping + " to contacts."
            payload = json.dumps({'intent':'message','message':'error','details': card_output})
            should_end_session = False
    
    else:        
        
        speech_output = "I didnt fully capture the request. Please repeat your request."
        reprompt_text = "I didnt fully capture the request. Please repeat your request."
        card_output = "I didnt fully capture the request. Please repeat your request."
        payload = json.dumps({'intent':'message','message':'error','details': card_output})
        should_end_session = False
    
    return build_response(session_attributes, build_speechlet_response2(
        card_title, speech_output, reprompt_text, should_end_session,card_output, card_type, topic,payload,session_attributes ))

#Takes a selfie; this requires a mqtt call to the physical device to initiate taking the photo       
def take_selfie(intent, session, session_attributes):
    """ If we wanted to initialize the session to have some attributes we could
    add those here
    """
    
    card_title = "Send Selfie"
    
    if session_attributes['IOTEnabled'] == False:
        speech_output = "This is a special feature only available to users that have built a magic mirror enabled Raspberry Pi device. You can contact the skill owner from the privacy link to get information about building a device."
        reprompt_text = "This is a special feature only available to users that have built a magic mirror enabled Raspberry Pi device. You can contact the skill owner from the privacy link to get information about building a device."
        should_end_session = True
        
        return build_response(session_attributes, build_speechlet_response(
            card_title, speech_output, reprompt_text, should_end_session)) 

    photo_id = uuid.uuid4()    
    photo_id = 'photo' + str(photo_id)
    session_attributes.update({'active_intent_name' : "sendselfie_contact"})    
    session_attributes.update({'photo_id':photo_id})
    
    card_title = "Take Selfie"
    card_type = 'Simple'
    topic = "display"
    speech_output = "Would you like to send this photo to one of your contacts?"
    reprompt_text = "Would you like to send this photo to one of your contacts?"
    card_output = "Ok, taking the photo now."
    payload = json.dumps({'intent':'takeselfie','photo_id':photo_id})
    should_end_session = False
    

    sns_message = json.dumps({'topic': 'selfie' ,'payload': photo_id})
    response = sns.publish(
        TopicArn='arn:aws:sns:us-east-1:039057814095:Magic_Mirror_MQTT',
        Message=sns_message)
    
    return build_response(session_attributes, build_speechlet_response2(
        card_title, speech_output, reprompt_text, should_end_session,card_output, card_type, topic,payload,session_attributes ))

#Determines if the selfie should be sent to a named contact            
def send_selfie_contact(intent, session, session_attributes):
    """ If we wanted to initialize the session to have some attributes we could
    add those here
    """
    
    card_title = "Send Selfie"
    
    if session_attributes['IOTEnabled'] == False:
        speech_output = "This is a special feature only available to users that have built a magic mirror enabled Raspberry Pi device. You can contact the skill owner from the privacy link to get information about building a device."
        reprompt_text = "This is a special feature only available to users that have built a magic mirror enabled Raspberry Pi device. You can contact the skill owner from the privacy link to get information about building a device."
        should_end_session = True
        
        return build_response(session_attributes, build_speechlet_response(
            card_title, speech_output, reprompt_text, should_end_session)) 
    
    #if the response is negative, exit
    if 'slots' in intent:
        if 'YesNo' in intent['slots']:
            if 'value' in intent['slots']['YesNo'] and "yes" not in intent['slots']['YesNo']['value']:
                speech_output = "Ok, I won't send the selfie."
                reprompt_text = "Ok, I won't send the selfie."
                should_end_session = True
            
            else:    
            
                if session.get('attributes', {}) and "active_intent_name" in session.get('attributes', {}):
                    photo_id = session['attributes']['photo_id']
                    session_attributes.update({'photo_id':photo_id})
        
                session_attributes.update({'active_intent_name' : "sendselfie_publish"})
                speech_output = "Ok. Tell me the name of the person that you want me to send the selfie to."
                reprompt_text = "Ok. Tell me the name of the person that you want me to send the selfie to."
                should_end_session = False     

        else:    
            session_attributes.update({'active_intent_name' : "sendselfie_publish"})
            speech_output = "I'm cancelling the request because you didn't say yes or no."
            reprompt_text = "I'm cancelling the request because you didn't say yes or no."
            should_end_session = True
    
    else:    
        session_attributes.update({'active_intent_name' : "sendselfie_publish"})
        speech_output = "I'm cancelling the request because you didn't say yes or no."
        reprompt_text = "I'm cancelling the request because you didn't say yes or no."
        should_end_session = True
    
    card_title = "Send Selfie"
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

#Sends the selfie to a named contact
def send_selfie_publish(intent, session, session_attributes):
    """ If we wanted to initialize the session to have some attributes we could
    add those here
    """
    card_title = "Send Selfie"
    should_end_session = True
    
    if session_attributes['IOTEnabled'] == False:
        speech_output = "This is a special feature only available to users that have built a magic mirror enabled Raspberry Pi device. You can contact the skill owner from the privacy link to get information about building a device."
        reprompt_text = "This is a special feature only available to users that have built a magic mirror enabled Raspberry Pi device. You can contact the skill owner from the privacy link to get information about building a device."
        should_end_session = True
        
        return build_response(session_attributes, build_speechlet_response(
            card_title, speech_output, reprompt_text, should_end_session)) 
    
    
    speech_output = ""
    card_output = ""
    card_type = 'Simple'
    topic = "display"
    message = ""
    payload = ""
    reprompt_text = ""
    
    message_to_ping = ""
    name_to_ping = ""
    
    if session.get('attributes', {}) and "active_intent_name" in session.get('attributes', {}):
        if session['attributes']['active_intent_name'] == "sendselfie_publish": #this was routed from the the selfie function, so it is ok to procees
        
            photo_id = session['attributes']['photo_id']
            
            key = "Photos/" + photo_id + ".jpg"
            response = s3.generate_presigned_url('get_object', Params = {'Bucket': bucket, 'Key': key}, ExpiresIn = 60)
            print(response)
            message_to_ping = "Check out this selfie: " + "https://" + bucket + ".s3.amazonaws.com/" + key
    
    
            if 'Name' in intent['slots']:
                    if 'value' in intent['slots']['Name']:
                        name_to_ping = intent['slots']['Name']['value']
                        print("Here:" + name_to_ping)

            if len(name_to_ping) > 0 and len(message_to_ping) > 0 :
                table = 'Magic_Mirror_Contact'
                response = dynamodb.get_item(TableName = table,
                    Key={
                         'Email' : {
                          "S" : session_attributes['email']
                        },
                        'ContactName' : {
                          "S" : name_to_ping
                        }

                    })
                    
                            
                if 'Item' in response:
                    print("A")
                    
                    if 'TopicArn' in response['Item']:
                    
                        print("B")

                        sns_message = session_attributes['first_name'] + " says " + message_to_ping
                        response = sns.publish(
                            TopicArn=response['Item']['TopicArn']['S'],
                            Message=sns_message)
                        
                        speech_output = "The message was sent to " + name_to_ping + "."
                        reprompt_text = "The message was sent to " + name_to_ping + "."
                        card_output = "The message was sent to " + name_to_ping + "."
                        payload = json.dumps({'intent':'message','message':'success','name': name_to_ping, 'details': message_to_ping})
                        should_end_session = True
                        
                    else:
                        print("C")
                        speech_output = "There was a problem trying to send a message to this contact. Can you please re-create the contact by saying 'add " + name_to_ping + " to contacts'?"
                        reprompt_text = "There was a problem trying to send a message to this contact. Can you please re-create the contact by saying 'add " + name_to_ping + " to contacts'?"
                        card_output = "There was a problem trying to send a message to this contact. Can you please re-create the contact by saying 'add " + name_to_ping + " to contacts'?"
                        session_attributes.update({'active_intent_name' : "addcontactname"}) 
                        payload = json.dumps({'intent':'message','message':'error','details': card_output})
                        should_end_session = False
                        
                else: #did not find a name
                    print("D")
                    speech_output = "I did not find the name " + name_to_ping + " in your settings. If I missheard you, please tell me the name again. Otherwise, please cancel this request and add the contact by saying 'add " + name_to_ping + " to contacts'."
                    reprompt_text = "I did not find the name " + name_to_ping + " in your settings. If I missheard you, please tell me the name again. Otherwise, please cancel this request and add the contact by saying 'add " + name_to_ping + " to contacts'."
                    card_output = "I did not find the name " + name_to_ping + " in your settings. If I missheard you, please tell me the name again. Otherwise, please cancel this request and add the contact by saying 'add " + name_to_ping + " to contacts'."
                    payload = json.dumps({'intent':'message','message':'error','details': card_output})
                    session_attributes.update({'active_intent_name' : "sendselfie_publish"})
                    should_end_session = False
    
    
            else:
                print("E")
                speech_output = "I did understand the name of the contact. Please tell me the name again."
                reprompt_text = "I did understand the name of the contact. Please tell me the name again."
                card_output = "I did understand the name of the contact. Please tell me the name again."
                payload = json.dumps({'intent':'message','message':'error','details': card_output})
                session_attributes.update({'active_intent_name' : "sendselfie_publish"})
                should_end_session = False
                
        else:
            print("F")
            session_attributes = {}
            card_title = "I Do Not Understand" 
            speech_output = "I did not understand your request. Can you try again, or rephrase."
            # If the user either does not reply to the welcome message or says something
            # that is not understood, they will be prompted again with this text.
            reprompt_text = "I did not understand your request. Can you try again, or rephrase."
            should_end_session = True
            return build_response(session_attributes, build_speechlet_response(
                card_title, speech_output, reprompt_text, should_end_session))   
            
    else:
        print("G")
        session_attributes = {}
        card_title = "I Do Not Understand" 
        speech_output = "I did not understand your request. Can you try again, or rephrase."
        # If the user either does not reply to the welcome message or says something
        # that is not understood, they will be prompted again with this text.
        reprompt_text = "I did not understand your request. Can you try again, or rephrase."
        should_end_session = True
    
        return build_response(session_attributes, build_speechlet_response(
            card_title, speech_output, reprompt_text, should_end_session))
            
    return build_response(session_attributes, build_speechlet_response2(
        card_title, speech_output, reprompt_text, should_end_session,card_output, card_type, topic,payload,session_attributes ))

#Returns an inspirational quote
def get_inspiration (intent, session, session_attributes):

    card_title = "Inspirational Quote"
    should_end_session = True
    
    speech_output = ""
    card_output = ""
    card_type = 'Simple'
    topic = "display"
    message = ""
    payload = ""
    reprompt_text = ""
    quoteText = ""
    quoteAuthor = ""
    
    URL="http://api.forismatic.com/api/1.0/?method=getQuote&format=json&lang=en"
    req = urllib2.Request(URL)
    req.add_header('Content-Type', 'application/x-www-form-urlencoded')
       
    #Fire off the request
    try:
        response = urllib2.urlopen(req, timeout =3)
        FullResponse = response.read()
        FullResponse = FullResponse.replace("\\","")
        print(FullResponse)
        
        parsed_response = json.loads(FullResponse)
        
        print(parsed_response)
        
        quoteText = parsed_response['quoteText']
        quoteAuthor = parsed_response['quoteAuthor']      
                     
        speech_output = quoteText  + " " + quoteAuthor 
        reprompt_text = quoteText + "<p>" + quoteAuthor + "</p>"
        card_output = quoteText + "\n\n- " + quoteAuthor
        payload = json.dumps({'intent':'inspiration','message':'success','quoteAuthor':quoteAuthor, 'quoteText':quoteText})
        should_end_session = True
               
    except urllib2.URLError as e:
                
        speech_output = "There was a problem retrieving your quote. Please try again later."
        reprompt_text = "There was a problem retrieving your quote. Please try again later."
        card_output = "There was a problem retrieving your quote. Please try again later."
        payload = json.dumps({'intent':'inspiration','message':'error'})
        should_end_session = True
    
    except socket.timeout as e:
    
        speech_output = "There was a problem retrieving your quote. Please try again later."
        reprompt_text = "There was a problem retrieving your quote. Please try again later."
        card_output = "There was a problem retrieving your quote. Please try again later."
        payload = json.dumps({'intent':'inspiration','message':'error'})
        should_end_session = True
    
    return build_response(session_attributes, build_speechlet_response2(
        card_title, speech_output, reprompt_text, should_end_session,card_output, card_type, topic,payload,session_attributes )) 

#Shows the last message displayed
def show_again(intent, session, session_attributes):
    """ If we wanted to initialize the session to have some attributes we could
    add those here
    """
    
    card_title = "Show Again"
    
    if session_attributes['IOTEnabled'] == False:
        speech_output = "This is a special feature only available to users that have built a magic mirror enabled Raspberry Pi device. You can contact the skill owner from the privacy link to get information about building a device."
        reprompt_text = "This is a special feature only available to users that have built a magic mirror enabled Raspberry Pi device. You can contact the skill owner from the privacy link to get information about building a device."
        should_end_session = True
        
        return build_response(session_attributes, build_speechlet_response(
            card_title, speech_output, reprompt_text, should_end_session)) 

    
    card_title = "Show Again"
    card_type = 'Simple'
    topic = "display"
    speech_output = "Sure thing."
    reprompt_text = "Sure thing."
    card_output = "Show Screen Again."
    payload = json.dumps({'intent':'show'})
    should_end_session = True
    
    return build_response(session_attributes, build_speechlet_response2(
        card_title, speech_output, reprompt_text, should_end_session,card_output, card_type, topic,payload,session_attributes ))
        
#Provides a 2 minute timer
def teeth_timer(intent, session, session_attributes):
    """ If we wanted to initialize the session to have some attributes we could
    add those here
    """
    
    card_title = "Teeth Timer"
    
    if session_attributes['IOTEnabled'] == False:
        speech_output = "This is a special feature only available to users that have built a magic mirror enabled Raspberry Pi device. You can contact the skill owner from the privacy link to get information about building a device."
        reprompt_text = "This is a special feature only available to users that have built a magic mirror enabled Raspberry Pi device. You can contact the skill owner from the privacy link to get information about building a device."
        should_end_session = True
        
        return build_response(session_attributes, build_speechlet_response(
            card_title, speech_output, reprompt_text, should_end_session)) 

    
    card_title = "Teeth Timer"
    card_type = 'Simple'
    topic = "display"
    speech_output = "O.K. Starting your timer now."
    reprompt_text = "O.K. Starting your timer now."
    card_output = "O.K. Starting your timer now"
    payload = json.dumps({'intent':'teeth'})
    should_end_session = True
    
    return build_response(session_attributes, build_speechlet_response2(
        card_title, speech_output, reprompt_text, should_end_session,card_output, card_type, topic,payload,session_attributes ))

#Create a reminder 
def remind_me(intent, session, session_attributes):
    """ If we wanted to initialize the session to have some attributes we could
    add those here
    """
    
    card_title = "Create Reminer"
    
    if session_attributes['IOTEnabled'] == False:
        speech_output = "This is a special feature only available to users that have built a magic mirror enabled Raspberry Pi device. You can contact the skill owner from the privacy link to get information about building a device."
        reprompt_text = "This is a special feature only available to users that have built a magic mirror enabled Raspberry Pi device. You can contact the skill owner from the privacy link to get information about building a device."
        should_end_session = True
        
        return build_response(session_attributes, build_speechlet_response(
            card_title, speech_output, reprompt_text, should_end_session)) 

    
    if 'Reminder' in intent['slots'] and len(intent['slots']['Reminder']['value'])>0 :
        session_attributes.update({'Reminder':intent['slots']['Reminder']['value']})
    else:
        speech_output = "What should I remind you to do?"
        reprompt_text = "What should I remind you to do?"
        should_end_session = False
        
        session_attributes.update({'active_intent_name' : "remind_me"})
                
        return build_response(session_attributes, build_speechlet_response(
            card_title, speech_output, reprompt_text, should_end_session)) 
            
 
    card_type = 'Simple'
    topic = "display"
    speech_output = "Is this a single, daily, or weekly reminder?"
    reprompt_text = "Is this a single, daily, or weekly reminder?"
    card_output = "Is this a single, daily, or weekly reminder?"
    display_output = "Creating a reminder to " + session_attributes['Reminder']
    payload = json.dumps({'intent':'create_reminder','display':display_output})
    should_end_session = False
    
    session_attributes.update({'active_intent_name' : "remind_me_freq"})
    
    return build_response(session_attributes, build_speechlet_response2(
        card_title, speech_output, reprompt_text, should_end_session,card_output, card_type, topic,payload,session_attributes ))

#Get the frequency of the reminder
def remind_me_freq(intent, session, session_attributes):
    """ If we wanted to initialize the session to have some attributes we could
    add those here
    """
    
    card_title = "Create Reminer"
    
    if session_attributes['IOTEnabled'] == False:
        speech_output = "This is a special feature only available to users that have built a magic mirror enabled Raspberry Pi device. You can contact the skill owner from the privacy link to get information about building a device."
        reprompt_text = "This is a special feature only available to users that have built a magic mirror enabled Raspberry Pi device. You can contact the skill owner from the privacy link to get information about building a device."
        should_end_session = True
        
        return build_response(session_attributes, build_speechlet_response(
            card_title, speech_output, reprompt_text, should_end_session)) 

    
    if 'Freq' in intent['slots'] and len(intent['slots']['Freq']['value'])>0 :
        session_attributes.update({'Freq':intent['slots']['Freq']['value']})
        
        if intent['slots']['Freq']['value'] == "daily":
            speech_output = "Ok, on what day should I start reminding you?"
        if intent['slots']['Freq']['value'] == "weekly":
            speech_output = "Ok, on what day should I remind you?"
        else:
            speech_output = "Ok, on what day should I remind you?"
            
    else:
        speech_output = "Is this a single, daily, or weekly reminder? You can also say cancel to exit."
        reprompt_text = "Is this a single, daily, or weekly reminder? You can also say cancel to exit."
        should_end_session = False
        
        
        session_attributes.update({'active_intent_name' : "remind_me_freq"})
                
        return build_response(session_attributes, build_speechlet_response(
            card_title, speech_output, reprompt_text, should_end_session)) 
            
 
    card_type = 'Simple'
    topic = "display"
    reprompt_text = speech_output
    card_output = speech_output
    display_output = "Creating a " + session_attributes['Freq']  + " reminder to " + session_attributes['Reminder']
    payload = json.dumps({'intent':'create_reminder','display':display_output})
    should_end_session = False
    
    session_attributes.update({'active_intent_name' : "remind_me_day"})
    
    return build_response(session_attributes, build_speechlet_response2(
        card_title, speech_output, reprompt_text, should_end_session,card_output, card_type, topic,payload,session_attributes ))

        
#Get the start day of the reminder 
def remind_me_day(intent, session, session_attributes):
    """ If we wanted to initialize the session to have some attributes we could
    add those here
    """
    
    card_title = "Create Reminer"
    
    if session_attributes['IOTEnabled'] == False:
        speech_output = "This is a special feature only available to users that have built a magic mirror enabled Raspberry Pi device. You can contact the skill owner from the privacy link to get information about building a device."
        reprompt_text = "This is a special feature only available to users that have built a magic mirror enabled Raspberry Pi device. You can contact the skill owner from the privacy link to get information about building a device."
        should_end_session = True
        
        return build_response(session_attributes, build_speechlet_response(
            card_title, speech_output, reprompt_text, should_end_session)) 

    
    if 'Day' in intent['slots'] and len(intent['slots']['Day']['value'])>0 :
        session_attributes.update({'Day':intent['slots']['Day']['value']})
    else:
        speech_output = "Ok, on what day should I remind you?"
        reprompt_text = "Ok, on what day should I remind you?"
        should_end_session = False
        
        session_attributes.update({'active_intent_name' : "remind_me_day"})
                
        return build_response(session_attributes, build_speechlet_response(
            card_title, speech_output, reprompt_text, should_end_session)) 
            
 
    day_obj = datetime.strptime(session_attributes['Day'], '%Y-%m-%d')
    day_obj_day = day_obj.strftime('%A')
 
    card_type = 'Simple'
    topic = "display"
    speech_output = "What time do you want to be reminded?"
    reprompt_text = "What time do you want to be reminded?"
    card_output = "What time do you want to be reminded?"
    display_output = "Creating a " + session_attributes['Freq']  + " reminder to " + session_attributes['Reminder'] + " on " + day_obj_day
    payload = json.dumps({'intent':'create_reminder','display':display_output})
    should_end_session = False
    
    session_attributes.update({'active_intent_name' : "remind_me_time"})
    
    return build_response(session_attributes, build_speechlet_response2(
        card_title, speech_output, reprompt_text, should_end_session,card_output, card_type, topic,payload,session_attributes ))

#Get the time of the reminder         
def remind_me_time(intent, session, session_attributes):
    """ If we wanted to initialize the session to have some attributes we could
    add those here
    """
    
    card_title = "Create Reminder"
    
    if session_attributes['IOTEnabled'] == False:
        speech_output = "This is a special feature only available to users that have built a magic mirror enabled Raspberry Pi device. You can contact the skill owner from the privacy link to get information about building a device."
        reprompt_text = "This is a special feature only available to users that have built a magic mirror enabled Raspberry Pi device. You can contact the skill owner from the privacy link to get information about building a device."
        should_end_session = True
        
        return build_response(session_attributes, build_speechlet_response(
            card_title, speech_output, reprompt_text, should_end_session)) 

    
    if 'Time' in intent['slots'] and len(intent['slots']['Time']['value'])>0 :
        if ":" not in intent['slots']['Time']['value']:
            speech_output = "Can you be more precise? Try saying Eleven A.M. or Eight P.M."
            reprompt_text = "Can you be more precise? Try saying Eleven A.M. or Eight P.M."
            should_end_session = False
            
            session_attributes.update({'active_intent_name' : "remind_me_time"})
                
            return build_response(session_attributes, build_speechlet_response(
                card_title, speech_output, reprompt_text, should_end_session))
                
        else:   
            session_attributes.update({'Time':intent['slots']['Time']['value']})
    else:
        speech_output = "What time do you want to be reminded?"
        reprompt_text = "What time do you want to be reminded?"
        should_end_session = False
                
        session_attributes.update({'active_intent_name' : "remind_me_time"})
                
        return build_response(session_attributes, build_speechlet_response(
            card_title, speech_output, reprompt_text, should_end_session)) 
        
    if session_attributes['Freq'] == 'single':
        speech_output = "O.K. I will create a one time reminder for you to " + session_attributes['Reminder'] + "."
    else:
        speech_output = "O.K. I will create a " + session_attributes['Freq'] + " reminder for you to " + session_attributes['Reminder'] + "."
        
        
    details = {}
    email = session_attributes['email']
    email_str = {'S' : email}
    details.update({"Email": email_str})
    
    reminder_str = {'S' : session_attributes['Reminder']}
    details.update({"Reminder": reminder_str})
    
    frquency_str = {'S' : session_attributes['Freq']}
    details.update({"Frequency": frquency_str})
    
    date_str = {'S' : session_attributes['Day'] + " " + session_attributes['Time']}
    details.update({"DateStr": date_str})
                
    response = update_table('Magic_Mirror_Reminders',details)    
    
    day_obj = datetime.strptime(session_attributes['Day'], '%Y-%m-%d')
    day_obj_day = day_obj.strftime('%A')
 
    time_obj = datetime.strptime(session_attributes['Time'], '%H:%M')
    time_obj_time = time_obj.strftime('%I:%M %p')
 
    card_type = 'Simple'
    topic = "display"
    reprompt_text = speech_output
    card_output = speech_output
    display_output = "Creating a " + session_attributes['Freq']  + " reminder to " + session_attributes['Reminder'] + " starting " + day_obj_day + " at " + time_obj_time
    payload = json.dumps({'intent':'create_reminder','display':display_output})
    should_end_session = True
    
    return build_response(session_attributes, build_speechlet_response2(
        card_title, speech_output, reprompt_text, should_end_session,card_output, card_type, topic,payload,session_attributes ))
 
#clear the reminder from the display and set the reminder to the next day or week    
def clear_reminders(intent, session, session_attributes):
    """ If we wanted to initialize the session to have some attributes we could
    add those here
    """
    
    card_title = "Clear Reminers"
    
    if session_attributes['IOTEnabled'] == False:
        speech_output = "This is a special feature only available to users that have built a magic mirror enabled Raspberry Pi device. You can contact the skill owner from the privacy link to get information about building a device."
        reprompt_text = "This is a special feature only available to users that have built a magic mirror enabled Raspberry Pi device. You can contact the skill owner from the privacy link to get information about building a device."
        should_end_session = True
        
        return build_response(session_attributes, build_speechlet_response(
            card_title, speech_output, reprompt_text, should_end_session)) 

    loc_results = get_location(session, intent, session_attributes)
    parsed_loc_results = json.loads(loc_results)
        
    #set variables
    lat = parsed_loc_results['lat']
    lng = parsed_loc_results['lng']
    loc_status = parsed_loc_results['loc_status']
    session_attributes = parsed_loc_results['session_attributes']
    
    current_time = get_current_time(lat,lng)
            
    if current_time != 'unknown':
    
        current_time_obj = datetime.strptime(current_time, '%Y-%m-%d %H:%M')
        
        table = dynamodb2.Table('Magic_Mirror_Reminders')
        response = table.query(KeyConditionExpression=Key('Email').eq(session_attributes['email']))
        
        for i in response['Items']:
            if 'Display' in i:
            
                reminder_time_obj = datetime.strptime(i['DateStr'], '%Y-%m-%d %H:%M')
            
                print(i['Reminder'])
                if  i['Frequency'] =="daily":
                    print('in daily')
                    current_time_obj = current_time_obj + timedelta(days=1)
                    newtime = current_time_obj.strftime('%Y-%m-%d') + " " + reminder_time_obj.strftime('%H:%M')
                    
                    response = table.update_item(
                    Key={
                        'Email': session_attributes['email'],
                        'Reminder': i['Reminder']
                    },
                    UpdateExpression="set DateStr = :d remove Display",
                    ExpressionAttributeValues={
                        ':d': newtime
                    }
                    )
                
                elif i['Frequency'] =="weekly":
                    print('in weekly')
                    reminder_time_obj = reminder_time_obj + timedelta(days=7)
                    newtime = reminder_time_obj.strftime('%Y-%m-%d %H:%M')
                    
                    response = table.update_item(
                    Key={
                        'Email': session_attributes['email'],
                        'Reminder': i['Reminder']
                    },
                    UpdateExpression="set DateStr = :d remove Display",
                    ExpressionAttributeValues={
                        ':d': newtime
                    }
                    )
                
                else:
                    print('in delete')
                    response = dynamodb.delete_item(TableName = 'Magic_Mirror_Reminders',
                    Key={
                         'Email' : {
                          "S" :session_attributes['email']
                    },
                    'Reminder' : {
                          "S" :i['Reminder']
                    }
                    
                    })                
               
        
    card_type = 'Simple'
    topic = "display"
    speech_output = "I've cleared your reminders."
    reprompt_text = "I've cleared your reminders."
    card_output = "I've cleared your reminders."
    display_output = 'Working'
    payload = json.dumps({'intent':'remindersprint','reminders':""})
    should_end_session = True
    
    return build_response(session_attributes, build_speechlet_response2(
        card_title, speech_output, reprompt_text, should_end_session,card_output, card_type, topic,payload,session_attributes ))

#clear delete the reminder         
def delete_reminders(intent, session, session_attributes):
    """ If we wanted to initialize the session to have some attributes we could
    add those here
    """
    
    card_title = "Delete Reminers"
    Reminder_list = ""
    
    if session_attributes['IOTEnabled'] == False:
        speech_output = "This is a special feature only available to users that have built a magic mirror enabled Raspberry Pi device. You can contact the skill owner from the privacy link to get information about building a device."
        reprompt_text = "This is a special feature only available to users that have built a magic mirror enabled Raspberry Pi device. You can contact the skill owner from the privacy link to get information about building a device."
        should_end_session = True
        
        return build_response(session_attributes, build_speechlet_response(
            card_title, speech_output, reprompt_text, should_end_session)) 

    
    table = dynamodb2.Table('Magic_Mirror_Reminders')
    response = table.query(KeyConditionExpression=Key('Email').eq(session_attributes['email']))
    
    for i in response['Items']:
        Reminder_list = Reminder_list + '<li>' + i['Reminder'] + '</li>'
           
    
    if len(response['Items']) == 0:
        speech_output = "There are no reminders to delete."
        reprompt_text = "There are no reminders to delete."
        should_end_session = True
        
        return build_response(session_attributes, build_speechlet_response(
            card_title, speech_output, reprompt_text, should_end_session))

    if 'InputNumber' in intent['slots']:
        if 'value' in intent['slots']['InputNumber']:
    
            if 0 < int(intent['slots']['InputNumber']['value']) <= len(response['Items']):
            
                DeleteNo = int(intent['slots']['InputNumber']['value'])
                
                count = 0            
                for i in response['Items']:
                    print("Reminder no:" + i['Reminder'])
                    print("Delete no:" + str(DeleteNo))
                    count = count+1
                    if count == DeleteNo:
                        deleteresponse = dynamodb.delete_item(TableName = 'Magic_Mirror_Reminders',
                            Key={
                                'Email' : {
                                 "S" :session_attributes['email']
                                },
                                'Reminder' : {
                                "S" :i['Reminder']
                                }
                            })   
                    
                card_type = 'Simple'
                topic = "display"
                speech_output = "I've deleted the reminder."
                reprompt_text = "I've deleted the reminder."
                card_output = "I've deleted the reminder."
                display_output = 'Working'
                payload = json.dumps({'intent':'reset_reminders'})
                should_end_session = True
                
                return build_response(session_attributes, build_speechlet_response2(
                    card_title, speech_output, reprompt_text, should_end_session,card_output, card_type, topic,payload,session_attributes ))
                    
            else:
                card_type = 'Simple'
                topic = "display"
                speech_output = "I didn't understand the number of the reminder you wish to delete. Can you tell me the number again?"
                reprompt_text = "I didn't understand the number of the reminder you wish to delete. Can you tell me the number again?"
                card_output = "I didn't understand the number of the reminder you wish to delete. Can you tell me the number again?"
                display_output = 'Working'
                payload = json.dumps({'intent':'reminderdelete','reminderslist':Reminder_list})
                
                should_end_session = False
                
                session_attributes.update({'active_intent_name' : "delete_reminders"})  
                
                return build_response(session_attributes, build_speechlet_response2(
                    card_title, speech_output, reprompt_text, should_end_session,card_output, card_type, topic,payload,session_attributes ))
        else:
            card_type = 'Simple'
            topic = "display"
            speech_output = "Tell me the number of the reminder you want me to delete."
            reprompt_text = "Tell me the number of the reminder you want me to delete."
            card_output = "Tell me the number of the reminder you want me to delete."
            display_output = 'Working'
            payload = json.dumps({'intent':'reminderdelete','reminderslist':Reminder_list})
               
            should_end_session = False
                
            session_attributes.update({'active_intent_name' : "delete_reminders"})  
                
            return build_response(session_attributes, build_speechlet_response2(
                card_title, speech_output, reprompt_text, should_end_session,card_output, card_type, topic,payload,session_attributes ))
                
    else:   
        card_type = 'Simple'
        topic = "display"
        speech_output = "Tell me the number of the reminder you want me to delete."
        reprompt_text = "Tell me the number of the reminder you want me to delete."
        card_output = "Tell me the number of the reminder you want me to delete."
        display_output = 'Working'
        payload = json.dumps({'intent':'reminderdelete','reminderslist':Reminder_list})
        
        should_end_session = False
        
        session_attributes.update({'active_intent_name' : "delete_reminders"})  
        
        return build_response(session_attributes, build_speechlet_response2(
            card_title, speech_output, reprompt_text, should_end_session,card_output, card_type, topic,payload,session_attributes ))
           
 
#This is called if the request is not understood       
def misunderstood():
    """ If we wanted to initialize the session to have some attributes we could
    add those here
    """
    session_attributes = {}
    card_title = "I Do Not Understand" 
    speech_output = "I did not understand your request. Can you try again, or rephrase."
    # If the user either does not reply to the welcome message or says something
    # that is not understood, they will be prompted again with this text.
    reprompt_text = "I did not understand your request. Can you try again, or rephrase."
    should_end_session = True
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

#This is called to end the session 
def handle_session_end_request():
    card_title = "Session Ended"
    speech_output = "Thank you for using the Mystic Mirror skill. " \
                    "Have a nice day!"
    # Setting this to true ends the session and exits the skill.
    should_end_session = True
    return build_response({}, build_speechlet_response(
        card_title, speech_output, None, should_end_session))




# --------------- Helpers that build all of the responses ----------------------

#This is the basic function if a mqtt call is not needed to the physical device
def build_speechlet_response(title, output, reprompt_text, should_end_session):
    
    if title == 'Link Account':
        cardtype = 'LinkAccount'
    else:
        cardtype = 'Simple'
        
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'card': {
            'type': cardtype,
            #'title': 'SessionSpeechlet - ' + title,
            #'content': 'SessionSpeechlet - ' + output
            'title': title,
            'content': output
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }

#This function is used if a message needs to be sent to the raspberry pi - for display on the Mystic Mirror screen
def build_speechlet_response2(card_title, speech_output, reprompt_text, should_end_session,card_output, card_type, topic, payload, session_attributes):
    
    if session_attributes['IOTEnabled'] == True:
        sns_message = json.dumps({'topic': session_attributes['email'] + "/" + topic ,'payload':payload})
        response = sns.publish(
            TopicArn=TopicARN,
            Message=sns_message)
    
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': speech_output
        },
        'card': {
            'type': card_type,
            #'title': 'SessionSpeechlet - ' + title,
            #'content': 'SessionSpeechlet - ' + output
            'title': card_title,
            'content': card_output
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }
    
def build_response(session_attributes, speechlet_response):
    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }


###### Helpers that support intents ##########

def get_profile(auth_token, session_attributes):
    
    URL = 'https://www.googleapis.com/oauth2/v2/userinfo'
    req = urllib2.Request(URL)
    
    #Add the headers, first we base64 encode the client id and client secret with a : inbetween and create the authorisation header
    req.add_header('Authorization', 'Bearer ' + auth_token)
    req.add_header('Content-Type', 'application/x-www-form-urlencoded')
    
    #Fire off the request
    try:
        response = urllib2.urlopen(req, timeout=5)
        FullResponse = response.read()
        parsed_response = json.loads(FullResponse)
        session_attributes.update({'email' : parsed_response['email']})
        session_attributes.update({'first_name' : parsed_response['given_name']})
        session_attributes.update({'user_linked' :True})
        
        session_attributes.update({'saved_location' :False})
        session_attributes.update({'IOTEnabled' :False})
        
        table = 'Magic_Mirror'
        response = dynamodb.get_item(TableName = table,
            Key={
                 'Email' : {
                  "S" : parsed_response['email']
                    }})

        #if user exists, get his default location
        if 'Item' in response:
            if 'City' in response['Item']:
                session_attributes.update({'city' :response['Item']['City']['S']})
                session_attributes.update({'saved_location' :True})
            if 'State' in response['Item']:
                session_attributes.update({'state' :response['Item']['State']['S']})
                session_attributes.update({'saved_location' :True})        
        else:         #if user does not exit then add him
            User_Details = {
                'Email': {'S':parsed_response['email']}
            }
            response = update_table(table, User_Details)
            
        #determine if user have IoT decvice - the magic mirror - enabled   
        table = 'Magic_Mirror_IOT'
        response = dynamodb.get_item(TableName = table,
            Key={
                 'Email' : {
                  "S" : parsed_response['email']
                    }})  

        if 'Item' in response:
            session_attributes.update({'IOTEnabled' :True})
                    
        
    except urllib2.URLError as e:
        session_attributes.update({'user_linked' :False})
        session_attributes.update({'saved_location' :False})
        session_attributes.update({'IOTEnabled' :False})
        #return session_attributes
        
    except socket.timeout as e:
        session_attributes.update({'user_linked' :False})
        session_attributes.update({'saved_location' :False})
        session_attributes.update({'IOTEnabled' :False})

    return session_attributes
    
#helper function to update dynamodb table    
def update_table(table,details):
    response = dynamodb.put_item(TableName = table, Item = details)
    
#helper function to convert Kelvin to Fahrenheit        
def k2f(t):
    return int((t*9/5.0)-459.67)

#helper function to get current time based on location      
def get_current_time(lat,lng):
    URL="http://api.geonames.org/timezoneJSON?formatted=true&lat=" + str(lat) + "&lng=" + str(lng) + "&username=dbj1906&style=full"
    req = urllib2.Request(URL)
    req.add_header('Content-Type', 'application/x-www-form-urlencoded')
            
    #Fire off the request
    try:
        response = urllib2.urlopen(req, timeout=4)
        FullResponse = response.read()
        parsed_response = json.loads(FullResponse)
                
        return parsed_response['time']
        
    except urllib2.URLError as e:
        return "unknown"
        
    except socket.timeout as e:
        return "unknown"

#helper function to get lat and long details for a location             
def get_location(session, intent, session_attributes):
    city =""
    state = ""


    #this checks to see if the location is in the attributes (not yet saved to session)
    if "city" in session_attributes:
        city = session_attributes['city']
    if "state" in session_attributes:
        state = session_attributes['state']
    

    
    #this checks to see if the location was saved to session 
    if session.get('attributes', {}) and "city" in session.get('attributes', {}):
        city = session['attributes']['city']
    if session.get('attributes', {}) and "state" in session.get('attributes', {}):
        state = session['attributes']['state']

        
    #this looks to see if the location was defined in the slot
    if 'slots' in intent:
        
        
        if 'City' in intent['slots'] and 'value' in intent['slots']['City']:
            if len(intent['slots']['City']['value'])>0:
                city = intent['slots']['City']['value']
                session_attributes.update({'city' :city})
                state = "" #clear out state value if the city is passed

        if 'State' in intent['slots'] and 'value' in intent['slots']['State']:
            if len(intent['slots']['State']['value'])>0:
                state = intent['slots']['State']['value']
                session_attributes.update({'state' :state})
            else:  #added by DBJ
                state = ""


    URL = "https://maps.googleapis.com/maps/api/geocode/json?address=" + city + "," + state + "&key=AIzaSyAebRROuB7o6CeVH_DLwEK_HK1Cr-HhWPs"
    URL = URL.replace(" ", "+")

    req = urllib2.Request(URL)
    
    #Add the headers
    req.add_header('Content-Type', 'application/x-www-form-urlencoded')
    
    #Initialize variables and Fire off the request
    no_of_records = 0
    status = "UNKNOWN_ERROR"
    loc_status = 0
    lat = 0
    lng = 0
    lat_ne = 0
    lng_ne = 0
    lat_sw = 0
    lng_sw = 0
    
    try:
        response = urllib2.urlopen(req, timeout=5)
        FullResponse = response.read()
        parsed_response = json.loads(FullResponse)
        status = parsed_response["status"]

    except urllib2.URLError as e:
        loc_status = 1 #we can't find the location
        
    except socket.timeout as e:
        loc_status = 1 #we can't find the location

    #check status codes of the returned JSON before proceeding to get latitude and longitude
    if status == "OK":
        no_of_records = len(parsed_response["results"])
        if no_of_records > 1:       #we found more than 1 record, we need to get more specific
            loc_status = 2
        else:                       #we only found 1 record; we can proceed
            lat = parsed_response['results'][0]['geometry']['location']['lat']
            lng = parsed_response['results'][0]['geometry']['location']['lng']
            
            lat_ne = parsed_response['results'][0]['geometry']['bounds']['northeast']['lat']
            lng_ne = parsed_response['results'][0]['geometry']['bounds']['northeast']['lng']
            lat_sw = parsed_response['results'][0]['geometry']['bounds']['southwest']['lat']
            lng_sw = parsed_response['results'][0]['geometry']['bounds']['southwest']['lng']
            
            
            loc_status = 0
    elif status == "ZERO_RESULTS":   #the location could not be found
        loc_status = 3
    else:                           #there was an error looking for the location
        loc_status = 4
    return json.dumps({'city':city,'state':state, 'lat':lat, 'lng':lng, 'lat_ne':lat_ne, 'lng_ne':lng_ne,'lat_sw':lat_sw, 'lng_sw':lng_sw,'session_attributes': session_attributes, 'loc_status':int(loc_status)})            