import argparse
from common import ROOT,serve,read_json
from core import Support,evaluate

def routes(support):
    def route(method,path,query,body):
        if method=='GET' and path=='/api/knowledge': return read_json(ROOT/'data/knowledge.json')
        if method=='GET' and path=='/api/history': return support.history()
        if method=='GET' and path=='/api/evaluation':return evaluate()
        if method=='POST' and path=='/api/ask':return support.create(body.get('question'),body.get('mode','local'))
        if method=='POST' and path=='/api/review':return support.review(body.get('id'),body.get('final_text'),body.get('decision'))
        raise LookupError()
    return route

def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=['serve','demo'],nargs='?',default='serve');p.add_argument('--port',type=int,default=8012);a=p.parse_args()
    if a.command=='serve':serve(routes(Support()),a.port,'SupportPilot')
    else:
        e=evaluate(ROOT/'reports/example');print(f"Proxy pass: {e['proxy_pass_rate']:.2%}; {e['count']} cases")
if __name__=='__main__':main()
