import test from 'node:test';
import assert from 'node:assert/strict';
import { scenes } from '../../game/content/ch01.js';

test('chapter 1 has exactly 4 scenes with unique ids', () => {
  assert.equal(scenes.length, 4);
  const ids = scenes.map((s) => s.id);
  assert.equal(new Set(ids).size, 4);
});

test('acid-test scene has a valid crash step index, step balances, and a simulation-note disclaimer', () => {
  const scene = scenes.find((s) => s.id === 'acid-test');
  assert.ok(scene.crashStep >= 0 && scene.crashStep < scene.steps.length);
  assert.ok(typeof scene.simulationNote === 'string' && scene.simulationNote.length > 0);
  scene.steps.forEach((step) => {
    assert.equal(typeof step.balances.a, 'number');
    assert.equal(typeof step.balances.b, 'number');
    assert.ok(step.narration.length > 0);
  });
});

test('two-paths scene has two columns with markers that all have detail text', () => {
  const scene = scenes.find((s) => s.id === 'two-paths');
  assert.equal(scene.columns.length, 2);
  scene.columns.forEach((col) => {
    assert.ok(col.markers.length > 0);
    col.markers.forEach((marker) => {
      assert.ok(marker.detail.length > 0);
    });
  });
});

test('day-in-production scenario has 4 vignettes, each with exactly one correct option', () => {
  const scene = scenes.find((s) => s.id === 'day-in-production');
  assert.equal(scene.vignettes.length, 4);
  scene.vignettes.forEach((vignette) => {
    const correctCount = vignette.options.filter((o) => o.correct).length;
    assert.equal(correctCount, 1);
    vignette.options.forEach((option) => {
      assert.ok(option.feedback.length > 0);
    });
  });
});

test('mindset-check quiz has 4 questions, each with a valid correctIndex', () => {
  const scene = scenes.find((s) => s.id === 'mindset-check');
  assert.equal(scene.questions.length, 4);
  scene.questions.forEach((q) => {
    assert.ok(q.correctIndex >= 0 && q.correctIndex < q.choices.length);
    assert.ok(q.explanation.length > 0);
  });
});
