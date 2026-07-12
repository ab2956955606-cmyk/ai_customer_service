import { afterEach, describe, expect, it, vi } from 'vitest';
import { api } from './client';

describe('API request headers', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('preserves JSON content type when adding an ephemeral DeepSeek key', async () => {
    const fetchMock = vi.fn<typeof fetch>().mockResolvedValue(
      new Response('{}', {
        status: 200,
        headers: { 'Content-Type': 'application/json' }
      })
    );
    vi.stubGlobal('fetch', fetchMock);

    const payload = {
      subject: 'Cannot reset password',
      description: 'The password reset email is not arriving.',
      customer_email: 'alice@example.com'
    };
    await api.createTicket(payload, 'sk-ephemeral-test');

    expect(fetchMock).toHaveBeenCalledOnce();
    const [url, init] = fetchMock.mock.calls[0];
    const headers = new Headers(init?.headers);
    expect(String(url)).toBe('http://localhost:8001/api/tickets');
    expect(init?.method).toBe('POST');
    expect(headers.get('Content-Type')).toBe('application/json');
    expect(headers.get('X-DeepSeek-API-Key')).toBe('sk-ephemeral-test');
    expect(JSON.parse(String(init?.body))).toEqual(payload);
  });

  it('sends the ephemeral DeepSeek key to the eval runner', async () => {
    const fetchMock = vi.fn<typeof fetch>().mockResolvedValue(
      new Response('{}', {
        status: 200,
        headers: { 'Content-Type': 'application/json' }
      })
    );
    vi.stubGlobal('fetch', fetchMock);

    await api.runEvals('zh', 'sk-ephemeral-eval-test');

    expect(fetchMock).toHaveBeenCalledOnce();
    const [url, init] = fetchMock.mock.calls[0];
    const headers = new Headers(init?.headers);
    expect(String(url)).toBe('http://localhost:8001/api/evals/run?locale=zh');
    expect(init?.method).toBe('POST');
    expect(headers.get('Content-Type')).toBe('application/json');
    expect(headers.get('X-DeepSeek-API-Key')).toBe('sk-ephemeral-eval-test');
  });

  it('loads the latest result for the selected eval language', async () => {
    const fetchMock = vi.fn<typeof fetch>().mockResolvedValue(
      new Response('{}', {
        status: 200,
        headers: { 'Content-Type': 'application/json' }
      })
    );
    vi.stubGlobal('fetch', fetchMock);

    await api.latestEvals('zh');

    expect(fetchMock).toHaveBeenCalledOnce();
    const [url] = fetchMock.mock.calls[0];
    expect(String(url)).toBe('http://localhost:8001/api/evals/latest?locale=zh');
  });
});
