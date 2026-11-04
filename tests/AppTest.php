<?php
declare(strict_types=1);
use PHPUnit\Framework\TestCase;
require_once __DIR__ . '/../app.php';

final class AppTest extends TestCase
{
    public function testHealthRouteReturnsTestedVersion(): void
    {
        [$status, $body] = route_response('/health', 'abc123');
        self::assertSame(200, $status);
        self::assertSame(['service' => 'ken-unify-php', 'status' => 'ok', 'version' => 'abc123'], $body);
    }

    public function testUnknownRouteReturns404(): void
    {
        self::assertSame([404, ['error' => 'not found']], route_response('/missing', 'abc123'));
    }

    public function testInvalidVersionIsRejected(): void
    {
        $this->expectException(InvalidArgumentException::class);
        health_payload('unsafe"version');
    }
}
