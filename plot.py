import pandas as pd
import matplotlib.pyplot as plt

# carregar dados
df = pd.read_csv("sensors_log.csv")

# converter timestamp
df["timestamp"] = pd.to_datetime(df["timestamp"])

# escolher o que plotar
plt.figure()

plt.plot(df["timestamp"], df["bateria1"], label="Bateria 1")
plt.plot(df["timestamp"], df["bateria2"], label="Bateria 2")

plt.xlabel("Tempo")
plt.ylabel("Voltagem")
plt.legend()

plt.xticks(rotation=45)
plt.tight_layout()

plt.show()
