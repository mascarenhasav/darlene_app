#!/bin/bash

cd /home/darlene/git/darlene_app

LOG_FILE="/home/darlene/git/darlene_app/control.ilog"

echo "---- $(date) ----" >> $LOG_FILE

git pull > /dev/null 2>&1 || exit 0

ACTION=$(jq -r '.action' control.json)

echo "Ação recebida: $ACTION" >> $LOG_FILE

case $ACTION in
restart)
echo "Reiniciando app" >> $LOG_FILE
sudo systemctl restart darlene_app
;;

stop)
    echo "Parando app" >> $LOG_FILE
    sudo systemctl stop darlene_app
    ;;

start)
    echo "Iniciando app" >> $LOG_FILE
    sudo systemctl start darlene_app
    ;;

reboot)
    echo "Reiniciando Raspberry" >> $LOG_FILE
    sudo reboot
    ;;

deploy)
    echo "Deploy manual acionado" >> $LOG_FILE
    sudo systemctl restart darlene_app
    ;;

*)
    echo "Nenhuma ação válida" >> $LOG_FILE
    exit 0
    ;;

esac

# Resetar ação

echo '{ "action": "none" }' > control.json

# Atualizar status no control.json

jq '.last_action = "'$ACTION'" | .last_run = "ok" | .last_update = "'$(date)'"' control.json > tmp.json && mv tmp.json control.json
echo "$ACTION executado com sucesso" >> $LOG_FILE

# Commit automático (opcional)

git add control.json
git commit -m "status update" > /dev/null 2>&1
git push > /dev/null 2>&1
