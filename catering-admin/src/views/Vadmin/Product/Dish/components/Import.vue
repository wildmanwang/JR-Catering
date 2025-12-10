/**
 * 菜品批量导入/维护页面
 * 
 * 功能说明：
 * 1. 从父窗口（Dish.vue）接收选中的菜品数据
 * 2. 在 Excel 风格的表格中批量编辑菜品信息
 * 3. 支持新增、编辑、保存操作
 * 
 * 数据流程：
 * 父窗口（Dish.vue） -> sessionStorage -> ImportGrid -> 保存到后端
 * 
 * 使用方式：
 * 1. 在菜品列表页选择记录，点击"导入"按钮
 * 2. 或直接访问 /product/dish/import（打开空白页）
 */
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ContentWrap } from '@/components/ContentWrap'
import { ButtonPre } from '@/components/ButtonPre'
import { PrompInfo } from '@/components/PrompInfo'
import ImportGrid, { type ImportGridColumn } from '@/wintemplate/importGrid/ImportGrid.vue'

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
 */
const columns: ImportGridColumn[] = [
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
    type: 'number',
    show: true
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
    type: 'number',
    show: true
  }
]

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

// ==================== 事件处理 ====================

/**
 * 数据加载完成回调
 * 
 * ImportGrid 组件从 sessionStorage 加载数据后触发
 * 
 * @param {any[]} data - 加载的数据列表
 */
const handleDataLoaded = (data: any[]) => {
  console.log('数据加载完成，共', data.length, '条记录')
  prompInfoRef.value?.ready()
}

/**
 * 数据变化回调
 * 
 * 表格数据发生变化时触发（新增、删除、编辑单元格）
 * 
 * @param {any[]} data - 当前的数据列表
 */
const handleDataChanged = (data: any[]) => {
  console.log('数据已变化，当前', data.length, '条记录')
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
    // 示例：
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

onMounted(() => {
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

