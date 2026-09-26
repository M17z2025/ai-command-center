import datetime as dt, importlib.util, pathlib, unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("portfolio",ROOT/"scripts/sigma_portfolio_status.py")
MOD=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(MOD)

class PortfolioStatusTests(unittest.TestCase):
    def base(self):
        return {"cycle":{"state":"CHANGED","last_evidenced_at":"2026-09-26T20:00:00Z"},"evidence":[{"type":"commit","value":"abc"}],"tests":{"evidence":[]},"production":{}}
    def test_changed_requires_evidence(self):
        d=self.base(); d["evidence"]=[]
        self.assertTrue(any("NO EVIDENCE" in x for x in MOD.validate_record(d)))
    def test_tested_requires_test_evidence(self):
        d=self.base(); d["cycle"]["state"]="TESTED"
        self.assertTrue(any("test evidence" in x for x in MOD.validate_record(d)))
    def test_verified_requires_production_identity(self):
        d=self.base(); d["cycle"]["state"]="VERIFIED_IN_PRODUCTION"; d["tests"]["evidence"]=["ci"]
        self.assertTrue(any("production commit" in x for x in MOD.validate_record(d)))
    def test_stale_is_derived(self):
        d=self.base()
        now=dt.datetime(2026,9,28,20,0,tzinfo=dt.timezone.utc)
        self.assertEqual(MOD.status(d,now,24),"STALE")
if __name__=="__main__": unittest.main()
