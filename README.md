# Optical Simulation Toolkit

**参数契约、复场数值处理和计算追溯的 Python 作品集。**

> 仓库所有者已于2026-10-15确认代码公开及派生权限并授权公开上传，暂不添加开源许可证。个人贡献和团队分工仍待核实，不默认独立作者身份。这里展示的是软件工程能力，不是已证实的B/R理论或全波损耗预测。

## 30秒了解项目

源于反谐振空芯光纤研究中的三个实际工程需求：参数是否可信、复场计算是否一致、任务失败后结果能否追溯。精简版本不依赖COMSOL，不包含研究几何、真实场包、论文PDF或求解器。

|模块|已实现内容|能展示的能力|
|---|---|---|
|M1 参数校验|Pydantic、来源元数据、受限表达式、依赖求值与SI数值换算|输入契约、异常处理和可解释错误|
|M2 复场计算|有符号Poynting、带权Fourier、复最小二乘与残差|复数线性代数、积分与数值负控制|
|M3 任务追溯|固定dummy worker、退出码、日志、SHA256和JSON状态|进程控制、失败留存和拒绝覆盖|

架构：显式人工输入 → 契约/数值模块 → 独立输出目录；统一CLI按子命令调用模块。M1/M3不依赖M2数值核，M3没有任意命令或shell入口。

所有示例使用 **`ALGORITHMIC_FIXTURE_NOT_COMSOL`**。人工数组不保证满足Maxwell方程，不是仿真场、真实传播模式、泄漏损耗或收敛证据。

## 安装与实际命令

Python 3.11+为声明范围；当前仅Windows/Python3.13.1接受实际验收。建议建立新虚拟环境。在本目录中执行：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -c requirements-tested.txt ".[test]"
.\.venv\Scripts\python.exe -I -B -m optics_portfolio.mvp_cli parameters --config examples/configs/toy_valid.json --out runs/params
.\.venv\Scripts\python.exe -I -B -m optics_portfolio.mvp_cli fields-demo --out runs/fields
.\.venv\Scripts\python.exe -I -B -m optics_portfolio.mvp_cli task-demo --case success --out runs/task
.\.venv\Scripts\python.exe -I -B -m pytest tests -q
```

每次使用新输出目录；已有路径会被拒绝。M1人工结果为8mm→0.008m、半宽0.004m、90°→π/2。M2验证有限Fourier和及已知复标量；这些仅是可解析核对的算术。M3记录dummy任务的进程状态与验收状态。

负控制命令：将配置改为`toy_invalid.json`返回2；将dummy case改为`failure`返回1（worker退出7）；`validation_failure`虽然worker退出0，CLI仍返回1。以上预期失败不是被隐藏的测试失败。

## 测试与依赖

本候选已在全新Windows环境通过 **117项测试，0失败，6.36秒**，并完成三个模块的CLI正反例。使用wheel非编辑安装、无关cwd及`-I -B`执行，安装包不引用旧MVP目录。详见[候选测试摘要](docs/TEST_RESULTS.md)；这是本次独立复测，不是沿用旧记录。

运行依赖仅NumPy、Pydantic；pytest用于测试。`requirements-tested.txt`列出本次候选验收目标版本，不是完整带hash锁文件。包内部distribution名称保留`optics-portfolio-m2-private`以维持已测试的元数据查询，不代表模块只剩M2；导入名为`optics_portfolio`。

测试覆盖单位/来源/异常输入、非均匀权重、法向与相位控制、解析Fourier参考、复杂标量残差、进程失败、超时、hash改动及拒覆盖。没有真实物理求解、性能加速或Linux验收结论。

## 目录

```text
src/optics_portfolio/  三模块、统一CLI和固定dummy worker
examples/configs/     两份人工配置：正常与故意错误
tests/                自包含测试，无私有场数据
docs/                 契约限制、测试摘要、案例展示方案、发布准入表
```

原始运行日志、环境、缓存和构建输出保留在候选目录之外，不随本副本分发。不要把未来runs目录中的本机日志直接提交。

## 明确局限

- M1是数值单位转换，不是通用量纲推理或经过安全认证的表达式沙箱。
- M2采用峰值相量；有限轮廓净通量不是独立出射通道，观察范数不是物理能量；只接受人工fixture标签，没有真实场导入adapter。
- M3只运行固定dummy，不是集群调度器或资源监控；hash不是数字签名，原子替换不等于掉电恢复保证。
- 未证实B/R优于同信息量传统方法；原研究的NO_FORECAST、目标验证未开始、模态身份失败和机制未决保持，不因软件测试通过改判。

## 真实应用与公开权限

[COMSOL应用案例方案](docs/COMSOL_CASE_SHOWCASE_PLAN.md)只描述已有证据类型与待授权材料，不包含真实研究数据、图或未发表精确指标。个人负责范围、项目时间和团队信息须确认后再填写；不默认独立作者身份。

查看[来源与权属](PROVENANCE.md)和[发布准入表](docs/RELEASE_GATE.md)。本次公开授权不等于授予开源许可、承认全部个人贡献或认证物理研究结论；真实研究数据仍不在公开范围内。
