from pathlib import Path
import json,shutil,hashlib,difflib,subprocess,sys
from PIL import Image,ImageChops,ImageOps,ImageStat
sys.stdout.reconfigure(encoding='utf-8')
r=Path('docs/IRPS_REFINAMENTO_PIXEL_PERFECT');run=Path('.runtime/pixel-perfect');inputdir=run/'entrada';
refs=sorted((inputdir/'referencias/01_REFERENCIAS_VISUAIS').glob('*.png'))
boxes=json.loads((run/'bounding-boxes.json').read_text());inventory=json.loads((r/'inventario.json').read_text(encoding='utf-8'))
metrics=[]
for i,ref in enumerate(refs):
 sid=f'{i:02d}';d=r/'comparacoes'/sid;d.mkdir(parents=True,exist_ok=True)
 shutil.copy2(ref,d/'referencia.png');w,h=Image.open(ref).size
 real=run/'depois'/f'{sid}-real-parcial-{w}.png';qa=run/'depois'/f'{sid}-sintetico-{w}.png'
 shutil.copy2(real,d/'implementacao-real-parcial.png');shutil.copy2(qa,d/'implementacao-sintetica.png')
 a=Image.open(ref).convert('RGB');b=Image.open(qa).convert('RGB');assert a.size==b.size
 side=Image.new('RGB',(w*2,h),'white');side.paste(a,(0,0));side.paste(b,(w,0));side.save(d/'lado-a-lado.png')
 Image.blend(a,b,.5).save(d/'sobreposicao-50.png')
 diff=ImageChops.difference(a,b);heat=ImageOps.colorize(ImageOps.grayscale(diff).point(lambda x:min(255,x*3)),(255,255,255),(222,0,30));heat.save(d/'diferencas.png')
 stat=ImageStat.Stat(diff);data={'screen':sid,'viewport':{'width':w,'height':h,'dpr':1},'raw_mean_absolute_rgb_error_0_255':stat.mean,'metric_is_not_a_fidelity_percentage':True,'caveat':'Textos, dados, estados, vetores e anti-aliasing diferem; o mapa não certifica identidade visual.'}
 measured=next(s for s in boxes if s['screen']==sid and s['mode']=='real-parcial');data['geometry']=[]
 for actual,expected in zip(measured['boxes'],inventory['expected_boxes'][sid]):
  delta={k:round(actual[k]-v,3) for k,v in zip(['x','y','width','height'],expected[1:])} if not actual.get('missing') else {}
  data['geometry'].append({'selector':expected[0],'expected':dict(zip(['x','y','width','height'],expected[1:])),'actual':actual,'delta':delta,'within_4px':bool(delta) and max(map(abs,delta.values()))<=4})
 data['all_measured_main_boxes_within_4px']=all(b['within_4px'] for b in data['geometry']);metrics.append(data)
 (d/'medidas.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
 md=['# Referência '+sid,'','## Medições','', '| Caixa | Δx | Δy | Δlargura | Δaltura | ±4 px |','|---|---:|---:|---:|---:|---|']
 for m in data['geometry']:
  delta=m['delta'];md.append('| '+m['selector']+' | '+' | '.join(str(delta.get(k,'ausente')) for k in ['x','y','width','height'])+' | '+str(m['within_4px'])+' |')
 md+=['','As medições cobrem caixas principais. Não validam cada ícone, controle, fonte ou espaçamento interno.','Veja RELATORIO_DIVERGENCIAS.md para o julgamento visual e as exceções.']
 (d/'CORRECOES_E_MEDIDAS.md').write_text('\n'.join(md),encoding='utf-8')
for name in ('antes','global'):
 target=r/('capturas-'+name);target.mkdir(exist_ok=True)
 for p in (run/name).glob('*.png'):shutil.copy2(p,target/p.name)
responsivo=r/'responsivo';responsivo.mkdir(exist_ok=True)
for p in (run/'depois').glob('*responsivo*'):shutil.copy2(p,responsivo/p.name)
for n in ('AUDITORIA_INDEPENDENTE_FIDELIDADE_7_TELAS.md','PROMPT_CODEX_REFINAMENTO_VISUAL_RIGOROSO.md'):
 d=r/'entrada';d.mkdir(exist_ok=True);shutil.copy2(inputdir/n,d/n)
(r/'medidas-consolidadas.json').write_text(json.dumps(metrics,ensure_ascii=False,indent=2),encoding='utf-8')
shutil.copy2(run/'bounding-boxes.json',r/'bounding-boxes.json')
d=r/'documentos-renderizados';d.mkdir(exist_ok=True)
for p in (run/'documentos').rglob('*'):
 if p.is_file():
  q=d/p.relative_to(run/'documentos');q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
# Review patch relative to the physical pre-round snapshot. Preserve original line content.
base=json.loads((run/'baseline.json').read_text());changed=[];patch=[]
for folder in ('frontend','backend','scripts'):
 for p in Path(folder).rglob('*'):
  n=p.as_posix()
  if not p.is_file() or p.suffix not in ('.tsx','.ts','.css','.py','.cjs') or any(part in ('node_modules','__pycache__','.venv') for part in p.parts):continue
  digest=hashlib.sha256(p.read_bytes()).hexdigest()
  if base.get(n)==digest:continue
  changed.append(n);old=run/'baseline'/p
  # New scripts weren't in the baseline. Existing source files were copied byte-for-byte.
  before=old.read_text(encoding='utf-8-sig') if old.exists() else ''
  after=p.read_text(encoding='utf-8-sig')
  patch.extend(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='a/'+n,tofile='b/'+n))
(r/'diff-refinamento.patch').write_text(''.join(patch),encoding='utf-8')
(r/'arquivos-alterados.json').write_text(json.dumps(changed,indent=2),encoding='utf-8')
core={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in Path('backend/irps_core').glob('*.py')}
(r/'integridade-v4.json').write_text(json.dumps({'unchanged':all(base['backend/irps_core/'+n]==v for n,v in core.items()),'sha256':core},indent=2),encoding='utf-8')
print('Comparações geradas:',len(metrics),'caixas válidas',sum(sum(m['within_4px'] for m in d['geometry']) for d in metrics),'de',sum(len(d['geometry']) for d in metrics));print('Arquivos de código alterados nesta rodada:',len(changed))
