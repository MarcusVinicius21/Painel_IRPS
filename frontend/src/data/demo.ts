import citiesData from './cities.json';
import type {City,Item,Inputs,State} from '../domain/model';
export const cities:City[]=citiesData;
export const families=['Materiais de consumo','Medicamentos','Veículos','Serviços contínuos','Obras'];
const bases=[
 ['papel','Papel A4, caixa com 10 resmas','caixa de 10 resmas',250,'Pontos atendidos','Caixas por ponto'],
 ['medicamento','Aciclovir 200 mg, comprimido','comprimido',0.15,'Atendimentos do exemplo','Comprimidos por atendimento'],
 ['veiculo','Veículo de 5 lugares, configuração do exemplo','veículo',118000,'Rotas do exemplo','Veículos por rota'],
 ['servico','Limpeza predial, hora de serviço','hora',27.5,'Postos de serviço','Horas por posto no horizonte'],
 ['obra','Pavimentação, área do projeto ilustrativo','m²',145,'Área do projeto em m²','Coeficiente do projeto'],
];
const names=[['Luvas, caixa de 100 unidades','Detergente 500 mL','Água sanitária 5 L','Saco para resíduos, pacote de 100','Papel toalha, pacote','Caneta, caixa de 50','Álcool 70%, frasco de 1 L'],['Paracetamol 500 mg','Dipirona 500 mg','Amoxicilina 500 mg','Solução fisiológica 100 mL','Omeprazol 20 mg'],['Ambulância tipo A','Veículo utilitário','Micro-ônibus de 28 lugares','Caminhão de apoio','Motocicleta de serviço'],['Vigilância por posto-hora','Manutenção predial por hora','Atendimento por hora','Suporte de TI por usuário-mês','Jardinagem por hora'],['Drenagem em metro linear','Pintura em m²','Escavação em m³','Calçada em m²','Cobertura em m²']];
export const catalog:Item[]=bases.map((b,i)=>({id:String(b[0]),name:String(b[1]),unit:String(b[2]),price:Number(b[3]),family:families[i],step:i===4?0.01:1,driver:String(b[4]),rateLabel:String(b[5]),version:1}));
for(let i=0;i<95;i++){
 const f=i%5,n=Math.floor(i/5);let unit=catalog[f].unit;
 if(f===0)unit=['caixa de 100 unidades','frasco de 500 mL','galão de 5 L','pacote de 100 unidades','pacote','caixa de 50 unidades','frasco de 1 L'][n%7];
 if(f===1)unit=['comprimido','comprimido','cápsula','frasco de 100 mL','cápsula'][n%5];
 if(f===3&&n%5===0)unit='posto-hora';
 if(f===3&&n%5===3)unit='usuário-mês';
 if(f===4)unit=['m','m²','m³','m²','m²'][n%5];
 const driver=f===4?(unit==='m'?'Extensão do projeto em metros':unit==='m³'?'Volume do projeto em m³':'Área do projeto em m²'):f===3&&unit==='usuário-mês'?'Usuários atendidos':catalog[f].driver;
 catalog.push({id:`cat-${i+1}`,name:n<names[f].length?names[f][n]:`${names[f][n%names[f].length]}, especificação ${n+1}`,family:families[f],unit,step:f===4?0.01:1,price:f===0?28+n*2:f===1?0.2+n*.1:f===2?130000+n*10000:f===3?29+n:160+n*5,driver,rateLabel:unit==='usuário-mês'?'Meses no horizonte':catalog[f].rateLabel,version:1});
}
export function defaultInputs(city:City,item:Item):Inputs{
 if(item.driver==='A confirmar')return {driver:null,rate:null,reserve:0,stock:null,incoming:null,floor:0,ceiling:1000000,source:''};
 const seed=Number(city.id)%137;
 let driver=80+seed,rate=1,stock=10+seed%25;
 if(item.family==='Medicamentos'){driver=800+seed*3;rate=12;stock=200;}
 if(item.family==='Veículos'){driver=1+seed%5;rate=1;stock=0;}
 if(item.family==='Serviços contínuos'){driver=1+seed%4;rate=item.unit==='usuário-mês'?12:2112;stock=0;}
 if(item.family==='Obras'){driver=500+seed*8;rate=1;stock=0;}
 if(item.id==='papel'&&city.id==='3131307'){driver=150;stock=30;}
 if(item.id==='papel'&&city.id==='3101607'){driver=110;stock=25;}
 return {driver,rate,reserve:0,stock:item.id==='papel'&&city.id==='3303005'?null:stock,incoming:0,floor:0,ceiling:1000000,source:'Parâmetros sintéticos desta demonstração; não são dados municipais.'};
}
export function initial():State{return {schema:1,role:'consorcio',catalog:structuredClone(catalog),scenario:{title:'Compra compartilhada 2027',period:'2027',cities:['3131307','3101607','3303005'],items:['papel','medicamento','veiculo'],activeItem:'papel',mode:'A',inputs:{},prices:{},allocations:{},globalConfirmed:false,budget:600000,reviewed:false},versions:[],revision:1,sourceFailure:false,retified:false,watches:[]};}
export const roles=[['consulta','Consulta pública (demo)'],['consorcio','Consórcio (demo)'],['fornecedor','Empresa exemplo (demo)'],['curadoria','Curadoria (demo)'],['admin','Administração (demo)']];
export const phaseLabels=['Estimado','Homologado','Contratado','Pago'];
export const sourceNames=['PNCP','Compras.gov.br','IBGE','INEP','SICONFI','TCE-MG','TCE-RJ','Portais municipais','Transferegov','Diários oficiais','BPS','CMED','SINAPI','SICRO','SIOPS','SIOPE'];
