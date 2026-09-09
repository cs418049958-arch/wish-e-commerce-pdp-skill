# 屏序与结构清单（V3，保留原文件路径）

多屏项目用 JSON 清单保持素材、版本和交付顺序。普通单屏编辑可使用简短说明；无需为校验补造动作、连接图或无关坐标。

## 项目字段

| 字段 | 规则 |
|---|---|
| schema_version | 新项目写 3；未填写按旧 V2 读取 |
| project | 项目名 |
| page_type | long、short-grayboard 或 single |
| task_mode | new、redesign、reuse、extend、edit、remove-copy |
| review_mode | checkpoints 或 autonomous |
| style_dna_id | 风格记录标识，未选定可写 pending |
| delivery_order | 需要交付的 screen_id 数组，保持策划／用户要求顺序；不包含跳过屏 |
| screens | 屏清单；跳过屏可用最小记录保留来源 |

## 普通屏核心字段

| 字段 | 规则 |
|---|---|
| screen_id | 两位数或以上的数字字符串，唯一；保留原编号可有跳号 |
| source_page_or_region | 页码、区域或文件名 |
| semantic_goal | 本屏主要传播目标 |
| exact_copy | 逐字文案数组；纯图为 [] |
| asset_plan | 数组，每项含 asset_id、source、use_policy、role；无现成素材可为空 |
| entity_count_exact | 必须准确的关键对象数量，例如每款产品；无产品／关键对象时可为 {} |
| primary_secondary_order | 视觉主次描述数组，至少一项 |
| style_dna_id | 与项目一致 |
| status | parsed、ready、generated、repair、qa_passed、user_approved、final、skipped；兼容 V2 旧状态 |
| final_file | 准备正式拼接时必填，终稿目录内的文件名，如 02-scene-v3.png |
| transition | 可选，描述与下一交付屏的衔接；长版需实际规划，首尾按需要描述 |

asset_plan.use_policy 取 direct-use、editable、reference、identity、approved-base、grayboard。
直接使用的素材不因写入提示词就算已复用；仍需检查成图来源和保留区域。
跳过屏最小记录为 screen_id、source_page_or_region、status=skipped。被跳过屏不得出现在 delivery_order。

## 条件字段

structural_requirements 是可选数组，仅列出本屏实际需要的约束：

- connections：要求非空 connection_graph，每项有 from、to、relation。
- anchors：要求非空 anchor_positions，每项有 entity、x、y、region，x/y 位于 0–1。
- axes：要求非空 shared_axes，每组至少两个对象名称。
- ports：要求非空 entry_exit_ports，每项有 continuity_group、object、from_screen、to_screen、edge_from、edge_to、normalized_x、diameter_or_width_ratio、material、lighting、direction、occlusion_forbidden。

端口从前一屏 bottom 到相邻交付屏 top，横向位置 0–1，宽度比例大于 0 且不大于 1。管道、动作与连接关系来自策划，不能为了简化字段而漏标确实需要的约束。
可额外记录 creative_mechanism、scene_layout、hero_action、protected_assets、evidence_presentation、forbidden_entities、forbidden_substitutions。没有实际要求时省略。

## 精简示例

```json
{
  "schema_version": 3,
  "project": "香氛合集详情页",
  "page_type": "long",
  "task_mode": "reuse",
  "review_mode": "checkpoints",
  "style_dna_id": "approved-kv-b2",
  "delivery_order": ["01", "02"],
  "screens": [
    {
      "screen_id": "01",
      "source_page_or_region": "已确认首屏",
      "semantic_goal": "介绍三款香型",
      "exact_copy": [],
      "asset_plan": [{"asset_id": "kv-b2", "source": "01-approved.png", "use_policy": "approved-base", "role": "确认首屏"}],
      "entity_count_exact": {"strawberry": 1, "lemon": 1, "avocado": 1},
      "primary_secondary_order": ["确认首屏原版"],
      "style_dna_id": "approved-kv-b2",
      "status": "user_approved",
      "final_file": "01-approved.png"
    },
    {
      "screen_id": "02",
      "source_page_or_region": "策划第2段",
      "semantic_goal": "表达对应香型的使用氛围",
      "exact_copy": [],
      "asset_plan": [{"asset_id": "scene-2", "source": "existing-scene.png", "use_policy": "direct-use", "role": "直接排版的场景"}],
      "entity_count_exact": {"lemon": 1},
      "primary_secondary_order": ["产品", "场景"],
      "style_dna_id": "approved-kv-b2",
      "status": "parsed",
      "transition": "承接首屏底部暖白背景"
    },
    {"screen_id": "03", "source_page_or_region": "用户本次排除的资料屏", "status": "skipped"}
  ]
}
```

示例用于说明格式，实际 exact_copy 必须来自项目资料。准备交付时补全所选屏的 final_file 并记录真实状态。

## 校验与拼接

```bash
python scripts/validate_screen_manifest.py --manifest screen-manifest.json
python scripts/stitch_screens.py --input-dir 03-final-screens --output long.png --screen-manifest screen-manifest.json --manifest stitch-report.json
```

首个脚本检查清单完整性和条件结构字段，不能识别成图中的物理关系、文字或审美。
拼接按 delivery_order 与 final_file 读取实际文件，拒绝额外旧稿、遗漏和不一致尺寸；默认不缩放。用户要求调整输出宽度时才使用 --resize，并再次检查文字可读性。
