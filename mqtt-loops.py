import paho.mqtt.client as mqtt
import json
import redis



host_ip = "192.168.1.11"
redis_port = 6379
mqtt_port = 1883
topic_subs = ["info/#", "sensor/#", "dev/test", "cmd/#"]



def save_history(topic, message):
    #payload parsing for valid json only
    try:
        payload = json.loads(message)
    except ValueError:
        print("payload not formatted as a json")
    #to-do: complex data structure for topic hierarchy

def light_info_parser(topic, message):
    #adds callback topic to message control the lights
    #to-do: add error handling for missing topics
    #print("light info parser called with topic {} and message {}".format(topic, message))
    callback_topics = {"info/light/tradfri": "cmd/light/tradfri"}
    message_dict = json.loads(message)
    message_dict["callback"]  = callback_topics[topic]
    
    redis_key = "light@{}".format(message_dict["name"])
    redis_value = json.dumps(message_dict)
    print("setting redis with key {} and value {}".format(redis_key, redis_value))
    r.set(redis_key, redis_value)
    #print("DEBUG redis done")

def list_lights():
    #to-do: figure out multiple light sources
    return json.loads(r.get("info/lights/tradfri").decode("utf-8"))

def check_light_status(light):
        #print("check light status was called")
        light_body = r.get("light@{}".format(light))
        return json.loads(light_body)["state"]

def set_all_lights_to(dimmer, color_temp):
    #fetching lights
    lights = json.loads(r.get("info/lights/tradfri").decode("utf-8"))
    #turning all lights on or off
    for l in lights:
        print("light: {}, dimmer {} ".format(l, dimmer))
        alter_light(light=l,status="on", dimmer = dimmer, 
        color_temp = color_temp)

def scene_evening():
    set_all_lights_to(dimmer = 50, color_temp = 50)

def scene_day():
    set_all_lights_to(dimmer = 100, color_temp = 1)



def alter_light(light, status, dimmer = None, color = None, color_temp = None):
    #accepts either on or off status
    #to-do error handling
    message = json.loads(r.get("light@{}".format(light)))
    
    topic = message["callback"]
    payload ={"name": message["name"],"state": status}
    
    #setting optional variables
    if dimmer is not None:
        payload["dimmer"] = dimmer
    if color is not None:
        payload["color"] = color
    if color_temp is not None:
        payload["colorTemp"] = color_temp
    print("debug")
    #publishing to mqtt topic
    print("publishing to mqtt with topic {} and message {}".format(topic, json.dumps(payload)))
    client.publish(topic,json.dumps(payload))
    print("DEBUG mqtt done")


def toggle_lights(topic=None,message=None):
    
    #list of available lights:
    
    lights = json.loads(r.get("info/lights/tradfri").decode("utf-8"))
    print(lights)
    #figuring out states of the lights, if any is on, all should be turned
    #off and vice versa
    light_toggle = "on"
    for l in lights:
        state = check_light_status(l)
        print("state was: {}".format(state))
        if(state == "on" ):
            light_toggle = "off"
    
 
    #turning all lights on or off
    for l in lights:
        alter_light(light=l,status=light_toggle)



def switch_info_parser(topic, message):
    #expected message is formatted as: 
    # {"name": "esp8266_switch_001", "switch": "D4"}
    #to-do: add json schema verification for incoming messages
    message_dict = json.loads(message)
  
    #routes contain the function calls for corresponding devices and their switches
    routes = {
        "esp8266_switch_001":{
            "D1":toggle_lights,
            "D4":scene_evening
        }
    }
    #calling the right function from message content
    try:
        routes[message_dict["name"]][message_dict["switch"]]()
    except ValueError:
        print(ValueError)
               

def hello_world():
    print("hello world!")

#holds logics for states
functions={
    "olohuonecolor": hello_world,
    "cmd/switch1": toggle_lights,
    "info/light/tradfri": light_info_parser,
    "cmd/switch": switch_info_parser
    }


def on_message(client, userdata, message):
   
    #extract topic and payload from 
    topic = message.topic
    payload = str(message.payload.decode("utf-8"))
    print("new message from {} , {}".format(topic, payload))
    
    #cache latest value to redis 
    r.set(topic, payload)
    print(functions[topic].__name__)
    
    try:
        functions[topic](topic, payload)
    except ValueError:
        print(ValueError)   

def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    for topic in topic_subs:
        client.subscribe(topic)
        print("subscriped to: %s" % topic)

#redis connection
r = redis.Redis(host=host_ip, port=redis_port)
#paho mqtt connection
client = mqtt.Client()
client.connect(host_ip,mqtt_port,60)
#callback functions
client.on_connect = on_connect
client.on_message = on_message
#main loop
client.loop_forever()
