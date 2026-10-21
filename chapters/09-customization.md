# 第九章 扩展、技能与提示模板 {#ch09}

## 9.1 从最小的定制开始

你可能希望 Pi 每次检查代码都关注错误处理，或者遇到表格任务就按照固定步骤工作。这些需求不一定要修改 Pi 源码。工程提供多种定制机制，选择时先问：我需要补充文字指令，还是新增真正的程序行为？

提示模板保存一段可反复调用的请求。技能保存面向某种任务的指导及配套资料。扩展则执行代码，可以增加工具、命令、事件处理器、模型服务和界面行为。Pi 包负责把这些资源打包分发，主题负责显示颜色。它们能够组合，但每种机制承担的责任不同。

例如“按固定格式介绍项目”可以先写模板；“按照一整套文档整理流程工作，还要参考格式文件”适合技能；“增加一个从内部系统查询工单的操作”需要可执行的扩展或相应 MCP 集成。先使用足够简单的机制，能够减少代码维护，也让使用者更容易理解发生了什么。

还有一类长期项目规则适合放进 AGENTS.md。它是上下文说明，通常跟随目录作用范围加载；模板则需要用户调用，技能完整内容通常按任务需要读取。把这些边界分开后，就不会为了一个固定写作格式而先创建复杂的事件系统。

## 9.2 提示模板把重复输入变成命令

在用户提示目录 ~/.pi/agent/prompts/ 下放一个 explain.md，即可提供 /explain 模板命令。文件可以写成：

~~~markdown
---
description: 介绍项目并列出尚待核实的事实
---
阅读项目说明，介绍用途、目录和启动方式。
补充关注点：$@
~~~

这里的文件名决定命令名，description 用于说明，$@ 会替换成调用时给出的全部参数。于是 /explain 安装方式 会展开成完整请求，再交给智能体。这个替换不是在 shell 中执行命令，也不会因为模板中出现“阅读”两个字就提前读取磁盘。

模板还支持位置参数和默认值，但第一次创建不必同时学习所有语法。先用一个参数跑通“文件被发现—命令出现—文字展开”的关系，再逐步增加变量。修改模板后，在活动会话里运行 /reload。常规 prompts 目录只发现直接子级的 Markdown 文件，嵌套选择需要配置或包清单支持。

需要留意同名命令的优先处理。AgentSession 会先尝试扩展注册的斜杠命令；没有被接管的输入，才继续按普通输入和模板规则处理。因此同样是 /review，可能来自模板，也可能来自可执行扩展。查看来源比只看命令名称更可靠。

## 9.3 技能把流程与材料放在一起

技能的标准形态是一个目录，里面有 SKILL.md，并可附带 scripts、references、assets 等文件。SKILL.md 开头两个 `---` 之间是 YAML 配置区，填写名称、描述等信息，后面才是正文指令。YAML 是常用的文本配置格式。例如：

~~~markdown
---
name: project-guide
description: 为初次阅读代码仓库的人编写项目导读。
---
先读项目说明，再确认入口和包之间的关系。
无法从文件确认的事实要明确说明。
~~~

启动时，Pi 通常把可用技能的名称、描述和路径提供给模型，而不是把所有技能全文都塞进上下文。任务匹配时，模型读取相应 SKILL.md，再按其中指导工作。这种按需加载减少无关文字，但模型可能漏选技能；需要明确使用时，可以输入 /skill:project-guide 并附加任务。

因此，description 要说明“做什么、何时使用”。技能目录里的脚本也不会因为文件存在就自动执行；具体是否读取、运行以及运行结果如何，仍取决于任务和工具动作。技能主要是指导，不是独立权限系统。文档中的 allowed-tools 字段也不能被理解成操作系统访问限制。

常见位置包括 ~/.pi/agent/skills/ 与项目的 .pi/skills/，还支持 ~/.agents/skills/ 及项目 .agents/skills/。项目的后一种目录会从工作目录向祖先发现，在存在仓库根时停止于根。包含 SKILL.md 的目录可递归发现；名称冲突时保留先发现的技能并给出警告。

## 9.4 扩展改变程序行为，也带来运行责任

扩展是加载进 Pi 进程的 TypeScript 或 JavaScript 模块。默认导出的工厂收到 ExtensionAPI，然后注册能力。pi.registerCommand() 增加用户命令，pi.registerTool() 增加模型可调用操作，pi.on() 订阅事件。这些都是实际代码，与模板展开文字的机制不同。

扩展可以在 tool_call 阶段阻止工具，也可在 tool_result 阶段修改结果。它还可以保存自定义会话数据，或者设置状态栏与小组件。写扩展时应按事件契约处理返回值：通知事件不一定采纳返回结果，拦截事件才有阻止等语义。并不是随便返回 false 就能取消所有操作。

常规扩展目录是 ~/.pi/agent/extensions/ 与 .pi/extensions/。目录内的直接源码文件，以及带 index.ts 或 index.js 的子目录入口，都能被发现。本地 TypeScript 扩展通过 jiti 加载，通常不必单独编译。开发时也能用 pi --extension ./hello.ts 指定文件，不必立即把它装成长期资源。

当前命令行程序本身也采用[内置扩展](https://github.com/earendil-works/pi/blob/16f5f0af4d85ca583d045ceb5ed6d646fcaf7761/packages/coding-agent/src/extensions/index.ts)，包含 llama.cpp、MCP、codemode 与工具搜索。MCP 是接入外部工具服务的协议，codemode 则让模型通过代码组合工具。codemode 和 tool_search 默认注册但不激活，可以通过工具配置启用，或者由 MCP 的工具暴露策略启用。这与“Pi 默认加载了什么扩展”和“模型当前能直接调用什么工具”是两个层面。

SDK 会话不会自动注入这些命令行内置扩展，需要宿主明确添加对应工厂，详见 [SDK 文档](https://github.com/earendil-works/pi/blob/16f5f0af4d85ca583d045ceb5ed6d646fcaf7761/packages/coding-agent/docs/sdk.md)。另一方面，仓库提供的 [subagent 示例](https://github.com/earendil-works/pi/blob/16f5f0af4d85ca583d045ceb5ed6d646fcaf7761/packages/coding-agent/examples/extensions/subagent/README.md)与 [plan-mode 示例](https://github.com/earendil-works/pi/blob/16f5f0af4d85ca583d045ceb5ed6d646fcaf7761/packages/coding-agent/examples/extensions/plan-mode/README.md)都位于示例目录。不能因目录存在就宣称用户启动 Pi 后天然拥有子代理或计划模式。阅读示例的安装和运行说明，才知道如何真正启用。

## 9.5 范围、信任与资源包

用户资源默认影响多个项目，项目资源用于当前工程。项目 .pi 配置和受保护资源要在项目信任获准后加载；拒绝信任会跳过它们。AGENTS.md 等上下文文件则按另一套规则发现，不因为拒绝信任就全部消失。sessionDir 还是一个例外：会话选择会在解决信任前读取它。

“信任”在这里是允许资源加载的决定，不是给扩展分配较小权限。扩展与 Pi 进程共享操作系统权限，技能也能指导模型运行脚本。来自陌生仓库的模板虽然只是文字，仍可能影响后续操作。应先查看来源、代码和指导内容，再决定在哪个环境中使用。

Pi 包能把扩展、技能、模板和主题组合成一个目录或 npm 包，通过 pi install 安装。文档语法包括 npm 来源、git 来源和本地路径；例如 pi install npm:@example/pi-tools@1.0.0 是格式示意，这个示例名称不是本书推荐或核实过的实际软件包。

默认安装声明写入用户 settings.json；--local 将声明写入项目 .pi/settings.json。包可以通过 package.json 中的 pi 清单指定资源路径，配置还可以进一步过滤，空数组表示该类资源不加载。pi list 查看包，pi config 管理资源启用状态。安装包与安装 Pi 主程序是两种不同操作。

### 本章小结

模板复用请求，技能复用任务指导和材料，扩展增加可执行行为，包分发多种资源。了解资源位置和加载条件，才能判断一个命令从哪里来、何时生效，以及它是否会运行真正的代码。

### 练习与参考答案

1. 只有一段固定的项目介绍格式，应优先选择什么？

参考答案：提示模板。它能直接把 Markdown 文件变成斜杠命令，没有新增程序行为就不必先编写扩展。

2. 启动时发现技能，是否代表全文已经发送给模型？

参考答案：通常不是。启动阶段主要提供名称、描述和路径，完整指导按需读取，也能用 /skill:name 明确加载。

3. 拒绝项目信任，能否保证项目中的所有文字都不会影响模型？

参考答案：不能。受保护的 .pi 资源会跳过，但上下文文件有独立规则；任务主动读取的文件也可能带入指令。

### 本章源码依据

- [packages/coding-agent/docs/configuration.md](https://github.com/earendil-works/pi/blob/16f5f0af4d85ca583d045ceb5ed6d646fcaf7761/packages/coding-agent/docs/configuration.md)
- [packages/coding-agent/docs/skills.md](https://github.com/earendil-works/pi/blob/16f5f0af4d85ca583d045ceb5ed6d646fcaf7761/packages/coding-agent/docs/skills.md)
- [packages/coding-agent/docs/prompt-templates.md](https://github.com/earendil-works/pi/blob/16f5f0af4d85ca583d045ceb5ed6d646fcaf7761/packages/coding-agent/docs/prompt-templates.md)
- [packages/coding-agent/docs/extensions.md](https://github.com/earendil-works/pi/blob/16f5f0af4d85ca583d045ceb5ed6d646fcaf7761/packages/coding-agent/docs/extensions.md)
- [packages/coding-agent/docs/packages.md](https://github.com/earendil-works/pi/blob/16f5f0af4d85ca583d045ceb5ed6d646fcaf7761/packages/coding-agent/docs/packages.md)
