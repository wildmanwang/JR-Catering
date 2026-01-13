<!--
  ImportDetail - DishGroup数据导入窗口
  
  功能：
  - 配置菜品和菜品分组的交叉数据
  - 从ImportBase窗口自动传递数据，打开交叉数据配置窗口
  - 支持通过配置的按钮选择行数据和列数据
-->
<script setup lang="ts">
import { ref } from 'vue'
import { ContentWrap } from '@/components/ContentWrap'
import { ImportCross } from '@/wintemplate/ImportCross'
import type { ImportCross as ImportCrossType } from '@/wintemplate/ImportCross'
import type { TableCrossDataConfigs } from '@/components/TableCross/src/TableCross.vue'
import SelectDish from '@/views/Vadmin/Product/Dish/components/SelectDish.vue'
import SelectDishgroup from './SelectDishgroup.vue'

defineOptions({
  name: 'DishGroupImportDetail'
})

// ==================== 行数据配置 ====================
/** 行数据配置 */
const rowDataConfig = ref({
  name: '菜品', // 数据名称
  allowAdd: true // 是否支持新增行
})

// ==================== 列数据配置 ====================
/** 列数据配置 */
const colDataConfig = ref({
  name: '菜品分组', // 数据名称
  allowAdd: true // 是否支持新增列
})

// ==================== 数据配置 ====================
/** 数据配置数组 */
const dataConfigs = ref<TableCrossDataConfigs>([
  { label: '配置菜品', type: 'int', format: '', primary: true },
  { label: '配置加价', type: 'decimal(12,2)', format: 'decimal(12,2)' }
])

// ==================== ImportCross 组件引用 ====================
const importCrossRef = ref<InstanceType<typeof ImportCrossType>>()

// ==================== 选择菜品窗口 ====================
/** 选择菜品窗口显示状态 */
const selectDishVisible = ref(false)

/** 已选菜品列表 */
const selectedDishes = ref<any[]>([])

/**
 * 打开选择菜品窗口
 */
const handleOpenSelectDish = () => {
  selectDishVisible.value = true
}

/**
 * 处理选择菜品确认
 * @param records - 选中的菜品记录列表
 */
const handleSelectDishConfirm = (records: any[]) => {
  selectedDishes.value = records
  // 将选中的菜品数据传递给ImportCross组件，作为行数据
  if (importCrossRef.value && records.length > 0) {
    importCrossRef.value.addRowDatas(records)
  }
}

/**
 * 处理选择菜品（直接选择，不关闭窗口）
 * @param records - 选中的菜品记录列表
 * @param type - 选择类型：'row' 表示行数据，'column' 表示列数据
 */
const handleSelectDish = (records: any[], type: 'row' | 'column') => {
  if (type === 'row' && importCrossRef.value && records.length > 0) {
    importCrossRef.value.addRowDatas(records)
  }
}

/**
 * 处理选择菜品取消
 */
const handleSelectDishCancel = () => {
  // 取消操作，无需处理
}

// ==================== 选择菜品分组窗口 ====================
/** 选择菜品分组窗口显示状态 */
const selectDishgroupVisible = ref(false)

/** 已选菜品分组列表 */
const selectedDishgroups = ref<any[]>([])

/**
 * 打开选择菜品分组窗口
 */
const handleOpenSelectDishgroup = () => {
  selectDishgroupVisible.value = true
}

/**
 * 处理选择菜品分组确认
 * @param records - 选中的菜品分组记录列表
 */
const handleSelectDishgroupConfirm = (records: any[]) => {
  selectedDishgroups.value = records
  // 将选中的菜品分组数据传递给ImportCross组件，作为列数据
  if (importCrossRef.value && records.length > 0) {
    importCrossRef.value.addColDatas(records)
  }
}

/**
 * 处理选择菜品分组（直接选择，不关闭窗口）
 * @param records - 选中的菜品分组记录列表
 * @param type - 选择类型：'row' 表示行数据，'column' 表示列数据
 */
const handleSelectDishgroup = (records: any[], type: 'row' | 'column') => {
  if (type === 'column' && importCrossRef.value && records.length > 0) {
    importCrossRef.value.addColDatas(records)
  }
}

/**
 * 处理选择菜品分组取消
 */
const handleSelectDishgroupCancel = () => {
  // 取消操作，无需处理
}

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
  // TODO: 实现保存逻辑
  // 这里可以调用保存API，将交叉数据保存到后端
  // try {
  //   const res = await saveDishGroupCrossDataApi(_data)
  //   if (res) {
  //     ElMessage.success('保存成功')
  //   }
  // } catch (error) {
  //   ElMessage.error('保存失败')
  // }
}
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
      :on-save="handleSave"
      @data-changed="handleDataChanged"
      @select-row-data="handleOpenSelectDish"
      @select-col-data="handleOpenSelectDishgroup"
    />

    <!-- 选择菜品窗口 -->
    <SelectDish
      v-model="selectDishVisible"
      :selected-records="selectedDishes"
      select-mode="multiple"
      select-type="row"
      @confirm="handleSelectDishConfirm"
      @cancel="handleSelectDishCancel"
      @select="handleSelectDish"
    />

    <!-- 选择菜品分组窗口 -->
    <SelectDishgroup
      v-model="selectDishgroupVisible"
      :selected-records="selectedDishgroups"
      select-mode="multiple"
      select-type="column"
      @confirm="handleSelectDishgroupConfirm"
      @cancel="handleSelectDishgroupCancel"
      @select="handleSelectDishgroup"
    />
  </ContentWrap>
</template>
