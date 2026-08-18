(() => {
  'use strict';

  const normalize = (value) => String(value || '').toLowerCase().replace(/[‐‑‒–—―]/g, '-').replace(/\s+/g, ' ').trim();
  const preparationRules = [
    ['semi_combed', ['セミコーマ', '半精梳', '半精梳棉', 'semi-combed', 'semi combed']],
    ['combed', ['コーマ', 'コーマ綿', '精梳', '精梳棉', 'combed', 'combed cotton']],
    ['carded', ['カード綿', '普梳', '普梳棉', 'carded', 'carded cotton']]
  ];
  const spinningRules = [
    ['Compact', ['コンパクト紡績', '紧密纺', 'compact spinning']],
    ['MVS', ['mvs', 'vortex', '涡流纺', '渦流紡']],
    ['Air Jet', ['エアジェット紡績', '喷气纺', 'air-jet spinning', 'air jet spinning']],
    ['Open End', ['oe', 'open-end', 'open end', 'ローター紡績', '气流纺', '转杯纺', 'rotor spinning']],
    ['Ring', ['リング紡績', '环锭纺', 'ring spinning']]
  ];

  const containsAny = (text, terms) => terms.some((term) => text.includes(normalize(term)));
  const detect = (text, rules, fallback) => {
    const normalized = normalize(text);
    const match = rules.find(([, terms]) => containsAny(normalized, terms));
    return match?.[0] || fallback;
  };

  function formEvidence(form) {
    return [
      form.elements.yarnName?.value,
      form.elements.yarnCode?.value,
      form.elements.compositionRaw?.value,
      form.elements.yarnStructure?.value,
      form.elements.processingMethod?.value,
      form.elements.notes?.value,
      form.elements.sourceUrl?.value
    ].filter(Boolean).join(' ');
  }

  function applyExplicitEvidence(form) {
    if (!form?.elements?.cottonPreparation || !form?.elements?.spinningMethod) return;
    const evidence = formEvidence(form);
    if (form.elements.cottonPreparation.value === 'unconfirmed') {
      const detectedPreparation = detect(evidence, preparationRules, 'unconfirmed');
      if (detectedPreparation !== 'unconfirmed') form.elements.cottonPreparation.value = detectedPreparation;
    }
    if (!form.elements.spinningMethod.value || form.elements.spinningMethod.value === 'Unknown') {
      const detectedSpinning = detect(evidence, spinningRules, 'Unknown');
      if (detectedSpinning !== 'Unknown') form.elements.spinningMethod.value = detectedSpinning;
    }
  }

  document.addEventListener('submit', (event) => {
    if (event.target?.id === 'capture') applyExplicitEvidence(event.target);
  }, true);

  window.KnitCompassYarnTaxonomyGuard = Object.freeze({
    detectCottonPreparation: (text) => detect(text, preparationRules, 'unconfirmed'),
    detectSpinningMethod: (text) => detect(text, spinningRules, 'Unknown')
  });
})();
