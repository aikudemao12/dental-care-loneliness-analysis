"""Physical layout and typography for the submitted statistical figures."""
import re
import matplotlib as mpl
from matplotlib.text import Text

def place(fig,ax,x,y,w,h):
 fw,fh=fig.get_size_inches();ax.set_position([x/fw,y/fh,w/fw,h/fh])


def above(ax,t,dx=0,dy=0):
 t.set_transform(ax.transAxes);t.set_position((dx,1+dy));t.set_ha('left');t.set_va('bottom')


def letters(fig):
 for ax in fig.axes:
  for t in ax.texts:
   if re.fullmatch('[ABCDEabcd]',t.get_text()):
    b=ax.get_position();fw,fh=fig.get_size_inches();t.set_transform(fig.transFigure);t.set_position((b.x0-.24/fw,getattr(ax,'_letter_y',b.y1*fh+.12)/fh));t.set_ha('left');t.set_va('bottom');t.set_fontsize(12)


def title(ax,text=None,pad=10,y=None):
 if text is not None:ax.set_title(text,loc='left',fontsize=11,pad=pad)
 ax._autotitlepos=False
 t=ax._left_title;t.set_fontsize(11);t.set_linespacing(1.25)
 if y is None:y=ax.get_position().y1*ax.figure.get_figheight()+pad/72
 at(fig=ax.figure,t=t,x=ax.get_position().x0*ax.figure.get_figwidth(),y=y)
 ax._letter_y=y
 ax.title.set_fontsize(11)


def at(fig,t,x,y,ha='left',va='bottom'):
 t.set_transform(fig.transFigure);t.set_position((x/fig.get_figwidth(),y/fig.get_figheight()));t.set_ha(ha);t.set_va(va)


def edit(fig,name):
 mpl.rcParams.update({'font.family':'sans-serif','font.sans-serif':['Arial','Helvetica','DejaVu Sans'],'svg.fonttype':'none','pdf.fonttype':42,'ps.fonttype':42})
 # Raise every visible text object to the explicit journal floor; do not scale PDFs.
 for t in fig.findobj(Text):
  if t.get_text():t.set_fontsize(max(10,t.get_fontsize()));t.set_path_effects([])
 for a in fig.axes:a.tick_params(labelsize=10);a.xaxis.label.set_fontsize(10);a.yaxis.label.set_fontsize(10)
 if name=='Figure_2_EJPH':
  fig.set_size_inches(7.5,11.45);a,b,c,d,e=fig.axes
  for ax,box in zip(fig.axes,[(1.65,10.0,5.55,.72),(1.65,7.85,1.95,1.1),(4.95,7.85,2.25,1.1),(1.65,5.55,5.55,1.25),(1.65,.5,5.55,4.0)]):place(fig,ax,*box)
  title(a,y=11.19)
  mean_labels=[t.get_text() for t in a.texts if re.fullmatch(r'\d+\.\d{3}',t.get_text())]
  a.set_xticklabels([f'{g}, mean {m}' for g,m in zip(['Low (0–1)','Mid (2)','High (3–4)'],mean_labels)])
  for t in a.texts:
   if t.get_text().startswith('Horizontal marks:'):
    t.set_text('Horizontal marks: weighted observed score support\nPoint/whisker: adjusted mean and 95% CI');at(fig,t,1.65,10.80)
   elif '%; n = ' in t.get_text():t.set_y(-.43)
   elif re.fullmatch(r'\d+\.\d{3}',t.get_text()):t.set_text('')
  title(b,'Primary adjusted\ncontrasts',y=9.10);title(c,'Score-specific adjusted\ncontrasts',y=9.10)
  c.set_xlabel('Disadvantage score (reference = 0)',fontsize=10)
  for t in c.texts:
   if t.get_text().startswith('Pale bars'):
    t.set_text(t.get_text().replace('Pale bars show weighted score support;','Weighted bars;'));t.set_position((.02,.165));t.set_ha('left');t.set_va('bottom')
  title(d,y=7.10)
  leg=d.get_legend();leg.set_bbox_to_anchor((7.2/7.5,7.03/11.45),transform=fig.transFigure);leg._loc=1
  for t in d.texts:
   if t.get_text().startswith('Shaded rows:'):at(fig,t,1.65,6.88)
  title(e,y=4.81)
  for t in e.texts:
   if 'CIs exclude' in t.get_text():at(fig,t,1.65,4.60)
   elif t.get_text().startswith('pooled '):at(fig,t,7.2,4.60,ha='right')
 elif 'S1_' in name:
  fig.set_size_inches(7.5,5.9);a,b=fig.axes
  place(fig,a,2.2,.75,1.3,4.4);place(fig,b,4.7,.75,2.55,4.4)
  title(a,'Largest missingness\ndomains',y=5.22);title(b,'Retained vs non-retained\nbalance',y=5.22)
  wraps={'Dental-care disadvantage group':'Dental-care\ndisadvantage group','Dental-care disadvantage score':'Dental-care\ndisadvantage score','No regular childhood care':'No regular\nchildhood care','Lack of continuous regular care':'Lack of continuous\nregular care','Late/non-continuous care':'Late/non-continuous\ncare','Recent drinking (past 7 days)':'Recent drinking\n(past 7 days)','Chronic disease burden':'Chronic disease\nburden','Wave 8 respondent weight':'Wave 8 respondent\nweight','Married or partnered':'Married or\npartnered'}
  for ax in [a,b]:
   ax.set_yticklabels([t.get_text().replace('\n',' ') if ax is a else wraps.get(t.get_text(),t.get_text()) for t in ax.get_yticklabels()])
   for t in ax.get_yticklabels():t.set_linespacing(1.2)
  leg=a.get_legend();leg.set_bbox_to_anchor((.02,.018),transform=fig.transFigure);leg._loc=3;leg.borderaxespad=0
  for t in b.texts:
   if re.fullmatch(r'0\.\d{3}',t.get_text()):
    val=float(t.get_text());t.set_x((.245 if val>.2 else .05) if val>.15 else .112)
    if val>.15:t.set_ha('center')
  for t in fig.texts:
   if t is not fig._suptitle:t.set_text('Dashed lines: |standardised difference| = 0.10');t.set_position((.97,.018));t.set_va('bottom');t.set_fontsize(10)
  a.set_xticks([0,50,100]);b.set_xticks([-.1,0,.1,.2,.3])
 elif 'S2_' in name:
  fig.set_size_inches(7.5,6.3)
  for ax,x in zip(fig.axes,[1.35,5.05]):
   place(fig,ax,x,.6,2.2,4.65);title(ax,y=5.80)
   for t in ax.texts:
    if t.get_text().startswith('largest |delta|'):t.set_text(t.get_text().replace(': ',':\n'));t.set_linespacing(1.4);at(fig,t,x,5.36)
    elif t.get_text().startswith('LOO mean '):at(fig,t,x+2.2,5.36,ha='right')
 elif 'S3_' in name:
  fig.set_size_inches(7.5,4.0)
  for ax,x in zip(fig.axes,[1.8,4.7]):place(fig,ax,x,.8,2.5,2.35);title(ax,pad=12);ax.set_xlabel(r'$\it{\beta}$ coefficient for loneliness')
 elif 'S4_' in name:
  fig.set_size_inches(7.5,4.65);a,b,c=fig.axes
  for ax,x,w in [(a,2.0,1.188),(b,3.838,1.1),(c,5.588,1.1)]:place(fig,ax,x,1.0,w,2.65)
  title(a,'Component\nprevalence',pad=15);title(b,'Joint model:\nloneliness',pad=15);title(c,'Joint model:\nCASP-12',pad=15)
  labs=[t.get_text().replace('No regular childhood care','No regular\nchildhood care').replace('Late/non-continuous care','Late/non-continuous\ncare').replace('Lifetime postponement','Lifetime\npostponement') for t in a.get_yticklabels()];a.set_yticklabels(labs)
  a.set_xlabel('Weighted\nprevalence, %');a.set_xticks([0,30,60]);b.set_xticks([0,.1]);c.set_xticks([-1,0,1])
  for ax in [a,b,c]:
   for t in ax.texts:
    if re.fullmatch(r'-?\d+\.\d+',t.get_text()):
     y=t.get_position()[1]-(.22 if ax is not a else 0);t.set_transform(ax.get_yaxis_transform());t.set_position((1.045,y));t.set_ha('left');t.set_va('center');t.set_clip_on(False)
  for t in fig.texts:
   if t is not fig._suptitle:t.set_text('Outcome scales differ; panels b and c\nshould not be compared by magnitude.');t.set_position((.975,.035))
 elif 'S5_' in name:
  fig.set_size_inches(7.5,5.5)
  for ax,(x,y) in zip(fig.axes,[(1.45,3.2),(4.98,3.2),(1.45,.65),(4.98,.65)]):place(fig,ax,x,y,1.9,1.25)
  for i,ax in enumerate(fig.axes):
   title(ax,ax.get_title(loc='left').replace(': depressive symptoms',': depressive\nsymptoms'),pad=15)
   for t in ax.texts:
    if re.fullmatch(r'-?\d+\.\d{3}',t.get_text()):t.set_transform(ax.get_yaxis_transform());t.set_x(1.025);t.set_ha('left');t.set_va('center')
  fig._suptitle.set_text('Supplementary Fig. S5 | Cohort-specific visiting\nand expenditure context')
 letters(fig)
 if fig._suptitle:
  fig._suptitle.set_position((.025,.975));fig._suptitle.set_fontsize(11)
 # The title bands use fixed physical offsets rather than scaled text.
 fig.canvas.draw()
 for t in fig.findobj(Text):
  if t.get_text():t.set_fontsize(max(10,t.get_fontsize()))
 fig.canvas.draw()

