import { test, expect } from '@playwright/test';

test.describe('AllergyNewsLetter 메인 페이지', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('메인 페이지 로드', async ({ page }) => {
    await expect(page).toHaveTitle('AllergyNewsLetter - 알러지 뉴스 브리핑');
    const logo = page.locator('.logo');
    await expect(logo).toHaveText('AllergyNewsLetter');
  });

  test('주요 기능 설명 표시', async ({ page }) => {
    await expect(page.getByText('최신 알러지 뉴스')).toBeVisible();
    await expect(page.getByText('PubMed 논문')).toBeVisible();
    await expect(page.getByText('매일 오전 8시 발송')).toBeVisible();
  });

  test('구독 버튼 클릭', async ({ page }) => {
    const subscribeButton = page.getByRole('link', { name: '뉴스레터 구독하기' });
    await expect(subscribeButton).toBeVisible();
    await subscribeButton.click();
    await expect(page).toHaveURL(/\/subscribe/);
  });

  test('구독 해지 버튼 클릭', async ({ page }) => {
    const unsubscribeButton = page.getByRole('link', { name: '구독 해지' });
    await expect(unsubscribeButton).toBeVisible();
    await unsubscribeButton.click();
    await expect(page).toHaveURL(/\/unsubscribe/);
  });
});

test.describe('구독 신청', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/subscribe');
  });

  test('구독 신청 페이지 로드', async ({ page }) => {
    await expect(page).toHaveTitle(/구독 신청/);
    await expect(page.getByRole('heading', { name: /뉴스레터 구독 신청/ })).toBeVisible();
    await expect(page.locator('input[type="email"]')).toBeVisible();
  });

  test('이메일 필수 입력 검증', async ({ page }) => {
    const emailInput = page.locator('input[type="email"]');
    await expect(emailInput).toHaveAttribute('required', '');
  });

  test('홈으로 돌아가기 버튼', async ({ page }) => {
    const homeButton = page.getByRole('link', { name: '홈으로 돌아가기' });
    await expect(homeButton).toBeVisible();
    await homeButton.click();
    await expect(page).toHaveURL(/\/$/);
  });
});

test.describe('구독 해지', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/unsubscribe');
  });

  test('구독 해지 페이지 로드', async ({ page }) => {
    await expect(page).toHaveTitle(/구독 해지/);
    await expect(page.getByRole('heading', { name: /뉴스레터 구독 해지/ })).toBeVisible();
  });

  test('이메일 입력 필드 확인', async ({ page }) => {
    const emailInput = page.locator('input[type="email"]');
    await expect(emailInput).toBeVisible();
    await expect(emailInput).toHaveAttribute('required', '');
  });
});

test.describe('인증 페이지', () => {
  test('인증 페이지 로드', async ({ page }) => {
    await page.goto('/verify/1?email=test@example.com');
    await expect(page).toHaveTitle(/인증/);
    const codeInput = page.locator('input[name="code"]');
    await expect(codeInput).toBeVisible();
  });
});

test.describe('결과 페이지', () => {
  test('구독 완료 페이지', async ({ page }) => {
    await page.goto('/result?email=test@example.com');
    await expect(page).toHaveTitle(/구독 완료/);
  });

  test('구독 해지 완료 페이지', async ({ page }) => {
    await page.goto('/unsubscribe/result?email=test@example.com');
    await expect(page).toHaveTitle(/구독 해지 완료/);
  });
});

test.describe('반응형 디자인', () => {
  test('모바일 뷰포트', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');
    const logo = page.locator('.logo');
    await expect(logo).toBeVisible();
    const subscribeButton = page.getByRole('link', { name: '뉴스레터 구독하기' });
    await expect(subscribeButton).toBeVisible();
  });

  test('태블릿 뷰포트', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto('/');
    const logo = page.locator('.logo');
    await expect(logo).toBeVisible();
  });
});

test.describe('접근성', () => {
  test('폼 레이블 확인', async ({ page }) => {
    await page.goto('/subscribe');
    const emailLabel = page.locator('label[for="email"]');
    await expect(emailLabel).toHaveText(/이메일/);
  });
});

test.describe('에러 처리', () => {
  test('404 페이지', async ({ page }) => {
    const response = await page.goto('/nonexistent-page');
    expect(response?.status()).toBe(404);
  });
});

test.describe('성능', () => {
  test('메인 페이지 로드 시간', async ({ page }) => {
    const startTime = Date.now();
    await page.goto('/');
    const endTime = Date.now();
    expect(endTime - startTime).toBeLessThan(3000);
  });
});
