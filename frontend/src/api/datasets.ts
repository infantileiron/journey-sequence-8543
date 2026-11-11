import {request} from './client';
import type {Dataset,DatasetBatch,SupplementResult,QuarantineRow} from '../types/entities';
export const list=()=>request<Dataset[]>('/datasets');
export const create=(data:unknown)=>request<Dataset>('/datasets','POST',data);
export const supplement=(id:string,data:unknown)=>request<SupplementResult>(`/datasets/${id}/supplement`,'POST',data);
export const batches=(id:string)=>request<DatasetBatch[]>(`/datasets/${id}/batches`);
export const quarantine=(id:string)=>request<QuarantineRow[]>(`/datasets/${id}/quarantine`);
