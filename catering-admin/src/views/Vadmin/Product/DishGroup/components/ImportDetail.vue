<!--
  ImportDetail - DishGroup数据导入窗口
  
  功能：
  - 配置菜品和菜品分组的交叉数据
  - 从ImportBase窗口自动传递数据，打开交叉数据配置窗口
  - 支持通过配置的按钮选择行数据和列数据
-->
<script setup lang="ts">
import { ref, computed } from 'vue'
import { ContentWrap } from '@/components/ContentWrap'
import { ImportCross } from '@/wintemplate/ImportCross'
import type { ImportCross as ImportCrossType } from '@/wintemplate/ImportCross'
import type { TableCrossDataConfigs } from '@/components/TableCross/src/TableCross.vue'
import type { StatusStoreItem } from '@/wintemplate/WinSheet'
import SelectDish from '@/views/Vadmin/Product/Dish/components/SelectDish.vue'
import SelectDishgroup from './SelectDishgroup.vue'

defineOptions({
  name: 'DishGroupImportDetail'
})

// ==================== 行数据配置 ====================
/** 行数据配置 */
const rowDataConfig = ref({
  name: '菜品', // 数据名称
  allowAdd: true, // 是否支持新增行
  selectComponent: SelectDish, // 选择数据的组件
  selectMode: 'multiple' as const, // 选择模式：多选
  passSelectedRecords: false // 是否回传已选记录给选择窗口
})

// ==================== 列数据配置 ====================
/** 列数据配置 */
const colDataConfig = ref({
  name: '菜品分组', // 数据名称
  allowAdd: true, // 是否支持新增列
  selectComponent: SelectDishgroup, // 选择数据的组件
  selectMode: 'multiple' as const, // 选择模式：多选
  passSelectedRecords: false // 是否回传已选记录给选择窗口
})

// ==================== 数据配置 ====================
/** 数据配置数组 */
const dataConfigs = ref<TableCrossDataConfigs>([
  { label: '配置菜品', type: 'number', component: 'NumberInput', format: 'integer', primary: true },
  { label: '配置加价', type: 'number', component: 'NumberInput', format: 'decimal(12,2)' }
])

// ==================== ImportCross 组件引用 ====================
const importCrossRef = ref<InstanceType<typeof ImportCrossType>>()

// ==================== 事件处理 ====================
/**
 * 处理数据变化
 * @param _data - 变化的数据
 */
const handleDataChanged = (_data: any) => {
  // 数据变化时的处理逻辑
}

/**
 * 处理保存
 * @param _data - 需要保存的数据
 */
const handleSave = async (_data: any) => {
  // 保存逻辑待实现
  // 可以调用保存API，将交叉数据保存到后端
  // try {
  //   const res = await saveDishGroupCrossDataApi(_data)
  //   if (res) {
  //     ElMessage.success('保存成功')
  //   }
  // } catch (error) {
  //   ElMessage.error('保存失败')
  // }
}

// ==================== 额外的缓存配置项 ====================
/**
 * 额外的状态存储配置项
 * 用于缓存 ImportDetail 组件特有的状态
 * 
 * 说明：
 * - 这些状态会在窗口切换和页面刷新时自动保存和恢复
 * - 使用 computed 确保响应式数据变化时能正确获取状态
 */
const extraStores = computed<StatusStoreItem[]>(() => [
  // 可以添加更多的缓存配置项，例如：
  // {
  //   name: 'customFilter',
  //   getState: () => ({ filterValue: customFilterValue.value }),
  //   setState: (state) => { customFilterValue.value = state.filterValue }
  // }
])
</script>

<template>
  <ContentWrap>
    <!-- 
      ImportCross 交叉数据配置组件
      - 自动从 sourceStorageKey 读取 ImportBase 的数据并作为列显示
      - 根据 rowDataConfig 和 colDataConfig 自动显示选择按钮
      - 按钮点击时会触发 select-row-data 或 select-col-data 事件
    -->
    <ImportCross
      ref="importCrossRef"
      storage-key="IMPORT_CROSS_PAYLOAD"
      source-storage-key="IMPORT_DishGroup_PAYLOAD"
      window-id="DishGroupImportDetail"
      :name-column-width="200"
      :data-column-width="160"
      :sum-column-width="120"
      :data-configs="dataConfigs"
      :row-data-config="rowDataConfig"
      :col-data-config="colDataConfig"
      :allow-direct-edit="false"
      :on-save="handleSave"
      :extra-stores="extraStores"
      @data-changed="handleDataChanged"
    />
  </ContentWrap>
</template>
