# IP Criteria Schema

适用于：
- 就业培训
- 职业教育
- 转行培训
- 技能课程
- 职业规划 / 咨询内容

生成 `IP_Criteria*.json` 时，至少包含这些键：

```json
{
  "source_summary": {},
  "style_dna": {},
  "hook_patterns": [],
  "structure": {},
  "lexicon": {},
  "worldview": [],
  "audience_model": {},
  "transfer_rules": {},
  "business_fit": {},
  "prompt_pack": {},
  "qa_tests": []
}
```

## 必填说明

### `source_summary`
- `folder`
- `total_files`
- `years`
- `representative_samples`

### `style_dna`
- `one_line_summary`
- `style_tags`
- `philosophy_profile`
- `power_posture`
- `style_radar`
- `contradictions`
- `signature_moves`

其中：

#### `philosophy_profile`
- `reality_model`
- `truth_source`
- `language_mode`
- `ideology`
- `hidden_premises`

写法要求：

- 不要写哲学套话
- 要写成“这个 IP 默认怎么理解世界”
- 要能直接指导生成

#### `power_posture`
- `speaker_role`
- `authority_score_1_to_10`
- `relation_to_audience`
- `trust_source`
- `command_style`

#### `style_radar`
- `authenticity`
- `power`
- `emotion`
- `logic`
- `specificity`
- `action`

每项都用 `1-10` 分，
并补一句解释。

#### `contradictions`
至少 2 条：
- `tension`
- `why_it_works`
- `transfer_warning`

### `hook_patterns`
至少 3 个：
- `name`
- `formula`
- `when_to_use`
- `warning`

### `structure`
- `stage_chain`
- `turning_point`
- `cta_style`

### `lexicon`
- `tone_particles`
- `signature_phrases`
- `sentence_rhythm`
- `emotion_words`

### `worldview`
写底层判断逻辑，不写空词。

建议跟 `style_dna.philosophy_profile` 呼应：

- `philosophy_profile` 负责解释这个 IP 怎么看世界
- `worldview` 负责落到可执行判断句

### `audience_model`
- `surface_audience`
- `decision_maker`
- `core_fears`
- `core_desires`

### `transfer_rules`
- `can_borrow`
- `cannot_borrow`
- `must_rewrite`

### `business_fit`
- `fit_level`
- `best_use_cases`
- `bad_use_cases`
- `adaptation_notes`

### `prompt_pack`
- `system_style`
- `opening_rules`
- `sentence_rules`
- `forbidden_patterns`
- `example_phrases`

说明：

- 这是给生成阶段直接用的压缩包
- 不要把整份分析报告塞进去
- 只保留最能影响成稿的规则

### `qa_tests`
每条写：
- `name`
- `pass_condition`
- `failure_signal`

## 特别提醒

如果当前任务是迁移到“相似业务”，
`business_fit` 不能省。

否则只能算分析报告，
不算生成判据。

如果当前任务要解决“AI 味太重”，
`style_dna` 和 `prompt_pack` 也不能省。
