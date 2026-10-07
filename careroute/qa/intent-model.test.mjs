import { test } from 'node:test';
import assert from 'node:assert/strict';
import { suggestIntent } from '../lib/intent-model.mjs';
test('held-out administrative phrases select useful tools', () => {
  for (const text of ['I do not have insurance and the clinic bill is expensive','my hospital bill costs too much','I need financial assistance for a prescription']) assert.equal(suggestIntent(text),'affordable');
  for (const text of ['I want to organize questions for an appointment','help me write notes before my visit','prepare a list of medications for my doctor']) assert.equal(suggestIntent(text),'prepare');
});
test('empty, unknown, mixed, and clinical-only wording abstains', () => {
  for (const text of ['', 'hello', 'chest pain', 'insurance visit', '😕', 'severe headache']) assert.equal(suggestIntent(text),null);
});
