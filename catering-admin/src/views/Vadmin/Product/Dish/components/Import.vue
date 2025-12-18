/**
 * 菜品批量导入/维护页面
 * 
 * 使用 ImportGrid 组件实现 Excel 风格的批量编辑
 * 数据通过 sessionStorage 从父窗口（Dish.vue）传递
 */
<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ContentWrap } from '@/components/ContentWrap'
import ImportGrid, { type ImportGridColumn, type SaveConfig, type ToolbarButton } from '@/wintemplate/importGrid/ImportGrid.vue'
import { getDishStatusOptionsApi, addDishListApi, putDishListApi, getDishApi } from '@/api/vadmin/product/dish'
import { getKitchenListApi } from '@/api/vadmin/product/kitchen'

defineOptions({
  name: 'DishImport'
})

// ==================== 常量 ====================
const IMPORT_STORAGE_KEY = 'IMPORT_DISH_PAYLOAD'

// ==================== 状态 ====================
const dishStatusOptions = ref<Array<{ label: string; value: number }>>([])
const kitchenOptions = ref<Array<{ label: string; value: number }>>([])

// ==================== 列配置 ====================
const columns = computed<ImportGridColumn[]>(() => [
  {
    field: 'id',
    label: 'ID',
    width: '80px',
    type: 'text',
    show: false
  },
  {
    field: 'name_unique',
    label: '名称',
    minWidth: '200px',
    type: 'text',
    show: true,
    required: true,
    value: ''
  },
  {
    field: 'name_display',
    label: '显示名称',
    minWidth: '200px',
    type: 'text',
    show: true,
    required: true
  },
  {
    field: 'name_english',
    label: '英文名称',
    minWidth: '200px',
    type: 'text',
    show: true
  },
  {
    field: 'kitchen_id',
    label: '厨部',
    width: '100px',
    type: 'select',
    show: true,
    required: true,
    options: kitchenOptions.value,
    selectProps: {
      disabled: false,
      filterable: false
    }
  },
  {
    field: 'spec',
    label: '规格',
    width: '160px',
    type: 'text',
    show: true
  },
  {
    field: 'price',
    label: '基础售价',
    width: '120px',
    type: 'number',
    show: true
  },
  {
    field: 'order_number',
    label: '排序号',
    width: '80px',
    type: 'number',
    show: true
  },
  {
    field: 'dish_images',
    label: '图片',
    width: '480px',
    type: 'image',
    size: 'small',
    show: true,
    value: []
  },
  {
    field: 'status',
    label: '状态',
    width: '60px',
    type: 'select',
    show: true,
    options: dishStatusOptions.value,
    selectProps: {
      disabled: true,
      filterable: false
    },
    value: -1
  }
])

// ==================== 数据获取 ====================
const getDishStatusOptions = async () => {
  try {
    const res = await getDishStatusOptionsApi()
    dishStatusOptions.value = res?.data || []
  } catch (err) {
    console.error('获取菜品状态列表失败：', err)
    dishStatusOptions.value = []
  }
}

const getKitchenOptions = async () => {
  try {
    const res = await getKitchenListApi({ is_active: true })
    kitchenOptions.value = res?.data?.map((kitchen: any) => ({
      label: kitchen.name_unique || `厨部${kitchen.id}`,
      value: kitchen.id
    })) || []
  } catch (err) {
    console.error('获取厨部列表失败：', err)
    kitchenOptions.value = []
  }
}

// ==================== 配置 ====================
const toolbarButtons = computed<ToolbarButton[]>(() => [
  { type: 'add', stype: 'new' },
  { type: 'save', stype: 'save' }
])

const saveConfig = computed<SaveConfig>(() => ({
  requiredFields: [
    { field: 'name_unique', label: '名称' },
    { field: 'name_display', label: '显示名称' },
    { field: 'kitchen_id', label: '厨部' }
  ],
  addApi: addDishListApi,
  updateApi: putDishListApi,
  getDetailApi: getDishApi,
  preprocessData: (data: any, isNew: boolean) => {
    return isNew ? { ...data, status: 0 } : data
  }
}))

onMounted(async () => {
  await Promise.all([getDishStatusOptions(), getKitchenOptions()])
})
</script>

<template>
  <ContentWrap>
    <ImportGrid
      :columns="columns"
      :storage-key="IMPORT_STORAGE_KEY"
      :save-config="saveConfig"
      :toolbar-buttons="toolbarButtons"
    />
  </ContentWrap>
</template>

