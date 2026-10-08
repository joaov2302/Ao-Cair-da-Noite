import { z } from 'zod';
export const attrKeys = ['FOR','AGI','VIG','PRE','INT'] as const;
export const labels = {FOR:'Força',AGI:'Agilidade',VIG:'Vigor',PRE:'Presença',INT:'Intelecto'};
export const draftSchema = z.object({name:z.string().max(120),concept:z.string(),race:z.string(),classId:z.string(),archetypeId:z.string(),
  attributes:z.object({FOR:z.number().int().min(0).max(3).nullable(),AGI:z.number().int().min(0).max(3).nullable(),VIG:z.number().int().min(0).max(3).nullable(),PRE:z.number().int().min(0).max(3).nullable(),INT:z.number().int().min(0).max(3).nullable()}),
  skills:z.string(),equipment:z.string(),techniques:z.string(),techniqueKind:z.string(),uniqueAbility:z.string(),story:z.string(),assetId:z.number().nullable()});
export type Draft = z.infer<typeof draftSchema>;
export const emptyDraft = (): Draft => ({name:'',concept:'',race:'',classId:'',archetypeId:'guerreiro',attributes:{FOR:1,AGI:1,VIG:1,PRE:1,INT:1},skills:'',equipment:'',techniques:'',techniqueKind:'',uniqueAbility:'',story:'',assetId:null});
export type Report = {maxima:{pv:number|null;pe:number|null;san:number|null}; errors:string[];warnings:string[];pending:{id:string;message:string}[];canApprove:boolean;explanations:{field:string;value:number;formula:string;inputs:Record<string,number>;sourceDocument:string;sourceSection:string;paragraph:number}[]};
export type Submission = {id:number;revision:number;snapshot:Draft;report:Report;current:boolean;createdAt:string;review:{status:string;comment:string}|null};
export type Character = {id:string;campaignId:number;ownerId:number;revision:number;rulesetVersion:number;data:Draft;resources:Record<string,number>;report:Report;approved:boolean;submissions:Submission[];decisions:{id:number;ruleId:string;value:object;reason:string}[]};
export type Campaign = {id:number;name:string;role:'master'|'player';rulesetVersion?:number};
export type Archetype = {id:string;name:string;role:string;initial:string;trails:string[];pv:number;pe:number;san:number};
export type Catalog = {archetypes:Archetype[];classes:{id:string;name:string;skill:string}[];assets:{id:number;label:string}[];rulesetVersion:number;sourceSha256:string};
