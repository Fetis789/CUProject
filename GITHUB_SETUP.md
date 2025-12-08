# Инструкция по подключению проекта к GitHub

## Шаг 1: Установка Git

Если Git не установлен на вашем компьютере:

1. Скачайте Git с официального сайта: https://git-scm.com/download/win
2. Установите Git, следуя инструкциям установщика
3. **ВАЖНО:** После установки **обязательно перезапустите терминал (или Cursor)**, чтобы обновился PATH

### Если Git не работает после установки:

Если после установки команда `git` не распознается, выполните в PowerShell:
```powershell
$env:Path += ";C:\Program Files\Git\bin"
```

Или просто **закройте и откройте терминал заново** - это должно решить проблему.

## Шаг 2: Настройка Git (первый раз)

Откройте терминал и выполните следующие команды (замените на свои данные):

```bash
git config --global user.name "Ваше Имя"
git config --global user.email "ваш.email@example.com"
```

## Шаг 3: Создание репозитория на GitHub

1. Войдите в свой аккаунт на GitHub (https://github.com)
2. Нажмите кнопку "+" в правом верхнем углу
3. Выберите "New repository"
4. Введите название репозитория
5. Выберите публичный (Public) или приватный (Private) репозиторий
6. **НЕ** ставьте галочки "Add a README file", "Add .gitignore", "Choose a license" (если проект уже существует)
7. Нажмите "Create repository"

## Шаг 4: Инициализация Git в вашем проекте

В терминале выполните следующие команды:

```bash
# Инициализация Git репозитория
git init

# Добавление всех файлов проекта
git add .

# Создание первого коммита
git commit -m "Initial commit"

# Добавление удаленного репозитория (замените YOUR_USERNAME и YOUR_REPO на свои)
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git

# Отправка кода на GitHub
git branch -M main
git push -u origin main
```

## Альтернативный способ (если репозиторий уже создан на GitHub)

Если вы уже создали репозиторий на GitHub с README, выполните:

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git pull origin main --allow-unrelated-histories
git push -u origin main
```

## Полезные команды Git

- `git status` - проверить статус изменений
- `git add .` - добавить все изменения
- `git commit -m "описание изменений"` - создать коммит
- `git push` - отправить изменения на GitHub
- `git pull` - получить изменения с GitHub

## Примечания

- Если GitHub запросит аутентификацию, используйте Personal Access Token вместо пароля
- Для создания токена: GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)


