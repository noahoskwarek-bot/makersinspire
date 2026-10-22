import re,json,sys,math
def parse(d):
    subs=[]
    for sp in re.findall(r'M[^M]*',d):
        toks=re.findall(r'[MCLZ]|-?[\d.]+(?:e-?\d+)?',sp)
        i=0;pts=[];segs=[]
        while i<len(toks):
            t=toks[i]
            if t=='M': start=(float(toks[i+1]),float(toks[i+2])); i+=3
            elif t=='C': segs.append(('C',[(float(toks[i+1+2*k]),float(toks[i+2+2*k])) for k in range(3)])); i+=7
            elif t=='L': segs.append(('L',[(float(toks[i+1]),float(toks[i+2]))])); i+=3
            elif t=='Z': i+=1
        subs.append((start,segs))
    return subs
def dist(p,a,b):
    (x,y),(x1,y1),(x2,y2)=p,a,b; L=math.hypot(x2-x1,y2-y1)
    if L<1e-9: return math.hypot(x-x1,y-y1)
    return abs((x2-x1)*(y1-y)-(x1-x)*(y2-y1))/L
TOL=0.25
def simp(d):
    out=[]
    for start,segs in parse(d):
        cur=start; s2=[]
        for k,p in segs:
            if k=='C' and dist(p[0],cur,p[2])<TOL and dist(p[1],cur,p[2])<TOL: s2.append(('L',[p[2]]))
            else: s2.append((k,p))
            cur=p[-1]
        # merge collinear L runs
        m=[];cur=start
        for k,p in s2:
            if k=='L' and m and m[-1][0]=='L':
                prev_start=m[-1][2]; 
                # check all points of the run stay within TOL
                run=m[-1][3]+[m[-1][1][0]]
                if all(dist(q,prev_start,p[0])<TOL for q in run):
                    m[-1]=('L',[p[0]],prev_start,run); cur=p[0]; continue
            m.append((k,p,cur,[]) ); cur=p[-1]
        f=lambda q:f'{round(q[0],1):g} {round(q[1],1):g}'
        s=f'M{f(start)}'
        for k,p,_,_ in m:
            if k=='L' and math.hypot(p[0][0]-start[0],p[0][1]-start[1])<0.05 and (k,p) is m[-1][:2]: continue
            s+=k+' '.join(f(q) for q in p) if k=='C' else 'L'+f(p[0])
        out.append(s+'Z')
    return ''.join(out)
if __name__=='__main__':
    src,dst=sys.argv[1],sys.argv[2]
    d=json.load(open(f'paths_{src}.json'))
    r={k:[simp(x) for x in v] for k,v in d.items()}
    json.dump(r,open(f'paths_{dst}.json','w')); print(dst,sum(map(len,r['mark']+r['word'])))
