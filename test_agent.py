import json, os, shutil, tempfile, unittest
import agent, tools

SRC = os.path.dirname(os.path.abspath(__file__))

class TestRequisitionAgent(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        for f in ("requisitions.json", "suppliers.csv"):
            shutil.copy(os.path.join(SRC, f), cls.tmp)
        cls.reqs = {r["id"]: r for r in json.load(open(os.path.join(cls.tmp, "requisitions.json")))}
        cls.out = {i: agent.decide(r, cls.tmp) for i, r in cls.reqs.items()}
    @classmethod
    def tearDownClass(cls): shutil.rmtree(cls.tmp)

    def test_1_PR1_auto(self):  self.assertEqual(self.out["PR1"]["decision"], "AUTO")
    def test_2_PR2_auto(self):  self.assertEqual(self.out["PR2"]["decision"], "AUTO")
    def test_3_PR3_auto(self):  self.assertEqual(self.out["PR3"]["decision"], "AUTO")
    def test_4_PR4_new_supplier_to_manager(self):
        self.assertEqual(self.out["PR4"]["decision"], "MANAGER"); self.assertIn("new", self.out["PR4"]["reason"])
    def test_5_PR5_over_limit_to_manager(self):
        self.assertEqual(self.out["PR5"]["decision"], "MANAGER"); self.assertIn("above", self.out["PR5"]["reason"])
    def test_6_three_pos_two_queue_five_logs(self):
        self.assertEqual(len(json.load(open(os.path.join(self.tmp, "po_created.json")))), 3)
        self.assertEqual(len(json.load(open(os.path.join(self.tmp, "manager_queue.json")))), 2)
        self.assertEqual(len(open(os.path.join(self.tmp, "decision_log.jsonl")).read().splitlines()), 5)
    def test_7_every_decision_has_reason(self):
        self.assertTrue(all(e["reason"] for e in self.out.values()))

if __name__ == "__main__":
    unittest.main(verbosity=2)
