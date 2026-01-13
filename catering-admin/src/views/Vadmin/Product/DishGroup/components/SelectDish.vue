<script setup lang="tsx">
import { ref, reactive, computed } from 'vue'
import { SelectRecord, type SelectTab } from '@/wintemplate/SelectRecord'
import { getDishListApi } from '@/api/vadmin/product/dish'
import { FormSchema } from '@/components/Form'
import { TableColumn } from '@/components/Table'

defineOptions({
  name: 'SelectDish'
})


// ==================== Emits ====================
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'confirm': [records: any[]]
  'cancel': []
  'select': [records: any[], type: 'row' | 'column']
}>()

// ==================== 查询条件配置 ====================
const searchSchema = reactive<FormSchema[]>([
  {
    field: 'status',
    label: '状态',
    component: 'Select',
    componentProps: {
      style: {
        width: '200px'
      },
      placeholder: '请选择状态',
      clearable: true
    },
    optionApi: async () => {
      // 这里可以调用状态选项API，暂时返回空数组
      return []
    }
  },
  {
    field: 'fuzzy_query_str',
    label: '模糊查询',
    component: 'Input',
    componentProps: {
      style: {
        width: '100%' // Input 组件设置为 100%，SelectRecord 会处理为 flex 填充剩余空间
      },
      placeholder: '请输入名称或显示名称',
      clearable: true
    }
  }
])

// ==================== 表格列配置 ====================
const tableColumns = reactive<TableColumn[]>([
  {
    field: 'id',
    label: 'ID',
    show: false,
    width: '80px'
  },
  {
    field: 'name_unique',
    label: '名称',
    show: true,
    minWidth: '200px'
  },
  {
    field: 'name_display',
    label: '显示名称',
    show: true,
    minWidth: '200px'
  },
  {
    field: 'kitchen_name_unique',
    label: '厨部',
    show: true,
    width: '150px'
  },
  {
    field: 'spec',
    label: '规格',
    show: true,
    width: '150px'
  },
  {
    field: 'price',
    label: '基础售价',
    show: true,
    width: '120px'
  },
  {
    field: 'status',
    label: '状态',
    show: true,
    width: '100px',
    slots: {
      default: (data: any) => {
        const row = data.row
        return (
          <>
            <span>{row.status === 1 ? '启用' : '禁用'}</span>
          </>
        )
      }
    }
  }
])

// ==================== Props ====================
interface SelectDishProps {
  modelValue: boolean
  selectedRecords?: any[]
  selectMode?: 'single' | 'multiple' // 选择模式
  defaultSearchParams?: Record<string, any> // 默认查询参数
  selectType?: 'row' | 'column' // 选择类型
}

// 使用方的配置：selectMode 可能是 'single'、'multiple'，也可能不配置（undefined）
// 如果不配置，SelectRecord 模板会使用默认值 'single'
const selectDishProps = withDefaults(defineProps<SelectDishProps>(), {
  selectedRecords: () => [],
  // selectMode 不设置默认值，由使用方配置或父组件传递
  // 如果未配置，SelectRecord 模板会使用默认值 'single'
  defaultSearchParams: () => ({}),
  selectType: 'row'
})

// ==================== Tab 配置 ====================
// 使用 computed 确保 selectMode 和 defaultSearchParams 能够响应式更新
const tabs = computed<SelectTab[]>(() => {
  return [
    {
      label: '选择菜品',
      name: 'select',
      searchSchema: searchSchema,
      fetchDataApi: getDishListApi,
      tableColumns: tableColumns,
      rowKey: 'id',
      displayField: (row: any) => {
        return row.name_unique || row.name_display || String(row.id || '')
      },
      selectMode: selectDishProps.selectMode, // 使用使用方配置的值，如果未配置则为 undefined，SelectRecord 会使用默认值 'single'
      defaultSearchParams: selectDishProps.defaultSearchParams
    }
  ]
})

// ==================== 事件处理 ====================
const handleConfirm = (records: any[]) => {
  emit('confirm', records)
}

const handleCancel = () => {
  emit('cancel')
}
</script>

<template>
  <SelectRecord
    :model-value="selectDishProps.modelValue"
    @update:model-value="(val: boolean) => emit('update:modelValue', val)"
    title="选择菜品"
    :tabs="tabs"
    :selected-records="selectDishProps.selectedRecords"
    :select-mode="selectDishProps.selectMode"
    :select-type="selectDishProps.selectType"
    @confirm="handleConfirm"
    @cancel="handleCancel"
    @select="(records: any[], type: 'row' | 'column') => emit('select', records, type)"
  />
</template>

<style lang="less" scoped>
</style>

