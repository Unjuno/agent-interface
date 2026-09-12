"""Scoped descriptive charts. Missing evidence is a gap, never a zero."""
import csv,json,math
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE=Path(__file__).resolve().parent

def main():
    rows=list(csv.DictReader((HERE/'evolution.csv').open(encoding='utf-8')))
    occurrences=list(csv.DictReader((HERE/'occurrences.csv').open(encoding='utf-8')))
    labels=[r['revision'] for r in rows];out=HERE/'charts';out.mkdir(exist_ok=True)
    def values(column):return [float(r[column]) if r[column] else math.nan for r in rows]
    files=[]
    def chart(name,title,ylabel,series,note,annotate=False):
        fig,ax=plt.subplots(figsize=(10,5),layout='constrained')
        fig.patch.set_facecolor('#f8fafc');ax.set_facecolor('#f8fafc')
        available=False
        for label,data in series:
            finite=[i for i,v in enumerate(data) if math.isfinite(v)]
            if finite:
                available=True
                ax.scatter(finite,[data[i] for i in finite],s=75,label=label,color='#2563eb')
                if annotate:
                    for i in finite:ax.annotate(f"n={rows[i]['episodes']}",(i,data[i]),xytext=(0,10),textcoords='offset points',ha='center',fontsize=9)
        if not available:
            ax.text(.5,.5,'NOT MEASURED / NOT AUDITED',transform=ax.transAxes,
                ha='center',va='center',fontsize=18,color='#64748b')
            ax.set_yticks([])
        elif len(series)>1:ax.legend()
        ax.set_xticks(range(len(labels)),labels,rotation=25,ha='right')
        ax.set_xlim(-.5,len(labels)-.5);ax.set_ylabel(ylabel)
        if name=='success':ax.set_ylim(0,1.15)
        ax.set_title(title+'\nPartial retrospective index — no convergence claim',loc='left',fontsize=13)
        ax.grid(axis='y',alpha=.2);ax.spines[['top','right']].set_visible(False)
        fig.supxlabel(note+'\nAbsent points mean unknown, not zero.',fontsize=9)
        fig.savefig(out/(name+'.png'),dpi=160);plt.close(fig);files.append(name+'.png')
    missing=[math.nan]*len(rows)
    discoveries=values('new_failure_classes')
    # A cumulative total cannot resume after an unknown prefix.
    cumulative=[];total=0;known=True
    for value in discoveries:
        known=known and math.isfinite(value)
        if known:total+=value
        cumulative.append(total if known else math.nan)
    chart('failure_discovery','Cumulative newly discovered failure classes','Classes',[('classes',cumulative)],'Global first-discovery ordering has not been audited.')
    chart('new_failure_classes','New failure classes by revision','Classes',[('classes',discoveries)],'Observed occurrences are not new-class discoveries.')
    chart('regression','Known introduced regression classes','Classes',[('regressions',values('regressions'))],'Focus recovery: one known class; other revisions not exhaustively audited.')
    chart('architecture_churn','Architecture churn: reviewer ratings','Ordinal score 0–3',[('churn',values('architecture_churn_score'))],'Retrospective judgments; not an automated metric or proof of stabilization.')
    chart('marginal_gain','Comparable primary-metric marginal gain','Improvement (%)',[('gain',values('best_marginal_gain'))],'No qualifying primary-metric comparison; byte proxies are excluded.')
    chart('success','Independent saved-task success in indexed self-use','Success fraction',[('success',values('hard_success_rate'))],'Different tasks and tiny cohorts; dots are descriptive, not an efficacy trend.',True)
    chart('latency','Comparable p95 / p99 latency','Latency (ms)',[('p95',values('p95')),('p99',values('p99'))],'No adequately sampled common latency endpoint available.')
    chart('planner_boundaries','Planner boundaries per successful task','Boundaries / success',[('boundaries',missing)],'Accepted program counts cannot substitute for actual planner boundaries.')
    per_success=[float(r['observations'])/float(r['successful_tasks']) if r['observations'] and r['successful_tasks'] and float(r['successful_tasks'])>0 else math.nan for r in rows]
    chart('observations','Archived observations per successful task','Frames / successful task',[('observations',per_success)],'Includes frames spent on failed tasks in the same cohort; controls excluded.')
    wrong=[sum(r['evaluation_revision']==label and r['taxonomy_id']=='F04' for r in occurrences) if any(r['evaluation_revision']==label and r['taxonomy_id']=='F04' for r in occurrences) else math.nan for label in labels]
    chart('incidents','Indexed wrong-target / stale-action incidents','Incident count',[('wrong-target: baseline controls',wrong),('stale action: unreviewed',missing)],'Wrong-target points describe baseline controls; absence is not zero incidents.')
    (out/'manifest.json').write_text(json.dumps(dict(matplotlib_version=matplotlib.__version__,charts=files,
        scope='partial descriptive index; missing coverage is not zero',freeze_assessment='not ready'),indent=2),encoding='utf-8')
    print(f'Generated {len(files)} separate charts')

if __name__=='__main__':main()
