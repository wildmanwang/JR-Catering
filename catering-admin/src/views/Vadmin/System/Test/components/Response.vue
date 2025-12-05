<script lang="ts">
import { reactive } from 'vue'
import { useValidator } from '@/hooks/web/useValidator'
import type { FreeFormField } from '@/wintemplate/baseFree'

const { required } = useValidator()

// ==================== 表单字段配置 ====================
export const formSchema: FreeFormField[] = [
  {
    field: 'name_unique',
    label: '名称',
    colProps: {
      span: 24
    },
    component: 'Input'
  },
  {
    field: 'name_display',
    label: '显示名称',
    colProps: {
      span: 24
    },
    component: 'Input'
  },
  {
    field: 'name_english',
    label: '英文名称',
    colProps: {
      span: 24
    },
    component: 'Input'
  },
  {
    field: 'kitchen_id',
    label: '厨部',
    colProps: {
      span: 12
    },
    component: 'Select',
    componentProps: {
      multiple: false,
      props: {
        label: 'name_unique',
        value: 'id'
      }
    }
    // 选项数据从主窗口传入，无需在此定义 optionApi
  },
  {
    field: 'price',
    label: '基础售价',
    colProps: {
      span: 12
    },
    component: 'Input'
  },
  {
    field: 'order_number',
    label: '排序号',
    colProps: {
      span: 12
    },
    component: 'Input'
  },
  {
    field: 'description',
    label: '简介',
    colProps: {
      span: 24
    },
    component: 'Input',
    componentProps: {
      type: 'textarea',
      rows: 4
    }
  },
  {
    field: 'description_english',
    label: '英文简介',
    colProps: {
      span: 24
    },
    component: 'Input',
    componentProps: {
      type: 'textarea',
      rows: 4
    }
  },
  {
    field: 'status',
    label: '状态',
    colProps: {
      span: 12
    },
    component: 'Select',
    componentProps: {
      disabled: true
    },
    value: 0
    // 选项数据从主窗口传入（dishStatusOptions），无需在此硬编码
  },
  {
    field: 'dish_images',
    label: '图片',
    type: 'image',
    colProps: {
      span: 24
    }
  }
]

// ==================== 表单验证规则 ====================
export const rules = reactive({
  name_unique: [required()],
  name_display: [required()],
  kitchen_id: [required()]
})

// ==================== Tab 配置 ====================
export const tabs = [
  { label: '基础信息', name: 'basic' },
  { label: '操作日志', name: 'log' }
]

// ==================== 特殊处理逻辑示例 ====================
// 如果需要定义特殊的处理逻辑、自定义组件等，可以在这里添加
// 例如：
// export const customHandlers = {
//   // 自定义字段处理
//   handleSpecialField: (data: any) => {
//     // 特殊处理逻辑
//   }
// }

// 或者定义自定义组件
// export const CustomComponent = defineComponent({
//   // 自定义组件定义
// })
</script>

<template>
  <!-- 
    此文件主要用于导出表单配置（formSchema, rules, tabs）
    如果需要定义特殊的组件、插槽或处理逻辑，可以在这里添加
    
    例如：
    - 自定义组件
    - 特殊的插槽内容
    - 额外的样式定义
  -->
  <div style="display: none;"></div>
</template>

<style lang="less" scoped>
/* 
  如果需要定义特殊的样式，可以在这里添加
  例如针对特定字段的自定义样式
*/
</style>

