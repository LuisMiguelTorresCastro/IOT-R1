from machine import Pin, ADC
import time
import network
from umqtt.simple import MQTTClient

# Configuración del sensor MQ-135
mq135_pin = 34  # Pin analógico del ESP32
adc = ADC(Pin(mq135_pin))
adc.atten(ADC.ATTN_11DB)  # Rango de 0 a 3.3V

# Configuración WiFi
SSID = "UTNG_GUEST"
PASSWORD = "Tu_PASSWORD"

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
    while not sta_if.isconnected():
        print(".", end="")
        time.sleep(0.3)
    print("\nWiFi Conectada!", sta_if.ifconfig())

# Función para conectar a MQTT
def conectar_mqtt():
    client = MQTTClient(MQTT_CLIENT_ID, MQTT_BROKER, port=MQTT_PORT, user=MQTT_USER, password=MQTT_PASSWORD, keepalive=0)
    client.connect()
    print("Conectado al broker MQTT")
    return client

# Leer datos del sensor MQ-135
def leer_mq135():
    valor = adc.read()  # Valor analógico entre 0 y 4095
    voltaje = valor * (3.3 / 4095)  # Convertir a voltaje
    ppm = (voltaje - 0.1) * 1000  # Conversión simple a ppm
    return ppm

# Publicar datos a MQTT
def publicar_datos(client, ppm):
    try:
        client.publish(MQTT_TOPIC, str(ppm))
        print(f"Datos publicados: {ppm} ppm")
    except Exception as e:
        print("Error al publicar datos:", e)

# Programa principal
conectar_wifi()
client = conectar_mqtt()
while True:
    calidad_aire = leer_mq135()
    print(f"Calidad del aire: {calidad_aire} ppm")
    publicar_datos(client, calidad_aire)
    time.sleep(15)  # Esperar 15 segundos antes de la próxima lectura
