#!/usr/bin/env python3
"""
🟢 Скрипт для заполнения графика активности GitHub
Создаёт коммиты с датами в прошлом для красивого зелёного графика
"""

import os
import subprocess
from datetime import datetime, timedelta
import random

# ============ НАСТРОЙКИ ============
REPO_NAME = "my-contributions"  # Название папки/репозитория
DAYS_BACK = 365  # За сколько дней назад создавать коммиты
MIN_COMMITS_PER_DAY = 1  # Минимум коммитов в день
MAX_COMMITS_PER_DAY = 6  # Максимум коммитов в день
SKIP_CHANCE = 0.15  # Шанс пропустить день (для естественности)
# === EMAIL для GitHub ===
GIT_EMAIL = "bolgarshin@mail.ru"
GIT_NAME = "Vladimir"
# ===================================


def run_command(cmd):
    """Выполняет команду в терминале"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0 and "nothing to commit" not in result.stderr:
        print(f"⚠️  Ошибка: {result.stderr}")
    return result


def create_repo():
    """Создаём новый репозиторий"""
    original_dir = os.getcwd()

    if not os.path.exists(REPO_NAME):
        os.makedirs(REPO_NAME)
        print(f"📁 Создана папка: {REPO_NAME}")

    os.chdir(REPO_NAME)

    if not os.path.exists(".git"):
        run_command("git init")
        # Устанавливаем email и имя для этого репозитория
        run_command(f'git config user.email "{GIT_EMAIL}"')
        run_command(f'git config user.name "{GIT_NAME}"')
        print(f"🔧 Инициализирован git репозиторий с email: {GIT_EMAIL}")

    # Создаём README если его нет
    if not os.path.exists("README.md"):
        with open("README.md", "w") as f:
            f.write("# My Contributions\n\n")
            f.write("Personal learning and practice repository.\n")
        run_command("git add README.md")
        run_command('git commit -m "Initial commit"')
        print("📝 Создан README.md")

    return original_dir


def make_commit(date):
    """Создаём коммит с указанной датой"""
    # Добавляем строку в файл
    with open("log.txt", "a") as f:
        f.write(f"{date.isoformat()}\n")

    date_str = date.strftime("%Y-%m-%dT%H:%M:%S")

    run_command("git add .")

    # Устанавливаем дату коммита через переменные окружения
    env_vars = f'GIT_AUTHOR_DATE="{date_str}" GIT_COMMITTER_DATE="{date_str}"'
    run_command(f'{env_vars} git commit -m "Update {date.strftime("%Y-%m-%d")}"')


def main():
    print("🟢 GitHub Contribution Graph Generator")
    print("=" * 40)

    original_dir = create_repo()

    today = datetime.now()
    total_commits = 0

    print(f"\n⏳ Создаю коммиты за последние {DAYS_BACK} дней...")
    print("   Это может занять несколько минут...\n")

    for day in range(DAYS_BACK, 0, -1):
        date = today - timedelta(days=day)

        # Случайно пропускаем некоторые дни (для естественности)
        if random.random() < SKIP_CHANCE:
            continue

        # Случайное количество коммитов в день
        num_commits = random.randint(MIN_COMMITS_PER_DAY, MAX_COMMITS_PER_DAY)

        for i in range(num_commits):
            # Добавляем случайное время (рабочие часы)
            commit_date = date.replace(
                hour=random.randint(9, 23),
                minute=random.randint(0, 59),
                second=random.randint(0, 59),
            )
            make_commit(commit_date)
            total_commits += 1

        # Прогресс каждые 30 дней
        if day % 30 == 0:
            print(
                f"   📅 Обработано: {DAYS_BACK - day}/{DAYS_BACK} дней ({total_commits} коммитов)"
            )

    os.chdir(original_dir)

    print("\n" + "=" * 40)
    print(f"✅ Готово! Создано {total_commits} коммитов")
    print(f"📁 Репозиторий: ./{REPO_NAME}")
    print("\n📤 Теперь выполните следующие команды:")
    print("-" * 40)
    print(f"cd {REPO_NAME}")
    print("git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git")
    print("git branch -M main")
    print("git push -u origin main")
    print("-" * 40)
    print("\n⚠️  Не забудьте:")
    print("   1. Создать ПУСТОЙ репозиторий на GitHub")
    print("   2. Репозиторий должен быть ПУБЛИЧНЫМ")
    print("   3. Email в git config должен совпадать с GitHub")
    print("\n🎉 После пуша график станет зелёным!")


if __name__ == "__main__":
    main()
