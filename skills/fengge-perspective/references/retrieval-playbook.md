# 检索手册

这个 skill 的默认原则是：**先检索，再代入。**

## 最小读取路径

### 纯框架问题

1. `references/mental-models.md`
2. `references/voice-dna.md`

### 具体主题问题

1. `python3 scripts/search_corpus.py "<query>" --route <route>`
2. `references/domain-router.md`
3. `references/mental-models.md`
4. `references/voice-dna.md`

### 年份敏感 / 观点可能变化

1. `python3 scripts/search_corpus.py "<query>" --route <route> --year <year>`
2. `references/evolution-timeline.md`
3. 再做版本裁决

## 路由选择

| 路由 | 用途 |
| --- | --- |
| `geo` | 地缘、国际地区、东南亚、香港、俄罗斯、签证、安全 |
| `finance` | A股、理财、市场情绪、牛市、投资 |
| `history` | 历史类比、王朝、更大文明叙事 |
| `life` | 工作、婚恋、社恐、买房、普通人困惑 |
| `creator` | 直播、拍片、B站、流量、主播圈 |
| `health` | 登山、心脏、熬夜、睡眠、体能 |

## 查询模板

### 地缘 / 国际地区

```bash
python3 scripts/search_corpus.py "缅北 诈骗 器官" --route geo
python3 scripts/search_corpus.py "香港 特供 蔬菜" --route geo
python3 scripts/search_corpus.py "美国 中国 创业土壤 工会" --route geo
```

### A股 / 理财

```bash
python3 scripts/search_corpus.py "A股 牛市 国家意志" --route finance --year 2025
python3 scripts/search_corpus.py "财富 保卫 理财" --route finance --year 2025
```

### 历史 / 类比

```bash
python3 scripts/search_corpus.py "历史 元朝 明朝 清朝" --route history
python3 scripts/search_corpus.py "太阳底下没有新鲜事 人性" --route history
```

### 日常 / 情感 / 工作

```bash
python3 scripts/search_corpus.py "工作 怨天尤人 幸福" --route life
python3 scripts/search_corpus.py "不结婚 苦恼 很现实" --route life
```

### 主播 / 内容 / 流量

```bash
python3 scripts/search_corpus.py "直播 拍视频 流量" --route creator
python3 scripts/search_corpus.py "B站 主播 纪录片" --route creator
```

### 健康 / 登山

```bash
python3 scripts/search_corpus.py "登山 心脏 熬夜" --route health --year 2024
python3 scripts/search_corpus.py "医生 熬夜 咖啡 心脏" --route health
```

## 数据层使用规则

### `original_text`

默认主检索层。

适合：

- 找原始口气
- 找完整上下文
- 找峰哥如何现场转弯
- 做一手证据

### `sft`

适合：

- 找更干净的问答骨架
- 辅助确认某类问题的稳定回答模板

### `all`

当你既想看原始说法，又想看清洗后的精炼答案时用。

## 过滤规则

默认脚本会排除：

- 文件名里带 `不完整`
- 文件名里带 `弹幕版`

原因：

- 噪声大
- 上下文破碎
- 重复污染更严重

如果用户就是要看原始残片，再加：

```bash
python3 scripts/search_corpus.py "<query>" --include-variants
```

## 搜索后的裁决

检索完不要机械拼接片段，至少做三步：

1. 看最新年份有没有更明确的说法
2. 看不同年份是否冲突
3. 再按“峰哥的判断顺序”重写输出

搜索只是取证，不是复制粘贴。
