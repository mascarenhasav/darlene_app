import random

def read_all():
    return {
        "battery": round(random.uniform(11.5, 13.8), 2),
        "water": random.randint(0, 100),
        "temp": random.randint(20, 40),
        "solar": random.randint(0, 500),
        "consumption": random.randint(0, 300),
        "inverter": random.choice(["ON", "OFF"]),
        "door": random.choice(["ABERTO", "FECHADO"]),
        "window": random.choice(["ABERTA", "FECHADA"]),
        "pump": random.choice(["ON", "OFF"])
    }
