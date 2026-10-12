import '@testing-library/jest-dom';

// Polyfill window.fetch if not present
if (!globalThis.fetch) {
  // @ts-ignore
  globalThis.fetch = () => Promise.resolve({
    ok: true,
    json: () => Promise.resolve({}),
    text: () => Promise.resolve(''),
  });
}
