 /**
   * utilities to do sigv4
   * @class SigV4Utils
   */
   
  function SigV4Utils(){}

  SigV4Utils.sign = function(key, msg){
    var hash = CryptoJS.HmacSHA256(msg, key);
    return hash.toString(CryptoJS.enc.Hex);
  };

  SigV4Utils.sha256 = function(msg) {
    var hash = CryptoJS.SHA256(msg);
    return hash.toString(CryptoJS.enc.Hex);
  };

  SigV4Utils.getSignatureKey = function(key, dateStamp, regionName, serviceName) {
    var kDate = CryptoJS.HmacSHA256(dateStamp, 'AWS4' + key);
    var kRegion = CryptoJS.HmacSHA256(regionName, kDate);
    var kService = CryptoJS.HmacSHA256(serviceName, kRegion);
    var kSigning = CryptoJS.HmacSHA256('aws4_request', kService);
    return kSigning;
  };

 
  
var email = '<ENTER THE EMAIL ADDRESS YOU USED FOR AUTHENTICATION - in lower case>'  
var time = moment.utc();
var dateStamp = time.format('YYYYMMDD');
var amzdate = dateStamp + 'T' + time.format('HHmmss') + 'Z';
var service = 'iotdevicegateway';
var region = 'us-east-1'; //change the region if you are not using US-East
var secretKey = '<ENTER YOUR SECRET KEY>';
var accessKey = '<ENTER YOUR ACCESS KEY>';
var algorithm = 'AWS4-HMAC-SHA256';
var method = 'GET';
var canonicalUri = '/mqtt';
var host = '<ENTER THE HOST ADDRESS - should look like - a6i0a3yz21r4k2.iot.us-east-1.amazonaws.com>'

var credentialScope = dateStamp + '/' + region + '/' + service + '/' + 'aws4_request';
var canonicalQuerystring = 'X-Amz-Algorithm=AWS4-HMAC-SHA256';
canonicalQuerystring += '&X-Amz-Credential=' + encodeURIComponent(accessKey + '/' + credentialScope);
canonicalQuerystring += '&X-Amz-Date=' + amzdate;
canonicalQuerystring += '&X-Amz-SignedHeaders=host';

var canonicalHeaders = 'host:' + host + '\n';

var payloadHash = SigV4Utils.sha256('');

var canonicalRequest = method + '\n' + canonicalUri + '\n' + canonicalQuerystring + '\n' + canonicalHeaders + '\nhost\n' + payloadHash;

    console.log('canonicalRequest ' + canonicalRequest);
	
	

var stringToSign = algorithm + '\n' +  amzdate + '\n' +  credentialScope + '\n' +  SigV4Utils.sha256(canonicalRequest);
var signingKey = SigV4Utils.getSignatureKey(secretKey, dateStamp, region, service);
var signature = SigV4Utils.sign(signingKey, stringToSign);

canonicalQuerystring += '&X-Amz-Signature=' + signature;

var requestUrl = 'wss://' + host + canonicalUri + '?' + canonicalQuerystring;

//requestUrl += "&X-Amz-Security-Token=" + encodeURIComponent(sessionToken);


var clientId='MyMagicMirror-web' + amzdate;

var client = new Paho.MQTT.Client(requestUrl, clientId);
var connectOptions = {
    onSuccess: function(){
		subscribe();
    },
    useSSL: true,
    timeout: 3,
    mqttVersion: 4,
    onFailure: function() {
        document.getElementById('successdisplay').innerHTML = "I am having a problem connecting to the Mystic Mirror Service.";
    }
};

client.connect(connectOptions);


if (client.connected) {

    };


client.onMessageArrived = onMessage;
client.onConnectionLost = function(e) { 

};	


 function subscribe() {
      client.subscribe(email + "/display");
      console.log("subscribed");
	  timedPublish();
	  
 };
 
 
var myKeepAlive = setInterval(function(){ sendPing() }, 43200000);

function sendPing() {
    client.pingreq;
}

function onMessage(message) {
	var obj = JSON.parse(message.payloadString)
	var oldinnerHTML = document.getElementById('successdisplay').innerHTML;
	
	if (obj.intent == "teeth" || obj.intent == "remindersprint" || obj.intent == "reset_reminders"){
		FormatMessage(message,oldinnerHTML);
	}
	else{

		  $( "#successdisplay" ).fadeOut(1000, function() {
			FormatMessage(message,oldinnerHTML);
		  });

	}
	
	

}
 
function FormatMessage(message,oldinnerHTML) {
		var obj = JSON.parse(message.payloadString)
		
	  //Brush Teeth Timer
	  if (obj.intent == "teeth"){
			$("#teeth").delay(120000).fadeOut(3000);
			delaysecs = 120000;
			setTimeout(Decrement,1000); 			
		}
		
	//Show Reminders in bottom div		
		else if (obj.intent == "remindersprint"){
		
			document.getElementById('reminder').innerHTML = obj.reminders;			
		}
	//Reset Reminders after delete	
		else if (obj.intent == "reset_reminders"){
			document.getElementById('reminder').innerHTML = ""
			sendtimetolambda();		
		}
		
		else{ //If the intent is one of the below, then it will show in the main div
			  
		 
		  var delaysecs = 8000;
		  
		  
		  if (obj.intent === "welcome") {
				document.getElementById('successdisplay').innerHTML = obj.message;
			} 
			else if (obj.intent === "help"){
				document.getElementById('successdisplay').innerHTML = obj.message;
			}
			else if (obj.intent === "quote"){
				document.getElementById('successdisplay').innerHTML = obj.message;
				delaysecs = 15000
			}
			else if (obj.intent === "location"){
				document.getElementById('successdisplay').innerHTML = obj.message;
			}
			else if (obj.intent === "create_reminder"){
				document.getElementById('successdisplay').innerHTML = obj.display;
			}
			else if (obj.intent === "reminderdelete"){
				document.getElementById('successdisplay').innerHTML = '<ol>' + obj.reminderslist + '</ol>';
			}
	//GET TIME		
			else if (obj.intent === "time" && obj.message === 'error'){
				document.getElementById('successdisplay').innerHTML = 'I was unable to tell you the time; can you try again later?'
			}
			else if (obj.intent === "time" && obj.message === 'success'){
				
				var innerHTMLval = "<table>" +
					"<tr><td class='time_day_date'>" + obj.cur_day + "<br>" + obj.cur_date + "</td></tr>" +
					"<tr><td class='time_time'>" + obj.cur_time + "</td></tr>" +
					"</table>"
				
				document.getElementById('successdisplay').innerHTML = innerHTMLval
				delaysecs = 15000
			}
			
	//GET WEATHER
			else if (obj.intent === "weather" && obj.message === 'error'){
				document.getElementById('successdisplay').innerHTML = obj.message_details;
			}
			else if (obj.intent === "weather" && obj.message === 'success'){

				var innerHTMLval = '<table class="weather">' +
					'<tr>' +
						'<td colspan=2 class="weather-loc">' + obj.city + ', ' + obj.state + '</td>' +
						'<td class="weather-time" align=right>' + obj.time + '</td>' +
					'</tr>' +
					'<tr>' +
						'<td class="weather-desc"><img src="http:' + obj.icon + '"></td>' +
						'<td class="weather-temp">' + obj.temp + '&deg<br><span style="font-size:14px;">(Feels Like ' + obj.feels_like + '&deg)</span></td>' +
						'<td class="weather-desc">' + obj.description + '</td>' +
					'</tr>' +
					'<tr>' +
						"<td colspan=3 class='weather-loc'>" + obj.forecast_day+ "'s Forecast</td>" +
					'</tr>' +
					'<tr>' +
						'<td class="weather-desc"><img src="http:' + obj.forecast_icon + '"></td>' +
						'<td class="weather-hilo"><span style="color:LightCoral">' + obj.forecast_hi + '&deg</span> | <span style="color:CadetBlue">' + obj.forecast_low  + '&deg</span></td>' +
						'<td class="weather-desc">' + obj.forecast_decs + '</td>'+
					'</tr>' +
					'</table><p><p>'
					
					innerHTMLval = innerHTMLval + '<table class="weather"><tr><td colspan=4 class="weather-loc">Four Day Forecast</td></tr>'
					innerHTMLval = innerHTMLval + ' <tr><td class="weather-forecast">' + obj.forecast_day1 + '</td><td class="weather-forecast"><img width="50%" src="http:' + obj.forecast_icon1 + '"> <td class="weather-forecast" style="width:125px"><span style="color:LightCoral">' + obj.forecast_hi1 + '&deg</span> | <span style="color:CadetBlue">' + obj.forecast_low1  + '&deg</span></td><td class="weather-forecast">' + obj.forecast_decs1 + '</td></tr>'
					innerHTMLval = innerHTMLval + ' <tr><td class="weather-forecast">' + obj.forecast_day2 + '</td><td class="weather-forecast"><img width="50%" src="http:' + obj.forecast_icon2 + '"> <td class="weather-forecast"><span style="color:LightCoral">' + obj.forecast_hi2 + '&deg</span> | <span style="color:CadetBlue">' + obj.forecast_low2  + '&deg</span></td><td class="weather-forecast">' + obj.forecast_decs2 + '</td></tr>'
					innerHTMLval = innerHTMLval + ' <tr><td class="weather-forecast">' + obj.forecast_day3 + '</td><td class="weather-forecast"><img width="50%" src="http:' + obj.forecast_icon3 + '"> <td class="weather-forecast"><span style="color:LightCoral">' + obj.forecast_hi3 + '&deg</span> | <span style="color:CadetBlue">' + obj.forecast_low3  + '&deg</span></td><td class="weather-forecast">' + obj.forecast_decs3 + '</td></tr>'
					innerHTMLval = innerHTMLval + ' <tr><td class="weather-forecast">' + obj.forecast_day4 + '</td><td class="weather-forecast"><img width="50%" src="http:' + obj.forecast_icon4 + '"> <td class="weather-forecast"><span style="color:LightCoral">' + obj.forecast_hi4 + '&deg</span> | <span style="color:CadetBlue">' + obj.forecast_low4  + '&deg</span></td><td class="weather-forecast">' + obj.forecast_decs4 + '</td></tr>'
					innerHTMLval = innerHTMLval + '</table>'
					
					
					document.getElementById('successdisplay').innerHTML = innerHTMLval;
					delaysecs = 15000
			}
	//GET TRAFFIC INFORMATION
			else if (obj.intent === "traffic" && obj.message === 'error'){
				document.getElementById('successdisplay').innerHTML = obj.details;
			}
			else if (obj.intent === "traffic" && obj.message === 'success'){
				var innerHTMLval = '<table class="traffic">' +
					'<tr>' +
						'<td class="traffic-image"><img src="' + obj.map + '"</td>' +
						'<td class="traffic-list">' + obj.details + '</td>' +
					'<tr>' +
					'</table>'
				
				document.getElementById('successdisplay').innerHTML = innerHTMLval;
				delaysecs = 20000
			}
	//SEND A MESSAGE
			else if (obj.intent === "message" && obj.message === 'error'){
				document.getElementById('successdisplay').innerHTML = obj.details;
			}
			else if (obj.intent === "message" && obj.message === 'success'){	
								
				var innerHTMLval = '<table>' +
					"<tr>" +
						"<td class='message_to' colspan=2>Message Sent to " + obj.name + "</td>" +
					"</tr>" +
					"<tr>" +
						"<td class='message_img'><img width=75% src='Images/Chat.png'></td>" +
						"<td class='message'><i>\"" + obj.details + "\"</i></td>" +
					"</tr>" +
					"</table>"
				
				document.getElementById('successdisplay').innerHTML = innerHTMLval;
			}
	//TAKE A SELFIE
			else if (obj.intent === "takeselfie"){
					
				var innerHTMLval = "Hold still. I'm taking your photo now."
				
				document.getElementById('successdisplay').innerHTML = innerHTMLval;
			}
			else if (obj.intent === "selfie-taken" && obj.message === 'error'){
					
				var innerHTMLval = "There was a problem taking the photo. Can you try again?"
				
				document.getElementById('successdisplay').innerHTML = innerHTMLval;
			}
			else if (obj.intent === "selfie-taken" && obj.message === 'success'){
				
				//alert("here")
				var photo_str = obj.photo.replace("\'", "");
				var photo_str = photo_str.replace("'", "");
				var photo_str = photo_str.replace("`", "");
				
				var innerHTMLval = '<table>' +
					"<tr>" +
						"<td class='message_img'><img src='" + photo_str  + "'></td>" +
						"<td class='message'>Would you to send this selfie to one of your conatcts?</td>" +
					"</tr>" +
					"</table>"
				
				document.getElementById('successdisplay').innerHTML = innerHTMLval;
				delaysecs = 10000
			}
	//PRINT THE NEWS HEADLINES
			else if (obj.intent === "news" && obj.message === 'error'){
					
				var innerHTMLval = "There was a problem obtaining your headlines. Can you try again?";
				
				document.getElementById('successdisplay').innerHTML = innerHTMLval;
			}
			else if (obj.intent === "news" && obj.message === 'success'){
				
				var newsobj = JSON.parse(obj.news_stories);
				
				var innerHTMLval = "<table>";
				
				for (i = 0; i < 5; i++) { 
					innerHTMLval += "<tr><td rowspan='2' class='news_image'><img src='" + newsobj.value[i].image.thumbnail.contentUrl + "'></td>"
					innerHTMLval += "<td class='news_headline'>" + newsobj.value[i].name + "</td></tr>";
					innerHTMLval += "<tr><td class='news_details'>" + newsobj.value[i].description + "</td></tr>";			
					
				}
				
				innerHTMLval += "</table>";
				
				document.getElementById('successdisplay').innerHTML = innerHTMLval;
				delaysecs = 45000
			}
	//INSPIRING QUOTE
			else if (obj.intent === "inspiration" && obj.message === 'error'){
					
				var innerHTMLval = "There was a problem obtaining your inspirational quote. Can you try again?";
				
				document.getElementById('successdisplay').innerHTML = innerHTMLval;
			}
			else if (obj.intent === "inspiration" && obj.message === 'success'){
							
				var innerHTMLval = "<table>";
				innerHTMLval += "<tr><td class='inspiration_quote'>" + obj.quoteText + "</td></tr>";
				innerHTMLval += "<tr><td class='inspiration_name'>- " + obj.quoteAuthor + "</td></tr>";			
				innerHTMLval += "</table>";
				
				document.getElementById('successdisplay').innerHTML = innerHTMLval;
			}
	//SHOW THE SCREEN AGAIN
			else if (obj.intent === "show"){
				document.getElementById('successdisplay').innerHTML = oldinnerHTML;
			}

	//ELSE the intent was not identified
			else {
				document.getElementById('successdisplay').innerHTML = message.payloadString;
			}
			 startFadeIn();
		  startFadeOut(delaysecs);
		  
		}
};

function send(content) {
	  //alert('in send');
      var message = new Paho.MQTT.Message(content);
      message.destinationName = "test/success";
      client.send(message);
      console.log("sent");
	  
    };

var mins = 2;  //Set the number of minutes you need
var secs = mins * 60;
var currentSeconds = 0;
var currentMinutes = 0;	
function Decrement() {
        currentMinutes = Math.floor(secs / 60);
        currentSeconds = secs % 60;
        if(currentSeconds <= 9) currentSeconds = "0" + currentSeconds;
        secs--;
        document.getElementById("teeth").innerHTML = currentMinutes + ":" + currentSeconds; //Set the element id you need the time put into.
        if(secs !== -1) setTimeout('Decrement()',1000);
};

function timedPublish() {
	sendtimetolambda();
    setInterval(sendtimetolambda, 1800000);
};
function sendtimetolambda() { //THIS FUNCTION IS USED TO QUERY FOR REMINDERS


	var d = new Date();
	var n = d.toLocaleString();
	var slash = n.indexOf('/');
	if (slash==1) n = '0' + n;
	var semi = n.indexOf(':');
	if (semi==14) n = n.replace(', ', ', 0');
	
	var payload = JSON.stringify({'email': email , 'time': n });
	client.send("remindertime/sendtime", payload);
}

var timer;
var timer2;
function startFadeOut(delaysecs) {
	clearTimeout(timer);
	timer = setTimeout(function() { $("#successdisplay").stop( true, true ).fadeOut(5000); }, delaysecs)
}


function startFadeIn() {
	clearTimeout(timer2);
	timer2 = setTimeout(function() { $("#successdisplay").stop( true, true ).fadeIn(500); }, 700)
}



