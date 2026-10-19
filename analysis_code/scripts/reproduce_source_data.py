"""Recompute all existing aggregate source data from restricted cohort inputs.

Uses the established WLS/HC3 specifications, sample definitions and presentation
schemas. No participant-level outputs are written. Inputs/outputs are configured
with flags or config.paths; no private absolute path is required.
"""
from __future__ import annotations
import argparse
import json
import re
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import statsmodels
import statsmodels.formula.api as smf
from patsy import build_design_matrices
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from config.paths import PATHS
from scripts.build_analysis_inputs import COMPONENTS, BARRIERS
from scripts.statistical_helpers import positive_cost_burden
from scripts.descriptive_helpers import summarize_table1, weighted_mean, weighted_sd
from scripts.supplementary_descriptives import summarize as supplementary_descriptives
from scripts.model_diagnostics import diagnose_fit

GROUPS = ['low_0_1','mid_2','high_3_4']
GT = "C(disadvantage_group, Treatment(reference='low_0_1'))"
MID, HIGH = GT+'[T.mid_2]', GT+'[T.high_3_4]'
CV = ['r7agey','female','education_level','bmi','chronic_burden','country']
ADJ = 'r7agey + female + education_level + bmi + chronic_burden + C(country)'
FORMULA = 'r8lnlys3 ~ '+GT+' + '+ADJ
R6 = ['married_partnered','r6_smoke_ever','r6_drink_freq','r6eurod','r6lnlys3']

def dump(path, data):
    # JSON permits neither NaN nor numpy scalars in downstream consumers.
    def default(v):
        if isinstance(v, np.generic): return v.item()
        if isinstance(v, Path): return str(v)
        raise TypeError(type(v).__name__)
    data=json.loads(json.dumps(data,default=default))
    def clean(x):
        if isinstance(x,float) and not np.isfinite(x):return None
        if isinstance(x,dict):return {k:clean(v) for k,v in x.items()}
        if isinstance(x,list):return [clean(v) for v in x]
        return x
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(clean(data),ensure_ascii=False,indent=2,allow_nan=False))

def pf(p):return 'Not estimable' if not np.isfinite(p) else ('<0.001' if p < .001 else f'{p:.3f}')
def ci(r):return 'Not estimable' if not np.isfinite(r['estimate']) else f"{r['estimate']:.3f} ({r['lcl']:.3f}, {r['ucl']:.3f})"
def complete(d,cols,weight='r8wtresp'):
    return d.dropna(subset=list(dict.fromkeys([*cols,weight]))).loc[lambda x:x[weight]>0].copy()
def term_result(fit,term):
    if term in getattr(fit,'nonestimable_terms',set()):
        return dict(estimate=np.nan,std_error=np.nan,lcl=np.nan,ucl=np.nan,p_value=np.nan,n=int(fit.nobs))
    v=fit.conf_int().loc[term]
    return dict(estimate=float(fit.params[term]),std_error=float(fit.bse[term]),lcl=float(v.iloc[0]),ucl=float(v.iloc[1]),p_value=float(fit.pvalues[term]),n=int(fit.nobs))
def set_result(df,i,r):
    mapping={'estimate':'estimate','coef':'estimate','std_error':'std_error','std_err':'std_error','lcl':'lcl','ci_low':'lcl','ucl':'ucl','ci_high':'ucl','p_value':'p_value','n':'n'}
    for c,key in mapping.items():
        if c in df:df.at[i,c]=r[key]

def run(inputs,template_dir,output_dir,correct_metadata=True):
    output_dir.mkdir(parents=True,exist_ok=True)
    original={p.name:pd.read_csv(p) for p in template_dir.glob('*.csv')}
    out={k:v.copy() for k,v in original.items()}
    def table(name):return out[name+'.csv']
    share_path=inputs/'share_analysis_dataset.csv' if inputs is not None else PATHS.share_analytic
    s=pd.read_csv(share_path,low_memory=False)
    s['disadvantage_group']=pd.Categorical(s['disadvantage_group'],GROUPS,ordered=True)
    a=complete(s.loc[s.analysis_eligible_loneliness.eq(1)],[*CV,'disadvantage_group','r8lnlys3'])
    casp=complete(s.loc[s.analysis_eligible_casp.eq(1)],[*CV,'disadvantage_group','r7casp12','r8casp12'])
    allfour=a.dropna(subset=COMPONENTS).copy()
    fixed=a.dropna(subset=R6).copy()
    fits={}; records=[]; spec=[]
    def fit(name,d,formula=FORMULA,weight='r8wtresp'):
        f=smf.wls(formula,data=d,weights=d[weight]).fit(cov_type='HC3')
        fits[name]=f
        diagnostics=diagnose_fit(f,d,weight)
        spec.append(dict(model=name,formula=formula,weight=weight,covariance='HC3',**diagnostics))
        for t in f.params.index:records.append(dict(model=name,term=t,**term_result(f,t)))
        return f
    def res(name,t):return term_result(fits[name],t)
    fit('primary',a)
    fit('perpoint',a,'r8lnlys3 ~ disadvantage_score + '+ADJ)
    five=a.copy();five['disadvantage_score']=pd.Categorical(five.disadvantage_score.astype(int),[0,1,2,3,4],ordered=True)
    fit('score_0_4',five,'r8lnlys3 ~ C(disadvantage_score, Treatment(reference=0)) + '+ADJ)
    fit('allfour',allfour)
    fit('casp',casp,'r8casp12 ~ '+GT+' + r7casp12 + '+ADJ)
    fit('joint_loneliness',allfour,'r8lnlys3 ~ '+' + '.join(COMPONENTS)+' + '+ADJ)
    fit('joint_casp',casp.dropna(subset=COMPONENTS),'r8casp12 ~ '+' + '.join(COMPONENTS)+' + r7casp12 + '+ADJ)
    fit('M1_core',a,'r8lnlys3 ~ '+GT+' + r7agey + female + C(country)')
    fits['M2_primary']=fits['primary']
    fit('M3_marital',a.dropna(subset=['married_partnered']),FORMULA+' + married_partnered')
    for i,extra in enumerate(['',' + r6_smoke_ever + r6_drink_freq',' + r6_smoke_ever + r6_drink_freq + r6eurod',' + r6_smoke_ever + r6_drink_freq + r6eurod + r6lnlys3']):
        fit(f'R6_B{i}',fixed,FORMULA+' + married_partnered'+extra)
    for age in [65,75]:fit('age_'+str(age),a.loc[a.r7agey.ge(age)])
    for label,d,drop in [('male',a.loc[a.female.eq(0)],'female'),('female',a.loc[a.female.eq(1)],'female'),('lower',a.loc[a.education_level.le(2)],'education_level'),('higher',a.loc[a.education_level.gt(2)],'education_level')]:
        fit('subgroup_'+label,d,FORMULA.replace(' + '+drop,''))
    barrier=complete(a.loc[a.disadvantage_score.ge(2)],list(BARRIERS))
    for b in BARRIERS:fit(b,barrier,'r8lnlys3 ~ '+b+' + '+ADJ)
    labels=table('supplementary_figure_s2_leave_one_country_out')[['omitted_country_code','omitted_country_label']].drop_duplicates()
    for row in labels.itertuples(index=False):
        code=int(row.omitted_country_code)
        d=a.loc[a.country.eq(code)]
        fit('country_'+str(code),d,FORMULA.replace(' + C(country)',''))
        fit('leaveout_'+str(code),a.loc[a.country.ne(code)])
    print(f'SHARE models fitted: primary N={len(a)}, allfour N={len(allfour)}, fixed R6 N={len(fixed)}',flush=True)
    external=[]
    for cohort,w in [('CHARLS',2),('KLoSA',7)]:
        external_path=(inputs/('charls_context_dataset.csv' if cohort=='CHARLS' else 'klosa_context_dataset.csv')) if inputs is not None else (PATHS.charls_analytic if cohort=='CHARLS' else PATHS.klosa_analytic)
        d=pd.read_csv(external_path,low_memory=False)
        if cohort=='CHARLS':d=d.loc[d.age_r2.ge(45)].copy()
        d[f'high_oopden_r{w}'],q=positive_cost_burden(d[f'oopden_r{w}'])
        check=dict(cohort=cohort,threshold_population='CHARLS age >=45 before complete-case filtering' if w==2 else 'All KLoSA input records before complete-case filtering',threshold_method='Unweighted pandas linear-interpolated 75th percentile among strictly positive costs',population_n=len(d),positive_cost_n=int(d[f'oopden_r{w}'].gt(0).sum()),threshold=q,education_actual=sorted(d.education_level.dropna().unique().tolist()),models=[])
        if w==2:check['data_version']='Version D, June 2021';check['education_label_0_used']=bool(d.education_level.eq(0).any())
        cov=[f'age_r{w}','female','education_level','married_partnered','bmi','current_smoker','drink_level']
        for exp in [f'high_oopden_r{w}',f'no_dental_visit_r{w}']:
            for follow,base in [(f'flonel_r{w+1}',f'flonel_r{w}'),(f'cesd10_r{w+1}',f'cesd10_r{w}')]:
                sub=complete(d,[exp,follow,base,*cov],f'weight_r{w}')
                name=cohort+'_'+exp+'_'+follow
                f=fit(name,sub,follow+' ~ '+exp+' + '+base+' + '+' + '.join(cov),f'weight_r{w}')
                check['models'].append(dict(outcome=follow,exposure=exp,n=len(sub),high_or_exposed_n=int(sub[exp].eq(1).sum()),reference_n=int(sub[exp].eq(0).sum()),design_rank=int(np.linalg.matrix_rank(f.model.exog)),design_columns=f.model.exog.shape[1],full_rank=bool(np.linalg.matrix_rank(f.model.exog)==f.model.exog.shape[1]),**{'result':res(name,exp)}))
        external.append(check)
    dump(output_dir/'external_group_checks.json',external)
    # Main model and sensitivity source tables retain their established schemas.
    d=table('figure_2_primary_models')
    for i,(name,t) in enumerate([('primary',MID),('primary',HIGH),('perpoint','disadvantage_score')]):
        r=res(name,t);set_result(d,i,r);d.at[i,'value_label']=ci(r)+'; P '+('' if r['p_value']<.001 else '= ')+pf(r['p_value'])
    d=table('share_all_four_exposure_components_sensitivity')
    for i,t in enumerate([MID,HIGH]):set_result(d,i,res('allfour',t))
    d=table('share_age_threshold_sensitivity')
    for i in d.index:set_result(d,i,res('age_'+('65' if '65' in d.at[i,'sample'] else '75'),d.at[i,'term']))
    d=table('figure_2_attenuation');ladder=['M1_core','M2_primary','M3_marital','R6_B0','R6_B1','R6_B2','R6_B3']
    for i in d.index:
        r=res(ladder[int(d.at[i,'model_order'])],HIGH if d.at[i,'contrast'].startswith('High') else MID)
        set_result(d,i,r);d.at[i,'value_text']=ci(r)
    d=table('figure_2_score_specification')
    for i in d.index:
        score=int(d.at[i,'score']);r=res('score_0_4',f'C(disadvantage_score, Treatment(reference=0))[T.{score}]')
        set_result(d,i,r);d.at[i,'value_text']=round(r['estimate'],3)
        sub=a.loc[a.disadvantage_score.eq(score)];d.at[i,'n_support']=len(sub);d.at[i,'weighted_share_pct']=100*sub.r8wtresp.sum()/a.r8wtresp.sum()
    code_map=dict(zip(labels.omitted_country_label,labels.omitted_country_code))
    for name in ['figure_2_country_specific','figure_2_country_variability']:
        d=table(name)
        for i in d.index:
            r=res('country_'+str(int(code_map[d.at[i,'country_label']])),HIGH)
            set_result(d,i,r);d.at[i,'positive']=r['estimate']>0;d.at[i,'significant_positive']=r['lcl']>0
        d=d.sort_values('estimate').reset_index(drop=True);d['sort_order']=range(len(d));out[name+'.csv']=d
    cs=table('figure_2_country_specific')
    table('figure_2_country_variability_summary')['value']=[len(cs),int(cs.positive.sum()),int(cs.significant_positive.sum())]
    d=table('supplementary_figure_s2_leave_one_country_out')
    for i in d.index:
        t=HIGH if d.at[i,'contrast'].startswith('High') else MID
        r=res('leaveout_'+str(int(d.at[i,'omitted_country_code'])),t);set_result(d,i,r)
        # Preserve the original mean-of-leaveout-estimates reference.
        ref=float(np.mean([res('leaveout_'+str(int(code)),t)['estimate'] for code in labels.omitted_country_code]));d.at[i,'pooled_reference']=ref;d.at[i,'delta_from_pooled']=r['estimate']-ref
    d=table('supplementary_figure_s3_subgroups')
    for i in d.index:set_result(d,i,res('subgroup_'+d.at[i,'subgroup_label'],HIGH if d.at[i,'contrast'].startswith('High') else MID))
    d=table('supplementary_figure_s4_components_joint')
    for i in d.index:set_result(d,i,res('joint_loneliness' if d.at[i,'outcome_label']=='Loneliness' else 'joint_casp',COMPONENTS[int(d.at[i,'sort_order'])]))
    d=table('share_barrier_models')
    for i,b in enumerate(BARRIERS):
        r=res(b,b);set_result(d,i,{k:(round(v,3) if k!='n' else v) for k,v in r.items()})
    d=table('supplementary_figure_s5_cross_cohort_context_checks')
    for i in d.index:
        co=d.at[i,'dataset'];w=2 if co=='CHARLS' else 7
        exp=('high_oopden_r' if d.at[i,'display_label'].startswith('High') else 'no_dental_visit_r')+str(w)
        outcome=('flonel_r' if d.at[i,'outcome_label']=='Loneliness' else 'cesd10_r')+str(w+1)
        r=res(co+'_'+exp+'_'+outcome,exp)
        # This pre-existing source row is reported at three decimals.
        if co=='KLoSA' and exp.startswith('high') and outcome.startswith('flonel'):
            r={k:(round(v,3) if k!='n' else v) for k,v in r.items()}
        set_result(d,i,r)
    # Empirical marginal means standardize over the entire weighted primary frame.
    f=fits['primary'];d=table('figure_2_adjusted_distribution')
    for i,g in enumerate(GROUPS):
        cf=a.copy();cf['disadvantage_group']=g
        x=np.asarray(build_design_matrices([f.model.data.design_info],cf)[0]);v=np.average(x,axis=0,weights=a.r8wtresp)
        mu=float(v@f.params);se=float(np.sqrt(v@f.cov_params()@v))
        sub=a.loc[a.disadvantage_group.eq(g)];vals=sub.r8lnlys3.to_numpy();w=sub.r8wtresp.to_numpy();order=np.argsort(vals)
        qs=np.interp([.25,.5,.75],(np.cumsum(w[order])-.5*w[order])/w.sum(),vals[order])
        d.loc[i,['adjusted_mean_loneliness','ci_low','ci_high','weighted_median','weighted_iqr_low','weighted_iqr_high','n','weighted_share_pct']]=[mu,mu-1.96*se,mu+1.96*se,qs[1],qs[0],qs[2],len(sub),100*w.sum()/a.r8wtresp.sum()]
    support=[]
    for g in GROUPS:
        sub=a.loc[a.disadvantage_group.eq(g)]
        for val,part in sub.groupby('r8lnlys3'):
            support.append([g,val,len(part),part.r8wtresp.sum(),100*part.r8wtresp.sum()/sub.r8wtresp.sum()])
    out['figure_2_outcome_support_distribution.csv']=pd.DataFrame(support,columns=table('figure_2_outcome_support_distribution').columns)
    # Descriptive summaries, with the original population-weighted variances.
    a['country_code']=a.country.astype(int)
    full=summarize_table1(a.copy());full.to_csv(output_dir/'share_table1_full.csv',index=False)
    if 'share_table1_full.csv' in out:out['share_table1_full.csv']=full.copy()
    lookup=full.set_index('Characteristic')
    aliases={'Late uptake or non-continuous regular care, %':'Late/absent uptake of regular care, %','Age 65 years or older, %':'Age >=65 years, %','Body mass index':'BMI, kg/m2','BMI 30 or higher, %':'BMI >=30 kg/m2, %'}
    d=table('table_1_source')
    for i in d.index:
        key=aliases.get(d.at[i,'Characteristic'],d.at[i,'Characteristic'])
        if key not in lookup.index:continue
        for c in d.columns[1:]:
            val=str(lookup.at[key,c])
            if '(' in val:
                dec=2 if key in ['Mean disadvantage score','Education level, mean (SD)','Chronic disease burden','Wave 8 loneliness'] else 1
                raw_col={'Mean disadvantage score':'disadvantage_score','Age, years':'r7agey','Education level, mean (SD)':'education_level','BMI, kg/m2':'bmi','Chronic disease burden':'chronic_burden','Wave 8 loneliness':'r8lnlys3'}[key]
                part=a if c=='Overall' else a.loc[a.disadvantage_group.eq(GROUPS[list(d.columns[2:]).index(c)])]
                val=f'{weighted_mean(part[raw_col],part.r8wtresp):.{dec}f} ({weighted_sd(part[raw_col],part.r8wtresp):.{dec}f})'
            d.at[i,c]=val
    d=table('supplementary_figure_s4_component_prevalence')
    for i in d.index:
        key=d.at[i,'source_table_characteristic'];key=aliases.get(key,key)
        d.at[i,'weighted_prevalence_pct']=float(lookup.at[key,'Overall'])
    ed=[]
    for e,stratum in a.groupby('education_level'):
        for g,sub in stratum.groupby('disadvantage_group',observed=True):ed.append([int(e),str(g),len(sub),100*sub.r8wtresp.sum()/stratum.r8wtresp.sum(),weighted_mean(sub.r8lnlys3,sub.r8wtresp)])
    out['share_education_by_disadvantage.csv']=pd.DataFrame(ed,columns=table('share_education_by_disadvantage').columns)
    d=table('share_postponement_count_audit');low=a.loc[a.disadvantage_group.eq('low_0_1') & a.disadv_postponed.eq(1)];count=low.rh789_.where(lambda v:v.ge(0)).dropna()
    d.loc[0,['n_postponers','n_count_observed','count_median','count_q25','count_q75','raw_zero_n','raw_999_n']]=[len(low),len(count),count.median(),count.quantile(.25),count.quantile(.75),count.eq(0).sum(),count.eq(999).sum()]
    out['share_component_observation_support.csv']=a.groupby(['disadvantage_component_nonmissing','disadvantage_group'],observed=True).agg(n=('disadvantage_score','size'),never_regular_n=('rh015_',lambda v:int(v.eq(5).sum()))).reset_index()
    # Missingness denominators remain all harmonized records, as in the original.
    missing_cols=['disadv_childhood','disadvantage_group','disadvantage_score','disadv_late_uptake','disadv_adult_pattern','disadv_postponed','r7lnlys3','r8casp12','r8lnlys3','r7casp12','current_smoker','drink_freq','bmi','chronic_burden','married_partnered','r7agey','education_level','female','r8wtresp']
    d=table('supplementary_figure_s1_missingness')
    for i,col in enumerate(missing_cols):
        n=int(s[col].isna().sum());d.loc[i,['n_total','missing_n','missing_pct','missing_pct_display']]=[len(s),n,n/len(s),100*n/len(s)]
    d['missing_bin']=pd.cut(d.missing_pct_display,[-.1,5,25,50,75,100],labels=['0-5','5-25','25-50','50-75','75-100'])
    age=s.loc[s.r7agey.ge(50)];base=age.loc[age.disadvantage_score.notna()];outcome=base.loc[base.r8lnlys3.notna()]
    retained=base.loc[base.analysis_eligible_loneliness.eq(1)];dropped=base.loc[base.analysis_eligible_loneliness.ne(1)]
    d=table('supplementary_figure_s1_attrition')
    for i,col in enumerate(['r7agey','female','education_level','married_partnered','bmi','chronic_burden','r7casp12','r7lnlys3']):
        x=retained[col].dropna();y=dropped[col].dropna();mx=x.mean();my=y.mean()
        binary=set(x.unique()).issubset({0,1}) and set(y.unique()).issubset({0,1})
        den=np.sqrt((mx*(1-mx)+my*(1-my))/2) if binary else np.sqrt((x.var(ddof=1)+y.var(ddof=1))/2)
        d.loc[i,['retained_n','not_retained_n','retained_mean_or_prop','not_retained_mean_or_prop','standardized_difference']]=[len(x),len(y),mx,my,(mx-my)/den if den else np.nan]
    counts=[len(s),len(age),len(base),len(outcome),len(a),int(base.r7lnlys3.notna().sum())]
    d=table('figure_1_sample_flow');d['n']=counts
    for i,prefix in [(1,'Age criterion not met or age unavailable'),(2,'Incomplete disadvantage score'),(3,'No linked Wave 8 loneliness outcome'),(4,'Missing respondent weight or model covariates')]:d.at[i,'exclusion_or_note']=f'{prefix}; n={counts[i-1]-counts[i]:,}'
    table('figure_1_wave7_overlap_check')['n']=[len(base),int(base.r7lnlys3.notna().sum()),len(outcome),int(base[['r7lnlys3','r8lnlys3']].notna().all(axis=1).sum()),len(a)]
    # Table 2 reuses exactly the fitted estimates used above, retaining row roles.
    d=table('table_2_source');rowfits={1:('primary',MID),2:('primary',HIGH),3:('perpoint','disadvantage_score'),10:('allfour',MID),11:('allfour',HIGH),13:('M1_core',HIGH),14:('primary',HIGH),15:('M3_marital',HIGH),16:('R6_B3',HIGH),17:('age_65',MID),18:('age_65',HIGH),19:('age_75',MID),20:('age_75',HIGH),22:('subgroup_lower',HIGH),23:('subgroup_higher',HIGH)}
    for score in [1,2,3,4]:
        rowfits[4+score]=('score_0_4',f'C(disadvantage_score, Treatment(reference=0))[T.{score}]')
        sub=a.loc[a.disadvantage_score.eq(score)];d.at[4+score,'Analysis']=f'Score {score} vs 0 (n={len(sub):,}; {100*sub.r8wtresp.sum()/a.r8wtresp.sum():.1f}%)'
    for i,b in enumerate(BARRIERS):rowfits[24+i]=(b,b)
    for i,(co,w,exp) in enumerate([('CHARLS',2,'high_oopden'),('CHARLS',2,'no_dental_visit'),('KLoSA',7,'high_oopden'),('KLoSA',7,'no_dental_visit')]):
        term=exp+'_r'+str(w);rowfits[27+i]=(co+'_'+term+'_flonel_r'+str(w+1),term)
    for i,(name,t) in rowfits.items():
        r=res(name,t);d.loc[i,['Estimate','P value','N']]=[ci(r),pf(r['p_value']),f"{r['n']:,}"]
    # Auditable aggregate details for missing/noncomputable denominators.
    detail=dict(primary_n=len(a),allfour_n=len(allfour),casp_n=len(casp),r6_fixed_n=len(fixed),barrier_n=len(barrier),flow=dict(zip(['all','age50','computable','outcome','primary','wave7_overlap'],counts)),primary_group_counts={g:int(a.disadvantage_group.eq(g).sum()) for g in GROUPS},primary_score_counts={str(i):int(a.disadvantage_score.eq(i).sum()) for i in range(5)},country_signcounts=dict(country_count=len(cs),positive=int(cs.positive.sum()),positive_ci_excludes_zero=int(cs.significant_positive.sum())),component_nonmissing_all=s.disadvantage_component_nonmissing.value_counts().sort_index().to_dict(),component_nonmissing_age50=age.disadvantage_component_nonmissing.value_counts().sort_index().to_dict(),noncomputable_age50_n=int(age.disadvantage_score.isna().sum()),noncomputable_age50_components_missing=age.loc[age.disadvantage_score.isna(),COMPONENTS].isna().sum().to_dict(),missing_primary_fields_outcome_available={c:int(outcome[c].isna().sum()) for c in [*CV,'r8wtresp']},nonpositive_weight_outcome_available=int(outcome.r8wtresp.le(0).sum()),education_means={g:weighted_mean(a.loc[a.disadvantage_group.eq(g),'education_level'],a.loc[a.disadvantage_group.eq(g),'r8wtresp']) for g in GROUPS},r7_boundary_observed={c:int(base[c].notna().sum()) for c in ['r7smoken','r7drinkxw','r7eurod','r7lnlys3']},software={'python':sys.version.split()[0],'numpy':np.__version__,'pandas':pd.__version__,'statsmodels':statsmodels.__version__})
    detail['models']=records;detail['model_specs']=spec;detail['table1_full']=full.to_dict('records');detail['external_group_checks']=external
    detail['education_by_disadvantage']=table('share_education_by_disadvantage').to_dict('records');detail['missingness']=table('supplementary_figure_s1_missingness').to_dict('records');detail['attrition']=table('supplementary_figure_s1_attrition').to_dict('records');detail['adjusted_distribution']=table('figure_2_adjusted_distribution').to_dict('records')
    extra,computability_table=supplementary_descriptives(s,a,casp)
    detail.update(extra)
    computability_table.to_csv(output_dir/'share_score_computability.csv',index=False)
    dump(output_dir/'results.json',detail)
    if correct_metadata:
        boundary=table('figure_1_operational_boundary')
        boundary.loc[boundary.definition.eq('No regular childhood dental care'),'variable_name']='rh015_; rh016_; rh018_'
        d=table('supplementary_variable_mapping')
        mask=d.Dataset.eq('SHARE') & d.Construct.eq('Childhood dental care')
        # Preserve the existing construct label and template schema.
        if not mask.any():
            mask=d.Dataset.eq('SHARE') & d['Variable name(s)'].eq('rh016_')
        d.loc[mask,'Variable name(s)']='rh015_; rh016_; rh018_ (raw blank indicators retained)'
        d.loc[mask,'Derivation']='Adverse=1 for rh016_=5 or verified structural nonadministration of rh016_ following rh015_=5. The structural branch requires original blank rh016_ and rh018_ cells, with no contradictory observed responses. Adverse=0 for rh016_=1.'
        d.loc[mask,'Missingness criteria']='True DK, refusal, unknown and other missing responses remain missing. A cleaned NaN alone is not structural-skip evidence.'
        d.loc[d['Construct'].eq('Adult regular-care pattern'),'Derivation']='Adverse=1 if rh015_=5 or rh018_=5; 0 only if rh015_=1 and rh018_=1; otherwise missing. RH018 denotes continuity since initiation.'
        d.loc[d['Construct'].eq('Adult regular-care pattern'),'Missingness criteria']='Unknown or missing responses remain missing unless an observed source response identifies the component as adverse.'
        mask=d['Construct'].eq('Late uptake or non-continuous regular care')
        d.loc[mask,'Variable name(s)']='rh015_; rh016_; rh017_; rh018_; rabyear'
        d.loc[mask,'Derivation']='Valid start age=rh017_-rabyear in 0-100 years. Adverse=1 if valid start age>25, rh015_=5 or rh018_=5; 0 if (rh016_=1 or valid start age<=25) and rh018_=1, provided no adverse criterion applies; otherwise missing. RH017 is structurally skipped after childhood initiation.'
        d.loc[mask,'Missingness criteria']='Invalid start ages <0 or >100 are missing; unknown onset or continuity is not assigned zero.'
        mask=d.Dataset.eq('CHARLS') & d.Construct.eq('Contextual covariates')
        d.loc[mask,'Derivation']=d.loc[mask,'Derivation'].str.replace('education codes 0 none, 1 less than lower secondary,2 upper secondary/vocational,3 tertiary','observed education codes 1 less than lower secondary,2 upper secondary/vocational,3 tertiary',regex=False)
        for co,pop in [('CHARLS','CHARLS respondents aged 45 years or older'),('KLoSA','all KLoSA input records')]:
            mask=d.Dataset.eq(co) & d.Construct.eq('Dental out-of-pocket expenditure')
            for idx in d.index[mask]:
                text=str(d.at[idx,'Derivation'])
                suffix=' Threshold uses the unweighted positive-cost distribution among '+pop+' before outcome-specific complete-case filtering.'
                if suffix not in text:d.at[idx,'Derivation']=text+suffix

    for name,d in out.items():
        if list(d.columns)!=list(original[name].columns):raise AssertionError('Schema changed: '+name)
        d.to_csv(output_dir/name,index=False,encoding='utf-8-sig')
    return detail

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input-dir',type=Path,default=None)
    p.add_argument('--template-dir',type=Path,default=ROOT.parent/'source_data')
    p.add_argument('--output-dir',type=Path,default=PATHS.tables_root/'source_data')
    p.add_argument('--legacy-metadata',action='store_true',help='For historical baseline verification only; keep the template metadata verbatim.')
    a=p.parse_args();run(a.input_dir,a.template_dir,a.output_dir,correct_metadata=not a.legacy_metadata)
if __name__=='__main__':main()
