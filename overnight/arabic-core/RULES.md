# Arabic core: translation rules

You are translating study cards for a Muslim speaker who will use them on camera, in formal Arabic (فصحى معاصرة), to answer critics. Accuracy matters more than elegance: a wrong fact on camera does real damage.

## Input
Each packet in `packets/NN.json` has: `title`, `thesis`, `premises` (each with `tag` P1, P2, … and `∴` for the conclusion), `evidence` (bullets), `ar_quotes` (Arabic texts already in the library, verified), `objections` (q, a), `practice` (q, a), `sum` (one-breath summary), `caution`, `review_note`, `quran_arabic` (verified Uthmani text for Quran references found in the packet), `hadith_arabic` (Arabic text and gradings from the open hadith dataset for hadith references found in the packet).

## Output
Write `out/NN.json` (same number) as UTF-8 JSON, exactly this shape:

```json
{
  "n": 2,
  "id": "<copy from packet>",
  "title": "Arabic title",
  "thesis": "…",
  "premises": [{"tag": "١", "text": "…"}, {"tag": "∴", "text": "…"}],
  "evidence": ["…"],
  "quotes": [{"text": "Arabic text exactly as given", "cite": "سورة … الآية …  or  صحيح البخاري ١١٣"}],
  "objections": [{"q": "…", "a": "…"}],
  "practice": {"q": "…", "a": "…"},
  "sum": "…",
  "omitted": ["English description of anything you left out and why"],
  "check": ["anything a human reviewer should double-check"]
}
```

Use Arabic-Indic digits (١٢٣) in tags, numbers and references in the Arabic text. Keep empty arrays or empty strings when the packet has nothing for a field.

## Hard rules
1. **Translate, do not add.** No new facts, names, dates, numbers, verses, hadith or quotations that are not in the packet. If a sentence is unclear, translate it conservatively and add a note to `check`.
2. **Quran:** whenever the English quotes or paraphrases a verse and its reference is in `quran_arabic`, put the exact Arabic from `quran_arabic` (copy it character for character) in `quotes`, and in the running text refer to it by surah and verse (e.g. «الأحزاب: ٣٥»). Never back-translate a verse from English. Warning: `quran_arabic` was matched automatically and can contain false matches where the English reference is actually a Bible chapter and verse (for example Deuteronomy 18:18, John 1:21, Genesis, Isaiah, Daniel, Acts). Ignore those; Bible references stay as Bible references (سفر التثنية ١٨: ١٨، إنجيل يوحنا ١: ٢١).
3. **Hadith:** keep the reference (صحيح البخاري ١١٣، صحيح مسلم ٣٠٠٤، سنن أبي داود ٣٦٤٦، جامع الترمذي، سنن ابن ماجه، سنن النسائي). If the English quotes the Prophet's ﷺ words and `hadith_arabic` has that hadith, use the Arabic wording of the relevant phrase from `hadith_arabic` verbatim instead of translating the English (the dataset text includes the chain; take only the words of the report). If `hadith_arabic` shows any grader saying Daif, Munkar or Mawdu while others say Sahih or Hasan, add «(مختلف في تصحيحه)» after the reference; if all listed graders say weak, add «(ضعيف)».
4. **Review notes:** if `review_note` or `caution` says a detail is not confirmed, leave that detail out of the Arabic and list what you left out in `omitted`. Examples: the counts "138 hadith" and "ninety-eight", "Issus 622", the description of Tesei's paper, the Mongols reading.
5. **Names:** standard Arabic forms: أبو هريرة، عبد الله بن عمرو، ابن عباس، ابن تيمية، الألباني، البخاري. Western scholars in Arabic script with the Latin name once in brackets the first time: هارالد موتسكي (Harald Motzki). Book titles: translate the meaning in Arabic and keep the original title in Latin letters in brackets.
6. **Tone:** clear, confident, measured. Short sentences that can be said aloud. No insults. Keep honest concessions ("this is debated", "scholars differ") exactly as strong as in the English.
7. **ﷺ** after the Prophet's name, رضي الله عنه/عنها only where natural and not repeated in every line.
8. Do not translate the English `title` literally if it reads badly in Arabic; keep its meaning.

## Glossary
- hadith rejecter / Quranist: منكرو السنة / القرآنيون
- chain of narration: الإسناد · text of a report: المتن · narrator: الراوي
- authentic / sound / weak: صحيح / حسن / ضعيف
- the canonical readings: القراءات · the seven ahruf: الأحرف السبعة
- abrogation: النسخ · the Uthmanic codex: المصحف العثماني · palimpsest: الرَّقّ الممسوح (طِرس)
- radiocarbon dating: التأريخ بالكربون المشع
- burden of proof: عبء الإثبات · circular reasoning: الاستدلال الدائري · fallacy: مغالطة
- secular liberalism: الليبرالية العلمانية · human rights: حقوق الإنسان · apostasy: الردة
- prophecy: نبوءة · inimitability: الإعجاز · the fitrah: الفطرة
- objection: اعتراض · reply: جواب · in one breath: باختصار
