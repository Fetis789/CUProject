# Скрипт для отправки кода на GitHub

# Добавляем Git в PATH (на случай, если нужно)
$env:Path += ";C:\Program Files\Git\bin"

# Проверяем статус
Write-Host "Проверка статуса репозитория..." -ForegroundColor Yellow
git status

# Добавляем все файлы
Write-Host "`nДобавление файлов..." -ForegroundColor Yellow
git add .

# Создаем коммит
Write-Host "`nСоздание коммита..." -ForegroundColor Yellow
git commit -m "Add project files"

# Отправляем на GitHub
Write-Host "`nОтправка на GitHub..." -ForegroundColor Yellow
git push origin main

Write-Host "`nГотово! Проверьте репозиторий на GitHub." -ForegroundColor Green





