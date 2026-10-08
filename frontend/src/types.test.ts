import { describe, expect, it } from 'vitest';
import { draftSchema, emptyDraft } from './types';
describe('Formato do rascunho',()=>{
  it('preserva atributos ausentes e diferencia zero',()=>{
    const data = emptyDraft(); data.attributes.FOR = null; data.attributes.AGI = 0;
    const result = draftSchema.parse(data);
    expect(result.attributes.FOR).toBeNull();expect(result.attributes.AGI).toBe(0);
  });
  it('não converte entrada decimal ou atributo fora da faixa',()=>{
    for (const value of [1.5,-1,4]) {
      const data=emptyDraft(); data.attributes.VIG=value;
      expect(draftSchema.safeParse(data).success).toBe(false);
    }
  });
});
