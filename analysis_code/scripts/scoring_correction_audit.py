"""Create aggregate old-versus-corrected scoring counts without exporting IDs."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd

def audit(previous: Path, current: Path):
    old=pd.read_csv(previous,dtype={'mergeid':str},low_memory=False).set_index('mergeid')
    new=pd.read_csv(current,dtype={'mergeid':str},low_memory=False).set_index('mergeid')
    if not old.index.is_unique or not new.index.is_unique or set(old.index)!=set(new.index):
        raise ValueError('Scoring comparison requires the identical unique source population.')
    new=new.reindex(old.index)
    required=['r7agey','female','education_level','bmi','chronic_burden','country','disadvantage_group','r8lnlys3','r8wtresp']
    oldmask=old.analysis_eligible_loneliness.eq(1)&old[required].notna().all(axis=1)&old.r8wtresp.gt(0)
    newmask=new.analysis_eligible_loneliness.eq(1)&new[required].notna().all(axis=1)&new.r8wtresp.gt(0)
    both=oldmask&newmask
    groups=['low_0_1','mid_2','high_3_4']
    rows=[]
    def add(metric,a,b,scope):rows.append(dict(metric=metric,old=a,new=b,scope=scope))
    add('source_records',len(old),len(new),'All harmonized SHARE records')
    add('primary_n',int(oldmask.sum()),int(newmask.sum()),'Primary loneliness analysis')
    for g in groups:add('primary_group_'+g,int((oldmask&old.disadvantage_group.eq(g)).sum()),int((newmask&new.disadvantage_group.eq(g)).sum()),'Primary loneliness analysis')
    add('allfour_primary_n',int((oldmask&old.disadvantage_component_nonmissing.eq(4)).sum()),int((newmask&new.disadvantage_component_nonmissing.eq(4)).sum()),'Primary loneliness analysis')
    changes=[]
    for c in ['disadv_childhood','disadv_adult_pattern','disadv_late_uptake','disadvantage_score','disadvantage_component_nonmissing']:
        mask=~(old[c].eq(new[c])|(old[c].isna()&new[c].isna()))
        add(c+'_missing_n',int(old[c].isna().sum()),int(new[c].isna().sum()),'All harmonized SHARE records')
        tab=pd.DataFrame({'old':old.loc[mask,c].fillna('missing'),'new':new.loc[mask,c].fillna('missing')}).value_counts().reset_index(name='n')
        changes.append(dict(variable=c,changed_all_n=int(mask.sum()),changed_old_primary_n=int((mask&oldmask).sum()),transitions=tab.to_dict('records')))
    move=pd.crosstab(old.loc[both,'disadvantage_group'],new.loc[both,'disadvantage_group']).reindex(index=groups,columns=groups,fill_value=0)
    report=dict(source_population_identical=True,primary_removed_n=int((oldmask&~newmask).sum()),primary_added_n=int((~oldmask&newmask).sum()),primary_removed_old_groups={g:int((oldmask&~newmask&old.disadvantage_group.eq(g)).sum()) for g in groups},retained_primary_group_transitions=[dict(old_group=x,new_group=y,n=int(move.loc[x,y])) for x in groups for y in groups if move.loc[x,y]],component_changes=changes,source_response_sensitivity_status='Incorporated in corrected primary scoring; not an independent current model')
    # Non-scoring model inputs must be exactly unchanged.
    check=[c for c in old if c not in ['disadv_childhood','disadv_adult_pattern','disadv_late_uptake','disadvantage_component_nonmissing','disadvantage_score','disadvantage_group','analysis_eligible_loneliness','analysis_eligible_casp']]
    mismatch=[]
    for c in check:
        if not (old[c].eq(new[c])|(old[c].isna()&new[c].isna())).all():mismatch.append(c)
    if mismatch:raise AssertionError('Non-scoring variables changed: '+', '.join(mismatch))
    report['unchanged_non_scoring_columns']=len(check)
    for g in groups:
        add('fixed_primary_group_'+g,int((oldmask&old.disadvantage_group.eq(g)).sum()),int((oldmask&new.disadvantage_group.eq(g)).sum()),'Fixed previous primary sample')
    for x in groups:
        for y in groups:
            if move.loc[x,y]:add('transition_'+x+'_to_'+y,0,int(move.loc[x,y]),'Participants retained in both primary samples')
    fixed_scores=pd.DataFrame({'old':old.loc[oldmask,'disadvantage_score'],'new':new.loc[oldmask,'disadvantage_score']})
    for (before,after),n in fixed_scores.value_counts().items():
        if before!=after:add(f'fixed_score_{int(before)}_to_{int(after)}',0,int(n),'Fixed previous primary sample')
    add('primary_added_n',0,report['primary_added_n'],'New primary sample membership')
    add('primary_removed_n',0,report['primary_removed_n'],'New primary sample membership')
    return pd.DataFrame(rows),report

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--previous',type=Path,required=True);p.add_argument('--current',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True);p.add_argument('--output-stem',default='share_scoring_correction_audit',help='Use a distinct stem to retain earlier correction history.');a=p.parse_args()
    table,report=audit(a.previous,a.current);a.output_dir.mkdir(parents=True,exist_ok=True)
    table.to_csv(a.output_dir/(a.output_stem+'.csv'),index=False)
    (a.output_dir/(a.output_stem+'.json')).write_text(json.dumps(report,indent=2,ensure_ascii=False,allow_nan=False))
    print(json.dumps({k:v for k,v in report.items() if k not in ['component_changes']},ensure_ascii=False))
if __name__=='__main__':main()
