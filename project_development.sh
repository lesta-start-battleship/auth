#!/bin/bash

# Функция для выполнения команд с выводом в консоль
execute_command() {
    echo "Выполнение: $1"
    eval "$1"
    if [ $? -ne 0 ]; then
        echo "Ошибка выполнения команды: $1"
        exit 1
    fi
}
# Делаем файлы исполняемыми
execute_command "chmod +x k3s-docker-build.sh"

# Сборка Docker-образа
execute_command "./k3s-docker-build.sh auth-service:latest"

# Применение секретов
execute_command "sudo kubectl apply -f secret_kuber.yaml"

# Применение конфигурации
execute_command "sudo kubectl apply -f config_kuber.yaml"

# Применение деплоймента
execute_command "sudo kubectl apply -f ./auth-deployment.yaml"

# Установка cert-manager
execute_command "sudo kubectl apply -f https://github.com/cert-manager/cert-manager/releases/latest/download/cert-manager.yaml"

# Применение Let's Encrypt конфигурации
execute_command "sudo kubectl apply -f ./letsencrypt.yaml"

# Применение ингресса
execute_command "sudo kubectl apply -f ./ingress.yaml"

echo "Все команды выполнены успешно."