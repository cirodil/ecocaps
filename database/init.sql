-- Создание расширений если нужно
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Таблицы будут созданы автоматически FastAPI при первом запуске
-- Этот файл можно использовать для добавления начальных данных

-- Пример добавления тестового пользователя (опционально)
INSERT INTO users (full_name, class_name, pin_code) VALUES 
('Тестовый Ученик', '10А', '1234')
ON CONFLICT (pin_code) DO NOTHING;