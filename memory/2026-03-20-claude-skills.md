# AI工具使用技巧 - Claude Code Skill推荐

**来源**：微信文章  
**记录时间**：2026-03-20 13:11  
**主题**：10个值得优先安装的 Claude Code skill

---

## 文章核心观点

Claude Code 不应只被看作"coding assistant"，接上浏览器、搜索、总结等能力后，它可以从"会写代码"进化为真正的 agent，能执行完整的工作流。

---

## 10个推荐 Skill

### 1. agent-browser ⭐（最优先）
**作用**：浏览器自动化（点击、填表、截图、抓取信息）  
**场景**：后台操作、表单填写、Web App测试、自动化流程  
**安装**：`npx skills add vercel-labs/agent-browser@agent-browser -g -y`  
**页面**：https://skills.sh/vercel-labs/agent-browser/agent-browser

---

### 2. find-skills
**作用**：从 Claude Code 生态中搜索现有 skill  
**价值**：避免"重复造轮子"，降低探索成本  
**安装**：`npx skills add vercel-labs/skills@find-skills -g -y`  
**页面**：https://skills.sh/vercel-labs/skills/find-skills

---

### 3. summarize
**作用**：信息压缩（长网页、文档、播客、会议纪要）  
**理念**："信息时代最稀缺的，不是内容，是压缩能力"  
**安装**：`npx skills add steipete/clawdis@summarize -g -y`  
**页面**：https://skills.sh/steipete/clawdis/summarize

---

### 4. skill-creator
**作用**：把自己的工作流沉淀成可复用 skill  
**价值**：将"零散经验"变成"可复用流程"  
**安装**：`npx skills add anthropics/skills@skill-creator -g -y`  
**页面**：https://skills.sh/anthropics/skills/skill-creator

---

### 5. tmux
**作用**：接管终端会话（长任务、远程机、交互式 CLI）  
**场景**：命令要跑很久、过程要持续观察、多个任务并行  
**安装**：`npx skills add steipete/clawdis@tmux -g -y`  
**页面**：https://skills.sh/steipete/clawdis/tmux

---

### 6. testing / e2e / playwright
**作用**：写可靠、可维护的测试代码  
**价值**：增加"测试工程经验"，不只是"能写出来"  
**安装**：`npx skills add anthropics/skills@webapp-testing -g -y`  
**页面**：https://skills.sh/anthropics/skills/webapp-testing

---

### 7. docs / readme / api-docs
**作用**：技术文档生成（README、API文档、项目说明）  
**价值**：给文档一套组织框架，让产出更像样  
**安装**：`npx skills add googleworkspace/cli@gws-docs -g -y`  
**页面**：https://skills.sh/googleworkspace/cli/gws-docs

---

### 8. refactor / review / best-practices
**作用**：代码重构、代码审查、最佳实践  
**价值**：从"能用"推向"更专业"，提升可维护性  
**安装**：`npx skills add supercent-io/skills-template@code-refactoring -g -y`  
**页面**：https://skills.sh/supercent-io/skills-template/code-refactoring

---

### 9. git-workflow / changelog / release
**作用**：Git工作流自动化（commit message、changelog、release note）  
**价值**：处理"烦但必须做"的交付环节  
**安装**：`npx skills add supercent-io/skills-template@changelog-maintenance -g -y`  
**页面**：https://skills.sh/supercent-io/skills-template/changelog-maintenance

---

### 10. research / web-search / extract
**作用**：研究助理（查资料、读网页、提取信息、比较方案）  
**推荐**：Tavily research skill  
**安装**：`npx skills add tavily-ai/skills@research -g -y`  
**页面**：https://skills.sh/tavily-ai/skills/research

---

## 核心洞察

**从 coding assistant 到 agent 的转变**：
- 不只是"会写"，还要"会执行"
- 不只是"生成"，还要"压缩"
- 不只是"做一次"，还要"持续控制"
- 不只是"写代码"，还要"交付代码"

**使用建议**：
1. 先装 agent-browser（最基础、最通用）
2. 用 find-skills 探索生态，避免重复造轮子
3. 高频重复的工作流，用 skill-creator 固化
4. 长期维护的代码库，配上 refactor/review skill

---

## 对咱们的启发

咱们现在的 OpenClaw 已经具备类似能力：
- ✅ **browser** → 对应 agent-browser（网页操作）
- ✅ **web_search / kimi_search** → 对应 research（信息搜索）
- ✅ **pdf-parser / feishu_doc** → 对应 summarize（信息处理）
- ✅ **skill-creator** → 已有，用于沉淀工作流

可以考虑增强的方向：
- 测试类 skill（webapp-testing）
- 代码重构类 skill（code-refactoring）
- Git工作流自动化（changelog-maintenance）

