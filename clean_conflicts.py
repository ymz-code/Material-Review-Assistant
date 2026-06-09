import re

# 读取文件
with open('c:\\Users\\li\\AppData\\Local\\Programs\\Trae CN\\project_1\\static\\index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 移除所有 Git 冲突标记
# 模式1: 移除 <<<<<<< Updated upstream 到 ======= 之间的内容（保留 ======= 后的内容）
content = re.sub(r'<<<<<<< Updated upstream.*?=======', '', content, flags=re.DOTALL)

# 模式2: 移除 <<<<<<< HEAD 到 ======= 之间的内容（保留 ======= 后的内容）
content = re.sub(r'<<<<<<< HEAD.*?=======', '', content, flags=re.DOTALL)

# 模式3: 移除 >>>>>>> 开头的行（任何分支名）
content = re.sub(r'>>>>>>> .*$', '', content, flags=re.MULTILINE)

# 模式4: 移除单独的 ======= 行（这些可能是残留的）
content = re.sub(r'^=======\s*$', '', content, flags=re.MULTILINE)

# 模式5: 移除空的代码块
content = re.sub(r'\{\s*\}', '', content)

# 写回文件
with open('c:\\Users\\li\\AppData\\Local\\Programs\\Trae CN\\project_1\\static\\index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print('Git 冲突标记已清理完成')