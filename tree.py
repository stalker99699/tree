import os
import argparse

def generate_tree(directory, indent='', exclude=None):
    if exclude is None:
        exclude = set()
    items = os.listdir(directory)
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

def main():
    parser = argparse.ArgumentParser(description='Генерирует описание проекта.')
    parser.add_argument('project_path', help='Путь к проекту')
    args = parser.parse_args()

    project_path = os.path.abspath(args.project_path)
    if not os.path.isdir(project_path):
        print("Ошибка: путь не существует или не является директорией")
        return

    project_name = os.path.basename(project_path)
    output_filename = f"{project_name}.txt"
    output_filepath = os.path.join(os.getcwd(), output_filename)

    exclude = {output_filename}
    try:
        tree_lines = generate_tree(project_path, indent='', exclude=exclude)
    except Exception as e:
        print(f"Ошибка при генерации дерева файлов: {e}")
        return

    tree_str = f"{project_name}/\n" + '\n'.join(tree_lines)
    file_contents = []

    for dirpath, dirnames, filenames in os.walk(project_path):
        if output_filename in filenames:
            filenames.remove(output_filename)
        dirnames[:] = [d for d in dirnames if d not in exclude]
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            relative_path = os.path.relpath(file_path, project_path)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                continue
            except Exception as e:
                print(f"Ошибка при чтении файла {file_path}: {e}")
                continue
            file_contents.append({
                'path': relative_path,
                'name': filename,
                'content': content
            })

    with open(output_filepath, 'w', encoding='utf-8') as f:
        f.write(f"Имя проекта: {project_name}\n\n")
        f.write("Древо файлов проекта:\n")
        f.write(tree_str)
        f.write("\n\n")
        for file_info in file_contents:
            f.write(f"Путь к файлу: {file_info['path']}\n")
            f.write(f"Имя файла: {file_info['name']}\n")
            f.write("Содержимое:\n")
            f.write(file_info['content'])
            f.write("\n\n---\n\n")

if __name__ == "__main__":
    main()
