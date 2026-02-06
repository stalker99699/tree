import os
import argparse

def restore_project(input_file):
    if not os.path.isfile(input_file):
        print("Ошибка: файл не существует")
        return
    
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Извлекаем имя проекта
    lines = content.split('\n')
    project_name = lines[0].replace("Имя проекта: ", "").strip()
    
    # Находим начало содержимого файлов
    try:
        files_start = content.index("Путь к файлу: ")
    except ValueError:
        print("Ошибка: неверный формат файла")
        return
    
    # Разделяем на блоки файлов
    file_blocks = content[files_start:].split("\n\n---\n\n")
    
    # Создаем директорию проекта
    project_dir = os.path.join(os.getcwd(), project_name)
    os.makedirs(project_dir, exist_ok=True)
    
    for block in file_blocks:
        if not block.strip():
            continue
            
        lines = block.split('\n')
        if len(lines) < 4:
            continue
            
        # Извлекаем информацию о файле
        file_path = lines[0].replace("Путь к файлу: ", "").strip()
        file_name = lines[1].replace("Имя файла: ", "").strip()
        content_start = 3  # После "Содержимое:"
        
        # Получаем полный путь к файлу
        full_path = os.path.join(project_dir, file_path)
        
        # Создаем директории если нужно
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        # Записываем содержимое файла
        file_content = '\n'.join(lines[content_start:])
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(file_content)
    
    print(f"Проект '{project_name}' успешно восстановлен в директории: {project_dir}")

def main():
    parser = argparse.ArgumentParser(description='Восстанавливает проект из файла')
    parser.add_argument('input_file', help='Путь к файлу проекта')
    args = parser.parse_args()
    
    restore_project(args.input_file)

if __name__ == "__main__":
    main()
