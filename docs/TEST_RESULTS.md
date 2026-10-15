# 软件测试记录

## 0.2.0独立Wheel复测

2026-10-15：**WINDOWS_WHEEL_AND_CLI_PASS**。Windows / Python3.13.1，新建隔离venv，非编辑安装；测试与CLI从无关工作目录通过`-I -B`调用已安装包。

- 正式Wheel：`hollow_core_fiber_numerical_study-0.2.0-py3-none-any.whl`。
- Wheel SHA256：`035e2428d25531169680f65b4fd760b869e0353962fa7d9eda935dfed0fbf1a7`。
- **118 passed in 4.64s**；0失败、0跳过。新增测试验证正式分发名、版本、Python约束及旧分发未安装。Wheel内8份Python源码与当前包源码hash一致。
- NumPy2.5.4、Pydantic2.14.1、pytest9.1.1；可选matplotlib3.11.2；setuptools84.0.0、wheel0.48.0。
- M1正常/异常配置，M2人工算术，M3正常/worker失败/验收失败/拒绝覆盖全部实际执行，退出码符合下方历史场景表；新版独立运行记录不沿用旧验收。
- 人工Fourier图实际生成：最大复系数误差`4.4048e-16`，重构误差`1.5701e-15`，文本画布检查通过；图经目视复核调整图例位置。PNG、SVG及解析参考JSON随仓库保留。

**保留的失败：**首次运行`run_a1`为117通过、1失败（8.41秒）。新增元数据测试把语义等价的`<3.14,>=3.13`与`>=3.13,<3.14`作字符串比较，导致误报。改为比较精确约束集合后完整复测；没有放宽Python范围，也没有修改数值算法。失败日志、复测命令、JUnit、依赖快照及Wheel均保存在公开仓库之外。

本次未运行COMSOL，未引入研究数据；没有Linux或其他Python版本验收。Python安装范围不等于所有版本实测通过。

## RC1历史测试摘要（不作为0.2.0验收）

日期：2026-10-15。状态：**RC_WINDOWS_WHEEL_RETEST_PASS**。

本文件是候选复测的软件结果摘要，不包含个人路径、原始日志或物理研究数据。原始命令、stdout/stderr、JUnit、wheel、环境及失败负控制证据独立保存在本候选之外，没有覆盖上游证据。

|项目|实际结果|
|---|---|
|环境|Windows，Python3.13.1；全新venv，system-site-packages关闭|
|直接依赖|NumPy2.5.4、Pydantic2.14.1、pytest9.1.1|
|构建|setuptools84.0.0 / wheel0.48.0；从候选副本构建wheel，非editable安装|
|源码身份|16份源代码/测试/人工配置/pyproject与上游逐字节相同；wheel中8份Python包文件与候选源码hash一致|
|pytest|**117 passed in 6.36s**；0失败、0错误、0跳过|
|独立运行|测试及CLI从无关cwd运行，Python `-I -B`；包位于新venv的site-packages，未引用旧MVP包|
|科研依赖|新环境未安装/发现原研究包、MPh或JPype；没有COMSOL运行或真实数据输入|
|原件保留|准备与结束时核对原MVP源文件及封存产物，未改变|

实际执行14条命令，全部退出码与预期一致：新建环境、安装依赖、构建wheel、安装wheel、记录版本、检查安装路径/科研导入缺席、pytest及以下CLI正反例。

|CLI场景|预期/实际退出码|证据解释|
|---|---:|---|
|M1正常人工配置|0 / 0|SI数值转换、依赖求值通过|
|M1未知符号配置|2 / 2|保存明确失败原因，不能当有效结果|
|M2人工复场演示|0 / 0|解析算术参考、Fourier与拟合检查通过|
|M3正常dummy|0 / 0|worker退出0，算术验收PASS|
|M3故意失败dummy|1 / 1|worker退出7，保留stdout/stderr/状态|
|M3验收故意失败|1 / 1|worker退出0但验收FAIL，未误标成功|
|M3同目录重复输出|2 / 2|拒绝覆盖既有产物|

M3三个已完成场景的文件manifest重新核验通过。超时和atomic replace失败等故障注入由单元测试覆盖。负控制的非零退出是预期行为；本次没有意外失败被隐去。

公开复现方式：使用README安装命令，在新目录执行同一CLI/pytest；应比较数值、状态和验收结论，不要求包含时间戳的整个任务目录逐字节相同。

**适用范围：** Windows此组版本的软件算术与接口验收。Linux、其他Python/依赖版本、大规模性能、对恶意输入的安全性、真实Maxwell场与物理收敛均未认证。人工数据统一标注ALGORITHMIC_FIXTURE_NOT_COMSOL。不存在B/R预测成功结论。
