# Retrieval Playbook

## 默认命令

```bash
python3 scripts/search_corpus.py "<用户问题>"
```

常见例子：

```bash
python3 scripts/search_corpus.py "计算机专业还能不能学"
python3 scripts/search_corpus.py "大三该不该实习"
python3 scripts/search_corpus.py "大专要不要专升本"
python3 scripts/search_corpus.py "AI 会不会取代程序员"
python3 scripts/search_corpus.py "古法编程还能持续多久" --year 2026
```

## 什么时候必须检索

- 学历 / 学校层级 / 路线选择
- 实习 / 校招 / 找工作标准
- 考研 / 专升本 / 是否离职
- AI / 岗位 / 编程语言 / 古法编程
- 任何明显依赖 `2026` 最新判断的话题

## 什么时候可以不检索

- 用户问的是很抽象的“他怎么看普通大学生就业”
- 当前话题和刚检索过的内容高度连续

## 检索后怎么裁决

- 默认 `2026 > 2025`
- `2026` 用来回答当前问题
- `2025` 主要补人物底色、泛就业现实主义和早期主张

## 检索关注点

优先找：

- 标题是否直接命中
- 标签是否对应学历 / 实习 / AI / 岗位
- 正文里是否出现“先分层、再给路线、再算账”

## 不要怎么用

- 不要只拿一条爆款就代表整个人物
- 不要把 `2025` 的泛认知内容压过 `2026` 的计算机就业主轴
