<!--
  ImportCross - 交叉数据导入模板
  
  功能：处理Dish和DishGroup的交叉数据配置
  支持多套配置值切换（使用菜品、配置加价）
-->
<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import TableCross, { type TableCrossRow, type TableCrossColumn, type TableCrossDataConfigs } from '@/components/TableCross/src/TableCross.vue'
import { ButtonPlus } from '@/components/ButtonPlus'
import { PromptInfo } from '@/components/PromptInfo'
import { ElSelect, ElOption, ElRadioGroup, ElRadioButton } from 'element-plus'
import { getBranchListApi } from '@/api/vadmin/system/branch'

/**
 * 行数据配置
 */
export interface RowDataConfig {
  name: string // 数据名称，例如：菜品
  allowAdd: boolean // 是否支持新增行
}

/**
 * 列数据配置
 */
export interface ColDataConfig {
  name: string // 数据名称，例如：菜品分组
  allowAdd: boolean // 是否支持新增列
}

/**
 * 按钮配置
 */
export interface ButtonConfig {
  stype: string // 按钮类型
  label?: string // 按钮文本（可选）
  onClick?: () => void // 点击事件处理函数（可选）
  show?: boolean // 是否显示，默认 true
  buttonType?: 'row' | 'column' | 'custom' // 按钮类型标识：行数据、列数据、自定义
}

/**
 * 组件 Props 接口
 */
export interface ImportCrossProps {
  /** 数据存储的 sessionStorage key（用于在页面间传递数据） */
  storageKey?: string
  /** 源数据存储的 sessionStorage key（用于从上一个窗口自动读取数据，如 ImportBase） */
  sourceStorageKey?: string
  /** 行数据记录数组（原 dishes，改为通用名称） */
  rowDatas?: any[]
  /** 列数据记录数组（原 dishGroups，改为通用名称） */
  colDatas?: any[]
  /** @deprecated 使用 rowDatas 代替 */
  dishes?: any[]
  /** @deprecated 使用 colDatas 代替 */
  dishGroups?: any[]
  /** 行数据配置 */
  rowDataConfig?: RowDataConfig
  /** 列数据配置 */
  colDataConfig?: ColDataConfig
  /** 按钮配置数组 */
  buttonConfigs?: ButtonConfig[]
  /** 窗口标识 */
  windowId?: string
  /** 名称列宽度（第一列） */
  nameColumnWidth?: number
  /** 数据列宽度 */
  dataColumnWidth?: number
  /** 汇总列宽度 */
  sumColumnWidth?: number
  /** 数据配置数组（支持多套数据配置） */
  dataConfigs?: TableCrossDataConfigs
  /** 保存处理函数 */
  onSave?: (data: any) => Promise<void> | void
}

const props = withDefaults(defineProps<ImportCrossProps>(), {
  storageKey: 'IMPORT_CROSS_PAYLOAD',
  sourceStorageKey: '',
  rowDatas: () => [],
  colDatas: () => [],
  rowDataConfig: () => ({ name: '行数据', allowAdd: true }),
  colDataConfig: () => ({ name: '列数据', allowAdd: true }),
  buttonConfigs: () => [],
  windowId: 'ImportCross',
  nameColumnWidth: 200,
  dataColumnWidth: 160,
  sumColumnWidth: 120,
  dataConfigs: () => []
})

const emit = defineEmits<{
  (e: 'dataChanged', data: any): void
  (e: 'save', data: any): void
  (e: 'select-row-data'): void // 选择行数据事件
  (e: 'select-col-data'): void // 选择列数据事件
}>()

// ==================== 状态管理 ====================
/** 门店ID */
const branchId = ref<number | null>(null)

/** 门店选项列表 */
const branchOptions = ref<any[]>([])

/** 数据切换类型：'use_dish' | 'price_add'（向后兼容，当没有数据配置时使用） */
const dataType = ref<'use_dish' | 'price_add'>('use_dish')

/** 当前选中的数据配置索引（从0开始） */
const currentDataConfigIndex = ref<number>(0)

/** 行数据记录列表（原 dishList，改为通用名称） */
const rowDataList = ref<any[]>([])

/** 列数据记录列表（原 dishGroupList，改为通用名称） */
const colDataList = ref<any[]>([])

/** 交叉数据配置（多套配置值） */
const crossData = ref<{
  use_dish: Record<string, Record<string, number | null>> // { dishId: { dishGroupId: value } }
  price_add: Record<string, Record<string, number | null>> // { dishId: { dishGroupId: value } }
}>({
  use_dish: {},
  price_add: {}
})

// ==================== 组件引用 ====================
const prompInfoRef = ref<InstanceType<typeof PromptInfo>>()
const tableCrossRef = ref<InstanceType<typeof TableCross>>()

// 为了在模板中使用
const dataConfigs = computed(() => props.dataConfigs ?? [])
const nameColumnWidth = computed(() => props.nameColumnWidth)
const dataColumnWidth = computed(() => props.dataColumnWidth)
const sumColumnWidth = computed(() => props.sumColumnWidth)

/** 按钮配置（根据 rowDataConfig 和 colDataConfig 自动生成，或使用配置的 buttonConfigs） */
const buttonConfigs = computed(() => {
  // 如果配置了 buttonConfigs，优先使用
  if (props.buttonConfigs && props.buttonConfigs.length > 0) {
    return props.buttonConfigs
  }
  
  // 否则根据 rowDataConfig 和 colDataConfig 自动生成
  const configs: ButtonConfig[] = []
  
  // 如果行数据配置允许新增，添加选择行数据按钮
  if (props.rowDataConfig?.allowAdd) {
    configs.push({
      stype: 'select',
      label: props.rowDataConfig.name || '行数据',
      show: true,
      buttonType: 'row'
    })
  }
  
  // 如果列数据配置允许新增，添加选择列数据按钮
  if (props.colDataConfig?.allowAdd) {
    configs.push({
      stype: 'select',
      label: props.colDataConfig.name || '列数据',
      show: true,
      buttonType: 'column'
    })
  }
  
  return configs
})

/**
 * 处理按钮点击
 * @param btn - 按钮配置
 */
const handleButtonClick = (btn: ButtonConfig) => {
  // 如果配置了 onClick，优先使用
  if (btn.onClick) {
    btn.onClick()
    return
  }
  
  // 否则根据 buttonType 来判断
  if (btn.buttonType === 'row') {
    emit('select-row-data')
  } else if (btn.buttonType === 'column') {
    emit('select-col-data')
  } else {
    // 如果没有 buttonType，尝试根据 label 来判断（向后兼容）
    if (btn.label === props.rowDataConfig?.name || btn.label === '行数据') {
      emit('select-row-data')
    } else if (btn.label === props.colDataConfig?.name || btn.label === '列数据') {
      emit('select-col-data')
    }
  }
}

// ==================== 计算属性 ====================
/** TableCross的行数据 */
const tableRows = computed<TableCrossRow[]>(() => {
  return rowDataList.value.map(rowData => {
    const row: TableCrossRow = {
      id: rowData.id,
      name: rowData.name_unique || rowData.name_display || ''
    }
    
    // 为每个列数据添加所有数据配置的值
    colDataList.value.forEach((colData) => {
      // 如果有数据配置，使用多套数据存储
      if (props.dataConfigs && props.dataConfigs.length > 0) {
        props.dataConfigs.forEach((_config, configIndex) => {
          const dataKey = `__data_${configIndex}_${colData.id}`
          // 从 crossData 中获取值（保持向后兼容）
          const oldValue = crossData.value[dataType.value]?.[String(rowData.id)]?.[String(colData.id)]
          // 优先使用新格式，如果没有则使用旧格式
          row[dataKey] = oldValue ?? null
        })
      } else {
        // 没有数据配置，使用旧的格式（向后兼容）
        const value = crossData.value[dataType.value]?.[String(rowData.id)]?.[String(colData.id)] ?? null
        row[String(colData.id)] = value
      }
    })
    
    return row
  })
})

/** TableCross的列数据 */
const tableColumns = computed<TableCrossColumn[]>(() => {
  return colDataList.value.map(colData => ({
    id: colData.id,
    name: colData.name_unique || colData.name_display || ''
  }))
})

// ==================== 初始化 ====================
/**
 * 加载门店列表
 */
const loadBranchList = async () => {
  try {
    const res = await getBranchListApi({ is_active: true })
    if (res?.data) {
      branchOptions.value = Array.isArray(res.data) ? res.data : []
    }
  } catch (error) {
    if (prompInfoRef.value) {
      prompInfoRef.value.err('加载门店列表失败')
    }
  }
}

/**
 * 从源窗口（如 ImportBase）加载数据
 */
const loadDataFromSource = () => {
  if (!props.sourceStorageKey) return
  
  try {
    const sourceData = sessionStorage.getItem(props.sourceStorageKey)
    if (sourceData) {
      const parsed = JSON.parse(sourceData)
      
      // ImportGrid 存储的数据格式：
      // 1. { action: 'import', data: [...] } - ImportGrid 自动保存的格式
      // 2. { data: [...] } - 从 BaseGrid 传入的格式
      // 3. 直接是数组格式
      let sourceList: any[] = []
      if (Array.isArray(parsed)) {
        sourceList = parsed
      } else if (parsed && typeof parsed === 'object') {
        if (parsed.action === 'import' && Array.isArray(parsed.data)) {
          // 格式1：ImportGrid 自动保存的格式
          sourceList = parsed.data
        } else if (Array.isArray(parsed.data)) {
          // 格式2：对象格式，包含 data
          sourceList = parsed.data
        }
      }
      
      // 将源窗口的数据作为列数据显示
      if (sourceList.length > 0) {
        colDataList.value = sourceList.map(item => ({
          id: item.id,
          name_unique: item.name_unique || item.name_display || '',
          ...item // 保留原始数据
        }))
        
        if (prompInfoRef.value) {
          prompInfoRef.value.info(`已从上一个窗口加载 ${colDataList.value.length} 个列数据`)
        }
      } else {
        // 数据为空，提示用户
        if (prompInfoRef.value) {
          prompInfoRef.value.warn('上一个窗口没有数据')
        }
      }
    } else {
      // 没有找到数据
      if (prompInfoRef.value) {
        prompInfoRef.value.warn('未找到上一个窗口的数据，请先在 ImportBase 中添加数据')
      }
    }
  } catch (error) {
    if (prompInfoRef.value) {
      prompInfoRef.value.err('从上一个窗口加载数据失败')
    }
  }
}

/**
 * 从sessionStorage加载数据
 */
const loadDataFromStorage = () => {
  if (!props.storageKey) return
  
  try {
    const storageData = sessionStorage.getItem(props.storageKey)
    if (storageData) {
      const data = JSON.parse(storageData)
      
      // 加载行数据和列数据（保持向后兼容）
      if (data.rowDatas && Array.isArray(data.rowDatas)) {
        rowDataList.value = data.rowDatas
      } else if (data.dishes && Array.isArray(data.dishes)) {
        // 向后兼容：如果使用旧的 dishes 字段
        rowDataList.value = data.dishes
      }
      if (data.colDatas && Array.isArray(data.colDatas)) {
        colDataList.value = data.colDatas
      } else if (data.dishGroups && Array.isArray(data.dishGroups)) {
        // 向后兼容：如果使用旧的 dishGroups 字段
        colDataList.value = data.dishGroups
      }
      if (data.branchId !== undefined) {
        branchId.value = data.branchId
      }
      if (data.crossData) {
        crossData.value = data.crossData
      }
    }
  } catch (error) {
    // 加载数据失败，静默处理
  }
  
  // 如果props中有数据，优先使用props（保持向后兼容）
  if (props.rowDatas && props.rowDatas.length > 0) {
    rowDataList.value = props.rowDatas
  } else if (props.dishes && props.dishes.length > 0) {
    // 向后兼容：如果使用旧的 dishes 字段
    rowDataList.value = props.dishes
  }
  if (props.colDatas && props.colDatas.length > 0) {
    colDataList.value = props.colDatas
  } else if (props.dishGroups && props.dishGroups.length > 0) {
    // 向后兼容：如果使用旧的 dishGroups 字段
    colDataList.value = props.dishGroups
  }
}

/**
 * 保存数据到sessionStorage
 */
const saveDataToStorage = () => {
  if (!props.storageKey) return
  
  try {
    const data = {
      rowDatas: rowDataList.value,
      colDatas: colDataList.value,
      // 保持向后兼容
      dishes: rowDataList.value,
      dishGroups: colDataList.value,
      branchId: branchId.value,
      crossData: crossData.value
    }
    sessionStorage.setItem(props.storageKey, JSON.stringify(data))
  } catch (error) {
    // 保存数据失败，静默处理
  }
}

// ==================== 事件处理 ====================
/**
 * 处理单元格更新
 */
const handleCellUpdate = (rowIndex: number, columnIndex: number, value: number | null, dataConfigIndex?: number) => {
  const row = tableRows.value[rowIndex]
  const column = tableColumns.value[columnIndex]
  
  if (!row || !column) return
  
  const dishId = String(row.id)
  const dishGroupId = String(column.id)
  const configIndex = dataConfigIndex ?? currentDataConfigIndex.value
  
  // 如果有数据配置，使用多套数据存储
  if (props.dataConfigs && props.dataConfigs.length > 0) {
    // 初始化数据结构（保持向后兼容）
    if (!crossData.value[dataType.value][dishId]) {
      crossData.value[dataType.value][dishId] = {}
    }
    
    // 更新值（保持向后兼容）
    crossData.value[dataType.value][dishId][dishGroupId] = value
  } else {
    // 没有数据配置，使用旧的格式
    if (!crossData.value[dataType.value][dishId]) {
      crossData.value[dataType.value][dishId] = {}
    }
    crossData.value[dataType.value][dishId][dishGroupId] = value
  }
  
  // 保存到storage
  saveDataToStorage()
  
  // 触发事件
  emit('dataChanged', {
    rowId: row.id,
    colId: column.id,
    dataType: dataType.value,
    dataConfigIndex: configIndex,
    value,
    // 保持向后兼容
    dishId: row.id,
    dishGroupId: column.id
  })
}

/**
 * 处理行数据更新
 */
const handleRowsUpdate = (rows: TableCrossRow[]) => {
  // 更新交叉数据
  rows.forEach(row => {
    const rowId = String(row.id)
    colDataList.value.forEach(colData => {
      const colId = String(colData.id)
      const value = row[colId] ?? null
      
      if (!crossData.value[dataType.value][rowId]) {
        crossData.value[dataType.value][rowId] = {}
      }
      crossData.value[dataType.value][rowId][colId] = value
    })
  })
  
  saveDataToStorage()
}

/**
 * 处理列数据更新
 */
const handleColumnsUpdate = (columns: TableCrossColumn[]) => {
  // 列更新时，需要重新构建交叉数据
  colDataList.value = columns.map(col => {
    const existing = colDataList.value.find(c => c.id === col.id)
    return existing || { id: col.id, name_unique: col.name }
  })
  
  saveDataToStorage()
}

/**
 * 新增行数据
 */
const addRowDatas = (records: any[]) => {
  if (!records || records.length === 0) return
  
  // 过滤掉已存在的记录
  const newRecords = records.filter(record => {
    const recordId = record.id
    return !rowDataList.value.some(item => item.id === recordId)
  })
  
  if (newRecords.length > 0) {
    rowDataList.value.push(...newRecords)
    saveDataToStorage()
    if (prompInfoRef.value) {
      prompInfoRef.value.info(`已添加 ${newRecords.length} 条行数据`)
    }
  } else {
    if (prompInfoRef.value) {
      prompInfoRef.value.warn('所选记录已存在')
    }
  }
}

/**
 * 新增列数据
 */
const addColDatas = (records: any[]) => {
  if (!records || records.length === 0) return
  
  // 过滤掉已存在的记录
  const newRecords = records.filter(record => {
    const recordId = record.id
    return !colDataList.value.some(item => item.id === recordId)
  })
  
  if (newRecords.length > 0) {
    colDataList.value.push(...newRecords)
    saveDataToStorage()
    if (prompInfoRef.value) {
      prompInfoRef.value.info(`已添加 ${newRecords.length} 条列数据`)
    }
  } else {
    if (prompInfoRef.value) {
      prompInfoRef.value.warn('所选记录已存在')
    }
  }
}

/**
 * 保存数据
 */
const handleSave = async () => {
  if (prompInfoRef.value) {
    prompInfoRef.value.info('正在保存...')
  }
  
  // 保存到storage
  saveDataToStorage()
  
  // 构建保存数据
  const saveData = {
    branchId: branchId.value,
    rowDatas: rowDataList.value,
    colDatas: colDataList.value,
    crossData: crossData.value,
    // 保持向后兼容
    dishes: rowDataList.value,
    dishGroups: colDataList.value
  }
  
  // 如果配置了保存处理函数，调用它
  if (props.onSave) {
    try {
      await props.onSave(saveData)
      if (prompInfoRef.value) {
        prompInfoRef.value.info('保存成功')
      }
    } catch (error) {
      if (prompInfoRef.value) {
        prompInfoRef.value.err('保存失败')
      }
    }
  } else {
    // 触发保存事件
    emit('save', saveData)
    if (prompInfoRef.value) {
      prompInfoRef.value.info('保存成功')
    }
  }
}

// ==================== 监听 ====================
/** 监听数据类型切换，更新表格数据 */
watch(dataType, () => {
  // 数据类型切换时，表格会自动通过computed更新
  if (prompInfoRef.value) {
    prompInfoRef.value.info(`已切换到${dataType.value === 'use_dish' ? '使用菜品' : '配置加价'}`)
  }
})

/** 监听数据配置索引切换 */
watch(currentDataConfigIndex, (newIndex) => {
  if (prompInfoRef.value && props.dataConfigs && props.dataConfigs[newIndex]) {
    prompInfoRef.value.info(`已切换到${props.dataConfigs[newIndex].label}`)
  }
})

/** 初始化：如果有数据配置，默认选中第一个 */
watch(() => props.dataConfigs, (configs) => {
  if (configs && configs.length > 0 && currentDataConfigIndex.value >= configs.length) {
    currentDataConfigIndex.value = 0
  }
}, { immediate: true })

// ==================== 监听源窗口数据变化 ====================
/**
 * 使用 StorageEvent 监听 sessionStorage 变化（跨标签页）
 * 注意：同源页面的 sessionStorage 变化不会触发 StorageEvent
 * 所以这里使用 focus 事件作为补充
 */
const handleStorageChange = (event: StorageEvent) => {
  if (event.key === props.sourceStorageKey && event.newValue) {
    loadDataFromSource()
    saveDataToStorage()
  }
}

const handleWindowFocus = () => {
  // 窗口获得焦点时，重新加载源数据（确保数据是最新的）
  if (props.sourceStorageKey) {
    loadDataFromSource()
    saveDataToStorage()
  }
}

// ==================== 生命周期 ====================
onMounted(async () => {
  await loadBranchList()
  
  // 先加载源窗口数据（如果配置了）
  if (props.sourceStorageKey) {
    loadDataFromSource()
    
    // 监听 sessionStorage 变化（跨标签页）
    window.addEventListener('storage', handleStorageChange)
    // 监听窗口焦点变化（同标签页内切换回来时）
    window.addEventListener('focus', handleWindowFocus)
  }
  
  // 再加载本地存储的数据
  loadDataFromStorage()
  
  if (prompInfoRef.value) {
    prompInfoRef.value.info('就绪')
  }
})

// 组件卸载时清理
onBeforeUnmount(() => {
  if (props.sourceStorageKey) {
    window.removeEventListener('storage', handleStorageChange)
    window.removeEventListener('focus', handleWindowFocus)
  }
})

// ==================== 暴露方法 ====================
defineExpose({
  getData: () => ({
    branchId: branchId.value,
    rowDatas: rowDataList.value,
    colDatas: colDataList.value,
    crossData: crossData.value,
    // 保持向后兼容
    dishes: rowDataList.value,
    dishGroups: colDataList.value
  }),
  saveDataToStorage,
  addRowDatas,
  addColDatas,
  getRowDatas: () => [...rowDataList.value],
  getColDatas: () => [...colDataList.value]
})
</script>

<template>
  <div class="import-cross-container">
    <!-- 顶部工具栏 -->
    <div class="import-cross-toolbar">
      <div class="toolbar-left">
        <!-- 门店下拉选择 -->
        <ElSelect
          v-model="branchId"
          placeholder="请选择门店"
          style="width: 160px"
          clearable
          @change="saveDataToStorage"
        >
          <ElOption
            v-for="branch in branchOptions"
            :key="branch.id"
            :label="branch.name_unique"
            :value="branch.id"
          />
        </ElSelect>
        
        <!-- 数据切换组件：只有当数据配置数组存在且长度 > 1 时才显示 -->
        <ElRadioGroup 
          v-if="dataConfigs && dataConfigs.length > 1"
          :model-value="currentDataConfigIndex"
          @update:model-value="(val: number) => { currentDataConfigIndex = val }"
          class="data-type-switch"
        >
          <ElRadioButton
            v-for="(config, index) in dataConfigs"
            :key="index"
            :label="index"
          >{{ config.label }}</ElRadioButton>
        </ElRadioGroup>
      </div>
      
      <!-- PromptInfo组件 -->
      <div class="toolbar-info">
        <PromptInfo ref="prompInfoRef" />
      </div>
      
      <!-- 右侧按钮组 -->
      <div class="toolbar-right">
        <!-- 根据配置显示按钮 -->
        <template v-for="(btn, index) in buttonConfigs" :key="index">
          <ButtonPlus
            v-if="btn.show !== false"
            :stype="btn.stype"
            @click="handleButtonClick(btn)"
          >
            <template v-if="btn.label">{{ btn.label }}</template>
          </ButtonPlus>
        </template>
        <!-- 默认保存按钮（如果没有在配置中） -->
        <ButtonPlus
          v-if="!buttonConfigs.some(btn => btn.stype === 'save')"
          stype="save"
          @click="handleSave"
        />
      </div>
    </div>
    
    <!-- TableCross组件 -->
    <div class="table-wrapper">
      <TableCross
        ref="tableCrossRef"
        :rows="tableRows"
        :columns="tableColumns"
        :name-column-width="nameColumnWidth"
        :data-column-width="dataColumnWidth"
        :sum-column-width="sumColumnWidth"
        :data-configs="dataConfigs"
        :current-data-config-index="currentDataConfigIndex"
        @update:rows="handleRowsUpdate"
        @update:columns="handleColumnsUpdate"
        @cell-update="handleCellUpdate"
        @update:current-data-config-index="(val: number) => { currentDataConfigIndex = val }"
      />
    </div>
  </div>
</template>

<style lang="less" scoped>
.import-cross-container {
  padding: 0 !important;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.import-cross-toolbar {
  display: flex;
  align-items: center;
  margin: 0 0 10px 0;
  gap: 10px;
  flex-shrink: 0;
}

.toolbar-left {
  flex: 0 0 auto;
  display: flex;
  gap: 10px;
  align-items: center;
}

.toolbar-info {
  flex: 1;
  min-width: 0;
}

.toolbar-right {
  flex: 0 0 auto;
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}

.table-wrapper {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

// 确保在 ContentWrap 容器中正确显示
// 这些样式确保 ImportCross 能够填充整个 ContentWrap 容器的高度
// 与 ImportGrid 保持完全一致的样式
:deep(.content-wrap),
:deep(.content-wrap .el-card),
:deep(.content-wrap .el-card__body) {
  height: 100% !important;
  display: flex !important;
  flex-direction: column !important;
  padding: 0 !important;
  margin: 0 !important;
}

:deep(.content-wrap .el-card__body) {
  flex: 1 !important;
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
  padding: 0 !important;
  margin: 0 !important;
}
</style>

