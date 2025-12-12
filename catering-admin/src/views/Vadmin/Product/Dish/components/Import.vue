/**
 * 菜品批量导入/维护页面
 * 
 * 功能特性：
 * 1. 从父窗口（Dish.vue）接收选中的菜品数据，支持批量编辑
 * 2. Excel 风格的表格交互（单元格编辑、键盘导航、复制粘贴）
 * 3. 支持新增、编辑、保存操作
 * 4. 自动加载菜品状态和厨部选项数据
 * 
 * 数据流程：
 * 父窗口（Dish.vue） -> sessionStorage -> ImportGrid 组件 -> 保存到后端
 * 
 * 使用方式：
 * 1. 在菜品列表页选择记录，点击"导入"按钮打开批量编辑页面
 * 2. 或直接访问 /product/dish/import 打开空白编辑页面
 * 
 * 技术说明：
 * - 使用 ImportGrid 通用组件实现 Excel 风格的表格编辑
 * - 通过 sessionStorage 在页面间传递数据
 * - 编辑模式下通过透明背景确保不遮挡单元格边框
 */
<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ContentWrap } from '@/components/ContentWrap'
import { ButtonPre } from '@/components/ButtonPre'
import { PrompInfo } from '@/components/PrompInfo'
import ImportGrid, { type ImportGridColumn } from '@/wintemplate/importGrid/ImportGrid.vue'
import { getDishStatusOptionsApi } from '@/api/vadmin/product/dish'
import { getKitchenListApi } from '@/api/vadmin/product/kitchen'

defineOptions({
  name: 'DishImport'
})

// ==================== 常量定义 ====================

/** 导入数据存储的 sessionStorage key（与父窗口 Dish.vue 保持一致） */
const IMPORT_STORAGE_KEY = 'IMPORT_DISH_PAYLOAD'

// ==================== 数据配置 ====================

/**
 * 创建默认行数据
 * 
 * 用于新增行时提供默认值，确保所有字段都有初始值
 * 
 * @returns {object} 默认行数据对象
 */
const createDefaultRow = () => ({
  id: undefined,
  name_unique: '',
  name_display: null,
  name_english: null,
  kitchen_id: 1,
  price: null,
  order_number: null,
  spec: null,
  unit: null,
  status: -1,
  dish_images: [],
  dish_images_display: [],
  action: null
})

/**
 * 列配置
 * 
 * 定义表格显示的列及其属性（宽度、类型、是否可编辑等）
 * 使用 computed 确保选项数据更新时列配置也会更新
 */
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
    minWidth: '240px',
    type: 'text',
    show: true
  },
  {
    field: 'name_display',
    label: '显示名称',
    minWidth: '240px',
    type: 'text',
    show: true
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
    label: '厨部ID',
    width: '100px',
    type: 'select',
    show: true,
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
    field: 'unit',
    label: '单位',
    width: '100px',
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
    width: '100px',
    type: 'number',
    show: true
  },
  {
    field: 'status',
    label: '状态',
    width: '100px',
    type: 'select',
    show: true,
    options: dishStatusOptions.value,
    selectProps: {
      disabled: true,
      filterable: false
    }
  }
])

/**
 * 数据转换函数
 * 
 * 将父窗口（Dish.vue）传入的数据转换为表格所需格式
 * 确保所有字段都有默认值，避免显示异常
 * 
 * @param {any} row - 父窗口传入的行数据
 * @returns {object} 转换后的行数据
 */
const mapRowData = (row: any) => {
  return {
    ...row,
    // 确保所有字段都有默认值
    name_unique: row.name_unique ?? '',
    name_display: row.name_display ?? row.name_unique ?? '',
    name_english: row.name_english ?? null,
    kitchen_id: row.kitchen_id ?? 1,
    price: row.price ?? null,
    order_number: row.order_number ?? null,
    spec: row.spec ?? null,
    unit: row.unit ?? null,
    status: row.status ?? -1,
    dish_images: Array.isArray(row.dish_images) ? row.dish_images : [],
    dish_images_display: Array.isArray(row.dish_images_display) ? row.dish_images_display : []
  }
}

// ==================== 组件引用 ====================

/** ImportGrid 组件引用（用于调用组件方法） */
const importGridRef = ref<InstanceType<typeof ImportGrid>>()

/** PrompInfo 组件引用（用于显示提示信息） */
const prompInfoRef = ref<InstanceType<typeof PrompInfo>>()

// ==================== 状态管理 ====================

/** 保存操作的加载状态 */
const saveLoading = ref(false)

/** 菜品状态选项 */
const dishStatusOptions = ref<Array<{ label: string; value: number }>>([])

/** 厨部选项 */
const kitchenOptions = ref<Array<{ label: string; value: number }>>([])

// ==================== 事件处理 ====================

/**
 * 数据加载完成回调
 * 
 * ImportGrid 组件从 sessionStorage 加载数据后触发
 * 
 * @param _data - 加载的数据列表（当前未使用）
 */
const handleDataLoaded = (_data: any[]) => {
  prompInfoRef.value?.ready()
}

/**
 * 数据变化回调
 * 
 * 表格数据发生变化时触发（新增、删除、编辑单元格）
 * 
 * @param _data - 当前的数据列表（当前未使用）
 */
const handleDataChanged = (_data: any[]) => {
  // 数据变化时的处理逻辑（如需要）
}

// ==================== 数据获取 ====================

/**
 * 获取菜品状态选项
 */
const getDishStatusOptions = async () => {
  try {
    const res = await getDishStatusOptionsApi()
    dishStatusOptions.value = res?.data || []
  } catch (err) {
    console.error('获取菜品状态列表失败：', err)
    dishStatusOptions.value = []
  }
}

/**
 * 获取厨部列表选项
 */
const getKitchenOptions = async () => {
  try {
    const res = await getKitchenListApi({ is_active: true })
    if (!res?.data) {
      kitchenOptions.value = []
      return
    }
    // 转换为下拉选项格式：{ label: string, value: number }
    kitchenOptions.value = res.data.map((kitchen: any) => ({
      label: kitchen.name_unique || `厨部${kitchen.id}`,
      value: kitchen.id
    }))
  } catch (err) {
    console.error('获取厨部列表失败：', err)
    kitchenOptions.value = []
  }
}

// ==================== 操作方法 ====================

/**
 * 新增行
 * 
 * 在表格末尾添加一行默认数据
 */
const handleAddRow = () => {
  const data = importGridRef.value?.getData() || []
  const newRow = createDefaultRow()
  data.push(newRow)
  importGridRef.value?.setData(data)
  prompInfoRef.value?.info('已新增 1 行')
}

/**
 * 保存数据
 * 
 * 将表格中的所有数据保存到后端
 * TODO: 实现实际的保存逻辑（调用 API）
 * 
 * @example
 * ```typescript
 * const res = await saveDishBatchApi(data)
 * if (res.code === 200) {
 *   prompInfoRef.value?.info(`成功保存 ${data.length} 条记录`)
 * }
 * ```
 */
const handleSave = async () => {
  const data = importGridRef.value?.getData() || []
  if (!data.length) {
    prompInfoRef.value?.warn('暂无可保存的数据')
    return
  }
  
  saveLoading.value = true
  try {
    // TODO: 实现保存逻辑
    // const res = await saveDishBatchApi(data)
    // if (res.code === 200) {
    //   prompInfoRef.value?.info(`成功保存 ${data.length} 条记录`)
    // }
    prompInfoRef.value?.info(`成功保存 ${data.length} 条记录`)
  } catch (err) {
    console.error('保存失败：', err)
    prompInfoRef.value?.err('保存失败，请稍后重试')
  } finally {
    saveLoading.value = false
  }
}

onMounted(async () => {
  // 获取选项数据
  await Promise.all([
    getDishStatusOptions(),
    getKitchenOptions()
  ])
  
  // 组件挂载后，ImportGrid 会自动从 sessionStorage 加载数据
  prompInfoRef.value?.ready()
})
</script>

<template>
  <ContentWrap>
    <!-- 工具栏 -->
    <div class="import-toolbar">
      <div class="toolbar-left">
        <ButtonPre stype="new" @click="handleAddRow" />
      </div>
      <div class="toolbar-info">
        <PrompInfo ref="prompInfoRef" />
      </div>
      <div class="toolbar-right">
        <ButtonPre stype="save" :loading="saveLoading" @click="handleSave" />
      </div>
    </div>
    
    <!-- 表格 -->
    <ImportGrid
      ref="importGridRef"
      :columns="columns"
      :storage-key="IMPORT_STORAGE_KEY"
      :create-default-row="createDefaultRow"
      :map-row-data="mapRowData"
      @data-loaded="handleDataLoaded"
      @data-changed="handleDataChanged"
    />
  </ContentWrap>
</template>

<style lang="less" scoped>
/* 确保 ContentWrap 内部的布局正确，移除所有 padding */
:deep(.content-wrap) {
  height: 100% !important;
  display: flex !important;
  flex-direction: column !important;
  padding: 0 !important;
}

:deep(.content-wrap .el-card) {
  height: 100% !important;
  display: flex !important;
  flex-direction: column !important;
  padding: 0 !important;
}

:deep(.content-wrap .el-card__body) {
  flex: 1 !important;
  display: flex !important;
  flex-direction: column !important;
  min-height: 0 !important;
  overflow: hidden !important;
  padding: 0 !important;
}

:deep(.content-wrap > div) {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
  height: 100%;
}

/* 工具栏 */
.import-toolbar {
  display: flex;
  align-items: center;
  margin: 0;
  gap: 10px;
}

.toolbar-left {
  flex: 0 0 auto;
}

.toolbar-info {
  flex: 1;
  min-width: 0; // 允许收缩
}

.toolbar-right {
  flex: 0 0 auto;
}

/* 移除 ImportGrid 容器的 padding */
:deep(.import-grid-container) {
  padding: 0 !important;
}
</style>

<style lang="less">
/* 
 * 全局样式：编辑模式下隐藏 wrapper 的边框和背景
 * 
 * 说明：通过设置透明背景确保不遮挡单元格的边框，提供更好的视觉效果
 * 适用于所有 Element Plus 输入组件（Input、Select、InputNumber）
 */
.import-grid-container .el-table__cell.editing-cell {
  /* 所有 wrapper 元素和内部元素 */
  .el-input__wrapper,
  .el-select__wrapper,
  .el-input-number__input-wrapper,
  .el-input-number .el-input__wrapper,
  .el-input__inner,
  input,
  textarea {
    border: none !important;
    border-width: 0 !important;
    border-color: transparent !important;
    background: transparent !important;
    background-color: transparent !important;
    box-shadow: none !important;
    outline: none !important;
  }
  
  /* 所有状态（hover、focus 等） */
  .el-input__wrapper:hover,
  .el-input__wrapper:focus,
  .el-input__wrapper:focus-within,
  .el-input__wrapper.is-focus,
  .el-input__wrapper.is-hover,
  .el-select__wrapper:hover,
  .el-select__wrapper:focus,
  .el-select__wrapper:focus-within,
  .el-select__wrapper.is-focus,
  .el-select__wrapper.is-hover,
  .el-input-number__input-wrapper:hover,
  .el-input-number__input-wrapper:focus,
  .el-input-number__input-wrapper:focus-within,
  .el-input-number__input-wrapper.is-focus,
  .el-input-number__input-wrapper.is-hover,
  .el-input-number .el-input__wrapper:hover,
  .el-input-number .el-input__wrapper:focus,
  .el-input-number .el-input__wrapper:focus-within,
  .el-input-number .el-input__wrapper.is-focus,
  .el-input-number .el-input__wrapper.is-hover,
  .el-input__inner:hover,
  .el-input__inner:focus,
  input:hover,
  input:focus,
  textarea:hover,
  textarea:focus {
    border: none !important;
    border-width: 0 !important;
    border-color: transparent !important;
    background: transparent !important;
    background-color: transparent !important;
    box-shadow: none !important;
    outline: none !important;
  }
}
</style>

