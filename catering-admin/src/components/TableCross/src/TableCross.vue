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
import { ElTable, ElTableColumn, ElInputNumber, ElIcon } from 'element-plus'
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
}

/**
 * Emits 接口
 */
export interface TableCrossEmits {
  (e: 'update:rows', value: TableCrossRow[]): void
  (e: 'update:columns', value: TableCrossColumn[]): void
  (e: 'update:currentRowIndex', value: number | null): void
  (e: 'update:currentColumnIndex', value: number | null): void
  (e: 'cell-update', rowIndex: number, columnIndex: number, value: number | null): void
  (e: 'row-add', payload: { row: TableCrossRow; insertIndex?: number }): void
  (e: 'column-add', payload: { column: TableCrossColumn; insertIndex?: number }): void
  (e: 'row-select', rowIndex: number): void
  (e: 'column-select', columnIndex: number): void
  (e: 'row-order-change', newRows: TableCrossRow[]): void
  (e: 'column-order-change', newColumns: TableCrossColumn[]): void
}

const props = withDefaults(defineProps<TableCrossProps>(), {
  currentRowIndex: null,
  currentColumnIndex: null,
  nameColumnWidth: 200,
  dataColumnWidth: 160,
  sumColumnWidth: 120
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
  
  if (event.target) {
    (event.target as HTMLElement).classList.remove('drag-over')
  }
  
  // 重新排序行
  const newRows = [...props.rows]
  const draggedRow = newRows[draggingRowIndex.value]
  newRows.splice(draggingRowIndex.value, 1)
  newRows.splice(targetRowIndex, 0, draggedRow)
  
  emit('update:rows', newRows)
  emit('row-order-change', newRows)
  
  // 更新当前行索引
  if (currentRowIndex.value === draggingRowIndex.value) {
    currentRowIndex.value = targetRowIndex
    emit('update:currentRowIndex', targetRowIndex)
  } else if (currentRowIndex.value !== null) {
    // 调整当前行索引
    if (draggingRowIndex.value < currentRowIndex.value && targetRowIndex >= currentRowIndex.value) {
      currentRowIndex.value--
      emit('update:currentRowIndex', currentRowIndex.value)
    } else if (draggingRowIndex.value > currentRowIndex.value && targetRowIndex <= currentRowIndex.value) {
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
 * 获取单元格的值
 */
const getCellValue = (rowIndex: number, columnIndex: number): number | null => {
  if (rowIndex < 0 || rowIndex >= props.rows.length) return null
  if (columnIndex < 0 || columnIndex >= props.columns.length) return null
  
  const row = props.rows[rowIndex]
  const column = props.columns[columnIndex]
  const value = row[column.id]
  
  if (value === null || value === undefined || value === '') {
    return null
  }
  
  const numValue = Number(value)
  return isNaN(numValue) ? null : numValue
}

/**
 * 获取单元格的值（用于输入框，返回 number | undefined）
 */
const getCellValueForInput = (rowIndex: number, columnIndex: number): number | undefined => {
  const value = getCellValue(rowIndex, columnIndex)
  return value === null ? undefined : value
}

/**
 * 更新单元格的值
 */
const updateCellValue = (rowIndex: number, columnIndex: number, value: number | null) => {
  if (rowIndex < 0 || rowIndex >= props.rows.length) return
  if (columnIndex < 0 || columnIndex >= props.columns.length) return
  
  const newRows = props.rows.map((row, idx) => {
    if (idx === rowIndex) {
      const column = props.columns[columnIndex]
      return { ...row, [column.id]: value }
    }
    return row
  })
  
  emit('update:rows', newRows)
  emit('cell-update', rowIndex, columnIndex, value)
}

/**
 * 计算汇总行的值（对列的数据汇总）
 */
const getRowSum = (rowIndex: number): number => {
  if (rowIndex < 0 || rowIndex >= props.rows.length) return 0
  
  let sum = 0
  props.columns.forEach((_column, colIdx) => {
    const value = getCellValue(rowIndex, colIdx)
    if (value !== null && value > 0) {
      sum += value
    }
  })
  return sum
}

/**
 * 计算汇总列的值（对行的数据汇总）
 */
const getColumnSum = (columnIndex: number): number => {
  if (columnIndex < 0 || columnIndex >= props.columns.length) return 0
  
  let sum = 0
  props.rows.forEach((_row, rowIdx) => {
    const value = getCellValue(rowIdx, columnIndex)
    if (value !== null && value > 0) {
      sum += value
    }
  })
  return sum
}

/**
 * 计算表格数据（包含汇总行）
 */
const tableData = ref(props.rows)

// 监听rows变化，更新tableData
watch(
  () => props.rows,
  (newRows) => {
    tableData.value = newRows
  },
  { immediate: true, deep: true }
)

// 为了在模板中使用，需要暴露columns
const columns = computed(() => props.columns)

// ==================== 填充列计算 ====================
/** 表格容器宽度 */
const tableWidth = ref<number>(0)

/** 计算是否需要填充列（只需要1列，充满剩余宽度） */
const needFillColumn = computed(() => {
  if (tableWidth.value <= 0) return false
  
  // 计算当前列的总宽度（包括边框等）
  // 名称列 + 数据列 + 汇总列
  const currentWidth = props.nameColumnWidth + (columns.value.length * props.dataColumnWidth) + props.sumColumnWidth
  
  // 如果当前宽度已经大于等于表格宽度，不需要填充
  if (currentWidth >= tableWidth.value) return false
  
  // 只需要1列填充列，让它充满剩余宽度
  return true
})

/** 计算填充列的剩余宽度 */
const fillColumnWidth = computed(() => {
  if (!needFillColumn.value) return 0
  
  // 计算当前列的总宽度
  const currentWidth = props.nameColumnWidth + (columns.value.length * props.dataColumnWidth) + props.sumColumnWidth
  
  // 计算剩余宽度（留出一些余量给边框）
  const remainingWidth = tableWidth.value - currentWidth - 20 // 20px 余量
  
  // 允许宽度缩小为0，不设置最小宽度限制
  return Math.max(0, remainingWidth)
})

/** 更新表格宽度 */
const updateTableWidth = () => {
  nextTick(() => {
    const tableEl = tableRef.value?.$el as HTMLElement
    if (tableEl) {
      // 获取表格的实际可见宽度
      const width = tableEl.clientWidth || tableEl.offsetWidth || 0
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
  
  // 第一行和第一列不可编辑
  if (rowIndex === 0 || columnIndex === 0) {
    return [-1, '第一行和第一列不可编辑']
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
  
  const tableEl = tableRef.value?.$el as HTMLElement
  if (tableEl) {
    tableEl.querySelectorAll('.el-table__cell.selected-cell').forEach(el => {
      el.classList.remove('selected-cell')
    })
    tableEl.querySelectorAll('.el-table__cell.editing-cell').forEach(el => {
      el.classList.remove('editing-cell')
    })
  }
  
  return [1, '就绪']
}

/**
 * 选中单元格（接口函数）
 */
const selectCell = (rowIndex: number, columnIndex: number): [number, string] => {
  // 参数校验
  if (rowIndex < 0 || rowIndex >= props.rows.length) {
    return [-1, `行号${rowIndex}无效`]
  }
  
  if (columnIndex < 0 || columnIndex >= props.columns.length) {
    return [-1, `列号${columnIndex}无效`]
  }
  
  // 退出当前编辑状态
  if (editingCell.value) {
    endEdit()
  }
  
  // 取消单元格选中和行/列选择
  deselectCell()
  deselectRow()
  deselectColumn()
  
  // 选中目标单元格
  nextTick(() => {
    const tableEl = tableRef.value?.$el as HTMLElement
    if (!tableEl) return
    
    const cellElement = tableEl.querySelector(
      `.el-table__body tbody tr:nth-child(${rowIndex + 1}) .el-table__cell:nth-child(${columnIndex + 2})`
    ) as HTMLElement
    if (cellElement) {
      cellElement.classList.add('selected-cell')
      
      currentRowIndex.value = rowIndex
      emit('update:currentRowIndex', rowIndex)
    }
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
    const fromRowIndex = target.fromRowIndex ?? currentRowIndex.value ?? 0
    const fromColumnIndex = target.fromColumnIndex ?? currentColumnIndex.value ?? 0
    
    let nextRowIndex = fromRowIndex
    let nextColumnIndex = fromColumnIndex
    
    switch (direction) {
      case 'left':
        if (nextColumnIndex > 0) {
          nextColumnIndex = fromColumnIndex - 1
        } else if (nextRowIndex > 0) {
          nextRowIndex = fromRowIndex - 1
          nextColumnIndex = props.columns.length - 1
        } else {
          return null
        }
        break
        
      case 'right':
      case 'tab':
      case 'enter':
        if (nextColumnIndex < props.columns.length - 1) {
          nextColumnIndex = fromColumnIndex + 1
        } else if (nextRowIndex < props.rows.length - 1) {
          nextRowIndex = fromRowIndex + 1
          nextColumnIndex = 0
        } else {
          return null // 超出边界后不会自动增加行或列
        }
        break
        
      case 'up':
        if (nextRowIndex > 0) {
          nextRowIndex = fromRowIndex - 1
        } else {
          return null
        }
        break
        
      case 'down':
        if (nextRowIndex < props.rows.length - 1) {
          nextRowIndex = fromRowIndex + 1
        } else {
          return null // 超出边界后不会自动增加行或列
        }
        break
    }
    
    targetRowIndex = nextRowIndex
    targetColumnIndex = nextColumnIndex
  }
  
  // 校验目标单元格是否合法
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
      // 校验当前编辑的单元格值
      const { rowIndex, columnIndex } = editingCell.value
      const value = getCellValue(rowIndex, columnIndex)
      if (value !== null && value <= 0) {
        return [-1, '单元格值必须大于0']
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
const handleInputUpdate = (rowIndex: number, columnIndex: number, value: number | null) => {
  // 校验值必须大于0
  if (value !== null && value <= 0) {
    return
  }
  
  updateCellValue(rowIndex, columnIndex, value)
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
  const rowIndex = props.rows.indexOf(row)
  const columnProperty = column.property || column.field
  
  // 处理名称列的点击（第1列）
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
  
  // 处理汇总列的点击
  if (columnProperty === '__sum__') {
    // 汇总列不处理点击
    return
  }
  
  // 处理交叉单元格的点击
  if (rowIndex >= 0 && columnProperty && columnProperty !== '__name__') {
    const columnIndex = props.columns.findIndex(col => col.id === columnProperty)
    if (columnIndex >= 0) {
      // 第一行和第一列不可编辑，但可以选中
      navigateToCell(
        { rowIndex, columnIndex },
        { validateCurrent: false }
      )
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
  const columnIndex = props.columns.findIndex(col => col.id === columnProperty)
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
  const rowIndex = props.rows.indexOf(row)
  const columnProperty = column.property || column.field
  
  // 只处理交叉单元格的双击
  if (rowIndex >= 0 && columnProperty && columnProperty !== '__name__') {
    const columnIndex = props.columns.findIndex(col => col.id === columnProperty)
    if (columnIndex >= 0) {
      // 第一行和第一列不可编辑
      if (rowIndex === 0 || columnIndex === 0) {
        return
      }
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
  
  const columnIndex = props.columns.findIndex(col => col.id === columnProperty)
  if (columnIndex === -1) {
    return
  }
  
  // 如果已经在编辑状态，不处理（让输入框自己处理）
  if (isEditing(rowIndex, columnIndex)) {
    return
  }
  
  const key = event.key
  
  // 如果按下的是可打印字符，直接进入编辑
  if (key.length === 1 && !event.ctrlKey && !event.metaKey && !event.altKey) {
    // 第一行和第一列不可编辑
    if (rowIndex === 0 || columnIndex === 0) {
      return
    }
    
    // 检查是否为数字
    const isNumber = /^[0-9]$/.test(key)
    if (!isNumber) {
      return
    }
    
    event.preventDefault()
    event.stopPropagation()
    
    // 直接设置第一个字符
    const numValue = Number(key)
    updateCellValue(rowIndex, columnIndex, numValue)
    
    // 设置编辑状态
    startEdit(rowIndex, columnIndex)
    return
  }
  
  // Delete 或 Backspace 删除单元格内容
  if ((key === 'Delete' || key === 'Backspace') && !editingCell.value) {
    // 第一行和第一列不可编辑
    if (rowIndex === 0 || columnIndex === 0) {
      return
    }
    event.preventDefault()
    updateCellValue(rowIndex, columnIndex, null)
    return
  }
  
  // F2 进入编辑
  if (key === 'F2') {
    // 第一行和第一列不可编辑
    if (rowIndex === 0 || columnIndex === 0) {
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
    // 第一行和第一列不可编辑
    if (rowIndex === 0 || columnIndex === 0) {
      return
    }
    event.preventDefault()
    event.stopPropagation()
    
    startEdit(rowIndex, columnIndex)
    return
  }
  
  // 方向键导航
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
    navigateToCell(
      { direction, fromRowIndex: rowIndex, fromColumnIndex: columnIndex },
      { validateCurrent: false }
    )
    return
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
        <div 
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
        <!-- 第一行和第一列不可编辑 -->
        <span 
          v-if="scope.$index === 0 || colIdx === 0"
          class="table-cross-cell non-editable-cell"
        >{{ getCellValue(scope.$index, colIdx) || '' }}</span>
        
        <!-- 编辑模式：数字输入框 -->
        <ElInputNumber
          v-else-if="isEditing(scope.$index, colIdx)"
          :key="`input-number-${scope.$index}-${colIdx}`"
          :ref="(el: any) => setInputRef(scope.$index, colIdx, el)"
          :model-value="getCellValueForInput(scope.$index, colIdx)"
          size="small"
          :controls="false"
          :min="1"
          :precision="0"
          class="excel-edit-input-number"
          @update:model-value="(val?: number) => handleInputUpdate(scope.$index, colIdx, val ?? null)"
          @focus="handleInputFocus(scope.$index, colIdx)"
          @blur="handleInputBlur($event, scope.$index, colIdx)"
        />
        
        <!-- 显示模式 -->
        <span 
          v-else
          class="table-cross-cell"
          :class="{ 
            'selected-cell': currentRowIndex === scope.$index && currentColumnIndex === colIdx,
            'editing-cell': isEditing(scope.$index, colIdx)
          }"
          @keydown="handleCellKeydown($event, scope.row, { property: column.id })"
          tabindex="0"
        >{{ getCellValue(scope.$index, colIdx) || '' }}</span>
      </template>
    </ElTableColumn>
    
    <!-- 汇总列（排在数据列之后，填充列之前） -->
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
        <div class="sum-cell">
          {{ getRowSum(scope.$index) }}
        </div>
      </template>
    </ElTableColumn>
    
    <!-- 填充列（空白标题列，用于铺满表格，排在汇总列之后） -->
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
  
  <!-- 汇总行 -->
  <div class="sum-row-wrapper">
    <table class="sum-row-table">
      <tbody>
        <tr class="sum-row">
          <td class="sum-row-name-cell" :style="{ width: `${nameColumnWidth}px`, minWidth: `${nameColumnWidth}px`, maxWidth: `${nameColumnWidth}px` }">
            列小计
          </td>
          <td
            v-for="(column, colIdx) in columns"
            :key="String(column.id)"
            class="sum-row-cell"
            :style="{ width: `${dataColumnWidth}px`, minWidth: `${dataColumnWidth}px`, maxWidth: `${dataColumnWidth}px` }"
          >
            {{ getColumnSum(colIdx) }}
          </td>
          <td class="sum-row-sum-cell" :style="{ width: `${sumColumnWidth}px`, minWidth: `${sumColumnWidth}px`, maxWidth: `${sumColumnWidth}px` }">
            <!-- 总列小计可以显示所有数据的列小计 -->
          </td>
          <td
            v-if="needFillColumn"
            class="sum-row-cell fill-column-cell"
            :style="{ width: `${fillColumnWidth}px`, minWidth: `${fillColumnWidth}px`, maxWidth: `${fillColumnWidth}px` }"
          >
            <!-- 填充列不显示内容 -->
          </td>
        </tr>
      </tbody>
    </table>
  </div>
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
  .el-table__cell {
    padding: 4px !important;
    position: relative;
    min-height: 32px;
    vertical-align: middle !important;
    
    &:hover {
      background-color: #f5f7fa;
    }
  }
  
  // 名称列样式
  .el-table__cell:first-child {
    background-color: #fafafa;
    border-right: 1px solid #e8e8e8;
    padding: 0 !important;
    cursor: pointer !important;
    user-select: none;
    -webkit-user-select: none;
    -moz-user-select: none;
    -ms-user-select: none;
  }
  
  // 表头样式
  .el-table__header th {
    background-color: #fafafa;
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
  }
  
  // 表格最后一行的下边框移除（避免与汇总行边框叠加，汇总行已有上边框）
  .el-table__body tbody tr:last-child .el-table__cell {
    border-bottom: none !important;
  }
  
  // 数据单元格的鼠标样式（Excel 风格）
  tbody .el-table__cell:not(:first-child):not(:last-child):not(.editing-cell) {
    cursor: cell !important;
    
    :deep(.cell) {
      cursor: cell !important;
    }
    
    *:not(input):not(.el-input-number) {
      cursor: cell !important;
    }
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
    text-align: center;
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
  padding: 4px 5px;
  word-break: break-word;
  white-space: pre-wrap;
  cursor: cell !important;
  box-sizing: border-box !important;
  user-select: none;
  outline: none !important;
  border: none !important;
  text-align: center;
  
  &:focus {
    outline: none !important;
    border: none !important;
  }
  
  &.non-editable-cell {
    cursor: default !important;
    background-color: #f5f7fa;
    color: #909399;
  }
  
  &.fill-column-cell {
    cursor: default !important;
    background-color: #fafafa;
  }
}

// ==================== 编辑组件样式 ====================
.excel-edit-input-number {
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

// ==================== 汇总行样式 ====================
.sum-row-wrapper {
  border-left: 1px solid #ebeef5;
  border-right: 1px solid #ebeef5;
  border-top: none;
  border-bottom: 1px solid #ebeef5;
  background-color: #fff;
  
  .sum-row-table {
    width: auto;
    table-layout: fixed;
    border-collapse: collapse;
    
    .sum-row {
      background-color: #fafafa;
      font-size: 14px;
      
      td {
        padding: 8px !important;
        text-align: center;
        border-top: none;
        border-bottom: none;
        border-right: 1px solid #ebeef5;
        font-size: 14px;
      }
      
      .sum-row-name-cell {
        border-right: 1px solid #ebeef5;
        text-align: center;
        box-sizing: border-box;
        // 宽度通过内联样式设置，使用配置的nameColumnWidth
        // table-layout: fixed 确保列宽严格按照设置的值
        // 边框与表头一致：右边border为1px
      }
      
      .sum-row-cell {
        box-sizing: border-box;
        // 宽度通过内联样式设置，使用配置的dataColumnWidth
        // table-layout: fixed 确保列宽严格按照设置的值
      }
      
      .sum-row-sum-cell {
        border-left: 0;
        box-sizing: border-box;
        // 宽度通过内联样式设置，使用配置的sumColumnWidth
        // table-layout: fixed 确保列宽严格按照设置的值
        // 边框与表头一致：左右border都是0（右边border由td的通用样式设置为1px）
      }
      
      .fill-column-cell {
        background-color: #fafafa;
        box-sizing: border-box;
        padding: 0 !important; // 填充列不需要padding，允许宽度缩小到0
        // 宽度通过内联样式设置，使用配置的fillColumnWidth
        // table-layout: fixed 确保列宽严格按照设置的值
      }
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
}
</style>

<style lang="less">
// ==================== 全局样式 ====================
.table-cross {
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
  
  // 名称列的 .cell 容器和所有子元素都应该是 pointer 光标
  tbody .el-table__cell:first-child {
    cursor: pointer !important;
    user-select: none !important;
    
    .cell {
      cursor: pointer !important;
      user-select: none !important;
    }
    
    * {
      cursor: pointer !important;
      user-select: none !important;
    }
  }
  
  // 数据单元格的光标样式（Excel 风格）
  tbody .el-table__cell:not(:first-child):not(:last-child):not(.editing-cell) {
    cursor: cell !important;
    
    .cell {
      cursor: cell !important;
    }
    
    .table-cross-cell {
      cursor: cell !important;
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

