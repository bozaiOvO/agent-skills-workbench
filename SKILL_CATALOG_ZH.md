# 我的 Skill 清单

> 更新时间：2026-07-16。真源：`skills/`。

- 正式 Skill：`110` 个
- 顶层 Skill：`95` 个
- Cheat 子 Skill：`15` 个
- 按功能：不知道名称时，从任务出发查找
- 按系列：知道体系时，从 DBS、宝玉、Cheat 等家族进入

## 一、按功能查找

### Agent、Skill 工程与执行底座（12）

| Skill | 作用 |
| --- | --- |
| [`agent-browser`](skills/agent-browser/SKILL.md) | 浏览器与桌面应用自动化。用于打开网页、点击填表、截图、抓取数据、登录和网页测试。 |
| [`cangjie-skill`](skills/cangjie-skill/SKILL.md) | 把书籍、长视频、播客或课程蒸馏成可执行 Skill。用于提炼方法论，不做普通摘要。 |
| [`caveman`](skills/caveman/SKILL.md) | 超精简回复模式，在保持技术准确的前提下降低输出长度。用户要求少废话、省 token 时使用。 |
| [`clarify`](skills/clarify/SKILL.md) | 通过追问把模糊问题整理成可直接回答的精确问题。用于目标、范围或意图不清时。 |
| [`clarity-first`](skills/clarity-first/SKILL.md) | 执行前检查目标、前提和缺失信息。用于宽泛、含糊或假设较多的任务。 |
| [`darwin-skill`](skills/darwin-skill/SKILL.md) | 自动评测并迭代优化 Skill。用于 Skill 打分、质量检查、自动优化和回归验证。 |
| [`dbs-agent-migration`](skills/dbs-agent-migration/SKILL.md) | 把项目整理成 Claude Code、Codex、Grok 共用的 Agent 工作台。用于真源、规则和 bridge 迁移。 |
| [`dbskill-upgrade`](skills/dbskill-upgrade/SKILL.md) | 安全升级全局 dbskill，自动检测版本、备份并同步。用于更新 Codex 中的 dbskill。 |
| [`find-skills`](skills/find-skills/SKILL.md) | 查找并安装现成 Agent Skill。用于用户询问某种能力是否已有可安装 Skill。 |
| [`huashu-nuwa`](skills/huashu-nuwa/SKILL.md) | 深度调研人物或主题，并生成可运行的人物视角 Skill。用于造 Skill、蒸馏人物思维方式。 |
| [`truth-check`](skills/truth-check/SKILL.md) | 判断类任务的事实校验护栏。用于区分事实、推断与不确定性，并做二次反驳检查。 |
| [`yao-meta-skill`](skills/yao-meta-skill/SKILL.md) | 创建、重构、评测和打包 Agent Skill。用于把工作流、文档或提示词做成可复用 Skill，并运行 `evals/` 质量验证。 |

### 采集、转写与知识沉淀（10）

| Skill | 作用 |
| --- | --- |
| [`baoyu-danger-x-to-markdown`](skills/baoyu-danger-x-to-markdown/SKILL.md) | 经用户同意，将 X/Twitter 帖子或文章转为带数据头的 Markdown。 |
| [`baoyu-electron-extract`](skills/baoyu-electron-extract/SKILL.md) | 提取 Electron 应用的资源和源码。用于解包 ASAR、恢复 sourcemap 和分析桌面应用。 |
| [`baoyu-url-to-markdown`](skills/baoyu-url-to-markdown/SKILL.md) | 抓取网页并转换为 Markdown。用于保存网页、登录后页面和常见平台内容。 |
| [`baoyu-wechat-summary`](skills/baoyu-wechat-summary/SKILL.md) | 提炼微信群聊重点并生成结构化摘要。支持群历史、成员画像和可选毒舌版。 |
| [`baoyu-youtube-transcript`](skills/baoyu-youtube-transcript/SKILL.md) | 下载 YouTube 字幕、逐字稿和封面。支持多语言、翻译、章节与说话人识别。 |
| [`douyin-hot-pipeline`](skills/douyin-hot-pipeline/SKILL.md) | 批量下载抖音博主视频，转写、校正、排序并归档。用于完整抖音内容采集流程。 |
| [`qieman-weekly-links`](skills/qieman-weekly-links/SKILL.md) | 从飞书且曼周刊提取推荐视频和公开链接，生成本地 Markdown 与 JSON 汇总。 |
| [`wechat-daily`](skills/wechat-daily/SKILL.md) | 从微信聊天、朋友圈和收藏夹生成日报与资产沉淀。用于摘要、客户跟进和内容整理。 |
| [`wechat-screen-reader`](skills/wechat-screen-reader/SKILL.md) | 通过屏幕截图和 OCR 安全读取微信聊天，不解密数据库。用于整理文字、图片和附件。 |
| [`weread`](skills/weread/SKILL.md) | 操作微信读书：搜索书籍、管理书架、查看划线笔记、书评和阅读统计。 |

### 内容策略、选题、脚本与增长（27）

| Skill | 作用 |
| --- | --- |
| [`cheat-on-content`](skills/cheat-on-content/SKILL.md) | 内容创作校准系统：完成打分、盲预测、发布复盘和规则进化。首次使用先运行 `/cheat-init`。 |
| [`cheat-init`](skills/cheat-on-content/skills/cheat-init/SKILL.md) | 初始化内容校准系统和项目脚手架。首次使用或缺少 `.cheat-state.json` 时运行。 |
| [`cheat-seed`](skills/cheat-on-content/skills/cheat-seed/SKILL.md) | 通过对话深挖一个选题并产出草稿。用于找角度、练选题或批量生成候选稿。 |
| [`cheat-trends`](skills/cheat-on-content/skills/cheat-trends/SKILL.md) | 抓取热点源并生成去重后的选题候选。用于找热点和更新 `candidates.md`。 |
| [`cheat-learn-from`](skills/cheat-on-content/skills/cheat-learn-from/SKILL.md) | 导入对标账号脚本和数据，提炼内容模式与评分信号。用于学习或拆解对标。 |
| [`cheat-persona`](skills/cheat-on-content/skills/cheat-persona/SKILL.md) | 根据复盘和评论数据生成受众画像。用于回答观众是谁并辅助选题写稿。 |
| [`cheat-score`](skills/cheat-on-content/skills/cheat-score/SKILL.md) | 按当前 rubric 给单篇稿件打分。只输出评分，不写文件也不生成预测。 |
| [`cheat-score-blind`](skills/cheat-on-content/skills/cheat-score-blind/SKILL.md) | 内部盲评分子代理。仅供其他 cheat 技能隔离上下文后调用，不直接面向用户。 |
| [`cheat-predict`](skills/cheat-on-content/skills/cheat-predict/SKILL.md) | 为最终稿建立不可篡改的盲预测记录。用于发布前打分、预测和校准。 |
| [`cheat-shoot`](skills/cheat-on-content/skills/cheat-shoot/SKILL.md) | 登记视频已拍摄并加入待发布队列。用于记录实际拍摄稿和拍摄进度。 |
| [`cheat-publish`](skills/cheat-on-content/skills/cheat-publish/SKILL.md) | 登记内容的发布链接、平台 ID 和时间。只更新元数据，不修改原预测。 |
| [`cheat-retro`](skills/cheat-on-content/skills/cheat-retro/SKILL.md) | 回收发布后的表现数据并复盘。用于把真实结果沉淀为评分规则改进依据。 |
| [`cheat-recommend`](skills/cheat-on-content/skills/cheat-recommend/SKILL.md) | 按当前评分规则从候选池推荐优先选题。用于决定下一篇或下一条做什么。 |
| [`cheat-bump`](skills/cheat-on-content/skills/cheat-bump/SKILL.md) | 升级内容评分规则或分桶边界。用户要求升级 rubric、调整权重或重新校准时使用。 |
| [`cheat-migrate`](skills/cheat-on-content/skills/cheat-migrate/SKILL.md) | 升级旧版 `.cheat-state.json` 数据结构。用于 schema 迁移和版本不兼容修复。 |
| [`cheat-status`](skills/cheat-on-content/skills/cheat-status/SKILL.md) | 查看内容校准系统的状态、进度和待办。只读查询，任何时候都可运行。 |
| [`dbs-ai-check`](skills/dbs-ai-check/SKILL.md) | 检测文案中的 AI 写作痕迹并输出报告。默认只诊断，不改写。 |
| [`dbs-benchmark`](skills/dbs-benchmark/SKILL.md) | 筛选真正值得模仿的对标对象。用于找账号、案例或商业对标。 |
| [`dbs-content`](skills/dbs-content/SKILL.md) | 诊断一个选题或文案该怎么做得更好。用于选题通过后的内容创作优化。 |
| [`dbs-content-system`](skills/dbs-content-system/SKILL.md) | 把本地文稿和素材搭成可复用的内容资产系统。用于抽取内容单元、主题地图和选题稿。 |
| [`dbs-hook`](skills/dbs-hook/SKILL.md) | 诊断并优化短视频开头。用于 Hook、首句和开场留人设计。 |
| [`dbs-resonate`](skills/dbs-resonate/SKILL.md) | 诊断文稿是否能打中受众并给出修改建议。用于共鸣、流量和完播风险检查。 |
| [`dbs-spread`](skills/dbs-spread/SKILL.md) | 用传播学理论拆解内容为什么能火、打中什么情绪。用于共鸣机制和受众立场分析。 |
| [`dbs-xhs-title`](skills/dbs-xhs-title/SKILL.md) | 从验证过的公式中生成和筛选小红书标题。用于起标题并解释选择理由。 |
| [`influence-coordinate`](skills/influence-coordinate/SKILL.md) | 从作用对象、机制和强度分析内容影响力。用于判断内容会怎样影响受众。 |
| [`learning-lobster`](skills/learning-lobster/SKILL.md) | 训练短视频选题、标题、开头和选题树。用于内容陪练，而非只交付成品。 |
| [`topic-audience-insight`](skills/topic-audience-insight/SKILL.md) | 从选题反推目标受众、真实问题和底层需求。用于判断内容在对谁说话。 |

### 写作、翻译、排版与发布（12）

| Skill | 作用 |
| --- | --- |
| [`baoyu-format-markdown`](skills/baoyu-format-markdown/SKILL.md) | 整理并美化 Markdown。用于补数据头、标题、摘要、层级、列表和代码块。 |
| [`baoyu-markdown-to-html`](skills/baoyu-markdown-to-html/SKILL.md) | 将 Markdown 转成带样式的 HTML。用于公众号兼容排版、代码、公式和图表渲染。 |
| [`baoyu-post-to-wechat`](skills/baoyu-post-to-wechat/SKILL.md) | 发布文章或图文到微信公众号。支持 Markdown、HTML、纯文本和多图内容。 |
| [`baoyu-post-to-weibo`](skills/baoyu-post-to-weibo/SKILL.md) | 发布文字、图片、视频或头条文章到微博。用于微博内容发布。 |
| [`baoyu-post-to-x`](skills/baoyu-post-to-x/SKILL.md) | 发布普通帖子或长文到 X/Twitter。支持图片、视频和 Markdown 长文。 |
| [`baoyu-translate`](skills/baoyu-translate/SKILL.md) | 翻译并润色文本、文件或网页。支持快翻、标准翻译、精翻和术语表。 |
| [`gzh-design`](skills/gzh-design/SKILL.md) | 将 Markdown、Word、PDF 或纯文本排成公众号 HTML。支持选主题和生成自定义组件库。 |
| [`humanizer`](skills/humanizer/SKILL.md) | 双重复审并去除文案 AI 味，同时贴近用户原有文风。用于人工化改写和润色。 |
| [`silent-middleaged`](skills/silent-middleaged/SKILL.md) | 模仿“不想说话的中年人”冷静克制、细节密集的第一人称文风写故事。 |
| [`style-dna-analysis`](skills/style-dna-analysis/SKILL.md) | 解析高一致性文本的文风 DNA，并产出可复用写作规则、Prompt 或模仿 Skill。 |
| [`style-sample-filter`](skills/style-sample-filter/SKILL.md) | 清洗、去重、聚类大量文本，筛选最适合反推文风 Prompt 或 Skill 的样本。 |
| [`语言劫持`](skills/语言劫持/SKILL.md) | 用孙宇晨体或咪蒙体强化文案的认知与情绪传播力，也可反向诊断所用写法。 |

### 视觉、图片、演示与 PDF（14）

| Skill | 作用 |
| --- | --- |
| [`baoyu-article-illustrator`](skills/baoyu-article-illustrator/SKILL.md) | 分析文章并生成合适的正文配图。用于文章配图、插图规划和批量生图。 |
| [`baoyu-comic`](skills/baoyu-comic/SKILL.md) | 把知识内容制作成分镜漫画。用于知识漫画、教程漫画和人物传记漫画。 |
| [`baoyu-compress-image`](skills/baoyu-compress-image/SKILL.md) | 压缩并转换图片格式。用于减小体积、转 WebP/PNG 和图片优化。 |
| [`baoyu-cover-image`](skills/baoyu-cover-image/SKILL.md) | 生成文章或内容封面图。用于制作横版、方形等多比例封面。 |
| [`baoyu-danger-gemini-web`](skills/baoyu-danger-gemini-web/SKILL.md) | 通过非官方 Gemini Web 接口生成文字和图片。用于 Gemini 生图、视觉理解和多轮生成。 |
| [`baoyu-diagram`](skills/baoyu-diagram/SKILL.md) | 生成专业 SVG 图表。用于架构图、流程图、时序图、思维导图和关系可视化。 |
| [`baoyu-image-gen`](skills/baoyu-image-gen/SKILL.md) | 调用多种 AI 平台生成或编辑图片。支持参考图、比例和批量生图。 |
| [`baoyu-infographic`](skills/baoyu-infographic/SKILL.md) | 把内容制作成专业信息图。用于高密度摘要、知识可视化和发布级长图。 |
| [`baoyu-slide-deck`](skills/baoyu-slide-deck/SKILL.md) | 将内容制作成专业幻灯片图片。用于生成 PPT 大纲、视觉风格和逐页成图。 |
| [`baoyu-xhs-images`](skills/baoyu-xhs-images/SKILL.md) | 把内容拆成小红书式图文卡片。用于小红书、微信图文和社交媒体轮播图。 |
| [`guizang-social-card-skill`](skills/guizang-social-card-skill/SKILL.md) | 生成归藏风格的社交媒体封面和图文卡片。用于小红书、公众号和轮播图。 |
| [`huashu-design`](skills/huashu-design/SKILL.md) | 用 HTML 制作高保真原型、交互演示、幻灯片和动画。也可做设计探索与专业评审。 |
| [`ian-xiaohei-illustrations`](skills/ian-xiaohei-illustrations/SKILL.md) | 生成 Ian 小黑风格的中文正文配图。用于文章插图、流程、观点和隐喻可视化。 |
| [`minimax-pdf`](skills/minimax-pdf/SKILL.md) | 创建、填写或重排高视觉质量 PDF。用于报告、提案、简历和印刷级文档。 |

### 直播专项（2）

| Skill | 作用 |
| --- | --- |
| [`livestream-optimizer`](skills/livestream-optimizer/SKILL.md) | 基于课程和直播逐字稿诊断定位、节奏、互动与转化，并给出下一场优化方案。 |
| [`livestream-structuring`](skills/livestream-structuring/SKILL.md) | 把直播原始逐字稿合并整理成可读文档。用于区分连麦、问答和主播讲解，不负责下载转写。 |

### 商业诊断、目标、决策与学习（16）

| Skill | 作用 |
| --- | --- |
| [`dbs`](skills/dbs/SKILL.md) | dontbesilent 商业工具箱总入口。根据问题自动路由到合适的诊断 Skill。 |
| [`dbs-action`](skills/dbs-action/SKILL.md) | 诊断“知道该做却做不动”的原因。用于拖延、执行阻力和行动卡点。 |
| [`dbs-chatroom`](skills/dbs-chatroom/SKILL.md) | 根据话题组织多位专家模拟讨论。用于定向聊天室和多角色观点碰撞。 |
| [`dbs-chatroom-austrian`](skills/dbs-chatroom-austrian/SKILL.md) | 模拟哈耶克、米塞斯与 Claude 的奥派经济学对话。用于奥派视角讨论。 |
| [`dbs-decision`](skills/dbs-decision/SKILL.md) | 把长期决策领域搭成本地知识工程。用于持续记录业务、职业、健康、投资等决策。 |
| [`dbs-deconstruct`](skills/dbs-deconstruct/SKILL.md) | 把模糊商业概念拆到可验证的具体含义。用于概念辨析和澄清术语。 |
| [`dbs-diagnosis`](skills/dbs-diagnosis/SKILL.md) | 诊断商业问题或完整商业模式。用于业务问诊、模式体检和机制拆解。 |
| [`dbs-goal`](skills/dbs-goal/SKILL.md) | 把模糊愿望审计成可检查的目标和交付物。用于个人 IP、成长或业务目标澄清。 |
| [`dbs-good-question`](skills/dbs-good-question/SKILL.md) | 把模糊问题改写成 Agent 可推理、可验证的问题说明书，并判断自动化程度。 |
| [`dbs-learning`](skills/dbs-learning/SKILL.md) | 把一个课题拆成连续学习内容，并根据反馈调整下一篇。用于交互式学习。 |
| [`dbs-report`](skills/dbs-report/SKILL.md) | 合并多次诊断存档，生成可交付的 Markdown 报告。用于汇报、打包和分享。 |
| [`dbs-restore`](skills/dbs-restore/SKILL.md) | 读取最近一次诊断存档并继续工作。配合 `dbs-save` 跨会话恢复上下文。 |
| [`dbs-save`](skills/dbs-save/SKILL.md) | 把当前诊断的关键状态保存到本地。用于跨会话续接和保留结论。 |
| [`dbs-slowisfast`](skills/dbs-slowisfast/SKILL.md) | 帮助创业者寻找短期更慢、长期更快的资产化路径。用于节奏和执行策略诊断。 |
| [`don-ge-skill`](skills/don-ge-skill/SKILL.md) | 以 Don 哥/dontbesilent 的直接风格分析赚钱、商业模式、定价、内容变现和 AI 工作流。 |
| [`targeted-chatroom`](skills/targeted-chatroom/SKILL.md) | 按话题组织指定专家进行多角色对话，并给出裁判式总结。 |

### 人物视角与思想框架（17）

| Skill | 作用 |
| --- | --- |
| [`buffett-perspective`](skills/buffett-perspective/SKILL.md) | 用巴菲特的思维框架分析投资、经营和长期决策。用户点名巴菲特视角时使用。 |
| [`diamond-sutra`](skills/diamond-sutra/SKILL.md) | 用《金刚经》和般若思想解释问题。用于经典解读、焦虑、执着和人生困境开解。 |
| [`elon-musk-perspective`](skills/elon-musk-perspective/SKILL.md) | 用马斯克的第一性原理分析成本、流程、产品和激进创新。用户点名马斯克视角时使用。 |
| [`fengge-perspective`](skills/fengge-perspective/SKILL.md) | 以峰哥亡命天涯的直播口吻做判断、吐槽和社会观察。用户点名峰哥视角时使用。 |
| [`feynman-perspective`](skills/feynman-perspective/SKILL.md) | 用费曼框架检验是否真正理解，并拆穿命名、类比和自欺。用户点名费曼视角时使用。 |
| [`jingying-weilai-framework`](skills/jingying-weilai-framework/SKILL.md) | 把《经营未来》作为经营、执行和治理的分析框架。用于拆书、陪读和实际问题分析。 |
| [`kge-perspective`](skills/kge-perspective/SKILL.md) | 用程序员 K 哥视角分析求职、学习、跳槽、考研、AI 转型和培训选择。 |
| [`mao-zedong-perspective`](skills/mao-zedong-perspective/SKILL.md) | 用《毛泽东选集》的方法分析矛盾、战略、组织和行动。用户点名毛泽东或毛选视角时使用。 |
| [`munger-philosophy`](skills/munger-philosophy/SKILL.md) | 用芒格多元思维模型和哲学框架诊断认知与决策。用户点名芒格视角时使用。 |
| [`naval-perspective`](skills/naval-perspective/SKILL.md) | 用 Naval 的杠杆、特定知识和财富框架分析人生与事业选择。用户点名 Naval 视角时使用。 |
| [`saul-goodman-perspective`](skills/saul-goodman-perspective/SKILL.md) | 用 Saul Goodman/Jimmy McGill 的思维和话术复盘谈判、说服与剧情写作，非法律建议。 |
| [`shuiqiupao-perspective`](skills/shuiqiupao-perspective/SKILL.md) | 用水球泡式直白视角分析职场、创业、人性、规则和 AI 机会。用户点名水球泡时使用。 |
| [`sunge`](skills/sunge/SKILL.md) | 用孙宇晨视角分析加密行业、流量叙事、注意力资产和高风险商业决策。 |
| [`tianya-perspective`](skills/tianya-perspective/SKILL.md) | 用天涯社区的集体认知分析社会、历史、人性和现实问题。用户点名天涯视角时使用。 |
| [`tractatus-framework`](skills/tractatus-framework/SKILL.md) | 把《逻辑哲学论》作为解释和分析框架。用于原文解读、陪读和现实问题分析。 |
| [`zhangxuefeng-perspective`](skills/zhangxuefeng-perspective/SKILL.md) | 用张雪峰视角分析教育选择、职业规划和阶层流动。用户点名张雪峰或雪峰视角时使用。 |
| [`程序员luck视角`](skills/程序员luck视角/SKILL.md) | 用程序员 luck 视角分析计算机专业就业、实习、校招、学历回报和 AI 转型。 |

## 二、按系列分组

| 系列 | 核心用途 | 成员 |
| --- | --- | --- |
| **DBS / dontbesilent 系列（25）** | 商业诊断、目标决策、内容诊断、传播分析和 Agent 工作台工具箱。 | [`dbs`](skills/dbs/SKILL.md)<br>[`dbs-action`](skills/dbs-action/SKILL.md)<br>[`dbs-agent-migration`](skills/dbs-agent-migration/SKILL.md)<br>[`dbs-ai-check`](skills/dbs-ai-check/SKILL.md)<br>[`dbs-benchmark`](skills/dbs-benchmark/SKILL.md)<br>[`dbs-chatroom`](skills/dbs-chatroom/SKILL.md)<br>[`dbs-chatroom-austrian`](skills/dbs-chatroom-austrian/SKILL.md)<br>[`dbs-content`](skills/dbs-content/SKILL.md)<br>[`dbs-content-system`](skills/dbs-content-system/SKILL.md)<br>[`dbs-decision`](skills/dbs-decision/SKILL.md)<br>[`dbs-deconstruct`](skills/dbs-deconstruct/SKILL.md)<br>[`dbs-diagnosis`](skills/dbs-diagnosis/SKILL.md)<br>[`dbs-goal`](skills/dbs-goal/SKILL.md)<br>[`dbs-good-question`](skills/dbs-good-question/SKILL.md)<br>[`dbs-hook`](skills/dbs-hook/SKILL.md)<br>[`dbs-learning`](skills/dbs-learning/SKILL.md)<br>[`dbs-report`](skills/dbs-report/SKILL.md)<br>[`dbs-resonate`](skills/dbs-resonate/SKILL.md)<br>[`dbs-restore`](skills/dbs-restore/SKILL.md)<br>[`dbs-save`](skills/dbs-save/SKILL.md)<br>[`dbs-slowisfast`](skills/dbs-slowisfast/SKILL.md)<br>[`dbs-spread`](skills/dbs-spread/SKILL.md)<br>[`dbs-xhs-title`](skills/dbs-xhs-title/SKILL.md)<br>[`dbskill-upgrade`](skills/dbskill-upgrade/SKILL.md)<br>[`don-ge-skill`](skills/don-ge-skill/SKILL.md) |
| **宝玉内容工具系列（21）** | 网页与平台内容获取、写作加工、图片生成、排版和多平台发布。 | [`baoyu-article-illustrator`](skills/baoyu-article-illustrator/SKILL.md)<br>[`baoyu-comic`](skills/baoyu-comic/SKILL.md)<br>[`baoyu-compress-image`](skills/baoyu-compress-image/SKILL.md)<br>[`baoyu-cover-image`](skills/baoyu-cover-image/SKILL.md)<br>[`baoyu-danger-gemini-web`](skills/baoyu-danger-gemini-web/SKILL.md)<br>[`baoyu-danger-x-to-markdown`](skills/baoyu-danger-x-to-markdown/SKILL.md)<br>[`baoyu-diagram`](skills/baoyu-diagram/SKILL.md)<br>[`baoyu-electron-extract`](skills/baoyu-electron-extract/SKILL.md)<br>[`baoyu-format-markdown`](skills/baoyu-format-markdown/SKILL.md)<br>[`baoyu-image-gen`](skills/baoyu-image-gen/SKILL.md)<br>[`baoyu-infographic`](skills/baoyu-infographic/SKILL.md)<br>[`baoyu-markdown-to-html`](skills/baoyu-markdown-to-html/SKILL.md)<br>[`baoyu-post-to-wechat`](skills/baoyu-post-to-wechat/SKILL.md)<br>[`baoyu-post-to-weibo`](skills/baoyu-post-to-weibo/SKILL.md)<br>[`baoyu-post-to-x`](skills/baoyu-post-to-x/SKILL.md)<br>[`baoyu-slide-deck`](skills/baoyu-slide-deck/SKILL.md)<br>[`baoyu-translate`](skills/baoyu-translate/SKILL.md)<br>[`baoyu-url-to-markdown`](skills/baoyu-url-to-markdown/SKILL.md)<br>[`baoyu-wechat-summary`](skills/baoyu-wechat-summary/SKILL.md)<br>[`baoyu-xhs-images`](skills/baoyu-xhs-images/SKILL.md)<br>[`baoyu-youtube-transcript`](skills/baoyu-youtube-transcript/SKILL.md) |
| **Cheat 内容校准系列（16）** | 从初始化、选题和盲预测，到发布、复盘和评分规则进化的完整闭环。 | [`cheat-on-content`](skills/cheat-on-content/SKILL.md)<br>[`cheat-init`](skills/cheat-on-content/skills/cheat-init/SKILL.md)<br>[`cheat-seed`](skills/cheat-on-content/skills/cheat-seed/SKILL.md)<br>[`cheat-trends`](skills/cheat-on-content/skills/cheat-trends/SKILL.md)<br>[`cheat-learn-from`](skills/cheat-on-content/skills/cheat-learn-from/SKILL.md)<br>[`cheat-persona`](skills/cheat-on-content/skills/cheat-persona/SKILL.md)<br>[`cheat-score`](skills/cheat-on-content/skills/cheat-score/SKILL.md)<br>[`cheat-score-blind`](skills/cheat-on-content/skills/cheat-score-blind/SKILL.md)<br>[`cheat-predict`](skills/cheat-on-content/skills/cheat-predict/SKILL.md)<br>[`cheat-shoot`](skills/cheat-on-content/skills/cheat-shoot/SKILL.md)<br>[`cheat-publish`](skills/cheat-on-content/skills/cheat-publish/SKILL.md)<br>[`cheat-retro`](skills/cheat-on-content/skills/cheat-retro/SKILL.md)<br>[`cheat-recommend`](skills/cheat-on-content/skills/cheat-recommend/SKILL.md)<br>[`cheat-bump`](skills/cheat-on-content/skills/cheat-bump/SKILL.md)<br>[`cheat-migrate`](skills/cheat-on-content/skills/cheat-migrate/SKILL.md)<br>[`cheat-status`](skills/cheat-on-content/skills/cheat-status/SKILL.md) |
| **人物与 IP 视角系列（14）** | 调用特定人物或社群的判断框架、语言风格和领域经验。 | [`buffett-perspective`](skills/buffett-perspective/SKILL.md)<br>[`elon-musk-perspective`](skills/elon-musk-perspective/SKILL.md)<br>[`fengge-perspective`](skills/fengge-perspective/SKILL.md)<br>[`feynman-perspective`](skills/feynman-perspective/SKILL.md)<br>[`kge-perspective`](skills/kge-perspective/SKILL.md)<br>[`mao-zedong-perspective`](skills/mao-zedong-perspective/SKILL.md)<br>[`munger-philosophy`](skills/munger-philosophy/SKILL.md)<br>[`naval-perspective`](skills/naval-perspective/SKILL.md)<br>[`saul-goodman-perspective`](skills/saul-goodman-perspective/SKILL.md)<br>[`shuiqiupao-perspective`](skills/shuiqiupao-perspective/SKILL.md)<br>[`sunge`](skills/sunge/SKILL.md)<br>[`tianya-perspective`](skills/tianya-perspective/SKILL.md)<br>[`zhangxuefeng-perspective`](skills/zhangxuefeng-perspective/SKILL.md)<br>[`程序员luck视角`](skills/程序员luck视角/SKILL.md) |
| **书籍与思想框架系列（3）** | 围绕特定经典或书籍进行解释、陪读和现实问题分析。 | [`diamond-sutra`](skills/diamond-sutra/SKILL.md)<br>[`jingying-weilai-framework`](skills/jingying-weilai-framework/SKILL.md)<br>[`tractatus-framework`](skills/tractatus-framework/SKILL.md) |
| **直播系列（2）** | 整理直播逐字稿，并复盘定位、节奏、互动和转化。 | [`livestream-structuring`](skills/livestream-structuring/SKILL.md)<br>[`livestream-optimizer`](skills/livestream-optimizer/SKILL.md) |
| **微信、飞书与阅读平台系列（5）** | 处理微信、飞书、公众号和微信读书中的内容与知识资产。 | [`gzh-design`](skills/gzh-design/SKILL.md)<br>[`qieman-weekly-links`](skills/qieman-weekly-links/SKILL.md)<br>[`wechat-daily`](skills/wechat-daily/SKILL.md)<br>[`wechat-screen-reader`](skills/wechat-screen-reader/SKILL.md)<br>[`weread`](skills/weread/SKILL.md) |
| **Skill 工程与基础能力系列（10）** | 创建、发现、优化、蒸馏和运行 Skill，并提供执行前判断护栏。 | [`agent-browser`](skills/agent-browser/SKILL.md)<br>[`cangjie-skill`](skills/cangjie-skill/SKILL.md)<br>[`caveman`](skills/caveman/SKILL.md)<br>[`clarify`](skills/clarify/SKILL.md)<br>[`clarity-first`](skills/clarity-first/SKILL.md)<br>[`darwin-skill`](skills/darwin-skill/SKILL.md)<br>[`find-skills`](skills/find-skills/SKILL.md)<br>[`huashu-nuwa`](skills/huashu-nuwa/SKILL.md)<br>[`truth-check`](skills/truth-check/SKILL.md)<br>[`yao-meta-skill`](skills/yao-meta-skill/SKILL.md) |
| **独立内容创作工具（11）** | 选题洞察、文风、配图和传播效果分析。 | [`guizang-social-card-skill`](skills/guizang-social-card-skill/SKILL.md)<br>[`humanizer`](skills/humanizer/SKILL.md)<br>[`ian-xiaohei-illustrations`](skills/ian-xiaohei-illustrations/SKILL.md)<br>[`influence-coordinate`](skills/influence-coordinate/SKILL.md)<br>[`learning-lobster`](skills/learning-lobster/SKILL.md)<br>[`silent-middleaged`](skills/silent-middleaged/SKILL.md)<br>[`style-dna-analysis`](skills/style-dna-analysis/SKILL.md)<br>[`style-sample-filter`](skills/style-sample-filter/SKILL.md)<br>[`targeted-chatroom`](skills/targeted-chatroom/SKILL.md)<br>[`topic-audience-insight`](skills/topic-audience-insight/SKILL.md)<br>[`语言劫持`](skills/语言劫持/SKILL.md) |
| **独立视觉与文档工具（2）** | 制作高保真 HTML 设计、交互演示和高质量 PDF。 | [`huashu-design`](skills/huashu-design/SKILL.md)<br>[`minimax-pdf`](skills/minimax-pdf/SKILL.md) |
| **抖音内容流水线（1）** | 下载抖音博主视频，完成转写、校正、排序和归档。 | [`douyin-hot-pipeline`](skills/douyin-hot-pipeline/SKILL.md) |

## 使用建议

- 不知道该用哪个：先看“按功能查找”。
- 已经知道体系：直接看“按系列分组”。
- DBS 是商业与内容诊断工具箱；`dbs` 是总入口。
- Cheat 是内容校准闭环；首次使用从 `cheat-init` 开始。
- 人物视角 Skill 只在明确需要该人物框架或表达方式时调用。
