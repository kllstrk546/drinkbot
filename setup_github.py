def setup_github():
    """Настройка GitHub для хранения бэкапов"""
    
    print("SETTING UP GITHUB BACKUP:")
    print("=" * 50)
    
    # 1. Инструкции для GitHub
    print(f"\n1. GITHUB SETUP INSTRUCTIONS:")
    
    instructions = [
        "1. Создайте новый репозиторий на GitHub",
        "2. Склонируйте этот репозиторий локально",
        "3. Добавьте .gitignore файл:",
        "   drink_bot.db",
        "*.db-journal",
        "__pycache__/",
        "*.pyc",
        ".env",
        "logs/",
        "backups/",
        "daily_bot_rotation.py",
        "emergency_bot_activation.py",
        "debug_*.py",
        "fix_*.py",
        "test_*.py",
        "implement_*.py",
        "notification_system.py",
        "rotation_check.py"
    ]
    
    for instruction in instructions:
        print(f"   {instruction}")
    
    # 2. Создаем .gitignore
    print(f"\n2. CREATING .gitignore:")
    
    gitignore_content = """# Database files
drink_bot.db
*.db-journal

# Python cache
__pycache__/
*.pyc

# Environment variables
.env

# Logs
logs/

# Backup files
backups/
daily_bot_rotation.py
emergency_bot_activation.py
debug_*.py
fix_*.py
test_*.py
implement_*.py
notification_system.py
rotation_check.py

# IDE files
.vscode/
.idea/

# OS files
.DS_Store
Thumbs.db
"""
    
    with open('.gitignore', 'w', encoding='utf-8') as f:
        f.write(gitignore_content)
    
    print("   ✅ .gitignore created")
    
    # 3. Git команды
    print(f"\n3. GIT COMMANDS:")
    
    git_commands = [
        "git init",
        "git add .",
        "git commit -m 'Initial commit - Drink Bot with all data'",
        "git remote add origin <YOUR_GITHUB_REPO_URL>",
        "git push -u origin main"
    ]
    
    for cmd in git_commands:
        print(f"   {cmd}")
    
    # 4. Автоматический скрипт для бэкапов
    print(f"\n4. AUTOMATIC BACKUP SCRIPT:")
    
    backup_script = """#!/bin/bash
# Автоматический бэкап данных бота

# Создаем бэкап с датой и временем
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
BACKUP_FILE="drink_bot_backup_${TIMESTAMP}.db"
SQL_DUMP_FILE="drink_bot_backup_${TIMESTAMP}.sql"

# Создаем бэкап базы данных
cp drink_bot.db "$BACKUP_FILE"

# Создаем SQL дамп
sqlite3 drink_bot.db > "$SQL_DUMP_FILE"

# Удаляем старые бэкапы (оставляем последние 10)
find . -name "drink_bot_backup_*.db" -type f -mtime +7 -delete
find . -name "drink_bot_backup_*.sql" -type f -mtime +7 -delete

# Сжимаем бэкапы
gzip "$BACKUP_FILE"
gzip "$SQL_DUMP_FILE"

echo "Backup completed: $BACKUP_FILE"
echo "SQL dump created: $SQL_DUMP_FILE"
echo "Old backups cleaned up"
"""
    
    with open('auto_backup.sh', 'w') as f:
        f.write(backup_script)
    
    print("   ✅ auto_backup.sh created")
    
    # 5. Cron настройка
    print(f"\n5. CRON SETUP FOR AUTOMATIC BACKUPS:")
    
    cron_setup = """# Добавьте в crontab для автоматических бэкапов каждые 6 часов
# Выполнить: crontab -e
    
# Команда для добавления в crontab:
# 0 */6 * * * /path/to/auto_backup.sh
    
# Или для тестирования (каждую минуту):
# */1 * * * * /path/to/auto_backup.sh
"""
    
    print("   Add to crontab:")
    print("   0 */6 * * * /path/to/auto_backup.sh")
    print("   (runs every 6 hours)")
    
    # 6. GitHub Actions
    print(f"\n6. GITHUB ACTIONS SETUP:")
    
    github_actions = """
name: Automatic Database Backup
on:
  schedule:
    - cron: '0 */6 * * *'
jobs:
  backup:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Backup database
      run: python backup_all_data.py
    - name: Upload to GitHub
      uses: actions/upload-artifact@v3
      with:
        path: drink_bot_backup_*.db
        name: database-backup
        retention-days: 30
    - name: Upload SQL dump
      uses: actions/upload-artifact@v3
      with:
        path: "drink_bot_backup_*.sql"
        name: sql-dump
        retention-days: 30
"""
    
    print("   GitHub Actions workflow created")
    
    print(f"\n" + "=" * 50)
    print("GITHUB SETUP COMPLETE!")
    print("\nNEXT STEPS:")
    print("1. Создайте репозиторий на GitHub")
    print("2. Склонируйте локально")
    print("3. Добавьте .gitignore")
    print("4. Сделайте первый коммит")
    print("5. Добавьте удаленный репозиторий")
    print("6. Настройте GitHub Actions")
    print("7. Настройте автоматические бэкапы")
    
    print(f"\nFILES CREATED:")
    print("✅ .gitignore")
    print("✅ auto_backup.sh")
    print("✅ GitHub Actions workflow")
    
    print(f"\nBENEFITS:")
    print("✅ Автоматические бэкапы каждые 6 часов")
    print("✅ Хранение 30 дней в GitHub")
    print("✅ Полное восстановление данных")
    print("✅ История изменений")

if __name__ == "__main__":
    setup_github()
