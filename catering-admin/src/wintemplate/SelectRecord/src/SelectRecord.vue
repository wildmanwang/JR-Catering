<script setup lang="tsx">
import { computed, ref, watch, unref, nextTick } from 'vue'
import { ElScrollbar, ElTabs, ElTabPane, ElCard, ElMenu, ElMenuItem, ElMessage } from 'element-plus'
import { ResponseDrawer, type ToolbarButton } from '@/wintemplate/ResponseDrawer'
import { Search } from '@/components/Search'
import { FormSchema } from '@/components/Form'
import { Table, TableColumn } from '@/components/Table'
import { useTable } from '@/hooks/web/useTable'
import { VueDraggable } from 'vue-draggable-plus'

defineOptions({
  name: 'SelectRecord'
})

// ==================== 类型定义 ====================
/** 选择模式 */
export type SelectMode = 'single' | 'multiple'

/** Tab 配置 */
export interface SelectTab {
  label: string // Tab 标签
  name: string // Tab 名称
  searchSchema?: FormSchema[] // 查询条件配置
  fetchDataApi?: (params: any) => Promise<any> // 数据源接口
  tableColumns?: TableColumn[] // 表格列配置
  rowKey?: string // 行唯一标识字段，默认 'id'
  displayField?: string | ((row: any) => string) // 显示字段或函数，用于已选列表显示
  defaultSearchParams?: Record<string, any> // 默认查询参数
  selectMode?: SelectMode // 选择模式：'single' | 'multiple'，默认 'multiple'
}

/** 组件 Props */
interface Props {
  modelValue: boolean // 抽屉显示状态
  title?: string // 抽屉标题
  width?: string | number // 抽屉宽度
  tabs?: SelectTab[] // Tab 配置，默认1个选项卡
  selectedRecords?: any[] // 初始已选记录
  maxSelect?: number // 最大选择数量，0表示不限制
  selectMode?: SelectMode // 全局选择模式，如果 Tab 中没有配置则使用此值
  selectType?: 'row' | 'column' // 选择类型：'row' 表示选择行数据，'column' 表示选择列数据
}

// ==================== Props 定义 ====================
const props = withDefaults(defineProps<Props>(), {
  width: 'calc(100vw - 600px)',
  tabs: () => [
    { label: '选择', name: 'select' }
  ],
  selectedRecords: () => [],
  maxSelect: 0,
  selectMode: 'multiple',
  selectType: 'row'
})

// ==================== Emits 定义 ====================
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'confirm': [records: any[]] // 确认选择事件，返回已选记录列表
  'cancel': [] // 取消事件
  'select': [records: any[], type: 'row' | 'column'] // 选择事件，返回选中的记录和类型（行或列）
}>()

// ==================== 计算属性 ====================
/** 抽屉显示状态 */
const drawerVisible = computed({
  get: () => props.modelValue,
  set: (val) => {
    emit('update:modelValue', val)
  }
})

/** 抽屉标题 */
const drawerTitle = computed(() => {
  return props.title || '选择记录'
})

/** 计算抽屉宽度 */
const drawerWidth = computed(() => {
  const defaultWidth = 'max(700px, calc(100vw - 600px))'
  if (props.width) {
    if (typeof props.width === 'string' && props.width !== defaultWidth) {
      return props.width
    }
    if (typeof props.width === 'number') {
      return props.width
    }
  }
  return defaultWidth
})

/** 计算工具栏按钮配置（用于传递给 ResponseDrawer） */
const toolbarButtons = computed<ToolbarButton[]>(() => {
  const buttons: ToolbarButton[] = []
  
  // 确认按钮
  buttons.push({
    stype: 'ok',
    show: true,
    onClick: handleConfirm
  })
  
  return buttons
})

// ==================== Tab 管理 ====================
const activeTab = ref(props.tabs[0]?.name || 'select')

// 监听 tabs 变化，确保 activeTab 始终有效
watch(() => props.tabs, (tabs) => {
  if (tabs.length > 0) {
    const currentTabExists = tabs.find(tab => tab.name === activeTab.value)
    if (!currentTabExists) {
      activeTab.value = tabs[0].name
    }
  }
}, { immediate: true })

// 监听 activeTab 变化，初始化默认查询参数并刷新数据
watch(() => activeTab.value, () => {
  initDefaultSearchParams()
  // 刷新当前 Tab 的表格
  const currentTable = tableRefs.value[activeTab.value]
  if (currentTable?.methods?.getList) {
    currentTable.methods.getList()
  }
})

// ==================== 已选记录管理 ====================
/** 已选记录列表 */
const selectedList = ref<any[]>([])

/** 当前选中的已选记录索引 */
const activeSelectedIndex = ref<string>('')

/** 获取记录的显示文本 */
const getRecordDisplayText = (record: any, tab: SelectTab): string => {
  if (typeof tab.displayField === 'function') {
    return tab.displayField(record)
  }
  if (typeof tab.displayField === 'string') {
    return record[tab.displayField] || String(record[tab.rowKey || 'id'] || '')
  }
  // 默认使用 rowKey 或 id
  const key = tab.rowKey || 'id'
  return String(record[key] || '')
}

/** 获取记录的唯一标识 */
const getRecordKey = (record: any, tab: SelectTab): string | number => {
  const key = tab.rowKey || 'id'
  return record[key]
}

/** 检查记录是否已选中 */
const isRecordSelected = (record: any, tab: SelectTab): boolean => {
  const recordKey = getRecordKey(record, tab)
  return selectedList.value.some(item => {
    const itemKey = getRecordKey(item, tab)
    return itemKey === recordKey
  })
}

/** 获取当前 Tab 的选择模式 */
const getSelectMode = (tab: SelectTab): SelectMode => {
  return tab.selectMode || props.selectMode || 'multiple'
}

/** 添加选中记录 */
const addSelectedRecord = (record: any, tab: SelectTab) => {
  const selectMode = getSelectMode(tab)
  
  // 单选模式：如果已选中其他记录，先清空
  if (selectMode === 'single') {
    if (selectedList.value.length > 0) {
      selectedList.value = []
    }
  } else {
    // 多选模式：检查是否已选中
    if (isRecordSelected(record, tab)) {
      ElMessage.warning('该记录已选中')
      return
    }
    
    // 检查最大选择数量
    if (props.maxSelect > 0 && selectedList.value.length >= props.maxSelect) {
      ElMessage.warning(`最多只能选择 ${props.maxSelect} 条记录`)
      return
    }
  }
  
  selectedList.value.push({ ...record })
  if (selectMode === 'single') {
    ElMessage.success('已选择')
  } else {
    ElMessage.success('已添加到选择列表')
  }
}

/** 移除选中记录 */
const removeSelectedRecord = (index: number) => {
  selectedList.value.splice(index, 1)
  if (activeSelectedIndex.value === String(index)) {
    activeSelectedIndex.value = ''
  }
}

/** 清空已选记录 */
const clearSelectedRecords = () => {
  selectedList.value = []
  activeSelectedIndex.value = ''
}

// 监听 props.selectedRecords 变化，初始化已选记录
watch(() => props.selectedRecords, (records) => {
  if (records && records.length > 0) {
    selectedList.value = [...records]
  } else {
    selectedList.value = []
  }
}, { immediate: true, deep: true })


// ==================== 查询和表格 ====================
/** 当前激活的 Tab */
const currentTab = computed(() => {
  return props.tabs.find(tab => tab.name === activeTab.value) || props.tabs[0]
})

/** 查询参数 */
const searchParams = ref<Recordable>({})

/** 初始化默认查询参数 */
const initDefaultSearchParams = () => {
  const tab = currentTab.value
  if (tab.defaultSearchParams) {
    searchParams.value = { ...tab.defaultSearchParams }
  } else {
    searchParams.value = {}
  }
}

/** 表格实例映射（Tab名称 -> 表格实例） */
const tableRefs = ref<Record<string, any>>({})

/** 初始化表格（为每个 Tab 创建表格实例） */
const initTables = () => {
  props.tabs.forEach(tab => {
    if (tab.fetchDataApi && tab.tableColumns) {
      const { tableRegister, tableState, tableMethods } = useTable({
        fetchDataApi: async () => {
          const { pageSize, currentPage } = tableState
          const res = await tab.fetchDataApi!({
            page: unref(currentPage),
            limit: unref(pageSize),
            ...unref(searchParams)
          })
          return {
            list: res.data || [],
            total: res.count || 0
          }
        }
      })
      
      tableRefs.value[tab.name] = {
        register: tableRegister,
        state: tableState,
        methods: tableMethods
      }
    }
  })
}

// 监听 tabs 变化，重新初始化表格
watch(() => props.tabs, () => {
  initTables()
}, { immediate: true, deep: true })

// 监听 drawerVisible 变化，打开时初始化表格
watch(() => drawerVisible.value, (val) => {
  if (val) {
    // 窗口打开时，确保表格已初始化
    if (Object.keys(tableRefs.value).length === 0) {
      initTables()
    }
    // 初始化已选记录
    if (props.selectedRecords && props.selectedRecords.length > 0) {
      selectedList.value = [...props.selectedRecords]
    } else {
      selectedList.value = []
    }
    activeSelectedIndex.value = ''
    // 初始化默认查询参数
    initDefaultSearchParams()
    // 刷新当前 Tab 的表格
    nextTick(() => {
      const currentTable = tableRefs.value[activeTab.value]
      if (currentTable?.methods?.getList) {
        currentTable.methods.getList()
      }
    })
  } else {
    // 关闭时清空已选记录
    selectedList.value = []
    activeSelectedIndex.value = ''
  }
})

/** 处理查询 */
const handleSearch = (params: Recordable) => {
  searchParams.value = { ...params }
  // 刷新当前 Tab 的表格
  const currentTable = tableRefs.value[activeTab.value]
  if (currentTable?.methods?.getList) {
    currentTable.methods.getList()
  }
}

/** 处理重置 */
const handleReset = () => {
  searchParams.value = {}
  // 刷新当前 Tab 的表格
  const currentTable = tableRefs.value[activeTab.value]
  if (currentTable?.methods?.getList) {
    currentTable.methods.getList()
  }
}

// ==================== 方法 ====================
/** 处理确认 */
const handleConfirm = () => {
  emit('confirm', [...selectedList.value])
  drawerVisible.value = false
}

/** 处理选择（用于直接返回数据给调用方，不关闭窗口） */
const handleSelect = (type: 'row' | 'column') => {
  if (selectedList.value.length > 0) {
    emit('select', [...selectedList.value], type)
    // 单选模式下，选择后自动关闭窗口
    const tab = currentTab.value
    if (getSelectMode(tab) === 'single') {
      drawerVisible.value = false
    } else {
      // 多选模式下，清空已选列表，继续选择
      selectedList.value = []
    }
  }
}

/** 处理取消 */
const handleCancel = () => {
  drawerVisible.value = false
  emit('cancel')
}

/** 处理表格行选择 */
const handleTableRowClick = (row: any, tab: SelectTab) => {
  const selectMode = getSelectMode(tab)
  
  if (selectMode === 'single') {
    // 单选模式：直接选择并返回
    selectedList.value = [{ ...row }]
    // 单选模式下，选择后立即触发 select 事件并关闭窗口
    emit('select', [{ ...row }], props.selectType)
    drawerVisible.value = false
  } else {
    // 多选模式：添加到已选列表
    addSelectedRecord(row, tab)
  }
}

/** 处理已选记录拖拽结束 */
const handleDragEnd = () => {
  // 拖拽结束后可以在这里处理排序逻辑
}

// ==================== ResponseDrawer 引用 ====================
const responseDrawerRef = ref<InstanceType<typeof ResponseDrawer>>()

// ==================== 信息提示 ====================
/**
 * 显示信息提示
 */
const showInfo = (type?: 'info' | 'warn' | 'error' | null, message?: string | null) => {
  // 通过 ResponseDrawer 的 showInfo 方法显示提示信息
  if (responseDrawerRef.value) {
    responseDrawerRef.value.showInfo(type || null, message || null)
  }
}

// ==================== 暴露方法 ====================
defineExpose({
  getSelectedRecords: () => [...selectedList.value],
  clearSelectedRecords,
  showInfo
})
</script>

<template>
  <ResponseDrawer
    ref="responseDrawerRef"
    v-model="drawerVisible"
    :title="drawerTitle"
    :width="drawerWidth"
    :toolbar-buttons="toolbarButtons"
    @close="handleCancel"
    @cancel="handleCancel"
  >
    <!-- 主体内容区域 -->
    <div class="select-record-content">
      <!-- 左侧：已选记录 -->
      <div class="selected-records-panel">
        <ElCard class="selected-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span>已选列表</span>
              <span class="selected-count">({{ selectedList.length }})</span>
            </div>
          </template>
          <ElScrollbar class="selected-scrollbar">
            <VueDraggable
              v-model="selectedList"
              :animation="200"
              handle=".drag-handle"
              @end="handleDragEnd"
            >
              <ElMenu
                v-model:default-active="activeSelectedIndex"
                class="selected-menu"
              >
                <ElMenuItem
                  v-for="(record, index) in selectedList"
                  :key="index"
                  :index="String(index)"
                  class="selected-menu-item"
                >
                  <div class="menu-item-content">
                    <span class="drag-handle">☰</span>
                    <span class="menu-item-text">
                      {{ getRecordDisplayText(record, currentTab) }}
                    </span>
                    <span
                      class="menu-item-remove"
                      @click.stop="removeSelectedRecord(index)"
                    >
                      ✕
                    </span>
                  </div>
                </ElMenuItem>
              </ElMenu>
            </VueDraggable>
            <div v-if="selectedList.length === 0" class="empty-selected">
              暂无已选记录
            </div>
          </ElScrollbar>
        </ElCard>
      </div>

      <!-- 右侧：选择区 -->
      <div class="select-panel">
        <ElTabs v-model="activeTab" class="select-tabs">
          <ElTabPane
            v-for="tab in props.tabs"
            :key="tab.name"
            :label="tab.label"
            :name="tab.name"
          >
            <div class="tab-content">
              <!-- 查询工具栏区 -->
              <div v-if="tab.searchSchema && tab.searchSchema.length > 0" class="search-toolbar">
                <Search
                  :schema="tab.searchSchema"
                  @search="handleSearch"
                  @reset="handleReset"
                />
              </div>

              <!-- 查询列表区 -->
              <div v-if="tab.fetchDataApi && tab.tableColumns" class="table-area">
                <Table
                  v-if="tableRefs[tab.name]"
                  :columns="tab.tableColumns"
                  :data="tableRefs[tab.name].state.dataList"
                  :loading="tableRefs[tab.name].state.loading"
                  :pagination="{
                    total: tableRefs[tab.name].state.total
                  }"
                  @register="tableRefs[tab.name].register"
                  @row-click="(row: any) => handleTableRowClick(row, tab)"
                />
              </div>
            </div>
          </ElTabPane>
        </ElTabs>
      </div>
    </div>
  </ResponseDrawer>
</template>

<style lang="less" scoped>
/* SelectRecord 内容区样式 */
.select-record-content {
  flex: 1;
  display: flex;
  overflow: hidden;
  gap: 20px;
}

.selected-records-panel {
  width: 300px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;

  .selected-card {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;

    :deep(.el-card__body) {
      flex: 1;
      display: flex;
      flex-direction: column;
      overflow: hidden;
      padding: 0;
    }

    .card-header {
      display: flex;
      align-items: center;
      gap: 8px;
      font-weight: 500;

      .selected-count {
        color: var(--el-color-primary);
        font-weight: normal;
      }
    }
  }

  .selected-scrollbar {
    flex: 1;
    min-height: 0;

    :deep(.el-scrollbar__wrap) {
      overflow-x: hidden;
    }
  }

  .selected-menu {
    border: none;
    width: 100%;

    .selected-menu-item {
      padding: 0;
      height: auto;
      line-height: normal;

      .menu-item-content {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 10px 15px;
        width: 100%;

        .drag-handle {
          cursor: move;
          color: var(--el-text-color-secondary);
          font-size: 14px;
          user-select: none;
        }

        .menu-item-text {
          flex: 1;
          min-width: 0;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        .menu-item-remove {
          cursor: pointer;
          color: var(--el-color-danger);
          font-size: 16px;
          padding: 0 4px;
          opacity: 0.7;
          transition: opacity 0.2s;

          &:hover {
            opacity: 1;
          }
        }
      }

      &:hover {
        background-color: var(--el-fill-color-light);
      }
    }
  }

  .empty-selected {
    padding: 40px 20px;
    text-align: center;
    color: var(--el-text-color-placeholder);
  }
}

.select-panel {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;

  .select-tabs {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;

    :deep(.el-tabs__content) {
      flex: 1;
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }

    :deep(.el-tab-pane) {
      flex: 1;
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }
  }

  .tab-content {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  .search-toolbar {
    flex-shrink: 0;
    margin-bottom: 15px;
  }

  .table-area {
    flex: 1;
    min-height: 0;
    overflow: hidden;
  }
}
</style>

