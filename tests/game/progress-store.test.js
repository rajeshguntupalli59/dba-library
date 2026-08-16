import test from 'node:test';
import assert from 'node:assert/strict';
import {
  parseProgress,
  serializeProgress,
  createStorageAdapter,
  createProgressStore,
} from '../../game/progress-store.js';

function makeFakeStorage(overrides = {}) {
  const store = new Map();
  return {
    getItem: overrides.getItem || ((key) => (store.has(key) ? store.get(key) : null)),
    setItem: overrides.setItem || ((key, value) => store.set(key, value)),
    removeItem: overrides.removeItem || ((key) => store.delete(key)),
  };
}

test('parseProgress returns default shape for null/invalid input', () => {
  assert.deepEqual(parseProgress(null), { xp: 0, chapters: {} });
  assert.deepEqual(parseProgress('not json'), { xp: 0, chapters: {} });
  assert.deepEqual(parseProgress(undefined), { xp: 0, chapters: {} });
});

test('parseProgress round-trips a valid serialized progress object', () => {
  const original = { xp: 42, chapters: { ch01: { 'acid-test': 20 } } };
  const raw = serializeProgress(original);
  assert.deepEqual(parseProgress(raw), original);
});

test('createStorageAdapter falls back to in-memory storage when localStorage throws', () => {
  const throwingStorage = makeFakeStorage({
    setItem: () => { throw new Error('QuotaExceededError'); },
  });
  const adapter = createStorageAdapter(throwingStorage);
  assert.equal(adapter.read(), null);
  const wrote = adapter.write('{"xp":5,"chapters":{}}');
  assert.equal(wrote, true);
  assert.equal(adapter.read(), '{"xp":5,"chapters":{}}');
});

test('createStorageAdapter uses real storage when available', () => {
  const realish = makeFakeStorage();
  const adapter = createStorageAdapter(realish);
  adapter.write('{"xp":9,"chapters":{}}');
  assert.equal(realish.getItem('dba-handbook-progress'), '{"xp":9,"chapters":{}}');
});

test('awardSceneXp adds xp once and is idempotent for the same scene', () => {
  const store = createProgressStore(makeFakeStorage());
  store.awardSceneXp('ch01', 'acid-test', 20);
  store.awardSceneXp('ch01', 'acid-test', 20);
  assert.equal(store.getTotalXp(), 20);
  assert.equal(store.isSceneComplete('ch01', 'acid-test'), true);
});

test('getChapterStats reports mastery once all scenes for a chapter are complete', () => {
  const store = createProgressStore(makeFakeStorage());
  store.awardSceneXp('ch01', 'acid-test', 20);
  store.awardSceneXp('ch01', 'two-paths', 15);
  let stats = store.getChapterStats('ch01', 4);
  assert.equal(stats.mastered, false);
  assert.equal(stats.completedScenes, 2);

  store.awardSceneXp('ch01', 'day-in-production', 20);
  store.awardSceneXp('ch01', 'mindset-check', 15);
  stats = store.getChapterStats('ch01', 4);
  assert.equal(stats.mastered, true);
  assert.equal(stats.completedScenes, 4);
});

test('getChaptersMasteredCount counts only fully mastered chapters', () => {
  const store = createProgressStore(makeFakeStorage());
  store.awardSceneXp('ch01', 'acid-test', 20);
  store.awardSceneXp('ch01', 'two-paths', 15);
  store.awardSceneXp('ch01', 'day-in-production', 20);
  store.awardSceneXp('ch01', 'mindset-check', 15);

  const count = store.getChaptersMasteredCount({ ch01: 4, ch02: 4 });
  assert.equal(count, 1);
});

test('progress persists across a new store instance backed by the same storage', () => {
  const storage = makeFakeStorage();
  const store1 = createProgressStore(storage);
  store1.awardSceneXp('ch01', 'acid-test', 20);

  const store2 = createProgressStore(storage);
  assert.equal(store2.getTotalXp(), 20);
  assert.equal(store2.isSceneComplete('ch01', 'acid-test'), true);
});
