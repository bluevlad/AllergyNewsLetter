import { test, expect } from '@playwright/test';

const BASE_URL = process.env.BASE_URL || 'http://www.unmong.com:4050';

test.describe('OpenAPI 스펙', () => {
  test('GET /openapi.json - OpenAPI 스펙 반환', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/openapi.json`);
    expect(response.status()).toBe(200);
    const data = await response.json();
    expect(data.openapi).toBe('3.1.0');
    expect(data.info.title).toBe('AllergyNewsLetter');
  });

  test('GET /docs - Swagger UI 페이지', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/docs`);
    expect(response.status()).toBe(200);
    const html = await response.text();
    expect(html).toContain('swagger-ui');
  });
});

test.describe('홈페이지 API', () => {
  test('GET / - 홈페이지 반환', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/`);
    expect(response.status()).toBe(200);
    const html = await response.text();
    expect(html).toContain('AllergyNewsLetter');
    expect(html).toContain('뉴스레터 구독하기');
  });
});

test.describe('구독 신청 API', () => {
  test('GET /subscribe - 구독 신청 폼', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/subscribe`);
    expect(response.status()).toBe(200);
    const html = await response.text();
    expect(html).toContain('구독 신청');
  });

  test('POST /subscribe - 유효한 이메일로 구독', async ({ request }) => {
    const response = await request.post(`${BASE_URL}/subscribe`, {
      form: { email: 'test@example.com', name: '테스트' }
    });
    expect([200, 302, 303, 307]).toContain(response.status());
  });

  test('POST /subscribe - 이메일 누락 시 에러', async ({ request }) => {
    const response = await request.post(`${BASE_URL}/subscribe`, {
      form: { name: '테스트' }
    });
    expect(response.status()).toBe(422);
    const data = await response.json();
    expect(data.detail).toBeDefined();
  });

  test('POST /subscribe - 이름 없이 구독 가능', async ({ request }) => {
    const response = await request.post(`${BASE_URL}/subscribe`, {
      form: { email: 'test2@example.com' }
    });
    expect([200, 302, 303, 307]).toContain(response.status());
  });
});

test.describe('이메일 인증 API', () => {
  test('GET /verify/{id} - 인증 페이지', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/verify/1?email=test@example.com`);
    expect(response.status()).toBe(200);
    const html = await response.text();
    expect(html).toContain('인증');
  });

  test('POST /verify - 필수 필드 누락', async ({ request }) => {
    const response = await request.post(`${BASE_URL}/verify`, {
      form: { verification_id: 1 }
    });
    expect(response.status()).toBe(422);
  });
});

test.describe('인증코드 재발송 API', () => {
  test('POST /resend - verification_id 누락', async ({ request }) => {
    const response = await request.post(`${BASE_URL}/resend`, { form: {} });
    expect(response.status()).toBe(422);
  });
});

test.describe('결과 페이지 API', () => {
  test('GET /result - 구독 완료 페이지', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/result?email=test@example.com`);
    expect(response.status()).toBe(200);
    const html = await response.text();
    expect(html).toContain('구독');
  });
});

test.describe('구독 해지 API', () => {
  test('GET /unsubscribe - 구독 해지 폼', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/unsubscribe`);
    expect(response.status()).toBe(200);
    const html = await response.text();
    expect(html).toContain('구독 해지');
  });

  test('POST /unsubscribe - 유효한 이메일', async ({ request }) => {
    const response = await request.post(`${BASE_URL}/unsubscribe`, {
      form: { email: 'test@example.com' }
    });
    expect([200, 302, 303, 307]).toContain(response.status());
  });

  test('POST /unsubscribe - 이메일 누락', async ({ request }) => {
    const response = await request.post(`${BASE_URL}/unsubscribe`, { form: {} });
    expect(response.status()).toBe(422);
  });
});

test.describe('토큰 기반 구독 해지', () => {
  test('GET /unsubscribe/token/{token} - 유효하지 않은 토큰', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/unsubscribe/token/invalid-token`);
    expect(response.status()).toBe(200);
  });

  test('GET /unsubscribe/result - 구독 해지 완료', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/unsubscribe/result?email=test@example.com`);
    expect(response.status()).toBe(200);
    const html = await response.text();
    expect(html).toContain('구독 해지');
  });
});

test.describe('에러 처리', () => {
  test('존재하지 않는 엔드포인트 - 404', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/nonexistent-endpoint`);
    expect(response.status()).toBe(404);
  });

  test('잘못된 HTTP 메소드 - 405', async ({ request }) => {
    const response = await request.delete(`${BASE_URL}/subscribe`);
    expect(response.status()).toBe(405);
  });
});

test.describe('응답 헤더', () => {
  test('HTML Content-Type', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/`);
    const contentType = response.headers()['content-type'];
    expect(contentType).toContain('text/html');
  });

  test('JSON Content-Type', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/openapi.json`);
    const contentType = response.headers()['content-type'];
    expect(contentType).toContain('application/json');
  });
});

test.describe('성능', () => {
  test('API 응답 시간', async ({ request }) => {
    const startTime = Date.now();
    await request.get(`${BASE_URL}/`);
    const responseTime = Date.now() - startTime;
    expect(responseTime).toBeLessThan(2000);
  });
});

test.describe('한글 처리', () => {
  test('한글 이름 처리', async ({ request }) => {
    const response = await request.post(`${BASE_URL}/subscribe`, {
      form: { email: 'test@example.com', name: '홍길동' }
    });
    expect([200, 302, 303, 307]).toContain(response.status());
  });

  test('한글 인코딩 확인', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/`);
    const html = await response.text();
    expect(html).toContain('알러지');
    expect(html).toContain('뉴스레터');
  });
});
