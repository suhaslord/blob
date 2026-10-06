from pathlib import Path
import json,statistics
ROOT=Path(__file__).resolve().parents[1];d=json.loads((ROOT/'public/data/dataset.json').read_text());rows=[]
for c in d['cases']:
 gold=c['gold_regions'];predicted=c['result']['regions'];iou=[]
 for g in gold:
  same=[r for r in predicted if r['kind']==g['kind']]
  best=max([max(0,min(r['end'],g['end'])-max(r['start'],g['start']))/(max(r['end'],g['end'])-min(r['start'],g['start'])) for r in same]+[0]);iou.append(round(best,3))
 rows.append({'case':c['id'],'split':'calibration' if c['clip']=='power' else 'held-out excerpt','score':c['result']['score'],'gold_region_count':len(gold),'detected_region_count':len(predicted),'region_iou':iou,'transcript_coverage':c['result']['alignment']['coverage']})
controls=[r for r in rows if r['gold_region_count']==0];moderate=[r for r in rows if 'moderate-volume' in r['case'] or 'severe-volume' in r['case']];pause=[r for r in rows if 'extra-pause' in r['case']];rushed=[r for r in rows if 'rushed' in r['case']]
summary={'dataset_cases':len(rows),'speakers':1,'excerpts':2,'calibration_clip':'power','held_out_clip':'beliefs','unmodified_or_global_gain_controls':len(controls),'control_false_positive_cases':sum(r['detected_region_count']>0 for r in controls),'moderate_and_severe_volume_mean_iou':round(statistics.mean(r['region_iou'][0] for r in moderate),3),'pause_mean_iou':round(statistics.mean(r['region_iou'][0] for r in pause),3),'rushed_detected_cases':sum(r['detected_region_count']>0 for r in rushed),'near_perfect_below_threshold_cases':2,'limitations':['Two excerpts of one speaker; this is not cross-speaker validation.','Exact labels describe injected changes. Baseline word boundaries are machine-estimated, not manually verified.','Near-perfect 5 dB edits are deliberately below the 7 dB energy threshold and are not detected.','Pause localization can include adjacent natural silence.','Scores express reference similarity, not subjective or competitive performance quality.'],'cases':rows}
(ROOT/'public/data/evaluation.json').write_text(json.dumps(summary,indent=2));print(json.dumps({k:v for k,v in summary.items() if k not in ['cases','limitations']},indent=2))
