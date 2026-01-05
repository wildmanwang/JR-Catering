<!--
  ImportDetail - DishGroup数据导入窗口
  
  功能：用于配置Dish和DishGroup的交叉数据
  从ImportBase窗口自动传递数据，打开交叉数据配置窗口
-->
<script setup lang="ts">
import { ContentWrap } from '@/components/ContentWrap'
import ImportCross from '@/wintemplate/importCross/ImportCross.vue'

defineOptions({
  name: 'DishGroupImportDetail'
})

// ==================== 常量 ====================
// ImportBase窗口的storage key（自动从该窗口读取数据）
const IMPORT_BASE_STORAGE_KEY = 'IMPORT_DishGroup_PAYLOAD'
// ImportCross窗口的storage key（用于保存交叉数据）
const IMPORT_CROSS_STORAGE_KEY = 'IMPORT_CROSS_PAYLOAD'

// ==================== 事件处理 ====================
/**
 * 处理数据变化
 */
const handleDataChanged = (data: any) => {
  console.log('数据变化:', data)
}

/**
 * 处理保存
 */
const handleSave = (data: any) => {
  console.log('保存数据:', data)
  // TODO: 实现保存逻辑
}
</script>

<template>
  <ContentWrap>
    <!-- 
      ImportCross 会自动从 sourceStorageKey 读取 ImportBase 的数据
      并将这些数据作为列（DishGroup）显示
    -->
    <ImportCross
      storage-key="IMPORT_CROSS_PAYLOAD"
      source-storage-key="IMPORT_DishGroup_PAYLOAD"
      window-id="DishGroupImportDetail"
      :name-column-width="200"
      :data-column-width="160"
      :sum-column-width="120"
      @data-changed="handleDataChanged"
      @save="handleSave"
    />
  </ContentWrap>
</template>

<style lang="less" scoped>
</style>

