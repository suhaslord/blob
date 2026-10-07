'use client';

import { useEffect, useRef, useState } from 'react';
import { suggestIntent } from '@/lib/intent-model.mjs';
import {
  ArrowRight,
  CheckCircle2,
  ExternalLink,
  HeartPulse,
  MapPin,
  PhoneCall,
  ShieldCheck,
  Sparkles,
  Stethoscope,
} from 'lucide-react';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Checkbox } from '@/components/ui/checkbox';
import { Textarea } from '@/components/ui/textarea';

type Mode = 'now' | 'affordable' | 'prepare';
const MODES = [
  { id: 'now' as const, label: 'I need care now', icon: HeartPulse },
  { id: 'affordable' as const, label: 'Find affordable care', icon: MapPin },
  { id: 'prepare' as const, label: 'Prepare for a visit', icon: Stethoscope },
];
const RED_FLAGS = [
  'Trouble breathing, fainting, or not responding',
  'Chest pain, stroke signs, or a severe injury',
  'Bleeding that will not stop',
  'Thoughts of suicide or harming someone',
];

export default function Home() {
  const [mode, setMode] = useState<Mode>('now');
  const [concern, setConcern] = useState('');
  const [flags, setFlags] = useState<string[]>([]);
  const [generated, setGenerated] = useState(false);
  const [questions, setQuestions] = useState<string[]>([]);
  const [questionDraft, setQuestionDraft] = useState('');
  const crisis = flags.includes(RED_FLAGS[3]);
  const emergency = flags.some(flag => flag !== RED_FLAGS[3]);
  const firstWords = concern.trim() || 'your concern';
  const suggestion = suggestIntent(concern);
  const resultRef = useRef<HTMLDivElement>(null);
  useEffect(() => { if (generated) resultRef.current?.focus(); }, [generated]);

  function toggleFlag(flag: string) {
    setFlags((current) =>
      current.includes(flag)
        ? current.filter((item) => item !== flag)
        : [...current, flag],
    );
    setGenerated(false);
  }

  return (
    <main className="min-h-screen overflow-hidden">
      <header className="mx-auto flex max-w-6xl items-center justify-between px-5 py-5 md:px-8">
        <a
          className="flex items-center gap-2 font-semibold tracking-tight"
          href="#top"
          aria-label="CareRoute home"
        >
          <span className="grid size-9 place-items-center rounded-xl bg-primary text-primary-foreground shadow-sm">
            <HeartPulse className="size-5" />
          </span>
          <span className="text-lg">CareRoute</span>
        </a>
        <Badge
          variant="outline"
          className="border-primary/20 bg-white/60 text-primary"
        >
          <ShieldCheck /> Privacy-first prototype
        </Badge>
      </header>

      <section
        id="top"
        className="relative mx-auto max-w-6xl px-5 pb-16 pt-8 md:px-8 md:pt-14"
      >
        <div className="route-line" aria-hidden="true" />
        <div className="relative grid items-start gap-10 lg:grid-cols-[0.78fr_1.22fr] lg:gap-14">
          <div className="pt-3">
            <Badge className="mb-5 bg-primary/10 text-primary hover:bg-primary/10">
              Free • no sign-in
            </Badge>
            <h1 className="max-w-xl text-balance text-5xl font-semibold leading-[0.98] tracking-[-0.055em] md:text-6xl">
              Know where to go.{' '}
              <span className="text-primary">Know what to ask.</span>
            </h1>
            <p className="mt-6 max-w-lg text-pretty text-base leading-7 text-muted-foreground md:text-lg">
              A two-minute guide to safer next steps, affordable local care, and
              a more prepared medical visit.
            </p>
            <div className="mt-8 grid max-w-md gap-3 text-sm text-muted-foreground sm:grid-cols-3">
              {['No diagnosis', 'No data saved', 'Official resources'].map(
                (item) => (
                  <div key={item} className="flex items-center gap-2">
                    <CheckCircle2 className="size-4 text-primary" /> {item}
                  </div>
                ),
              )}
            </div>
          </div>

          <Card className="relative overflow-visible rounded-[1.75rem] border-0 bg-white/90 py-0 shadow-[0_24px_80px_-28px_rgba(15,55,60,0.35)] ring-1 ring-primary/10 backdrop-blur">
            <CardContent className="p-4 md:p-6">
              <div id="care-inputs">
              <div className="grid gap-2 rounded-2xl bg-muted p-1.5 sm:grid-cols-3" aria-label="Choose a care tool">
                {MODES.map(({ id, label, icon: Icon }) => (
                  <button
                    key={id}
                    type="button"
                    aria-pressed={mode === id}
                    onClick={() => {
                      setMode(id);
                      setGenerated(false);
                    }}
                    className={`flex min-h-11 items-center justify-center gap-2 rounded-xl px-3 text-sm font-medium transition ${mode === id ? 'bg-white text-foreground shadow-sm' : 'text-muted-foreground hover:text-foreground'}`}
                  >
                    <Icon className="size-4" /> {label}
                  </button>
                ))}
              </div>
              <div className="mt-6">
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-primary">
                  Safety check
                </p>
                <h2 className="mt-2 text-2xl font-semibold tracking-tight">
                  Is any of this happening right now?
                </h2>
                <div className="mt-4 grid gap-3 sm:grid-cols-2">
                  {RED_FLAGS.map((flag) => (
                    <label
                      key={flag}
                      className="flex cursor-pointer items-start gap-3 rounded-xl border bg-background/70 p-3 text-sm leading-5 transition hover:border-primary/30"
                    >
                      <Checkbox
                        checked={flags.includes(flag)}
                        onCheckedChange={() => toggleFlag(flag)}
                      />
                      <span>{flag}</span>
                    </label>
                  ))}
                </div>
                <label
                  className="mt-5 block text-sm font-medium"
                  htmlFor="concern"
                >
                  Briefly describe what you need help with{' '}
                  <span className="font-normal text-muted-foreground">
                    (optional)
                  </span>
                </label>
                <Textarea
                  id="concern"
                  value={concern}
                  onChange={(event) => {
                    setConcern(event.target.value);
                    setGenerated(false);
                  }}
                  className="mt-2 min-h-24 resize-none bg-background"
                  placeholder="Example: I have had a sore throat for two days and do not have insurance."
                  maxLength={1000}
                  aria-describedby="privacy-note"
                />
                <p id="privacy-note" className="mt-2 text-xs leading-5 text-muted-foreground">US resources. Your text stays on this device and clears when you reload. Avoid names or identifying details.</p>
                {mode === 'prepare' && (
                  <div className="mt-4 rounded-xl border p-3">
                    <label htmlFor="visit-question" className="block text-sm font-medium">Your top questions for the visit</label>
                    <p className="mt-1 text-xs text-muted-foreground">Add up to five questions, in the order you want to ask them. They stay on this device.</p>
                    <form className="mt-2 flex gap-2" onSubmit={event => {event.preventDefault(); if(questionDraft.trim() && questions.length < 5) {setQuestions([...questions,questionDraft.trim()]);setQuestionDraft('');setGenerated(false);}}}>
                      <input id="visit-question" className="min-w-0 flex-1 rounded-lg border px-3 py-2 text-sm" maxLength={200} value={questionDraft} onChange={event => setQuestionDraft(event.target.value)} placeholder="Example: What should I bring to the visit?" />
                      <Button type="submit" variant="outline" disabled={!questionDraft.trim() || questions.length >= 5}>Add</Button>
                    </form>
                    <ol className="mt-3 space-y-2 text-sm">
                      {questions.map((question,index) => <li key={index} className="flex items-start justify-between gap-2"><span>{index+1}. {question}</span><div className="flex shrink-0 gap-2"><button type="button" className="underline disabled:opacity-40" disabled={index===0} aria-label={`Move question ${index+1} up`} onClick={() => {const next=[...questions];[next[index-1],next[index]]=[next[index],next[index-1]];setQuestions(next);setGenerated(false);}}>Up</button><button type="button" className="underline disabled:opacity-40" disabled={index===questions.length-1} aria-label={`Move question ${index+1} down`} onClick={() => {const next=[...questions];[next[index],next[index+1]]=[next[index+1],next[index]];setQuestions(next);setGenerated(false);}}>Down</button><button type="button" className="underline" aria-label={`Remove question ${index+1}`} onClick={() => {setQuestions(questions.filter((_,i) => i !== index));setGenerated(false);}}>Remove</button></div></li>)}
                    </ol>
                    {questions.length === 5 && <p role="status" className="mt-2 text-xs">Five questions added. Remove one to add another.</p>}
                  </div>
                )}
                {suggestion && !flags.length && suggestion !== mode && (
                  <div className="mt-3 rounded-xl border bg-background p-3 text-sm">
                    <p>Suggested tool: {suggestion === 'affordable' ? 'affordable care' : 'visit preparation'}.</p>
                    <p className="mt-1 text-xs text-muted-foreground">A small on-device model suggests a tool from your wording. You decide; it does not assess your health.</p>
                    <Button variant="outline" className="mt-2" onClick={() => {setMode(suggestion);setGenerated(false);}}>Use suggested tool</Button>
                  </div>
                )}
                <Button
                  size="lg"
                  className="mt-5 h-11 w-full rounded-xl"
                  onClick={() => setGenerated(true)}
                >
                  Build my next-step plan <ArrowRight data-icon="inline-end" />
                </Button>
              </div>
              </div>
              {(generated || emergency || crisis) && (
                <div ref={resultRef} tabIndex={-1} role="region" aria-label="Your next steps" aria-live="polite" className="mt-6 rounded-2xl outline-none animate-in fade-in slide-in-from-bottom-2">
                  {emergency ? (
                    <Alert variant="destructive" className="border-destructive/30 bg-destructive/5 p-4">
                      <PhoneCall className="size-5" />
                      <AlertTitle>Call 911 now</AlertTitle>
                      <AlertDescription>
                        These warning signs may be an emergency. Do not wait for this website. <a href="tel:911" className="font-semibold underline">Call 911</a>.
                        {crisis && <span> You also selected a crisis warning. Tell the emergency operator; <a href="tel:988" className="font-semibold underline">988</a> offers additional US crisis support.</span>}
                      </AlertDescription>
                    </Alert>
                  ) : crisis ? (
                    <Alert
                      variant="destructive"
                      className="border-destructive/30 bg-destructive/5 p-4"
                    >
                      <PhoneCall className="size-5" />
                      <AlertTitle>Get immediate crisis support</AlertTitle>
                      <AlertDescription>
                        Call or text <a href="tel:988" className="font-semibold underline">988</a> now. If anyone is in
                        immediate danger, call <a href="tel:911" className="font-semibold underline">911</a>.
                      </AlertDescription>
                    </Alert>
                  ) : (
                    <Plan mode={mode} concern={firstWords} questions={questions} />
                  )}
                  {!flags.length && <Button variant="outline" className="mt-3" onClick={() => window.print()}>Print my plan</Button>}
                </div>
              )}
              {(concern || flags.length > 0 || generated || questions.length > 0 || questionDraft) && <Button variant="ghost" className="mt-3" onClick={() => {setConcern('');setFlags([]);setGenerated(false);setMode('now');setQuestions([]);setQuestionDraft('');}}>Clear and start over</Button>}
            </CardContent>
          </Card>
        </div>
      </section>

      <section className="border-t bg-white/55">
        <div className="mx-auto grid max-w-6xl gap-8 px-5 py-10 text-sm text-muted-foreground md:grid-cols-[1fr_auto] md:px-8">
          <div>
            <p className="font-semibold text-foreground">
              CareRoute is an educational prototype, not medical advice.
            </p>
            <p className="mt-1 max-w-2xl">
              It does not diagnose conditions or replace a clinician.
              Information entered here stays in this browser session.
              Not selecting a warning sign does not rule out an emergency. These resources are for the United States.
            </p>
          </div>
          <div className="flex flex-wrap gap-4">
            <a
              className="hover:text-primary"
              href="https://medlineplus.gov/ency/article/001927.htm"
              target="_blank"
              rel="noreferrer"
            >
              Emergency guidance <ExternalLink className="inline size-3" />
            </a>
            <a
              className="hover:text-primary"
              href="https://findahealthcenter.hrsa.gov/"
              target="_blank"
              rel="noreferrer"
            >
              HRSA centers <ExternalLink className="inline size-3" />
            </a>
            <a
              className="hover:text-primary"
              href="https://211.org/"
              target="_blank"
              rel="noreferrer"
            >
              211 help <ExternalLink className="inline size-3" />
            </a>
          </div>
        </div>
      </section>
    </main>
  );
}

function Plan({ mode, concern, questions }: { mode: Mode; concern: string; questions: string[] }) {
  if (mode === 'affordable')
    return (
      <div className="rounded-2xl border border-primary/15 bg-primary/5 p-5">
        <p className="flex items-center gap-2 font-semibold text-primary">
          <MapPin className="size-4" /> Your affordable-care route
        </p>
        <ol className="mt-4 space-y-3 text-sm leading-6">
          <li>
            <strong>1. Search a community health center.</strong> They serve
            people with or without insurance and use a sliding fee scale.
          </li>
          <li>
            <strong>2. Call 211.</strong> Ask for nearby low-cost clinics,
            transportation, or prescription help.
          </li>
          <li>
            <strong>3. Before visiting, ask:</strong> “What will this cost
            without insurance, and do you offer financial assistance?”
          </li>
        </ol>
        <div className="mt-5 flex flex-wrap gap-2">
          <Button
            render={
              <a
                href="https://findahealthcenter.hrsa.gov/"
                target="_blank"
                rel="noreferrer"
                aria-label="Find a community health center"
              />
            }
          >
            <MapPin /> Find a health center
          </Button>
          <Button
            variant="outline"
            render={
              <a
                href="https://211.org/"
                target="_blank"
                rel="noreferrer"
                aria-label="Open 211 local services"
              />
            }
          >
            Open 211
          </Button>
        </div>
      </div>
    );
  if (mode === 'prepare')
    return (
      <div className="rounded-2xl border border-primary/15 bg-primary/5 p-5">
        <p className="flex items-center gap-2 font-semibold text-primary">
          <Sparkles className="size-4" /> Your visit-prep card
        </p>
        <p className="mt-3 text-sm text-muted-foreground">
          Bring this summary: “I’d like help with {concern}.”
        </p>
        {questions.length > 0 && <div className="mt-4"><h3 className="text-sm font-semibold">My priorities</h3><ol className="mt-2 list-decimal space-y-1 pl-5 text-sm">{questions.map((question,index) => <li key={index}>{question}</li>)}</ol></div>}
        <ul className="mt-4 space-y-2 text-sm">
          {[
            'When did it start, and what makes it better or worse?',
            'What medications, allergies, or health conditions should I mention?',
            'What should I watch for, and when should I seek urgent help?',
            'What will the recommended care cost?',
          ].map((item) => (
            <li key={item} className="flex gap-2">
              <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-primary" />{' '}
              {item}
            </li>
          ))}
        </ul>
      </div>
    );
  return (
    <div className="rounded-2xl border border-primary/15 bg-primary/5 p-5">
      <p className="flex items-center gap-2 font-semibold text-primary">
        <ShieldCheck className="size-4" /> No emergency warning signs selected
      </p>
      <p className="mt-3 text-sm leading-6">
        For {concern}, consider calling your primary-care clinic or a nurse
        advice line. If you cannot get timely help, an urgent-care clinic may be
        appropriate. If symptoms become severe or a red flag appears, call 911.
      </p>
      <Button
        variant="outline"
        className="mt-4"
        render={
          <a
            href="https://findahealthcenter.hrsa.gov/"
            target="_blank"
            rel="noreferrer"
            aria-label="Find nearby care"
          />
        }
      >
        <MapPin /> Find nearby care
      </Button>
    </div>
  );
}
