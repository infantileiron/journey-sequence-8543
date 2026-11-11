import type {Dictionary} from '../types/entities';export function label(code:string,dictionary:Dictionary){return dictionary.entries.find(e=>e.code===code)?.label||code}
