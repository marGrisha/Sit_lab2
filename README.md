Структура базы данных
База данных нормализована до третьей нормальной формы (3НФ).

Основные таблицы:

country
location
volcano
eruption
impact

Связь 1:N:

country → location 
location → volcano 
volcano → eruption 

Связь 1:1:
eruption → impact

Установка и запуск
1. Установка зависимостей
pip install -r requirements.txt
