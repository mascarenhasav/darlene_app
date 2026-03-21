import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)

# 🔥 inicializa vários pinos de uma vez
def setup_doors(doors_config):
    for door in doors_config:
        GPIO.setup(door["pin"], GPIO.IN, pull_up_down=GPIO.PUD_UP)

# 🔥 lê todas as portas
def read_doors(doors_config):
    states = {}

    for door in doors_config:
        pin = door["pin"]
        name = door["name"]

        state = GPIO.input(pin)
        states[name] = state  # True = aberto, False = fechado

    return states
