FROM nginx:alpine
# Удаляем стандартную страницу Nginx перед копированием своей
RUN rm /usr/share/nginx/html/index.html
# Копируем ИМЕННО файл из корня
COPY index.html /usr/share/nginx/html/index.html
# Если у тебя есть стили, раскомментируй строку ниже:
# COPY style.css /usr/share/nginx/html/style.css