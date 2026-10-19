"""Explicit structural-skip, unknown-response and score-boundary tests."""
import itertools
from pathlib import Path
import tempfile
import unittest
import numpy as np
import pandas as pd
from build_analysis_inputs import derive_share, read_source, SHARE_COLUMNS, RH_COLUMNS, COMPONENTS


def frames(cases, raw_evidence=True):
    h = pd.DataFrame(0.0, index=range(len(cases)), columns=SHARE_COLUMNS)
    r = pd.DataFrame(np.nan, index=h.index, columns=RH_COLUMNS)
    h['mergeid'] = r['mergeid'] = [str(i) for i in h.index]
    h['rabyear'] = 1950
    for i, (ever, child, continuous, age, post) in enumerate(cases):
        r.loc[i, ['rh015_', 'rh016_', 'rh018_', 'rh017_', 'rh788_']] = [ever, child, continuous, 1950+age, post]
    if raw_evidence:
        for c in ['rh016_', 'rh018_']:
            r[c.rstrip('_')+'_raw_blank'] = r[c].isna()
    return h, r


class ScoringTests(unittest.TestCase):
    def test_score_groups_and_structural_skips(self):
        # Inputs followed by expected score, observed count, and group.
        cases = [
            ((1,1,1,np.nan,5),0,4,'low_0_1'),
            ((1,1,1,np.nan,1),1,4,'low_0_1'),
            ((1,5,1,30,5),2,4,'mid_2'),
            ((5,np.nan,np.nan,np.nan,5),3,4,'high_3_4'),
            ((5,np.nan,np.nan,np.nan,1),4,4,'high_3_4'),
            ((5,np.nan,np.nan,np.nan,np.nan),3,3,'high_3_4'),
            ((5,np.nan,np.nan,np.nan,-1),3,3,'high_3_4'),
            ((5,np.nan,np.nan,np.nan,-2),3,3,'high_3_4'),
            ((1,5,np.nan,np.nan,5),np.nan,2,None),
            ((5,-1,np.nan,np.nan,np.nan),np.nan,2,None),
            ((5,-2,np.nan,np.nan,np.nan),np.nan,2,None),
            ((5,8,np.nan,np.nan,np.nan),np.nan,2,None),
        ]
        out = derive_share(*frames([c[0] for c in cases]))
        for i, (_, score, count, group) in enumerate(cases):
            np.testing.assert_equal(out.loc[i,'disadvantage_score'],score)
            self.assertEqual(out.loc[i,'disadvantage_component_nonmissing'],count)
            if group is None: self.assertTrue(pd.isna(out.loc[i,'disadvantage_group']))
            else: self.assertEqual(out.loc[i,'disadvantage_group'],group)
        self.assertTrue(out.loc[5:7,'disadv_postponed'].isna().all())
        self.assertTrue(out.loc[9:11,'disadv_childhood'].isna().all())

    def test_raw_blank_provenance_and_contradictions(self):
        h, r = frames([(5,np.nan,np.nan,np.nan,5)], raw_evidence=False)
        self.assertTrue(pd.isna(derive_share(h,r).loc[0,'disadv_childhood']))
        # Contradictory observed childhood responses are never overwritten;
        # observed/unknown continuity cannot establish a clean skip branch.
        out = derive_share(*frames([(5,1,np.nan,np.nan,5),(5,5,np.nan,np.nan,5),
                                   (5,np.nan,1,np.nan,5),(5,np.nan,-1,np.nan,5),
                                   (-1,np.nan,np.nan,np.nan,5),(-2,np.nan,np.nan,np.nan,5)]))
        np.testing.assert_equal(out.disadv_childhood.to_numpy(),[0,1,np.nan,np.nan,np.nan,np.nan])

    def test_read_source_preserves_negative_and_text_unknown_identity(self):
        # Explicit empty, DK, refusal, positive unknown, NA text, and observed
        # contradiction: only the empty source cell is structural evidence.
        tokens=['','-1','-2','8','NA','unknown','1','5']
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'history.csv'
            pd.DataFrame({'mergeid':list(map(str,range(8))), 'rh015_':['5']*8,
                          'rh016_':tokens,'rh018_':['']*8,'rh017_':['']*8,'rh788_':['5']*8,
                          **{c:['']*8 for c in RH_COLUMNS if c not in ['mergeid','rh015_','rh016_','rh018_','rh017_','rh788_']}}).to_csv(p,index=False)
            r=read_source(p,RH_COLUMNS,'mergeid')
            h,_=frames([(5,np.nan,np.nan,np.nan,5)]*8)
            out=derive_share(h,r)
        self.assertEqual(r.rh016_raw_blank.tolist(),[True]+[False]*7)
        np.testing.assert_equal(out.disadv_childhood.to_numpy(),[1,np.nan,np.nan,np.nan,np.nan,np.nan,0,1])

    def test_combinations_and_boundaries(self):
        responses=[1,5,-1,-2,8,np.nan]
        ages=[-1,0,25,25.001,26,100,101,np.nan]
        cases=list(itertools.product(responses,responses,responses,ages))
        out=derive_share(*frames([(*case,5) for case in cases]))
        for i,(ever,child,continuous,age) in enumerate(cases):
            valid_age=age if 0<=age<=100 else np.nan
            childhood=0.0 if child==1 else (1.0 if child==5 or (ever==5 and pd.isna(child) and pd.isna(continuous)) else np.nan)
            adult=1.0 if ever==5 or continuous==5 else (0.0 if ever==continuous==1 else np.nan)
            late=1.0 if valid_age>25 or ever==5 or continuous==5 else (0.0 if (child==1 or valid_age<=25) and continuous==1 else np.nan)
            np.testing.assert_allclose(out.loc[i,'regular_dental_start_age'],valid_age,equal_nan=True)
            expected=np.array([childhood,adult,late,0.0]);count=int(np.isfinite(expected).sum())
            np.testing.assert_equal(out.loc[i,COMPONENTS].astype(float).to_numpy(),expected)
            np.testing.assert_equal(out.loc[i,'disadvantage_component_nonmissing'],count)
            score=np.nansum(expected) if count>=3 else np.nan
            np.testing.assert_equal(out.loc[i,'disadvantage_score'],score)
            if count>=3:
                self.assertEqual(out.loc[i,'disadvantage_group'],'low_0_1' if score<=1 else ('mid_2' if score==2 else 'high_3_4'))
            else:self.assertTrue(pd.isna(out.loc[i,'disadvantage_group']))
        self.assertEqual(len(cases),1728)

if __name__=='__main__':
    unittest.main()
