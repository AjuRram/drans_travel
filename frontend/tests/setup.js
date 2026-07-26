import "@testing-library/jest-dom/vitest";

class LocalStorageMock {
  constructor() {
    this.store = {};
  }
  clear() {
    this.store = {};
  }
  getItem(key) {
    return this.store[key] ?? null;
  }
  setItem(key, value) {
    this.store[key] = String(value);
  }
  removeItem(key) {
    delete this.store[key];
  }
}

Object.defineProperty(globalThis, "localStorage", {
  value: new LocalStorageMock(),
});

beforeEach(() => {
  localStorage.clear();
  vi.restoreAllMocks();
});
