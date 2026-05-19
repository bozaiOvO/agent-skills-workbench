# 领域路由

峰哥的话题跨度很大。

如果不先路由，AI 很容易把：

- 地缘话题答成情感鸡汤
- A股答成泛泛投资建议
- 历史答成百科摘要
- 日常困惑答成大国叙事

所以要先分流。

## 路由表

| 路由 | 典型问题 | 先查什么 | 输出重点 |
| --- | --- | --- | --- |
| `geo` | 缅北、东南亚、香港、俄罗斯、留学生、安全 | 合法通路、现实成本、链条闭合、地区差异、谣言断点 | 先破谣，再讲结构 |
| `finance` | A股、理财、牛市、投资、外汇 | 当前事实、年份、市场情绪、宏观叙事、普通人动作 | 先看环境，再谈个股 |
| `history` | 朝代、人物、制度类比、文明比较 | 具体史实、类比目标、用户是求知识还是求判断 | 历史是镜子，不是段子 |
| `life` | 工作、婚恋、社恐、幸福、买房 | 用户是真求建议、求安慰、还是求站队 | 先落现实动作 |
| `creator` | 直播、拍片、B站、主播圈、流量 | 平台机制、节目效果、关系链、内容成本 | 先拆内容机制 |
| `health` | 登山、熬夜、心脏、体能、医生建议 | 医学事实、旅行经验、个人状态、不要越界装专业 | 先承认边界 |

## 每条路由怎么搜

### `geo`

```bash
python3 scripts/search_corpus.py "缅北 诈骗 器官" --route geo
python3 scripts/search_corpus.py "美国 中国 创业土壤 工会" --route geo
python3 scripts/search_corpus.py "香港 特供" --route geo
```

先看：

- 这地方能不能去
- 谁能去
- 成本和收益是谁承担
- 网络流言哪一环最不成立

### `finance`

```bash
python3 scripts/search_corpus.py "A股 牛市 国家意志" --route finance --year 2025
python3 scripts/search_corpus.py "理财 财富 保卫" --route finance --year 2025
```

先看：

- 这是阶段判断还是长期判断
- 他是在讲大盘、情绪、国家叙事，还是讲个股
- 这次回答需不需要先查今天的最新事实

### `history`

```bash
python3 scripts/search_corpus.py "历史 元朝 明朝 清朝" --route history
python3 scripts/search_corpus.py "太阳底下没有新鲜事 人性" --route history
```

先看：

- 用户要的是史实，还是借历史说现实
- 峰哥是否在用历史做类比，而不是做百科讲解

### `life`

```bash
python3 scripts/search_corpus.py "工作 怨天尤人 幸福" --route life
python3 scripts/search_corpus.py "不结婚 苦恼 很现实" --route life
```

先看：

- 这是求安慰还是求裁决
- 先别急着给大道理，先看现实烦恼是什么

### `creator`

```bash
python3 scripts/search_corpus.py "直播 拍视频 流量" --route creator
python3 scripts/search_corpus.py "B站 主播 纪录片" --route creator
```

先看：

- 平台机制
- 节目效果
- 内容成本
- 人物关系是不是戏剧化了

### `health`

```bash
python3 scripts/search_corpus.py "登山 心脏 熬夜" --route health --year 2024
python3 scripts/search_corpus.py "医生 熬夜 咖啡 心脏" --route health
```

先看：

- 哪部分是医学事实
- 哪部分只是个人经验
- 哪部分不能让 skill 越界硬答

## 路由失败时怎么办

如果问题横跨多个路由：

- 先按“事实占比最高”的路由查
- 再用其他路由补充

例子：

- `A股和国家意志`：先 `finance`，再补 `geo`
- `历史如何解释今天的男女问题`：先 `history`，再补 `life`

不要一次把所有路由都开满，那会把答案搅浑。
