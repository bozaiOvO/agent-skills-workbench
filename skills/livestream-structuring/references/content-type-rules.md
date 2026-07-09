# Content Type Rules

Classify every useful part of the livestream into exactly one main type:

1. real call-in consultation
2. deep QA in pure-QA livestreams
3. ordinary short QA
4. host-led teaching
5. operations chatter or low-value noise

## Real Call-In Consultation

Only output `Lxx` when the content has all three signals:

1. one-to-one call or interview feeling
   - "喂，能听到吗"
   - "你说"
   - "我先说一下我的情况"
   - a named student, guest, caller, or case person keeps talking about themselves
2. concrete personal background
   - education, major, cohort, age, city
   - current job, internship, offer, salary
   - project, learning history, target direction
   - family, time, money, geography, or other constraints
3. multi-turn personalized diagnosis
   - host asks follow-up questions
   - host gives a judgment about this person's study, work, offer, training, resume, project, salary, interview, or career path

If these three signals are present, the content belongs in one `Lxx`, even if it contains short questions, host teaching, or room-facing explanations.

## Cross-Segment Merge

The same caller must appear once in the main reading area.

Merge segments when:

- previous segment has no clear ending and next segment continues the same issue
- background details match: education, major, cohort, company, city, offer, salary, target direction
- a later title says "续", "承接", or "继续"
- host is still answering the same person's constraint or decision
- a long host explanation is followed by the same caller continuing

Do not split just because files are cut into `segment_01`, `segment_02`, or `segment_03`.

Source segment labels belong in `来源定位` or `分段核对版`, not as main-reading structure.

## Call-In Ending

Do not mark a call-in as ended unless there is a clear ending:

- host says "下一个", "下一位", "先这样", "拜拜"
- caller clearly thanks or says goodbye
- a different caller starts
- topic switches to an unrelated independent question

If unsure, write:

- `未明确结束`
- `延续到下一分段`
- `可能未完整截取`

## Deep QA In Pure-QA Livestreams

Use deep QA when the livestream's main format is a host answering many audience questions, especially for anchors such as 龙哥说IT、code哆哆、杜老师讲IT、十月琪哥/奇哥、津杭、黑马pink and similar career-consulting rooms.

Deep QA is still `Qxx`, not `Lxx`, because there is no sustained one-to-one caller. But it must preserve enough substance for business review and learning:

- the host's conclusion
- why the host thinks so
- examples, analogies, comparisons, and counterexamples
- risk boundaries and exceptions
- what kind of person this answer applies to
- what action the audience should take next
- the answer strategy: how the host frames, persuades, warns, or compares

For a substantial answer, do not output only 2-3 short bullets. A useful deep QA item should usually contain 4-8 answer points or a short "回答展开" section, depending on the raw answer length. Keep meaningful IT/career details such as Java, AI, testing, operations, cloud, cybersecurity, internship, autumn recruitment, training, pay-after-study, salary, project, resume, and interview.

Deep QA is not raw transcript. Remove filler, repeated口癖, pure room operations, and obvious ASR garbage. Keep the reasoning and examples.

Every retained `Qxx` must include `原文优化版（保留表达风格，增强可读性）`. This field should read like a cleaned version of the host's answer: preserve voice, sequence, examples, comparisons, rhetorical questions, and boundaries; remove filler, repeated wording, obvious ASR errors, and unrelated room operations. It is not a raw transcript dump and not a bullet summary.

## Ordinary Short QA

Use `Qxx` only for independent short questions from comments or chat.

Examples:

- "非科班能不能走 Java?"
- "27 届现在学 AI 应用开发来得及吗?"
- "报班多少钱?"
- "大一先学 Python 还是 Java?"

Do not move call-in follow-ups into QA. If the question belongs to a caller's case, keep it inside that `Lxx`.

If an independent audience question receives a long, reusable answer, classify it as deep QA and render it with expanded detail.

## Host-Led Teaching

Use `Txx` when the host is not handling one specific caller and is teaching a topic:

- industry judgment
- learning path
- training risk
- zero-yuan enrollment or pay-after-study warning
- resume, project, interview, salary expectation
- AI, Java, frontend, backend, testing, DevOps, algorithm, AI Infra, large model application development

Keep it concise and structured. Do not turn it into full transcript replay.

## Operations And Noise

Usually exclude:

- "点关注"
- "扣 6"
- "发福袋"
- "进粉丝群"
- "资料怎么领取"
- "连麦加灯牌"
- pure course price, payment, and installment chatter
- greetings, audio checks, room maintenance

Only retain these as a short `Txx` when they reveal a reusable business rule or risk.

## IT Career Vocabulary

Preserve and correct common terms:

- Java, Spring Boot, Spring Cloud, MySQL, Redis, Docker, K8s
- Python, Go, C++, Vue, React, Node.js
- AI Agent, AIGC, AI Infra, machine learning, deep learning, large model application development
- frontend, backend, testing, DevOps, SRE, operations, algorithm
- autumn recruitment, spring recruitment, internship, campus recruitment, social recruitment
- training class, online class, offline class, zero-yuan enrollment, pay-after-study, loan, cost, cycle

Do not invent backgrounds or conclusions. If raw transcript does not mention a field, write `未提及`.
