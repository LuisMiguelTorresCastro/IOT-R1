from machine import Pin, ADC
import time
import network
from umqtt.simple import MQTTClient
import json
import gc
import ubinascii  # Para generar un ID de cliente único
import ntptime  # Para sincronizar la hora

# Configuración del sensor MQ-135
mq135_pin = 34
adc = ADC(Pin(mq135_pin))
adc.atten(ADC.ATTN_11DB)

# Configuración WiFi
SSID = "UTNG_GUEST"  # Tu SSID
PASSWORD = "R3d1nv1t4d0s#UT"  # Tu contraseña

# Configuración MQTT (Broker Público)
MQTT_BROKER = "broker.emqx.io"
MQTT_USER = "torresluis"  # Tu usuario
MQTT_PASSWORD = "Luis0207@"  # Tu contraseña
# Generar un ID de cliente único a partir de la dirección MAC
MQTT_CLIENT_ID = ubinascii.hexlify(network.WLAN().config('mac')).decode()
MQTT_TOPIC = "salida/01"
MQTT_PORT = 1883  # Corregido: Volver al puerto 1883


def conectar_wifi():
    print("Conectando a WiFi...")
    sta_if = network.WLAN(network.STA_IF)
    sta_if.active(True)
    sta_if.connect(SSID, PASSWORD)
    while not sta_if.isconnected():
        print(".", end="")
        time.sleep(0.3)
    print("\nWiFi Conectada!", sta_if.ifconfig())
    return sta_if

def conectar_mqtt():
    client = MQTTClient(MQTT_CLIENT_ID, MQTT_BROKER, port=MQTT_PORT, user=MQTT_USER, password=MQTT_PASSWORD, keepalive=300)  # Keepalive más largo
    try:
        client.connect()
        print("Conectado al broker MQTT:", MQTT_BROKER)
        return client
    except Exception as e:
        print("Error al conectar al broker MQTT:", e)
        return None

def leer_mq135():
    valor = adc.read()
    voltaje = valor * (3.3 / 4095)
    # ¡CALIBRACIÓN NECESARIA!
    ppm = max(0, (voltaje - 0.1) * 1000)
    print(f"Valor ADC: {valor}, Voltaje: {voltaje:.2f}V, PPM (estimado, SIN CALIBRAR): {ppm:.2f}")
    return ppm, voltaje

def obtener_timestamp_utc():
    """Obtiene el timestamp actual en formato ISO 8601 (UTC)."""
    try:
        # Sincronizar la hora con un servidor NTP.  ¡MUY IMPORTANTE!
        ntptime.settime()
        # Obtener la hora actual como una tupla.
        year, month, day, hour, minute, second, weekday, yearday = time.localtime()
        # Formatear la fecha y hora como una cadena ISO 8601.
        timestamp_str = "{:04d}-{:02d}-{:02d}T{:02d}:{:02d}:{:02d}Z".format(year, month, day, hour, minute, second)
        return timestamp_str
    except Exception as e:
        print("Error al obtener la hora NTP:", e)
        # En caso de error, usar time.time() como respaldo, pero será menos preciso.
         # Obtener la hora actual como una tupla.
        year, month, day, hour, minute, second, weekday, yearday = time.localtime()
        # Formatear la fecha y hora como una cadena ISO 8601.
        timestamp_str = "{:04d}-{:02d}-{:02d}T{:02d}:{:02d}:{:02d}Z".format(year, month, day, hour, minute, second)
        return timestamp_str


def publicar_datos(client, ppm, deviceName="unknown_device", sensorName="unknown_sensor"):
    if client is None:
        print("No se puede publicar: cliente MQTT no conectado.")
        return
    try:
        timestamp = obtener_timestamp_utc()  # Obtener el timestamp como cadena ISO 8601
        data = {
            "ppm": ppm,
            "deviceName": deviceName,
            "sensor": sensorName,
            "timestamps": timestamp  # Usar el timestamp formateado
        }
        payload = json.dumps(data).encode('utf-8')
        client.publish(MQTT_TOPIC, payload)
        print(f"Datos publicados: {payload}")
    except Exception as e:
        print("Error al publicar datos:", e)

def reconnect_mqtt(client, sta_if):
    try:
        if client:
            client.disconnect()
    except:
        pass

    if not sta_if.isconnected():
        print("Reconectando a WiFi...")
        sta_if.connect(SSID, PASSWORD)
        while not sta_if.isconnected():
            print(".", end="")
            time.sleep(0.3)
        print("\nWiFi Reconectada!", sta_if.ifconfig())

    time.sleep(5)

    try:
        new_client = conectar_mqtt()
        return new_client
    except Exception as e:
        print("Error al reconectar al broker MQTT:", e)
        return None

# --- Programa Principal ---

sta_if = conectar_wifi()
client = conectar_mqtt()

if client is None:
    print("No se pudo conectar inicialmente al broker MQTT. Saliendo.")
    #exit() # Removido: exit() no es una función incorporada en MicroPython
    raise SystemExit  # Usar SystemExit en su lugar


while True:
    try:
        client.ping()  # ¡Llamar a ping() PRIMERO!
        print("MQTT Ping OK")
    except Exception as e:
        print("MQTT Connection Lost", e)
        client = reconnect_mqtt(client, sta_if)
        if client is None:
            print("Fallo la reconexión MQTT. Saliendo.")
            break

    ppm, voltaje = leer_mq135()
    publicar_datos(client, ppm, "ESP32_1", "MQ135")  # Usar nombres descriptivos
    time.sleep(15)
    gc.collect()