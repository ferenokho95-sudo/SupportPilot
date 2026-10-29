import statistics
from common import ROOT,connect,read_json,now,require_text,save_json
from engine import Assistant,grade

class Support:
    def __init__(self,db_path=None):
        self.db_path=db_path;self.assistant=Assistant()
        with connect(db_path) as db:
            db.execute('CREATE TABLE IF NOT EXISTS tickets(id INTEGER PRIMARY KEY,question TEXT NOT NULL,result TEXT NOT NULL,status TEXT NOT NULL,final_text TEXT,created_at TEXT NOT NULL,reviewed_at TEXT)')
    def create(self,question,mode='local'):
        import json
        result=self.assistant.answer(question,mode)
        with connect(self.db_path) as db:
            cursor=db.execute('INSERT INTO tickets(question,result,status,created_at) VALUES (?,?,?,?)',(question,json.dumps(result,ensure_ascii=False),'pending',now()))
            tid=cursor.lastrowid
        return dict(result,id=tid,status='pending')
    def review(self,tid,final_text,decision):
        import json
        if decision not in ('accept','edit','reject'):raise ValueError('decision: accept, edit или reject')
        with connect(self.db_path) as db:
            row=db.execute('SELECT * FROM tickets WHERE id=?',(tid,)).fetchone()
            if not row:raise LookupError()
            if row['status']!='pending':raise ValueError('Обращение уже проверено')
            original=json.loads(row['result'])
            if decision=='accept': final_text=original['text']
            elif decision=='edit':final_text=require_text(final_text,'final_text',15000)
            else:final_text=''
            db.execute('UPDATE tickets SET status=?,final_text=?,reviewed_at=? WHERE id=?',(decision,final_text,now(),tid))
        return {'id':tid,'status':decision,'final_text':final_text,'sent':False}
    def history(self):
        import json
        with connect(self.db_path) as db:rows=[dict(r) for r in db.execute('SELECT * FROM tickets ORDER BY id DESC LIMIT 200')]
        for row in rows:row['result']=json.loads(row['result'])
        return rows

def evaluate(out=None):
    assistant=Assistant();results=[]
    for case in read_json(ROOT/'data/cases.json'):
        result=assistant.answer(case['question'])
        results.append(dict(case_id=case['id'],question=case['question'],expected_action=case['expected_action'],result=result,**grade(case,result)))
    report={'source':'22 синтетических обращения, локальный режим. Добровольцы и клиенты не участвовали.',
      'count':len(results),'proxy_pass_rate':sum(r['proxy_pass'] for r in results)/len(results),
      'action_accuracy':sum(r['action_ok'] for r in results)/len(results),
      'avg_latency_ms':statistics.mean(r['result']['latency_ms'] for r in results),
      'cost_usd':0.0,'quality_note':'proxy_pass = правильное действие + ожидаемая статья + все группы ключевых слов. Это не экспертная оценка смысла ответа.',
      'results':results}
    if out:
        save_json(out/'evaluation.json',report)
        (out/'REPORT.md').write_text('# SupportPilot — проверка\n\n'+report['source']+'\n\n'+report['quality_note']+f"\n\nProxy pass: {report['proxy_pass_rate']:.2%}; action accuracy: {report['action_accuracy']:.2%}; среднее время: {report['avg_latency_ms']:.2f} мс.\n\nЭто время генерации локального черновика, а не время работы оператора. API и человеческая оценка не запускались.\n",encoding='utf-8')
    return report
