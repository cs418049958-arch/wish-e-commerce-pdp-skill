# 策划生产合同 V2

## 目录

1. 合同目的
2. 项目字段
3. 单屏字段
4. 拓扑写法
5. 第 05 屏示例
6. 放行规则

## 1. 合同目的

把策划语义转换为可检查的对象数量、连接拓扑、锚点、中心轴、进出屏接口和禁止项。没有合同，不生成。

## 2. 项目字段

```json
{
  "project": "项目名",
  "page_type": "long",
  "style_dna_id": "B-tech-clean-v1",
  "screens": []
}
```

`page_type` 仅允许 `long` 或 `short-grayboard`。

## 3. 单屏必填字段

| 字段 | 写法 |
|---|---|
| screen_id | 两位数，例如 `05` |
| source_page_or_region | 页码、表格区域或截图位置 |
| semantic_goal | 唯一传播目标 |
| exact_copy | 正式文案数组；没有则 `[]` |
| creative_mechanism | 不可替换的创意机制 |
| scene_layout | 区域划分和阅读动线 |
| hero_action | 核心动作 |
| entity_count_exact | `{对象名: 准确数量}` |
| connection_graph | `{from,to,relation}` 数组 |
| anchor_positions | `{entity,x,y,region}`；x/y 使用 0–1 |
| shared_axes | 必须共轴的对象数组 |
| entry_exit_ports | 跨屏物体接口数组；没有则 `[]` |
| primary_secondary_order | 至少 1 个视觉层级对象 |
| evidence_presentation | 证据布局；没有则写 `none` |
| protected_assets | 正式文字、包装、Logo、报告等 |
| forbidden_entities | 禁止出现的对象 |
| forbidden_substitutions | 禁止替代版式 |
| style_dna_id | 对应视觉 DNA |
| status | 初始为 `parsed` |

不要用“若干、适量、大概、类似”等模糊词描述关键对象。

## 4. 拓扑写法

- `connected_to`：必须物理连接。
- `aligned_center_x`：必须共用垂直中心轴。
- `inside`：对象必须位于另一对象内部。
- `flows_to`：液体、粒子或动势方向。
- `surrounds`：证书、菌种或卖点围绕主体。
- `above/below/left_of/right_of`：明确相对位置。
- `continues_to_next_screen`：从本屏边缘延续到下一屏。

锚点不是精确设计坐标，而是验收容差基准。中心轴类关系默认允许画布宽度 2% 以内误差；跨屏接口默认允许 1%。

## 5. 第 05 屏示例

```json
{
  "screen_id": "05",
  "source_page_or_region": "策划长图第05段",
  "semantic_goal": "透明啫喱溶解毛发并恢复畅通",
  "exact_copy": ["3分钟起效"],
  "creative_mechanism": "产品倒入浴室地漏，地漏下方唯一一根透明U型管展示同一流向内的包裹、断裂、溶解",
  "scene_layout": "上部真实浴室地漏操作，下部透明管道剖面，报告位于侧边",
  "hero_action": "产品液体从地漏进入同一根U型管",
  "entity_count_exact": {
    "floor_drain": 1,
    "transparent_u_pipe": 1,
    "product": 1,
    "report_card": 1
  },
  "connection_graph": [
    {"from": "floor_drain", "to": "vertical_inlet", "relation": "connected_to"},
    {"from": "vertical_inlet", "to": "transparent_u_pipe", "relation": "connected_to"},
    {"from": "hair", "to": "transparent_u_pipe", "relation": "inside"},
    {"from": "clear_gel", "to": "transparent_u_pipe", "relation": "flows_to"}
  ],
  "anchor_positions": [
    {"entity": "floor_drain", "x": 0.5, "y": 0.34, "region": "upper"},
    {"entity": "transparent_u_pipe", "x": 0.5, "y": 0.67, "region": "lower"}
  ],
  "shared_axes": [["floor_drain", "vertical_inlet", "transparent_u_pipe.inlet"]],
  "entry_exit_ports": [],
  "primary_secondary_order": ["transparent_u_pipe", "product_action", "report_card"],
  "evidence_presentation": "侧边轻量毛玻璃证据卡；无机构、编号、印章",
  "protected_assets": ["产品包装", "3分钟起效", "报告真实内容"],
  "forbidden_entities": ["second_pipe", "branch_pipe", "second_outlet", "floating_product"],
  "forbidden_substitutions": ["双管过程分镜", "孤立展示管", "普通圆贴徽章"],
  "style_dna_id": "B-tech-clean-v1",
  "status": "parsed"
}
```

## 6. 放行规则

- 对象数量与 `entity_count_exact` 不一致：失败。
- `connection_graph` 任一连接缺失或错位：失败。
- `shared_axes` 明显偏移：失败。
- 禁止对象出现：失败。
- 用通用卡片或分镜替代策划机制：失败。
- 合同字段只写在提示词但没有成图反查记录：失败。
