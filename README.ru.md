<p align="center">
  <a href="README.md">English</a> · <strong>Русский</strong>
</p>

<p align="center">
  <h1 align="center">Pi Delegate</h1>
</p>

<p align="center">
  <a href="https://github.com/letya999/pi-delegate"><img src="https://img.shields.io/badge/статус-активен-brightgreen" alt="статус"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/лицензия-MIT-blue" alt="Лицензия: MIT"></a>
  <a href="https://skills.sh/letya999/pi-delegate"><img src="https://skills.sh/b/letya999/pi-delegate" alt="skills.sh"></a>
  <img src="https://img.shields.io/badge/python-3.10+-blue.svg" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/cli-pi%20%7C%20omp-purple" alt="CLI: pi | omp">
</p>

Скилл-делегат для неинтерактивного запуска Pi Coding Agent и Oh My Pi (OMP) от [Артема Летюшева](https://github.com/letya999).

Основная команда — `scripts/delegate_pi.py`. Главный потребитель — управляющий агент или оркестратор: каждый запуск выполняет Pi или OMP в ограниченном подпроцессе и возвращает структурированный JSON-конверт.

---

## Одна цель, изолированный подпроцесс, нулевое доверие

Скрипт-обёртка служит детерминированным барьером безопасности между управляющим агентом и CLI Pi/OMP:

- **Поддержка двух рантаймов:** Бесшовная делегация в нативный Pi (`--runtime pi`) или Oh My Pi (`--runtime omp`).
- **Строго неинтерактивный запуск:** Вызывает CLI напрямую через `subprocess.run(..., shell=False)` без диалогового перехвата.
- **Гибкий контроль инструментов:** Поддерживает явные списки разрешённых инструментов (`--tools read,grep,find,ls,write`) или полное отключение вызова инструментов (`--no-tools`).
- **Верификация результатов:** Ответ считается непроверенным до независимой инспекции через diff и тесты.
- **Изоляция секретов:** Никогда не копирует и не логирует токены аутентификации между домашними профилями и изолированными стендами.

## Матрица возможностей

| Параметр / Возможность | Спецификация | Поведение и гарантии |
|---|---|---|
| **Рантаймы** | `--runtime pi` или `--runtime omp` | Единый интерфейс для Pi Coding Agent и Oh My Pi |
| **Команда запуска** | `pi -p "<task>"` / `omp -p "<task>"` | Неинтерактивное выполнение в режиме print |
| **Ограничение каталога** | Subprocess cwd (Pi) / `--cwd <cwd>` (OMP) | Ограничивает область действия целевой папкой проекта |
| **Ограничение тулов** | `--tools <list>` или `--no-tools` | Контролирует набор инструментов, доступных агенту |
| **Расширения и скиллы** | `--extension`, `--skill`, `--prompt-template` | Передаёт внешние ресурсы напрямую в контекст |
| **Профили OMP** | `--profile <name>` | Выбирает профиль Oh My Pi (только для рантайма OMP) |
| **Изолированный профиль** | `--agent-dir <path>` | Устанавливает `PI_CODING_AGENT_DIR` без копирования ключей |
| **Автономные правки** | `--auto-approve` | Передаёт `--approve` (Pi) или `--auto-approve` (OMP) |
| **Переопределение бинарника** | Переменные `PI_BIN` / `OMP_BIN` | Приоритетный путь до вызова из PATH или Bun |
| **Коды возврата** | `0, 2, 65, 124, 126, 127` | Стандартизированная маршрутизация ошибок |

## Установка

Через `npx skills`:

```bash
npx skills add letya999/pi-delegate
```

Или клонированием в каталог скиллов:

```bash
git clone https://github.com/letya999/pi-delegate.git .agents/skills/pi-delegate
```

## Быстрый старт

### POSIX (macOS, Linux, WSL)

```bash
python3 scripts/delegate_pi.py \
  --runtime pi \
  --cwd "$PWD" \
  --task "Проанализируй репозиторий и выдели самую критичную проблему." \
  --timeout 45m
```

### Windows PowerShell

```powershell
py -3 .\scripts\delegate_pi.py `
  --runtime pi `
  --cwd (Get-Location).Path `
  --task "Проанализируй репозиторий и выдели самую критичную проблему." `
  --timeout 45m
```

---

<details>
<summary>Схема JSON-манифеста и интеграция с агентом</summary>

Обёртка записывает `stdout.txt`, `stderr.log` и `result.json` во временный каталог:

```json
{
  "tool": "pi",
  "cwd": "C:\\work\\repo",
  "exit_code": 0,
  "timed_out": false,
  "response": "Финальный извлеченный текст ответа от Pi/OMP",
  "output_dir": "C:\\Temp\\pi-delegate-xyz",
  "stdout": "C:\\Temp\\pi-delegate-xyz\\stdout.txt",
  "stderr": "C:\\Temp\\pi-delegate-xyz\\stderr.log"
}
```

Если выполнение завершилось с кодом 0, но не вернуло ответ, обёртка завершается с кодом `65`.

</details>

<details>
<summary>Флаги CLI и параметры запуска</summary>

| Флаг | Тип | Описание |
|---|---|---|
| `--runtime` | `pi` или `omp` (по умолчанию: `omp`) | Целевой рантайм для запуска. |
| `--cwd` | Путь (обязательный) | Рабочий каталог проекта. Код `2`, если каталог не существует. |
| `--task` | Строка (обязательный) | Текст задачи / поручения для Pi/OMP. |
| `--timeout` | Время (по умолчанию: `45m`) | Таймаут: `90s`, `45m`, `2h` или число секунд. |
| `--model` | Строка | Переопределение модели. |
| `--profile` | Строка | Имя профиля OMP (только для OMP). |
| `--agent-dir` | Путь | Каталог конфигурации Pi (`PI_CODING_AGENT_DIR`). |
| `--tools` | Строка | Список разрешенных инструментов (`read,grep,find,ls,write`). |
| `--no-tools` | Флаг | Отключает вызов любых инструментов. |
| `--extension` | Путь | Путь к расширению Pi. |
| `--skill` | Путь | Путь к скиллу Pi. |
| `--prompt-template` | Путь | Путь к шаблону промпта Pi. |
| `--auto-approve` | Флаг | Автоматическое одобрение инструментов. |
| `--output-dir` | Путь | Каталог для сохранения логов и манифеста. |

</details>

<details>
<summary>Правила безопасности и изоляция секретов</summary>

- **Защита секретов:** Никогда не считывает, не печатает и не копирует токены OAuth и API-ключи.
- **Явные ограничения инструментов:** Позволяет ограничить тулы только чтением, когда запись запрещена.
- **Защита от циклов:** Делегированный агент не должен запускать новые подпроцессы через обёртки.

</details>

<details>
<summary>Протокол независимой верификации</summary>

Ответы делегата не считаются окончательным доказательством. При изменении файлов:

1. Проверьте diff: `git diff --stat` и `git diff`.
2. Запустите тесты независимо: `pytest`, `npm test`, `cargo test`.
3. Проверьте добавленные файлы и импорты.

</details>

<details>
<summary>Набор тестов</summary>

Запуск тестов через стандартную библиотеку `unittest`:

```bash
python -m unittest discover -s tests -v
```

</details>

<details>
<summary>Точки входа скилла</summary>

- [SKILL.md](SKILL.md) — Спецификация инструкций для кодинг-агентов.
- [QUICKSTART.md](QUICKSTART.md) — Краткое руководство.
- [references/runtime-setup.md](references/runtime-setup.md) — Проверка окружения перед запуском.
- [references/headless-reference.md](references/headless-reference.md) — Справочник флагов Pi/OMP CLI.
- [.well-known/agent-skills/index.json](.well-known/agent-skills/index.json) — Индекс для каталога skills.sh.
- [dist/pi-delegate.zip](dist/pi-delegate.zip) — Архив скилла.

</details>

<details>
<summary>Лицензия</summary>

MIT License. См. полный текст в [LICENSE](LICENSE). Copyright (c) 2026 Artem Letyushev.

</details>
