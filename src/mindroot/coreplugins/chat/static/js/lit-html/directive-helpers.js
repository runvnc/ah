import{_$LH as o}from"./lit-html.js";
/**
 * @license
 * Copyright 2020 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */const{I:t}=o,i=o=>null===o||"object"!=typeof o&&"function"!=typeof o,n={HTML:1,SVG:2,MATHML:3},e=(o,t)=>void 0===t?void 0!==o?._$litType$:o?._$litType$===t,l=o=>null!=o?._$litType$?.h,c=o=>void 0!==o?._$litDirective$,d=o=>o?._$litDirective$,f=o=>void 0===o.strings,s=()=>document.createComment(""),r=(o,i,n)=>{const e=o._$AA.parentNode,l=void 0===i?o._$AB:i._$AA;if(void 0===n){const i=e.insertBefore(s(),l),c=e.insertBefore(s(),l);n=new t(i,c,o,o.options)}else{const t=n._$AB.nextSibling,i=n._$AM,c=i!==o;if(c){let t;n._$AQ?.(o),n._$AM=o,void 0!==n._$AP&&(t=o._$AU)!==i._$AU&&n._$AP(t)}if(t!==l||c){let o=n._$AA;for(;o!==t;){const t=o.nextSibling;e.insertBefore(o,l),o=t}}}return n},v=(o,t,i=o)=>(o._$AI(t,i),o),u={},m=(o,t=u)=>o._$AH=t,p=o=>o._$AH,M=o=>{o._$AP?.(!1,!0);let t=o._$AA;const i=o._$AB.nextSibling;for(;t!==i;){const o=t.nextSibling;t.remove(),t=o}},h=o=>{o._$AR()};export{n as TemplateResultType,h as clearPart,p as getCommittedValue,d as getDirectiveClass,r as insertPart,l as isCompiledTemplateResult,c as isDirectiveResult,i as isPrimitive,f as isSingleExpression,e as isTemplateResult,M as removePart,v as setChildPartValue,m as setCommittedValue};
//# sourceMappingURL=directive-helpers.js.map
