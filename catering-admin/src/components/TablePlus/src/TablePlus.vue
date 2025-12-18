<!--
  TablePlus - 可编辑表格基础组件
  
  功能：表格渲染、单元格编辑、键盘导航、复制粘贴、单元格/行选择
  支持：文本、数字、图片、下拉选择等列类型
-->
<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, nextTick, watch } from 'vue'
import { ElTable, ElTableColumn, ElInput, ElInputNumber, ElSelect, ElOption, ElIcon } from 'element-plus'
import { Delete } from '@element-plus/icons-vue'
import { ImagePlus } from '@/components/ImagePlus'

/**
 * 列配置接口
 */
export interface TablePlusColumn {
  /** 字段名（对应数据对象的 key） */
  field: string
  /** 列标题 */
  label: string
  /** 列宽度（如 '100px'） */
  width?: string
  /** 最小列宽度 */
  minWidth?: string
  /** 是否显示该列（默认 true） */
  show?: boolean
  /** 数据类型 */
  type?: 'text' | 'number' | 'select' | 'image' | 'date'
  /** ImagePlus 组件尺寸（仅当 type='image' 时有效，默认 'small'） */
  size?: 'normal' | 'small'
  /** 自定义格式化函数 */
  formatter?: (row: any, column: any, cellValue: any) => string
  /** 下拉选择选项（type='select' 时必填） */
  options?: Array<{ label: string; value: any }>
  /** 是否可编辑（默认 true） */
  editable?: boolean
  /** 是否必填（默认 false） */
  required?: boolean
  /** Element Plus Select 组件的属性（仅当 type='select' 时有效） */
  selectProps?: {
    disabled?: boolean
    readonly?: boolean
    clearable?: boolean
    filterable?: boolean
    allowCreate?: boolean
    [key: string]: any
  }
}

/**
 * Props 接口
 */
export interface TablePlusProps {
  /** 列配置数组 */
  columns: TablePlusColumn[]
  /** 表格数据 */
  data: any[]
  /** 当前行索引 */
  currentRowIndex?: number | null
  /** 是否显示删除按钮（默认 true） */
  showDeleteButton?: boolean
}

/**
 * Emits 接口
 */
export interface TablePlusEmits {
  (e: 'update:data', value: any[]): void
  (e: 'update:currentRowIndex', value: number | null): void
  (e: 'cell-click', rowIndex: number, field: string, event: MouseEvent): void
  (e: 'cell-dblclick', rowIndex: number, field: string, event: MouseEvent): void
  (e: 'cell-update', rowIndex: number, field: string, value: any): void
  (e: 'row-delete', rowIndex: number): void
  (e: 'row-add', defaultRow: any): void
  (e: 'image-update', rowIndex: number, field: string, value: any[]): void
  (e: 'cell-validate', rowIndex: number, field: string, value: any): boolean | string | null
}

const props = withDefaults(defineProps<TablePlusProps>(), {
  currentRowIndex: null,
  showDeleteButton: true
})

const emit = defineEmits<TablePlusEmits>()

// 表格引用
const tableRef = ref<InstanceType<typeof ElTable>>()

// ==================== 编辑状态管理 ====================
/** 当前正在编辑的单元格 */
const editingCell = ref<{ rowIndex: number; field: string } | null>(null)

/** 选中的行索引 */
const selectedRowIndex = ref<number | null>(props.currentRowIndex ?? null)

/** 选中的多行索引（用于 Ctrl/Shift 多选） */
const selectedWholeRowIndices = ref<number[]>([])

/** 上次选中的行索引（用于 Shift 范围选择） */
const lastSelectedRowIndex = ref<number | null>(null)

/** 当前行索引（computed，优先使用编辑状态，否则使用选中状态） */
const effectiveRowIndex = computed(() => {
  // 优先使用编辑状态的单元格所在行
  if (editingCell.value?.rowIndex !== undefined && editingCell.value?.rowIndex !== null) {
    return editingCell.value.rowIndex
  }
  // 否则使用选中的行索引
  return selectedRowIndex.value
})

// 监听 props.currentRowIndex 的变化，同步到内部状态
watch(
  () => props.currentRowIndex,
  (newVal) => {
    if (newVal !== selectedRowIndex.value) {
      selectedRowIndex.value = newVal
    }
  },
  { immediate: true }
)

// ==================== ImagePlus 引用管理 ====================
/** ImagePlus 组件引用映射 */
const imagePlusRefsMap = new Map<string, InstanceType<typeof ImagePlus>>()

/** 设置 ImagePlus 组件引用 */
const setImagePlusRef = (rowIndex: number, field: string, el: any) => {
  setTimeout(() => {
    const refKey = `${rowIndex}-${field}`
    el ? imagePlusRefsMap.set(refKey, el) : imagePlusRefsMap.delete(refKey)
  }, 0)
}

// ==================== 输入组件引用管理 ====================
/** 输入组件引用映射（用于直接访问组件实例的 focus 方法） */
const inputRefsMap = new Map<string, any>()

/** 设置输入组件引用 */
const setInputRef = (rowIndex: number, field: string, el: any) => {
  const refKey = `${rowIndex}-${field}`
  if (el) {
    inputRefsMap.set(refKey, el)
  } else {
    inputRefsMap.delete(refKey)
  }
}

// ==================== 辅助常量 ====================
const CURRENT_ROW_COLOR = '#409EFF'

// ==================== 工具函数 ====================
/**
 * 深拷贝对象
 */
const deepCloneObject = (obj: any): any => {
  if (obj === null || typeof obj !== 'object') return obj
  if (obj instanceof Date) return new Date(obj)
  if (Array.isArray(obj)) {
    return obj.map(item => deepCloneObject(item))
  }
  const cloned: any = {}
  for (const key in obj) {
    if (obj.hasOwnProperty(key)) {
      cloned[key] = deepCloneObject(obj[key])
    }
  }
  return cloned
}

/**
 * 格式化单元格显示值
 */
const formatCellValue = (value: any, column: TablePlusColumn): string => {
  if (column.formatter) {
    return column.formatter({}, column, value)
  }
  
  if (value === null || value === undefined) {
    return ''
  }
  
  if (column.type === 'select' && column.options) {
    const option = column.options.find(opt => opt.value === value)
    return option ? option.label : String(value)
  }
  
  if (column.type === 'image') {
    const count = Array.isArray(value) ? value.length : 0
    return count > 0 ? `${count} 张图片` : ''
  }
  
  return String(value)
}

// ==================== 编辑相关函数 ====================
/**
 * 判断单元格是否正在编辑
 */
const isEditing = (rowIndex: number, field: string): boolean => {
  return editingCell.value !== null &&
         editingCell.value.rowIndex === rowIndex &&
         editingCell.value.field === field
}

/**
 * 开始编辑单元格
 */
const startEdit = (rowIndex: number, field: string, options?: { isKeyboardInput?: boolean; inputValue?: string }) => {
  const col = props.columns.find(c => c.field === field)
  if (!col || col.editable === false || col.type === 'image') {
    return
  }
  
  // 如果已经在编辑这个单元格，不做任何操作
  if (isEditing(rowIndex, field)) {
    return
  }
  
  editingCell.value = { rowIndex, field }
  
  // 等待 DOM 更新后聚焦输入框
  // 使用双重 nextTick + requestAnimationFrame + setTimeout 确保 DOM 完全更新
  nextTick(() => {
    nextTick(() => {
      requestAnimationFrame(() => {
        // 再使用 setTimeout 确保浏览器完成渲染
        setTimeout(() => {
          const refKey = `${rowIndex}-${field}`
          
          // 首先尝试通过 ref 访问组件实例
          const componentRef = inputRefsMap.get(refKey)
          if (componentRef) {
            // 如果组件有 focus 方法，直接调用
            if (typeof componentRef.focus === 'function') {
              componentRef.focus()
              
              // 等待焦点设置完成后再设置光标位置
              setTimeout(() => {
                const cellKey = `${rowIndex}-${field}`
                const inputElement = document.querySelector(`[data-cell-key="${cellKey}"]`) as HTMLElement
                if (inputElement) {
                  const actualInput = inputElement.querySelector('input, textarea') as HTMLInputElement | HTMLTextAreaElement
                  if (actualInput && document.activeElement === actualInput) {
                    setCursorPosition(actualInput, col, options)
                  }
                }
              }, 10)
              return
            }
            
            // 如果组件有 input 属性（ElInput 组件），访问其内部的 input 元素
            if (componentRef.input) {
              const actualInput = componentRef.input as HTMLInputElement | HTMLTextAreaElement
              if (actualInput) {
                actualInput.focus()
                setCursorPosition(actualInput, col, options)
                return
              }
            }
          }
          
          // 如果 ref 方法失败，回退到 DOM 查询方法
          const cellKey = `${rowIndex}-${field}`
          const inputElement = document.querySelector(`[data-cell-key="${cellKey}"]`) as HTMLElement
          if (!inputElement) {
            return
          }
          
          // 对于 select 列，需要特殊处理：打开下拉框
          if (col.type === 'select') {
            // 等待 DOM 完全渲染后再打开下拉框
            setTimeout(() => {
              // 重新查询 inputElement，确保获取到最新的 DOM
              const cellKey = `${rowIndex}-${field}`
              const currentInputElement = document.querySelector(`[data-cell-key="${cellKey}"]`) as HTMLElement
              if (!currentInputElement) {
                return
              }
              
              // 方法1：通过 ref 访问组件实例，尝试调用内部方法
              const selectRef = inputRefsMap.get(refKey)
              if (selectRef) {
                // Element Plus ElSelect 可能有 handleFocus 或 toggleMenu 方法
                if (typeof (selectRef as any).handleFocus === 'function') {
                  (selectRef as any).handleFocus()
                  // 再触发点击事件
                  setTimeout(() => {
                    const wrapper = currentInputElement.querySelector('.el-select__wrapper') as HTMLElement
                    if (wrapper) {
                      wrapper.click()
                    }
                  }, 20)
                  return
                }
                // 尝试调用 focus
                if (typeof selectRef.focus === 'function') {
                  selectRef.focus()
                }
              }
              
              // 方法2：点击整个 select wrapper 区域（最可靠的方法）
              const selectWrapper = currentInputElement.querySelector('.el-select__wrapper') as HTMLElement
              if (selectWrapper) {
                // 创建并触发鼠标点击事件
                const clickEvent = new MouseEvent('click', {
                  bubbles: true,
                  cancelable: true,
                  view: window
                })
                selectWrapper.dispatchEvent(clickEvent)
                // 同时也调用 click 方法
                selectWrapper.click()
                return
              }
              
              // 方法3：点击下拉箭头
              const caret = currentInputElement.querySelector('.el-select__caret') as HTMLElement
              if (caret) {
                const clickEvent = new MouseEvent('click', {
                  bubbles: true,
                  cancelable: true,
                  view: window
                })
                caret.dispatchEvent(clickEvent)
                caret.click()
                return
              }
              
              // 方法4：点击整个 select 元素
              const selectEl = currentInputElement.querySelector('.el-select') as HTMLElement
              if (selectEl) {
                selectEl.click()
                return
              }
            }, 100)
            return
          }
          
          // 对于 ElInput, ElInputNumber，需要查找内部的 input 元素
          let actualInput: HTMLInputElement | HTMLTextAreaElement | null = null
          
          // 尝试多种方式查找 input 元素
          const selectors = [
            'input',
            'textarea',
            '.el-input__wrapper input',
            '.el-input__inner input',
            '.el-textarea__inner',
            '.el-input__wrapper .el-input__inner',
            'input.el-input__inner'
          ]
          
          for (const selector of selectors) {
            actualInput = inputElement.querySelector(selector) as HTMLInputElement | HTMLTextAreaElement
            if (actualInput) {
              break
            }
          }
          
          // 如果还是没找到，尝试在整个 inputElement 内部递归查找
          if (!actualInput) {
            const allInputs = inputElement.querySelectorAll('input, textarea')
            if (allInputs.length > 0) {
              actualInput = allInputs[0] as HTMLInputElement | HTMLTextAreaElement
            }
          }
          
          if (actualInput) {
            // 确保元素可见和可聚焦
            if (actualInput.offsetParent !== null) {
              actualInput.focus()
              setCursorPosition(actualInput, col, options)
            }
          }
        }, 10) // 10ms 延迟确保浏览器完成渲染
      })
    })
  })
}

/**
 * 设置光标位置
 */
const setCursorPosition = (actualInput: HTMLInputElement | HTMLTextAreaElement, col: any, options?: { isKeyboardInput?: boolean; inputValue?: string }) => {
  const isKeyboardInput = options?.isKeyboardInput || false
  const isNumberColumn = col.type === 'number'
  const isTextColumn = col.type === 'text' || !isNumberColumn
  
  if (isKeyboardInput) {
    // 键盘录入模式
    // 文本单元格和数字单元格：光标定位在文本末尾，方便继续输入
    const textLength = actualInput.value.length
    actualInput.setSelectionRange(textLength, textLength)
  } else {
    // 双击模式
    if (isNumberColumn) {
      // 数字单元格：选中数字，方便直接输入替换
      actualInput.select()
    } else if (isTextColumn) {
      // 文本单元格：光标定位在文本末尾，方便继续输入
      const textLength = actualInput.value.length
      actualInput.setSelectionRange(textLength, textLength)
    }
  }
}

/**
 * 结束编辑（内部函数，仅清除编辑状态）
 */
const endEdit = () => {
  editingCell.value = null
}

/**
 * 退出编辑状态并进入选中状态
 * @param shouldValidate 是否校验数据（默认 false）
 * @param shouldSelect 是否选中当前单元格（默认 true，用于 Enter 键场景；false 用于导航到其他单元格场景）
 * @returns 是否成功退出编辑（校验失败时返回 false）
 */
const exitEditMode = (shouldValidate: boolean = false, shouldSelect: boolean = true): boolean => {
  if (!editingCell.value) {
    return true // 如果不在编辑状态，直接返回成功
  }
  
  const { rowIndex, field } = editingCell.value
  
  // 1. 校验数据（如果需要）
  if (shouldValidate) {
    const currentValue = props.data[rowIndex]?.[field]
    const validateResult = validateCell(rowIndex, field, currentValue)
    
    // 校验失败，停止继续动作
    if (validateResult !== true && validateResult !== null) {
      return false
    }
  }
  
  // 2. 退出编辑状态
  endEdit()
  
  // 3. 如果需要选中当前单元格，则进入单元格选中状态，单元格获得焦点
  if (shouldSelect) {
    nextTick(() => {
      const tableEl = tableRef.value?.$el as HTMLElement
      if (!tableEl) return
      
      const visibleColumns = props.columns.filter(col => col.show !== false)
      const columnIndex = visibleColumns.findIndex(c => c.field === field)
      if (columnIndex !== -1) {
        // 跳过序号列，所以 columnIndex + 2
        const cellElement = tableEl.querySelector(
          `.el-table__body tbody tr:nth-child(${rowIndex + 1}) .el-table__cell:nth-child(${columnIndex + 2})`
        ) as HTMLElement
        if (cellElement) {
          // 移除编辑状态类
          cellElement.classList.remove('editing-cell')
          // 添加选中状态类
          cellElement.classList.add('selected-cell')
          
          // 更新选中行索引
          selectedRowIndex.value = rowIndex
          emit('update:currentRowIndex', rowIndex)
          
          // 确保单元格获得焦点
          const col = props.columns.find(c => c.field === field)
          const focusElement = col?.type === 'image'
            ? (cellElement.querySelector('.table-plus-image') as HTMLElement)
            : (cellElement.querySelector('.table-plus-cell') as HTMLElement)
          
          if (focusElement) {
            focusElement.focus()
          }
          
          updateSelectedRowIndex()
        }
      }
    })
  }
  
  return true
}

/**
 * 取消选择单元格
 * @returns 是否成功取消选择
 */
const deselectCell = (): boolean => {
  // 1. 如果单元格处于编辑状态，则退出编辑状态（不校验，不选中）
  if (editingCell.value) {
    // 直接调用 endEdit()，不调用 exitEditMode()，因为 exitEditMode 会选中单元格
    endEdit()
  }
  
  // 2. 单元格取消选中状态，并失去焦点
  const tableEl = tableRef.value?.$el as HTMLElement
  if (tableEl) {
    // 移除所有单元格的选中状态和编辑状态
    tableEl.querySelectorAll('.el-table__cell.selected-cell').forEach(el => {
      el.classList.remove('selected-cell')
    })
    tableEl.querySelectorAll('.el-table__cell.editing-cell').forEach(el => {
      el.classList.remove('editing-cell')
    })
    
    // 移除所有单元格的焦点（包括普通单元格和 image 列）
    tableEl.querySelectorAll('.table-plus-cell, .table-plus-image').forEach((el: HTMLElement) => {
      el.blur()
    })
  }
  
  // 注意：不清除 selectedRowIndex，因为可能需要在取消选中后保留行索引信息
  // 如果需要完全清除，可以取消下面的注释
  // selectedRowIndex.value = null
  // emit('update:currentRowIndex', null)
  
  return true
}

/**
 * 取消行选择
 * @returns 是否成功取消行选择
 */
const deselectRow = (): boolean => {
  // 清除整行选中状态
  selectedWholeRowIndices.value = []
  lastSelectedRowIndex.value = null
  
  // 清除行选中相关的 DOM 样式（如果有的话）
  const tableEl = tableRef.value?.$el as HTMLElement
  if (tableEl) {
    // 移除行选中相关的样式类（根据实际实现调整）
    tableEl.querySelectorAll('tr.selected-row').forEach(el => {
      el.classList.remove('selected-row')
    })
  }
  
  return true
}

/**
 * 选择行
 * @param targetRowIndex 目标行号
 * @param selectType 选择类型：'single' | 'ctrl' | 'shift'
 * @returns 是否成功选择行
 */
const selectRow = (targetRowIndex: number, selectType: 'single' | 'ctrl' | 'shift' = 'single'): boolean => {
  // ==================== 步骤1：校验目标行号是否有效 ====================
  if (targetRowIndex < 0 || targetRowIndex >= props.data.length) {
    return false // 无效行号，停止动作
  }
  
  // ==================== 步骤2：如果当前有单元格处于编辑或选中状态，则取消单元格选中 ====================
  deselectCell()
  
  // ==================== 步骤3：执行行选择操作 ====================
  const tableEl = tableRef.value?.$el as HTMLElement
  if (!tableEl) {
    return false
  }
  
  let rowsToSelect: number[] = []
  
  switch (selectType) {
    case 'single':
      // 单选：先取消其他行选择，再选中目标行
      // 清除所有行的选中样式（先取消其他行选择）
      const tbody = tableEl.querySelector('.el-table__body tbody')
      if (tbody) {
        tbody.querySelectorAll('tr.selected-row').forEach(el => {
          el.classList.remove('selected-row')
        })
      }
      
      // 更新选中行列表（再选目标行）
      selectedWholeRowIndices.value = [targetRowIndex]
      lastSelectedRowIndex.value = targetRowIndex
      rowsToSelect = [targetRowIndex]
      break
      
    case 'ctrl':
      // ctrl选：不取消其他行选择，增加选中当前行（如果已选中则取消选中）
      const currentIndex = selectedWholeRowIndices.value.indexOf(targetRowIndex)
      if (currentIndex === -1) {
        // 未选中，添加到选中列表（不取消其他行选择）
        selectedWholeRowIndices.value.push(targetRowIndex)
        // 在 ctrl 模式下，需要确保所有已选中的行都有样式，所以 rowsToSelect 应该包含所有已选中的行
        rowsToSelect = [...selectedWholeRowIndices.value]
        // 更新 lastSelectedRowIndex
        lastSelectedRowIndex.value = targetRowIndex
      } else {
        // 已选中，从选中列表移除
        selectedWholeRowIndices.value.splice(currentIndex, 1)
        // 移除该行的选中样式
        const tbody = tableEl.querySelector('.el-table__body tbody')
        if (tbody) {
          const rows = Array.from(tbody.querySelectorAll('tr'))
          if (rows[targetRowIndex]) {
            rows[targetRowIndex].classList.remove('selected-row')
          }
        }
        // 如果移除后没有选中的行，清除 lastSelectedRowIndex 和当前行
        if (selectedWholeRowIndices.value.length === 0) {
          lastSelectedRowIndex.value = null
          selectedRowIndex.value = null
          emit('update:currentRowIndex', null)
          updateSelectedRowIndex()
        } else {
          // 更新 lastSelectedRowIndex 为最后一个选中的行
          lastSelectedRowIndex.value = selectedWholeRowIndices.value[selectedWholeRowIndices.value.length - 1]
          // 确保其他已选中的行保持样式（重新应用所有已选中行的样式）
          rowsToSelect = [...selectedWholeRowIndices.value]
        }
        // ctrl 模式下取消选中，如果还有其他选中的行，需要确保它们保持样式
        if (rowsToSelect.length > 0) {
          // 继续执行后续的样式应用逻辑
          break
        }
        // 如果没有其他选中的行，直接返回
        return true
      }
      break
      
    case 'shift':
      // shift选：选中目标行到上次选中行之间的全部行
      if (lastSelectedRowIndex.value !== null) {
        // 有上次选中的行，选中从上次选中行到目标行之间的所有行
        const startRowIndex = lastSelectedRowIndex.value
        const endRowIndex = targetRowIndex
        const minRowIndex = Math.min(startRowIndex, endRowIndex)
        const maxRowIndex = Math.max(startRowIndex, endRowIndex)
        
        // 生成需要选中的行索引列表
        rowsToSelect = []
        for (let i = minRowIndex; i <= maxRowIndex; i++) {
          if (i >= 0 && i < props.data.length) {
            rowsToSelect.push(i)
          }
        }
        
        // 更新选中行列表（合并，去重）
        const newSelectedRows = [...new Set([...selectedWholeRowIndices.value, ...rowsToSelect])]
        selectedWholeRowIndices.value = newSelectedRows
      } else {
        // 没有上次选中的行，只选中目标行（相当于单选）
        selectedWholeRowIndices.value = [targetRowIndex]
        rowsToSelect = [targetRowIndex]
      }
      lastSelectedRowIndex.value = targetRowIndex
      break
  }
  
  // 应用选中样式到需要选中的行
  // 使用双重 nextTick 确保 DOM 更新完成
  nextTick(() => {
    nextTick(() => {
      rowsToSelect.forEach(rowIndex => {
        // 使用更可靠的选择器
        const tbody = tableEl.querySelector('.el-table__body tbody')
        if (tbody) {
          const rows = Array.from(tbody.querySelectorAll('tr'))
          if (rows[rowIndex]) {
            rows[rowIndex].classList.add('selected-row')
          }
        }
      })
    })
  })
  
  // ==================== 步骤4：设置目标行为当前行 ====================
  // 注意：ctrl 模式下不设置当前行（保持原样），只更新选中行列表
  if (selectType !== 'ctrl') {
    selectedRowIndex.value = targetRowIndex
    emit('update:currentRowIndex', targetRowIndex)
    updateSelectedRowIndex()
  } else {
    // ctrl 模式下，如果目标行被选中，设置为当前行
    if (rowsToSelect.length > 0 && rowsToSelect.includes(targetRowIndex)) {
      selectedRowIndex.value = targetRowIndex
      emit('update:currentRowIndex', targetRowIndex)
      updateSelectedRowIndex()
    }
  }
  
  return true
}

/**
 * 计算目标单元格（只计算，不执行实际操作）
 * @param target 目标单元格配置
 * @param allowAddRow 是否允许自动新增行（默认 true）
 * @returns 目标单元格信息，如果无效则返回 null
 */
const calculateTargetCell = (
  target: 
    | { rowIndex: number; field: string }
    | { direction: 'up' | 'down' | 'left' | 'right' | 'tab' | 'enter'; fromRowIndex?: number; fromField?: string },
  allowAddRow: boolean = true
): { rowIndex: number; field: string; shouldAddRow: boolean } | null => {
  const tableEl = tableRef.value?.$el as HTMLElement
  let targetRowIndex: number
  let targetField: string
  let shouldAddRow = false
  
  // 判断是精确单元格还是相对位置
  if ('rowIndex' in target && 'field' in target) {
    // 精确单元格
    targetRowIndex = target.rowIndex
    targetField = target.field
    
    // 校验精确单元格是否合法
    if (targetRowIndex < 0 || targetRowIndex >= props.data.length) {
      return null
    }
    
    const col = props.columns.find(c => c.field === targetField)
    if (!col || col.show === false || col.editable === false) {
      return null
    }
  } else {
    // 相对位置
    const direction = target.direction
    const fromRowIndex = target.fromRowIndex ?? selectedRowIndex.value ?? 0
    const fromField = target.fromField ?? (() => {
      // 如果没有指定字段，尝试从当前选中单元格获取
      if (tableEl) {
        const selectedCell = tableEl.querySelector('.el-table__cell.selected-cell') as HTMLElement
        if (selectedCell) {
          const rowElement = selectedCell.closest('tr')
          if (rowElement) {
            const cellIndex = Array.from(rowElement.children).indexOf(selectedCell)
            const visibleColumns = props.columns.filter(col => col.show !== false)
            if (cellIndex > 0 && cellIndex <= visibleColumns.length) {
              return visibleColumns[cellIndex - 1].field
            }
          }
        }
      }
      // 默认使用第一个可编辑字段
      const editableFields = getEditableFields()
      return editableFields[0] || ''
    })()
    
    if (!fromField) {
      return null
    }
    
    // 根据方向计算目标单元格
    const editableFields = getEditableFields()
    const currentFieldIndex = editableFields.indexOf(fromField)
    
    if (currentFieldIndex === -1) {
      return null
    }
    
    let nextRowIndex = fromRowIndex
    let nextFieldIndex = currentFieldIndex
    
    switch (direction) {
      case 'left':
        // 向左：如果左边有有效的数据单元格，则记录该单元格，否则找上一行的最后一个单元格并记录；如果已是首行第一列，则停止继续动作
        if (nextFieldIndex > 0) {
          nextFieldIndex = currentFieldIndex - 1
        } else if (nextRowIndex > 0) {
          // 如果已是第一个数据单元格，则记录上一行的最后一个单元格
          nextRowIndex = fromRowIndex - 1
          nextFieldIndex = editableFields.length - 1
        } else {
          // 如果已是首行第一列，则停止继续动作
          return null
        }
        break
        
      case 'right':
      case 'tab':
      case 'enter':
        // 向右：如果右边有有效的数据单元格，则记录该单元格，否则找下一行的第一个单元格并记录；如果已是末行，则记录单元格的行号为最大行号+1，列号为1
        if (nextFieldIndex < editableFields.length - 1) {
          nextFieldIndex = currentFieldIndex + 1
        } else if (nextRowIndex < props.data.length - 1) {
          // 如果已是最后一个数据单元格，则记录下一行的首个单元格
          nextRowIndex = fromRowIndex + 1
          nextFieldIndex = 0
        } else if (allowAddRow) {
          // 如果是末行最后一个数据单元格，则记录单元格的行号为最大行号+1，列号为1（第一个字段）
          nextRowIndex = props.data.length // 最大行号 + 1
          nextFieldIndex = 0 // 列号为1（第一个字段）
          shouldAddRow = true
        } else {
          return null
        }
        break
        
      case 'up':
        // 向上：如果有上一行，则记录上一行同列的单元格，否则停止继续动作
        if (nextRowIndex > 0) {
          nextRowIndex = fromRowIndex - 1
        } else {
          // 如果已是首行，则停止继续动作
          return null
        }
        break
        
      case 'down':
        // 向下：如果有下一行，则记录下一行同列的单元格，否则记录单元格的行号为最大行号+1，列号为当前列
        if (nextRowIndex < props.data.length - 1) {
          nextRowIndex = fromRowIndex + 1
        } else if (allowAddRow) {
          // 已是末行，记录单元格的行号为最大行号+1，列号为当前列
          nextRowIndex = props.data.length // 最大行号 + 1
          // nextFieldIndex 保持不变（当前列）
          shouldAddRow = true
        } else {
          return null
        }
        break
    }
    
    targetRowIndex = nextRowIndex
    targetField = editableFields[nextFieldIndex]
  }
  
  // 校验目标单元格是否合法
  if (targetRowIndex < 0) {
    return null
  }
  
  // 如果目标行号大于等于当前数据长度，需要新增行
  if (targetRowIndex >= props.data.length) {
    if (!allowAddRow) {
      return null
    }
    shouldAddRow = true
  }
  
  return {
    rowIndex: targetRowIndex,
    field: targetField,
    shouldAddRow
  }
}

// ==================== 单元格值更新 ====================
const handleInputUpdate = (rowIndex: number, field: string, value: any) => {
  const newData = [...props.data]
  newData[rowIndex] = {
    ...newData[rowIndex],
    [field]: value
  }
  emit('update:data', newData)
  emit('cell-update', rowIndex, field, value)
}

const handleInputInput = (rowIndex: number, field: string) => {
  // 输入时的处理（如果需要）
}

const handleInputFocus = (rowIndex: number, field: string) => {
  // 聚焦时确保编辑状态
  if (!isEditing(rowIndex, field)) {
    startEdit(rowIndex, field)
  }
}

const handleInputBlur = (event: FocusEvent, rowIndex: number, field: string) => {
  // 延迟执行，以便其他事件（如点击另一个单元格）先执行
  setTimeout(() => {
    // 如果焦点移到了另一个单元格的输入框，不退出编辑模式
    const activeElement = document.activeElement
    if (activeElement && activeElement.closest('.excel-edit-input, .excel-edit-select, .excel-input-number-left, .excel-edit-textarea')) {
      return
    }
    endEdit()
  }, 100)
}

// ==================== 图片列处理 ====================
/**
 * 获取 ImagePlus 组件的唯一key
 */
const getImagePlusKey = (rowIndex: number, field: string) => {
  const row = props.data[rowIndex]
  const rowId = row?.id || `temp-${rowIndex}`
  return `image-${rowId}-${field}`
}

/**
 * 处理 ImagePlus 组件的值更新
 */
const handleImageUpdate = (rowIndex: number, field: string, val: any[]) => {
  // 直接使用 ImagePlus 组件返回的值，不进行过滤
  // ImagePlus 组件已经正确处理了删除逻辑（?add 标记的图片直接删除，?original 标记的图片标记为 ?delete）
  const newValue = Array.isArray(val) ? [...val] : (val || [])
  
  const newData = [...props.data]
  const newRow = {
    ...deepCloneObject(newData[rowIndex]),
    [field]: newValue
  }
  newData[rowIndex] = newRow
  
  emit('update:data', newData)
  emit('image-update', rowIndex, field, newValue)
}

/**
 * 处理图片单元格点击
 */
const handleImageCellClick = (rowIndex: number, field: string, event: Event) => {
  // 使用统一的导航函数选中该单元格
  navigateToCell(
    { rowIndex, field },
    { validateCurrent: false, allowAddRow: false }
  )
  // 阻止事件冒泡，避免触发表格的 cell-click 事件
  event.stopPropagation()
}

// ==================== 下拉选择处理 ====================
const handleSelectVisibleChange = (visible: boolean, rowIndex: number, field: string) => {
  if (visible) {
    // 下拉菜单打开时，设置菜单宽度与单元格一致
    nextTick(() => {
      const cellKey = `${rowIndex}-${field}`
      const selectElement = document.querySelector(`[data-cell-key="${cellKey}"]`) as HTMLElement
      if (selectElement) {
        const cell = selectElement.closest('.el-table__cell') as HTMLElement
        if (cell) {
          const cellWidth = cell.offsetWidth
          // 查找下拉框（使用正确的类名）
          const dropdown = document.querySelector('.table-plus-select-dropdown') as HTMLElement
          if (dropdown) {
            dropdown.style.minWidth = `${cellWidth}px`
            dropdown.style.width = `${cellWidth}px`
            dropdown.style.maxWidth = `${cellWidth}px`
          }
        }
      }
    })
  }
}

// ==================== 单元格选择 ====================
/**
 * 导航到目标单元格（统一的单元格选择函数）
 * @param target 目标单元格配置
 *   - 精确单元格：{ rowIndex: number, field: string }
 *   - 相对位置：{ direction: 'up' | 'down' | 'left' | 'right' | 'tab' | 'enter', fromRowIndex?: number, fromField?: string }
 * @param options 选项
 *   - validateCurrent: 是否校验当前编辑单元格（默认 true）
 *   - allowAddRow: 是否允许自动新增行（默认 true）
 * @returns 是否成功导航
 */
const navigateToCell = (
  target: 
    | { rowIndex: number; field: string }
    | { direction: 'up' | 'down' | 'left' | 'right' | 'tab' | 'enter'; fromRowIndex?: number; fromField?: string },
  options: { validateCurrent?: boolean; allowAddRow?: boolean } = {}
): boolean => {
  const { validateCurrent = true, allowAddRow = true } = options
  
  // ==================== 步骤1：处理编辑状态 ====================
  if (editingCell.value) {
    // 退出编辑状态（根据选项决定是否校验，但不选中当前单元格，因为要选中新单元格）
    if (!exitEditMode(validateCurrent, false)) {
      return false // 校验失败，停止继续动作
    }
  }
  
  // ==================== 步骤2：目标单元格校验（此时不做实际的操作，只为获取精确的目标单元格）====================
  const targetCell = calculateTargetCell(target, allowAddRow)
  
  // 如果目标单元格不合法，则停止动作
  if (!targetCell) {
    return false
  }
  
  const { rowIndex: targetRowIndex, field: targetField, shouldAddRow } = targetCell
  
  // ==================== 步骤3：执行选择单元格的操作 ====================
  // 3.1 如果有行被选中，取消行选择
  if (selectedWholeRowIndices.value.length > 0) {
    deselectRow()
  }
  
  // 3.2 如果有单元格处于编辑或选中状态，则取消单元格选中
  deselectCell()
  
  // 3.3 如果目标单元格的行号大于最大行号，则新增行
  if (shouldAddRow) {
    const defaultRow: any = {}
    props.columns.forEach(col => {
      defaultRow[col.field] = col.type === 'number' ? null : (col.type === 'image' ? [] : '')
    })
    emit('row-add', defaultRow)
  }
  
  // 3.4 选中目标单元格，并获得焦点
  // 如果新增了行，需要等待数据更新
  if (shouldAddRow || targetRowIndex >= props.data.length) {
    nextTick(() => {
      if (props.data.length > 0) {
        const actualRowIndex = props.data.length - 1
        applyCellSelection(actualRowIndex, targetField)
        // 3.5 设置目标单元格所在行为当前行
        selectedRowIndex.value = actualRowIndex
        emit('update:currentRowIndex', actualRowIndex)
        updateSelectedRowIndex()
      }
    })
  } else {
    applyCellSelection(targetRowIndex, targetField)
    // 3.5 设置目标单元格所在行为当前行
    selectedRowIndex.value = targetRowIndex
    emit('update:currentRowIndex', targetRowIndex)
    updateSelectedRowIndex()
  }
  
  updateSelectedRowIndex()
  return true
}

/**
 * 应用单元格选中状态（内部辅助函数）
 * 注意：此函数只负责 DOM 操作和焦点设置，不负责更新 selectedRowIndex（由调用方负责）
 */
const applyCellSelection = (rowIndex: number, field: string) => {
  nextTick(() => {
    const tableEl = tableRef.value?.$el as HTMLElement
    if (!tableEl) return
    
    const visibleColumns = props.columns.filter(col => col.show !== false)
    const columnIndex = visibleColumns.findIndex(c => c.field === field)
    if (columnIndex !== -1) {
      // 跳过序号列，所以 columnIndex + 2（序号列是第1个，数据列从第2个开始）
      const cellElement = tableEl.querySelector(
        `.el-table__body tbody tr:nth-child(${rowIndex + 1}) .el-table__cell:nth-child(${columnIndex + 2})`
      ) as HTMLElement
      if (cellElement) {
        cellElement.classList.add('selected-cell')
        
        // 确保新单元格获得焦点，这样键盘事件才能正确触发
        // 对于普通单元格，查找 .table-plus-cell
        // 对于 image 列，查找 .table-plus-image
        const col = props.columns.find(c => c.field === field)
        const focusElement = col?.type === 'image'
          ? (cellElement.querySelector('.table-plus-image') as HTMLElement)
          : (cellElement.querySelector('.table-plus-cell') as HTMLElement)
        
        if (focusElement) {
          // 让新单元格获得焦点
          focusElement.focus()
        }
      }
    }
  })
}

/**
 * 选中单元格（保留向后兼容）
 */
const selectCell = (rowIndex: number, field?: string) => {
  if (!field) {
    selectedRowIndex.value = rowIndex
    emit('update:currentRowIndex', rowIndex)
    return
  }
  
  navigateToCell({ rowIndex, field }, { validateCurrent: false })
}

/**
 * 更新选中行索引（基于当前选中的单元格）
 */
const updateSelectedRowIndex = () => {
  nextTick(() => {
    const selectedCell = document.querySelector('.el-table__cell.selected-cell') as HTMLElement
    if (selectedCell) {
      const row = selectedCell.closest('tr')
      if (row) {
        const tbody = row.parentElement
        if (tbody) {
          const rows = Array.from(tbody.querySelectorAll('tr'))
          const rowIndex = rows.indexOf(row)
          if (rowIndex !== -1) {
            selectedRowIndex.value = rowIndex
            emit('update:currentRowIndex', rowIndex)
          }
        }
      }
    }
  })
}

/**
 * 设置当前行（程序内部使用）
 */
const setCurrentRow = (rowIndex: number | null) => {
  selectedRowIndex.value = rowIndex
  emit('update:currentRowIndex', rowIndex)
}

// ==================== 行删除 ====================
/**
 * 处理删除行
 */
const handleDeleteRow = (rowIndex: number) => {
  if (rowIndex < 0 || rowIndex >= props.data.length) return
  
  const newData = [...props.data]
  newData.splice(rowIndex, 1)
  
  emit('update:data', newData)
  emit('row-delete', rowIndex)
  
  // 如果删除了当前行，清除选中状态
  if (selectedRowIndex.value === rowIndex) {
    selectedRowIndex.value = null
    emit('update:currentRowIndex', null)
  } else if (selectedRowIndex.value !== null && selectedRowIndex.value > rowIndex) {
    // 如果删除的行在当前行之前，更新当前行索引
    selectedRowIndex.value--
    emit('update:currentRowIndex', selectedRowIndex.value)
  }
  
  // 结束编辑
  if (editingCell.value && editingCell.value.rowIndex === rowIndex) {
    endEdit()
  }
}

// ==================== 单元格点击事件 ====================
/**
 * 处理单元格点击
 */
const handleCellClick = (row: any, column: any, cell?: HTMLElement, event?: MouseEvent) => {
  const rowIndex = props.data.indexOf(row)
  const field = column.property || column.field
  
  // 处理序号列的点击（序号列没有 field，type 为 'index'）
  if (!field && column.type === 'index') {
    // 判断是否按住了 Ctrl 或 Shift 键
    const isCtrlPressed = event?.ctrlKey || event?.metaKey // metaKey 为 Mac 的 Cmd 键
    const isShiftPressed = event?.shiftKey
    
    // 确定选择类型
    let selectType: 'single' | 'ctrl' | 'shift' = 'single'
    if (isShiftPressed) {
      selectType = 'shift'
    } else if (isCtrlPressed) {
      selectType = 'ctrl'
    }
    
    // 普通点击且该行已经被选中（在 selectedWholeRowIndices 中），不切换，直接返回
    // 注意：这里检查的是行是否被选中，而不是 effectiveRowIndex，因为单元格选中和行选中是不同的状态
    if (selectType === 'single' && selectedWholeRowIndices.value.includes(rowIndex)) {
      return
    }
    
    // 使用 selectRow 函数来处理行选择（它会自动处理 DOM 样式）
    selectRow(rowIndex, selectType)
    
    return
  }
  
  if (rowIndex === -1 || !field) return
  
  const col = props.columns.find(c => c.field === field)
  if (!col || col.editable === false) {
    return
  }
  
  // 如果点击的是正在编辑的单元格，不处理（保持编辑状态）
  if (isEditing(rowIndex, field)) {
    return
  }
  
  // 使用统一的导航函数
  navigateToCell(
    { rowIndex, field },
    { validateCurrent: false, allowAddRow: false }
  )
  
  emit('cell-click', rowIndex, field, event!)
}

/**
 * 处理单元格双击
 */
const handleCellDblclick = (row: any, column: any, cell?: HTMLElement, event?: MouseEvent) => {
  const rowIndex = props.data.indexOf(row)
  const field = column.property || column.field
  
  if (rowIndex === -1 || !field) return
  
  const col = props.columns.find(c => c.field === field)
  if (!col || col.editable === false || col.type === 'image') {
    return
  }
  
  startEdit(rowIndex, field)
  
  // 对于 select 列，双击后自动打开下拉框
  if (col.type === 'select') {
    // 等待编辑状态设置完成后再打开下拉框，使用双重 nextTick 确保 DOM 更新完成
    nextTick(() => {
      nextTick(() => {
        const cellKey = `${rowIndex}-${field}`
        const refKey = `${rowIndex}-${field}`
        
        // 方法1：通过 ref 访问组件实例
        const selectRef = inputRefsMap.get(refKey)
        if (selectRef) {
          // 调用 focus 方法
          if (typeof selectRef.focus === 'function') {
            selectRef.focus()
          }
        }
        
        // 方法2：查找 DOM 元素并操作
        const inputElement = document.querySelector(`[data-cell-key="${cellKey}"]`) as HTMLElement
        if (inputElement) {
          // 找到 select wrapper
          const selectWrapper = inputElement.querySelector('.el-select__wrapper') as HTMLElement
          if (selectWrapper) {
            // 先 focus wrapper
            selectWrapper.focus()
            // 然后点击 wrapper
            selectWrapper.click()
            // 如果点击不起作用，尝试发送 mousedown 事件
            const mouseDownEvent = new MouseEvent('mousedown', {
              bubbles: true,
              cancelable: true,
              view: window
            })
            selectWrapper.dispatchEvent(mouseDownEvent)
            return
          }
          
          // 找到内部的 input 元素
          const input = inputElement.querySelector('input') as HTMLInputElement
          if (input) {
            input.focus()
            // 发送 Space 键事件来打开下拉框
            const spaceEvent = new KeyboardEvent('keydown', {
              key: ' ',
              code: 'Space',
              keyCode: 32,
              bubbles: true,
              cancelable: true
            })
            input.dispatchEvent(spaceEvent)
            // 也发送 keyup 事件
            const spaceUpEvent = new KeyboardEvent('keyup', {
              key: ' ',
              code: 'Space',
              keyCode: 32,
              bubbles: true,
              cancelable: true
            })
            input.dispatchEvent(spaceUpEvent)
            return
          }
        }
      })
    })
  }
  
  emit('cell-dblclick', rowIndex, field, event!)
}

// ==================== 键盘导航 ====================
/**
 * 获取可编辑字段列表（包括 image 列，用于导航）
 */
const getEditableFields = () => {
  return props.columns.filter(col => col.show !== false && col.editable !== false).map(col => col.field)
}

/**
 * 校验单元格数据
 * @returns true 表示校验通过，string 表示错误信息，null 表示不需要校验
 */
const validateCell = (rowIndex: number, field: string, value: any): boolean | string | null => {
  // 触发外部校验事件
  const result = emit('cell-validate', rowIndex, field, value)
  
  // 如果返回 false 或字符串，表示校验失败
  if (result === false) {
    return '数据校验失败'
  }
  if (typeof result === 'string') {
    return result
  }
  
  // 如果返回 true 或 null，表示校验通过或不需要校验
  return result === true || result === null
}


/**
 * 处理输入框键盘事件（编辑模式）
 */
const handleInputKeydown = (event: KeyboardEvent, rowIndex: number, field: string) => {
  const key = event.key
  
  // Tab: 退出编辑（校验），跳转单元格
  if (key === 'Tab') {
    event.preventDefault()
    event.stopPropagation()
    
    // 先退出编辑状态（校验）
    if (!exitEditMode(true)) {
      return // 校验失败，不跳转
    }
    
    // 跳转到下一个单元格
    const direction = event.shiftKey ? 'left' : 'right'
    navigateToCell(
      { direction, fromRowIndex: rowIndex, fromField: field },
      { validateCurrent: false, allowAddRow: true } // 已经校验过了，不需要再校验
    )
    return
  }
  
  // Enter: 退出编辑（校验），不跳转单元格
  if (key === 'Enter') {
    event.preventDefault()
    event.stopPropagation()
    
    // 退出编辑状态（校验），不跳转
    exitEditMode(true)
    return
  }
  
  // Escape: 退出编辑（不校验）
  if (key === 'Escape') {
    event.preventDefault()
    event.stopPropagation()
    
    exitEditMode(false)
    return
  }
  
  // 方向键：由编辑组件自身来处理键盘事件（不拦截）
  // 对于 select/text/number 类型，方向键用于编辑框内的光标操作
  if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(key)) {
    // 不拦截，让编辑组件自己处理
    return
  }
}

/**
 * 处理单元格键盘事件（非编辑模式）
 */
const handleCellKeydown = (event: KeyboardEvent, row: any, column: any) => {
  const rowIndex = props.data.indexOf(row)
  const field = column.property || column.field
  
  if (rowIndex === -1 || !field) return
  
  const col = props.columns.find(c => c.field === field)
  if (col && col.editable === false) return
  
  const key = event.key
  const isImageColumn = col && col.type === 'image'
  
  // 对于 image 列，处理导航键和 Delete 键
  if (isImageColumn) {
    // Delete 或 Backspace 删除所有图片
    if ((key === 'Delete' || key === 'Backspace') && !editingCell.value) {
      event.preventDefault()
      
      const currentImages = props.data[rowIndex]?.[field]
      const imageArray = Array.isArray(currentImages) ? currentImages : []
      // 使用 markOriginalImagesAsDeleted 标记所有图片为删除
      const deletedImages = markOriginalImagesAsDeleted(imageArray)
      
      const newData = props.data.map((r, idx) => {
        if (idx === rowIndex) {
          return { ...r, [field]: deletedImages }
        }
        return r
      })
      emit('update:data', newData)
      emit('image-update', rowIndex, field, deletedImages)
      return
    }
    
    // Tab: 选中下一个单元格
    if (key === 'Tab') {
      event.preventDefault()
      event.stopPropagation()
      
      const direction = event.shiftKey ? 'left' : 'right'
      navigateToCell(
        { direction, fromRowIndex: rowIndex, fromField: field },
        { validateCurrent: false, allowAddRow: true }
      )
      return
    }
    
    // Enter: 同 Tab 键
    if (key === 'Enter') {
      event.preventDefault()
      event.stopPropagation()
      
      navigateToCell(
        { direction: 'tab', fromRowIndex: rowIndex, fromField: field },
        { validateCurrent: false, allowAddRow: true }
      )
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
        { direction, fromRowIndex: rowIndex, fromField: field },
        { validateCurrent: false, allowAddRow: true }
      )
      return
    }
    
    // image 列的其他键不处理，让浏览器默认行为处理
    return
  }
  
  // 如果已经在编辑状态，不处理（让输入框自己处理）
  if (isEditing(rowIndex, field)) {
    return
  }
  
  // 忽略 Ctrl+C 和 Ctrl+V，让全局事件处理
  if (event.ctrlKey || event.metaKey) {
    if (key === 'c' || key === 'C' || key === 'v' || key === 'V') {
      return
    }
  }
  
  // 如果按下的是可打印字符，直接进入编辑
  if (key.length === 1 && !event.ctrlKey && !event.metaKey && !event.altKey) {
    event.preventDefault()
    event.stopPropagation()
    
    // 检查是否是数字列
    if (col?.type === 'number') {
      // 数字列：检查输入是否为有效数字
      const isNumber = /^[0-9.\-+]$/.test(key)
      if (!isNumber) {
        // 输入非法数字则忽略
        return
      }
    }
    
    // 直接设置第一个字符（Excel行为：输入时替换整个内容）
    const newData = [...props.data]
    let newValue: any = key
    
    if (col?.type === 'number') {
      // 数字列：如果输入的是数字，替换原值
      newValue = key
    } else {
      // 文本列：用输入的文本代替原文本
      newValue = key
    }
    
    newData[rowIndex] = { ...newData[rowIndex], [field]: newValue }
    emit('update:data', newData)
    
    // 设置编辑状态（标记为键盘录入模式）
    startEdit(rowIndex, field, { isKeyboardInput: true, inputValue: key })
    return
  }
  
  // Delete 或 Backspace 删除单元格内容
  if ((key === 'Delete' || key === 'Backspace') && !editingCell.value) {
    event.preventDefault()
    
    // 图片类型：标记所有图片为删除（相当于对每个图片点了删除按钮）
    if (col?.type === 'image') {
      const currentImages = props.data[rowIndex]?.[field]
      const imageArray = Array.isArray(currentImages) ? currentImages : []
      // 使用 markOriginalImagesAsDeleted 标记所有图片为删除
      const deletedImages = markOriginalImagesAsDeleted(imageArray)
      
      const newData = props.data.map((row, idx) => {
        if (idx === rowIndex) {
          return { ...row, [field]: deletedImages }
        }
        return row
      })
      emit('update:data', newData)
      emit('image-update', rowIndex, field, deletedImages)
    } else {
      // 其他类型：清空单元格内容
      const newData = [...props.data]
      newData[rowIndex] = { ...newData[rowIndex], [field]: col?.type === 'number' ? null : '' }
      emit('update:data', newData)
      emit('cell-update', rowIndex, field, col?.type === 'number' ? null : '')
    }
    return
  }
  
  // F2 进入编辑
  if (key === 'F2') {
    event.preventDefault()
    startEdit(rowIndex, field)
    return
  }
  
  // Tab: 选中下一个单元格
  if (key === 'Tab') {
    event.preventDefault()
    event.stopPropagation()
    
    const direction = event.shiftKey ? 'left' : 'right'
    navigateToCell(
      { direction, fromRowIndex: rowIndex, fromField: field },
      { validateCurrent: false, allowAddRow: true }
    )
    return
  }
  
  // Enter: 同 Tab 键
  if (key === 'Enter') {
    event.preventDefault()
    event.stopPropagation()
    
    navigateToCell(
      { direction: 'tab', fromRowIndex: rowIndex, fromField: field },
      { validateCurrent: false, allowAddRow: true }
    )
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
      { direction, fromRowIndex: rowIndex, fromField: field },
      { validateCurrent: false, allowAddRow: true }
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
  
  const rowIndex = Array.from(tbody.children).indexOf(rowElement)
  if (rowIndex === -1) return null
  
  const cellIndex = Array.from(rowElement.children).indexOf(selectedCell)
  if (cellIndex === -1) return null
  
  // 跳过序号列
  const columnIndex = cellIndex - 1
  if (columnIndex < 0) return null
  
  const visibleColumns = props.columns.filter(col => col.show !== false)
  if (columnIndex >= visibleColumns.length) return null
  
  const column = visibleColumns[columnIndex]
  return { rowIndex, field: column.field, column }
}

/**
 * 处理原图片数组的删除标记
 * 在粘贴新图片之前，需要将原图片标记为删除
 */
const markOriginalImagesAsDeleted = (imageArray: any[]): any[] => {
  if (!Array.isArray(imageArray)) {
    return []
  }
  
  return imageArray
    .map(item => {
      // 如果是对象：直接删除（还没保存到后台，不需要保留）
      if (typeof item === 'object' && item !== null) {
        return null
      }
      
      // 如果是字符串：处理标记
      if (typeof item === 'string') {
        if (item.includes('?original') || item.includes('?add')) {
          // original 或 add → delete（标记为删除）
          return item.replace(/\?(original|add)/, '?delete')
        } else if (item.includes('?delete')) {
          // delete → 保持不变
          return item
        } else {
          // 没有标记的字符串（默认是 original），改为 delete
          return item + '?delete'
        }
      }
      
      return item
    })
    .filter(item => item !== null) // 过滤掉对象元素
}

/**
 * 处理图片数组的粘贴转换
 * 将复制的图片数组转换为可粘贴的格式
 * 注意：只复制粘贴字符串格式的图片 URL，不复制对象（内存预览）
 */
const processImageArrayForPaste = (imageArray: any[]): any[] => {
  if (!Array.isArray(imageArray)) {
    return []
  }
  
  return imageArray
    .filter(item => {
      // 过滤掉对象格式（内存预览），只保留字符串格式的图片 URL
      // 因为内存预览 URL 在其他行无法访问
      if (typeof item === 'object' && item !== null) {
        return false
      }
      // 过滤掉删除标记的图片
      if (typeof item === 'string' && item.includes('?delete')) {
        return false
      }
      return typeof item === 'string'
    })
    .map(item => {
      // 处理字符串格式的图片标记
      if (typeof item === 'string') {
        // original → add（这样后台会新增这个图片）
        if (item.includes('?original')) {
          return item.replace('?original', '?add')
        }
        // add → 保持不变（后台会新增）
        if (item.includes('?add')) {
          return item
        }
        // 没有标记的，添加 ?add 标记
        return item + '?add'
      }
      return item
    })
    .filter(Boolean) // 过滤掉空值
}

/**
 * 处理复制（Ctrl+C）
 */
const handleCopy = (event: ClipboardEvent) => {
  // 优先处理编辑模式
  if (editingCell.value) {
    const { rowIndex, field } = editingCell.value
    const col = props.columns.find(c => c.field === field)
    const value = props.data[rowIndex]?.[field]
    
    if (value !== undefined && value !== null) {
      event.preventDefault()
      let copyValue = ''
      let copyData = value
      
      // 根据列类型处理显示值和复制数据
      if (col?.type === 'image') {
        // 图片类型：只复制字符串格式的图片 URL，过滤掉对象（内存预览）
        const imageArray = Array.isArray(value) ? value : []
        const stringImages = imageArray.filter((item: any) => typeof item === 'string')
        copyData = stringImages
        copyValue = `${stringImages.length} image(s)`
      } else {
        copyValue = String(value)
      }
      
      // 使用 clipboardData 设置剪贴板
      if (event.clipboardData) {
        // text/plain: 用户可见的文本
        event.clipboardData.setData('text/plain', copyValue)
        // 自定义格式：包含类型和值的元数据
        const cellData = {
          type: col?.type || 'text',
          value: copyData,
          field: field
        }
        event.clipboardData.setData('application/x-importgrid-cell', JSON.stringify(cellData))
      }
    }
    return
  }
  
  // 非编辑模式：从选中的单元格复制
  const cellInfo = getSelectedCellInfo()
  if (cellInfo) {
    event.preventDefault()
    const { rowIndex, field, column } = cellInfo
    const value = props.data[rowIndex]?.[field]
    
    let copyValue = ''
    let copyData = value
    
    if (value !== undefined && value !== null) {
      // 根据列类型处理显示值和复制数据
      if (column.type === 'image') {
        // 图片类型：只复制字符串格式的图片 URL，过滤掉对象（内存预览）
        const imageArray = Array.isArray(value) ? value : []
        const stringImages = imageArray.filter((item: any) => typeof item === 'string')
        copyData = stringImages
        copyValue = `${stringImages.length} image(s)`
      } else {
        // 其他类型：拷贝原始值（字符串形式）
        copyValue = String(value)
      }
    }
    
    // 使用 clipboardData 设置剪贴板
    if (event.clipboardData) {
      // text/plain: 用户可见的文本
      event.clipboardData.setData('text/plain', copyValue)
      // 自定义格式：包含类型和值的元数据
      const cellData = {
        type: column.type || 'text',
        value: copyData,
        field: field
      }
      event.clipboardData.setData('application/x-importgrid-cell', JSON.stringify(cellData))
    }
  }
}

/**
 * 处理粘贴（Ctrl+V）
 */
const handlePaste = (event: ClipboardEvent) => {
  // 优先处理编辑模式
  if (editingCell.value) {
    event.preventDefault()
    const { rowIndex, field } = editingCell.value
    const targetCol = props.columns.find(c => c.field === field)
    
    if (!targetCol || targetCol.editable === false) {
      return
    }
    
    // 尝试获取自定义格式的数据
    const customData = event.clipboardData?.getData('application/x-importgrid-cell')
    let cellData: any = null
    
    if (customData) {
      try {
        cellData = JSON.parse(customData)
      } catch (e) {
        // 解析失败，使用普通文本
      }
    }
    
    // 如果有自定义数据且类型匹配
    if (cellData && cellData.type === targetCol.type) {
      // 类型匹配，直接复制值
      if (targetCol.type === 'image') {
        // 图片类型：特殊处理数组
        // 1. 先标记原图片为删除
        const deletedImages = markOriginalImagesAsDeleted(props.data[rowIndex][field])
        // 2. 处理要粘贴的新图片（确保深拷贝）
        const newImages = processImageArrayForPaste(cellData.value)
        // 3. 合并删除标记的原图片和新图片（创建全新数组）
        const mergedImages = [...deletedImages, ...newImages]
        
        // 4. 更新行数据（创建新行对象以避免引用共享）
        const newData = props.data.map((row, idx) => {
          if (idx === rowIndex) {
            return { ...row, [field]: mergedImages }
          }
          return row
        })
        emit('update:data', newData)
        emit('image-update', rowIndex, field, mergedImages)
      } else {
        // 非图片类型，也创建新行对象
        const newData = props.data.map((row, idx) => {
          if (idx === rowIndex) {
            return { ...row, [field]: cellData.value }
          }
          return row
        })
        emit('update:data', newData)
        emit('cell-update', rowIndex, field, cellData.value)
      }
    } else if (cellData && cellData.type !== targetCol.type) {
      // 类型不匹配，忽略粘贴
      console.log('类型不匹配，忽略粘贴操作')
      return
    } else {
      // 没有自定义数据，使用普通文本粘贴（兼容外部复制）
      const pasteData = event.clipboardData?.getData('text/plain') || ''
      if (pasteData) {
        if (targetCol.type === 'number') {
          const num = Number(pasteData)
          if (!isNaN(num)) {
            handleInputUpdate(rowIndex, field, num)
          }
        } else if (targetCol.type === 'image') {
          // 图片类型不支持从普通文本粘贴
          console.log('图片列不支持从文本粘贴')
        } else {
          handleInputUpdate(rowIndex, field, pasteData)
        }
      }
    }
    return
  }
  
  // 非编辑模式：粘贴到选中的单元格
  const cellInfo = getSelectedCellInfo()
  if (cellInfo) {
    event.preventDefault()
    const { rowIndex, field, column } = cellInfo
    
    // 检查列是否可编辑
    if (column.editable === false) {
      return
    }
    
    // 尝试获取自定义格式的数据
    const customData = event.clipboardData?.getData('application/x-importgrid-cell')
    let cellData: any = null
    
    if (customData) {
      try {
        cellData = JSON.parse(customData)
      } catch (e) {
        // 解析失败，使用普通文本
      }
    }
    
    // 如果有自定义数据且类型匹配
    if (cellData && cellData.type === column.type) {
      // 类型匹配，直接复制值
      if (column.type === 'image') {
        // 图片类型：特殊处理数组
        // 1. 先标记原图片为删除
        const deletedImages = markOriginalImagesAsDeleted(props.data[rowIndex][field])
        // 2. 处理要粘贴的新图片
        const newImages = processImageArrayForPaste(cellData.value)
        // 3. 合并删除标记的原图片和新图片
        const mergedImages = [...deletedImages, ...newImages]
        
        const newData = props.data.map((row, idx) => {
          if (idx === rowIndex) {
            return { ...row, [field]: mergedImages }
          }
          return row
        })
        emit('update:data', newData)
        emit('image-update', rowIndex, field, mergedImages)
      } else {
        // 非图片类型
        const newData = props.data.map((row, idx) => {
          if (idx === rowIndex) {
            return { ...row, [field]: cellData.value }
          }
          return row
        })
        emit('update:data', newData)
        emit('cell-update', rowIndex, field, cellData.value)
      }
    } else if (cellData && cellData.type !== column.type) {
      // 类型不匹配，忽略粘贴
      console.log('类型不匹配，忽略粘贴操作')
      return
    } else {
      // 没有自定义数据，使用普通文本粘贴（兼容外部复制）
      const pasteData = event.clipboardData?.getData('text/plain') || ''
      if (pasteData !== undefined && pasteData !== null && pasteData !== '') {
        if (column.type === 'number') {
          const num = Number(pasteData)
          if (!isNaN(num)) {
            handleInputUpdate(rowIndex, field, num)
          }
        } else if (column.type === 'select' && column.options) {
          // 对于 select 类型，尝试通过 label 或 value 匹配
          const option = column.options.find(opt => opt.label === pasteData || String(opt.value) === pasteData)
          if (option) {
            handleInputUpdate(rowIndex, field, option.value)
          } else {
            // 如果没有匹配的选项，直接使用粘贴的值
            handleInputUpdate(rowIndex, field, pasteData)
          }
        } else if (column.type === 'image') {
          // 图片类型不支持从普通文本粘贴
          console.log('图片列不支持从文本粘贴')
        } else {
          handleInputUpdate(rowIndex, field, pasteData)
        }
      } else {
        // 如果粘贴数据为空，清空单元格
        if (column.type === 'image') {
          const newData = props.data.map((row, idx) => {
            if (idx === rowIndex) {
              return { ...row, [field]: [] }
            }
            return row
          })
          emit('update:data', newData)
          emit('image-update', rowIndex, field, [])
        } else if (column.type === 'number') {
          handleInputUpdate(rowIndex, field, null)
        } else {
          handleInputUpdate(rowIndex, field, '')
        }
      }
    }
  }
}

// ==================== 生命周期 ====================
onMounted(() => {
  // 监听复制粘贴事件
  document.addEventListener('copy', handleCopy)
  document.addEventListener('paste', handlePaste)
})

onBeforeUnmount(() => {
  // 清理事件监听
  document.removeEventListener('copy', handleCopy)
  document.removeEventListener('paste', handlePaste)
})

/**
 * 上传指定行的图片字段
 */
const uploadRowImageField = async (rowIndex: number, field: string): Promise<void> => {
  const refKey = `${rowIndex}-${field}`
  const imagePlusRef = imagePlusRefsMap.get(refKey)
  if (imagePlusRef?.uploadPendingImages) {
    await imagePlusRef.uploadPendingImages()
  }
}

// ==================== 暴露方法 ====================
defineExpose({
  startEdit,
  endEdit,
  selectCell,
  selectRow,
  setCurrentRow,
  uploadRowImageField
})
</script>

<template>
  <ElTable
    ref="tableRef"
    :data="props.data"
    border
    class="table-plus"
    :row-class-name="({ rowIndex }: any) => effectiveRowIndex === rowIndex ? 'current-row' : ''"
    @cell-click="handleCellClick"
    @cell-dblclick="handleCellDblclick"
  >
    <!-- 序号列 -->
    <ElTableColumn
      type="index"
      :index="(index: number) => index + 1"
      width="40"
      align="center"
      label=""
    >
      <template #default="scope">
        <div class="row-index-cell">
          <span v-if="effectiveRowIndex === scope.$index" class="row-index-pointer">
            <!-- 右箭头图标 -->
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
              style="display: block;"
            >
              <path
                d="M9 6L15 12L9 18"
                :stroke="CURRENT_ROW_COLOR"
                stroke-width="2.5"
                stroke-linecap="round"
                stroke-linejoin="round"
                fill="none"
              />
            </svg>
          </span>
          <span v-else class="row-index-number">{{ scope.$index + 1 }}</span>
        </div>
      </template>
    </ElTableColumn>
    
    <!-- 数据列 -->
    <ElTableColumn
      v-for="column in props.columns.filter(col => col.show !== false)"
      :key="column.field"
      :prop="column.field"
      :label="column.label"
      :width="column.width"
      :min-width="column.minWidth"
      align="center"
    >
      <template #header>
        <span>
          {{ column.label }}
          <span v-if="column.required" style="color: #f56c6c; margin-left: 2px;">*</span>
        </span>
      </template>
      <template #default="scope">
        <!-- 图片列：使用 ImagePlus 组件 -->
        <div
          v-if="column.type === 'image' && column.editable !== false"
          :key="getImagePlusKey(scope.$index, column.field)"
          :data-cell-key="`${scope.$index}-${column.field}`"
          class="table-plus-image"
          tabindex="0"
          @click="handleImageCellClick(scope.$index, column.field, $event)"
          @keydown="handleCellKeydown($event, scope.row, { property: column.field })"
        >
          <ImagePlus
            :ref="(el: any) => setImagePlusRef(scope.$index, column.field, el)"
            :model-value="scope.row[column.field] || []"
            @update:model-value="(val: any[]) => handleImageUpdate(scope.$index, column.field, val)"
            :disabled="false"
            :limit="10"
            :size="column.size || 'small'"
          />
        </div>
        
        <!-- 编辑模式：数字输入框 -->
        <ElInputNumber
          v-else-if="isEditing(scope.$index, column.field) && column.editable !== false && column.type === 'number'"
          :key="`input-number-${scope.$index}-${column.field}`"
          :ref="(el: any) => setInputRef(scope.$index, column.field, el)"
          :data-cell-key="`${scope.$index}-${column.field}`"
          v-model="scope.row[column.field]"
          size="small"
          :controls="false"
          class="table-plus-input table-plus-input-number"
          :style="{ textAlign: 'left' }"
          @keydown.stop="handleInputKeydown($event, scope.$index, column.field)"
          @focus="handleInputFocus(scope.$index, column.field)"
          @blur="handleInputBlur($event, scope.$index, column.field)"
          @input="handleInputInput(scope.$index, column.field)"
        />
        
        <!-- 编辑模式：下拉选择 -->
        <ElSelect
          v-else-if="isEditing(scope.$index, column.field) && column.editable !== false && column.type === 'select' && column.options"
          :key="`select-${scope.$index}-${column.field}`"
          :ref="(el: any) => setInputRef(scope.$index, column.field, el)"
          :data-cell-key="`${scope.$index}-${column.field}`"
          v-model="scope.row[column.field]"
          size="small"
          class="table-plus-select"
          popper-class="table-plus-select-dropdown"
          :style="{ width: '100%', minWidth: '100%', maxWidth: '100%', display: 'block' }"
          :disabled="column.selectProps?.disabled ?? false"
          :readonly="column.selectProps?.readonly"
          :clearable="column.selectProps?.clearable"
          :filterable="column.selectProps?.filterable ?? false"
          :allow-create="column.selectProps?.allowCreate ?? false"
          v-bind="column.selectProps || {}"
          @keydown.stop="handleInputKeydown($event, scope.$index, column.field)"
          @focus="handleInputFocus(scope.$index, column.field)"
          @blur="handleInputBlur($event, scope.$index, column.field)"
          @visible-change="(visible: boolean) => handleSelectVisibleChange(visible, scope.$index, column.field)"
        >
          <ElOption
            v-for="opt in column.options"
            :key="opt.value"
            :label="opt.label"
            :value="opt.value"
          />
        </ElSelect>
        
        <!-- 编辑模式：多行文本输入框 -->
        <ElInput
          v-else-if="isEditing(scope.$index, column.field) && column.editable !== false && column.type === 'text'"
          :key="`textarea-${scope.$index}-${column.field}`"
          :ref="(el: any) => setInputRef(scope.$index, column.field, el)"
          :data-cell-key="`${scope.$index}-${column.field}`"
          v-model="scope.row[column.field]"
          type="textarea"
          resize="none"
          size="small"
          class="table-plus-input table-plus-textarea"
          @keydown.stop="handleInputKeydown($event, scope.$index, column.field)"
          @focus="handleInputFocus(scope.$index, column.field)"
          @blur="handleInputBlur($event, scope.$index, column.field)"
          @input="handleInputInput(scope.$index, column.field)"
          @update:model-value="handleInputUpdate(scope.$index, column.field, $event)"
        />
        
        <!-- 编辑模式：单行文本输入框 -->
        <ElInput
          v-else-if="isEditing(scope.$index, column.field) && column.editable !== false"
          :key="`input-${scope.$index}-${column.field}`"
          :ref="(el: any) => setInputRef(scope.$index, column.field, el)"
          :data-cell-key="`${scope.$index}-${column.field}`"
          v-model="scope.row[column.field]"
          size="small"
          class="table-plus-input"
          @keydown.stop="handleInputKeydown($event, scope.$index, column.field)"
          @focus="handleInputFocus(scope.$index, column.field)"
          @blur="handleInputBlur($event, scope.$index, column.field)"
          @input="handleInputInput(scope.$index, column.field)"
          @update:model-value="handleInputUpdate(scope.$index, column.field, $event)"
        />
        
        <!-- 显示模式 -->
        <span 
          v-else
          :data-cell-key="`${scope.$index}-${column.field}`"
          class="table-plus-cell"
          :class="{ 
            'cell-focused': isEditing(scope.$index, column.field),
            'cell-number': column.type === 'number',
            'cell-text': column.type !== 'number',
            'cell-text-multiline': column.type === 'text'
          }"
          @keydown="column.editable !== false && handleCellKeydown($event, scope.row, { property: column.field })"
          tabindex="0"
        >{{ formatCellValue(scope.row[column.field], column) }}</span>
      </template>
    </ElTableColumn>
    
    <!-- 删除按钮列 -->
    <ElTableColumn
      v-if="props.showDeleteButton"
      label=""
      width="40"
      align="center"
      fixed="right"
    >
      <template #default="scope">
        <div
          class="action-delete"
          :class="{ 'action-delete-current': effectiveRowIndex === scope.$index }"
          @click.stop="handleDeleteRow(scope.$index)"
        >
          <ElIcon :size="16">
            <Delete />
          </ElIcon>
        </div>
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

.absolute-fill-cell() {
  position: absolute !important;
  top: 0 !important;
  left: -1px !important;
  right: -1px !important;
  bottom: 0 !important;
  width: calc(100% + 2px) !important;
  min-width: calc(100% + 2px) !important;
  max-width: calc(100% + 2px) !important;
  height: 100% !important;
  min-height: 100% !important;
  max-height: 100% !important;
}

// ==================== 表格基础样式 ====================
:deep(.table-plus) {
  .el-table__cell {
    padding: 4px !important;
    position: relative;
    min-height: 32px;
    vertical-align: middle !important;
    
    &:hover {
      background-color: #f5f7fa;
    }
  }
  
  // 序号列样式
  .el-table__cell:first-child {
    background-color: #fafafa;
    font-weight: 600;
    border-right: 2px solid #e8e8e8;
    padding: 0 !important;
    cursor: pointer !important; // 整个单元格区域都是手指指针
    
    // 确保 .cell 容器和所有子元素都是 pointer 光标
    .cell {
      cursor: pointer !important;
    }
    
    * {
      cursor: pointer !important;
    }
  }
  
  // 表头样式
  .el-table__header th {
    background-color: #fafafa;
    font-weight: 600;
    border-bottom: 2px solid #e8e8e8;
    text-align: center !important;
  }
  
  // 数据单元格的鼠标样式（Excel 风格）- 非编辑模式下整个单元格都显示单元格光标
  tbody .el-table__cell:not(:first-child):not(:last-child):not(.editing-cell) {
    cursor: cell !important;
    
    // 确保 .cell 容器也使用 cell 光标
    :deep(.cell) {
      cursor: cell !important;
    }
    
    // 确保单元格内的所有元素也继承光标样式（非编辑模式）
    // 排除编辑组件
    *:not(input):not(textarea):not(.el-select):not(.el-input):not(.el-input-number):not(.el-select__wrapper) {
      cursor: cell !important;
    }
  }
  
  // 编辑中的单元格样式
  .el-table__cell.editing-cell {
    padding: 0 !important;
    overflow: visible !important;
    position: relative !important;
    // 编辑模式下，使用编辑组件自身的光标，不强制设置
    cursor: default !important;
    
    :deep(.cell) {
      padding: 0 !important;
      margin: 0 !important;
      position: static !important;
    }
    
    // 编辑组件内部使用自己的光标（text 光标）
    :deep(input),
    :deep(textarea) {
      cursor: text !important;
    }
    
    // Select 组件使用默认光标
    :deep(.el-select) {
      cursor: default !important;
    }
  }
}

// ==================== 序号列样式 ====================
.row-index-cell {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  
  // 确保所有子元素都继承 pointer 光标
  * {
    cursor: pointer;
  }
}

.row-index-pointer {
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  
  // 确保 SVG 和 path 元素也继承 pointer 光标
  svg,
  svg path {
    cursor: pointer;
  }
}

.row-index-number {
  font-size: 12px;
  color: #606266;
  cursor: pointer;
}

// 当前行的首尾列前景色为绿色（和选中边框一样的颜色）
:deep(.el-table__body) {
  tbody tr.current-row {
    // 序号列（第一列）
    .el-table__cell:first-child {
      .row-index-cell {
        .row-index-pointer,
        .row-index-number {
          color: rgb(16, 153, 104) !important; // 和选中边框一样的绿色
        }
      }
    }
    
    // Action 列（最后一列）
    .el-table__cell:last-child {
      .action-delete {
        color: rgb(16, 153, 104) !important; // 和选中边框一样的绿色
        
        &:hover {
          color: #f56c6c !important; // hover 时保持红色
        }
      }
    }
  }
}

// ==================== 单元格显示样式 ====================
.table-plus-cell {
  display: block;
  width: 100% !important;
  min-width: 100% !important;
  max-width: 100% !important;
  flex: 1 1 auto !important; // 占满 flex 容器
  padding: 4px 5px;
  word-break: break-word;
  white-space: pre-wrap;
  cursor: cell !important; // Excel 风格的单元格光标
  box-sizing: border-box !important;
  // 确保文本也使用 cell 光标，而不是 text 光标
  user-select: none; // 防止文本选择时显示 text 光标
  // 隐藏焦点时的边框（使用选中状态的绿色边框代替）
  outline: none !important;
  border: none !important;
  
  &:focus {
    outline: none !important;
    border: none !important;
  }
  
  &.cell-number {
    text-align: left;
  }
  
  &.cell-text {
    text-align: left;
  }
  
  &.cell-text-multiline {
    max-height: 4.8em;
    overflow: hidden;
    text-overflow: ellipsis;
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
  }
  
  &.cell-focused {
    outline: 2px solid rgb(16, 153, 104);
    outline-offset: -2px;
  }
}

// ==================== 编辑组件样式 ====================
.table-plus-select {
  width: 100% !important;
  min-width: 100% !important;
  max-width: 100% !important;
  
  :deep(.el-select__wrapper) {
    .fill-container();
    .remove-border-bg();
    padding: 0 4px !important;
    display: flex !important;
    align-items: center !important;
    
    &:hover, &:focus, &:focus-within, &.is-focus {
      .remove-border-bg();
    }
  }
  
  :deep(.el-select__selected-item) {
    flex: 1 !important;
    padding: 0 !important;
    line-height: normal !important;
  }
  
  :deep(.el-select__placeholder) {
    flex: 1 !important;
    padding: 0 !important;
  }
  
  :deep(.el-select__caret) {
    flex-shrink: 0 !important;
  }
}

.table-plus-input {
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
    
    &:hover, &:focus {
      .remove-border-bg();
    }
  }
  
  :deep(.el-input-number__decrease),
  :deep(.el-input-number__increase) {
    display: none !important;
  }
}

.table-plus-textarea {
  .absolute-fill-cell();
  display: block !important;
  z-index: 10 !important;
  
  :deep(.el-textarea) {
    .absolute-fill-cell();
    display: block !important;
    padding: 0 !important;
    margin: 0 !important;
  }
  
  :deep(.el-textarea__inner) {
    .absolute-fill-cell();
    .remove-border-bg();
    padding: 4px 5px !important;
    margin: 0 !important;
    resize: none !important;
    overflow-y: auto !important;
    overflow-x: hidden !important;
    box-sizing: border-box !important;
    
    &:hover, &:focus, &:active {
      .remove-border-bg();
    }
  }
}

// ==================== 图片列样式 ====================
.table-plus-image {
  position: relative !important;
  width: 100% !important;
  min-width: 100% !important;
  max-width: none !important;
  height: auto !important;
  min-height: auto !important;
  margin: 0 !important;
  padding: 4px !important;
  display: block !important;
  box-sizing: border-box !important;
  cursor: cell !important; // Excel 风格的单元格光标
  // 隐藏焦点时的边框（使用选中状态的绿色边框代替）
  outline: none !important;
  border: none !important;
  
  &:focus {
    outline: none !important;
    border: none !important;
  }
  overflow: visible !important;
  background: transparent !important;
  
  // 阻止 ImagePlus 组件内部元素接收 Tab 键焦点
  :deep(*) {
    // 将所有可聚焦元素设置为不可通过 Tab 键聚焦
    &[tabindex]:not([tabindex="-1"]) {
      tabindex: -1;
    }
    // 对于按钮、链接等元素，也设置为不可聚焦
    button,
    a,
    input,
    select,
    textarea {
      tabindex: -1;
    }
  }
}

:deep(.el-table__body tbody tr:has(.table-plus-image)) {
  height: auto !important;
  max-height: none !important;
}

:deep(.el-table__cell:has(.table-plus-image)) {
  height: auto !important;
  max-height: none !important;
  min-height: 32px !important;
  white-space: normal !important;
}

// ==================== 删除按钮样式 ====================
.action-delete {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  cursor: pointer;
  color: inherit;
  transition: color 0.2s ease;
  
  &:hover {
    color: #f56c6c;
  }
  
  &.action-delete-current {
    color: #409eff;
    
    &:hover {
      color: #f56c6c;
    }
  }
  
  :deep(.el-icon) {
    color: inherit;
  }
}
</style>

<style lang="less">
// ==================== 全局样式 ====================
.table-plus {
  // 强制覆盖 Element Plus .cell 的 padding
  .el-table__header .el-table__cell .cell {
    padding: 0 !important;
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
  }
  
  // 序号列的 .cell 容器和所有子元素都应该是 pointer 光标
  tbody .el-table__cell:first-child {
    cursor: pointer !important;
    
    .cell {
      cursor: pointer !important;
    }
    
    * {
      cursor: pointer !important;
    }
  }
  
  // 数据单元格的光标样式（Excel 风格）- 非编辑模式
  tbody .el-table__cell:not(:first-child):not(:last-child):not(.editing-cell) {
    cursor: cell !important;
    
    // 确保 .cell 容器也使用 cell 光标
    .cell {
      cursor: cell !important;
    }
    
    // 确保 .table-plus-cell 也使用 cell 光标
    .table-plus-cell {
      cursor: cell !important;
    }
  }
  
  // 强制移除编辑组件边框和背景
  .el-input__wrapper,
  .el-select__wrapper,
  .el-input-number__wrapper,
  .el-textarea__inner {
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
  
  // 单元格选中时的边框样式（使用伪元素，避免影响布局）
  .el-table__cell {
    position: relative;
    
    &.selected-cell::after {
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      border: 2px solid rgb(16, 153, 104); // Green border
      pointer-events: none; // Allow clicks to pass through
      box-sizing: border-box;
      z-index: 1;
    }
  }
  
  // 行选中时，该行的数据单元格（排除序号列和Action列）添加绿色边框
  // 形成一个整体的边框框住所有数据单元格
  tbody tr.selected-row {
    position: relative;
    
    // 所有数据单元格：添加上边框和下边框
    .el-table__cell:not(:first-child):not(:last-child) {
      position: relative !important;
      
      &::before {
        content: '' !important;
        position: absolute !important;
        top: 0 !important;
        left: 0 !important;
        right: 0 !important;
        height: 2px !important;
        background-color: rgb(16, 153, 104) !important; // Green border (上边框)
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
        background-color: rgb(16, 153, 104) !important; // Green border (下边框)
        pointer-events: none !important;
        z-index: 1 !important;
      }
    }
    
    // 第一个数据单元格：添加左边框（使用 box-shadow，因为 ::before 已被上边框占用）
    .el-table__cell:nth-child(2) {
      position: relative !important;
      
      // 左边框
      box-shadow: -2px 0 0 0 rgb(16, 153, 104) !important;
      
      // 上边框（确保第一个单元格也有上边框）
      &::before {
        content: '' !important;
        position: absolute !important;
        top: 0 !important;
        left: 0 !important;
        right: 0 !important;
        height: 2px !important;
        background-color: rgb(16, 153, 104) !important; // Green border (上边框)
        pointer-events: none !important;
        z-index: 1 !important;
      }
      
      // 下边框（确保第一个单元格也有下边框）
      &::after {
        content: '' !important;
        position: absolute !important;
        bottom: 0 !important;
        left: 0 !important;
        right: 0 !important;
        height: 2px !important;
        background-color: rgb(16, 153, 104) !important; // Green border (下边框)
        pointer-events: none !important;
        z-index: 1 !important;
      }
    }
    
    // 最后一个数据单元格：添加右边框（使用 box-shadow，因为 ::after 已被下边框占用）
    .el-table__cell:nth-last-child(2) {
      position: relative !important;
      
      // 右边框
      box-shadow: 2px 0 0 0 rgb(16, 153, 104) !important;
      
      // 上边框（确保最后一个单元格也有上边框）
      &::before {
        content: '' !important;
        position: absolute !important;
        top: 0 !important;
        left: 0 !important;
        right: 0 !important;
        height: 2px !important;
        background-color: rgb(16, 153, 104) !important; // Green border (上边框)
        pointer-events: none !important;
        z-index: 1 !important;
      }
      
      // 下边框（确保最后一个单元格也有下边框）
      &::after {
        content: '' !important;
        position: absolute !important;
        bottom: 0 !important;
        left: 0 !important;
        right: 0 !important;
        height: 2px !important;
        background-color: rgb(16, 153, 104) !important; // Green border (下边框)
        pointer-events: none !important;
        z-index: 1 !important;
      }
    }
  }
}

// 下拉菜单样式（teleported 到 body）
.table-plus-select-dropdown {
  min-width: fit-content !important;
  
  .el-select-dropdown__wrap {
    width: 100% !important;
  }
  
  .el-select-dropdown__list {
    width: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
  }
  
  .el-select-dropdown__item {
    width: 100% !important;
    padding: 8px 12px;
    white-space: nowrap;
    box-sizing: border-box;
    margin: 0 !important;
  }
}
</style>

