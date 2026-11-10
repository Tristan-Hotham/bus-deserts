import zipfile,csv,io,sys,json,datetime as dt
from collections import defaultdict
src,out=sys.argv[1],sys.argv[2]
DAYS={'wk':'20261117','sat':'20261121','sun':'20261122'}
z=zipfile.ZipFile(src)
def rd(f): return csv.DictReader(io.TextIOWrapper(z.open(f),'utf-8-sig'))
wd=['monday','tuesday','wednesday','thursday','friday','saturday','sunday']
act={k:set() for k in DAYS}
for r in rd('calendar.txt'):
    for k,d in DAYS.items():
        w=wd[dt.datetime.strptime(d,'%Y%m%d').weekday()]
        if r['start_date']<=d<=r['end_date'] and r[w]=='1': act[k].add(r['service_id'])
for r in rd('calendar_dates.txt'):
    for k,d in DAYS.items():
        if r['date']==d:
            (act[k].add if r['exception_type']=='1' else act[k].discard)(r['service_id'])
rtype={r['route_id']:r['route_type'] for r in rd('routes.txt')}
trip={}
for r in rd('trips.txt'):
    ks=[k for k in DAYS if r['service_id'] in act[k]]
    trip[r['trip_id']]=(ks,r['route_id'])
S=defaultdict(lambda:{'n':{k:0 for k in DAYS},'first':{},'last':{},'a19':0,'h':[0]*30,'routes':set(),'rt':set()})
for r in rd('stop_times.txt'):
    t=trip.get(r['trip_id'])
    if not t: continue
    s=S[r['stop_id']]; s['routes'].add(t[1]); s['rt'].add(rtype.get(t[1],''))
    if not t[0] or r.get('pickup_type')=='1': continue
    tm=r['departure_time'] or r['arrival_time']
    if not tm: continue
    hh=int(tm[:2]); mins=hh*60+int(tm[3:5])
    for k in t[0]:
        s['n'][k]+=1
        s['first'][k]=min(s['first'].get(k,9999),mins); s['last'][k]=max(s['last'].get(k,-1),mins)
        if k=='wk':
            s['h'][min(hh,29)]+=1
            if mins>=19*60: s['a19']+=1
w=csv.writer(open(out,'w',newline=''))
w.writerow(['stop_id','stop_name','lat','lon','route_types','n_routes','wk_n','wk_first','wk_last','wk_after19','wk_hours','sat_n','sat_last','sun_n','sun_last'])
for r in rd('stops.txt'):
    s=S.get(r['stop_id'])
    if s is None: s={'n':{k:0 for k in DAYS},'first':{},'last':{},'a19':0,'h':[0]*30,'routes':set(),'rt':set()}
    w.writerow([r['stop_id'],r['stop_name'],r['stop_lat'],r['stop_lon'],'|'.join(sorted(s['rt'])),len(s['routes']),s['n']['wk'],s['first'].get('wk',''),s['last'].get('wk',''),s['a19'],'|'.join(map(str,s['h'])),s['n']['sat'],s['last'].get('sat',''),s['n']['sun'],s['last'].get('sun','')])
print(out,len(S),{k:len(v) for k,v in act.items()})
