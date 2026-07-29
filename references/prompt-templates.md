# 提示词模板

## 目录

1. 概念整屏
2. 生产终稿
3. 结构重建
4. 受保护资产定向修正
5. 短版灰版
6. 无文案信息版

## 1. 概念整屏

```text
Asset: 电商详情页第 <NN> 屏概念稿
Goal: <唯一传播目标>
Planning source: <页码/区域>
Creative mechanism: <不可丢失机制>
Scene layout: <区域和阅读动线>
Hero action: <核心动作>
Entity count exact: <对象=准确数量>
Connection graph: <对象A → 关系 → 对象B>
Anchors and shared axes: <位置与共轴对象>
Entry/exit ports: <跨屏接口；没有写 none>
Visual hierarchy: <第一/第二/第三主体>
Evidence: <证据形式>
Style DNA: <完整视觉 DNA，不写“沿用某方案”>
Product identity: <原始产品图为真值>
Exact copy: <逐字文案>
Forbidden entities: <禁止对象>
Forbidden substitutions: <禁止通用版式>
Output: 一张完整扁平化概念整屏，用于确认构图、场景、材质和视觉语言
```

## 2. 生产终稿

```text
Asset: 电商详情页第 <NN> 屏生产终稿
Use approved concept: <已确认概念稿>
Planning contract: <完整结构合同>
Style DNA: <完整视觉 DNA>
Protected assets: <正式中文、数字、Logo、包装、报告、关键Icon>
Scene generation: 使用 ImageGen 完成已确认的场景、人物、管道、材质、光影和装饰
Asset integrity: 受保护资产以用户原图或确定性复现为真值；不得重写、重绘、猜测或新增
Output: 最终扁平 PNG；即使制作过程分层，交付不要求可编辑分层
QA: 先结构、再视觉、最后逐字内容与产品身份
Avoid: 假文字、错误数字、假Logo、虚构报告、包装漂移、普通字体/Icon、第二结构
```

工具环境只能整屏 ImageGen 时，补充：

```text
Render all content in one flattened result, but treat every protected asset as immutable. Change no supplied character, number, logo, package label, report detail, or already-approved icon. If any protected item cannot be preserved exactly, return a new concept candidate rather than claiming production approval.
```

## 3. 结构重建

用于对象数量、连接、中心轴、人物动作或策划构图错误：

```text
Rebuild from source; do not edit the rejected image as the structural base.
Source of truth: <策划源页> + <产品身份> + <视觉DNA>
Exact entity counts: <对象数量>
Required topology: <连接图>
Shared axes and anchors: <位置>
Forbidden entities: <第二根管、支管、第二出口等>
Keep visual DNA: <标题、Icon、材质、光线、色彩和信息密度完整规则>
Protected assets: <不得漂移内容>
Reject if: 数量、接口、轴线、视觉DNA或受保护资产任一错误
```

## 4. 受保护资产定向修正

仅用于单个文字、数字、Logo、包装或报告错误：

```text
Edit target: 第 <NN> 屏
Change only: <唯一受保护资产>
Keep unchanged: 构图、对象数量、连接拓扑、产品位置、场景、光线、色板、标题、其他文案、其他数字、Icon和报告
Verify after edit: 列出全部受保护资产并逐项复核，不只检查本次修改项
Avoid: 重画整屏、改变其他字符、增加脚注、生成机构/编号/印章、风格降级
```

如果定向修正导致任何其他受保护资产漂移，撤销该候选并改用确定性资产合成或重新生成。

## 5. 短版灰版

```text
Image 1: 短版灰版，像素级版式母版
Image 2: 产品身份真值
Lock canvas: 原宽高和比例
Lock gutters: 两侧白边全高保留，宽度、颜色、位置不变
Lock layout: 模块顺序、坐标、圆角、间距、Logo、标题、文字、数字、Icon、脚注和样式不变
Planning contract per module: <对象数量、动作、空间关系>
Fill only: <允许填充区域和内容>
Avoid: 改画布、删白边、重排、改字、场景越界、遮挡文案、漏掉策划机制
```

## 6. 无文案信息版

仅在完整设计确认且用户明确需要后：

```text
Keep unchanged: 原画布、白边、背景、模块结构、产品、包装原生Logo/文字、场景、人物/手部动作、使用演示、材质、光影
Remove only: 页面排版标题、正文、数字、卖点、角标、Icon、脚注、步骤标签和说明
Output: 与确认稿构图一致的无文案信息版
Avoid: 删除产品、包装信息或场景；重排模块；改尺寸；生成假字
```
