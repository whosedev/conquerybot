#!/bin/bash

# Funkcja do sprawdzania czy bot działa
check_bot() {
    if pgrep -f "python3 -m conquerybot.main" > /dev/null; then
        return 0
    else
        return 1
    fi
}

# Funkcja do uruchamiania bota
start_bot() {
    if check_bot; then
        echo "Bot już działa!"
    else
        cd ..
        nohup python3 -m conquerybot.main > bot.log 2>&1 &
        echo "Bot został uruchomiony!"
    fi
}

# Funkcja do zatrzymywania bota
stop_bot() {
    if check_bot; then
        pkill -f "python3 -m conquerybot.main"
        echo "Bot został zatrzymany!"
    else
        echo "Bot nie działa!"
    fi
}

# Funkcja do restartowania bota
restart_bot() {
    stop_bot
    sleep 2
    start_bot
}

# Funkcja do sprawdzania statusu
status_bot() {
    if check_bot; then
        echo "Bot działa!"
    else
        echo "Bot nie działa!"
    fi
}

# Obsługa komend
case "$1" in
    start)
        start_bot
        ;;
    stop)
        stop_bot
        ;;
    restart)
        restart_bot
        ;;
    status)
        status_bot
        ;;
    *)
        echo "Użycie: $0 {start|stop|restart|status}"
        exit 1
        ;;
esac

exit 0 