import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
sys.path.insert(0,str(HERE/'upstream'))
from candidate import DependencyCache
import exact_crop_semantic_probe_v1 as upstream
from study import fixture_paths, build_requests

class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.paths=fixture_paths(Path(self.tmp.name))
    def test_candidate_matches_baseline_all_workloads(self):
        for w in ('METADATA','ROI','IMAGE'):
            cache=DependencyCache()
            for req in build_requests(w,self.paths):
                self.assertEqual(upstream.score_path(req['contract'],req['image']),cache.score(req['contract'],req['image']))
    def test_metadata_reuses_expensive_nodes(self):
        cache=DependencyCache(); reqs=build_requests('METADATA',self.paths)
        for r in reqs: cache.score(r['contract'],r['image'])
        self.assertEqual(cache.counters['frame_recompute'],1)
        self.assertEqual(cache.counters['crop_recompute'],1)
        self.assertEqual(cache.counters['frame_reuse'],23)
        self.assertEqual(cache.counters['crop_reuse'],23)
    def test_roi_recomputes_only_four_crops(self):
        cache=DependencyCache(); reqs=build_requests('ROI',self.paths)
        for r in reqs: cache.score(r['contract'],r['image'])
        self.assertEqual(cache.counters['frame_recompute'],1)
        self.assertEqual(cache.counters['crop_recompute'],4)
    def test_image_workload_versions_exact_bytes(self):
        cache=DependencyCache(); reqs=build_requests('IMAGE',self.paths)
        for r in reqs: cache.score(r['contract'],r['image'])
        self.assertEqual(cache.counters['frame_recompute'],4)
        self.assertEqual(cache.counters['crop_recompute'],4)
    def test_bad_authority_fails_closed(self):
        req=build_requests('METADATA',self.paths)[0]; c=dict(req['contract'],grants_input_authority=True)
        with self.assertRaises(ValueError): DependencyCache().score(c,req['image'])
    def test_git_blob_ids(self):
        expected={'exact_crop_semantic_probe_v1.py':'22a5c022d613039b0386535304cbc432009699af','inkscape_selection_frame_probe_v1.py':'f4a68e95e6bbeb2896a00168f0c88282551be4e4'}
        for name,want in expected.items():
            b=(HERE/'upstream'/name).read_bytes(); got=hashlib.sha1(f'blob {len(b)}\0'.encode()+b).hexdigest(); self.assertEqual(got,want)

if __name__=='__main__': unittest.main()
