import unittest,tempfile,json,os
from pathlib import Path
from unittest.mock import patch
from core import Support,evaluate
from engine import Assistant,grade
class Tests(unittest.TestCase):
 def setUp(self):
    self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.s=Support(Path(self.tmp.name)/'test.db')
 def test_known_source_and_grounded_local(self):
    r=self.s.assistant.answer('Где скачать электронный чек после оплаты?');self.assertEqual(r['action'],'draft');self.assertEqual(r['sources'][0]['id'],'receipt');self.assertIn('Документы',r['text'])
 def test_unknown_and_vague(self):
    self.assertEqual(self.s.assistant.answer('У меня проблема')['action'],'clarify');self.assertEqual(self.s.assistant.answer('Какая погода завтра в Москве?')['action'],'escalate')
 def test_secret_escalates(self):self.assertEqual(self.s.assistant.answer('Сообщить CVV карты')['action'],'escalate')
 def test_approve_and_no_resend(self):
    r=self.s.create('Где скачать электронный чек после оплаты?');out=self.s.review(r['id'],None,'accept');self.assertFalse(out['sent']);self.assertEqual(out['final_text'],r['text'])
    with self.assertRaises(ValueError):self.s.review(r['id'],'new','edit')
 def test_edit_and_history_persist(self):
    r=self.s.create('У меня проблема');self.s.review(r['id'],'Уточните номер заказа','edit');new=Support(self.s.db_path);self.assertEqual(new.history()[0]['final_text'],'Уточните номер заказа')
 def test_llm_invalid_citation_rejected(self):
    with patch('engine.llm',return_value={'text':json.dumps({'action':'draft','answer':'Hi','source_ids':['invented']}),'model':'mock'}):
      with self.assertRaises(ValueError):self.s.assistant.answer('Где скачать электронный чек после оплаты?','llm')
 def test_empty_input(self):
    with self.assertRaises(ValueError):self.s.create('')
 def test_evaluation_not_human_accuracy(self):
    e=evaluate();self.assertEqual(e['count'],22);self.assertGreaterEqual(e['action_accuracy'],.7);self.assertIn('не экспертная',e['quality_note'])
if __name__=='__main__':unittest.main()
