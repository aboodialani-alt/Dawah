import json,re,sys
idx=json.load(open("../da-v2/site/idx.json",encoding="utf8"))
parts={p["id"]:p for p in idx["parts"]}
titles=[f"Part {parts[b['p']]['no']} · {b['title']}" for b in idx["briefs"]]
s=open("board.html",encoding="utf8").read()
s=s.replace("/*DA_TITLES*/[]",json.dumps(titles,ensure_ascii=False))
import os; os.makedirs("site",exist_ok=True); open("site/index.html","w",encoding="utf8").write(s)
print(len(titles),"titles",len(s),"bytes")
