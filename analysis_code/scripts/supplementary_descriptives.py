"""Availability and score-computability summaries already present in the supplement."""
import numpy as np
import pandas as pd
from scripts.build_analysis_inputs import COMPONENTS
from scripts.descriptive_helpers import weighted_mean,weighted_sd

def summarize(share,primary,casp):
    age=share.loc[share.r7agey.ge(50)]
    groups={'computable':age.loc[age.disadvantage_score.notna()],'not_computable':age.loc[age.disadvantage_score.isna()]}
    info={};rows=[]
    for label,d in groups.items():
        info[label]={'n':len(d),'pct_of_age50':100*len(d)/len(age),'component_observation_counts':{str(i):int(d.disadvantage_component_nonmissing.eq(i).sum()) for i in range(5)},'component_missing_n':{c:int(d[c].isna().sum()) for c in COMPONENTS},'characteristics':[]}
        for col in ['r7agey','bmi','chronic_burden','r7casp12']:
            x=d[col].dropna();info[label]['characteristics'].append({'variable':col,'n_available':len(x),'mean':float(x.mean()),'sd':float(x.std(ddof=1))})
        for col,code in [('female',1),('education_level',1),('education_level',2),('education_level',3)]:
            x=d[col].dropna();info[label]['characteristics'].append({'variable':col,'code':code,'n_available':len(x),'n':int(x.eq(code).sum()),'pct':100*float(x.eq(code).mean())})
    n0,n1=len(groups['computable']),len(groups['not_computable'])
    rows.append(['Participants (% of age-eligible N='+f'{len(age):,}'+')',f'{100*n0/len(age):.1f}%',f'{100*n1/len(age):.1f}%'])
    dist=info['not_computable']['component_observation_counts']
    rows.append(['Score components observed in noncomputable group','—','; '.join(f'{i}: {dist[str(i)]:,} ({100*dist[str(i)]/n1:.1f}%)' for i in range(3))])
    for col,label in zip(COMPONENTS,['Childhood-care history missing in noncomputable group','Regular-care continuity component missing in noncomputable group','Late uptake or non-continuous regular care component missing in noncomputable group','Lifetime cost-related postponement component missing in noncomputable group']):
        n=info['not_computable']['component_missing_n'][col];rows.append([label,'—',f'{n:,} ({100*n/n1:.1f}%)'])
    rows.append(['Available-case characteristics (unweighted)','',''])
    specs=[('r7agey',None,'Age, years; mean (SD)'),('female',1,'Female sex, n (%)'),('education_level',1,'Education category 1 (lower), n (%)'),('education_level',2,'Education category 2 (middle), n (%)'),('education_level',3,'Education category 3 (higher), n (%)'),('bmi',None,'BMI, kg/m²; mean (SD)'),('chronic_burden',None,'Chronic disease burden; mean (SD)'),('r7casp12',None,'Wave 7 CASP-12; mean (SD)')]
    for var,code,label in specs:
        vals=[]
        for g in info:
            r=next(x for x in info[g]['characteristics'] if x['variable']==var and x.get('code')==code)
            vals.append(f"{r['mean']:.2f} ({r['sd']:.2f}); n={r['n_available']:,}" if code is None else f"{r['n']:,} ({r['pct']:.1f}%)")
        rows.append([label,*vals])
    rendered=pd.DataFrame(rows,columns=['Characteristic',f'Computable score\n(n={n0:,})',f'Score not computable\n(n={n1:,})'])
    availability={'harmonized_n':len(share),'age50_n':len(age),'computable_all_records_n':int(share.disadvantage_score.notna().sum()),'wave7_wave8_casp_observed_n':int(share[['r7casp12','r8casp12']].notna().all(axis=1).sum()),'wave7_wave8_loneliness_observed_n':int(share[['r7lnlys3','r8lnlys3']].notna().all(axis=1).sum()),'casp_completecase_n':len(casp),'loneliness_primary_n':len(primary)}
    observed={}
    numeric=[]
    variables=[*COMPONENTS,'disadvantage_score','r7agey','female','education_level','married_partnered','bmi','chronic_burden','r8lnlys3','r8casp12','r8adla','r8iadla','r6_smoke_ever','r6_drink_freq','r6eurod','r6lnlys3']
    for g in ['overall','low_0_1','mid_2','high_3_4']:
        d=primary if g=='overall' else primary.loc[primary.disadvantage_group.eq(g)]
        observed[g]={c:int(d[c].notna().sum()) for c in variables}
        for c in variables:
            numeric.append({'group':g,'variable':c,'n_available':observed[g][c],'weighted_mean':weighted_mean(d[c],d.r8wtresp),'weighted_sd':weighted_sd(d[c],d.r8wtresp)})
    return {'availability':availability,'score_computability':info,'score_computability_table':rendered.to_dict('records'),'primary_available_case_denominators':observed,'primary_descriptive_unrounded':numeric},rendered
