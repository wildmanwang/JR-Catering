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
  /** 默认行数据（用于新增行时，如果未提供 defaultRow 参数） */
  defaultRow?: any
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
  (e: 'row-add', payload: { defaultRow: any; insertIndex?: number }): void
  (e: 'column-add', payload: { field: string; colDefine: TablePlusColumn; insertIndex?: number }): void
  (e: 'column-delete', field: string): void
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
/** 当前行索引（当前聚焦的行） */
const currentRowIndex = ref<number | null>(props.currentRowIndex ?? null)

/** 选中的行索引数组（用于 Ctrl/Shift 多选，有绿色边框的行） */
const selectedRowIndices = ref<number[]>([])

/** 上次选中的行索引（用于 Shift 范围选择） */
const lastSelectedRowIndex = ref<number | null>(null)

/** 当前行索引（computed，优先使用编辑状态，否则使用选中状态） */
const effectiveRowIndex = computed(() => {
  // 优先使用编辑状态的单元格所在行
  if (editingCell.value?.rowIndex !== undefined && editingCell.value?.rowIndex !== null) {
    return editingCell.value.rowIndex
  }
  // 否则使用当前行索引
  return currentRowIndex.value
})

// 监听 props.currentRowIndex 的变化，同步到内部状态
watch(
  () => props.currentRowIndex,
  (newVal) => {
    if (newVal !== currentRowIndex.value) {
      currentRowIndex.value = newVal
    }
  },
  { immediate: true }
)

// ==================== ImagePlus 引用管理 ====================
/** ImagePlus 组件引用映射 */
const imagePlusRefsMap = new Map<string, InstanceType<typeof ImagePlus>>()

/**
 * 设置 ImagePlus 组件引用
 * @param rowIndex 行索引
 * @param field 字段名
 * @param el 组件实例
 */
const setImagePlusRef = (rowIndex: number, field: string, el: any) => {
  delayExecute(() => {
    const refKey = `${rowIndex}-${field}`
    el ? imagePlusRefsMap.set(refKey, el) : imagePlusRefsMap.delete(refKey)
  }, 0)
}

// ==================== 输入组件引用管理 ====================
/** 输入组件引用映射（用于直接访问组件实例的 focus 方法） */
const inputRefsMap = new Map<string, any>()

/** 输入元素键盘事件监听器映射（用于清理事件监听器） */
// 注意：不再需要 inputKeydownListenersMap
// Tab 和 Escape 键的处理已统一由全局事件监听器 handleGlobalKeydown 处理

// 注意：不再需要 findActualInputElement、attachInputKeydownListener 和 attachListenerToInput
// Tab 和 Escape 键的处理已统一由全局事件监听器 handleGlobalKeydown 处理

/** 设置输入组件引用 */
const setInputRef = (rowIndex: number, field: string, el: any) => {
  const refKey = `${rowIndex}-${field}`
  
  if (el) {
    inputRefsMap.set(refKey, el)
    
    // 注意：不再需要手动添加事件监听器
    // Tab 和 Escape 键的处理已统一由全局事件监听器 handleGlobalKeydown 处理
  } else {
    inputRefsMap.delete(refKey)
    
    // 注意：不再需要清理手动添加的事件监听器
    // Tab 和 Escape 键的处理已统一由全局事件监听器 handleGlobalKeydown 处理
  }
}

// ==================== 辅助常量 ====================
const CURRENT_ROW_COLOR = '#409EFF'

// ==================== 工具函数 ====================
/**
 * 深拷贝对象
 * @param obj 要拷贝的对象
 * @returns 深拷贝后的新对象
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
 * 延迟执行函数（用于 DOM 更新后的操作）
 * @param callback 要执行的函数
 * @param delay 延迟时间（毫秒），默认 10ms
 */
const delayExecute = (callback: () => void, delay: number = 10) => {
  setTimeout(callback, delay)
}

/**
 * 更新指定单元格的数据
 * @param rowIndex 行索引
 * @param field 字段名
 * @param value 新值
 */
const updateCellData = (rowIndex: number, field: string, value: any) => {
  const newData = props.data.map((row, idx) => {
    if (idx === rowIndex) {
      return { ...row, [field]: value }
    }
    return row
  })
  emit('update:data', newData)
  
  const col = props.columns.find(c => c.field === field)
  if (col?.type === 'image') {
    emit('image-update', rowIndex, field, value)
  } else {
    emit('cell-update', rowIndex, field, value)
  }
}

/**
 * 处理普通文本粘贴（兼容外部复制）
 * @param pasteData 粘贴的文本数据
 * @param rowIndex 行索引
 * @param field 字段名
 * @param column 列配置
 */
const handlePlainTextPaste = (pasteData: string, rowIndex: number, field: string, column: TablePlusColumn) => {
  if (!pasteData) return
  
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
    // 图片类型不支持从普通文本粘贴，忽略
  } else {
    handleInputUpdate(rowIndex, field, pasteData)
  }
}

/**
 * 打开 Select 下拉框（用于双击 select 列时自动展开）
 * @param rowIndex 行索引
 * @param field 字段名
 * @param refKey ref 键值
 */
const openSelectDropdown = (rowIndex: number, field: string, refKey: string) => {
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
      delayExecute(() => {
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
  }
}

/**
 * 处理自定义格式的粘贴数据
 * @param cellData 自定义格式的单元格数据
 * @param rowIndex 行索引
 * @param field 字段名
 * @param column 列配置
 * @returns 是否成功处理
 */
const handleCustomDataPaste = (cellData: any, rowIndex: number, field: string, column: TablePlusColumn): boolean => {
  if (cellData.type !== column.type) {
    // 类型不匹配，忽略粘贴
    return false
  }
  
  if (column.type === 'image') {
    // 图片类型：特殊处理数组
    // 1. 先标记原图片为删除
    const deletedImages = markOriginalImagesAsDeleted(props.data[rowIndex]?.[field] || [])
    // 2. 处理要粘贴的新图片
    const newImages = processImageArrayForPaste(cellData.value)
    // 3. 合并删除标记的原图片和新图片
    const mergedImages = [...deletedImages, ...newImages]
    updateCellData(rowIndex, field, mergedImages)
  } else {
    // 非图片类型
    updateCellData(rowIndex, field, cellData.value)
  }
  
  return true
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
 * 内部辅助函数：取消选择单元格（不返回结果，用于内部调用）
 */
const _deselectCellInternal = (): void => {
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
    tableEl.querySelectorAll('.table-plus-cell, .table-plus-image').forEach((el: HTMLElement) => {
      el.blur()
    })
  }
}

/**
 * 进入编辑（接口函数）
 * @param row 行索引，从0开始
 * @param field 字段名
 * @param options 可选配置
 * @returns [code, message] code=1表示成功，code=-1表示失败
 */
const startEdit = (row: number, field: string, options?: { isKeyboardInput?: boolean; inputValue?: string }): [number, string] => {
  // 参数校验
  if (row < 0 || row >= props.data.length) {
    return [-1, `行号${row}无效`]
  }
  
  const col = props.columns.find(c => c.field === field)
  if (!col || col.show === false) {
    return [-1, `列${field}无效`]
  }
  
  if (col.editable === false) {
    return [-1, `列${field}不可编辑`]
  }
  
  if (col.type === 'image') {
    return [-1, '图片列不支持编辑']
  }
  
  // 检查当前选中单元格是否与目标单元格一致
  const selectedCell = document.querySelector('.el-table__cell.selected-cell') as HTMLElement
  if (selectedCell) {
    const rowElement = selectedCell.closest('tr')
    if (rowElement) {
      const tbody = rowElement.parentElement
      if (tbody) {
        const rows = Array.from(tbody.querySelectorAll('tr'))
        const actualRowIndex = rows.indexOf(rowElement)
        if (actualRowIndex !== row) {
          return [-1, '目标单元格未选中']
        }
        
        const visibleColumns = props.columns.filter(col => col.show !== false)
        const cellIndex = Array.from(rowElement.children).indexOf(selectedCell)
        if (cellIndex > 0 && cellIndex <= visibleColumns.length) {
          const actualField = visibleColumns[cellIndex - 1].field
          if (actualField !== field) {
            return [-1, '目标单元格未选中']
          }
        }
      }
    }
  } else {
    // 如果没有选中单元格，允许直接进入编辑（兼容某些场景）
    // 但需要先选中单元格
    const [selectCode, selectMsg] = selectCell(row, field)
    if (selectCode !== 1) {
      return [selectCode, selectMsg]
    }
  }
  
  // 如果已经在编辑这个单元格，不做任何操作
  if (isEditing(row, field)) {
    return [1, '就绪']
  }
  
  editingCell.value = { rowIndex: row, field }
  
  // 等待 DOM 更新后聚焦输入框
  // 使用双重 nextTick + requestAnimationFrame + setTimeout 确保 DOM 完全更新
  nextTick(() => {
    nextTick(() => {
      requestAnimationFrame(() => {
        // 再使用 setTimeout 确保浏览器完成渲染
        setTimeout(() => {
          const refKey = `${row}-${field}`
          
          // 首先尝试通过 ref 访问组件实例
          const componentRef = inputRefsMap.get(refKey)
          if (componentRef) {
            // 如果组件有 focus 方法，直接调用
            if (typeof componentRef.focus === 'function') {
              componentRef.focus()
              
              // 等待焦点设置完成后再设置光标位置
              delayExecute(() => {
                const cellKey = `${row}-${field}`
                const inputElement = document.querySelector(`[data-cell-key="${cellKey}"]`) as HTMLElement
                if (inputElement) {
                  const actualInput = inputElement.querySelector('input, textarea') as HTMLInputElement | HTMLTextAreaElement
                  if (actualInput && document.activeElement === actualInput) {
                    setCursorPosition(actualInput, col, options)
                  }
                }
                
                // 注意：不再需要手动添加事件监听器，全局监听器已处理 Tab 和 Escape 键
              })
              return
            }
            
            // 如果组件有 input 属性（ElInput 组件），访问其内部的 input 元素
            if (componentRef.input) {
              const actualInput = componentRef.input as HTMLInputElement | HTMLTextAreaElement
              if (actualInput) {
                actualInput.focus()
                setCursorPosition(actualInput, col, options)
                // 注意：不再需要手动添加事件监听器，全局监听器已处理 Tab 和 Escape 键
                return
              }
            }
          }
          
          // 如果 ref 方法失败，回退到 DOM 查询方法
          const cellKey = `${row}-${field}`
          const inputElement = document.querySelector(`[data-cell-key="${cellKey}"]`) as HTMLElement
          if (!inputElement) {
            return
          }
          
          // 对于 select 列，需要特殊处理：打开下拉框
          if (col.type === 'select') {
            // 等待 DOM 完全渲染后再打开下拉框
            delayExecute(() => {
              openSelectDropdown(row, field, refKey)
              // 添加键盘事件监听器
              // 注意：不再需要手动添加事件监听器，全局监听器已处理 Tab 和 Escape 键
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
          
          // 注意：不再需要手动添加事件监听器，全局监听器已处理 Tab 和 Escape 键
        }) // 延迟确保浏览器完成渲染
      })
    })
  })
  
  return [1, '就绪']
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
 * 内部辅助函数：退出编辑状态（不返回结果，用于内部调用）
 * @param shouldValidate 是否校验数据
 * @param shouldSelect 是否选中当前单元格
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
          currentRowIndex.value = rowIndex
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
 * 退出编辑（接口函数）
 * @param row 行索引，从0开始
 * @param field 字段名
 * @param shouldValidate 是否校验数据，默认true
 * @returns [code, message] code=1表示成功，code=-1表示失败
 */
const exitEdit = (row: number, field: string, shouldValidate: boolean = true): [number, string] => {
  // 如果当前没有单元格处于编辑状态，直接返回成功
  if (!editingCell.value) {
    return [1, '就绪']
  }
  
  // 参数校验
  if (row < 0 || row >= props.data.length) {
    return [-1, `行号${row}无效`]
  }
  
  const col = props.columns.find(c => c.field === field)
  if (!col) {
    return [-1, `列${field}无效`]
  }
  
  // 检查当前编辑单元格是否与目标单元格一致
  const { rowIndex, field: currentField } = editingCell.value
  if (rowIndex !== row || currentField !== field) {
    return [-1, '目标单元格与编辑单元格不一致']
  }
  
  // 校验数据（如果需要）
  if (shouldValidate) {
    const currentValue = props.data[rowIndex]?.[field]
    const validateResult = validateCell(rowIndex, field, currentValue)
    
    // 校验失败，返回错误信息
    if (validateResult !== true && validateResult !== null) {
      const errorMsg = typeof validateResult === 'string' ? validateResult : '数据校验失败'
      return [-1, errorMsg]
    }
  }
  
  // 退出编辑状态并选中单元格
  const success = exitEditMode(shouldValidate, true)
  if (!success) {
    return [-1, '退出编辑失败']
  }
  
  return [1, '就绪']
}

/**
 * 退出单元格选中（接口函数）
 * @param row 行索引（可选，如果提供则只取消该行的单元格选中）
 * @param field 字段名（可选，如果提供则只取消该字段的单元格选中）
 * @returns [code, message] code=1表示成功，code=-1表示失败
 */
const deselectCell = (row?: number, field?: string): [number, string] => {
  const tableEl = tableRef.value?.$el as HTMLElement
  
  // 如果提供了row和field，只取消该单元格的选中
  if (row !== undefined && field !== undefined) {
    // 参数校验
    if (row < 0 || row >= props.data.length) {
      return [-1, `行号${row}无效`]
    }
    
    const col = props.columns.find(c => c.field === field)
    if (!col) {
      return [-1, `列${field}无效`]
    }
    
    // 如果该单元格正在编辑，退出编辑状态
    if (editingCell.value && editingCell.value.rowIndex === row && editingCell.value.field === field) {
      endEdit()
    }
    
    // 取消该单元格的选中状态
    if (tableEl) {
      const tbody = tableEl.querySelector('.el-table__body tbody')
      if (tbody) {
        const rows = Array.from(tbody.querySelectorAll('tr'))
        if (rows[row]) {
          const visibleColumns = props.columns.filter(col => col.show !== false)
          const fieldIndex = visibleColumns.findIndex(c => c.field === field)
          if (fieldIndex >= 0) {
            // 数据列从第2个开始（第1个是序号列）
            const cellIndex = fieldIndex + 1
            const cells = Array.from(rows[row].children)
            if (cells[cellIndex]) {
              cells[cellIndex].classList.remove('selected-cell')
              cells[cellIndex].classList.remove('editing-cell')
              const cellElement = cells[cellIndex].querySelector('.table-plus-cell, .table-plus-image') as HTMLElement
              if (cellElement) {
                cellElement.blur()
              }
            }
          }
        }
      }
    }
    
    return [1, '就绪']
  }
  
  // 如果没有提供参数，取消所有单元格的选中
  // 如果单元格处于编辑状态，则退出编辑状态
  if (editingCell.value) {
    endEdit()
  }
  
  // 单元格取消选中状态，并失去焦点
  if (tableEl) {
    // 移除所有单元格的选中状态和编辑状态
    tableEl.querySelectorAll('.el-table__cell.selected-cell').forEach(el => {
      el.classList.remove('selected-cell')
    })
    tableEl.querySelectorAll('.el-table__cell.editing-cell').forEach(el => {
      el.classList.remove('editing-cell')
    })
    
    // 移除所有单元格的聚焦状态（cell-focused 类）
    tableEl.querySelectorAll('.table-plus-cell.cell-focused').forEach(el => {
      el.classList.remove('cell-focused')
    })
    
    // 移除所有单元格的焦点（包括普通单元格和 image 列）
    tableEl.querySelectorAll('.table-plus-cell, .table-plus-image').forEach((el: HTMLElement) => {
      el.blur()
    })
  }
  
  return [1, '就绪']
}


/**
 * 选中行（接口函数）
 * @param row 行索引，从0开始
 * @param selectType 选择模式，默认'single'
 * @returns [code, message] code=1表示成功，code=-1表示失败
 */
const selectRow = (row: number, selectType: 'single' | 'ctrl' | 'shift' = 'single'): [number, string] => {
  // 参数校验
  if (row < 0 || row >= props.data.length) {
    return [-1, `行号${row}无效`]
  }
  
  // 单选模式下，如果目标行是唯一被选中的行，直接返回（避免重复操作）
  // 注意：如果有多行被选中，即使目标行在其中，也应该先取消其他行，再选中目标行
  if (selectType === 'single' && selectedRowIndices.value.length === 1 && selectedRowIndices.value[0] === row) {
    return [1, '就绪']
  }
  
  // 退出单元格选中（使用接口函数）
  const [deselectCellCode, deselectCellMsg] = deselectCell()
  if (deselectCellCode !== 1) {
    return [deselectCellCode, deselectCellMsg]
  }
  
  // 执行行选择操作
  const tableEl = tableRef.value?.$el as HTMLElement
  if (!tableEl) {
    return [-1, '表格元素不存在']
  }
  
  let rowsToSelect: number[] = []
  
  switch (selectType) {
    case 'single':
      // 单选：先取消所有其他行选择，再选中目标行
      // 使用接口函数确保一致性
      const [deselectRowCode, deselectRowMsg] = deselectRow()
      if (deselectRowCode !== 1) {
        return [deselectRowCode, deselectRowMsg]
      }
      
      // 选中目标行
      selectedRowIndices.value = [row]
      lastSelectedRowIndex.value = row
      rowsToSelect = [row]
      break
      
    case 'ctrl':
      // ctrl选：不取消其他行选择，增加选中当前行（如果已选中则取消选中）
      const currentIndex = selectedRowIndices.value.indexOf(row)
      if (currentIndex === -1) {
        selectedRowIndices.value.push(row)
        rowsToSelect = [...selectedRowIndices.value]
        lastSelectedRowIndex.value = row
      } else {
        selectedRowIndices.value.splice(currentIndex, 1)
        const tbody = tableEl.querySelector('.el-table__body tbody')
        if (tbody) {
          const rows = Array.from(tbody.querySelectorAll('tr'))
          if (rows[row]) {
            rows[row].classList.remove('selected-row')
          }
        }
        if (selectedRowIndices.value.length === 0) {
          lastSelectedRowIndex.value = null
          currentRowIndex.value = null
          emit('update:currentRowIndex', null)
          return [1, '就绪']
        } else {
          lastSelectedRowIndex.value = selectedRowIndices.value[selectedRowIndices.value.length - 1]
          rowsToSelect = [...selectedRowIndices.value]
        }
        if (rowsToSelect.length === 0) {
          return [1, '就绪']
        }
      }
      break
      
    case 'shift':
      // shift选：选中目标行到上次选中行之间的全部行
      if (lastSelectedRowIndex.value !== null) {
        const startRowIndex = lastSelectedRowIndex.value
        const endRowIndex = row
        const minRowIndex = Math.min(startRowIndex, endRowIndex)
        const maxRowIndex = Math.max(startRowIndex, endRowIndex)
        
        rowsToSelect = []
        for (let i = minRowIndex; i <= maxRowIndex; i++) {
          if (i >= 0 && i < props.data.length) {
            rowsToSelect.push(i)
          }
        }
        
        const newSelectedRows = [...new Set([...selectedRowIndices.value, ...rowsToSelect])]
        selectedRowIndices.value = newSelectedRows
      } else {
        selectedRowIndices.value = [row]
        rowsToSelect = [row]
      }
      lastSelectedRowIndex.value = row
      break
  }
  
  // 应用选中样式到需要选中的行
  nextTick(() => {
    nextTick(() => {
      rowsToSelect.forEach(rowIndex => {
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
  
  // 设置目标行为当前行
  if (selectType !== 'ctrl') {
    currentRowIndex.value = row
    emit('update:currentRowIndex', row)
  } else {
    if (rowsToSelect.length > 0 && rowsToSelect.includes(row)) {
      currentRowIndex.value = row
      emit('update:currentRowIndex', row)
    }
  }
  
  return [1, '就绪']
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
    const fromRowIndex = target.fromRowIndex ?? currentRowIndex.value ?? 0
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

const handleInputInput = (_rowIndex: number, _field: string) => {
  // 输入时的处理（如果需要）
}

const handleInputFocus = (rowIndex: number, field: string) => {
  // 聚焦时确保编辑状态
  if (!isEditing(rowIndex, field)) {
    startEdit(rowIndex, field) // 忽略返回值，只触发编辑
  }
}

/**
 * 处理输入框失焦事件
 * @param _event 焦点事件
 * @param _rowIndex 行索引
 * @param _field 字段名
 */
const handleInputBlur = (_event: FocusEvent, _rowIndex: number, _field: string) => {
  // 延迟执行，以便其他事件（如点击另一个单元格）先执行
  delayExecute(() => {
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
  // 检查点击的目标是否是删除按钮（删除按钮不应该选中单元格）
  const target = event.target as HTMLElement
  if (target && (target.classList.contains('remove-btn-normal') || target.classList.contains('remove-btn-small') || target.closest('.remove-btn-normal') || target.closest('.remove-btn-small'))) {
    // 点击的是删除按钮，不选中单元格，让删除功能正常执行
    return
  }
  
  // 使用 selectCell 接口函数选中该单元格
  selectCell(rowIndex, field)
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
// ==================== 列操作 ====================
/**
 * 新增列（接口函数）
 * @param field 字段名
 * @param colDefine 列定义对象
 * @param insertIndex 插入位置，从0开始。如果未提供或insertIndex<0，则在末尾追加；如果insertIndex>=0且<=最大列号，则在insertIndex前插入
 * @returns [code, message, newColIndex] code=1表示成功，code=-1表示失败
 */
const addColumn = async (field: string, colDefine: TablePlusColumn, insertIndex?: number): Promise<[number, string, number?]> => {
  // 参数校验
  if (!field || field.trim() === '') {
    return [-1, '字段名field无效']
  }
  
  // 检查字段名是否已存在
  if (props.columns.some(col => col.field === field)) {
    return [-1, `字段名${field}已存在`]
  }
  
  // 校验列定义
  if (!colDefine || typeof colDefine !== 'object') {
    return [-1, '列定义colDefine无效']
  }
  
  if (!colDefine.field || !colDefine.label) {
    return [-1, '列定义缺少必要属性（field或label）']
  }
  
  // 退出单元格选中
  const [deselectCode, deselectMsg] = deselectCell()
  if (deselectCode !== 1) {
    return [deselectCode, deselectMsg]
  }
  
  // 确定插入位置
  const visibleColumns = props.columns.filter(col => col.show !== false)
  let finalInsertIndex: number | undefined
  
  if (insertIndex === undefined || insertIndex < 0) {
    // 在末尾追加
    finalInsertIndex = undefined
  } else if (insertIndex >= 0 && insertIndex <= visibleColumns.length) {
    // 在insertIndex前插入
    finalInsertIndex = insertIndex
  } else {
    return [-1, `列号${insertIndex}无效`]
  }
  
  // 触发column-add事件
  emit('column-add', { field, colDefine, insertIndex: finalInsertIndex })
  
  // 等待父组件处理
  await nextTick()
  
  // 确定新增列的索引
  const newVisibleColumns = props.columns.filter(col => col.show !== false)
  const newColIndex = finalInsertIndex === undefined ? newVisibleColumns.length - 1 : finalInsertIndex
  
  return [1, '就绪', newColIndex]
}

/**
 * 删除列（接口函数）
 * @param field 字段名
 * @returns [code, message] code=1表示成功，code=-1表示失败
 */
const deleteColumn = async (field: string): Promise<[number, string]> => {
  // 参数校验
  const col = props.columns.find(c => c.field === field)
  if (!col) {
    return [-1, `字段名${field}无效`]
  }
  
  // 退出单元格选中
  const [deselectCode, deselectMsg] = deselectCell()
  if (deselectCode !== 1) {
    return [deselectCode, deselectMsg]
  }
  
  // 如果删除的列是当前选中单元格的列，清除选中状态
  if (editingCell.value && editingCell.value.field === field) {
    endEdit()
    currentRowIndex.value = null
    emit('update:currentRowIndex', null)
  }
  
  // 触发column-delete事件
  emit('column-delete', field)
  
  // 等待父组件处理
  await nextTick()
  
  return [1, '就绪']
}

// ==================== 单元格导航 ====================
/**
 * 导航到单元格（接口函数）
 * @param target 目标单元格配置
 * @param options 选项
 * @returns [code, message] code=1表示成功，code=-1表示失败
 */
const navigateToCell = (
  target: 
    | { rowIndex: number; field: string }
    | { direction: 'up' | 'down' | 'left' | 'right' | 'tab' | 'enter'; fromRowIndex?: number; fromField?: string },
  options: { validateCurrent?: boolean; allowAddRow?: boolean } = {}
): [number, string] => {
  const { validateCurrent = true, allowAddRow = true } = options
  
  // 处理编辑状态
  if (editingCell.value) {
    const success = exitEditMode(validateCurrent, false)
    if (!success) {
      return [-1, '退出编辑失败']
    }
  }
  
  // 计算目标单元格位置
  const targetCell = calculateTargetCell(target, allowAddRow)
  
  // 如果目标单元格不合法，返回错误
  if (!targetCell) {
    return [-1, '目标单元格无效']
  }
  
  const { rowIndex: targetRowIndex, field: targetField, shouldAddRow } = targetCell
  
  // 取消所有行选中和单元格选中
  const [deselectRowCode, deselectRowMsg] = deselectRow()
  if (deselectRowCode !== 1) {
    return [deselectRowCode, deselectRowMsg]
  }
  
  const [deselectCellCode, deselectCellMsg] = deselectCell()
  if (deselectCellCode !== 1) {
    return [deselectCellCode, deselectCellMsg]
  }
  
  // 如果目标单元格的行号大于最大行号且allowAddRow为true，则新增行
  if (shouldAddRow && allowAddRow) {
    const defaultRow: any = {}
    props.columns.forEach(col => {
      defaultRow[col.field] = col.type === 'number' ? null : (col.type === 'image' ? [] : '')
    })
    emit('row-add', { defaultRow, insertIndex: targetRowIndex })
  }
  
  // 选中目标单元格，并获得焦点
  // 如果新增了行，需要等待数据更新
  if (shouldAddRow || targetRowIndex >= props.data.length) {
    nextTick(() => {
      if (props.data.length > 0) {
        const actualRowIndex = props.data.length - 1
        applyCellSelection(actualRowIndex, targetField)
        currentRowIndex.value = actualRowIndex
        emit('update:currentRowIndex', actualRowIndex)
      }
    })
  } else {
    applyCellSelection(targetRowIndex, targetField)
    currentRowIndex.value = targetRowIndex
    emit('update:currentRowIndex', targetRowIndex)
  }
  
  return [1, '就绪']
}

/**
 * 应用单元格选中状态（内部辅助函数）
 * 注意：此函数只负责 DOM 操作和焦点设置，不负责更新 currentRowIndex（由调用方负责）
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
 * 取消选中行（接口函数）
 * @param row 行索引（可选，如果提供则只取消该行的选中状态）
 * @returns [code, message] code=1表示成功，code=-1表示失败
 */
const deselectRow = (row?: number): [number, string] => {
  const tableEl = tableRef.value?.$el as HTMLElement
  
  // 如果提供了row参数，只取消该行的选中状态
  if (row !== undefined) {
    // 参数校验
    if (row < 0 || row >= props.data.length) {
      return [-1, `行号${row}无效`]
    }
    
    // 从选中行数组中移除该行
    const index = selectedRowIndices.value.indexOf(row)
    if (index !== -1) {
      selectedRowIndices.value.splice(index, 1)
    }
    
    // 如果该行是当前行，清除当前行
    if (currentRowIndex.value === row) {
      currentRowIndex.value = null
      emit('update:currentRowIndex', null)
    }
    
    // 如果该行是上次选中的行，更新lastSelectedRowIndex
    if (lastSelectedRowIndex.value === row) {
      if (selectedRowIndices.value.length > 0) {
        lastSelectedRowIndex.value = selectedRowIndices.value[selectedRowIndices.value.length - 1]
      } else {
        lastSelectedRowIndex.value = null
      }
    }
    
    // 移除该行的DOM选中样式
    if (tableEl) {
      const tbody = tableEl.querySelector('.el-table__body tbody')
      if (tbody) {
        const rows = Array.from(tbody.querySelectorAll('tr'))
        if (rows[row]) {
          rows[row].classList.remove('selected-row')
        }
      }
    }
    
    return [1, '就绪']
  }
  
  // 如果没有提供参数，取消所有行的选中状态
  // 清除整行选中状态
  selectedRowIndices.value = []
  lastSelectedRowIndex.value = null
  currentRowIndex.value = null
  emit('update:currentRowIndex', null)
  
  // 清除行选中相关的 DOM 样式
  if (tableEl) {
    tableEl.querySelectorAll('tr.selected-row').forEach(el => {
      el.classList.remove('selected-row')
    })
  }
  
  return [1, '就绪']
}

/**
 * 取消选中当前行（接口函数，向后兼容）
 * @returns [code, message] code=1表示成功，code=-1表示失败
 */
const clearCurrentRow = (): [number, string] => {
  // 取消所有单元格选中
  const [cellCode, cellMsg] = deselectCell()
  if (cellCode !== 1) {
    return [cellCode, cellMsg]
  }
  
  // 取消所有行选中
  return deselectRow()
}

/**
 * 选中单元格（接口函数）
 * @param row 行索引，从0开始
 * @param field 字段名
 * @returns [code, message] code=1表示成功，code=-1表示失败
 */
const selectCell = (row: number, field: string): [number, string] => {
  // 参数校验
  if (row < 0 || row >= props.data.length) {
    return [-1, `行号${row}无效`]
  }
  
  const col = props.columns.find(c => c.field === field)
  if (!col || col.show === false || col.editable === false) {
    return [-1, `列${field}无效`]
  }
  
  // 退出当前编辑状态
  if (editingCell.value) {
    const success = exitEditMode(false, false)
    if (!success) {
      return [-1, '退出编辑失败']
    }
  }
  
  // 取消单元格选中和行选择
  const [deselectCellCode, deselectCellMsg] = deselectCell()
  if (deselectCellCode !== 1) {
    return [deselectCellCode, deselectCellMsg]
  }
  
  const [deselectRowCode, deselectRowMsg] = deselectRow()
  if (deselectRowCode !== 1) {
    return [deselectRowCode, deselectRowMsg]
  }
  
  // 选中目标单元格
  const [navCode, navMsg] = navigateToCell({ rowIndex: row, field }, { validateCurrent: false, allowAddRow: false })
  if (navCode !== 1) {
    return [navCode, navMsg]
  }
  
  return [1, '就绪']
}

/**
 * 更新选中行索引（基于当前选中的单元格）
 * 注意：此函数主要用于从 DOM 状态同步到内部状态，通常不需要手动调用
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
            currentRowIndex.value = rowIndex
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
/**
 * 设置当前行（接口函数）
 * @param row 行索引，如果提供且有效则设置当前行，如果为 null 或 undefined 则取消当前行
 * @returns [code, message] code=1表示成功，code=-1表示失败
 */
const setCurrentRow = (row: number | null | undefined): [number, string] => {
  // 如果 row 为 null 或 undefined，取消当前行
  if (row === null || row === undefined) {
    currentRowIndex.value = null
    emit('update:currentRowIndex', null)
    return [1, '就绪']
  }
  
  // 参数校验
  if (row < 0 || row >= props.data.length) {
    return [-1, `行号${row}无效`]
  }
  
  // 设置当前行
  currentRowIndex.value = row
  emit('update:currentRowIndex', row)
  return [1, '就绪']
}

// ==================== 行操作 ====================
/**
 * 新增行（接口函数）
 * @param row 插入位置，从0开始。如果未提供或row<0，则在末尾追加；如果row>=0且<=最大行号，则在row前插入
 * @param defaultRow 默认行数据，如果未提供则使用列配置的默认值
 * @returns [code, message, newRowIndex] code=1表示成功，code=-1表示失败
 */
const addRow = async (row?: number, defaultRow?: any): Promise<[number, string, number?]> => {
  // 取消所有单元格选中和行选中（在新增行之前执行，确保能正确取消选中）
  const [deselectCellCode, deselectCellMsg] = deselectCell()
  if (deselectCellCode !== 1) {
    return [deselectCellCode, deselectCellMsg]
  }
  
  const [deselectRowCode, deselectRowMsg] = deselectRow()
  if (deselectRowCode !== 1) {
    return [deselectRowCode, deselectRowMsg]
  }
  
  // 确定插入位置
  let insertIndex: number | undefined
  if (row === undefined || row < 0) {
    // 在末尾追加
    insertIndex = undefined
  } else if (row >= 0 && row <= props.data.length) {
    // 在row前插入
    insertIndex = row
  } else {
    return [-1, `行号${row}无效`]
  }
  
  // 创建默认行数据
  // 优先使用传入的 defaultRow，其次使用 props.defaultRow，最后使用列配置的默认值
  const newDefaultRow: any = {}
  props.columns.forEach(col => {
    if (col.type === 'number') {
      newDefaultRow[col.field] = null
    } else if (col.type === 'image') {
      newDefaultRow[col.field] = []
    } else {
      newDefaultRow[col.field] = ''
    }
  })
  
  // 合并默认行数据：列配置默认值 < props.defaultRow < 传入的 defaultRow
  const finalDefaultRow = { ...newDefaultRow, ...props.defaultRow, ...defaultRow }
  
  // 触发row-add事件
  emit('row-add', { defaultRow: finalDefaultRow, insertIndex })
  
  // 等待父组件处理并DOM更新
  await nextTick()
  await nextTick() // 双重nextTick确保DOM完全更新
  
  // 确定新增行的索引
  let newRowIndex: number
  if (insertIndex === undefined) {
    newRowIndex = props.data.length - 1
  } else {
    newRowIndex = insertIndex
  }
  
  // 选中新增的行
  if (newRowIndex >= 0 && newRowIndex < props.data.length) {
    const [selectCode, selectMsg] = selectRow(newRowIndex)
    if (selectCode !== 1) {
      return [selectCode, selectMsg, newRowIndex]
    }
  }
  
  return [1, '就绪', newRowIndex]
}

/**
 * 删除行（接口函数）
 * @param row 行索引，从0开始
 * @returns [code, message] code=1表示成功，code=-1表示失败
 */
const deleteRow = async (row: number): Promise<[number, string]> => {
  // 参数校验
  if (row < 0 || row >= props.data.length) {
    return [-1, `行号${row}无效`]
  }
  
  // 取消所有行的选中状态（删除行时应该清除所有选中状态）
  const [deselectRowCode, deselectRowMsg] = deselectRow()
  if (deselectRowCode !== 1) {
    return [deselectRowCode, deselectRowMsg]
  }
  
  // 取消所有单元格选中
  const [deselectCellCode, deselectCellMsg] = deselectCell()
  if (deselectCellCode !== 1) {
    return [deselectCellCode, deselectCellMsg]
  }
  
  // 如果删除的行是当前行，清除当前行
  if (currentRowIndex.value === row) {
    currentRowIndex.value = null
    emit('update:currentRowIndex', null)
  } else if (currentRowIndex.value !== null && currentRowIndex.value > row) {
    // 如果删除的行在当前行之前，更新当前行索引（减1）
    currentRowIndex.value--
    emit('update:currentRowIndex', currentRowIndex.value)
  }
  
  // 如果删除的行正在编辑，结束编辑状态
  if (editingCell.value && editingCell.value.rowIndex === row) {
    endEdit()
  }
  
  // 在组件内部删除数据，然后通过emit('update:data')通知父组件
  const newData = [...props.data]
  newData.splice(row, 1)
  emit('update:data', newData)
  
  // 同时触发row-delete事件（保持向后兼容）
  emit('row-delete', row)
  
  // 等待DOM更新
  await nextTick()
  
  return [1, '就绪']
}

// ==================== 单元格点击事件 ====================
/**
 * 处理单元格点击
 */
const handleCellClick = (row: any, column: any, _cell?: HTMLElement, event?: MouseEvent) => {
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
    
    // 使用 selectRow 函数来处理行选择（它会自动处理 DOM 样式）
    // 注意：无论点击行是否与当前行号一致，都应该选中（按优化方案要求）
    selectRow(rowIndex, selectType)
    
    return
  }
  
  if (rowIndex === -1 || !field) return
  
  // 使用统一的导航函数（内部会处理列校验和编辑状态检查）
  navigateToCell(
    { rowIndex, field },
    { validateCurrent: false, allowAddRow: false }
  ) // 忽略返回值
  
  emit('cell-click', rowIndex, field, event!)
}

/**
 * 处理单元格双击
 */
const handleCellDblclick = (row: any, column: any, _cell?: HTMLElement, event?: MouseEvent) => {
  const rowIndex = props.data.indexOf(row)
  const field = column.property || column.field
  
  if (rowIndex === -1 || !field) return
  
  // 使用统一的编辑函数（内部会处理列校验和编辑状态检查）
  const [editCode] = startEdit(rowIndex, field)
  if (editCode !== 1) {
    return // 如果编辑失败，不继续处理
  }
  
  const col = props.columns.find(c => c.field === field)
  if (!col) {
    return
  }
  
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
  // 注意：如果没有监听器，emit 会返回 undefined，此时应该返回 true（不需要校验）
  const result = emit('cell-validate', rowIndex, field, value)
  
  // 如果没有监听器，emit 会返回 undefined，此时应该返回 true（不需要校验）
  if (result === undefined) {
    return true
  }
  
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
    
    // Tab: 选中下一个单元格（Shift+Tab 向前跳转）
    if (key === 'Tab') {
      event.preventDefault()
      event.stopPropagation()
      
      const direction = event.shiftKey ? 'left' : 'right'
      navigateToCell(
        { direction, fromRowIndex: rowIndex, fromField: field },
        { validateCurrent: false, allowAddRow: true }
      ) // 忽略返回值
      return
    }
    
    // Enter: 图片列不支持编辑，Enter 键不处理
    if (key === 'Enter') {
      // 图片列不支持编辑，Enter 键不处理
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
      ) // 忽略返回值
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
    startEdit(rowIndex, field, { isKeyboardInput: true, inputValue: key }) // 忽略返回值
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
    startEdit(rowIndex, field) // 忽略返回值
    return
  }
  
  // Tab: 选中下一个单元格（Shift+Tab 向前跳转）
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
  
  // Enter: 双击单元格进入编辑状态
  if (key === 'Enter') {
    event.preventDefault()
    event.stopPropagation()
    
    // 如果单元格不可编辑或者是图片列，则忽略
    if (col?.editable === false || col?.type === 'image') {
      return
    }
    
    // 双击进入编辑状态
    startEdit(rowIndex, field)
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
    ) // 忽略返回值
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
 * 准备复制数据（提取公共逻辑）
 * @param value 单元格值
 * @param column 列配置
 * @returns 包含 copyValue 和 copyData 的对象
 */
const prepareCopyData = (value: any, column: TablePlusColumn | null): { copyValue: string; copyData: any } => {
  let copyValue = ''
  let copyData = value
  
  if (value !== undefined && value !== null) {
    if (column?.type === 'image') {
      // 图片类型：只复制字符串格式的图片 URL，过滤掉对象（内存预览）
      const imageArray = Array.isArray(value) ? value : []
      const stringImages = imageArray.filter((item: any) => typeof item === 'string')
      copyData = stringImages
      copyValue = `${stringImages.length} image(s)`
    } else {
      copyValue = String(value)
    }
  }
  
  return { copyValue, copyData }
}

/**
 * 处理复制（Ctrl+C）
 * 支持编辑模式和非编辑模式，统一处理逻辑
 */
const handleCopy = (event: ClipboardEvent) => {
  // 确定源单元格：优先使用编辑模式，否则使用选中的单元格
  let rowIndex: number | null = null
  let field: string | null = null
  let column: TablePlusColumn | null = null
  
  if (editingCell.value) {
    // 编辑模式：使用当前编辑的单元格
    rowIndex = editingCell.value.rowIndex
    field = editingCell.value.field
    column = props.columns.find(c => c.field === field) || null
  } else {
    // 非编辑模式：使用选中的单元格
    const cellInfo = getSelectedCellInfo()
    if (cellInfo) {
      rowIndex = cellInfo.rowIndex
      field = cellInfo.field
      column = cellInfo.column
    }
  }
  
  // 如果没有有效的源单元格，忽略复制
  if (rowIndex === null || !field || !column) {
    return
  }
  
  const value = props.data[rowIndex]?.[field]
  if (value === undefined || value === null) {
    return
  }
  
  event.preventDefault()
  
  // 准备复制数据
  const { copyValue, copyData } = prepareCopyData(value, column)
  
  // 设置剪贴板数据
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

/**
 * 处理粘贴（Ctrl+V）
 * 支持编辑模式和非编辑模式，统一处理逻辑
 */
const handlePaste = (event: ClipboardEvent) => {
  // 确定目标单元格：优先使用编辑模式，否则使用选中的单元格
  let rowIndex: number | null = null
  let field: string | null = null
  let column: TablePlusColumn | null = null
  
  if (editingCell.value) {
    // 编辑模式：使用当前编辑的单元格
    rowIndex = editingCell.value.rowIndex
    field = editingCell.value.field
    column = props.columns.find(c => c.field === field) || null
  } else {
    // 非编辑模式：使用选中的单元格
    const cellInfo = getSelectedCellInfo()
    if (cellInfo) {
      rowIndex = cellInfo.rowIndex
      field = cellInfo.field
      column = cellInfo.column
    }
  }
  
  // 如果没有有效的目标单元格，忽略粘贴
  if (rowIndex === null || !field || !column || column.editable === false) {
    return
  }
  
  event.preventDefault()
  
  // 尝试获取自定义格式的数据
  const customData = event.clipboardData?.getData('application/x-importgrid-cell')
  let cellData: any = null
  
  if (customData) {
    try {
      cellData = JSON.parse(customData)
    } catch (e) {
      // 解析失败，忽略自定义数据，使用普通文本
    }
  }
  
  // 处理粘贴数据
  if (cellData) {
    // 有自定义数据：尝试使用自定义格式处理
    if (!handleCustomDataPaste(cellData, rowIndex, field, column)) {
      // 类型不匹配，忽略粘贴
      return
    }
  } else {
    // 没有自定义数据：使用普通文本粘贴（兼容外部复制）
    const pasteData = event.clipboardData?.getData('text/plain') || ''
    if (pasteData) {
      handlePlainTextPaste(pasteData, rowIndex, field, column)
    } else {
      // 如果粘贴数据为空，清空单元格
      if (column.type === 'image') {
        updateCellData(rowIndex, field, [])
      } else if (column.type === 'number') {
        handleInputUpdate(rowIndex, field, null)
      } else {
        handleInputUpdate(rowIndex, field, '')
      }
    }
  }
}

/**
 * 处理全局 keydown 事件（专门处理编辑模式下的 Tab 和 Escape 键）
 * 
 * 使用全局事件监听器的原因：
 * 1. Element Plus 组件可能不会将 keydown 事件传递到内部的 input 元素
 * 2. 使用捕获阶段可以确保优先处理键盘事件，防止浏览器默认行为
 * 3. 全局监听器可以捕获所有键盘事件，不受组件内部事件处理影响
 * 
 * 这是唯一的事件监听方案，简化代码并避免冗余
 */
const handleGlobalKeydown = (event: KeyboardEvent) => {
  // 只处理 Tab 和 Escape 键
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
  
  // 如果焦点不在表格内，不处理
  if (!activeElement || !tableElement || !tableElement.contains(activeElement)) {
    return
  }
  
  // 立即阻止默认行为（必须在捕获阶段阻止，否则浏览器会先处理）
  event.preventDefault()
  event.stopPropagation()
  event.stopImmediatePropagation()
  
  if (isTab) {
    // Tab 键：退出编辑（校验），跳转到下一个单元格
    const direction = event.shiftKey ? 'left' : 'right'
    const currentRowIndex = editingCell.value.rowIndex
    const currentField = editingCell.value.field
    
    navigateToCell(
      { direction, fromRowIndex: currentRowIndex, fromField: currentField },
      { validateCurrent: true, allowAddRow: true }
    ) // 忽略返回值
  } else if (isEscape) {
    // Escape 键：退出编辑（不校验）
    if (editingCell.value) {
      const { rowIndex, field } = editingCell.value
      exitEdit(rowIndex, field, false)
    }
  }
}

// ==================== 生命周期 ====================
onMounted(() => {
  // 监听复制粘贴事件
  document.addEventListener('copy', handleCopy)
  document.addEventListener('paste', handlePaste)
  
  // 监听全局 keydown 事件（处理编辑模式下的 Tab 和 Escape 键）
  // 使用捕获阶段 + passive: false，确保能够阻止默认行为
  // 同时在 window 和 document 级别监听，确保能够捕获到键盘事件
  window.addEventListener('keydown', handleGlobalKeydown, { capture: true, passive: false })
  document.addEventListener('keydown', handleGlobalKeydown, { capture: true, passive: false })
})

onBeforeUnmount(() => {
  // 清理事件监听
  document.removeEventListener('copy', handleCopy)
  document.removeEventListener('paste', handlePaste)
  window.removeEventListener('keydown', handleGlobalKeydown, { capture: true } as any)
  document.removeEventListener('keydown', handleGlobalKeydown, { capture: true } as any)
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
  // 单元格操作接口
  selectCell,
  deselectCell,
  startEdit,
  exitEdit,
  clearCurrentRow,
  navigateToCell,
  // 行操作接口
  selectRow,
  deselectRow,
  addRow,
  deleteRow,
  // 列操作接口
  addColumn,
  deleteColumn,
  // 其他接口
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
          @click.stop="deleteRow(scope.$index)"
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
    user-select: none; // 禁止文字选中
    -webkit-user-select: none;
    -moz-user-select: none;
    -ms-user-select: none;
    
    // 确保 .cell 容器和所有子元素都是 pointer 光标
    .cell {
      cursor: pointer !important;
      user-select: none; // 禁止文字选中
      -webkit-user-select: none;
      -moz-user-select: none;
      -ms-user-select: none;
    }
    
    * {
      cursor: pointer !important;
      user-select: none; // 禁止文字选中
      -webkit-user-select: none;
      -moz-user-select: none;
      -ms-user-select: none;
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
  user-select: none; // 禁止文字选中
  -webkit-user-select: none;
  -moz-user-select: none;
  -ms-user-select: none;
  
  // 确保所有子元素都继承 pointer 光标和禁止选中
  * {
    cursor: pointer;
    user-select: none;
    -webkit-user-select: none;
    -moz-user-select: none;
    -ms-user-select: none;
  }
}

.row-index-pointer {
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  user-select: none; // 禁止文字选中
  -webkit-user-select: none;
  -moz-user-select: none;
  -ms-user-select: none;
  
  // 确保 SVG 和 path 元素也继承 pointer 光标和禁止选中
  svg,
  svg path {
    cursor: pointer;
    user-select: none;
    -webkit-user-select: none;
    -moz-user-select: none;
    -ms-user-select: none;
  }
}

.row-index-number {
  font-size: 12px;
  color: #606266;
  cursor: pointer;
  user-select: none; // 禁止文字选中
  -webkit-user-select: none;
  -moz-user-select: none;
  -ms-user-select: none;
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
  
  // 序号列的 .cell 容器和所有子元素都应该是 pointer 光标，并禁止文字选中
  tbody .el-table__cell:first-child {
    cursor: pointer !important;
    user-select: none !important; // 禁止文字选中
    -webkit-user-select: none !important;
    -moz-user-select: none !important;
    -ms-user-select: none !important;
    
    .cell {
      cursor: pointer !important;
      user-select: none !important; // 禁止文字选中
      -webkit-user-select: none !important;
      -moz-user-select: none !important;
      -ms-user-select: none !important;
    }
    
    * {
      cursor: pointer !important;
      user-select: none !important; // 禁止文字选中
      -webkit-user-select: none !important;
      -moz-user-select: none !important;
      -ms-user-select: none !important;
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
    
    // 最后一个数据单元格：添加右边框
    // 注意：Action列是最后一列，所以倒数第二个是最后一个数据单元格
    .el-table__cell:nth-last-child(2) {
      position: relative !important;
      
      // 右边框（使用 border-right，因为 box-shadow 可能被覆盖）
      border-right: 2px solid rgb(16, 153, 104) !important;
      
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


