#!/bin/bash

# Проверка аргументов
if [ -z "$1" ]; then
  echo "❌ Укажи имя образа (например: my-app:latest)"
  echo "Пример: ./k3s-docker-build.sh my-app:latest"
  exit 1
fi

IMAGE_NAME="$1"
TAR_NAME="${IMAGE_NAME//[:\/]/_}.tar"  # заменяет / и : чтобы имя файла было корректным

echo "📦 Билдим Docker-образ: $IMAGE_NAME"
docker build -t "$IMAGE_NAME" .

if [ $? -ne 0 ]; then
  echo "❌ Ошибка сборки"
  exit 1
fi

echo "📂 Сохраняем в файл: $TAR_NAME"
docker save "$IMAGE_NAME" -o "$TAR_NAME"

if [ $? -ne 0 ]; then
  echo "❌ Ошибка сохранения"
  exit 1
fi

echo "📥 Импорт в k3s через containerd"
sudo k3s ctr images import "$TAR_NAME"

if [ $? -ne 0 ]; then
  echo "❌ Ошибка импорта"
  exit 1
fi

echo "✅ Готово! Образ '$IMAGE_NAME' доступен внутри k3s"
