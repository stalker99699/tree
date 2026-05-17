#!/usr/bin/env python3
import os
import argparse
import base64

# Расширения бинарных файлов
BINARY_EXTENSIONS = {
    # Двоичные файлы
    '.exe', '.dll', '.so',
    # Изображения
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.ico', '.webp', '.svg',
    # Архивы
    '.zip', '.tar', '.rar', '.7z', '.gz', '.bz2', '.xz',
    # Документы
    '.pdf', '.docx', '.xlsx', '.pptx', '.odt', '.ods',
    # Медиа
    '.mp3', '.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flac', '.wav', '.ogg',
}

def is_binary_file(filepath):
    """Проверяет, является ли файл бинарным по расширению или содержимому."""
    ext = os.path.splitext(filepath)[1].lower()
    if ext in BINARY_EXTENSIONS:
        return True
    
    # Проверяем первые байты файла на наличие бинарных данных
    try:
        with open(filepath, 'rb') as f:
            chunk = f.read(1024)
            # Если есть нулевые байты, это бинарный файл
            if b'\x00' in chunk:
                return True
            # Проверяем соотношение печатных символов
            text_chars = bytearray({7, 8, 9, 10, 12, 13, 27} | set(range(0x20, 0x100)) - {0x7f})
            non_text = sum(1 for byte in chunk if byte not in text_chars)
            if len(chunk) > 0 and non_text / len(chunk) > 0.3:
                return True
    except Exception:
        pass
    
    return False

def generate_tree(directory, indent='', exclude=None):
    """Генерирует дерево директорий."""
    if exclude is None:
        exclude = set()
    
    try:
        items = os.listdir(directory)
    except PermissionError:
        return []
    
    items = [item for item in items if item not in exclude]
    items.sort()
    
    files = []
    dirs = []
    for item in items:
        path = os.path.join(directory, item)
        if os.path.isfile(path):
            files.append(item)
        else:
            dirs.append(item)
    
    output = []
    for i, item in enumerate(files):
        if i == len(files) - 1 and not dirs:
            output.append(f"{indent}└── {item}")
        else:
            output.append(f"{indent}├── {item}")
    
    for i, item in enumerate(dirs):
        path = os.path.join(directory, item)
        if i == len(dirs) - 1:
            output.append(f"{indent}└── {item}/")
            new_indent = indent + '    '
        else:
            output.append(f"{indent}├── {item}/")
            new_indent = indent + '│   '
        subtree = generate_tree(path, new_indent, exclude)
        output.extend(subtree)
    
    return output

def encode_file(filepath):
    """Кодирует файл в base64 строку."""
    try:
        with open(filepath, 'rb') as f:
            content = f.read()
        encoded = base64.b64encode(content).decode('ascii')
        return encoded, True
    except Exception as e:
        print(f"Ошибка при чтении файла {filepath}: {e}")
        return None, False

def decode_file(encoded_content):
    """Декодирует base64 строку обратно в байты."""
    try:
        decoded = base64.b64decode(encoded_content)
        return decoded, True
    except Exception as e:
        print(f"Ошибка при декодировании: {e}")
        return None, False

def pack_project(project_path, output_filename=None):
    """Упаковывает проект в один файл."""
    project_path = os.path.abspath(project_path)
    
    if not os.path.isdir(project_path):
        print("Ошибка: путь не существует или не является директорией")
        return False
    
    project_name = os.path.basename(project_path)
    if output_filename is None:
        output_filename = f"{project_name}.txt"
    
    output_filepath = os.path.join(os.getcwd(), output_filename)
    exclude = {output_filename}
    
    try:
        tree_lines = generate_tree(project_path, indent='', exclude=exclude)
    except Exception as e:
        print(f"Ошибка при генерации дерева файлов: {e}")
        return False
    
    tree_str = f"{project_name}/\n" + '\n'.join(tree_lines)
    file_contents = []
    
    for dirpath, dirnames, filenames in os.walk(project_path):
        if output_filename in filenames:
            filenames.remove(output_filename)
        dirnames[:] = [d for d in dirnames if d not in exclude]
        
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            relative_path = os.path.relpath(file_path, project_path)
            
            # Определяем тип файла
            is_binary = is_binary_file(file_path)
            
            if is_binary:
                # Кодируем бинарный файл в base64
                encoded, success = encode_file(file_path)
                if not success:
                    continue
                file_contents.append({
                    'path': relative_path,
                    'name': filename,
                    'content': encoded,
                    'is_binary': True
                })
            else:
                # Пробуем прочитать как текст с разными кодировками
                content = None
                encodings = ['utf-8', 'cp1251', 'latin-1', 'koi8-r', 'iso-8859-1']
                
                for encoding in encodings:
                    try:
                        with open(file_path, 'r', encoding=encoding) as f:
                            content = f.read()
                        break
                    except (UnicodeDecodeError, UnicodeError):
                        continue
                    except Exception as e:
                        print(f"Ошибка при чтении файла {file_path}: {e}")
                        break
                
                if content is None:
                    # Если не удалось прочитать ни в одной кодировке, используем base64
                    encoded, success = encode_file(file_path)
                    if success:
                        file_contents.append({
                            'path': relative_path,
                            'name': filename,
                            'content': encoded,
                            'is_binary': True
                        })
                    continue
                
                file_contents.append({
                    'path': relative_path,
                    'name': filename,
                    'content': content,
                    'is_binary': False
                })
    
    # Записываем результат
    try:
        with open(output_filepath, 'w', encoding='utf-8') as f:
            f.write(f"Имя проекта: {project_name}\n\n")
            f.write("Древо файлов проекта:\n")
            f.write(tree_str)
            f.write("\n\n")
            
            for file_info in file_contents:
                f.write(f"Путь к файлу: {file_info['path']}\n")
                f.write(f"Имя файла: {file_info['name']}\n")
                f.write(f"Тип: {'binary' if file_info['is_binary'] else 'text'}\n")
                f.write("Содержимое (base64):\n" if file_info['is_binary'] else "Содержимое:\n")
                f.write(file_info['content'])
                f.write("\n\n---\n\n")
        
        print(f"Проект успешно упакован в файл: {output_filepath}")
        print(f"Всего файлов: {len(file_contents)}")
        binary_count = sum(1 for f in file_contents if f['is_binary'])
        if binary_count > 0:
            print(f"Бинарных файлов: {binary_count}")
        return True
        
    except Exception as e:
        print(f"Ошибка при записи файла: {e}")
        return False

def unpack_project(input_file):
    """Распаковывает проект из файла."""
    if not os.path.isfile(input_file):
        print("Ошибка: файл не существует")
        return False
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Ошибка при чтении файла: {e}")
        return False
    
    # Извлекаем имя проекта
    lines = content.split('\n')
    project_name = None
    for line in lines:
        if line.startswith("Имя проекта:"):
            project_name = line.replace("Имя проекта:", "").strip()
            break
    
    if not project_name:
        print("Ошибка: неверный формат файла (не найдено имя проекта)")
        return False
    
    # Находим начало содержимого файлов
    try:
        files_start = content.index("Путь к файлу:")
    except ValueError:
        print("Ошибка: неверный формат файла (не найдены файлы)")
        return False
    
    # Разделяем на блоки файлов
    file_blocks = content[files_start:].split("\n\n---\n\n")
    
    # Создаем директорию проекта
    project_dir = os.path.join(os.getcwd(), project_name)
    os.makedirs(project_dir, exist_ok=True)
    
    restored_count = 0
    binary_count = 0
    
    for block in file_blocks:
        if not block.strip():
            continue
        
        block_lines = block.split('\n')
        if len(block_lines) < 4:
            continue
        
        # Извлекаем информацию о файле
        file_path = None
        file_name = None
        is_binary = False
        content_start = None
        
        for i, line in enumerate(block_lines):
            if line.startswith("Путь к файлу:"):
                file_path = line.replace("Путь к файлу:", "").strip()
            elif line.startswith("Имя файла:"):
                file_name = line.replace("Имя файла:", "").strip()
            elif line.startswith("Тип:"):
                is_binary = 'binary' in line.lower()
            elif line.startswith("Содержимое"):
                content_start = i + 1
                break
        
        if not file_path or not file_name or content_start is None:
            continue
        
        # Получаем полный путь к файлу
        full_path = os.path.join(project_dir, file_path)
        
        # Создаем директории если нужно
        dir_path = os.path.dirname(full_path)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
        
        # Извлекаем содержимое
        file_content_lines = block_lines[content_start:]
        file_content = '\n'.join(file_content_lines)
        
        # Записываем файл
        try:
            if is_binary:
                # Декодируем из base64
                decoded, success = decode_file(file_content)
                if not success:
                    continue
                with open(full_path, 'wb') as f:
                    f.write(decoded)
                binary_count += 1
            else:
                # Записываем как текст
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(file_content)
            
            restored_count += 1
        except Exception as e:
            print(f"Ошибка при записи файла {full_path}: {e}")
            continue
    
    print(f"Проект '{project_name}' успешно восстановлен в директории: {project_dir}")
    print(f"Восстановлено файлов: {restored_count}")
    if binary_count > 0:
        print(f"Бинарных файлов: {binary_count}")
    
    return True

def main():
    parser = argparse.ArgumentParser(
        description='Упаковка и распаковка проектов в/из одного файла',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  %(prog)s pack ./myproject          - Упаковать проект myproject
  %(prog)s pack ./myproject -o out.txt  - Упаковать с указанием имени файла
  %(prog)s unpack project.txt        - Распаковать проект из файла
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Команда')
    
    # Команда pack
    pack_parser = subparsers.add_parser('pack', help='Упаковать проект')
    pack_parser.add_argument('project_path', help='Путь к проекту')
    pack_parser.add_argument('-o', '--output', help='Имя выходного файла')
    
    # Команда unpack
    unpack_parser = subparsers.add_parser('unpack', help='Распаковать проект')
    unpack_parser.add_argument('input_file', help='Путь к файлу проекта')
    
    args = parser.parse_args()
    
    if args.command == 'pack':
        output_file = args.output if hasattr(args, 'output') else None
        pack_project(args.project_path, output_file)
    elif args.command == 'unpack':
        unpack_project(args.input_file)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
