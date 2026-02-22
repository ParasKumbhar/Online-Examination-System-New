# Read the file
with open('Exam/examProject/settings.py', 'r') as f:
    content = f.read()

# Replace the INSTALLED_APPS section
old_text = """    'django.contrib.staticfiles',
    'core',"""

new_text = """    'django.contrib.staticfiles',
    'rest_framework',
    'core',
    'api',"""

content = content.replace(old_text, new_text)

# Write the file
with open('Exam/examProject/settings.py', 'w') as f:
    f.write(content)

print('Done - settings.py updated')
