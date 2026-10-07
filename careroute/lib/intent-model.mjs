// Multinomial naive Bayes trained on hand-written synthetic administrative intents.
// Never used for diagnosis, red flags, or medical urgency.
const samples = {
  affordable: ['cannot afford care insurance bill cost expensive', 'uninsured low cost clinic financial assistance', 'cheap doctor without insurance money', 'sliding scale fees payment help', 'prescription costs budget medication assistance', 'transportation to free clinic', 'hospital bill too expensive', 'need affordable health center'],
  prepare: ['prepare appointment questions doctor visit', 'write summary for my appointment', 'what should i bring to the visit', 'organize notes before seeing clinician', 'list medications and allergies for doctor', 'remember questions at consultation', 'visit preparation checklist', 'explain my concern to a nurse'],
  now: ['need help with a health concern', 'where can i get care today', 'call my clinic for advice', 'find nearby primary care', 'not sure what to do next', 'need to talk with a nurse', 'looking for health information', 'general next steps for care'],
};
const stop = new Set('a an the to for my i me with of and at in do what should can get need'.split(' '));
const tokens = text => (text.toLowerCase().match(/[a-z]+/g) || []).filter(w => !stop.has(w));
const vocabulary = new Set();
const classes = Object.entries(samples).map(([mode, phrases]) => {
  const counts = new Map(); let total = 0;
  for (const phrase of phrases) for (const word of tokens(phrase)) {counts.set(word,(counts.get(word)||0)+1);vocabulary.add(word);total++;}
  return {mode,counts,total};
});
export function suggestIntent(text) {
  const words = tokens(text).filter(w => vocabulary.has(w));
  if (words.length < 2) return null;
  const scores = classes.map(c => ({mode:c.mode,score:words.reduce((n,w)=>n+Math.log(((c.counts.get(w)||0)+1)/(c.total+vocabulary.size)),0)})).sort((a,b)=>b.score-a.score);
  if (scores[0].score-scores[1].score < 0.8) return null;
  return scores[0].mode === 'now' ? null : scores[0].mode;
}
