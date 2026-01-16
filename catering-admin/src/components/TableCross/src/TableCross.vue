<!--
  TableCross - 交叉表格组件
  
  功能特性：
  - 行表示一个对象，第1列显示名称
  - 列表示一个对象，第1行显示名称
  - 交叉格配置整数数字（>0），编辑时只有数字输入
  - 最后一行是汇总行，对列数据汇总，第1列显示"选择"按钮用于新增行
  - 最后一列是汇总列，对行数据汇总，第1行显示"选择"按钮用于新增列
  - 表格和鼠标样式参考Excel，可参考组件TableGrid
  - 点击行的第1列（对象名称列），退出编辑/选择，选中该行
  - 点击列的第1行（对象名称行），退出编辑/选择，选中该列
  - 方向键、tab、enter响应参考TableGrid，但超出边界后不会自动增加行列
-->
<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, nextTick, watch } from 'vue'
import { ElTable, ElTableColumn, ElInputNumber, ElInput, ElCheckbox, ElRadioGroup, ElRadio, ElIcon, ElLink } from 'element-plus'
import { Rank } from '@element-plus/icons-vue'

/**
 * 行对象接口
 */
export interface TableCrossRow {
  /** 行ID（唯一标识） */
  id: string | number
  /** 行名称（显示在第1列） */
  name: string
  /** 交叉数据，key为列ID，value为数字 */
  [key: string]: any
}

/**
 * 列对象接口
 */
export interface TableCrossColumn {
  /** 列ID（唯一标识） */
  id: string | number
  /** 列名称（显示在第1行） */
  name: string
}

/**
 * 数据配置项接口
 */
export interface TableCrossDataConfig {
  /** 配置标签（显示在单选按钮上） */
  label: string
  /** 数据类型：'int' | 'decimal(12,2)' | 'string' 等 */
  type: string
  /** 显示格式：用于格式化显示值 */
  format?: string
  /** 是否为主配置（只有第一个元素有效）：当为true时，如果第一套数据配置了值，其他数据才可以配置 */
  primary?: boolean
  /** 编辑组件类型：'NumberInput' | 'Input' | 'Checkbox' | 'RadioBox'，默认根据type自动推断 */
  component?: 'NumberInput' | 'Input' | 'Checkbox' | 'RadioBox'
  /** RadioBox选项（当component为'RadioBox'时必填） */
  radioOptions?: Array<{ label: string; value: any }>
}

/**
 * 数据配置数组类型
 */
export type TableCrossDataConfigs = TableCrossDataConfig[]

/**
 * Props 接口
 */
export interface TableCrossProps {
  /** 行数据数组 */
  rows: TableCrossRow[]
  /** 列数据数组 */
  columns: TableCrossColumn[]
  /** 当前选中的行索引 */
  currentRowIndex?: number | null
  /** 当前选中的列索引 */
  currentColumnIndex?: number | null
  /** 名称列宽度（第一列） */
  nameColumnWidth?: number
  /** 数据列宽度 */
  dataColumnWidth?: number
  /** 汇总列宽度 */
  sumColumnWidth?: number
  /** 数据配置数组（支持多套数据配置） */
  dataConfigs?: TableCrossDataConfigs
  /** 当前选中的数据配置索引（从0开始） */
  currentDataConfigIndex?: number
  /** 是否允许删除行（当为 true 时，在行小计列之后添加操作列） */
  allowDeleteRow?: boolean
  /** 是否允许删除列（当为 true 时，在列小计行之后添加操作行） */
  allowDeleteColumn?: boolean
}

/**
 * Emits 接口
 */
export interface TableCrossEmits {
  (e: 'update:rows', value: TableCrossRow[]): void
  (e: 'update:columns', value: TableCrossColumn[]): void
  (e: 'update:currentRowIndex', value: number | null): void
  (e: 'update:currentColumnIndex', value: number | null): void
  (e: 'update:currentDataConfigIndex', value: number): void
  (e: 'cell-update', rowIndex: number, columnIndex: number, value: number | null, dataConfigIndex?: number): void
  (e: 'row-add', payload: { row: TableCrossRow; insertIndex?: number }): void
  (e: 'column-add', payload: { column: TableCrossColumn; insertIndex?: number }): void
  (e: 'row-select', rowIndex: number): void
  (e: 'column-select', columnIndex: number): void
  (e: 'row-order-change', newRows: TableCrossRow[]): void
  (e: 'column-order-change', newColumns: TableCrossColumn[]): void
  (e: 'row-delete', rowIndex: number): void
  (e: 'column-delete', columnIndex: number): void
}

const props = withDefaults(defineProps<TableCrossProps>(), {
  currentRowIndex: null,
  currentColumnIndex: null,
  nameColumnWidth: 200,
  dataColumnWidth: 160,
  sumColumnWidth: 120,
  dataConfigs: () => [],
  currentDataConfigIndex: 0,
  allowDeleteRow: false,
  allowDeleteColumn: false
})

const emit = defineEmits<TableCrossEmits>()

// 表格引用
const tableRef = ref<InstanceType<typeof ElTable>>()

// ==================== 编辑状态管理 ====================
/** 当前正在编辑的单元格 */
const editingCell = ref<{ rowIndex: number; columnIndex: number } | null>(null)

/** 当前行索引（当前聚焦的行） */
const currentRowIndex = ref<number | null>(props.currentRowIndex ?? null)

/** 当前列索引（当前聚焦的列） */
const currentColumnIndex = ref<number | null>(props.currentColumnIndex ?? null)

/** 选中的行索引 */
const selectedRowIndex = ref<number | null>(null)

/** 选中的列索引 */
const selectedColumnIndex = ref<number | null>(null)

// ==================== 拖拽状态管理 ====================
/** 正在拖拽的列索引 */
const draggingColumnIndex = ref<number | null>(null)

/** 正在拖拽的行索引 */
const draggingRowIndex = ref<number | null>(null)

/**
 * 处理列拖拽开始
 */
const handleColumnDragStart = (event: DragEvent, columnIndex: number) => {
  draggingColumnIndex.value = columnIndex
  if (event.dataTransfer) {
    event.dataTransfer.effectAllowed = 'move'
    event.dataTransfer.setData('text/plain', String(columnIndex))
  }
  // 添加拖拽样式
  if (event.target) {
    (event.target as HTMLElement).classList.add('dragging')
  }
}

/**
 * 处理列拖拽结束
 */
const handleColumnDragEnd = (event: DragEvent) => {
  draggingColumnIndex.value = null
  if (event.target) {
    (event.target as HTMLElement).classList.remove('dragging')
  }
  // 移除所有拖拽相关的样式
  const tableEl = tableRef.value?.$el as HTMLElement
  if (tableEl) {
    tableEl.querySelectorAll('.drag-over').forEach(el => {
      el.classList.remove('drag-over')
    })
  }
}

/**
 * 处理列拖拽进入
 */
const handleColumnDragEnter = (event: DragEvent, targetColumnIndex: number) => {
  event.preventDefault()
  if (draggingColumnIndex.value === null || draggingColumnIndex.value === targetColumnIndex) {
    return
  }
  if (event.target) {
    (event.target as HTMLElement).classList.add('drag-over')
  }
}

/**
 * 处理列拖拽离开
 */
const handleColumnDragLeave = (event: DragEvent) => {
  if (event.target) {
    (event.target as HTMLElement).classList.remove('drag-over')
  }
}

/**
 * 处理列拖拽放置
 */
const handleColumnDrop = (event: DragEvent, targetColumnIndex: number) => {
  event.preventDefault()
  event.stopPropagation()
  
  if (draggingColumnIndex.value === null || draggingColumnIndex.value === targetColumnIndex) {
    return
  }
  
  if (event.target) {
    (event.target as HTMLElement).classList.remove('drag-over')
  }
  
  // 重新排序列
  const newColumns = [...props.columns]
  const draggedColumn = newColumns[draggingColumnIndex.value]
  newColumns.splice(draggingColumnIndex.value, 1)
  newColumns.splice(targetColumnIndex, 0, draggedColumn)
  
  // 更新行的数据，重新映射列ID
  const newRows = props.rows.map(row => {
    // 保持行的列数据顺序与新的列顺序一致
    const reorderedRow: TableCrossRow = {
      id: row.id,
      name: row.name
    }
    newColumns.forEach(column => {
      reorderedRow[column.id] = row[column.id] ?? null
    })
    return reorderedRow
  })
  
  emit('update:columns', newColumns)
  emit('update:rows', newRows)
  emit('column-order-change', newColumns)
  
  draggingColumnIndex.value = null
}

/**
 * 处理行拖拽开始
 */
const handleRowDragStart = (event: DragEvent, rowIndex: number) => {
  // 检查是否是汇总行或操作行，不允许拖拽
  const row = tableData.value[rowIndex]
  if (row && (row.__row_type__ === 'sum' || row.__row_type__ === 'action')) {
    event.preventDefault()
    return
  }
  
  draggingRowIndex.value = rowIndex
  if (event.dataTransfer) {
    event.dataTransfer.effectAllowed = 'move'
    event.dataTransfer.setData('text/plain', String(rowIndex))
  }
  // 添加拖拽样式
  if (event.target) {
    (event.target as HTMLElement).classList.add('dragging')
  }
}

/**
 * 处理行拖拽结束
 */
const handleRowDragEnd = (event: DragEvent) => {
  draggingRowIndex.value = null
  if (event.target) {
    (event.target as HTMLElement).classList.remove('dragging')
  }
  // 移除所有拖拽相关的样式
  const tableEl = tableRef.value?.$el as HTMLElement
  if (tableEl) {
    tableEl.querySelectorAll('.drag-over').forEach(el => {
      el.classList.remove('drag-over')
    })
  }
}

/**
 * 处理行拖拽进入
 */
const handleRowDragEnter = (event: DragEvent, targetRowIndex: number) => {
  event.preventDefault()
  if (draggingRowIndex.value === null || draggingRowIndex.value === targetRowIndex) {
    return
  }
  
  // 检查目标行是否是汇总行或操作行，不允许拖拽到这些行
  const targetRow = tableData.value[targetRowIndex]
  if (targetRow && (targetRow.__row_type__ === 'sum' || targetRow.__row_type__ === 'action')) {
    return
  }
  
  if (event.target) {
    (event.target as HTMLElement).classList.add('drag-over')
  }
}

/**
 * 处理行拖拽离开
 */
const handleRowDragLeave = (event: DragEvent) => {
  if (event.target) {
    (event.target as HTMLElement).classList.remove('drag-over')
  }
}

/**
 * 处理行拖拽放置
 */
const handleRowDrop = (event: DragEvent, targetRowIndex: number) => {
  event.preventDefault()
  event.stopPropagation()
  
  if (draggingRowIndex.value === null || draggingRowIndex.value === targetRowIndex) {
    return
  }
  
  // 检查拖拽的行和目标行是否是汇总行或操作行
  const draggedRow = tableData.value[draggingRowIndex.value]
  const targetRow = tableData.value[targetRowIndex]
  
  if (!draggedRow || !targetRow) {
    return
  }
  
  // 汇总行和操作行不允许拖拽
  if (draggedRow.__row_type__ === 'sum' || draggedRow.__row_type__ === 'action') {
    return
  }
  
  // 不能拖拽到汇总行或操作行的位置
  if (targetRow.__row_type__ === 'sum' || targetRow.__row_type__ === 'action') {
    return
  }
  
  // 将 tableData 索引转换为 props.rows 索引
  // 因为 tableData = props.rows + 汇总行 + 操作行
  // 所以如果索引 >= props.rows.length，说明是汇总行或操作行
  const draggedDataRowIndex = draggingRowIndex.value
  const targetDataRowIndex = targetRowIndex
  
  if (draggedDataRowIndex < 0 || draggedDataRowIndex >= props.rows.length) {
    return
  }
  if (targetDataRowIndex < 0 || targetDataRowIndex >= props.rows.length) {
    return
  }
  
  if (event.target) {
    (event.target as HTMLElement).classList.remove('drag-over')
  }
  
  // 重新排序行
  const newRows = [...props.rows]
  const draggedRowData = newRows[draggedDataRowIndex]
  newRows.splice(draggedDataRowIndex, 1)
  newRows.splice(targetDataRowIndex, 0, draggedRowData)
  
  emit('update:rows', newRows)
  emit('row-order-change', newRows)
  
  // 更新当前行索引（使用数据行索引）
  if (currentRowIndex.value === draggedDataRowIndex) {
    currentRowIndex.value = targetDataRowIndex
    emit('update:currentRowIndex', targetDataRowIndex)
  } else if (currentRowIndex.value !== null) {
    // 调整当前行索引
    if (draggedDataRowIndex < currentRowIndex.value && targetDataRowIndex >= currentRowIndex.value) {
      currentRowIndex.value--
      emit('update:currentRowIndex', currentRowIndex.value)
    } else if (draggedDataRowIndex > currentRowIndex.value && targetDataRowIndex <= currentRowIndex.value) {
      currentRowIndex.value++
      emit('update:currentRowIndex', currentRowIndex.value)
    }
  }
  
  draggingRowIndex.value = null
}

// 监听 props 的变化
watch(
  () => props.currentRowIndex,
  (newVal) => {
    if (newVal !== currentRowIndex.value) {
      currentRowIndex.value = newVal
    }
  },
  { immediate: true }
)

watch(
  () => props.currentColumnIndex,
  (newVal) => {
    if (newVal !== currentColumnIndex.value) {
      currentColumnIndex.value = newVal
    }
  },
  { immediate: true }
)


// ==================== 输入组件引用管理 ====================
/** 输入组件引用映射 */
const inputRefsMap = new Map<string, any>()

/**
 * 设置输入组件引用
 */
const setInputRef = (rowIndex: number, columnIndex: number, el: any) => {
  const refKey = `${rowIndex}-${columnIndex}`
  if (el) {
    inputRefsMap.set(refKey, el)
  } else {
    inputRefsMap.delete(refKey)
  }
}

// ==================== 工具函数 ====================
/**
 * 延迟执行函数
 */
const delayExecute = (callback: () => void, delay: number = 10) => {
  setTimeout(callback, delay)
}

/**
 * 验证数据类型
 */
const validateDataType = (value: any, type: string): boolean => {
  if (value === null || value === undefined || value === '') {
    return true // 空值允许
  }
  
  // 解析类型字符串，例如 'decimal(12,2)' -> { type: 'decimal', precision: 12, scale: 2 }
  const typeMatch = type.match(/^(\w+)(?:\((\d+)(?:,(\d+))?\))?$/)
  if (!typeMatch) return false
  
  const baseType = typeMatch[1].toLowerCase()
  const numValue = Number(value)
  
  switch (baseType) {
    case 'int':
    case 'integer':
      return Number.isInteger(numValue) && !isNaN(numValue)
    case 'decimal':
    case 'float':
    case 'double':
    case 'numeric':
      return !isNaN(numValue) && isFinite(numValue)
    case 'string':
    case 'text':
      return true // 字符串类型接受任何值
    default:
      return !isNaN(numValue) && isFinite(numValue) // 默认按数字处理
  }
}

/**
 * 格式化显示值
 */
const formatValue = (value: any, format?: string): string => {
  if (value === null || value === undefined || value === '') {
    return ''
  }
  
  if (!format) {
    return String(value)
  }
  
  const numValue = Number(value)
  if (isNaN(numValue)) {
    return String(value)
  }
  
  // 处理常见的格式
  switch (format.toLowerCase()) {
    case 'decimal':
    case 'decimal(12,2)':
      return numValue.toFixed(2)
    case 'decimal(10,2)':
      return numValue.toFixed(2)
    case 'int':
    case 'integer':
      return Math.floor(numValue).toString()
    default:
      // 可以扩展更多格式，如日期、时间等
      return String(value)
  }
}

/**
 * 获取单元格的多套数据存储key
 */
const getCellDataKey = (columnId: string | number, dataConfigIndex: number): string => {
  return `__data_${dataConfigIndex}_${columnId}`
}

/**
 * 检查单元格是否可编辑（考虑primary依赖）
 */
const isCellEditable = (rowIndex: number, columnIndex: number, dataConfigIndex: number): boolean => {
  // 检查是否是汇总行或操作行
  const tableRow = tableData.value[rowIndex]
  if (tableRow && (tableRow.__row_type__ === 'sum' || tableRow.__row_type__ === 'action')) {
    return false
  }
  
  // 注意：rowIndex 是 props.rows 的索引，rowIndex=0 对应第一行数据单元（标题行在表头，不在 props.rows 中）
  // columnIndex 是 props.columns 的索引，columnIndex=0 对应第一列数据单元（名称列不在 props.columns 中）
  // 所以第一行数据单元（rowIndex=0）和第一列数据单元（columnIndex=0）都应该可编辑
  
  // 如果没有数据配置，使用默认逻辑
  if (!props.dataConfigs || props.dataConfigs.length === 0) {
    return true
  }
  
  // 如果是第一套数据（索引0），总是可编辑
  if (dataConfigIndex === 0) {
    return true
  }
  
  // 检查第一套数据是否配置了primary
  const firstConfig = props.dataConfigs[0]
  if (!firstConfig || !firstConfig.primary) {
    // primary为false或未设置，多套数据独立
    return true
  }
  
  // primary为true，需要检查第一套数据是否有值
  // 注意：这里需要使用数据行的索引，而不是 tableData 的索引
  const dataRowIndex = rowIndex >= props.rows.length ? -1 : rowIndex
  if (dataRowIndex < 0 || dataRowIndex >= props.rows.length) {
    return false
  }
  
  const column = props.columns[columnIndex]
  if (!column) {
    return false
  }
  
  // 获取第一套数据的值（使用专用函数避免循环调用）
  const firstValue = getFirstDataValue(dataRowIndex, columnIndex)
  
  // 如果第一套数据有值，其他数据才可以编辑
  return firstValue !== null && firstValue !== undefined && firstValue !== ''
}

/**
 * 获取单元格的值（支持多套数据）
 * 注意：此函数不检查是否可编辑，只负责获取原始值
 * 可编辑性检查应该在显示层面处理
 */
const getCellValue = (rowIndex: number, columnIndex: number, dataConfigIndex?: number): any => {
  if (rowIndex < 0 || rowIndex >= props.rows.length) return null
  if (columnIndex < 0 || columnIndex >= props.columns.length) return null
  
  const row = props.rows[rowIndex]
  const column = props.columns[columnIndex]
  
  // 如果有多套数据配置，使用对应的数据key
  const configIndex = dataConfigIndex ?? props.currentDataConfigIndex ?? 0
  
  let value: any
  
  if (props.dataConfigs && props.dataConfigs.length > 0) {
    const dataKey = getCellDataKey(column.id, configIndex)
    value = row[dataKey]
    // 如果多套数据中没有找到，尝试使用旧的格式（向后兼容）
    if (value === undefined) {
      value = row[column.id]
    }
  } else {
    // 没有数据配置，使用旧的格式
    value = row[column.id]
  }
  
  if (value === null || value === undefined || value === '') {
    return null
  }
  
  // 根据组件类型返回不同的值
  const config = props.dataConfigs?.[configIndex]
  const componentType = config?.component
  
  if (componentType === 'Checkbox' || componentType === 'RadioBox') {
    // Checkbox和RadioBox返回原始值
    return value
  }
  
  // NumberInput和Input返回数字或字符串
  const numValue = Number(value)
  return isNaN(numValue) ? value : numValue
}

/**
 * 获取第一套数据的值（用于primary依赖检查，避免循环调用）
 */
const getFirstDataValue = (rowIndex: number, columnIndex: number): any => {
  if (rowIndex < 0 || rowIndex >= props.rows.length) return null
  if (columnIndex < 0 || columnIndex >= props.columns.length) return null
  
  const row = props.rows[rowIndex]
  const column = props.columns[columnIndex]
  
  // 直接获取第一套数据的值，不使用 getCellValue 避免循环
  if (props.dataConfigs && props.dataConfigs.length > 0) {
    const dataKey = getCellDataKey(column.id, 0)
    const value = row[dataKey]
    if (value !== undefined) {
      return value
    }
    // 如果多套数据中没有找到，尝试使用旧的格式（向后兼容）
    return row[column.id] ?? null
  } else {
    // 没有数据配置，使用旧的格式
    return row[column.id] ?? null
  }
}

/**
 * 获取单元格的格式化显示值
 */
const getCellDisplayValue = (rowIndex: number, columnIndex: number, dataConfigIndex?: number): string => {
  const configIndex = dataConfigIndex ?? props.currentDataConfigIndex ?? 0
  
  // 检查是否可编辑（考虑primary依赖），如果不可编辑，显示空
  if (!isCellEditable(rowIndex, columnIndex, configIndex)) {
    return ''
  }
  
  const value = getCellValue(rowIndex, columnIndex, dataConfigIndex)
  if (value === null) return ''
  
  const config = props.dataConfigs?.[configIndex]
  const componentType = config?.component
  
  // Checkbox显示为"是"/"否"
  if (componentType === 'Checkbox') {
    return value ? '是' : '否'
  }
  
  // RadioBox显示为选项的label
  if (componentType === 'RadioBox' && config?.radioOptions) {
    const option = config.radioOptions.find(opt => opt.value === value)
    return option ? option.label : String(value)
  }
  
  const format = config?.format
  return formatValue(value, format)
}

/**
 * 获取单元格的值（用于输入框）
 */
const getCellValueForInput = (rowIndex: number, columnIndex: number, dataConfigIndex?: number): any => {
  const configIndex = dataConfigIndex ?? props.currentDataConfigIndex ?? 0
  
  // 检查是否可编辑（考虑primary依赖），如果不可编辑，返回空值
  if (!isCellEditable(rowIndex, columnIndex, configIndex)) {
    const config = props.dataConfigs?.[configIndex]
    const componentType = config?.component
    if (componentType === 'NumberInput' || (!componentType && config?.type && /^(int|integer|decimal|float|double|numeric)/i.test(config.type))) {
      return undefined
    } else if (componentType === 'Input') {
      return ''
    } else if (componentType === 'Checkbox') {
      return false
    } else {
      return undefined
    }
  }
  
  const value = getCellValue(rowIndex, columnIndex, dataConfigIndex)
  const config = props.dataConfigs?.[configIndex]
  const componentType = config?.component
  
  // NumberInput返回number | undefined
  if (componentType === 'NumberInput' || (!componentType && config?.type && /^(int|integer|decimal|float|double|numeric)/i.test(config.type))) {
    return value === null ? undefined : (typeof value === 'number' ? value : Number(value))
  }
  
  // 其他类型返回原始值
  return value === null ? (componentType === 'Input' ? '' : undefined) : value
}

/**
 * 更新单元格的值（支持多套数据）
 */
const updateCellValue = (rowIndex: number, columnIndex: number, value: any, dataConfigIndex?: number) => {
  if (rowIndex < 0 || rowIndex >= props.rows.length) return
  if (columnIndex < 0 || columnIndex >= props.columns.length) return
  
  const configIndex = dataConfigIndex ?? props.currentDataConfigIndex ?? 0
  const config = props.dataConfigs?.[configIndex]
  
  // 验证数据类型（对于数字类型）
  if (value !== null && value !== undefined && value !== '' && config?.type) {
    const componentType = config.component
    // 只有NumberInput需要验证数字类型
    if (componentType === 'NumberInput' || (!componentType && config.type && /^(int|integer|decimal|float|double|numeric)/i.test(config.type))) {
      if (!validateDataType(value, config.type)) {
        return // 数据类型不匹配，不更新
      }
    }
  }
  
  const column = props.columns[columnIndex]
  const newRows = props.rows.map((row, idx) => {
    if (idx === rowIndex) {
      const updatedRow = { ...row }
      
      // 如果有多套数据配置，使用对应的数据key
      if (props.dataConfigs && props.dataConfigs.length > 0) {
        const dataKey = getCellDataKey(column.id, configIndex)
        updatedRow[dataKey] = value
      } else {
        // 没有数据配置，使用旧的格式（向后兼容）
        updatedRow[column.id] = value
      }
      
      return updatedRow
    }
    return row
  })
  
  emit('update:rows', newRows)
  emit('cell-update', rowIndex, columnIndex, value, configIndex)
}

/**
 * 计算汇总行的值（对列的数据汇总，支持多套数据）
 */
const getRowSum = (rowIndex: number): number => {
  // 如果 rowIndex 超出数据行范围，返回 0
  // 注意：rowIndex 是 tableData 中的索引，需要转换为 props.rows 中的索引
  if (rowIndex < 0) return 0
  
  // 检查是否是汇总行或操作行
  const row = tableData.value[rowIndex]
  if (row && (row.__row_type__ === 'sum' || row.__row_type__ === 'action')) {
    return 0
  }
  
  // 转换为数据行索引
  const dataRowIndex = rowIndex
  if (dataRowIndex < 0 || dataRowIndex >= props.rows.length) return 0

  const configIndex = props.currentDataConfigIndex ?? 0
  let sum = 0
  props.columns.forEach((_column, colIdx) => {
    const value = getCellValue(dataRowIndex, colIdx, configIndex)
    if (value !== null && value > 0) {
      sum += value
    }
  })
  return sum
}

/**
 * 计算汇总列的值（对行的数据汇总，支持多套数据）
 * 注意：只计算数据行，不包括汇总行和操作行
 */
const getColumnSum = (columnIndex: number): number => {
  if (columnIndex < 0 || columnIndex >= props.columns.length) return 0
  
  const configIndex = props.currentDataConfigIndex ?? 0
  let sum = 0
  // 只遍历数据行（props.rows），不包括汇总行和操作行
  props.rows.forEach((_row, rowIdx) => {
    const value = getCellValue(rowIdx, columnIndex, configIndex)
    if (value !== null && value > 0) {
      sum += value
    }
  })
  return sum
}

/**
 * 计算表格数据（包含汇总行和操作行）
 */
const tableData = computed(() => {
  const data = [...props.rows]
  
  // 添加汇总行（列小计）
  const sumRow: TableCrossRow = {
    id: '__sum_row__',
    name: '列小计',
    __row_type__: 'sum'
  }
  
  // 为汇总行添加每列的小计值
  props.columns.forEach((column, colIdx) => {
    sumRow[String(column.id)] = getColumnSum(colIdx)
  })
  
  // 添加汇总列的汇总值（行小计的汇总）
  sumRow['__sum__'] = null
  
  // 如果允许删除行，添加操作列
  if (props.allowDeleteRow) {
    sumRow['__action_column__'] = null
  }
  
  data.push(sumRow)
  
  // 如果允许删除列，添加操作行
  if (props.allowDeleteColumn) {
    const actionRow: TableCrossRow = {
      id: '__action_row__',
      name: '操作',
      __row_type__: 'action'
    }
    
    // 为操作行添加每列的删除按钮标记
    props.columns.forEach((column) => {
      actionRow[String(column.id)] = '__delete_column__'
    })
    
    // 汇总列和操作列不显示内容
    actionRow['__sum__'] = null
    if (props.allowDeleteRow) {
      actionRow['__action_column__'] = null
    }
    
    data.push(actionRow)
  }
  
  return data
})

/**
 * 获取行的 CSS 类名
 */
const getRowClassName = ({ row }: { row: TableCrossRow; rowIndex: number }): string => {
  if (row.__row_type__ === 'sum') {
    return 'sum-row-type'
  }
  if (row.__row_type__ === 'action') {
    return 'action-row-type'
  }
  return ''
}

// 为了在模板中使用，需要暴露columns
const columns = computed(() => props.columns)

// 当前数据配置索引（用于模板）
const currentDataConfigIndex = computed(() => props.currentDataConfigIndex ?? 0)

// 数据配置（用于模板）
const dataConfigs = computed(() => props.dataConfigs ?? [])

// ==================== 填充列计算 ====================
/** 表格容器宽度 */
const tableWidth = ref<number>(0)

/** 计算是否需要填充列（只需要1列，充满剩余宽度） */
const needFillColumn = computed(() => {
  if (tableWidth.value <= 0) return false
  
  // 计算当前列的总宽度（包括边框等）
  // 名称列 + 数据列 + 汇总列 + 操作列（如果存在）
  let currentWidth = props.nameColumnWidth + (columns.value.length * props.dataColumnWidth) + props.sumColumnWidth
  
  // 如果允许删除行，添加操作列宽度（100px）
  if (props.allowDeleteRow) {
    currentWidth += 100
  }
  
  // 考虑边框宽度：每列之间都有边框，边框宽度约为 1px
  // 列数 = 名称列(1) + 数据列(columns.length) + 汇总列(1) + 操作列(0或1) = 2 + columns.length + (allowDeleteRow ? 1 : 0)
  const columnCount = 2 + columns.value.length + (props.allowDeleteRow ? 1 : 0)
  const borderWidth = columnCount * 1 // 每列左右各0.5px边框，约等于每列1px
  
  const totalWidth = currentWidth + borderWidth
  
  // 留出安全边距（10px），确保填充列不会导致滚动
  const safeMargin = 10
  
  // 如果当前宽度 + 安全边距已经大于等于表格宽度，不需要填充
  if (totalWidth + safeMargin >= tableWidth.value) return false
  
  // 计算填充列的最小宽度要求（至少5px才显示）
  const minFillWidth = 5
  const remainingWidth = tableWidth.value - totalWidth - safeMargin - 1 // 1px 是填充列本身的边框
  
  // 如果剩余宽度小于最小要求，不显示填充列
  if (remainingWidth < minFillWidth) return false
  
  // 只需要1列填充列，让它充满剩余宽度
  return true
})

/** 计算填充列的剩余宽度 */
const fillColumnWidth = computed(() => {
  if (!needFillColumn.value) return 0
  
  // 计算当前列的总宽度（不包括填充列）
  let currentWidth = props.nameColumnWidth + (columns.value.length * props.dataColumnWidth) + props.sumColumnWidth
  
  // 如果允许删除行，添加操作列宽度（100px）
  if (props.allowDeleteRow) {
    currentWidth += 100
  }
  
  // 考虑边框宽度（不包括填充列的边框）
  // 列数 = 名称列(1) + 数据列(columns.length) + 汇总列(1) + 操作列(0或1)
  const columnCount = 2 + columns.value.length + (props.allowDeleteRow ? 1 : 0)
  // Element Plus 表格的边框：每列之间1px边框
  const borderWidth = columnCount * 1
  
  const totalWidthWithoutFill = currentWidth + borderWidth
  
  // 计算剩余宽度
  // 填充列本身也会增加一列，所以需要考虑它的边框（+1px）
  const remainingWidth = tableWidth.value - totalWidthWithoutFill - 1 // 1px 是填充列本身的边框
  
  // 确保填充列宽度不会导致横向滚动
  // 如果剩余宽度小于等于0，返回0（不应该发生，因为 needFillColumn 已经检查过了）
  // 但为了安全，还是做这个检查
  if (remainingWidth <= 0) {
    return 0
  }
  
  // 返回剩余宽度，但不要太大（避免计算误差导致滚动）
  // 留出 10px 的安全边距，确保不会出现横向滚动
  const finalWidth = Math.max(0, remainingWidth - 10)
  
  // 如果计算出的宽度太小（小于5px），不显示填充列，避免显示一个很窄的列
  if (finalWidth < 5) {
    return 0
  }
  
  return finalWidth
})

/** 更新表格宽度 */
const updateTableWidth = () => {
  nextTick(() => {
    const tableEl = tableRef.value?.$el as HTMLElement
    if (tableEl) {
      // 获取表格容器的实际可见宽度（不包括滚动条）
      // 使用 clientWidth 而不是 offsetWidth，因为 clientWidth 不包括滚动条宽度
      let width = tableEl.clientWidth || 0
      
      // 如果表格有父容器，使用父容器的宽度（更准确）
      const parentEl = tableEl.parentElement
      if (parentEl) {
        const parentWidth = parentEl.clientWidth || 0
        if (parentWidth > 0) {
          // 使用父容器的宽度，但要考虑表格的 padding 和 margin
          const computedStyle = window.getComputedStyle(tableEl)
          const paddingLeft = parseFloat(computedStyle.paddingLeft) || 0
          const paddingRight = parseFloat(computedStyle.paddingRight) || 0
          const marginLeft = parseFloat(computedStyle.marginLeft) || 0
          const marginRight = parseFloat(computedStyle.marginRight) || 0
          
          const availableWidth = parentWidth - paddingLeft - paddingRight - marginLeft - marginRight
          if (availableWidth > 0) {
            width = availableWidth
          }
        }
      }
      
      // 如果宽度发生变化，更新
      if (width > 0 && width !== tableWidth.value) {
        tableWidth.value = width
      }
    }
  })
}

// ==================== 编辑相关函数 ====================
/**
 * 判断单元格是否正在编辑
 */
const isEditing = (rowIndex: number, columnIndex: number): boolean => {
  return editingCell.value !== null &&
         editingCell.value.rowIndex === rowIndex &&
         editingCell.value.columnIndex === columnIndex
}

/**
 * 进入编辑（接口函数）
 */
const startEdit = (rowIndex: number, columnIndex: number): [number, string] => {
  // 参数校验
  if (rowIndex < 0 || rowIndex >= props.rows.length) {
    return [-1, `行号${rowIndex}无效`]
  }
  
  if (columnIndex < 0 || columnIndex >= props.columns.length) {
    return [-1, `列号${columnIndex}无效`]
  }
  
  // 如果已经在编辑这个单元格，不做任何操作
  if (isEditing(rowIndex, columnIndex)) {
    return [1, '就绪']
  }
  
  editingCell.value = { rowIndex, columnIndex }
  
  // 等待 DOM 更新后聚焦输入框
  nextTick(() => {
    nextTick(() => {
      requestAnimationFrame(() => {
        setTimeout(() => {
          const refKey = `${rowIndex}-${columnIndex}`
          const componentRef = inputRefsMap.get(refKey)
          if (componentRef) {
            if (typeof componentRef.focus === 'function') {
              componentRef.focus()
            } else if (componentRef.input) {
              const actualInput = componentRef.input as HTMLInputElement
              if (actualInput) {
                actualInput.focus()
                actualInput.select()
              }
            }
          }
        })
      })
    })
  })
  
  return [1, '就绪']
}

/**
 * 结束编辑（内部函数）
 */
const endEdit = () => {
  editingCell.value = null
}

/**
 * 退出编辑（接口函数）
 */
const exitEdit = (rowIndex: number, columnIndex: number): [number, string] => {
  if (!editingCell.value) {
    return [1, '就绪']
  }
  
  const { rowIndex: currentRow, columnIndex: currentCol } = editingCell.value
  if (currentRow !== rowIndex || currentCol !== columnIndex) {
    return [-1, '目标单元格与编辑单元格不一致']
  }
  
  endEdit()
  
  // 选中当前单元格
  nextTick(() => {
    const tableEl = tableRef.value?.$el as HTMLElement
    if (!tableEl) return
    
    const cellElement = tableEl.querySelector(
      `.el-table__body tbody tr:nth-child(${rowIndex + 1}) .el-table__cell:nth-child(${columnIndex + 2})`
    ) as HTMLElement
    if (cellElement) {
      cellElement.classList.remove('editing-cell')
      cellElement.classList.add('selected-cell')
      
      currentRowIndex.value = rowIndex
      emit('update:currentRowIndex', rowIndex)
    }
  })
  
  return [1, '就绪']
}

/**
 * 退出单元格选中（接口函数）
 */
const deselectCell = (): [number, string] => {
  if (editingCell.value) {
    endEdit()
  }
  
  // 清除DOM中的选中类（参考TableGrid的实现）
  const tableEl = tableRef.value?.$el as HTMLElement
  if (tableEl) {
    tableEl.querySelectorAll('.el-table__cell.selected-cell').forEach(el => {
      el.classList.remove('selected-cell')
    })
  }
  
  // 清除响应式状态
  currentRowIndex.value = null
  currentColumnIndex.value = null
  emit('update:currentRowIndex', null)
  emit('update:currentColumnIndex', null)
  
  return [1, '就绪']
}

/**
 * 选中单元格（接口函数）
 * 所有交叉的数据单元格都可以选中，包括第一行数据单元（rowIndex=0）和第一列数据单元（columnIndex=0）
 * 排除汇总行、操作行、汇总列、操作列
 */
const selectCell = (rowIndex: number, columnIndex: number): [number, string] => {
  // 参数校验
  if (rowIndex < 0 || rowIndex >= props.rows.length) {
    return [-1, `行号${rowIndex}无效`]
  }
  
  if (columnIndex < 0 || columnIndex >= props.columns.length) {
    return [-1, `列号${columnIndex}无效`]
  }
  
  // 注意：columnIndex 是 props.columns 的索引，columnIndex=0 对应第一列数据单元（名称列不在 props.columns 中）
  // rowIndex 是 props.rows 的索引，rowIndex=0 对应第一行数据单元（标题行在表头，不在 props.rows 中）
  // 所以第一行数据单元（rowIndex=0）和第一列数据单元（columnIndex=0）都可以选中
  
  // 退出当前编辑状态
  if (editingCell.value) {
    endEdit()
  }
  
  // 取消单元格选中和行/列选择
  deselectCell()
  deselectRow()
  deselectColumn()
  
  // 更新当前行和列索引（响应式更新，模板会自动更新选中状态）
  currentRowIndex.value = rowIndex
  currentColumnIndex.value = columnIndex
  emit('update:currentRowIndex', rowIndex)
  emit('update:currentColumnIndex', columnIndex)
  
  // 等待DOM更新后直接操作DOM添加选中类（参考TableGrid的实现）
  nextTick(() => {
    nextTick(() => {
      const tableEl = tableRef.value?.$el as HTMLElement
      if (!tableEl) {
        return
      }
      
      // 注意：columnIndex + 2 是因为第1列是名称列，所以数据列从第2列开始
      const selector = `.el-table__body tbody tr:nth-child(${rowIndex + 1}) .el-table__cell:nth-child(${columnIndex + 2})`
      const cellElement = tableEl.querySelector(selector) as HTMLElement
      if (cellElement) {
        // 直接操作DOM添加selected-cell类（参考TableGrid的实现）
        cellElement.classList.add('selected-cell')
        
        // 确保单元格获得焦点，这样键盘事件才能正确触发
        const focusElement = cellElement.querySelector('.table-cross-cell') as HTMLElement
        if (focusElement) {
          focusElement.focus()
        }
      }
    })
  })
  
  return [1, '就绪']
}

/**
 * 选中行（接口函数）
 */
const selectRow = (rowIndex: number): [number, string] => {
  if (rowIndex < 0 || rowIndex >= props.rows.length) {
    return [-1, `行号${rowIndex}无效`]
  }
  
  // 退出编辑和单元格选中
  if (editingCell.value) {
    endEdit()
  }
  deselectCell()
  deselectColumn()
  
  selectedRowIndex.value = rowIndex
  currentRowIndex.value = rowIndex
  emit('update:currentRowIndex', rowIndex)
  emit('row-select', rowIndex)
  
  // 应用选中样式
  nextTick(() => {
    const tableEl = tableRef.value?.$el as HTMLElement
    if (tableEl) {
      const tbody = tableEl.querySelector('.el-table__body tbody')
      if (tbody) {
        const rows = Array.from(tbody.querySelectorAll('tr'))
        rows.forEach((row, idx) => {
          if (idx === rowIndex) {
            row.classList.add('selected-row')
          } else {
            row.classList.remove('selected-row')
          }
        })
      }
    }
  })
  
  return [1, '就绪']
}

/**
 * 取消行选中（接口函数）
 */
const deselectRow = (): [number, string] => {
  selectedRowIndex.value = null
  
  const tableEl = tableRef.value?.$el as HTMLElement
  if (tableEl) {
    tableEl.querySelectorAll('tr.selected-row').forEach(el => {
      el.classList.remove('selected-row')
    })
  }
  
  return [1, '就绪']
}

/**
 * 选中列（接口函数）
 */
const selectColumn = (columnIndex: number): [number, string] => {
  if (columnIndex < 0 || columnIndex >= props.columns.length) {
    return [-1, `列号${columnIndex}无效`]
  }
  
  // 退出编辑和单元格选中
  if (editingCell.value) {
    endEdit()
  }
  deselectCell()
  deselectRow()
  
  selectedColumnIndex.value = columnIndex
  currentColumnIndex.value = columnIndex
  emit('update:currentColumnIndex', columnIndex)
  emit('column-select', columnIndex)
  
  // 应用选中样式
  nextTick(() => {
    const tableEl = tableRef.value?.$el as HTMLElement
    if (tableEl) {
      const tbody = tableEl.querySelector('.el-table__body tbody')
      if (tbody) {
        const rows = Array.from(tbody.querySelectorAll('tr'))
        rows.forEach(row => {
          const cells = Array.from(row.children)
          cells.forEach((cell, idx) => {
            if (idx === columnIndex + 1) { // +1 因为第1列是名称列
              cell.classList.add('selected-column')
            } else {
              cell.classList.remove('selected-column')
            }
          })
        })
      }
    }
  })
  
  return [1, '就绪']
}

/**
 * 取消列选中（接口函数）
 */
const deselectColumn = (): [number, string] => {
  selectedColumnIndex.value = null
  
  const tableEl = tableRef.value?.$el as HTMLElement
  if (tableEl) {
    tableEl.querySelectorAll('.el-table__cell.selected-column').forEach(el => {
      el.classList.remove('selected-column')
    })
  }
  
  return [1, '就绪']
}

// ==================== 单元格导航 ====================
/**
 * 计算目标单元格（只计算，不执行实际操作）
 * 计算所有交叉数据单元格，包括第一行数据单元（rowIndex=0）和第一列数据单元（columnIndex=0）
 * 注意：rowIndex=0 对应第一行数据单元（标题行在表头，不在 props.rows 中）
 *      columnIndex=0 对应第一列数据单元（名称列不在 props.columns 中）
 */
const calculateTargetCell = (
  target: 
    | { rowIndex: number; columnIndex: number }
    | { direction: 'up' | 'down' | 'left' | 'right' | 'tab' | 'enter'; fromRowIndex?: number; fromColumnIndex?: number }
): { rowIndex: number; columnIndex: number } | null => {
  let targetRowIndex: number
  let targetColumnIndex: number
  
  // 判断是精确单元格还是相对位置
  if ('rowIndex' in target && 'columnIndex' in target) {
    // 精确单元格
    targetRowIndex = target.rowIndex
    targetColumnIndex = target.columnIndex
  } else {
    // 相对位置
    const direction = target.direction
    const fromRowIndex = target.fromRowIndex ?? currentRowIndex.value ?? 0 // 默认从第0行开始（第一行数据单元）
    const fromColumnIndex = target.fromColumnIndex ?? currentColumnIndex.value ?? 0 // 默认从第0列开始（第一列数据单元）
    
    // 确保起始位置在有效范围内
    if (fromRowIndex < 0 || fromColumnIndex < 0) {
      // 如果当前不在数据单元格范围内，从第一个数据单元格开始（rowIndex=0, columnIndex=0）
      targetRowIndex = 0
      targetColumnIndex = 0
    } else {
      let nextRowIndex = fromRowIndex
      let nextColumnIndex = fromColumnIndex
      
      switch (direction) {
        case 'left':
          // 向左：如果左边有数据单元格，则移动到左边，否则移动到上一行的最后一个数据单元格
          if (nextColumnIndex > 0) {
            nextColumnIndex = fromColumnIndex - 1
          } else if (nextRowIndex > 0) {
            nextRowIndex = fromRowIndex - 1
            nextColumnIndex = props.columns.length - 1
          } else {
            return null // 已经是第一个数据单元格（rowIndex=0, columnIndex=0）
          }
          break
          
        case 'right':
        case 'tab':
        case 'enter':
          // 向右：如果右边有数据单元格，则移动到右边，否则移动到下一行的第一个数据单元格
          if (nextColumnIndex < props.columns.length - 1) {
            nextColumnIndex = fromColumnIndex + 1
          } else if (nextRowIndex < props.rows.length - 1) {
            nextRowIndex = fromRowIndex + 1
            nextColumnIndex = 0 // 从第0列开始（第一列数据单元）
          } else {
            return null // 已经是最后一个数据单元格
          }
          break
          
        case 'up':
          // 向上：移动到上一行同列的数据单元格（可以移动到第一行数据单元rowIndex=0）
          if (nextRowIndex > 0) {
            nextRowIndex = fromRowIndex - 1
          } else {
            // 如果已经在第一行数据单元，不能再向上
            return null
          }
          break
          
        case 'down':
          // 向下：移动到下一行同列的数据单元格
          if (nextRowIndex < props.rows.length - 1) {
            nextRowIndex = fromRowIndex + 1
          } else {
            return null // 已经是最后一行数据单元格
          }
          break
      }
      
      targetRowIndex = nextRowIndex
      targetColumnIndex = nextColumnIndex
    }
  }
  
  // 校验目标单元格是否合法
  // 注意：rowIndex 是 props.rows 的索引，rowIndex=0 对应第一行数据单元（标题行在表头，不在 props.rows 中）
  // columnIndex 是 props.columns 的索引，columnIndex=0 对应第一列数据单元（名称列不在 props.columns 中）
  // 所以 rowIndex=0 和 columnIndex=0 都是允许的
  if (targetRowIndex < 0 || targetRowIndex >= props.rows.length) {
    return null
  }
  
  if (targetColumnIndex < 0 || targetColumnIndex >= props.columns.length) {
    return null
  }
  
  return {
    rowIndex: targetRowIndex,
    columnIndex: targetColumnIndex
  }
}

/**
 * 导航到单元格（接口函数）
 * 导航到所有交叉数据单元格，包括第一行数据单元（rowIndex=0）和第一列数据单元（columnIndex=0）
 */
const navigateToCell = (
  target: 
    | { rowIndex: number; columnIndex: number }
    | { direction: 'up' | 'down' | 'left' | 'right' | 'tab' | 'enter'; fromRowIndex?: number; fromColumnIndex?: number },
  options: { validateCurrent?: boolean } = {}
): [number, string] => {
  const { validateCurrent = true } = options
  
  // 处理编辑状态
  if (editingCell.value) {
    if (validateCurrent) {
      // 校验当前编辑的单元格值（仅对NumberInput类型）
      const { rowIndex, columnIndex } = editingCell.value
      const configIndex = props.currentDataConfigIndex ?? 0
      const config = props.dataConfigs?.[configIndex]
      const componentType = config?.component
      
      // 只有NumberInput需要校验值必须大于0
      if (componentType === 'NumberInput' || (!componentType && config?.type && /^(int|integer|decimal|float|double|numeric)/i.test(config.type))) {
        const value = getCellValue(rowIndex, columnIndex)
        if (value !== null && typeof value === 'number' && value <= 0) {
          return [-1, '单元格值必须大于0']
        }
      }
    }
    endEdit()
  }
  
  // 计算目标单元格位置
  const targetCell = calculateTargetCell(target)
  
  // 如果目标单元格不合法，返回错误
  if (!targetCell) {
    return [-1, '目标单元格无效']
  }
  
  const { rowIndex: targetRowIndex, columnIndex: targetColumnIndex } = targetCell
  
  // 取消所有行选中和列选中
  deselectRow()
  deselectColumn()
  
  // 选中目标单元格
  selectCell(targetRowIndex, targetColumnIndex)
  
  return [1, '就绪']
}

// ==================== 单元格值更新 ====================
const handleInputUpdate = (rowIndex: number, columnIndex: number, value: any) => {
  // 检查是否可编辑（考虑primary依赖）
  const configIndex = props.currentDataConfigIndex ?? 0
  if (!isCellEditable(rowIndex, columnIndex, configIndex)) {
    return
  }
  
  // 校验值必须大于0（仅对NumberInput类型，如果没有数据配置，使用默认校验）
  if (!props.dataConfigs || props.dataConfigs.length === 0) {
    if (value !== null && typeof value === 'number' && value <= 0) {
      return
    }
  } else {
    const config = props.dataConfigs[configIndex]
    const componentType = config?.component
    // 只有NumberInput需要校验值必须大于0
    if (componentType === 'NumberInput' || (!componentType && config?.type && /^(int|integer|decimal|float|double|numeric)/i.test(config.type))) {
      if (value !== null && typeof value === 'number' && value <= 0) {
        return
      }
    }
  }
  
  updateCellValue(rowIndex, columnIndex, value, configIndex)
}

const handleInputFocus = (rowIndex: number, columnIndex: number) => {
  if (!isEditing(rowIndex, columnIndex)) {
    startEdit(rowIndex, columnIndex)
  }
}

const handleInputBlur = (_event: FocusEvent, rowIndex: number, columnIndex: number) => {
  delayExecute(() => {
    const activeElement = document.activeElement
    if (activeElement && activeElement.closest('.excel-edit-input-number')) {
      return
    }
    if (editingCell.value && editingCell.value.rowIndex === rowIndex && editingCell.value.columnIndex === columnIndex) {
      exitEdit(rowIndex, columnIndex)
    }
  }, 100)
}

// ==================== 单元格点击事件 ====================
/**
 * 处理单元格点击
 */
const handleCellClick = (row: any, column: any) => {
  // 如果是汇总行或操作行，不处理
  if (row.__row_type__ === 'sum' || row.__row_type__ === 'action') {
    return
  }
  
  // 从 tableData 中查找行索引
  // 注意：不能直接使用引用比较，因为 tableData 是 computed，每次都会创建新数组
  // 使用行的 id 来查找（更可靠）
  const rowId = row.id
  let tableRowIndex = tableData.value.findIndex(r => r === row)
  
  // 如果引用比较失败，使用 id 比较
  if (tableRowIndex < 0 && rowId) {
    tableRowIndex = tableData.value.findIndex(r => r.id === rowId)
  }
  
  if (tableRowIndex < 0) {
    return
  }
  
  // tableData 的结构是：props.rows + 汇总行 + 操作行
  // 如果 tableRowIndex >= props.rows.length，说明是汇总行或操作行（虽然已经检查了__row_type__，但双重保险）
  if (tableRowIndex >= props.rows.length) {
    return
  }
  
  // tableRowIndex 就是数据行的索引（因为汇总行和操作行在 tableData 的后面）
  const rowIndex = tableRowIndex
  const columnProperty = column.property || column.field
  
  // 处理名称列的点击（第1列）- 不选中单元格，选中行
  if (columnProperty === 'name' || columnProperty === '__name__') {
    if (rowIndex >= 0 && rowIndex < props.rows.length) {
      // 退出编辑、选择，选中该行
      if (editingCell.value) {
        endEdit()
      }
      deselectCell()
      deselectColumn()
      selectRow(rowIndex)
    }
    return
  }
  
  // 处理汇总列的点击 - 不选中
  if (columnProperty === '__sum__') {
    return
  }
  
  // 处理操作列的点击 - 不选中
  if (columnProperty === '__action_column__') {
    return
  }
  
  // 处理交叉数据单元格的点击
  if (rowIndex >= 0 && columnProperty && columnProperty !== '__name__') {
    // 查找列索引，需要处理类型匹配问题（columnProperty 可能是字符串，而 col.id 可能是数字）
    // 因为模板中使用 String(column.id) 作为 prop，所以 columnProperty 是字符串
    const columnIndex = props.columns.findIndex(col => String(col.id) === String(columnProperty))
    
    if (columnIndex >= 0) {
      // 注意：columnIndex 是 props.columns 的索引，columnIndex=0 对应第一列数据单元（名称列不在 props.columns 中）
      // tableRowIndex 是 tableData 的索引，tableRowIndex=0 对应第一行数据单元（标题行在表头，不在 tableData 中）
      // 所以第一行数据单元（rowIndex=0）和第一列数据单元（columnIndex=0）都可以选中
      // 选中交叉数据单元格（包括第一行和第一列的交叉单元）
      selectCell(rowIndex, columnIndex)
      return
    }
  }
}

/**
 * 处理表头单元格点击
 */
const handleHeaderClick = (column: any) => {
  const columnProperty = column.property || column.field
  
  // 处理名称列的点击（第1列）
  if (columnProperty === 'name' || columnProperty === '__name__') {
    // 名称列的表头不处理
    return
  }
  
  // 处理汇总列的表头点击
  if (columnProperty === '__sum__') {
    // 汇总列的表头不处理
    return
  }
  
  // 处理数据列的表头点击（第1行）
  // 统一转换为字符串比较（因为模板中使用 String(column.id) 作为 prop）
  const columnIndex = props.columns.findIndex(col => String(col.id) === String(columnProperty))
  if (columnIndex >= 0) {
    // 退出编辑、选择，选中该列
    if (editingCell.value) {
      endEdit()
    }
    deselectCell()
    deselectRow()
    selectColumn(columnIndex)
  }
}

/**
 * 处理单元格双击
 */
const handleCellDblclick = (row: any, column: any) => {
  // 如果是汇总行或操作行，不处理
  if (row.__row_type__ === 'sum' || row.__row_type__ === 'action') {
    return
  }
  
  // 从 tableData 中查找行索引
  // 使用行的 id 来查找（更可靠）
  const rowId = row.id
  let tableRowIndex = tableData.value.findIndex(r => r === row)
  
  // 如果引用比较失败，使用 id 比较
  if (tableRowIndex < 0 && rowId) {
    tableRowIndex = tableData.value.findIndex(r => r.id === rowId)
  }
  
  if (tableRowIndex < 0 || tableRowIndex >= props.rows.length) {
    return
  }
  const rowIndex = tableRowIndex
  const columnProperty = column.property || column.field
  
  // 只处理交叉单元格的双击
  if (rowIndex >= 0 && columnProperty && columnProperty !== '__name__') {
    // 统一转换为字符串比较（因为模板中使用 String(column.id) 作为 prop）
    const columnIndex = props.columns.findIndex(col => String(col.id) === String(columnProperty))
    if (columnIndex >= 0) {
      const [editCode] = startEdit(rowIndex, columnIndex)
      if (editCode !== 1) {
        return
      }
    }
  }
}

// ==================== 键盘导航 ====================
/**
 * 处理单元格键盘事件（非编辑模式）
 */
const handleCellKeydown = (event: KeyboardEvent, row: any, column: any) => {
  const rowIndex = props.rows.indexOf(row)
  const columnProperty = column.property || column.field
  
  // 名称列不处理键盘事件
  if (columnProperty === 'name' || columnProperty === '__name__') {
    return
  }
  
  if (rowIndex === -1) {
    return
  }
  
  // 统一转换为字符串比较（因为模板中使用 String(column.id) 作为 prop）
  const columnIndex = props.columns.findIndex(col => String(col.id) === String(columnProperty))
  if (columnIndex === -1) {
    return
  }
  
  // 如果已经在编辑状态，不处理（让输入框自己处理）
  if (isEditing(rowIndex, columnIndex)) {
    return
  }
  
  const key = event.key
  const configIndex = props.currentDataConfigIndex ?? 0
  const config = props.dataConfigs?.[configIndex]
  const componentType = config?.component
  
  // 忽略 Ctrl+C 和 Ctrl+V，让全局事件处理
  if (event.ctrlKey || event.metaKey) {
    if (key === 'c' || key === 'C' || key === 'v' || key === 'V') {
      return
    }
  }
  
  // 如果按下的是可打印字符，直接进入编辑
  if (key.length === 1 && !event.ctrlKey && !event.metaKey && !event.altKey) {
    // 检查是否可编辑（考虑primary依赖）
    if (!isCellEditable(rowIndex, columnIndex, configIndex)) {
      return
    }
    
    // 根据组件类型检查输入是否有效
    if (componentType === 'NumberInput' || (!componentType && config?.type && /^(int|integer|decimal|float|double|numeric)/i.test(config.type))) {
      // 数字输入：检查是否为有效数字字符
      const isNumber = /^[0-9.\-+]$/.test(key)
      if (!isNumber) {
        return
      }
      
      event.preventDefault()
      event.stopPropagation()
      
      // 直接设置第一个字符
      const numValue = Number(key)
      if (!isNaN(numValue)) {
        updateCellValue(rowIndex, columnIndex, numValue)
        // 设置编辑状态（标记为键盘录入模式）
        startEdit(rowIndex, columnIndex)
      }
      return
    } else if (componentType === 'Input' || !componentType) {
      // 文本输入：接受任何可打印字符
      event.preventDefault()
      event.stopPropagation()
      
      // 直接设置第一个字符
      updateCellValue(rowIndex, columnIndex, key)
      // 设置编辑状态（标记为键盘录入模式）
      startEdit(rowIndex, columnIndex)
      return
    }
    // Checkbox和RadioBox不支持键盘直接输入
  }
  
  // Delete 或 Backspace 删除单元格内容
  if ((key === 'Delete' || key === 'Backspace') && !editingCell.value) {
    // 检查是否可编辑（考虑primary依赖）
    if (!isCellEditable(rowIndex, columnIndex, configIndex)) {
      return
    }
    
    event.preventDefault()
    
    // 根据组件类型设置不同的默认值
    if (componentType === 'Checkbox') {
      updateCellValue(rowIndex, columnIndex, false)
    } else if (componentType === 'NumberInput' || (!componentType && config?.type && /^(int|integer|decimal|float|double|numeric)/i.test(config.type))) {
      updateCellValue(rowIndex, columnIndex, null)
    } else {
      updateCellValue(rowIndex, columnIndex, '')
    }
    return
  }
  
  // F2 进入编辑
  if (key === 'F2') {
    // 检查是否可编辑（考虑primary依赖）
    if (!isCellEditable(rowIndex, columnIndex, configIndex)) {
      return
    }
    
    event.preventDefault()
    startEdit(rowIndex, columnIndex)
    return
  }
  
  // Tab: 选中下一个单元格（Shift+Tab 向前跳转）
  if (key === 'Tab') {
    event.preventDefault()
    event.stopPropagation()
    
    const direction = event.shiftKey ? 'left' : 'right'
    navigateToCell(
      { direction, fromRowIndex: rowIndex, fromColumnIndex: columnIndex },
      { validateCurrent: false }
    )
    return
  }
  
  // Enter: 进入编辑状态
  if (key === 'Enter') {
    // 检查是否可编辑（考虑primary依赖）
    if (!isCellEditable(rowIndex, columnIndex, configIndex)) {
      return
    }
    
    event.preventDefault()
    event.stopPropagation()
    
    startEdit(rowIndex, columnIndex)
    return
  }
  
  // 方向键导航（只在有单元格被选中时处理）
  if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(key)) {
    event.preventDefault()
    event.stopPropagation()
    
    const directionMap: { [key: string]: 'up' | 'down' | 'left' | 'right' } = {
      ArrowUp: 'up',
      ArrowDown: 'down',
      ArrowLeft: 'left',
      ArrowRight: 'right'
    }
    
    const direction = directionMap[key]
    
    // 使用当前选中的单元格位置（如果有），否则使用当前单元格位置
    // 注意：rowIndex=0 对应第一行数据单元，columnIndex=0 对应第一列数据单元，都可以导航
    const fromRowIndex = currentRowIndex.value !== null ? currentRowIndex.value : rowIndex
    const fromColumnIndex = currentColumnIndex.value !== null ? currentColumnIndex.value : columnIndex
    
    // 导航到目标单元格（包括第一行和第一列的数据单元）
    navigateToCell(
      { direction, fromRowIndex, fromColumnIndex },
      { validateCurrent: false }
    )
    return
  }
}

// ==================== 复制粘贴功能 ====================
/**
 * 获取当前选中的单元格信息
 */
const getSelectedCellInfo = () => {
  const selectedCell = document.querySelector('.el-table__cell.selected-cell') as HTMLElement
  if (!selectedCell) return null
  
  const rowElement = selectedCell.closest('tr')
  if (!rowElement) return null
  
  const tbody = rowElement.parentElement
  if (!tbody) return null
  
  const rows = Array.from(tbody.querySelectorAll('tr'))
  const rowIndex = rows.indexOf(rowElement)
  if (rowIndex === -1 || rowIndex >= props.rows.length) return null
  
  const cellIndex = Array.from(rowElement.children).indexOf(selectedCell)
  if (cellIndex === -1) return null
  
  // 跳过名称列
  const columnIndex = cellIndex - 1
  if (columnIndex < 0 || columnIndex >= props.columns.length) return null
  
  const column = props.columns[columnIndex]
  return { rowIndex, columnIndex, column }
}

/**
 * 处理复制（Ctrl+C）
 */
const handleCopy = (event: ClipboardEvent) => {
  // 确定源单元格：优先使用编辑模式，否则使用选中的单元格
  let rowIndex: number | null = null
  let columnIndex: number | null = null
  let column: TableCrossColumn | null = null
  
  if (editingCell.value) {
    // 编辑模式：使用当前编辑的单元格
    rowIndex = editingCell.value.rowIndex
    columnIndex = editingCell.value.columnIndex
    column = props.columns[columnIndex] || null
  } else {
    // 非编辑模式：使用选中的单元格
    const cellInfo = getSelectedCellInfo()
    if (cellInfo) {
      rowIndex = cellInfo.rowIndex
      columnIndex = cellInfo.columnIndex
      column = cellInfo.column
    }
  }
  
  // 如果没有有效的源单元格，忽略复制
  if (rowIndex === null || columnIndex === null || !column) {
    return
  }
  
  const configIndex = props.currentDataConfigIndex ?? 0
  const value = getCellValue(rowIndex, columnIndex, configIndex)
  
  if (value === null || value === undefined) {
    return
  }
  
  event.preventDefault()
  
  // 准备复制数据
  const config = props.dataConfigs?.[configIndex]
  const componentType = config?.component
  let copyValue = ''
  let copyData: any = value
  
  if (componentType === 'Checkbox') {
    copyValue = value ? '是' : '否'
    copyData = value
  } else if (componentType === 'RadioBox' && config?.radioOptions) {
    const option = config.radioOptions.find(opt => opt.value === value)
    copyValue = option ? option.label : String(value)
    copyData = value
  } else {
    copyValue = getCellDisplayValue(rowIndex, columnIndex, configIndex)
    copyData = value
  }
  
  // 设置剪贴板数据
  if (event.clipboardData) {
    // text/plain: 用户可见的文本
    event.clipboardData.setData('text/plain', copyValue)
    // 自定义格式：包含类型和值的元数据
    const cellData = {
      type: componentType || config?.type || 'text',
      value: copyData,
      configIndex: configIndex
    }
    event.clipboardData.setData('application/x-tablecross-cell', JSON.stringify(cellData))
  }
}

/**
 * 处理粘贴（Ctrl+V）
 */
const handlePaste = (event: ClipboardEvent) => {
  // 确定目标单元格：优先使用编辑模式，否则使用选中的单元格
  let rowIndex: number | null = null
  let columnIndex: number | null = null
  let column: TableCrossColumn | null = null
  
  if (editingCell.value) {
    // 编辑模式：使用当前编辑的单元格
    rowIndex = editingCell.value.rowIndex
    columnIndex = editingCell.value.columnIndex
    column = props.columns[columnIndex] || null
  } else {
    // 非编辑模式：使用选中的单元格
    const cellInfo = getSelectedCellInfo()
    if (cellInfo) {
      rowIndex = cellInfo.rowIndex
      columnIndex = cellInfo.columnIndex
      column = cellInfo.column
    }
  }
  
  // 如果没有有效的目标单元格，忽略粘贴
  if (rowIndex === null || columnIndex === null || !column) {
    return
  }
  
  const configIndex = props.currentDataConfigIndex ?? 0
  
  // 检查是否可编辑
  if (!isCellEditable(rowIndex, columnIndex, configIndex)) {
    return
  }
  
  event.preventDefault()
  
  // 尝试获取自定义格式的数据
  const customData = event.clipboardData?.getData('application/x-tablecross-cell')
  let cellData: any = null
  
  if (customData) {
    try {
      cellData = JSON.parse(customData)
    } catch (e) {
      // 解析失败，忽略自定义数据，使用普通文本
    }
  }
  
  // 处理粘贴数据
  const config = props.dataConfigs?.[configIndex]
  const componentType = config?.component
  
  if (cellData && cellData.type === componentType) {
    // 有自定义数据且类型匹配：使用自定义格式处理
    handleInputUpdate(rowIndex, columnIndex, cellData.value)
  } else {
    // 没有自定义数据或类型不匹配：使用普通文本粘贴
    const pasteData = event.clipboardData?.getData('text/plain') || ''
    if (pasteData) {
      if (componentType === 'Checkbox') {
        // Checkbox: 将"是"、"true"、"1"等转换为true，其他为false
        const boolValue = ['是', 'true', '1', 'yes'].includes(pasteData.toLowerCase())
        handleInputUpdate(rowIndex, columnIndex, boolValue)
      } else if (componentType === 'RadioBox' && config?.radioOptions) {
        // RadioBox: 尝试通过label或value匹配
        const option = config.radioOptions.find(opt => opt.label === pasteData || String(opt.value) === pasteData)
        if (option) {
          handleInputUpdate(rowIndex, columnIndex, option.value)
        }
      } else if (componentType === 'NumberInput' || (!componentType && config?.type && /^(int|integer|decimal|float|double|numeric)/i.test(config.type))) {
        // NumberInput: 尝试转换为数字
        const num = Number(pasteData)
        if (!isNaN(num)) {
          handleInputUpdate(rowIndex, columnIndex, num)
        }
      } else {
        // Input: 直接使用文本
        handleInputUpdate(rowIndex, columnIndex, pasteData)
      }
    } else {
      // 如果粘贴数据为空，清空单元格
      if (componentType === 'Checkbox') {
        handleInputUpdate(rowIndex, columnIndex, false)
      } else if (componentType === 'NumberInput' || (!componentType && config?.type && /^(int|integer|decimal|float|double|numeric)/i.test(config.type))) {
        handleInputUpdate(rowIndex, columnIndex, null)
      } else {
        handleInputUpdate(rowIndex, columnIndex, '')
      }
    }
  }
}

// ==================== 全局键盘事件 ====================
/**
 * 处理全局 keydown 事件（专门处理编辑模式下的 Tab 和 Escape 键）
 */
const handleGlobalKeydown = (event: KeyboardEvent) => {
  const isTab = event.key === 'Tab' || event.keyCode === 9 || event.code === 'Tab'
  const isEscape = event.key === 'Escape' || event.keyCode === 27
  
  if (!isTab && !isEscape) {
    return
  }
  
  // 只在编辑模式下处理
  if (!editingCell.value) {
    return
  }
  
  // 检查焦点是否在表格内
  const activeElement = document.activeElement
  const tableElement = tableRef.value?.$el as HTMLElement
  
  if (!activeElement || !tableElement || !tableElement.contains(activeElement)) {
    return
  }
  
  event.preventDefault()
  event.stopPropagation()
  event.stopImmediatePropagation()
  
  if (isTab) {
    // Tab 键：退出编辑（校验），跳转到下一个单元格
    const direction = event.shiftKey ? 'left' : 'right'
    const currentRowIndex = editingCell.value.rowIndex
    const currentColumnIndex = editingCell.value.columnIndex
    
    navigateToCell(
      { direction, fromRowIndex: currentRowIndex, fromColumnIndex: currentColumnIndex },
      { validateCurrent: true }
    )
  } else if (isEscape) {
    // Escape 键：退出编辑（不校验）
    if (editingCell.value) {
      const { rowIndex, columnIndex } = editingCell.value
      exitEdit(rowIndex, columnIndex)
    }
  }
}

// ==================== 行操作 ====================
/**
 * 新增行（接口函数）
 */
const addRow = async (row?: number): Promise<[number, string, number?]> => {
  // 取消所有选中
  deselectCell()
  deselectRow()
  deselectColumn()
  
  // 确定插入位置
  let insertIndex: number | undefined
  if (row === undefined || row < 0 || row >= props.rows.length) {
    // 在末尾追加
    insertIndex = undefined
  } else if (row >= 0 && row <= props.rows.length) {
    // 在row前插入
    insertIndex = row
  } else {
    return [-1, `行号${row}无效`]
  }
  
  // 创建默认行数据
  const newRow: TableCrossRow = {
    id: `temp-${Date.now()}`,
    name: ''
  }
  
  // 初始化所有列的数据为null
  props.columns.forEach(column => {
    newRow[column.id] = null
  })
  
  // 触发row-add事件
  emit('row-add', { row: newRow, insertIndex })
  
  // 等待父组件处理并DOM更新
  await nextTick()
  await nextTick()
  
  // 确定新增行的索引
  let newRowIndex: number
  if (insertIndex === undefined) {
    newRowIndex = props.rows.length - 1
  } else {
    newRowIndex = insertIndex
  }
  
  return [1, '就绪', newRowIndex]
}

/**
 * 新增列（接口函数）
 */
const addColumn = async (col?: number): Promise<[number, string, number?]> => {
  // 取消所有选中
  deselectCell()
  deselectRow()
  deselectColumn()
  
  // 确定插入位置
  let insertIndex: number | undefined
  if (col === undefined || col < 0 || col >= props.columns.length) {
    // 在末尾追加
    insertIndex = undefined
  } else if (col >= 0 && col <= props.columns.length) {
    // 在col前插入
    insertIndex = col
  } else {
    return [-1, `列号${col}无效`]
  }
  
  // 创建默认列数据
  const newColumn: TableCrossColumn = {
    id: `temp-${Date.now()}`,
    name: ''
  }
  
  // 触发column-add事件
  emit('column-add', { column: newColumn, insertIndex })
  
  // 等待父组件处理并DOM更新
  await nextTick()
  await nextTick()
  
  // 确定新增列的索引
  let newColumnIndex: number
  if (insertIndex === undefined) {
    newColumnIndex = props.columns.length - 1
  } else {
    newColumnIndex = insertIndex
  }
  
  return [1, '就绪', newColumnIndex]
}

// ==================== 生命周期 ====================
onMounted(() => {
  // 监听复制粘贴事件
  document.addEventListener('copy', handleCopy)
  document.addEventListener('paste', handlePaste)
  
  // 监听全局 keydown 事件（处理编辑模式下的 Tab 和 Escape 键）
  window.addEventListener('keydown', handleGlobalKeydown, { capture: true, passive: false })
  document.addEventListener('keydown', handleGlobalKeydown, { capture: true, passive: false })
  
  // 初始化表格宽度
  updateTableWidth()
  
  // 监听窗口大小变化
  window.addEventListener('resize', updateTableWidth)
  
  // 使用 ResizeObserver 监听表格容器大小变化
  nextTick(() => {
    const tableEl = tableRef.value?.$el as HTMLElement
    if (tableEl && window.ResizeObserver) {
      const resizeObserver = new ResizeObserver(() => {
        updateTableWidth()
      })
      resizeObserver.observe(tableEl)
      
      // 保存 observer 引用以便清理
      ;(tableRef.value as any).__resizeObserver = resizeObserver
    }
  })
})

onBeforeUnmount(() => {
  // 清理事件监听
  document.removeEventListener('copy', handleCopy)
  document.removeEventListener('paste', handlePaste)
  window.removeEventListener('keydown', handleGlobalKeydown, { capture: true } as any)
  document.removeEventListener('keydown', handleGlobalKeydown, { capture: true } as any)
  window.removeEventListener('resize', updateTableWidth)
  
  // 清理 ResizeObserver
  const tableEl = tableRef.value?.$el as HTMLElement
  if (tableEl && (tableRef.value as any).__resizeObserver) {
    ;(tableRef.value as any).__resizeObserver.disconnect()
  }
})

// ==================== 暴露方法 ====================
defineExpose({
  // 单元格操作接口
  selectCell,
  deselectCell,
  startEdit,
  exitEdit,
  navigateToCell,
  // 行操作接口
  selectRow,
  deselectRow,
  addRow,
  // 列操作接口
  selectColumn,
  deselectColumn,
  addColumn
})
</script>

<template>
  <ElTable
    ref="tableRef"
    :data="tableData"
    border
    class="table-cross"
    :row-class-name="getRowClassName"
    @cell-click="handleCellClick"
    @cell-dblclick="handleCellDblclick"
    @header-click="handleHeaderClick"
  >
    <!-- 名称列 -->
    <ElTableColumn
      prop="__name__"
      label=""
      :width="nameColumnWidth"
      align="center"
      fixed="left"
    >
      <template #header>
        <div class="name-header-cell"></div>
      </template>
      <template #default="scope">
        <!-- 汇总行和操作行：不显示拖动标志 -->
        <div 
          v-if="scope.row.__row_type__ === 'sum' || scope.row.__row_type__ === 'action'"
          class="name-cell sum-row-name-cell"
        >
          <span class="row-name-text">{{ scope.row.name }}</span>
        </div>
        
        <!-- 普通数据行 -->
        <div 
          v-else
          class="name-cell"
          :class="{ 
            'selected-row-name': selectedRowIndex === scope.$index,
            'dragging': draggingRowIndex === scope.$index,
            'drag-over': false
          }"
          draggable="true"
          @dragstart="(e: DragEvent) => handleRowDragStart(e, scope.$index)"
          @dragend="handleRowDragEnd"
          @dragenter="(e: DragEvent) => handleRowDragEnter(e, scope.$index)"
          @dragleave="handleRowDragLeave"
          @dragover.prevent
          @drop="(e: DragEvent) => handleRowDrop(e, scope.$index)"
        >
          <span class="drag-handle">
            <ElIcon :size="14"><Rank /></ElIcon>
          </span>
          <span class="row-name-text">{{ scope.row.name }}</span>
        </div>
      </template>
    </ElTableColumn>
    
    <!-- 数据列 -->
    <ElTableColumn
      v-for="(column, colIdx) in columns"
      :key="String(column.id)"
      :prop="String(column.id)"
      :label="column.name"
      :width="dataColumnWidth"
      align="center"
    >
      <template #header>
        <div 
          class="column-header-cell"
          :class="{ 
            'selected-column-name': selectedColumnIndex === colIdx,
            'dragging': draggingColumnIndex === colIdx,
            'drag-over': false
          }"
          draggable="true"
          @dragstart="(e: DragEvent) => handleColumnDragStart(e, colIdx)"
          @dragend="handleColumnDragEnd"
          @dragenter="(e: DragEvent) => handleColumnDragEnter(e, colIdx)"
          @dragleave="handleColumnDragLeave"
          @dragover.prevent
          @drop="(e: DragEvent) => handleColumnDrop(e, colIdx)"
        >
          <span class="drag-handle">
            <ElIcon :size="14"><Rank /></ElIcon>
          </span>
          <span class="column-name-text">{{ column.name }}</span>
        </div>
      </template>
      <template #default="scope">
        <!-- 汇总行：显示列小计 -->
        <span 
          v-if="scope.row.__row_type__ === 'sum'"
          class="table-cross-cell sum-row-cell"
        >{{ scope.row[String(column.id)] ?? '' }}</span>
        
        <!-- 操作行：显示删除列按钮 -->
        <div 
          v-else-if="scope.row.__row_type__ === 'action'"
          class="table-cross-cell action-cell"
        >
          <ElLink 
            type="primary" 
            :underline="false"
            @click.stop="emit('column-delete', colIdx)"
          >
            删除列
          </ElLink>
        </div>
        
        <!-- 编辑模式：根据配置渲染不同的组件 -->
        <template v-else-if="isEditing(scope.$index, colIdx) && isCellEditable(scope.$index, colIdx, currentDataConfigIndex)">
          <!-- NumberInput -->
          <ElInputNumber
            v-if="dataConfigs[currentDataConfigIndex]?.component === 'NumberInput' || (!dataConfigs[currentDataConfigIndex]?.component && dataConfigs[currentDataConfigIndex]?.type && /^(int|integer|decimal|float|double|numeric)/i.test(dataConfigs[currentDataConfigIndex].type))"
            :key="`input-number-${scope.$index}-${colIdx}`"
            :ref="(el: any) => setInputRef(scope.$index, colIdx, el)"
            :model-value="getCellValueForInput(scope.$index, colIdx)"
            size="small"
            :controls="false"
            :min="1"
            :precision="dataConfigs[currentDataConfigIndex]?.type?.includes('decimal') ? 2 : 0"
            class="excel-edit-input-number"
            @update:model-value="(val?: number) => handleInputUpdate(scope.$index, colIdx, val ?? null)"
            @focus="handleInputFocus(scope.$index, colIdx)"
            @blur="handleInputBlur($event, scope.$index, colIdx)"
          />
          
          <!-- Input -->
          <ElInput
            v-else-if="dataConfigs[currentDataConfigIndex]?.component === 'Input'"
            :key="`input-${scope.$index}-${colIdx}`"
            :ref="(el: any) => setInputRef(scope.$index, colIdx, el)"
            :model-value="getCellValueForInput(scope.$index, colIdx)"
            size="small"
            class="excel-edit-input"
            @update:model-value="(val: string) => handleInputUpdate(scope.$index, colIdx, val)"
            @focus="handleInputFocus(scope.$index, colIdx)"
            @blur="handleInputBlur($event, scope.$index, colIdx)"
          />
          
          <!-- Checkbox -->
          <ElCheckbox
            v-else-if="dataConfigs[currentDataConfigIndex]?.component === 'Checkbox'"
            :key="`checkbox-${scope.$index}-${colIdx}`"
            :ref="(el: any) => setInputRef(scope.$index, colIdx, el)"
            :model-value="getCellValueForInput(scope.$index, colIdx)"
            class="excel-edit-checkbox"
            @update:model-value="(val: boolean) => handleInputUpdate(scope.$index, colIdx, val)"
            @focus="handleInputFocus(scope.$index, colIdx)"
            @blur="handleInputBlur($event, scope.$index, colIdx)"
          />
          
          <!-- RadioBox -->
          <ElRadioGroup
            v-else-if="dataConfigs[currentDataConfigIndex]?.component === 'RadioBox' && dataConfigs[currentDataConfigIndex]?.radioOptions"
            :key="`radio-${scope.$index}-${colIdx}`"
            :ref="(el: any) => setInputRef(scope.$index, colIdx, el)"
            :model-value="getCellValueForInput(scope.$index, colIdx)"
            class="excel-edit-radio"
            @update:model-value="(val: any) => handleInputUpdate(scope.$index, colIdx, val)"
            @focus="handleInputFocus(scope.$index, colIdx)"
            @blur="handleInputBlur($event, scope.$index, colIdx)"
          >
            <ElRadio
              v-for="option in dataConfigs[currentDataConfigIndex].radioOptions"
              :key="option.value"
              :label="option.value"
            >
              {{ option.label }}
            </ElRadio>
          </ElRadioGroup>
        </template>
        
        <!-- 显示模式 -->
        <span 
          v-else
          class="table-cross-cell data-cell"
          :class="{ 
            'editing-cell': isEditing(scope.$index, colIdx),
            'non-editable-cell': !isCellEditable(scope.$index, colIdx, currentDataConfigIndex)
          }"
          @keydown="handleCellKeydown($event, scope.row, { property: column.id })"
          tabindex="0"
        >{{ getCellDisplayValue(scope.$index, colIdx) }}</span>
      </template>
    </ElTableColumn>
    
    <!-- 汇总列（排在数据列之后，操作列之前） -->
    <ElTableColumn
      prop="__sum__"
      label="行小计"
      :width="sumColumnWidth"
      align="center"
    >
      <template #header>
        <div class="sum-header-cell">
          行小计
        </div>
      </template>
      <template #default="scope">
        <!-- 汇总行和操作行：不显示行小计 -->
        <div 
          v-if="scope.row.__row_type__ === 'sum' || scope.row.__row_type__ === 'action'"
          class="sum-cell sum-column-cell"
        ></div>
        
        <!-- 普通数据行：显示行小计 -->
        <div v-else class="sum-cell sum-column-cell">
          {{ getRowSum(scope.$index) }}
        </div>
      </template>
    </ElTableColumn>
    
    <!-- 操作列（排在汇总列之后，填充列之前，当 allowDeleteRow=true 时显示） -->
    <ElTableColumn
      v-if="allowDeleteRow"
      prop="__action_column__"
      label="操作"
      width="100"
      align="center"
    >
      <template #header>
        <div class="column-header-cell action-column-header">
          <!-- 操作列不显示拖动标志 -->
          <span class="column-name-text">操作</span>
        </div>
      </template>
      <template #default="scope">
        <!-- 汇总行和操作行：操作列不显示内容 -->
        <div 
          v-if="scope.row.__row_type__ === 'sum' || scope.row.__row_type__ === 'action'"
          class="table-cross-cell action-cell"
        ></div>
        
        <!-- 普通数据行：显示删除行按钮 -->
        <div 
          v-else
          class="table-cross-cell action-cell"
        >
          <ElLink 
            type="primary" 
            :underline="false"
            @click.stop="emit('row-delete', scope.$index)"
          >
            删除行
          </ElLink>
        </div>
      </template>
    </ElTableColumn>
    
    <!-- 填充列（空白标题列，用于铺满表格，排在操作列之后） -->
    <ElTableColumn
      v-if="needFillColumn"
      prop="__fill__"
      label=""
      :width="fillColumnWidth"
      align="center"
    >
      <template #header>
        <div class="column-header-cell fill-column-header">
          <!-- 空白标题 -->
        </div>
      </template>
      <template #default>
        <!-- 填充列不显示内容 -->
        <span class="table-cross-cell fill-column-cell"></span>
      </template>
    </ElTableColumn>
    
  </ElTable>
</template>

<style lang="less" scoped>
// ==================== Less Mixins ====================
.remove-border-bg() {
  border: none !important;
  border-width: 0 !important;
  border-radius: 0 !important;
  box-shadow: none !important;
  outline: none !important;
  background: transparent !important;
  background-color: transparent !important;
}

.fill-container() {
  width: 100% !important;
  min-width: 100% !important;
  max-width: 100% !important;
  height: 100% !important;
}

// ==================== 表格基础样式 ====================
:deep(.table-cross) {
  // 设置整个表格的默认背景色为浅灰色
  .el-table__cell {
    padding: 4px !important;
    position: relative;
    min-height: 32px;
    vertical-align: middle !important;
    background-color: #fafafa !important; // 默认背景色为浅灰色，使用 !important 确保优先级
  }
  
  // 名称列样式
  .el-table__cell:first-child {
    background-color: #fafafa !important;
    border-right: 1px solid #e8e8e8;
    padding: 0 !important;
    cursor: default !important;
    user-select: none;
    -webkit-user-select: none;
    -moz-user-select: none;
    -ms-user-select: none;
  }
  
  // 表头样式
  .el-table__header th {
    background-color: #fafafa !important;
    border-bottom: 1px solid #e8e8e8;
    text-align: center !important;
    height: auto !important;
    min-height: 32px;
    padding: 4px !important;
  }
  
  // 表头单元格内容容器
  .el-table__header .el-table__cell {
    height: auto !important;
    min-height: 32px;
    padding: 4px !important;
    background-color: #fafafa !important;
  }
  
  
  // 表格最后一行的下边框移除（避免与汇总行边框叠加，汇总行已有上边框）
  .el-table__body tbody tr:last-child .el-table__cell {
    border-bottom: none !important;
  }
  
  // 数据单元格的鼠标样式（Excel 风格）
  // 只匹配数据行的数据列单元格（通过 .data-cell 类名识别，排除汇总行、操作行、汇总列、操作列、填充列）
  tbody tr:not(.sum-row-type):not(.action-row-type) .el-table__cell:not(:first-child):not(.editing-cell) {
    // 排除汇总列（包含 .sum-column-cell）、操作列（包含 .action-cell）、填充列（包含 .fill-column-cell）
    // 使用 :has() 选择器（如果浏览器不支持，下面的规则会作为fallback）
    &:not(:has(.sum-column-cell)):not(:has(.action-cell)):not(:has(.fill-column-cell)) {
      // 整个单元格使用 cell 光标（包括边缘的 padding 区域）
      cursor: cell !important;
      // 数据单元格背景色为白色
      background-color: #ffffff !important;
      
      :deep(.cell) {
        cursor: cell !important;
      }
      
      // 所有子元素都使用 cell 光标，除了输入框和链接
      *:not(input):not(.el-input-number):not(.el-input-number__wrapper):not(.el-input-number__decrease):not(.el-input-number__increase):not(.el-link):not(.el-input__wrapper):not(.el-input__inner) {
        cursor: cell !important;
      }
    }
  }
  
  // 编辑模式下的数据单元格也保持白色背景
  tbody tr:not(.sum-row-type):not(.action-row-type) .el-table__cell.editing-cell {
    &:not(:has(.sum-column-cell)):not(:has(.action-cell)):not(:has(.fill-column-cell)) {
      background-color: #ffffff !important;
    }
  }
  
  // 汇总列单元格使用默认光标（优先级更高，确保覆盖上面的规则）
  // 使用 :has() 选择器识别包含 .sum-column-cell 的单元格
  tbody tr:not(.sum-row-type):not(.action-row-type) .el-table__cell:not(:first-child):not(.editing-cell):has(.sum-column-cell) {
    cursor: default !important;
    background-color: #fafafa !important; // 汇总列单元格保持浅灰色背景
    
    :deep(.cell) {
      cursor: default !important;
    }
    
    * {
      cursor: default !important;
    }
  }
  
  // 操作列单元格保持浅灰色背景
  tbody tr:not(.sum-row-type):not(.action-row-type) .el-table__cell:not(:first-child):has(.action-cell) {
    background-color: #fafafa !important;
  }
  
  // 填充列单元格保持浅灰色背景
  tbody tr:not(.sum-row-type):not(.action-row-type) .el-table__cell:not(:first-child):has(.fill-column-cell) {
    background-color: #fafafa !important;
  }
  
  // 汇总行的所有单元格保持浅灰色背景
  tr.sum-row-type .el-table__cell {
    background-color: #fafafa !important;
  }
  
  // 操作行的所有单元格保持浅灰色背景
  tr.action-row-type .el-table__cell {
    background-color: #fafafa !important;
  }
  
  // 编辑中的单元格样式
  .el-table__cell.editing-cell {
    padding: 0 !important;
    overflow: visible !important;
    position: relative !important;
    cursor: default !important;
    
    :deep(.cell) {
      padding: 0 !important;
      margin: 0 !important;
      position: static !important;
    }
    
    :deep(input) {
      cursor: text !important;
    }
    
    // 如果编辑的单元格是数据单元格，保持白色背景
    &:not(:has(.sum-column-cell)):not(:has(.action-cell)):not(:has(.fill-column-cell)) {
      background-color: #ffffff !important;
    }
  }
}

// ==================== 名称单元格样式 ====================
.name-cell {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: flex-start;
  padding: 4px 8px;
  cursor: move;
  user-select: none;
  gap: 6px;
  
  &.selected-row-name {
    color: rgb(16, 153, 104);
    font-weight: 600;
  }
  
  &.dragging {
    opacity: 0.5;
    background-color: #f0f0f0;
  }
  
  &.drag-over {
    border-top: 2px solid rgb(16, 153, 104);
  }
  
  .drag-handle {
    display: flex;
    align-items: center;
    color: #909399;
    cursor: move;
    flex-shrink: 0;
    
    &:hover {
      color: rgb(16, 153, 104);
    }
  }
  
  .row-name-text {
    flex: 1;
    text-align: left; // 普通数据行的名称单元格左对齐
  }
  
  // 汇总行和操作行的名称单元格使用默认箭头指针（不显示拖动指针），并保持居中对齐
  &.sum-row-name-cell {
    cursor: default !important;
    justify-content: center; // 汇总行和操作行的名称单元格居中对齐
    
    .row-name-text {
      text-align: center; // 汇总行和操作行的文字居中对齐
    }
    
    * {
      cursor: default !important;
    }
  }
}

.name-header-cell {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.column-header-cell {
  width: 100%;
  min-width: 0;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 4px 8px;
  cursor: move;
  user-select: none;
  gap: 6px;
  
  // 操作列表头：不显示拖动标志，不可拖动
  &.action-column-header {
    cursor: default;
    
    .drag-handle {
      display: none;
    }
  }
  box-sizing: border-box;
  
  &.selected-column-name {
    color: rgb(16, 153, 104);
    font-weight: 600;
  }
  
  &.dragging {
    opacity: 0.5;
    background-color: #f0f0f0;
  }
  
  &.drag-over {
    border-left: 2px solid rgb(16, 153, 104);
  }
  
  .drag-handle {
    display: flex;
    align-items: center;
    color: #909399;
    cursor: move;
    flex-shrink: 0;
    
    &:hover {
      color: rgb(16, 153, 104);
    }
  }
  
  .column-name-text {
    flex: 1;
    min-width: 0;
    text-align: center;
    word-break: break-word;
    word-wrap: break-word;
    overflow-wrap: break-word;
    white-space: normal;
    line-height: 1.4;
  }
  
  &.fill-column-header {
    cursor: default;
    user-select: none;
    
    .drag-handle {
      display: none;
    }
  }
}

// ==================== 单元格显示样式 ====================
.table-cross-cell {
  display: block;
  width: 100% !important;
  min-width: 100% !important;
  max-width: 100% !important;
  flex: 1 1 auto !important;
  
  &.action-cell {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 4px;
    cursor: default !important; // 背景单元格保持箭头指针
    
    // 删除按钮本身保持手指型（ElLink默认就是pointer）
    .el-link {
      cursor: pointer !important;
    }
  }
  padding: 4px 5px;
  word-break: break-word;
  white-space: pre-wrap;
  cursor: default !important; // 默认箭头，只有 .data-cell 才是 cell 光标
  box-sizing: border-box !important;
  user-select: none;
  outline: none !important;
  border: none !important;
  text-align: center;
  
  // 只有数据单元格才使用 cell 光标，并设置白色背景
  &.data-cell {
    cursor: cell !important;
    background-color: #ffffff !important; // 数据单元格背景色为白色，使用 !important 确保优先级
  }
  
  &:focus {
    outline: none !important;
    border: none !important;
  }
  
  &.non-editable-cell {
    cursor: default !important;
    background-color: #fafafa !important; // 非可编辑单元格保持浅灰色背景
    color: #909399;
  }
  
  &.fill-column-cell {
    cursor: default !important;
    background-color: #fafafa !important; // 填充列单元格保持浅灰色背景
  }
  
  // 汇总列单元格样式
  &.sum-row-cell {
    background-color: #fafafa !important;
  }
  
  // 操作单元格样式
  &.action-cell {
    background-color: #fafafa !important;
  }
}

// ==================== 编辑组件样式 ====================
.excel-edit-input-number,
.excel-edit-input {
  :deep(.el-input),
  :deep(.el-input-number) {
    .fill-container();
    display: block !important;
  }
  
  :deep(.el-input__wrapper),
  :deep(.el-input-number__wrapper) {
    .fill-container();
    .remove-border-bg();
    padding: 0 4px !important;
    display: flex !important;
    align-items: center !important;
    
    &:hover, &:focus, &:focus-within, &.is-focus {
      .remove-border-bg();
    }
  }
  
  :deep(.el-input__inner) {
    .fill-container();
    .remove-border-bg();
    padding: 0 !important;
    line-height: normal !important;
    display: flex !important;
    align-items: center !important;
    text-align: center !important;
    
    &:hover, &:focus {
      .remove-border-bg();
    }
  }
  
  :deep(.el-input-number__decrease),
  :deep(.el-input-number__increase) {
    display: none !important;
  }
}

.excel-edit-checkbox {
  :deep(.el-checkbox) {
    .remove-border-bg();
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    width: 100% !important;
    height: 100% !important;
    
    .el-checkbox__input {
      .remove-border-bg();
    }
    
    .el-checkbox__label {
      padding-left: 0 !important;
    }
  }
}

.excel-edit-radio {
  :deep(.el-radio-group) {
    .remove-border-bg();
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    width: 100% !important;
    height: 100% !important;
    gap: 8px;
    
    .el-radio {
      margin-right: 0 !important;
      
      .el-radio__input {
        .remove-border-bg();
      }
      
      .el-radio__label {
        padding-left: 4px !important;
      }
    }
  }
}

// ==================== 汇总行和操作行样式（现在作为表格行的一部分） ====================
:deep(.el-table__body) {
  // 汇总行样式
  tr.sum-row-type {
    background-color: #fafafa !important;
    font-size: 14px;
    
    .el-table__cell {
      background-color: #fafafa !important;
      padding: 8px !important;
    }
    
    .name-cell.sum-row-name-cell {
      background-color: #fafafa !important;
      font-weight: normal;
      cursor: default !important; // 汇总行名称单元格使用默认箭头指针
      
      * {
        cursor: default !important;
      }
    }
    
    .table-cross-cell.sum-row-cell {
      background-color: #fafafa !important;
      font-weight: normal;
    }
  }
  
  // 操作行样式
  tr.action-row-type {
    background-color: #fafafa !important;
    border-top: 1px solid #ebeef5;
    font-size: 14px;
    
    .el-table__cell {
      background-color: #fafafa !important;
      padding: 8px !important;
    }
    
    .name-cell.sum-row-name-cell {
      background-color: #fafafa !important;
      font-weight: normal;
      cursor: default !important; // 汇总行名称单元格使用默认箭头指针
      
      * {
        cursor: default !important;
      }
    }
    
    .table-cross-cell.action-cell {
      background-color: #fafafa !important;
    }
  }
}

// ==================== 汇总列样式 ====================
.sum-header-cell {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 4px;
}

.sum-cell {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 4px 8px;
  text-align: center;
  font-size: 14px;
  cursor: default !important; // 汇总列单元格使用默认箭头指针
  user-select: none; // 行小计单元格文字不可选中
  -webkit-user-select: none;
  -moz-user-select: none;
  -ms-user-select: none;
}

// 汇总列单元格的父元素也使用默认光标
.sum-column-cell {
  cursor: default !important;
  
  &,
  * {
    cursor: default !important;
  }
}
</style>

<style lang="less">
// ==================== 全局样式 ====================
.table-cross {
  // 设置所有单元格的默认背景色为浅灰色
  .el-table__cell {
    background-color: #fafafa !important;
  }
  
  // 名称列背景色
  .el-table__cell:first-child {
    background-color: #fafafa !important;
  }
  
  // 表头背景色
  .el-table__header th,
  .el-table__header .el-table__cell {
    background-color: #fafafa !important;
  }
  
  // 汇总行和操作行背景色
  tr.sum-row-type .el-table__cell,
  tr.action-row-type .el-table__cell {
    background-color: #fafafa !important;
  }
  
  // 汇总列、操作列、填充列背景色
  .el-table__cell:has(.sum-column-cell),
  .el-table__cell:has(.action-cell),
  .el-table__cell:has(.fill-column-cell) {
    background-color: #fafafa !important;
  }
  
  // 数据单元格背景色为白色（非汇总列、操作列、填充列、名称列的数据单元格）
  tbody tr:not(.sum-row-type):not(.action-row-type) .el-table__cell:not(:first-child) {
    &:not(:has(.sum-column-cell)):not(:has(.action-cell)):not(:has(.fill-column-cell)) {
      background-color: #ffffff !important;
    }
  }
  
  // 编辑状态下的数据单元格也保持白色背景
  .el-table__cell.editing-cell {
    &:not(:has(.sum-column-cell)):not(:has(.action-cell)):not(:has(.fill-column-cell)) {
      background-color: #ffffff !important;
    }
    
    // 如果编辑的是汇总列、操作列、填充列，保持浅灰色
    &:has(.sum-column-cell),
    &:has(.action-cell),
    &:has(.fill-column-cell) {
      background-color: #fafafa !important;
    }
  }
  
  // 强制覆盖 Element Plus .cell 的 padding
  .el-table__header .el-table__cell .cell {
    padding: 0 !important;
    width: 100% !important;
    min-width: 0 !important;
    max-width: 100% !important;
    height: auto !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
  }
  
  .el-table__body .el-table__cell .cell {
    padding-left: 0 !important;
    padding-right: 0 !important;
  }
  
  // 单元格内部容器：充满容器并居中对齐
  tbody .el-table__cell .cell {
    width: 100% !important;
    min-width: 100% !important;
    max-width: 100% !important;
    height: 100% !important;
    padding: 0 !important;
    margin: 0 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
  }
  
  // 名称列的 .cell 容器和所有子元素都应该是默认光标（箭头）
  // 但 .name-cell 会覆盖为 move（四向箭头）
  tbody .el-table__cell:first-child {
    cursor: default !important;
    user-select: none !important;
    
    .cell {
      cursor: default !important;
      user-select: none !important;
    }
    
    // .name-cell 会覆盖为 move（四向箭头）
    .name-cell {
      cursor: move !important;
    }
    
    // 汇总行和操作行的名称单元格使用默认箭头指针（不显示拖动指针）
    .name-cell.sum-row-name-cell {
      cursor: default !important;
      
      * {
        cursor: default !important;
      }
    }
  }
  
  // 表头的名称列单元格（四角区域）保持默认箭头指针
  .el-table__header .el-table__cell:first-child {
    cursor: default !important;
    
    .cell {
      cursor: default !important;
    }
    
    * {
      cursor: default !important;
    }
  }
  
  // 数据单元格的光标样式（Excel 风格）
  // 只匹配数据行的数据列单元格（通过 .data-cell 类名识别，排除汇总行、操作行、汇总列、操作列、填充列）
  tbody tr:not(.sum-row-type):not(.action-row-type) .el-table__cell:not(:first-child):not(.editing-cell) {
    // 排除汇总列（包含 .sum-column-cell）、操作列（包含 .action-cell）、填充列（包含 .fill-column-cell）
    // 使用 :has() 选择器（如果浏览器不支持，下面的规则会作为fallback）
    &:not(:has(.sum-column-cell)):not(:has(.action-cell)):not(:has(.fill-column-cell)) {
      // 整个单元格使用 cell 光标（包括边缘的 padding 区域）
      cursor: cell !important;
      
      .cell {
        cursor: cell !important;
      }
      
      .table-cross-cell.data-cell {
        cursor: cell !important;
      }
      
      // 所有子元素都使用 cell 光标，除了输入框和链接
      *:not(input):not(.el-input-number):not(.el-input-number__wrapper):not(.el-input-number__decrease):not(.el-input-number__increase):not(.el-link):not(.el-input__wrapper):not(.el-input__inner) {
        cursor: cell !important;
      }
    }
  }
  
  // 汇总列单元格使用默认光标（优先级更高，确保覆盖上面的规则）
  // 使用 :has() 选择器识别包含 .sum-column-cell 的单元格
  tbody tr:not(.sum-row-type):not(.action-row-type) .el-table__cell:not(:first-child):not(.editing-cell):has(.sum-column-cell) {
    cursor: default !important;
    
    .cell {
      cursor: default !important;
    }
    
    .table-cross-cell {
      cursor: default !important;
    }
    
    * {
      cursor: default !important;
    }
  }
  
  // 强制移除编辑组件边框和背景
  .el-input__wrapper,
  .el-input-number__wrapper {
    border: none !important;
    box-shadow: none !important;
    background: transparent !important;
    
    &:hover,
    &:focus,
    &:focus-within,
    &.is-focus {
      border: none !important;
      box-shadow: none !important;
      background: transparent !important;
    }
  }
  
  // 单元格选中时的边框样式
  .el-table__cell {
    position: relative;
    
    &.selected-cell::after {
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      border: 2px solid rgb(16, 153, 104);
      pointer-events: none;
      box-sizing: border-box;
      z-index: 1;
    }
  }
  
  // 行选中时，该行的数据单元格添加绿色边框
  tbody tr.selected-row {
    position: relative;
    
    .el-table__cell:not(:first-child):not(:last-child) {
      position: relative !important;
      
      &::before {
        content: '' !important;
        position: absolute !important;
        top: 0 !important;
        left: 0 !important;
        right: 0 !important;
        height: 2px !important;
        background-color: rgb(16, 153, 104) !important;
        pointer-events: none !important;
        z-index: 1 !important;
      }
      
      &::after {
        content: '' !important;
        position: absolute !important;
        bottom: 0 !important;
        left: 0 !important;
        right: 0 !important;
        height: 2px !important;
        background-color: rgb(16, 153, 104) !important;
        pointer-events: none !important;
        z-index: 1 !important;
      }
    }
    
    .el-table__cell:nth-child(2) {
      position: relative !important;
      box-shadow: -2px 0 0 0 rgb(16, 153, 104) !important;
    }
    
    .el-table__cell:nth-last-child(2) {
      position: relative !important;
      border-right: 2px solid rgb(16, 153, 104) !important;
    }
  }
  
  // 列选中时，该列的数据单元格添加绿色边框
  .el-table__cell.selected-column {
    position: relative;
    
    &::before {
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      bottom: 0;
      width: 2px;
      background-color: rgb(16, 153, 104);
      pointer-events: none;
      z-index: 1;
    }
    
    &::after {
      content: '';
      position: absolute;
      top: 0;
      right: 0;
      bottom: 0;
      width: 2px;
      background-color: rgb(16, 153, 104);
      pointer-events: none;
      z-index: 1;
    }
  }
}
</style>

