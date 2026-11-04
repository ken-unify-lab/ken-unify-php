FROM php:8.3-cli-alpine AS build
COPY --from=composer:2 /usr/bin/composer /usr/local/bin/composer
WORKDIR /app
RUN apk add --no-cache $PHPIZE_DEPS libxml2-dev oniguruma-dev git unzip \
    && docker-php-ext-install dom mbstring xml xmlwriter
COPY composer.json app.php ./
COPY tests ./tests
RUN composer install --no-interaction --prefer-dist --no-progress \
    && mkdir -p reports && composer test

FROM php:8.3-cli-alpine
WORKDIR /app
COPY --from=build /app/app.php ./app.php
EXPOSE 10000
CMD ["sh", "-c", "APP_VERSION=${RENDER_GIT_COMMIT:-dev} exec php -S 0.0.0.0:${PORT:-10000} app.php"]
