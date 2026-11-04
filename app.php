<?php
declare(strict_types=1);

function health_payload(string $version): array
{
    if (!preg_match('/^[a-zA-Z0-9._-]+$/D', $version)) {
        throw new InvalidArgumentException('Invalid application version');
    }
    return ['service' => 'ken-unify-php', 'status' => 'ok', 'version' => $version];
}

function route_response(string $path, string $version): array
{
    return $path === '/health'
        ? [200, health_payload($version)]
        : [404, ['error' => 'not found']];
}

if (realpath($_SERVER['SCRIPT_FILENAME'] ?? '') === __FILE__) {
    $path = parse_url($_SERVER['REQUEST_URI'] ?? '/', PHP_URL_PATH) ?: '/';
    [$status, $payload] = route_response($path, getenv('APP_VERSION') ?: 'dev');
    http_response_code($status);
    header('Content-Type: application/json');
    echo json_encode($payload, JSON_THROW_ON_ERROR);
}
