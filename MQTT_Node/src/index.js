/**
 * Darian Johnson
 */

var awsIot = require('aws-iot-device-sdk');
var config = require("./config");

var ctx = null;
var client = null;

// Route the incoming request based on type (LaunchRequest, IntentRequest, etc.) The JSON body of the request is provided in the event parameter.
exports.handler = function (event, context) {
    try {
		
		console.log(event);
		var obj = JSON.parse(event.Records[0].Sns.Message);
        console.log(obj);
		var topic = obj.topic;
		var payload = obj.payload;
		
		var deviceName = "MyMagicMirror-Lambda-" + topic;        // this device is really the controller

		var mqtt_config = {
			"keyPath": config.privateKey,
			"certPath": config.certificate,
			"caPath": config.rootCA,
			"host": config.host,
			"port": 8883,
			"clientId": deviceName, 
			"region":"us-east-1",
			"debug":true
		};
		
        console.log(event);
		var obj = JSON.parse(event.Records[0].Sns.Message);
        console.log(obj);
		var topic = obj.topic;
		var payload = obj.payload;
		
        ctx = context;

        client = awsIot.device(mqtt_config);

        client.on("connect",function(){
            console.log("Connected to AWS IoT");
        });
		
		mqttPublish(topic, payload);

    } catch (e) {
        console.log("EXCEPTION in handler:  " + e);
        ctx.fail("Exception: " + e);
    }
};


function mqttPublish(topic, payload)
{

    console.log("mqttPublish:  Topic = " + topic);
	console.log("mqttPublish:  Payload = " + payload);
    client.publish(topic, payload, "qos=1");
    client.end();

    client.on("close", (function () {
        console.log("MQTT CLIENT CLOSE - thinks it's done, successfully. ");
    }));

    client.on("error", (function (err, granted) {
        console.log("MQTT CLIENT ERROR!!  " + err);
    }));
}