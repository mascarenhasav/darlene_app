#!/bin/bash

cd /home/darlene/git/darlene_app

# pega hash atual

LOCAL=$(git rev-parse HEAD)

# atualiza info do remoto

git fetch origin

REMOTE=$(git rev-parse origin/main)

if [ "$LOCAL" != "$REMOTE" ]; then
echo "Atualizando código..."

```
git pull

echo "Reiniciando serviço..."
sudo systemctl restart darlene_app
```

else
echo "Sem mudanças"
fi
