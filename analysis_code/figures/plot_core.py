"""Shared plotting helpers for aggregate manuscript data."""
from pathlib import Path


import argparse, hashlib, json, re, sys


import matplotlib as mpl


import matplotlib.pyplot as plt


import matplotlib.patheffects as pe


from matplotlib.lines import Line2D


from matplotlib.patches import PathPatch, FancyArrowPatch


from matplotlib.path import Path as MplPath


from matplotlib.transforms import Bbox


from matplotlib.text import Text


import numpy as np


import pandas as pd


from PIL import Image


HERE=Path(__file__).parent


SIZES={'Figure_1_EJPH':(4458,4540),'Figure_2_EJPH':(4152,5473),
       'Supplementary_Figure_S1_EJPH':(4823,3201),'Supplementary_Figure_S2_EJPH':(4296,3535),
       'Supplementary_Figure_S3_EJPH':(4350,2141),'Supplementary_Figure_S4_EJPH':(4383,2599),
       'Supplementary_Figure_S5_EJPH':(4338,3003)}


ACTIVE={}; REPORT={}; FIGURES={}; BASE_BOX={}


ACTIVE={}; REPORT={}; FIGURES={}; BASE_BOX={}


ACTIVE={}; REPORT={}; FIGURES={}; BASE_BOX={}


ACTIVE={}; REPORT={}; FIGURES={}; BASE_BOX={}


sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()


def style():
    mpl.rcParams.update({'font.family':'sans-serif','font.sans-serif':['Arial','Helvetica','DejaVu Sans'],
        'svg.fonttype':'none','pdf.fonttype':42,'ps.fonttype':42,'font.size':7,
        'axes.spines.right':False,'axes.spines.top':False,'axes.linewidth':.75,
        'legend.frameon':False,'savefig.facecolor':'white'})


def read_csv(name):
    actual={'supplementary_figure_s5_external_full.csv':'supplementary_figure_s5_cross_cohort_context_checks.csv'}.get(name,name)
    ACTIVE[actual]=sha(SOURCE/actual); d=pd.read_csv(SOURCE/actual)
    if actual=='supplementary_figure_s1_missingness.csv':
        aliases={'no regular childhood dental care':'disadv_childhood','life-course dental-care disadvantage group':'disadvantage_group',
          'life-course dental-care disadvantage score':'disadvantage_score','late uptake or non-continuous regular care':'disadv_late_uptake',
          'no stable adult regular care':'disadv_adult_pattern','lack of continuous regular care':'disadv_adult_pattern',
          'lifetime postponement of dental visits':'disadv_postponed','Wave 7 loneliness score':'r7lnlys3',
          'Wave 8 CASP-12 score':'r8casp12','Wave 8 loneliness score':'r8lnlys3','Wave 7 CASP-12 score':'r7casp12',
          'current smoking':'current_smoker','recent drinking indicator (past 7 days)':'drink_freq','body mass index':'bmi',
          'chronic disease burden':'chronic_burden','married or partnered':'married_partnered','Wave 7 age in years':'r7agey',
          'education level':'education_level','female':'female','Wave 8 respondent weight':'r8wtresp'}
        d['variable']=d.variable.replace(aliases)
    if actual in ['supplementary_figure_s4_component_prevalence.csv','supplementary_figure_s4_components_joint.csv']:
        d['display_label']=d.display_label.replace({'Late uptake or non-continuous care':'Late uptake / never regular'})
    if actual=='supplementary_figure_s5_cross_cohort_context_checks.csv':
        d['display_label']=d.display_label.replace({'High dental out-of-pocket expenditure':'High OOP burden'})
    return d


def numeric_artists(fig):
    """Fingerprint plotted coordinates independently of text and figure size."""
    data=[]
    for ax in fig.axes:
        data.append({'lines':[[np.asarray(l.get_xdata(),dtype=float).tolist(),np.asarray(l.get_ydata(),dtype=float).tolist()] for l in ax.lines],
                     'collections':[{'offsets':c.get_offsets().tolist(), 'paths':[p.vertices.tolist() for p in c.get_paths()]} for c in ax.collections],
                     'bars':[[p.get_x(),p.get_y(),p.get_width(),p.get_height()] for p in ax.patches if isinstance(p,mpl.patches.Rectangle)]})
    return hashlib.sha256(json.dumps(data,sort_keys=True,default=lambda x:x.item()).encode()).hexdigest()


def capture(fig, base, *args):
    name=Path(base).name
    # Measure the historical layout before changing any text. Fixed crop dimensions
    # retain the original aspect ratio; no exported image is stretched or squeezed.
    fig.canvas.draw()
    original=json.loads((HERE/'initial_plot_geometry.json').read_text())[name]
    left,bottom=original['spines'][0][0];rect=fig.axes[0].get_position();fw,fh=fig.get_size_inches()
    x0=rect.x0*fw-left/72
    y0=rect.y0*fh-(original['page_pt'][1]-bottom)/72
    BASE_BOX[name]=Bbox.from_bounds(x0,y0,SIZES[name][0]/600,SIZES[name][1]/600)
    FIGURES[name]=fig


def load_module(file):
    env={'Path':Path,'np':np,'pd':pd,'mpl':mpl,'plt':plt,'pe':pe,'Line2D':Line2D,
         'FIG_DIR':OUTPUT,'read_source_csv':read_csv,'save_pub_figure':capture,
         'component_prevalence':lambda:read_csv('supplementary_figure_s4_component_prevalence.csv')}
    exec(compile((HERE/file).read_text(),file,'exec'),env)
    return env


def interval_checks(fig,name):
    checks=[]
    def ck(ax,d,lo,hi,axis='x'):
        lim=sorted(ax.get_xlim() if axis=='x' else ax.get_ylim())
        d=d.dropna(subset=[lo,hi]); assert (d[lo]<=d[hi]).all()
        assert (d[lo]>=lim[0]-1e-10).all() and (d[hi]<=lim[1]+1e-10).all(),(name,'Clipped interval',lim,d[[lo,hi]].min().tolist(),d[[lo,hi]].max().tolist())
        checks.append({'axis':axis,'limits':lim,'n':len(d),'pass':True})
    if name=='Figure_2_EJPH':
        for i,n,lo,hi,axis in [(0,'adjusted_distribution','ci_low','ci_high','y'),(1,'primary_models','lcl','ucl','x'),(2,'score_specification','lcl','ucl','y'),(3,'attenuation','lcl','ucl','x'),(4,'country_variability','lcl','ucl','x')]:
            ck(fig.axes[i],read_csv('figure_2_'+n+'.csv'),lo,hi,axis)
    elif name.endswith(('S2_EJPH','S3_EJPH')):
        s='s2_leave_one_country_out' if 'S2_' in name else 's3_subgroups'
        d=read_csv('supplementary_figure_'+s+'.csv')
        for ax,contrast in zip(fig.axes,['Mid vs low','High vs low']):ck(ax,d[d.contrast.eq(contrast)],'ci_low','ci_high')
    elif 'S4_' in name:
        d=read_csv('supplementary_figure_s4_components_joint.csv')
        for ax,outcome in zip(fig.axes[1:],['Loneliness','CASP-12']):ck(ax,d[d.outcome_label.eq(outcome)],'lcl','ucl')
    elif 'S5_' in name:
        d=read_csv('supplementary_figure_s5_external_full.csv')
        for ax,co,out in zip(fig.axes,['CHARLS','CHARLS','KLoSA','KLoSA'],['Loneliness','CESD-10','Loneliness','CESD-10']):ck(ax,d[d.dataset.eq(co)&d.outcome_label.eq(out)],'lcl','ucl')
    return checks


def expand_corrected_intervals(fig, name):
    """Extend only bounds that would otherwise truncate corrected uncertainty."""
    changed=[]
    def extend(ax, values, axis='x'):
        values=np.asarray(values,dtype=float);values=values[np.isfinite(values)]
        if not len(values):return
        bounds=list(ax.get_xlim() if axis=='x' else ax.get_ylim())
        lo,hi=sorted(bounds);minimum,maximum=float(values.min()),float(values.max())
        if minimum>=lo and maximum<=hi:return
        pad=.04*max(hi-lo, maximum-minimum)
        new=[min(lo,minimum-pad) if minimum<lo else lo,max(hi,maximum+pad) if maximum>hi else hi]
        if bounds[0]>bounds[1]:new.reverse()
        (ax.set_xlim if axis=='x' else ax.set_ylim)(new)
        changed.append({'panel':fig.axes.index(ax),'axis':axis,'before':bounds,'after':new,'reason':'Complete corrected intervals must remain visible.'})
    if name=='Figure_2_EJPH':
        for i,n,lo,hi,axis in [(0,'adjusted_distribution','ci_low','ci_high','y'),(1,'primary_models','lcl','ucl','x'),(2,'score_specification','lcl','ucl','y'),(3,'attenuation','lcl','ucl','x'),(4,'country_variability','lcl','ucl','x')]:
            d=read_csv('figure_2_'+n+'.csv');extend(fig.axes[i],d[[lo,hi]].to_numpy().ravel(),axis)
    elif name.endswith(('S2_EJPH','S3_EJPH')):
        suffix='s2_leave_one_country_out' if 'S2_' in name else 's3_subgroups'
        d=read_csv('supplementary_figure_'+suffix+'.csv')
        for ax,c in zip(fig.axes,['Mid vs low','High vs low']):extend(ax,d.loc[d.contrast.eq(c),['ci_low','ci_high']].to_numpy().ravel())
    elif 'S4_' in name:
        d=read_csv('supplementary_figure_s4_components_joint.csv')
        for ax,o in zip(fig.axes[1:],['Loneliness','CASP-12']):extend(ax,d.loc[d.outcome_label.eq(o),['lcl','ucl']].to_numpy().ravel())
        extend(fig.axes[0],read_csv('supplementary_figure_s4_component_prevalence.csv').weighted_prevalence_pct.to_numpy())
    for ax in fig.axes:
        lo,hi=sorted(ax.get_xlim())
        if lo>0 or hi<0:
            for line in ax.lines:
                x=np.asarray(line.get_xdata(),dtype=float);y=np.asarray(line.get_ydata(),dtype=float)
                if len(x)==2 and np.all(x==0) and np.array_equal(y,[0,1]) and line.get_transform()==ax.get_xaxis_transform():
                    line.set_visible(False)
    return changed


def refine(fig,name):
    changes=[]
    if name=='Figure_2_EJPH':
        a,b,c,d,e=fig.axes
        for t in a.texts:
            if t.get_text().startswith('Horizontal marks:'):
                t.set_position((0,-.59));t.set_ha('left');t.set_va('top')
            elif '%; n = ' in t.get_text():t.set_y(-.43)
        for ax in [b,c]:
            for t in ax.texts:
                if t.get_text() in ['B','C']:t.set_y(1.36)
        for t in b.texts:
            if re.fullmatch(r'-?\d+\.\d{3}',t.get_text()):
                t.set_transform(b.get_yaxis_transform());t.set_x(1.035);t.set_ha('left')
        for t in fig.axes[2].texts:
            if t.get_text().startswith('Pale bars'):
                s=read_csv('figure_2_score_specification.csv').set_index('score')
                t.set_text(f'Pale bars show weighted score support; score 4 = {s.loc[4,"weighted_share_pct"]:.1f}%')
        for t in fig.axes[3].texts:
            if t.get_text()=='Wave 6 proxy subset':
                d=read_csv('figure_2_attenuation.csv');ns=d.loc[d.model_label.eq('R6 bridge'),'n'].unique();assert len(ns)==1
                t.set_text(f'Shaded rows: fixed Wave 6 subset (n = {int(ns[0]):,})')
                t.set_transform(fig.axes[3].transAxes);t.set_position((0,-.63));t.set_va('top')
        c=read_csv('figure_2_country_variability.csv')
        for t in fig.axes[4].texts:
            if t.get_text().startswith('25/26'):t.set_text(f'{int((c.estimate>0).sum())}/{len(c)} estimates > 0; {int(((c.lcl>0)|(c.ucl<0)).sum())}/{len(c)} CIs exclude 0')
            elif t.get_text().startswith('pooled '):
                t.set_transform(e.transAxes);t.set_position((.99,1.075));t.set_ha('right');t.set_va('bottom')
        # Tighten the country panel without changing any estimate or interval.
        e.set_xlim(-.32, .40)
        e.set_xticks([-.30, -.20, -.10, .00, .10, .20, .30, .40])
        changes.append('Panel E x range -0.32 to 0.40 retains zero and all 26 complete confidence intervals; original panel geometry is unchanged.')
        changes.append('Original A / B-C / D / E arrangement; current observed support and fixed Wave 6 sample retained.')
    if 'S1_' in name:
        ax=fig.axes[0];labs=[t.get_text().replace('No stable adult regular care','Lack of continuous regular care').replace('Late or absent uptake','Late/non-continuous care') for t in ax.get_yticklabels()]
        ax.set_yticklabels(labs)
        for t in ax.texts:
            if re.fullmatch(r'\d+\.\d',t.get_text()):
                val=float(t.get_text());x,y=t.get_position()
                if val>90:t.set_x(val-2);t.set_ha('right');t.set_color('white')
                elif 56<val<60:t.set_x(61.2)
        for t in fig.axes[1].texts:
            if re.fullmatch(r'0\.\d{3}',t.get_text()):
                val=float(t.get_text())
                if val>.15:t.set_x(val-.008);t.set_ha('right');t.set_color('white')
                elif .045<val<.06:t.set_x(.108)
        changes.append('Updated continuous-care terminology in original horizontal layout; top-14 missingness rule retained.')
    if 'S2_' in name:
        for ax in fig.axes:
            for t in ax.texts:
                if t.get_text().startswith('largest |delta|'):
                    t.set_position((0,1.005));t.set_ha('left');t.set_va('bottom')
                elif t.get_text().startswith('LOO mean '):
                    t.set_transform(ax.transAxes);t.set_position((1,1.005));t.set_ha('right');t.set_va('bottom')
        changes.append('Mean-of-LOO and largest-delta notes occupy the existing gap below each panel title, clear of intervals.')
    if 'S3_' in name:
        ax=fig.axes[0]; ax.set_yticklabels([t.get_text().replace('Lower education','Non-higher\neducation') for t in ax.get_yticklabels()])
        changes.append('Non-higher education label wraps locally; all subgroup intervals and sample sizes updated.')
    if 'S4_' in name:
        # Available-case prevalence denominators were independently verified from
        # restricted inputs; only aggregate counts accompany this plotting code.
        meta=json.loads((HERE/'component_prevalence_denominators.json').read_text())
        assert meta['source_data_sha256']==sha(SOURCE/'supplementary_figure_s4_component_prevalence.csv')
        den=meta['denominators']
        labels=['No regular childhood care','Lack of continuous\nregular care','Late/non-continuous care','Lifetime postponement']
        fig.axes[0].set_yticklabels([f'{s}\nn = {n:,}' for s,n in zip(labels,den)])
        for t in fig.axes[0].texts:
            if re.fullmatch(r'\d+\.\d',t.get_text()):
                val=float(t.get_text())
                if 37<val<40:t.set_x(41.2)
                elif 50<val<60:t.set_x(val-2);t.set_ha('right')
        for ax,xx in zip(fig.axes[1:],[.05,.5]):
            for t in ax.texts:
                if re.fullmatch(r'-?\d+\.\d{3}',t.get_text()):
                    t.set_position((xx,t.get_position()[1]+.22));t.set_ha('center');t.set_va('top');t.set_path_effects([])
        changes.append('Available-case denominators retained; coefficient labels displaced within each row to clear uncertainty intervals.')
    if 'S5_' in name:
        fig._suptitle.set_text('Supplementary Fig. S5 | Cohort-specific visiting and expenditure context')
        # Longer authorised title stays in the historical title band.
        fig._suptitle.set_fontsize(9.3)
        for i,ax in enumerate(fig.axes):
            if i in [0,2]:ax.set_xlim(-.18,.78)
            ax.set_yticklabels(['High OOP\nexpenditure','No dental visit'])
            for t in ax.texts:
                if re.fullmatch(r'-?\d+\.\d{3}',t.get_text()):t.set_path_effects([])
        changes.append('Corrected expenditure models and terminology; lower x limit -0.18 in loneliness panels preserves full corrected CIs.')
    if 'S5_' not in name:changes.extend(expand_corrected_intervals(fig,name))
    return changes

