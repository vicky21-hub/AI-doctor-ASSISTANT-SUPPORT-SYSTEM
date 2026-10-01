/**
 * parseDiagnosisReport.ts
 *
 * Parses the exact backend diagnosis text format into structured data.
 *
 * Actual backend format observed:
 *  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 *  **📋  AI HEALTH CONSULTATION REPORT**
 *  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 *
 *  **🧠  Symptoms Assessed In This Consultation:**
 *    1. Fever
 *
 *  **🧬  CLINICAL ASSESSMENT**
 *  🎯 **Most Likely Condition:**  Pneumonia
 *  📊 **Confidence:**  70%  [███████░░░]  — High confidence
 *  🔴 **Risk Level:**  High
 *  📌 **Recommended Action:**  🚨 **Urgent Care** — See a doctor today…
 *  📖 **Clinical Note:**  An infection of the lungs…
 *
 *  Section titles appear as either:
 *    **EMOJI  TITLE**            ← full-line bold
 *    **🧠  Symptoms Assessed…:** ← full-line bold with colon
 *    🚨 **HIGH RISK — …**        ← emoji BEFORE the bold (high-risk banner)
 *  Data lines always have emoji prefix followed by **label:**  value
 */

export interface AltCondition {
  name: string;
  confidence: number;
  label: string;
}

export interface DiagnosisData {
  symptomsAssessed: string[];
  findingsBySymptom: { symptom: string; items: string[] }[];
  condition: string;
  confidence: number;
  confidenceLabel: string;
  riskLevel: 'HIGH' | 'MEDIUM' | 'LOW' | 'UNKNOWN';
  recommendedAction: string;
  clinicalNote: string;
  isHighRisk: boolean;
  alternativeConditions: AltCondition[];
  recommendedTests: string[];
  medicines: string[];
  selfCare: string[];
  diet: string[];
  specialist: string;
  emergencyWarnings: string[];
  disclaimer: string[];
  duration: string;
  severity: string;
  temperature: string;
  keyFindings: string[];
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

/** Remove all **bold** markers and trim. */
function clean(s: string): string {
  return s.replace(/\*\*/g, '').replace(/\*/g, '').trim();
}

/**
 * Strip every leading emoji / bullet / symbol character and whitespace.
 * Handles multi-byte emoji (e.g. 🧪, 🌡️, 👩‍⚕️) by scanning with the
 * Unicode Emoji regex category.  Falls back to a broad character class.
 */
function stripLeading(s: string): string {
  // Remove leading whitespace, bullet chars, and emoji
  return s
    .replace(/^[\s\t]+/, '')
    // Unicode emoji sequences (incl. variation selectors and ZWJ)
    .replace(/^(\p{Emoji_Presentation}|\p{Emoji}\uFE0F)(\u200D(\p{Emoji_Presentation}|\p{Emoji}\uFE0F))*[\s\uFE0F]*/gu, '')
    // Any leftover common bullet / warning symbols
    .replace(/^[✓✔•⚠⚕️🔴🟡🟢🚨🎯📊📌📖📋📄🧠🧬🔍🌡️⏱️🟣]+[\s]*/gu, '')
    .replace(/^\uFE0F/, '')
    .trim();
}

/** Normalise a string to an uppercase key suitable for section matching. */
function toKey(s: string): string {
  return clean(stripLeading(s)).toUpperCase().replace(/[:\s]+/g, ' ').trim();
}

/**
 * Split the raw report into named sections.
 *
 * A new section starts when a line is:
 *  1. A ━━━ separator            → ignored (just marks boundaries)
 *  2. A full-bold title:  **...** on its own line
 *  3. A partial-bold:     🧠 **Title** or similar where the label is bold
 *     but only if the entire visible content (after stripping emoji) is
 *     just the bold part (no value on the same line).
 */
function splitSections(text: string): Record<string, string[]> {
  const sections: Record<string, string[]> = {};
  let key = '__preamble__';
  sections[key] = [];

  for (const raw of text.split(/\r?\n/)) {
    const line = raw.trimEnd();
    const trimmed = line.trim();

    // Skip separator lines
    if (/^━{3,}/.test(trimmed) || /^-{3,}/.test(trimmed)) continue;

    // ── Detect section-title lines ───────────────────────────────────────
    // Pattern A: the ENTIRE line (after leading emoji strip) is **something**
    //   e.g.  "**📋  AI HEALTH CONSULTATION REPORT**"
    //   e.g.  "**🧬  CLINICAL ASSESSMENT**"
    const fullBoldMatch = trimmed.match(/^\*\*(.+?)\*\*\s*$/);
    if (fullBoldMatch) {
      const candidate = toKey(fullBoldMatch[1]);
      // Skip the report-header title itself (it's just a banner, not a data section)
      if (!candidate.includes('AI HEALTH CONSULTATION REPORT')) {
        key = candidate;
        if (!sections[key]) sections[key] = [];
        continue;
      }
    }

    // Pattern B: leading emoji + **Title** with no value after (symptoms header)
    //   e.g.  "**🧠  Symptoms Assessed In This Consultation:**"
    //   (already caught by Pattern A above since whole line is bold)
    // But some titles have no ** e.g. inline bold label + colon only:
    const emojiThenBoldNoValue = trimmed.match(/^(?:\p{Emoji_Presentation}|\p{Emoji}\uFE0F)\S*\s+\*\*(.+?)\*\*\s*:?\s*$/u);
    if (emojiThenBoldNoValue) {
      const candidate = toKey(emojiThenBoldNoValue[1]);
      key = candidate;
      if (!sections[key]) sections[key] = [];
      continue;
    }

    // Collect into current section
    sections[key].push(line);
  }

  return sections;
}

/** Return trimmed, non-empty lines from a section, stripping ━ rows. */
function lines(secs: Record<string, string[]>, key: string): string[] {
  return (secs[key] ?? [])
    .map(l => l.trim())
    .filter(l => l.length > 0 && !/^━{3,}/.test(l));
}

/**
 * Extract the value from a data line like:
 *   🎯 **Most Likely Condition:**  Pneumonia
 *   📊 **Confidence:**  70%  [███████░░░]  — High confidence
 *
 * Returns empty string if the label does not match.
 */
function extractInlineValue(line: string, ...labels: string[]): string {
  const stripped = clean(stripLeading(line));
  for (const label of labels) {
    // Match "Label:  value" or "Label  value"
    const re = new RegExp(`^${label.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\s*:?\\s*(.+)`, 'i');
    const m = stripped.match(re);
    if (m) return clean(m[1]).replace(/\[[\u2588\u2591]+\]/g, '').trim();
  }
  return '';
}

// ─── Main parser ──────────────────────────────────────────────────────────────

export function parseDiagnosisReport(text: string): DiagnosisData {
  console.log('RAW REPORT', text);

  const secs = splitSections(text);
  console.log('SECTIONS DETECTED', Object.keys(secs));

  // ── Symptoms assessed ────────────────────────────────────────────────────
  const symptomsAssessed: string[] = [];
  const sympKey = Object.keys(secs).find(k =>
    k.includes('SYMPTOM') && (k.includes('ASSESSED') || k.includes('CONSULTATION'))
  );
  if (sympKey) {
    for (const l of lines(secs, sympKey)) {
      const m = l.match(/^\d+\.\s*(.+)/);
      if (m) symptomsAssessed.push(clean(m[1]));
    }
  }
  // Fallback: global numbered list in preamble area
  if (!symptomsAssessed.length) {
    for (const l of lines(secs, '__preamble__')) {
      const m = l.match(/^\d+\.\s*(.+)/);
      if (m) symptomsAssessed.push(clean(m[1]));
    }
  }

  // ── Findings by symptom ──────────────────────────────────────────────────
  const findingsBySymptom: { symptom: string; items: string[] }[] = [];
  const findKey = Object.keys(secs).find(k => k.includes('FINDINGS BY SYMPTOM'));
  if (findKey) {
    let current: { symptom: string; items: string[] } | null = null;
    for (const l of lines(secs, findKey)) {
      const bold = l.match(/^\*\*(.+?)\*\*$/);
      if (bold) {
        if (current) findingsBySymptom.push(current);
        current = { symptom: clean(bold[1]), items: [] };
      } else if (current && /^[•\u2022]/.test(l)) {
        const item = clean(l.replace(/^[•\u2022]\s*/, ''));
        if (item) current.items.push(item);
      }
    }
    if (current) findingsBySymptom.push(current);
  }

  // ── Patient summary ──────────────────────────────────────────────────────
  let duration = '', severity = '', temperature = '';
  const keyFindings: string[] = [];
  const patKey = Object.keys(secs).find(k => k.includes('PATIENT SUMMARY'));
  if (patKey) {
    for (const l of lines(secs, patKey)) {
      const v = (label: string) => extractInlineValue(l, label);
      if (!duration    && v('Duration'))    duration    = v('Duration').replace(/\[[\u2588\u2591]+\]/, '').trim();
      if (!severity    && v('Severity'))    severity    = v('Severity').replace(/\[[\u2588\u2591]+\]/, '').trim();
      if (!temperature && v('Temperature')) temperature = v('Temperature');
      if (/^[•\u2022]/.test(l)) {
        const item = clean(l.replace(/^[•\u2022]\s*/, ''));
        if (item) keyFindings.push(item);
      }
    }
  }
  // Fallback: extract from findings-by-symptom block
  if (!duration || !severity) {
    for (const fb of findingsBySymptom) {
      for (const item of fb.items) {
        if (!duration    && /^Duration:/i.test(item))    duration    = item.replace(/^Duration:\s*/i, '');
        if (!severity    && /^Severity:/i.test(item))    severity    = item.replace(/^Severity:\s*/i, '').replace(/\[[\u2588\u2591]+\]/, '').trim();
        if (!temperature && /^Temperature:/i.test(item)) temperature = item.replace(/^Temperature:\s*/i, '');
      }
    }
  }

  // ── Clinical assessment ──────────────────────────────────────────────────
  let condition = '', confidence = 0, confidenceLabel = 'Low';
  let riskLevel: DiagnosisData['riskLevel'] = 'UNKNOWN';
  let recommendedAction = '', clinicalNote = '';

  const clinKey = Object.keys(secs).find(k => k.includes('CLINICAL ASSESSMENT'));
  if (clinKey) {
    for (const l of lines(secs, clinKey)) {
      if (!condition) {
        const v = extractInlineValue(l, 'Most Likely Condition', 'Condition');
        if (v) condition = v;
      }
      if (!confidence) {
        const v = extractInlineValue(l, 'Confidence', 'Confidence Score');
        if (v) {
          const m = v.match(/(\d+)%/);
          if (m) {
            confidence = parseInt(m[1]);
            const lm = v.match(/[—\-]\s*(High|Medium|Low)\s*confidence/i);
            confidenceLabel = lm ? lm[1] : confidence >= 70 ? 'High' : confidence >= 40 ? 'Medium' : 'Low';
          }
        }
      }
      if (riskLevel === 'UNKNOWN') {
        const v = extractInlineValue(l, 'Risk Level', 'Risk');
        if (v) {
          const r = v.toUpperCase();
          if (r.includes('HIGH'))        riskLevel = 'HIGH';
          else if (r.includes('MEDIUM')) riskLevel = 'MEDIUM';
          else if (r.includes('LOW'))    riskLevel = 'LOW';
        }
      }
      if (!recommendedAction) {
        const v = extractInlineValue(l, 'Recommended Action', 'Action');
        if (v) recommendedAction = clean(stripLeading(v));
      }
      if (!clinicalNote) {
        const v = extractInlineValue(l, 'Clinical Note', 'Note');
        if (v) clinicalNote = v;
      }
    }
  }

  // ── Global regex fallbacks (robust — work even if section parsing fails) ──
  if (!condition) {
    const m = text.match(/Most Likely Condition\s*:?\s*\*?\*?\s*([^\n*[\]]+)/i);
    if (m) condition = clean(m[1]).trim();
  }
  if (!confidence) {
    const m = text.match(/Confidence\s*(?:Score)?\s*:\s*\*?\*?\s*(\d+)%/i);
    if (m) confidence = parseInt(m[1]);
  }
  if (riskLevel === 'UNKNOWN') {
    const m = text.match(/Risk Level\s*:\s*\*?\*?\s*(High|Medium|Low)/i);
    if (m) {
      const r = m[1].toUpperCase();
      riskLevel = r === 'HIGH' ? 'HIGH' : r === 'MEDIUM' ? 'MEDIUM' : 'LOW';
    }
  }
  // Still unknown → check for banner
  if (riskLevel === 'UNKNOWN') {
    if (/HIGH RISK/i.test(text))        riskLevel = 'HIGH';
    else if (/MEDIUM RISK/i.test(text)) riskLevel = 'MEDIUM';
    else if (/LOW RISK/i.test(text))    riskLevel = 'LOW';
  }
  if (!clinicalNote) {
    const m = text.match(/Clinical Note\s*:\s*\*?\*?\s*([^\n]+)/i);
    if (m) clinicalNote = clean(m[1]).trim();
  }
  if (!recommendedAction) {
    const m = text.match(/Recommended Action\s*:\s*\*?\*?\s*([^\n]+)/i);
    if (m) recommendedAction = clean(stripLeading(m[1])).trim();
  }

  // Confidence label fallback
  if (confidence && confidenceLabel === 'Low') {
    confidenceLabel = confidence >= 70 ? 'High' : confidence >= 40 ? 'Medium' : 'Low';
  }

  // Warn if critical fields still missing
  if (!condition)  console.warn('[DiagnosisParser] condition not found');
  if (!confidence) console.warn('[DiagnosisParser] confidence not found');
  if (riskLevel === 'UNKNOWN') console.warn('[DiagnosisParser] riskLevel not found');

  // ── Alternative conditions ────────────────────────────────────────────────
  const alternativeConditions: AltCondition[] = [];
  const altKey = Object.keys(secs).find(k => k.includes('ALTERNATIVE'));
  if (altKey) {
    for (const l of lines(secs, altKey)) {
      // "  1. **Malaria**  —  70% [███████░░░] (High)"
      const m = l.match(/\d+\.\s*\*?\*?(.+?)\*?\*?\s*[—\-]\s*(\d+)%[^(]*\((\w+)\)/);
      if (m) {
        alternativeConditions.push({
          name: clean(m[1]).trim(),
          confidence: parseInt(m[2]),
          label: m[3],
        });
      }
    }
  }

  // ── Recommended tests ─────────────────────────────────────────────────────
  const recommendedTests: string[] = [];
  const testKey = Object.keys(secs).find(k => k.includes('RECOMMENDED TEST'));
  if (testKey) {
    for (const l of lines(secs, testKey)) {
      const item = clean(stripLeading(l));
      if (item) recommendedTests.push(item);
    }
  }

  // ── Medicines ─────────────────────────────────────────────────────────────
  const medicines: string[] = [];
  const medKey = Object.keys(secs).find(k => k.includes('MEDICATION'));
  if (medKey) {
    for (const l of lines(secs, medKey)) {
      if (/consult|pharmacist|always|warning/i.test(l)) continue;
      const item = clean(stripLeading(l))
        .replace(/\s*\*?\(require[^)]*\)\*?/gi, '')
        .trim();
      if (item) medicines.push(item);
    }
  }

  // ── Self care ─────────────────────────────────────────────────────────────
  const selfCare: string[] = [];
  const careKey = Object.keys(secs).find(k => k.includes('WHAT YOU CAN DO'));
  if (careKey) {
    for (const l of lines(secs, careKey)) {
      // Lines start with "  ✓ rest"
      const item = l.replace(/^[\s✓✔]+/, '').trim();
      if (item) selfCare.push(clean(item));
    }
  }

  // ── Diet ──────────────────────────────────────────────────────────────────
  const diet: string[] = [];
  const dietKey = Object.keys(secs).find(k => k.includes('RECOMMENDED DIET'));
  if (dietKey) {
    for (const l of lines(secs, dietKey)) {
      const item = clean(stripLeading(l));
      if (item) diet.push(item);
    }
  }

  // ── Specialist ────────────────────────────────────────────────────────────
  let specialist = '';
  const specKey = Object.keys(secs).find(k => k.includes('SPECIALIST'));
  if (specKey) {
    for (const l of lines(secs, specKey)) {
      if (/^book|^consult/i.test(l.trim())) continue;
      const item = clean(stripLeading(l));
      if (item.length > 2) { specialist = item; break; }
    }
  }

  // ── Emergency warnings ────────────────────────────────────────────────────
  const emergencyWarnings: string[] = [];
  const emergKey = Object.keys(secs).find(k => k.includes('EMERGENCY WARNING'));
  if (emergKey) {
    for (const l of lines(secs, emergKey)) {
      if (/seek immediate|call \*\*|helpline|108|112/i.test(l)) continue;
      // Lines: "  ⚠️ Chest pain worsens…"
      const item = clean(l.replace(/^[\s⚠️\u26a0\ufe0f]+/, '').trim());
      if (item) emergencyWarnings.push(item);
    }
  }

  // ── Disclaimer ────────────────────────────────────────────────────────────
  const disclaimer: string[] = [];
  const discKey = Object.keys(secs).find(k => k.includes('DISCLAIMER'));
  if (discKey) {
    for (const l of lines(secs, discKey)) {
      const item = clean(l.replace(/^[\s•\u2022]+/, '').trim());
      if (item.length > 5) disclaimer.push(item);
    }
  }

  const result: DiagnosisData = {
    symptomsAssessed,
    findingsBySymptom,
    condition:      condition || 'Assessment Complete',
    confidence,
    confidenceLabel,
    riskLevel,
    recommendedAction,
    clinicalNote,
    isHighRisk: riskLevel === 'HIGH',
    alternativeConditions,
    recommendedTests,
    medicines,
    selfCare,
    diet,
    specialist,
    emergencyWarnings,
    disclaimer: disclaimer.length ? disclaimer : [
      'This assessment is based only on questionnaire responses.',
      'It is NOT a confirmed medical diagnosis.',
      'Always consult a licensed healthcare professional for diagnosis and treatment.',
    ],
    duration,
    severity,
    temperature,
    keyFindings,
  };

  console.log('PARSED DATA', result);
  return result;
}
