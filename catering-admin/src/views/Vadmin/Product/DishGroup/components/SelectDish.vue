<script setup lang="tsx">
import { ref, reactive } from 'vue'
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
    colProps: {
      span: 8
    },
    componentProps: {
      style: {
        width: '100%'
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
    colProps: {
      span: 8
    },
    componentProps: {
      style: {
        width: '100%'
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

const selectDishProps = withDefaults(defineProps<SelectDishProps>(), {
  selectedRecords: () => [],
  selectMode: 'multiple',
  defaultSearchParams: () => ({}),
  selectType: 'row'
})

// ==================== Tab 配置 ====================
const tabs = ref<SelectTab[]>([
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
    selectMode: selectDishProps.selectMode,
    defaultSearchParams: selectDishProps.defaultSearchParams
  }
])

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

