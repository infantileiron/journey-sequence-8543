import {ref} from 'vue';import type {User} from '../types/entities';
export const user=ref<User|null>(JSON.parse(sessionStorage.getItem('journey-user')||'null'));
export function saveSession(token:string,value:User){sessionStorage.setItem('journey-token',token);sessionStorage.setItem('journey-user',JSON.stringify(value));user.value=value}
export function clearSession(){sessionStorage.removeItem('journey-token');sessionStorage.removeItem('journey-user');user.value=null}
