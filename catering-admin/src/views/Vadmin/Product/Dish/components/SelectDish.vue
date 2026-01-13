<!--
  SelectDish - 选择菜品组件
  
  功能说明：
  这是一个封装了 SelectRecord 的菜品选择组件，用于选择菜品记录。
  默认单选模式，可通过 select-mode prop 修改为多选模式。
  
  使用方式：
  <SelectDish
    v-model="drawerVisible"
    :selected-records="selectedDishes"
    select-mode="single"
    @confirm="handleConfirm"
    @cancel="handleCancel"
    @select="handleSelect"
  />
-->
<script setup lang="tsx">
import { reactive, useAttrs, computed } from 'vue'
import { SelectRecord } from '@/wintemplate/SelectRecord'
import { getDishListApi, getDishStatusOptionsApi } from '@/api/vadmin/product/dish'
import { FormSchema } from '@/components/Form'
import { TableColumn } from '@/components/Table'

defineOptions({
  name: 'SelectDish'
})

// ==================== 查询条件配置 ====================
const searchSchema = reactive<FormSchema[]>([
  {
    field: 'status',
    label: '状态',
    component: 'Select',
    value: 1,
    componentProps: {
      style: {
        width: '200px'
      },
      placeholder: '请选择状态',
      clearable: true
    },
    optionApi: async () => {
      const res = await getDishStatusOptionsApi()
      return res.data || []
    }
  },
  {
    field: 'fuzzy_query_str',
    label: '模糊查询',
    component: 'Input',
    value: '',
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
interface selectRecProps {
  modelValue: boolean
  selectedRecords?: any[]
  selectMode?: 'single' | 'multiple' // 选择模式
  selectType?: 'row' | 'column' // 选择类型
  title?: string // 抽屉标题
  fetchDataApi?: (params: any) => Promise<any> // 数据源接口
  rowKey?: string // 行唯一标识字段
  displayField?: string | ((row: any) => string) // 显示字段或函数
}

const selectRecProps = withDefaults(defineProps<selectRecProps>(), {
  selectedRecords: () => [],
  selectMode: 'single', // 默认值：单选模式（如果父组件没有传递，则使用此默认值）
  selectType: 'row',
  title: '选择菜品',
  fetchDataApi: () => getDishListApi,
  rowKey: 'id',
  displayField: () => (row: any) => row.name_unique
})

// 获取 $attrs，但排除 select-mode 和 select-type，因为它们已经在 props 中定义了
// 这样可以确保显式传递的 props 优先级高于 $attrs 中的值
const attrs = useAttrs()
const filteredAttrs = computed(() => {
  const { 'select-mode': _, 'select-type': __, ...rest } = attrs
  return rest
})

</script>

<template>
  <!-- 
    事件透传说明：
    所有事件（包括 update:modelValue、confirm、cancel、select）都通过 v-bind="$attrs" 自动透传
    由 SelectRecord 统一管理和触发，无需在此重复定义
  -->
  <SelectRecord
    :model-value="selectRecProps.modelValue"
    :title="selectRecProps.title"
    :search-schema="searchSchema"
    :fetch-data-api="selectRecProps.fetchDataApi"
    :table-columns="tableColumns"
    :row-key="selectRecProps.rowKey"
    :display-field="selectRecProps.displayField"
    :selected-records="selectRecProps.selectedRecords"
    :select-mode="selectRecProps.selectMode"
    :select-type="selectRecProps.selectType"
    v-bind="filteredAttrs"
  />
</template>

<style lang="less" scoped>
</style>

