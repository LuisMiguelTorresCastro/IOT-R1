from machine import Pin, time_pulse_us, PWM
import time

# Configuración del sensor HC-SR04
TRIG = Pin(12, Pin.OUT)  
ECHO = Pin(13, Pin.IN)  

# Configuración de los pines del LED RGB (PWM)
led_red = PWM(Pin(14), freq=1000)   
led_green = PWM(Pin(26), freq=1000)  
led_blue = PWM(Pin(25), freq=1000)   

def medir_distancia():
    TRIG.off()
    time.sleep_us(5)
    TRIG.on()
    time.sleep_us(10)
    TRIG.off()
    
    tiempo = time_pulse_us(ECHO, 1, 30000)  # Espera la señal de eco
    if tiempo < 0:
        return -1 
    
    distancia = (tiempo / 2) / 29.1  # Convertir a cm
    return distancia

def set_color(r, g, b):
    led_red.duty(int(r * 1023 / 255))
    led_green.duty(int(g * 1023 / 255))
    led_blue.duty(int(b * 1023 / 255))

while True:
    dist = medir_distancia()
    if dist != -1:
        print("Distancia:", dist, "cm")
        
        if dist < 10:
            set_color(255, 0, 0)  # Rojo
        elif 10 <= dist < 30:
            set_color(255, 255, 0)  # Amarillo
        else:
            set_color(0, 255, 0)  # Verde
    else:
        set_color(0, 0, 255)  # Azul (error en la medición)
    
    time.sleep(0.5)
