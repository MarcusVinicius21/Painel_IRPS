export type City={id:string;name:string;uf:string};
export type Item={id:string;name:string;family:string;unit:string;step:number;price:number|null;driver:string;rateLabel:string;version:number};
export type Inputs={driver:number|null;rate:number|null;reserve:number;stock:number|null;incoming:number|null;floor:number;ceiling:number;source:string};
export type Allocation={target:number;reason:string;weights:Record<string,number>;floors:Record<string,number>;caps:Record<string,number>};
export type Scenario={title:string;period:string;cities:string[];items:string[];mode:'A'|'B';activeItem:string;inputs:Record<string,Inputs>;prices:Record<string,number|null>;allocations:Record<string,Allocation>;globalConfirmed:boolean;budget:number|null;reviewed:boolean};
export type Version={id:number;date:string;scenario:Scenario};
export type State={schema:1;role:string;scenario:Scenario;catalog:Item[];versions:Version[];revision:number;sourceFailure:boolean;retified:boolean;watches:string[]};
export type Line={city:City;item:Item;q:number|null;price:number|null;value:number|null;status:string;inputs:Inputs};
