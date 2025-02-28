from machine import Pin, ADC
import time
import network
from umqtt.simple import MQTTClient
import json 

# Configuración del sensor MQ-135
mq135_pin = 34 
adc = ADC(Pin(mq135_pin))
adc.atten(ADC.ATTN_11DB)  

# Configuración WiFi
SSID = "Redmi Note 12R"  
PASSWORD = "1234567812"  

# Configuración MQTT
MQTT_BROKER = "broker.hivemq.com"  
MQTT_USER = ""  
MQTT_PASSWORD = ""  
MQTT_CLIENT_ID = "ESP32_MQ135"  
MQTT_TOPIC = "utng/arg/mq135"  
MQTT_PORT = 1883  


# Conectar a WiFi
def conectar_wifi():
    print("Conectando a WiFi...")
    sta_if = network.WLAN(network.STA_IF)
    sta_if.active(True)
    sta_if.connect(SSID, PASSWORD)

    timeout = 20  
    while not sta_if.isconnected() and timeout > 0:
        print(".", end="")
        time.sleep(0.3)
        timeout -= 1

    if sta_if.isconnected():
        print("\nWiFi Conectada!", sta_if.ifconfig())
    else:
        print("\nError: No se pudo conectar a WiFi")
        return False

    return True

# Función para conectar a MQTT
def conectar_mqtt():
    try:
        client = MQTTClient(MQTT_CLIENT_ID, MQTT_BROKER, port=MQTT_PORT, user=MQTT_USER, password=MQTT_PASSWORD, keepalive=60) #keepalive=60 is better than keepalive =0
        client.connect()
        print("Conectado al broker MQTT:", MQTT_BROKER)
        return client
    except Exception as e:
        print("Error al conectar a MQTT:", e)
        return None

# Leer datos del sensor MQ-135
def leer_mq135():
    valor = adc.read() 
    voltaje = valor * (3.3 / 4095)  
    
 
    ppm = max(0, (voltaje - 0.1) * 1000)
    print(f"Valor ADC: {valor}, Voltaje: {voltaje:.2f}V,  PPM (estimado, SIN CALIBRAR): {ppm:.2f}")  
    return ppm

# Publicar datos a MQTT (usando JSON)
def publicar_datos(client, ppm):
    try:
        if client:
            data = {
                "ppm": ppm,
                "timestamp": time.time()  
            }

            payload = json.dumps(data)

            client.publish(MQTT_TOPIC, payload)
            print(f"Datos publicados (JSON): {payload}")  

        else:
            print("Error: Cliente MQTT no disponible")
    except Exception as e:
        print("Error al publicar datos:", e)

# Programa principal
if conectar_wifi():
    client = conectar_mqtt()
    if client:
        while True:
            calidad_aire = leer_mq135()
            publicar_datos(client, calidad_aire)
            time.sleep(15)  
    else:
        print("No se pudo iniciar MQTT, revisa la conexión.")
else:
    print("No se pudo conectar a WiFi. Verifica las credenciales o el alcance de la señal.")