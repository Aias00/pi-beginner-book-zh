# 第五章 从一句话到一次工具调用 {#ch05}

## 5.1 选一个能够跟踪的小任务

“智能体”听起来像一个独立工作的角色，在工程中却可以拆成一组普通程序步骤：接受输入，向模型请求回答，执行回答中要求的工具，再把结果交回模型。本章用“请读取 README.md，用三句话介绍项目”作为例子。我们假设文件存在、模型已经配置、项目没有额外拦截行为，以便先看清正常路径。

这是一条说明性的执行轨迹，并不是本书实际发送过的模型请求。模型也可能采用不同工具顺序，甚至根据已有上下文直接回答。阅读源码时，必须区分“程序允许发生什么”和“某次模型一定会做什么”。前者可以从函数和类型确认，后者需要真实运行记录。

先定义两个后面会反复出现的词。消息是交谈中的内容记录，例如用户的请求、助手的回答、工具返回的文件文字。事件是程序通知其他部分“发生了什么”的信号，例如回答开始、文字更新、工具执行结束。消息回答“内容是什么”，事件回答“进展到哪里”。同一条回答在生成中可以对应很多更新事件。

## 5.2 启动时先把工作环境装配好

启动命令的源码入口很短，位于 [packages/coding-agent/src/cli.ts](https://github.com/earendil-works/pi/blob/16f5f0af4d85ca583d045ceb5ed6d646fcaf7761/packages/coding-agent/src/cli.ts)。它先调用 setupCli() 做命令行环境准备，再把命令行参数交给 main()。真正组织启动工作的函数在 [packages/coding-agent/src/main.ts](https://github.com/earendil-works/pi/blob/16f5f0af4d85ca583d045ceb5ed6d646fcaf7761/packages/coding-agent/src/main.ts)。它既处理模型和工具参数，也处理会话、资源、运行模式等选择。

有些命令根本不进入对话。例如版本查询、认证相关命令、软件包管理各有处理分支。正常对话则需要先确定会话的工作目录，因为继续旧会话可能关联另一个目录。假如先按目录甲加载了扩展，却打开目录乙的会话，就可能让配置和工具环境错配，因此当前实现把最终目录的确定放在服务创建之前。

接下来建立三类服务。SettingsManager 负责读取设置；ModelRuntime 负责模型目录、认证和模型访问；ResourceLoader 负责扩展、技能、提示模板、主题及上下文等资源。它们不是三个会聊天的人，而是职责不同的对象。项目信任也在这一阶段影响哪些项目资源能够进入运行环境。

main() 根据解析后的选项调用会话创建流程，最终进入 sdk.ts 中的 createAgentSession()。SDK 的意思是供其他程序使用的开发接口，因此一个 TypeScript 应用也能调用这个工厂，而不必先模拟终端按键。这个工厂会选择或恢复模型与思考级别，重建已有消息，计算默认工具集合，再创建底层 Agent 和外层 AgentSession。

Agent 管理模型循环、消息状态、工具与排队输入。AgentSession 在其外面补上文件会话、扩展生命周期、压缩、重试和运行管理。二者解决的问题不同，所以不能只看名字就把它们当成重复实现。交互界面、打印模式和 RPC 都依赖这套会话机制，再各自处理输入输出。

## 5.3 输入怎样到达真正读取文件的代码

现在用户提交“请读取 README.md，用三句话介绍项目”。交互层把文本交给 AgentSession.prompt()。它先检查是否是扩展注册的斜杠命令；如果是，命令可以直接处理输入。如果没有命令接管，再触发输入处理器，并按配置展开技能命令或提示模板。我们的普通句子经过这些步骤后仍是用户请求。

如果当前会话正在工作，程序不能无条件同时启动第二轮。调用者需要说明新输入用于调整当前工作，还是排到当前工作之后。正常空闲状态下，prompt() 检查模型和认证，再通过 _startRun() 准备消息、处理必要的压缩和启动钩子，最后调用 this.agent.prompt(messages)。

Agent.prompt() 把消息交给底层 runAgentLoop()。可以把循环先读成一句话：“请求模型，处理回答中的工具，必要时再请求模型。”第一轮请求包含当前分支历史、有效系统指令、工具定义及模型设置。工具定义告诉模型有哪些操作、每种操作接受什么参数，它本身还没有读取任何文件。

假设模型返回一个 read 调用，参数可以示意为：

~~~json
{"path":"README.md"}
~~~

这是 read 的参数示例，不是某个服务商完整的网络报文。程序需要根据工具名找到实际实现，校验参数并经过工具钩子，然后调用工具。真正的文件读取在 [packages/coding-agent/src/core/tools/read.ts](https://github.com/earendil-works/pi/blob/16f5f0af4d85ca583d045ceb5ed6d646fcaf7761/packages/coding-agent/src/core/tools/read.ts) 中；createReadToolDefinition() 创建定义，execute() 解析路径、检查可读性、读取内容，并按文字或图片分别处理。

普通文本会变成工具结果中的文字块。大文件受到行数和字节数限制，结果可能提示从下一段继续读取。这个限制意味着“调用过 read”不必然等于“已经读完全文”。本例的 README 若很短，一次调用即可返回全部内容；若很长，模型需要根据结果继续读取或缩小问题。

工具结果被加入消息历史，模型才有了新获得的文件内容。下一轮请求包含这个结果，模型据此生成三句话。因而读取动作和最终介绍之间通常存在两次模型请求：先决定读什么，再根据读取结果作答。这也解释了为什么一句自然语言任务可能产生多轮用量。

![读取任务中的两轮模型请求：先提出读取操作，再根据工具结果回答。](assets/tool-loop.png)

## 5.4 同一段工作怎样显示、保存和结束

工具运行和回答生成期间，Agent 发出事件。message_start 表示一条消息开始，message_update 携带生成进展，message_end 对应完成后的消息。工具还有 tool_execution_start、tool_execution_update 和 tool_execution_end 等事件。界面利用这些信号显示读取路径、进度、正文或错误。

AgentSession 订阅底层事件，执行内部处理，并把完成的消息写入 SessionManager。界面不是会话保存的唯一触发者：换成没有终端界面的打印模式，核心机制仍然存在。打印模式输出最后回答；JSON 模式逐行输出事件，便于另一段程序消费；RPC 则接受外部程序发送的控制命令。

不要把每一个事件都当成一条永久消息，也不要把一个 turn 当成整次任务。turn 是一次模型回答以及该回答要求的工具调用；run 是围绕一个输入持续推进的工作，可能包含多个 turn。中途重试、恢复或排队输入还可能让会话在一次底层结束事件之后继续工作。

因此，集成程序只看到 agent_end 时，不宜立即认定整个会话已经没有后续动作。会话层提供 agent_settled，表示自动处理已告一段落；使用 SDK 时，空闲状态下实际启动一次运行的 prompt() 会等待运行及其后续处理；排队或扩展接管的调用可能提前返回，排队成功不表示任务已完成。需要等待会话空闲时，使用 session.waitForIdle()，并留意后续是否又安排了新工作。理解这些边界，能够避免过早打印“完成”或关闭仍被使用的资源。

### 本章小结

一次读取任务沿着 main、SDK 工厂、AgentSession、Agent 和具体工具实现逐层展开。模型提出结构化操作，Pi 执行文件访问；消息保存内容，事件传递进展。把这几种职责分开，后面的源码就会从大文件变成一条能够跟踪的调用链。

### 练习与参考答案

1. 模型返回“我要读取 README”这句话，是否已经证明文件被读取？

参考答案：没有。只有实际产生工具调用并由工具执行返回结果，才能证明这条程序路径访问过文件；普通文字只是回答内容。

2. 为什么最终回答通常要等到 read 之后再发起一次模型请求？

参考答案：首次请求可能只有任务和历史，文件内容是工具执行后才获得的。下一次请求把工具结果带给模型，才能据此组织答案。

3. message_update 与 message_end 分别适合做什么？

参考答案：前者适合逐步刷新界面，后者提供完成后的消息。把所有更新片段都当成独立最终回答会造成重复。

### 本章源码依据

- [packages/coding-agent/src/main.ts](https://github.com/earendil-works/pi/blob/16f5f0af4d85ca583d045ceb5ed6d646fcaf7761/packages/coding-agent/src/main.ts)
- [packages/coding-agent/src/core/sdk.ts](https://github.com/earendil-works/pi/blob/16f5f0af4d85ca583d045ceb5ed6d646fcaf7761/packages/coding-agent/src/core/sdk.ts)
- [packages/coding-agent/src/core/agent-session.ts](https://github.com/earendil-works/pi/blob/16f5f0af4d85ca583d045ceb5ed6d646fcaf7761/packages/coding-agent/src/core/agent-session.ts)
- [packages/agent/src/agent.ts](https://github.com/earendil-works/pi/blob/16f5f0af4d85ca583d045ceb5ed6d646fcaf7761/packages/agent/src/agent.ts)
- [packages/coding-agent/src/core/tools/read.ts](https://github.com/earendil-works/pi/blob/16f5f0af4d85ca583d045ceb5ed6d646fcaf7761/packages/coding-agent/src/core/tools/read.ts)
