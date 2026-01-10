<script setup lang="tsx">
import { ref, reactive } from 'vue'
import { SelectRecord, type SelectTab } from '@/wintemplate/SelectRecord'
import { getDishGroupListApi } from '@/api/vadmin/product/dishGroup'
import { FormSchema } from '@/components/Form'
import { TableColumn } from '@/components/Table'

defineOptions({
  name: 'SelectDishgroup'
})

// ==================== Props ====================
interface SelectDishgroupProps {
  modelValue: boolean
  selectedRecords?: any[]
  selectMode?: 'single' | 'multiple' // 选择模式
  defaultSearchParams?: Record<string, any> // 默认查询参数
  selectType?: 'row' | 'column' // 选择类型
}

const selectDishgroupProps = withDefaults(defineProps<SelectDishgroupProps>(), {
  selectedRecords: () => [],
  selectMode: 'multiple',
  defaultSearchParams: () => ({}),
  selectType: 'column'
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
    field: 'stype',
    label: '类型',
    show: true,
    width: '120px'
  },
  {
    field: 'order_number',
    label: '排序号',
    show: true,
    width: '100px'
  }
])

// ==================== Tab 配置 ====================
const tabs = ref<SelectTab[]>([
  {
    label: '选择菜品分组',
    name: 'select',
    searchSchema: searchSchema,
    fetchDataApi: getDishGroupListApi,
    tableColumns: tableColumns,
    rowKey: 'id',
    displayField: (row: any) => {
      return row.name_unique || row.name_display || String(row.id || '')
    },
    selectMode: selectDishgroupProps.selectMode,
    defaultSearchParams: selectDishgroupProps.defaultSearchParams
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
    :model-value="selectDishgroupProps.modelValue"
    @update:model-value="(val: boolean) => emit('update:modelValue', val)"
    title="选择菜品分组"
    :tabs="tabs"
    :selected-records="selectDishgroupProps.selectedRecords"
    :select-mode="selectDishgroupProps.selectMode"
    :select-type="selectDishgroupProps.selectType"
    @confirm="handleConfirm"
    @cancel="handleCancel"
    @select="(records: any[], type: 'row' | 'column') => emit('select', records, type)"
  />
</template>

<style lang="less" scoped>
</style>

