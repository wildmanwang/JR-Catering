# BaseGrid 通用表格模板

## 简介

BaseGrid 是一个通用的数据浏览表格模板，支持数据列类型、数据多选、数据分页等功能。通过简单的配置即可实现复杂的数据表格展示。

## 功能特性

1. **支持多种列类型**：
   - `selection`: 多选列
   - `image`: 图片列（支持预览）
   - `text`: 普通文本列
   - `action`: 操作列（自定义插槽）

2. **数据分页**：自动处理分页逻辑

3. **数据多选**：支持表格行多选功能

4. **图片预览**：图片列支持点击预览功能

## 使用示例

### 基本用法

```vue
<script setup lang="tsx">
import { ref } from 'vue'
import { BaseGrid } from '@/wintemplate/BaseGrid'
import { getDishListApi, delDishListApi } from '@/api/vadmin/product/dish'
import { BaseButton } from '@/components/Button'

// 定义列配置
const columns = [
  {
    field: 'selection',
    label: '',
    type: 'selection'
  },
  {
    field: 'dish_image',
    label: '图片',
    type: 'image',
    width: '110px',
    imageListField: 'dish_images', // 图片列表字段
    defaultImage: '/src/assets/imgs/no_image.png'
  },
  {
    field: 'name_unique',
    label: '名称',
    type: 'text',
    minWidth: '240px'
  },
  {
    field: 'name_display',
    label: '显示名称',
    type: 'text',
    minWidth: '240px'
  },
  {
    field: 'kitchen_name_unique',
    label: '分类',
    type: 'text',
    width: '160px'
  },
  {
    field: 'spec',
    label: '规格',
    type: 'text',
    width: '160px'
  },
  {
    field: 'unit',
    label: '单位',
    type: 'text',
    width: '160px'
  },
  {
    field: 'price',
    label: '基础售价',
    type: 'text',
    width: '120px'
  },
  {
    field: 'status',
    label: '状态',
    type: 'text',
    width: '100px',
    formatter: (row) => {
      // 自定义格式化函数
      const statusMap = { 1: '启用', 0: '禁用' }
      return statusMap[row.status] || '未知'
    }
  },
  {
    field: 'action',
    label: '操作',
    type: 'action',
    width: '140px',
    actionSlots: (data) => {
      const row = data.row
      return (
        <>
          <BaseButton type="primary" link size="small" onClick={() => editAction(row)}>
            修改
          </BaseButton>
          <BaseButton type="danger" link size="small" onClick={() => delData(row)}>
            删除
          </BaseButton>
        </>
      )
    }
  }
]

// 搜索参数
const searchParams = ref({})

// 数据获取接口
const fetchDataApi = async (params: { page: number; limit: number; [key: string]: any }) => {
  const res = await getDishListApi(params)
  // 处理数据（参考 Dish.vue 的数据处理逻辑）
  if (res.data) {
    res.data.map((row: any) => (row.dish_images.sort((a: string, b: string) => a.localeCompare(b))))
    res.data.forEach((o: any) => (o.dish_images = o.dish_images.map((p: string) => p.split('-').slice(1).join('-'))))
  }
  return {
    data: res.data || [],
    count: res.count || 0
  }
}

// 删除接口
const fetchDelApi = async (ids: string[] | number[] | number | string) => {
  const res = await delDishListApi(ids)
  return res.code === 200
}

// 操作函数
const editAction = (row: any) => {
  console.log('编辑', row)
}

const delData = (row: any) => {
  console.log('删除', row)
}
</script>

<template>
  <BaseGrid
    :columns="columns"
    :fetch-data-api="fetchDataApi"
    :fetch-del-api="fetchDelApi"
    :search-params="searchParams"
    node-key="id"
    :show-action="true"
  >
    <template #toolbar>
      <BaseButton type="primary" @click="addAction">新增</BaseButton>
      <BaseButton type="danger" @click="batchDelete">批量删除</BaseButton>
    </template>
  </BaseGrid>
</template>
```

## API

### Props

| 参数 | 说明 | 类型 | 默认值 |
|------|------|------|--------|
| columns | 列配置数组 | `GridColumn[]` | 必填 |
| fetchDataApi | 数据获取接口 | `Function` | 必填 |
| fetchDelApi | 删除接口 | `Function` | 可选 |
| nodeKey | 行键，用于多选 | `string` | `'id'` |
| showAction | 是否显示操作栏 | `boolean` | `false` |
| reserveSelection | 是否保留选择（分页后保留） | `boolean` | `false` |
| searchParams | 搜索参数 | `Record<string, any>` | `{}` |
| defaultImage | 默认图片路径 | `string` | `'/src/assets/imgs/no_image.png'` |

### GridColumn 配置

| 参数 | 说明 | 类型 | 默认值 |
|------|------|------|--------|
| field | 字段名 | `string` | 必填 |
| label | 列标题 | `string` | 必填 |
| type | 列类型 | `'selection' \| 'image' \| 'text' \| 'action'` | `'text'` |
| width | 列宽度 | `string \| number` | - |
| minWidth | 最小宽度 | `string \| number` | - |
| align | 对齐方式 | `'left' \| 'center' \| 'right'` | - |
| fixed | 固定列 | `boolean \| 'left' \| 'right'` | - |
| show | 是否显示 | `boolean` | `true` |
| formatter | 格式化函数 | `(row: any) => any` | - |
| imageField | 图片字段名（图片列专用） | `string` | - |
| imageListField | 图片列表字段名（图片列专用） | `string` | - |
| defaultImage | 默认图片路径（图片列专用） | `string` | - |
| imageHeight | 图片高度（图片列专用） | `string` | `'60px'` |
| actionSlots | 操作列插槽函数（操作列专用） | `(data: any) => JSX.Element` | - |

### 暴露的方法

通过 `ref` 可以访问以下方法：

- `getList()`: 刷新数据
- `getSelections()`: 获取选中的行
- `tableMethods`: 表格方法对象
- `tableState`: 表格状态对象

## 注意事项

1. `fetchDataApi` 函数需要返回 `{ data: any[], count: number }` 格式的数据
2. 图片列会自动处理图片路径和预览功能
3. 操作列需要通过 `actionSlots` 函数返回 JSX 元素
4. 搜索参数变化时，需要手动调用 `getList()` 刷新数据

