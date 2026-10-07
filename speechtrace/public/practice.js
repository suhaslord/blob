'use strict';
// These annotations describe user intent, never model judgments.
const rehearsalDecisions = new Map();
function clearRehearsalNotes() {
  rehearsalDecisions.clear();
  const field = document.getElementById('practice-goal');
  if (field) field.value = '';
  document.getElementById('practice-preview').hidden = true;
  document.getElementById('practice-preview').textContent = '';
}
function addRehearsalChoice(card, region, index) {
  const label = document.createElement('label');
  label.textContent = 'Your interpretation';
  const choice = document.createElement('select');
  choice.id = 'rehearsal-choice-' + index;
  label.htmlFor = choice.id;
  choice.setAttribute('aria-label', 'Your interpretation of ' + formatTime(region.start) + ' to ' + formatTime(region.end));
  for (const value of ['Review later', 'Intentional choice', 'Practice this passage']) {
    const option = document.createElement('option');
    option.value = value; option.textContent = value; choice.append(option);
  }
  choice.addEventListener('change', () => rehearsalDecisions.set(index, choice.value));
  card.append(label, choice);
}
document.getElementById('practice-export').addEventListener('click', () => {
  if (!result || document.getElementById('results').hidden) return;
  const goal = document.getElementById('practice-goal').value.trim();
  const lines = ['SpeechTrace rehearsal notes', '',
    'Intention: ' + (goal || 'No intention entered.'),
    'Result: ' + document.getElementById('result-mode').textContent,
    'Reference similarity: ' + result.score.toFixed(1),
    'Rubric: 40% energy, 40% pacing, 20% contour.', '',
    'Moments to listen to'];
  result.regions.forEach((region, index) => {
    lines.push('', formatTime(region.start) + ' to ' + formatTime(region.end),
      'Your interpretation: ' + (rehearsalDecisions.get(index) || 'Review later'),
      region.explanation);
    if (region.words) lines.push('Words: ' + region.words);
  });
  if (!result.regions.length) lines.push('No differences crossed the current thresholds.');
  lines.push('', 'A difference can be intentional. Similarity does not measure artistic quality.',
    'Word boundaries are estimates. Listen before deciding what to change.',
    'Notes remain in this browser tab until this download. The app does not save them.');
  const text = lines.join('\n');
  const preview = document.getElementById('practice-preview');
  preview.textContent = text; preview.hidden = false;
  const url = URL.createObjectURL(new Blob([text], {type:'text/plain;charset=utf-8'}));
  const link = document.createElement('a'); link.href = url; link.download = 'speechtrace-rehearsal-notes.txt';
  link.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
});
