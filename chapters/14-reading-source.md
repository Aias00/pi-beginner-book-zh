# 第十四章 如何沿着入口阅读源码 {#ch14}

## 14.1 阅读的目标是一条解释得通的路径

第一次打开大型仓库，很容易把“理解工程”误认为“从第一行顺序读完所有文件”。这样既慢，也难以知道哪些细节重要。更实用的目标是先解释一条具体行为：终端收到什么输入，哪个函数选择环境，谁调用模型，工具结果在哪里保存，界面又怎样得到通知。

本章建议继续使用“读取 README.md 并介绍项目”这个例子。它足够小，能跨过主要层次，又不会立即涉及图片、复杂扩展和会话分叉。阅读时拿一张纸，记下函数、输入、输出和下一步。遇到一个尚未理解的辅助函数，可以先标记其作用，等它影响主线时再深入。

先读根 README、包的 README 和 package.json。package.json 描述包名、依赖、导出和命令入口；它能够解释为什么仓库目录名、npm 包名和终端命令不完全相同。coding-agent 发布包的 bin 指向编译后的命令文件；研究当前源码时，再从 packages/coding-agent/src/cli.ts 进入，不要把生成产物当成唯一实现。

本书链接固定到提交 16f5f0af4d85ca583d045ceb5ed6d646fcaf7761。固定提交的意义，是让你打开的文件与正文讨论一致。以后切换到新版本，应重新确认函数名和控制分支。一个网页上的最新说明与一份旧源码，单独看都可能正确，放在一起却不一定匹配。

## 14.2 从很短的入口走到创建会话

先打开 [packages/coding-agent/src/cli.ts](https://github.com/earendil-works/pi/blob/16f5f0af4d85ca583d045ceb5ed6d646fcaf7761/packages/coding-agent/src/cli.ts)。文件只调用 setupCli() 与 main()。这告诉我们入口主要负责转交，不包含完整智能体逻辑。接着到 main.ts 搜索 main 的定义，先辨认认证、包管理、版本、导出等可以提前退出的分支。

剩下的正常路径可以按“参数、会话、服务、会话对象、模式”阅读。parseArgs() 把文本参数变成结构化选项；createSessionManager() 决定新建、继续、恢复或分叉会话；会话目录确定后，程序创建与目录关联的设置、模型和资源服务，再创建真正执行工作的会话对象。

这里应该问一个具体问题：“旧会话的目录与启动目录不同，会先按哪一个加载项目资源？”当前实现先选择目标会话并确定目录，才构建相应服务。main.ts 附近的注释说明这个顺序是为了避免目录相关资源错配。理解因果关系，比记住一长串局部变量更有用。

再跟到 sdk.ts 的 createAgentSession()。不要只看函数名称就跳过：它恢复历史、确定模型和思考级别、选择默认工具，并创建 Agent 与 AgentSession。阅读构造函数的参数时，可以先给每一项分类：模型访问、消息转换、工具选择、事件扩展、存储管理。先理解类别，再研究每个可选项。

最后回到 main.ts 末尾，看看交互模式、RPC 和打印模式怎样使用同一个运行对象。你会发现“界面很多”不必然意味着“核心执行循环很多”。模式主要提供不同输入输出，模型与会话的基础机制是共享的。这也是 SDK 能嵌入其他程序的原因。

## 14.3 给大文件建立责任边界

AgentSession 是大文件，直接逐行读容易失去方向。第一遍先找 constructor、prompt、_startRun、subscribe、compact 和 navigateTree。constructor 说明它依赖哪些对象，prompt 说明用户输入怎样进入，_startRun 说明怎样调用 Agent，事件处理则连接保存、扩展和后续工作。

接下来顺着 Agent.prompt() 到 runPromptMessages()，再到低层 runAgentLoop()。这里开始关注模型回答与工具调用之间的循环。先找一次请求在哪里发起、工具结果在哪里加入、是否需要下一轮怎样判断，再读取消与并发等细节。底层循环的路径是 [packages/agent/src/agent-loop.ts](https://github.com/earendil-works/pi/blob/16f5f0af4d85ca583d045ceb5ed6d646fcaf7761/packages/agent/src/agent-loop.ts)。

工具层可以选 read 作为第一站。createReadToolDefinition() 同时给出工具名称、参数和执行函数。参数说明是模型与程序之间的约定；execute() 才承担真正的读取工作。这种“定义加实现”的组织方式，也能帮助你认识其他工具，不必逐个从头猜设计。

若关心“保存在哪里”，再跳到 [packages/coding-agent/src/core/session-manager.ts](https://github.com/earendil-works/pi/blob/16f5f0af4d85ca583d045ceb5ed6d646fcaf7761/packages/coding-agent/src/core/session-manager.ts)，看 appendMessage() 与 buildSessionContext()。前者增加消息条目，后者为当前路径重建上下文。把保存和重建放在一起读，可以看见文件中的全部记录为何不等于模型本轮收到的消息。

若关心“为什么技能没加载”，应该转向资源发现和信任决策，而不是先修改 Agent 循环。若关心“为什么字没有显示”，应先看模式层怎样订阅事件。把现象放回负责它的层，能够避免在一个看似重要的大类里反复搜索，却始终碰不到真正条件。

## 14.4 用搜索和小问题验证理解

搜索工具是导航，不是替代理解。rg --files 可以列文件，rg -n 可以查找符号及行号。比如搜索 createAgentSession 能找到定义、调用和测试，再选择一处真实调用向下跟踪。不要仅凭命中片段判断复杂条件：需要返回函数，读完整分支，并查看进入它之前的数据怎样生成。

类型也是阅读线索。函数参数常告诉你它允许哪些状态，返回值说明调用者能够依赖什么。如果外部库接口不确定，检查当前依赖版本及已安装声明，而不是用熟悉的旧 API 补齐想象。示例可以帮助理解用法，但 examples 里的扩展不代表主程序默认已经安装。

第一轮阅读完全可以只读，不安装、不启动模型，也不运行构建。运行验证有自己的价值，但应先知道要验证什么。环境变量可能让某些测试连接真实服务，仓库也规定了检查和测试入口；因此不要为了“看看工程”就运行所有测试，更不要把未运行的示例写成已经成功的实验结果。

下面三个练习用于自查。如果你能指出负责的函数，说明一条小轨迹，并讲出结论的边界，就已经具备继续深入的基础。答案不要求背行号；代码变动后，责任和数据流通常比旧行号更值得保留。

### 练习一：默认工具在哪里决定？

问题：看到 read、bash、edit、write 在界面出现，能否断定它们写死在终端绘制代码里？

参考答案：不能。默认名字来自设置层的 DEFAULT_TOOL_NAMES，会话工厂结合配置、禁用选项和工具选择计算启用集合，AgentSession 再组织实际工具。界面负责显示。继续追踪时应从 sdk.ts 的工具选择逻辑出发，避免先修改渲染组件。

### 练习二：一次 Agent 结束是否等于整个任务完成？

问题：集成程序收到 agent_end 就退出，会漏掉什么？

参考答案：会话层可能还有重试、恢复、压缩后的继续工作或排队输入。AgentSession._startRun() 在底层调用后还检查后续动作，最终发出 agent_settled。需要等待整体空闲时，应理解会话事件并使用 session.waitForIdle()；实际启动运行的 prompt() 与只是排队的调用，返回时机不同，不能只凭一个低层事件推断。

### 练习三：一句话如何证明经过了文件读取？

问题：在哪里分别确认用户请求、工具选择和真实磁盘访问？

参考答案：AgentSession.prompt() 处理用户请求；Agent 及低层循环处理模型返回的工具调用；read.ts 的 execute() 使用文件操作读取内容。真实运行还应检查调用和结果记录。三处连起来，才能区分模型打算做什么、程序允许什么和实际完成什么。

### 本章小结

先沿入口建立调用链，再按问题进入设置、资源、存储、工具和界面。每次阅读都保留一个可验证的小问题，记录输入如何变化、由谁负责下一步，并明确哪些结论来自源码、哪些还需要运行证据。

### 本章源码依据

- [packages/coding-agent/src/main.ts](https://github.com/earendil-works/pi/blob/16f5f0af4d85ca583d045ceb5ed6d646fcaf7761/packages/coding-agent/src/main.ts)
- [packages/coding-agent/src/core/sdk.ts](https://github.com/earendil-works/pi/blob/16f5f0af4d85ca583d045ceb5ed6d646fcaf7761/packages/coding-agent/src/core/sdk.ts)
- [packages/coding-agent/src/core/agent-session.ts](https://github.com/earendil-works/pi/blob/16f5f0af4d85ca583d045ceb5ed6d646fcaf7761/packages/coding-agent/src/core/agent-session.ts)
- [packages/agent/src/agent.ts](https://github.com/earendil-works/pi/blob/16f5f0af4d85ca583d045ceb5ed6d646fcaf7761/packages/agent/src/agent.ts)
- [packages/coding-agent/src/core/tools/read.ts](https://github.com/earendil-works/pi/blob/16f5f0af4d85ca583d045ceb5ed6d646fcaf7761/packages/coding-agent/src/core/tools/read.ts)
