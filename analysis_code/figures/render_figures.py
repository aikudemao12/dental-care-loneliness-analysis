"""Render the seven manuscript figures from aggregate CSVs in the initial layout.

Usage: python render_figures.py --source-data ../../source_data --output Figures
The historical modules contain layout functions only; no historical analyses run.
"""
from pathlib import Path
import argparse, hashlib, json, re, sys
import matplotlib as mpl
mpl.use('Agg')
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
                elif t.get_text().startswith('pooled '):
                    t.set_transform(ax.transAxes);t.set_position((1,1.005));t.set_ha('right');t.set_va('bottom')
        changes.append('Pooled and largest-delta notes occupy the existing gap below each panel title, clear of intervals.')
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

def draw_figure1():
    name='Figure_1_EJPH';src=json.loads((HERE/'initial_f1_geometry.json').read_text())
    pw,ph=src['page'][2:];width,height=np.array(SIZES[name])/600
    fig=plt.figure(figsize=(width,height)); scale=width*72/pw
    ph=height*72/scale  # Uniform vector scale; retain the original PNG aspect ratio.
    # Two coordinate-preserving panels share the same original x geometry.
    split=294
    a=fig.add_axes([0,1-split/ph,1,split/ph]); b=fig.add_axes([0,0,1,1-split/ph])
    for ax,lo,hi in [(a,0,split),(b,split,ph)]:ax.set(xlim=(0,pw),ylim=(hi,lo));ax.axis('off')
    def target(y):return a if y<split else b
    omitted={0,1,2,3,4,17,35,36,41,42,47,48,53,54}
    for i,d in enumerate(src['drawings']):
        if i in omitted:continue
        vertices=[];codes=[];last=None
        for item in d['items']:
            typ=item[0]
            if typ in ['l','c']:
                if last!=item[1]:vertices.append(item[1]);codes.append(MplPath.MOVETO)
                vertices.extend(item[2:]);codes.extend([MplPath.LINETO] if typ=='l' else [MplPath.CURVE4]*3);last=item[-1]
            elif typ=='re':
                x0,y0,x1,y1=item[1];vertices.extend([(x0,y0),(x1,y0),(x1,y1),(x0,y1),(x0,y0)])
                codes.extend([MplPath.MOVETO,MplPath.LINETO,MplPath.LINETO,MplPath.LINETO,MplPath.CLOSEPOLY]);last=None
            else:raise ValueError(typ)
        if d['closePath'] and vertices:vertices.append(vertices[0]);codes.append(MplPath.CLOSEPOLY)
        target(d['rect'][1]).add_patch(PathPatch(MplPath(vertices,codes),facecolor=d['fill'] if d['fill'] else 'none',edgecolor=d['color'] if d['color'] else 'none',lw=(d['width'] or 0)*scale,clip_on=False))
    # Preserve the historical line correction: no small upward jog after the
    # country/context box. The necessary final turn into the outcome stays.
    context_route=[(195.63519287109375,196.65089416503906),
                   (559.8771362304688,196.65089416503906),
                   (559.8771362304688,152.80039978027344),
                   (592.88525390625,152.80039978027344)]
    a.add_patch(PathPatch(MplPath(context_route,[MplPath.MOVETO]+[MplPath.LINETO]*3),
        facecolor='none',edgecolor=src['drawings'][17]['fill'],
        lw=.7779925465583801*scale,linestyle=(0,(6,4)),clip_on=False,
        gid='country_context_straightened'))
    flow=read_csv('figure_1_sample_flow.csv');counts=flow.n.astype(int).tolist()
    for extra in ['figure_1_conceptual_framework.csv','figure_1_operational_boundary.csv','figure_1_wave7_overlap_check.csv']:read_csv(extra)
    replacements={'Later-life loneliness':'Loneliness in adults\naged 50 years and older','Complete life-course dental-care':'Computable life-course dental-care',
        'Incomplete disadvantage':'Score not computable','score':'(fewer than three components)',
        'n = 61,530':f'n = {counts[2]:,}','n = 14,712':f'n = {counts[1]-counts[2]:,}',
        'n = 31,644':f'n = {counts[3]:,}','n = 29,886':f'n = {counts[2]-counts[3]:,}',
        'n = 30,908':f'n = {counts[4]:,}','n = 736':f'n = {counts[3]-counts[4]:,}'}
    for s in src['spans']:
        old=s['text']
        if old.startswith(('solid arrows:','dashed arrows:')):continue
        txt=replacements.get(old,old);x,y=s['origin'];ha='left'
        if old in replacements and x<510 and y>350 or old=='Later-life loneliness':
            x=(s['bbox'][0]+s['bbox'][2])/2;ha='center'
        color=tuple(((s['color']>>c)&255)/255 for c in [16,8,0])
        target(y).text(x,y+5 if old=='Later-life loneliness' else y,txt,fontsize=max(5,s['size']*scale),color=color,fontweight='bold' if s['flags']&16 else 'normal',ha=ha,va='baseline',clip_on=False)
    def arrow(ax,pts,color,dashed=False):
        ax.add_patch(FancyArrowPatch(path=MplPath(pts,[MplPath.MOVETO]+[MplPath.LINETO]*(len(pts)-1)),arrowstyle='-|>',mutation_scale=4.5,lw=.65,color=color,linestyle=(0,(4,3)) if dashed else '-',clip_on=False))
    # Four explicit arrow meanings occupy the original legend footprint.
    for y,label,color,dash in [(10,'Grey: conceptual relations','#636B76',False),(22,'Red: study association','#B94A67',False),(34,'Blue: possible pathways','#2E7895',False),(46,'Dashed: residual contextual confounding','#65717D',True)]:
        arrow(a,[(492,y),(520,y)],color,dash);a.text(529,y,label,fontsize=5,color='#65717D',va='center')
    # Exclusions branch between retained stages, then terminate at the matching box.
    for i,(prev_bottom,cy) in enumerate(zip([421.56,488.75,555.94,623.13],[466.83,534.02,601.21,668.40])):
        mid=prev_bottom+11.67
        arrow(b,[(326.48,mid),(535,mid),(535,cy),(559.5,cy)],'#AEB8C2',True)
    FIGURES[name]=fig;BASE_BOX[name]=Bbox.from_bounds(0,0,width,height)
    return fig,['Initial vector node/box geometry retained; latest counts and terminology inserted as editable text.',
                'Four short legend entries replace ambiguous two-entry legend; exclusion arrows branch at corresponding restriction.',
                'Previously corrected country/context dashed line stays horizontal until its final turn into the outcome.']

def save(fig,name,changes):
    fig.canvas.draw();bbox=BASE_BOX[name];ids=list('AB') if name=='Figure_1_EJPH' else (list('ABCDE') if name=='Figure_2_EJPH' else list('abcd')[:len(fig.axes)])
    align=None
    if ALIGNMENT:
        from audit_panel_alignment import require_matplotlib_panel_alignment
        rows=[];cols=[];ex=[]
        if name=='Figure_1_EJPH':cols=[ids]
        elif name=='Figure_2_EJPH':
            rows=[['B','C']];cols=[['A','D','E']]
            ex=[{'panels':['A','D','E'],'checks':['vertical-gutter'],'reason':'Inherited initial figure uses distinct heights for distribution, ladder, and 26-country forest.'},
                {'panels':['B','C'],'checks':['panel-label'],'reason':'Original B/C letters retained at their original anchors.'}]
        elif 'S5_' in name:rows=[['a','b'],['c','d']];cols=[['a','c'],['b','d']]
        else:rows=[ids]
        if 'S4_' in name:ex=[{'panels':['a'],'checks':['panel-width'],'reason':'Initial prevalence panel has width ratio 1.08; two effect panels have ratio 1.0.'}]
        # Initial label anchors are preserved; they are checked separately against historical geometry.
        align=require_matplotlib_panel_alignment(fig,json_out=QA/(name+'.alignment.json'),tolerance_pt=1.5,gutter_tolerance_pt=1.5,
            panel_ids=ids,row_groups=rows,column_groups=cols,exemptions=ex,require_panel_labels=False)
    checks=interval_checks(fig,name)
    rec={'panels':ids,'source_files_sha256':dict(ACTIVE),'numeric_artist_sha256':numeric_artists(fig),
         'historical_layout':'initial_submission','original_png_size':SIZES[name],
         'canvas_inches':fig.get_size_inches().tolist(),'crop_inches':list(bbox.bounds),
         'axes':[{'position':list(ax.get_position().bounds),'xlim':list(ax.get_xlim()),'ylim':list(ax.get_ylim())} for ax in fig.axes],
         'interval_extent_checks':checks,'necessary_local_adjustments':changes}
    fig.savefig(OUTPUT/(name+'.pdf'),bbox_inches=bbox,metadata={'Title':name,'Author':'','Creator':'','Producer':''})
    fig.savefig(OUTPUT/(name+'.png'),dpi=600,bbox_inches=bbox,metadata={'Title':name,'Software':''})
    with Image.open(OUTPUT/(name+'.png')) as im:
        rec['final_png_size']=list(im.size)
        assert max(abs(im.size[i]-SIZES[name][i]) for i in [0,1])<=1,(name,im.size)
        im.convert('RGB').save(OUTPUT/(name+'.tif'),compression='tiff_lzw',dpi=(600,600))
        im.resize((1500,round(im.height/im.width*1500))).save(QA/(name+'.preview.png'))
    ext='eps' if name.startswith('Figure_') else 'svg'
    if ext=='eps':
        fig.savefig(OUTPUT/(name+'.eps'),bbox_inches=bbox,metadata={'Creator':'Manuscript figure'})
    else:
        fig.savefig(OUTPUT/(name+'.svg'),bbox_inches=bbox,metadata={'Title':name,'Creator':'','Date':None})
    rec['files_sha256']={name+'.'+ext:sha(OUTPUT/(name+'.'+ext)) for ext in ['pdf','png','tif',ext]}
    rec['text']=[{'text':t.get_text(),'font_pt':t.get_fontsize()} for t in fig.findobj(Text) if t.get_visible() and t.get_text()]
    REPORT[name]=rec;(QA/'restored_report.json').write_text(json.dumps(REPORT,ensure_ascii=False,indent=2))
    plt.close(fig);print(name,rec['final_png_size'],'exported',flush=True)

def main():
    global SOURCE,OUTPUT,QA,ALIGNMENT
    p=argparse.ArgumentParser();p.add_argument('--source-data',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--qa',type=Path);p.add_argument('--alignment-tools',type=Path);p.add_argument('--figures',nargs='*')
    args=p.parse_args();SOURCE=args.source_data;OUTPUT=args.output;QA=args.qa or OUTPUT.parent/'figure_qa';ALIGNMENT=args.alignment_tools
    if ALIGNMENT:sys.path.insert(0,str(ALIGNMENT))
    OUTPUT.mkdir(parents=True,exist_ok=True);QA.mkdir(parents=True,exist_ok=True)
    if (QA/'restored_report.json').exists():REPORT.update(json.loads((QA/'restored_report.json').read_text()))
    # Prevent original plotting routines from closing the figure before export.
    close=plt.close;plt.close=lambda *a,**kw:None
    jobs=[('Figure_1_EJPH',None,None),('Figure_2_EJPH','initial_f2.py','draw_figure_2'),
          ('Supplementary_Figure_S1_EJPH','initial_supp.py','draw_supplementary_s1'),
          ('Supplementary_Figure_S2_EJPH','initial_s2.py','draw_supplementary_s2'),
          ('Supplementary_Figure_S3_EJPH','initial_supp.py','draw_supplementary_s3'),
          ('Supplementary_Figure_S4_EJPH','initial_supp.py','draw_supplementary_s4'),
          ('Supplementary_Figure_S5_EJPH','initial_supp.py','draw_supplementary_s5')]
    for name,file,fn in jobs:
        if args.figures and name not in args.figures:continue
        ACTIVE.clear();style()
        if file:
            env=load_module(file)
            if name=='Figure_2_EJPH':
                r=read_csv('figure_2_primary_models.csv').set_index('short_label').loc['High vs low']
                env.update(POOLED_HIGH=float(r.estimate),POOLED_HIGH_LCL=float(r.lcl),POOLED_HIGH_UCL=float(r.ucl))
            env[fn]();fig=FIGURES[name];before=numeric_artists(fig);changes=refine(fig,name)
            assert numeric_artists(fig)==before,(name,'Unexpected change to numeric artists during text update')
        else:fig,changes=draw_figure1()
        save(fig,name,changes);close(fig)
    plt.close=close
if __name__=='__main__':main()
