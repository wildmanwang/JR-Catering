<!--
  ImportGrid 组件 - Excel 风格的通用数据导入/批量维护模板
  
  功能特性：
  1. Excel 风格的表格交互（单元格编辑、键盘导航、复制粘贴）
  2. 支持多种数据类型（文本、数字、下拉选择、图片、日期）
  3. 数据持久化（通过 sessionStorage 在页面间传递数据）
  4. 单元格编辑（单击聚焦、双击编辑、键盘输入自动进入编辑）
  5. 键盘导航（Tab/Enter 跳转、方向键移动、Esc 取消）
  6. 复制粘贴（Ctrl+C/Ctrl+V）
  
  使用场景：
  - 从父窗口选择记录后批量编辑
  - 新建多条记录
  - 批量维护数据
  
  使用示例：
  <ImportGrid
    :columns="columns"
    :storage-key="STORAGE_KEY"
    :create-default-row="createDefaultRow"
    :map-row-data="mapRowData"
    @data-loaded="handleDataLoaded"
    @data-changed="handleDataChanged"
  />
-->
<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, onUnmounted, watch, nextTick, h, toRaw } from 'vue'
import { useRouter } from 'vue-router'
import { ElTable, ElTableColumn, ElInput, ElInputNumber, ElSelect, ElOption } from 'element-plus'
import { useTagsViewStoreWithOut } from '@/store/modules/tagsView'

/**
 * 列配置接口
 */
export interface ImportGridColumn {
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
  /** 自定义格式化函数 */
  formatter?: (row: any, column: any, cellValue: any) => string
  /** 下拉选择选项（type='select' 时必填） */
  options?: Array<{ label: string; value: any }>
  /** 是否可编辑（默认 true） */
  editable?: boolean
}

/**
 * 组件 Props 接口
 */
export interface ImportGridProps {
  /** 列配置数组 */
  columns: ImportGridColumn[]
  /** 数据存储的 sessionStorage key（用于在页面间传递数据） */
  storageKey: string
  /** 创建默认行数据的函数（用于新增行） */
  createDefaultRow?: () => any
  /** 数据转换函数（将父窗口传入的数据转换为表格所需格式） */
  mapRowData?: (row: any) => any
}

const props = withDefaults(defineProps<ImportGridProps>(), {
  createDefaultRow: () => ({}),
  mapRowData: (row: any) => row
})

/**
 * 组件事件定义
 */
const emit = defineEmits<{
  /** 数据加载完成事件 */
  dataLoaded: [data: any[]]
  /** 数据变化事件 */
  dataChanged: [data: any[]]
}>()

// ==================== 状态管理 ====================

/** Router 实例（用于获取当前路由路径） */
const router = useRouter()

/** 标签页 Store（用于检测标签页是否被关闭） */
const tagsViewStore = useTagsViewStoreWithOut()

/** 页面状态存储的 sessionStorage key（基于当前路由路径） */
const PAGE_STATE_KEY = computed(() => {
  return `IMPORT_GRID_STATE_${router.currentRoute.value.fullPath}`
})

/** 页面准备就绪标志（用于防止恢复状态时触发保存） */
const pageReady = ref(false)

/** 正在恢复状态标志（用于防止恢复状态时触发保存） */
const isRestoring = ref(false)

/** 状态保存定时器 */
let saveStateTimer: NodeJS.Timeout | null = null

/** 组件挂载时的路由信息（用于检测标签页关闭） */
let mountedRoutePath: string | null = null
let mountedRouteFullPath: string | null = null

/** 表格数据列表 */
const dataList = ref<any[]>([])

/** 当前正在编辑的单元格信息 { rowIndex: 行索引, field: 字段名 } */
const editingCell = ref<{ rowIndex: number; field: string } | null>(null)

/** 标记是否正在输入（防止 blur 事件误触发导致退出编辑模式） */
const isInputting = ref(false)

/** 当前正在编辑的输入框 DOM 引用 */
const currentInputRef = ref<HTMLInputElement | null>(null)

/** blur 事件延迟处理的定时器引用 */
const blurTimerRef = ref<NodeJS.Timeout | null>(null)

/** 待输入的值的引用（用于键盘输入时暂存第一个字符） */
const pendingInputValue = ref<{ rowIndex: number; field: string; value: string } | null>(null)

/** Element Plus Table 组件引用 */
const tableRef = ref<InstanceType<typeof ElTable>>()

// ==================== 计算属性 ====================

/** 可编辑的列配置（过滤掉隐藏和不可编辑的列） */
const editableColumns = computed(() => {
  return props.columns.filter(col => col.show !== false && col.editable !== false)
})

/** 可编辑的字段名列表 */
const editableFields = computed(() => {
  return editableColumns.value.map(col => col.field)
})

// ==================== 数据加载 ====================

/**
 * 保存页面状态
 * 同时写入 tagsViewStore.pageStates（内存）和 sessionStorage（刷新恢复）
 */
const savePageState = async () => {
  try {
    const state = {
      dataList: toRaw(dataList.value) || []
    }
    
    // 同时保存到内存（tagsViewStore）和 sessionStorage
    const fullPath = router.currentRoute.value.fullPath
    tagsViewStore.setPageState(fullPath, state)
    sessionStorage.setItem(PAGE_STATE_KEY.value, JSON.stringify(state))
    console.log('ImportGrid: 保存页面状态', state)
  } catch (err) {
    console.error('ImportGrid: 保存页面状态失败', err)
  }
}

/**
 * 恢复页面状态
 * 优先从 tagsViewStore.pageStates（内存）读取，如果没有则从 sessionStorage 恢复并同步到 tagsViewStore
 */
const restorePageState = () => {
  try {
    const fullPath = router.currentRoute.value.fullPath
    
    // 优先从内存（tagsViewStore）读取
    let state = tagsViewStore.getPageState(fullPath)
    
    if (state) {
      // 内存中有状态，直接返回
      console.log('ImportGrid: 从内存恢复页面状态', state)
      return state
    }
    
    // 内存中没有，尝试从 sessionStorage 恢复（页面刷新场景）
    const cache = sessionStorage.getItem(PAGE_STATE_KEY.value)
    if (cache) {
      state = JSON.parse(cache)
      // 同步到 tagsViewStore（内存）
      tagsViewStore.setPageState(fullPath, state)
      console.log('ImportGrid: 从 sessionStorage 恢复页面状态并同步到内存', state)
      return state
    }
    
    return null
  } catch (err) {
    console.error('ImportGrid: 恢复页面状态失败', err)
    return null
  }
}

/**
 * 清除页面状态缓存
 * 同时清理 tagsViewStore.pageStates（内存）和 sessionStorage
 * @param stateKey - 可选的状态 key，如果不提供则使用默认的 PAGE_STATE_KEY
 * @param fullPath - 可选的路由完整路径，如果不提供则使用当前路由的 fullPath
 */
const clearPageState = (stateKey?: string, fullPath?: string) => {
  try {
    const keyToRemove = stateKey || PAGE_STATE_KEY.value
    const pathToClear = fullPath || router.currentRoute.value.fullPath
    
    // 同时清理内存和 sessionStorage
    tagsViewStore.clearPageState(pathToClear)
    sessionStorage.removeItem(keyToRemove)
    console.log('ImportGrid: 清除页面状态', { stateKey: keyToRemove, fullPath: pathToClear })
  } catch (err) {
    console.error('ImportGrid: 清除页面状态失败', err)
  }
}

/**
 * 从 sessionStorage 加载数据（从父窗口传入的数据）
 * 
 * 工作流程：
 * 1. 从 sessionStorage 读取数据（由父窗口通过 persistImportPayload 保存）
 * 2. 使用 mapRowData 转换数据格式
 * 3. 合并默认行数据，确保所有字段都有默认值
 * 4. 加载完成后清除 sessionStorage，避免重复加载
 * 5. 如果没有数据，创建一行默认数据
 * 
 * @returns {boolean} 是否成功加载了数据
 */
const loadDataFromStorage = () => {
  try {
    const cache = sessionStorage.getItem(props.storageKey)
    if (cache) {
      const payload = JSON.parse(cache)
      if (Array.isArray(payload) && payload.length > 0) {
        // 使用 mapRowData 转换数据，并合并默认行数据
        dataList.value = payload.map(row => ({
          ...props.createDefaultRow(),
          ...props.mapRowData(row)
        }))
        emit('dataLoaded', dataList.value)
        // 清除 sessionStorage，避免重复加载
        sessionStorage.removeItem(props.storageKey)
        return true
      }
    }
  } catch (err) {
    console.error('加载导入数据失败：', err)
  }
  
  // 如果没有数据，创建一行默认数据
  dataList.value = [props.createDefaultRow()]
  emit('dataLoaded', dataList.value)
  return false
}

/**
 * 监听数据变化
 */
watch(
  () => dataList.value,
  (newData) => {
    emit('dataChanged', newData)
    
    // 自动保存状态（debounce）
    if (pageReady.value && !isRestoring.value) {
      if (saveStateTimer) {
        clearTimeout(saveStateTimer)
      }
      saveStateTimer = setTimeout(async () => {
        await savePageState()
      }, 500)
    }
    
    // 如果正在编辑，确保输入框保持焦点
    // 使用 flush: 'post' 确保在 DOM 更新后执行
    if (editingCell.value && isInputting.value) {
      const editing = editingCell.value
      if (editing && isEditing(editing.rowIndex, editing.field)) {
        const { rowIndex, field } = editing
        // 使用 requestAnimationFrame 确保浏览器完成渲染
        requestAnimationFrame(() => {
          requestAnimationFrame(() => {
            const cellInput = document.querySelector(`[data-cell-key="${rowIndex}-${field}"]`) as HTMLElement
            if (cellInput) {
              const inputElement = cellInput.querySelector('input') as HTMLInputElement
              if (inputElement) {
                // 标记正在输入，防止 blur 事件误触发
                isInputting.value = true
                // 恢复焦点
                if (document.activeElement !== inputElement) {
                  inputElement.focus()
                  // 将光标移到末尾
                  const len = inputElement.value.length
                  inputElement.setSelectionRange(len, len)
                }
                currentInputRef.value = inputElement
                // 延迟清除标记
                setTimeout(() => {
                  isInputting.value = false
                }, 200)
              }
            }
          })
        })
      }
    }
  },
  { deep: true, flush: 'post' }
)

// 监听编辑状态变化，确保输入框渲染后设置值
watch(
  editingCell,
  (newVal) => {
    if (newVal && pendingInputValue.value) {
      // 等待Vue重新渲染
      nextTick(() => {
        nextTick(() => {
          // data-cell-key 是直接设置在 input 元素上的，所以找到的就是 input 元素本身
          const elInput = document.querySelector(`[data-cell-key="${newVal.rowIndex}-${newVal.field}"]`) as HTMLInputElement
          if (elInput && pendingInputValue.value) {
            elInput.value = pendingInputValue.value.value
            dataList.value[newVal.rowIndex][newVal.field] = pendingInputValue.value.value
            elInput.focus()
            const len = elInput.value.length
            elInput.setSelectionRange(len, len)
            currentInputRef.value = elInput
            setTimeout(() => {
              isInputting.value = false
              pendingInputValue.value = null
            }, 300)
          }
        })
      })
    }
  },
  { immediate: false }
)

/**
 * 检查单元格是否正在编辑
 */
const isEditing = (rowIndex: number, field: string) => {
  return editingCell.value?.rowIndex === rowIndex && editingCell.value?.field === field
}

/**
 * 开始编辑单元格
 */
const startEdit = (rowIndex: number, field: string) => {
  const col = props.columns.find(c => c.field === field)
  if (col && col.editable === false) {
    console.log('startEdit: 列不可编辑', { rowIndex, field })
    return
  }
  
  console.log('startEdit: 开始编辑', { rowIndex, field })
  
  // 标记正在输入，防止blur事件误触发
  isInputting.value = true
  
  editingCell.value = { rowIndex, field }
  
  console.log('startEdit: 设置编辑状态', { editingCell: editingCell.value, isEditing: isEditing(rowIndex, field) })
  
  // 延迟聚焦，确保输入框已经渲染
  nextTick(() => {
    nextTick(() => {
      console.log('startEdit: nextTick 后', { editingCell: editingCell.value, isEditing: isEditing(rowIndex, field) })
      focusInput(rowIndex, field, false)
      // 延迟清除输入标记
      setTimeout(() => {
        isInputting.value = false
      }, 100)
    })
  })
}

/**
 * 结束编辑
 */
const endEdit = () => {
  // 清除blur定时器
  if (blurTimerRef.value) {
    clearTimeout(blurTimerRef.value)
    blurTimerRef.value = null
  }
  
  // 移除选中状态和编辑状态
  document.querySelectorAll('.el-table__cell.selected-cell, .el-table__cell.editing-cell').forEach(el => {
    el.classList.remove('selected-cell', 'editing-cell')
  })
  
  editingCell.value = null
  currentInputRef.value = null
  isInputting.value = false
}

/**
 * 聚焦输入框
 */
const focusInput = (rowIndex: number, field: string, shouldSelect = true) => {
  // 使用双重 nextTick 和 requestAnimationFrame 确保 DOM 完全渲染
  nextTick(() => {
    nextTick(() => {
      requestAnimationFrame(() => {
        requestAnimationFrame(() => {
          const element = document.querySelector(`[data-cell-key="${rowIndex}-${field}"]`) as HTMLElement
          console.log('focusInput: 查找输入框', { rowIndex, field, element })
          
          if (!element) {
            console.warn('focusInput: 未找到元素', { rowIndex, field })
            return
          }
          
          // data-cell-key 可能设置在 Element Plus 组件容器上，也可能直接设置在 input 元素上
          let elInput: HTMLInputElement | null = null
          
          // 如果找到的元素本身就是 input 或 textarea，直接使用
          if (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA') {
            elInput = element as HTMLInputElement
          } else {
            // 否则查找内部的 input 或 textarea
            elInput = element.querySelector('input, textarea') as HTMLInputElement
          }
          
          console.log('focusInput: 找到输入元素', { elInput, tagName: element.tagName })
          
          if (elInput) {
            elInput.focus()
            console.log('focusInput: 已聚焦', { activeElement: document.activeElement })
            // 只有在没有初始值的情况下才选中所有文本
            if (shouldSelect) {
              elInput.select()
            } else {
              // 如果有初始值，将光标移到末尾
              const len = elInput.value.length
              elInput.setSelectionRange(len, len)
            }
          } else {
            console.warn('focusInput: 未找到输入元素', { element, tagName: element.tagName })
          }
          
          // 给父单元格添加选中类和编辑类
          const cell = element.closest('.el-table__cell') as HTMLElement
          if (cell) {
            // 移除其他单元格的选中状态和编辑状态
            document.querySelectorAll('.el-table__cell.selected-cell').forEach(el => {
              el.classList.remove('selected-cell', 'editing-cell')
            })
            cell.classList.add('selected-cell', 'editing-cell')
          }
        })
      })
    })
  })
}

/**
 * 处理单元格点击
 */
const handleCellClick = (row: any, column: any, cell?: HTMLElement, event?: MouseEvent) => {
  const rowIndex = dataList.value.indexOf(row)
  const field = column.property || column.field
  
  if (rowIndex === -1 || !field) return
  
  const col = props.columns.find(c => c.field === field)
  if (col && col.editable === false) return
  
  // 如果点击的是正在编辑的单元格，不处理（保持编辑状态）
  if (isEditing(rowIndex, field)) {
    return
  }
  
  // 如果点击的是另一个单元格，先退出当前编辑模式
  if (editingCell.value) {
    endEdit()
  }
  
  // 单击时只获得焦点，不进入编辑模式
  // 清除其他单元格的选中状态
  document.querySelectorAll('.el-table__cell.selected-cell').forEach(el => {
    el.classList.remove('selected-cell')
  })
  
  // 添加当前单元格的选中状态
  // 使用 nextTick 确保 DOM 已更新
  nextTick(() => {
    // 通过事件目标查找单元格
    if (event && event.target) {
      const targetCell = (event.target as HTMLElement).closest('.el-table__cell') as HTMLElement
      if (targetCell) {
        targetCell.classList.add('selected-cell')
        return
      }
    }
    
    // 如果事件目标不存在，通过 DOM 查找
    const visibleColumns = props.columns.filter(col => col.show !== false)
    const columnIndex = visibleColumns.findIndex(c => c.field === field)
    if (columnIndex !== -1) {
      // 跳过序号列，所以 columnIndex + 2
      const cellElement = document.querySelector(
        `.el-table__body tbody tr:nth-child(${rowIndex + 1}) .el-table__cell:nth-child(${columnIndex + 2})`
      ) as HTMLElement
      if (cellElement) {
        cellElement.classList.add('selected-cell')
      }
    }
  })
}

/**
 * 处理单元格双击
 */
const handleCellDblclick = (row: any, column: any, cell?: HTMLElement, event?: MouseEvent) => {
  const rowIndex = dataList.value.indexOf(row)
  const field = column.property || column.field
  
  if (rowIndex === -1 || !field) return
  
  const col = props.columns.find(c => c.field === field)
  if (col && col.editable === false) return
  
  console.log('handleCellDblclick: 双击进入编辑', { rowIndex, field })
  
  // 双击时获得焦点并进入编辑模式
  // 先设置选中状态
  document.querySelectorAll('.el-table__cell.selected-cell').forEach(el => {
    el.classList.remove('selected-cell')
  })
  
  if (cell) {
    cell.classList.add('selected-cell')
  }
  
  // 然后进入编辑模式
  startEdit(rowIndex, field)
}

/**
 * 处理键盘输入（直接进入编辑）
 */
const handleCellKeydown = (event: KeyboardEvent, row: any, column: any) => {
  const rowIndex = dataList.value.indexOf(row)
  const field = column.property || column.field
  
  // 忽略 Ctrl+C 和 Ctrl+V，让全局事件处理
  if (event.ctrlKey || event.metaKey) {
    if (event.key === 'c' || event.key === 'C' || event.key === 'v' || event.key === 'V') {
      return
    }
  }
  
  console.log('handleCellKeydown: 键盘输入', { rowIndex, field, key: event.key, column })
  
  if (rowIndex === -1 || !field) {
    console.log('handleCellKeydown: 无效参数', { rowIndex, field })
    return
  }
  
  const col = props.columns.find(c => c.field === field)
  if (col && col.editable === false) return
  
  // 如果已经在编辑状态，不处理（让输入框自己处理）
  if (isEditing(rowIndex, field)) {
    return
  }
  
  // 如果按下的是可打印字符，直接进入编辑
  if (event.key.length === 1 && !event.ctrlKey && !event.metaKey && !event.altKey) {
    event.preventDefault()
    event.stopPropagation()
    
    console.log('handleCellKeydown: 进入编辑模式', { rowIndex, field, key: event.key })
    
    // 清除之前的blur定时器
    if (blurTimerRef.value) {
      clearTimeout(blurTimerRef.value)
      blurTimerRef.value = null
    }
    
    // 标记正在输入（提前标记，防止blur事件误触发）
    isInputting.value = true
    
    // 直接设置第一个字符（Excel行为：输入时替换整个内容）
    dataList.value[rowIndex][field] = event.key
    
    // 设置编辑状态（这会触发Vue重新渲染）
    editingCell.value = { rowIndex, field }
    
    console.log('handleCellKeydown: 设置编辑状态', { rowIndex, field, editingCell: editingCell.value })
    
    // 确保输入框渲染后获得焦点
    nextTick(() => {
      nextTick(() => {
        requestAnimationFrame(() => {
          requestAnimationFrame(() => {
            focusInput(rowIndex, field, false)
            setTimeout(() => {
              isInputting.value = false
            }, 300)
          })
        })
      })
    })
  }
  
  // Delete 或 Backspace 删除单元格内容
  if ((event.key === 'Delete' || event.key === 'Backspace') && !editingCell.value) {
    event.preventDefault()
    const col = props.columns.find(c => c.field === field)
    dataList.value[rowIndex][field] = col?.type === 'number' ? null : ''
  }
  
  // F2 进入编辑
  if (event.key === 'F2') {
    event.preventDefault()
    startEdit(rowIndex, field)
  }
}

/**
 * 处理输入框键盘事件
 */
const handleInputKeydown = (event: KeyboardEvent, rowIndex: number, field: string) => {
  const col = props.columns.find(c => c.field === field)
  const currentIndex = editableFields.value.indexOf(field)
  
  // Tab: 行为与非编辑模式一致（向右移动到下一列，但不进入编辑模式）
  if (event.key === 'Tab') {
    event.preventDefault()
    endEdit()
    
    const visibleColumns = props.columns.filter(col => col.show !== false)
    
    if (event.shiftKey) {
      // Shift+Tab: 向左移动
      if (currentIndex > 0) {
        // 跳转到上一列（不进入编辑模式）
        const prevField = editableFields.value[currentIndex - 1]
        const prevColumn = visibleColumns.find(col => col.field === prevField)
        if (prevColumn) {
          const prevColumnIndex = visibleColumns.indexOf(prevColumn)
          const tbody = document.querySelector('.el-table__body tbody')
          if (tbody) {
            const rowElement = tbody.children[rowIndex] as HTMLElement
            if (rowElement) {
              const prevCell = rowElement.children[prevColumnIndex + 1] as HTMLElement
              if (prevCell) {
                document.querySelectorAll('.el-table__cell.selected-cell').forEach(el => {
                  el.classList.remove('selected-cell')
                })
                prevCell.classList.add('selected-cell')
              }
            }
          }
        }
      } else if (rowIndex > 0) {
        // 如果已是行首，则跳转到上一行最后一列
        const prevField = editableFields.value[editableFields.value.length - 1]
        const prevColumn = visibleColumns.find(col => col.field === prevField)
        if (prevColumn) {
          const prevColumnIndex = visibleColumns.indexOf(prevColumn)
          const tbody = document.querySelector('.el-table__body tbody')
          if (tbody) {
            const prevRow = tbody.children[rowIndex - 1] as HTMLElement
            if (prevRow) {
              const prevCell = prevRow.children[prevColumnIndex + 1] as HTMLElement
              if (prevCell) {
                document.querySelectorAll('.el-table__cell.selected-cell').forEach(el => {
                  el.classList.remove('selected-cell')
                })
                prevCell.classList.add('selected-cell')
              }
            }
          }
        }
      }
    } else {
      // Tab: 向右移动到下一列（不进入编辑模式）
      if (currentIndex < editableFields.value.length - 1) {
        // 如果还有下一列，跳转到下一列
        const nextField = editableFields.value[currentIndex + 1]
        const nextColumn = visibleColumns.find(col => col.field === nextField)
        if (nextColumn) {
          const nextColumnIndex = visibleColumns.indexOf(nextColumn)
          const tbody = document.querySelector('.el-table__body tbody')
          if (tbody) {
            const rowElement = tbody.children[rowIndex] as HTMLElement
            if (rowElement) {
              const nextCell = rowElement.children[nextColumnIndex + 1] as HTMLElement
              if (nextCell) {
                document.querySelectorAll('.el-table__cell.selected-cell').forEach(el => {
                  el.classList.remove('selected-cell')
                })
                nextCell.classList.add('selected-cell')
              }
            }
          }
        }
      } else if (rowIndex < dataList.value.length - 1) {
        // 如果已是行尾，则跳转到下一行第1列
        const firstField = editableFields.value[0]
        const firstColumn = visibleColumns.find(col => col.field === firstField)
        if (firstColumn) {
          const firstColumnIndex = visibleColumns.indexOf(firstColumn)
          const tbody = document.querySelector('.el-table__body tbody')
          if (tbody) {
            const nextRow = tbody.children[rowIndex + 1] as HTMLElement
            if (nextRow) {
              const firstCell = nextRow.children[firstColumnIndex + 1] as HTMLElement
              if (firstCell) {
                document.querySelectorAll('.el-table__cell.selected-cell').forEach(el => {
                  el.classList.remove('selected-cell')
                })
                firstCell.classList.add('selected-cell')
              }
            }
          }
        }
      } else {
        // 如果已是最后1行，则新增1行，并跳转到该行第1列
        const newRow = { ...props.createDefaultRow() }
        dataList.value.push(newRow)
        nextTick(() => {
          const firstField = editableFields.value[0]
          const firstColumn = visibleColumns.find(col => col.field === firstField)
          if (firstColumn) {
            const firstColumnIndex = visibleColumns.indexOf(firstColumn)
            const tbody = document.querySelector('.el-table__body tbody')
            if (tbody) {
              const newRowElement = tbody.children[dataList.value.length - 1] as HTMLElement
              if (newRowElement) {
                const firstCell = newRowElement.children[firstColumnIndex + 1] as HTMLElement
                if (firstCell) {
                  document.querySelectorAll('.el-table__cell.selected-cell').forEach(el => {
                    el.classList.remove('selected-cell')
                  })
                  firstCell.classList.add('selected-cell')
                }
              }
            }
          }
        })
      }
    }
  }
  
  // Enter: 退出编辑，但焦点保留在当前单元格
  if (event.key === 'Enter') {
    event.preventDefault()
    endEdit()
    // 保持当前单元格的选中状态
    nextTick(() => {
      const visibleColumns = props.columns.filter(col => col.show !== false)
      const columnIndex = visibleColumns.findIndex(c => c.field === field)
      if (columnIndex !== -1) {
        const tbody = document.querySelector('.el-table__body tbody')
        if (tbody) {
          const rowElement = tbody.children[rowIndex] as HTMLElement
          if (rowElement) {
            const cell = rowElement.children[columnIndex + 1] as HTMLElement
            if (cell) {
              document.querySelectorAll('.el-table__cell.selected-cell').forEach(el => {
                el.classList.remove('selected-cell')
              })
              cell.classList.add('selected-cell')
            }
          }
        }
      }
    })
  }
  
  // Escape: 退出编辑，但焦点保留在当前单元格（与 Enter 行为一致）
  if (event.key === 'Escape') {
    event.preventDefault()
    endEdit()
    // 保持当前单元格的选中状态
    nextTick(() => {
      const visibleColumns = props.columns.filter(col => col.show !== false)
      const columnIndex = visibleColumns.findIndex(c => c.field === field)
      if (columnIndex !== -1) {
        const tbody = document.querySelector('.el-table__body tbody')
        if (tbody) {
          const rowElement = tbody.children[rowIndex] as HTMLElement
          if (rowElement) {
            const cell = rowElement.children[columnIndex + 1] as HTMLElement
            if (cell) {
              document.querySelectorAll('.el-table__cell.selected-cell').forEach(el => {
                el.classList.remove('selected-cell')
              })
              cell.classList.add('selected-cell')
            }
          }
        }
      }
    })
  }
  
  // 方向键导航
  if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(event.key)) {
    if (col?.type === 'select') {
      // 下拉框时，方向键用于选择，不阻止
      return
    }
    event.preventDefault()
    endEdit()
    
    let newRowIndex = rowIndex
    let newFieldIndex = currentIndex
    
    if (event.key === 'ArrowUp' && rowIndex > 0) {
      newRowIndex = rowIndex - 1
    } else if (event.key === 'ArrowDown') {
      if (rowIndex < dataList.value.length - 1) {
        newRowIndex = rowIndex + 1
      } else {
        // 添加新行
        const newRow = { ...props.createDefaultRow() }
        dataList.value.push(newRow)
        newRowIndex = dataList.value.length - 1
      }
    } else if (event.key === 'ArrowLeft' && currentIndex > 0) {
      newFieldIndex = currentIndex - 1
    } else if (event.key === 'ArrowRight' && currentIndex < editableFields.value.length - 1) {
      newFieldIndex = currentIndex + 1
    }
    
    startEdit(newRowIndex, editableFields.value[newFieldIndex])
  }
}

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
 * 处理复制（Ctrl+C）
 */
const handleCopy = (event: ClipboardEvent) => {
  // 优先处理编辑模式
  if (editingCell.value) {
    const { rowIndex, field } = editingCell.value
    const value = dataList.value[rowIndex]?.[field]
    if (value !== undefined && value !== null) {
      const copyValue = String(value)
      // 使用 clipboardData 设置剪贴板（必须在 copy 事件中同步设置）
      if (event.clipboardData) {
        event.clipboardData.setData('text/plain', copyValue)
        console.log('handleCopy: 编辑模式', { rowIndex, field, value: copyValue })
      }
      // 同时使用 Clipboard API 确保设置成功（异步，作为备用）
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(copyValue).then(() => {
          console.log('handleCopy: Clipboard API 设置成功（编辑模式）')
        }).catch(err => {
          console.warn('handleCopy: Clipboard API 失败', err)
        })
      }
    }
    return
  }
  
  // 非编辑模式：从选中的单元格复制
  const cellInfo = getSelectedCellInfo()
  console.log('handleCopy: 非编辑模式', { cellInfo })
  if (cellInfo) {
    const { rowIndex, field } = cellInfo
    const value = dataList.value[rowIndex]?.[field]
    console.log('handleCopy: 单元格值', { rowIndex, field, value })
    
    let copyValue = ''
    if (value !== undefined && value !== null) {
      // 拷贝原始值（字符串形式），而不是格式化后的显示值
      copyValue = String(value)
    }
    
    // 使用 clipboardData 设置剪贴板（必须在 copy 事件中同步设置）
    if (event.clipboardData) {
      event.clipboardData.setData('text/plain', copyValue)
      console.log('handleCopy: clipboardData 设置', { value: copyValue })
    }
    
    // 同时使用 Clipboard API 确保设置成功（异步，作为备用）
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(copyValue).then(() => {
        console.log('handleCopy: Clipboard API 设置成功', { value: copyValue })
      }).catch(err => {
        console.warn('handleCopy: Clipboard API 失败', err)
      })
    }
  } else {
    console.log('handleCopy: 未找到选中的单元格')
  }
}

/**
 * 处理粘贴（Ctrl+V）
 */
const handlePaste = (event: ClipboardEvent) => {
  // 优先处理编辑模式
  if (editingCell.value) {
    event.preventDefault()
    // 直接使用系统剪贴板
    const pasteData = event.clipboardData?.getData('text/plain') || ''
    console.log('handlePaste: 编辑模式', { pasteData })
    if (pasteData) {
      const { rowIndex, field } = editingCell.value
      const col = props.columns.find(c => c.field === field)
      
      if (col?.type === 'number') {
        const num = Number(pasteData)
        if (!isNaN(num)) {
          dataList.value[rowIndex][field] = num
          console.log('handlePaste: 粘贴数字', { rowIndex, field, value: num })
        }
      } else {
        dataList.value[rowIndex][field] = pasteData
        console.log('handlePaste: 粘贴文本', { rowIndex, field, value: pasteData })
      }
    }
    return
  }
  
  // 非编辑模式：粘贴到选中的单元格
  const cellInfo = getSelectedCellInfo()
  console.log('handlePaste: 非编辑模式', { cellInfo })
  if (cellInfo) {
    event.preventDefault()
    // 直接使用系统剪贴板
    const pasteData = event.clipboardData?.getData('text/plain') || ''
    console.log('handlePaste: 粘贴数据', { pasteData })
    if (pasteData !== undefined && pasteData !== null && pasteData !== '') {
      const { rowIndex, field, column } = cellInfo
      
      // 检查列是否可编辑
      if (column.editable === false) {
        console.log('handlePaste: 列不可编辑', { field })
        return
      }
      
      if (column.type === 'number') {
        const num = Number(pasteData)
        if (!isNaN(num)) {
          dataList.value[rowIndex][field] = num
          console.log('handlePaste: 粘贴数字成功', { rowIndex, field, value: num })
        } else {
          console.log('handlePaste: 粘贴数字失败，不是有效数字', { pasteData })
        }
      } else if (column.type === 'select' && column.options) {
        // 对于 select 类型，尝试通过 label 或 value 匹配
        const option = column.options.find(opt => opt.label === pasteData || String(opt.value) === pasteData)
        if (option) {
          dataList.value[rowIndex][field] = option.value
          console.log('handlePaste: 粘贴选择项成功', { rowIndex, field, value: option.value })
        } else {
          // 如果没有匹配的选项，直接使用粘贴的值
          dataList.value[rowIndex][field] = pasteData
          console.log('handlePaste: 粘贴选择项（无匹配），使用原始值', { rowIndex, field, value: pasteData })
        }
      } else {
        dataList.value[rowIndex][field] = pasteData
        console.log('handlePaste: 粘贴文本成功', { rowIndex, field, value: pasteData })
      }
    } else {
      // 如果粘贴数据为空，清空单元格
      const { rowIndex, field, column } = cellInfo
      if (column.editable !== false) {
        dataList.value[rowIndex][field] = column.type === 'number' ? null : ''
        console.log('handlePaste: 粘贴空值', { rowIndex, field })
      }
    }
  } else {
    console.log('handlePaste: 未找到选中的单元格')
  }
}

/**
 * 格式化单元格显示值
 */
const formatCellValue = (value: any, column: ImportGridColumn) => {
  if (value === null || value === undefined) return ''
  
  if (column.type === 'select' && column.options) {
    const option = column.options.find(opt => opt.value === value)
    return option ? option.label : value
  }
  
  return String(value)
}

/**
 * 处理输入框焦点事件
 */
const handleInputFocus = (rowIndex: number, field: string) => {
  // 清除blur定时器
  if (blurTimerRef.value) {
    clearTimeout(blurTimerRef.value)
    blurTimerRef.value = null
  }
  
  // 确保输入框获得焦点时保持编辑状态
  if (!isEditing(rowIndex, field)) {
    editingCell.value = { rowIndex, field }
  }
  
  // 标记正在输入
  isInputting.value = true
  setTimeout(() => {
    isInputting.value = false
  }, 100)
}

/**
 * 处理输入框失去焦点事件
 */
const handleInputBlur = (e: FocusEvent, rowIndex: number, field: string) => {
  // 如果正在输入，不处理blur
  if (isInputting.value) {
    return
  }
  
  // 清除之前的blur定时器
  if (blurTimerRef.value) {
    clearTimeout(blurTimerRef.value)
    blurTimerRef.value = null
  }
  
  // 延迟处理blur，检查焦点是否真的离开了
  blurTimerRef.value = setTimeout(() => {
    // 如果正在输入，不退出编辑
    if (isInputting.value) {
      blurTimerRef.value = null
      return
    }
    
    // 检查是否仍然是当前编辑的单元格
    if (!isEditing(rowIndex, field)) {
      blurTimerRef.value = null
      return
    }
    
    // 检查焦点是否真的离开了输入框
    const activeElement = document.activeElement
    
    // 查找当前单元格的输入框
    const cellInput = document.querySelector(`[data-cell-key="${rowIndex}-${field}"]`) as HTMLElement
    if (cellInput) {
      const inputElement = cellInput.querySelector('input') as HTMLInputElement
      // 如果焦点还在当前输入框上，不退出编辑
      if (inputElement && (inputElement === activeElement || inputElement.contains(activeElement as Node))) {
        blurTimerRef.value = null
        return
      }
    }
    
    // 检查焦点是否在单元格内的其他元素中（如下拉框）
    const input = e.target as HTMLElement
    const cell = input?.closest('.el-table__cell')
    if (cell && cell.contains(activeElement)) {
      blurTimerRef.value = null
      return
    }
    
    // 只有焦点确实离开了单元格，才退出编辑
    if (isEditing(rowIndex, field)) {
      endEdit()
    }
    
    blurTimerRef.value = null
  }, 200)
}

/**
 * 处理输入框输入事件
 */
const handleInputInput = (rowIndex: number, field: string) => {
  // 标记正在输入
  isInputting.value = true
  setTimeout(() => {
    isInputting.value = false
  }, 300)
}

/**
 * 处理输入框更新事件
 */
const handleInputUpdate = (val: string, rowIndex: number, field: string) => {
  // 标记正在输入
  isInputting.value = true
  
  // 更新值时，确保不会因为数据变化导致失去焦点
  if (isEditing(rowIndex, field)) {
    dataList.value[rowIndex][field] = val
    // 确保编辑状态保持
    if (!isEditing(rowIndex, field)) {
      editingCell.value = { rowIndex, field }
    }
  }
  
  setTimeout(() => {
    isInputting.value = false
  }, 300)
}

/**
 * 渲染单元格内容（已废弃，改用模板语法）
 */
const renderCellContent = (scope: any, column: ImportGridColumn) => {
  const { row, $index } = scope
  const field = column.field
  const rowIndex = $index
  const isEditable = column.editable !== false
  
  const editing = isEditing(rowIndex, field)
  if (editingCell.value && editingCell.value.field === field) {
    console.log('renderCellContent:', { rowIndex, field, editingCell: editingCell.value, editing, isEditable })
  }
  
  if (editing && isEditable) {
    // 编辑模式
    if (column.type === 'number') {
      return h(ElInputNumber, {
        key: `input-number-${rowIndex}-${field}`, // 添加稳定的 key，确保组件实例复用
        'data-cell-key': `${rowIndex}-${field}`,
        modelValue: row[field],
        'onUpdate:modelValue': (val: any) => {
          row[field] = val
        },
        onKeydown: (e: KeyboardEvent) => {
          e.stopPropagation()
          handleInputKeydown(e, rowIndex, field)
        },
        onFocus: () => {
          if (!isEditing(rowIndex, field)) {
            editingCell.value = { rowIndex, field }
          }
        },
        onBlur: (e: FocusEvent) => {
          setTimeout(() => {
            if (isInputting.value) {
              return
            }
            
            const activeElement = document.activeElement
            const input = e.target as HTMLElement
            
            if (input && input.contains(activeElement)) {
              return
            }
            
            const cell = input.closest('.el-table__cell')
            if (cell && cell.contains(activeElement)) {
              return
            }
            
            if (isEditing(rowIndex, field)) {
              endEdit()
            }
          }, 150)
        },
        onInput: () => {
          isInputting.value = true
          setTimeout(() => {
            isInputting.value = false
          }, 100)
        },
        controls: false,
        class: 'excel-edit-input',
        size: 'small'
      })
    } else if (column.type === 'select' && column.options) {
      return h(ElSelect, {
        key: `select-${rowIndex}-${field}`, // 添加稳定的 key，确保组件实例复用
        'data-cell-key': `${rowIndex}-${field}`,
        modelValue: row[field],
        'onUpdate:modelValue': (val: any) => {
          row[field] = val
        },
        onKeydown: (e: KeyboardEvent) => {
          e.stopPropagation()
          handleInputKeydown(e, rowIndex, field)
        },
        onFocus: () => {
          if (!isEditing(rowIndex, field)) {
            editingCell.value = { rowIndex, field }
          }
        },
        onBlur: (e: FocusEvent) => {
          if (isInputting.value) {
            return
          }
          
          setTimeout(() => {
            if (isInputting.value) {
              return
            }
            
            const activeElement = document.activeElement
            const input = e.target as HTMLElement
            
            if (input && input.contains(activeElement)) {
              return
            }
            
            const cell = input.closest('.el-table__cell')
            if (cell && cell.contains(activeElement)) {
              return
            }
            
            if (isEditing(rowIndex, field)) {
              endEdit()
            }
          }, 100)
        },
        class: 'excel-edit-select',
        size: 'small',
        filterable: true
      }, {
        default: () => column.options!.map((opt) => 
          h(ElOption, { key: opt.value, label: opt.label, value: opt.value })
        )
      })
    } else {
      return h(ElInput, {
        key: `input-${rowIndex}-${field}`, // 添加稳定的 key，确保组件实例复用
        'data-cell-key': `${rowIndex}-${field}`,
        modelValue: row[field],
        'onUpdate:modelValue': (val: string) => {
          // 标记正在输入
          isInputting.value = true
          console.log('onUpdate:modelValue: 标记正在输入', val)
          
          // 更新值时，确保不会因为数据变化导致失去焦点
          if (isEditing(rowIndex, field)) {
            row[field] = val
            // 确保编辑状态保持
            if (!isEditing(rowIndex, field)) {
              editingCell.value = { rowIndex, field }
            }
            
            // 使用 requestAnimationFrame 确保在浏览器渲染后恢复焦点
            requestAnimationFrame(() => {
              requestAnimationFrame(() => {
                const cellInput = document.querySelector(`[data-cell-key="${rowIndex}-${field}"]`) as HTMLElement
                if (cellInput) {
                  const inputElement = cellInput.querySelector('input') as HTMLInputElement
                  if (inputElement) {
                    currentInputRef.value = inputElement
                    // 确保输入框保持焦点
                    if (document.activeElement !== inputElement) {
                      inputElement.focus()
                      // 将光标移到末尾
                      const len = inputElement.value.length
                      inputElement.setSelectionRange(len, len)
                    }
                  }
                }
              })
            })
          }
          
          // 延迟清除标记（减少延迟时间，因为使用了 flush: 'post'）
          setTimeout(() => {
            isInputting.value = false
            console.log('onUpdate:modelValue: 清除输入标记')
          }, 300)
        },
        onFocus: (e: FocusEvent) => {
          // 清除blur定时器
          if (blurTimerRef.value) {
            clearTimeout(blurTimerRef.value)
            blurTimerRef.value = null
          }
          
          // 确保输入框获得焦点时保持编辑状态
          if (!isEditing(rowIndex, field)) {
            editingCell.value = { rowIndex, field }
          }
          
          // 保存输入框引用
          const input = e.target as HTMLInputElement
          if (input) {
            currentInputRef.value = input
          }
          
          // 标记正在输入（获得焦点时）
          isInputting.value = true
          setTimeout(() => {
            isInputting.value = false
          }, 100)
        },
        onBlur: (e: FocusEvent) => {
          // 如果正在输入，不处理blur
          if (isInputting.value) {
            console.log('blur被忽略：正在输入')
            return
          }
          
          // 清除之前的blur定时器
          if (blurTimerRef.value) {
            clearTimeout(blurTimerRef.value)
            blurTimerRef.value = null
          }
          
          // 延迟处理blur，检查焦点是否真的离开了
          blurTimerRef.value = setTimeout(() => {
            // 如果正在输入，不退出编辑
            if (isInputting.value) {
              blurTimerRef.value = null
              return
            }
            
            // 检查是否仍然是当前编辑的单元格
            if (!isEditing(rowIndex, field)) {
              blurTimerRef.value = null
              return
            }
            
            // 检查焦点是否真的离开了输入框
            const activeElement = document.activeElement
            
            // 查找当前单元格的输入框
            const cellInput = document.querySelector(`[data-cell-key="${rowIndex}-${field}"]`) as HTMLElement
            if (cellInput) {
              const inputElement = cellInput.querySelector('input') as HTMLInputElement
              // 如果焦点还在当前输入框上，不退出编辑
              if (inputElement && (inputElement === activeElement || inputElement.contains(activeElement as Node))) {
                blurTimerRef.value = null
                return
              }
            }
            
            // 检查焦点是否在单元格内的其他元素中（如下拉框）
            const input = e.target as HTMLElement
            const cell = input?.closest('.el-table__cell')
            if (cell && cell.contains(activeElement)) {
              blurTimerRef.value = null
              return
            }
            
            // 检查是否是当前正在编辑的输入框
            if (currentInputRef.value && (currentInputRef.value === activeElement || currentInputRef.value.contains(activeElement as Node))) {
              blurTimerRef.value = null
              return
            }
            
            // 只有焦点确实离开了单元格，才退出编辑
            if (isEditing(rowIndex, field)) {
              console.log('退出编辑模式')
              endEdit()
            }
            
            blurTimerRef.value = null
          }, 500)
        },
        onInput: () => {
          // 标记正在输入
          isInputting.value = true
          console.log('onInput: 标记正在输入')
          // 延迟清除标记，给输入操作时间（增加延迟时间，确保 Vue 重新渲染完成）
          setTimeout(() => {
            isInputting.value = false
            console.log('onInput: 清除输入标记')
          }, 500)
        },
        onKeydown: (e: KeyboardEvent) => {
          // 标记正在输入（键盘输入时）
          isInputting.value = true
          console.log('onKeydown: 标记正在输入', e.key)
          // 阻止事件冒泡，避免触发单元格的keydown事件
          e.stopPropagation()
          handleInputKeydown(e, rowIndex, field)
          // 延迟清除标记，确保输入操作完成（增加延迟时间，确保 Vue 重新渲染完成）
          setTimeout(() => {
            isInputting.value = false
            console.log('onKeydown: 清除输入标记')
          }, 500)
        },
        class: 'excel-edit-input',
        size: 'small'
      })
    }
  } else {
    // 显示模式
    return h('span', {
      class: ['excel-cell', { 'cell-focused': isEditing(rowIndex, field) }],
      onDblclick: () => isEditable && handleCellDblclick(row, { property: field }),
      onKeydown: (e: KeyboardEvent) => handleCellKeydown(e, row, { property: field }),
      onFocus: (e: FocusEvent) => {
        const cell = (e.target as HTMLElement).closest('.el-table__cell') as HTMLElement
        if (cell) {
          document.querySelectorAll('.el-table__cell.selected-cell').forEach(el => {
            el.classList.remove('selected-cell')
          })
          cell.classList.add('selected-cell')
        }
      },
      onBlur: () => {
        const cell = document.querySelector('.el-table__cell.selected-cell') as HTMLElement
        if (cell && !editingCell.value) {
          cell.classList.remove('selected-cell')
        }
      },
      tabindex: isEditable ? 0 : -1
    }, formatCellValue(row[field], column))
  }
}

onMounted(async () => {
  // 先不显示页面，等待状态恢复完成
  isRestoring.value = true
  
  // 保存组件挂载时的路由信息（用于检测标签页关闭）
  mountedRoutePath = router.currentRoute.value.path
  mountedRouteFullPath = router.currentRoute.value.fullPath
  
  // 优先恢复页面状态（如果存在）
  const state = restorePageState()
  if (state && state.dataList && Array.isArray(state.dataList) && state.dataList.length > 0) {
    // 恢复表格数据
    dataList.value = state.dataList.map(row => ({
      ...props.createDefaultRow(),
      ...row
    }))
    emit('dataLoaded', dataList.value)
    console.log('ImportGrid: 从页面状态恢复数据', dataList.value.length, '条记录')
  } else {
    // 如果没有页面状态，尝试从父窗口传入的数据加载
    const loaded = loadDataFromStorage()
    if (!loaded) {
      // 如果两者都没有，创建一行默认数据
      dataList.value = [props.createDefaultRow()]
      emit('dataLoaded', dataList.value)
    }
  }
  
  // 状态恢复完成，显示页面
  isRestoring.value = false
  pageReady.value = true
  
  // 监听全局复制粘贴事件
  document.addEventListener('copy', handleCopy)
  document.addEventListener('paste', handlePaste)
  
  // 监听全局键盘事件，处理焦点单元格的键盘输入
  const handleGlobalKeydown = (event: KeyboardEvent) => {
    // 如果焦点在输入框内，不处理（让输入框自己处理）
    const activeElement = document.activeElement
    if (activeElement && (activeElement.tagName === 'INPUT' || activeElement.tagName === 'TEXTAREA' || activeElement.tagName === 'SELECT')) {
      return
    }
    
    // 如果正在编辑，不处理（让 handleInputKeydown 处理）
    if (editingCell.value) {
      return
    }
    
    // 查找当前选中的单元格
    const selectedCell = document.querySelector('.el-table__cell.selected-cell') as HTMLElement
    if (!selectedCell) return
    
    // 获取单元格对应的行和列信息
    const rowElement = selectedCell.closest('tr')
    if (!rowElement) return
    
    // 从表格body中获取行索引（排除表头）
    const tbody = rowElement.parentElement
    if (!tbody) return
    
    const rowIndex = Array.from(tbody.children).indexOf(rowElement)
    if (rowIndex === -1) return
    
    const cellIndex = Array.from(rowElement.children).indexOf(selectedCell)
    if (cellIndex === -1) return
    
    // 跳过序号列
    const columnIndex = cellIndex - 1
    if (columnIndex < 0) return
    
    const visibleColumns = props.columns.filter(col => col.show !== false)
    if (columnIndex >= visibleColumns.length) return
    
    const column = visibleColumns[columnIndex]
    const currentIndex = editableFields.value.indexOf(column.field)
    
    // Tab 或 Enter: 跳转到下一列
    if (event.key === 'Tab' || event.key === 'Enter') {
      event.preventDefault()
      
      if (event.key === 'Tab' && event.shiftKey) {
        // Shift+Tab: 向左移动
        if (currentIndex > 0) {
          // 跳转到上一列
          const prevField = editableFields.value[currentIndex - 1]
          const prevColumn = visibleColumns.find(col => col.field === prevField)
          if (prevColumn) {
            const prevColumnIndex = visibleColumns.indexOf(prevColumn)
            const prevCell = rowElement.children[prevColumnIndex + 1] as HTMLElement
            if (prevCell) {
              document.querySelectorAll('.el-table__cell.selected-cell').forEach(el => {
                el.classList.remove('selected-cell')
              })
              prevCell.classList.add('selected-cell')
            }
          }
        } else if (rowIndex > 0) {
          // 如果已是行首，则跳转到上一行最后一列
          const prevRow = tbody.children[rowIndex - 1] as HTMLElement
          if (prevRow) {
            const lastField = editableFields.value[editableFields.value.length - 1]
            const lastColumn = visibleColumns.find(col => col.field === lastField)
            if (lastColumn) {
              const lastColumnIndex = visibleColumns.indexOf(lastColumn)
              const lastCell = prevRow.children[lastColumnIndex + 1] as HTMLElement
              if (lastCell) {
                document.querySelectorAll('.el-table__cell.selected-cell').forEach(el => {
                  el.classList.remove('selected-cell')
                })
                lastCell.classList.add('selected-cell')
              }
            }
          }
        }
      } else {
        // Tab 或 Enter: 向右移动到下一列
        if (currentIndex < editableFields.value.length - 1) {
          // 如果还有下一列，跳转到下一列
          const nextField = editableFields.value[currentIndex + 1]
          const nextColumn = visibleColumns.find(col => col.field === nextField)
          if (nextColumn) {
            const nextColumnIndex = visibleColumns.indexOf(nextColumn)
            const nextCell = rowElement.children[nextColumnIndex + 1] as HTMLElement
            if (nextCell) {
              document.querySelectorAll('.el-table__cell.selected-cell').forEach(el => {
                el.classList.remove('selected-cell')
              })
              nextCell.classList.add('selected-cell')
            }
          }
        } else if (rowIndex < dataList.value.length - 1) {
          // 如果已是行尾，则跳转到下一行第1列
          const nextRow = tbody.children[rowIndex + 1] as HTMLElement
          if (nextRow) {
            const firstField = editableFields.value[0]
            const firstColumn = visibleColumns.find(col => col.field === firstField)
            if (firstColumn) {
              const firstColumnIndex = visibleColumns.indexOf(firstColumn)
              const firstCell = nextRow.children[firstColumnIndex + 1] as HTMLElement
              if (firstCell) {
                document.querySelectorAll('.el-table__cell.selected-cell').forEach(el => {
                  el.classList.remove('selected-cell')
                })
                firstCell.classList.add('selected-cell')
              }
            }
          }
        } else {
          // 如果已是最后1行，则新增1行，并跳转到该行第1列
          const newRow = { ...props.createDefaultRow() }
          dataList.value.push(newRow)
          nextTick(() => {
            const newRowElement = tbody.children[dataList.value.length - 1] as HTMLElement
            if (newRowElement) {
              const firstField = editableFields.value[0]
              const firstColumn = visibleColumns.find(col => col.field === firstField)
              if (firstColumn) {
                const firstColumnIndex = visibleColumns.indexOf(firstColumn)
                const firstCell = newRowElement.children[firstColumnIndex + 1] as HTMLElement
                if (firstCell) {
                  document.querySelectorAll('.el-table__cell.selected-cell').forEach(el => {
                    el.classList.remove('selected-cell')
                  })
                  firstCell.classList.add('selected-cell')
                }
              }
            }
          })
        }
      }
      return
    }
    
    // Esc: 取消当前焦点
    if (event.key === 'Escape') {
      event.preventDefault()
      document.querySelectorAll('.el-table__cell.selected-cell').forEach(el => {
        el.classList.remove('selected-cell')
      })
      return
    }
    
    // 其他可打印字符，调用 handleCellKeydown 处理
    const row = dataList.value[rowIndex]
    if (row && column) {
      handleCellKeydown(event, row, { property: column.field, field: column.field })
    }
  }
  
  document.addEventListener('keydown', handleGlobalKeydown)
  
  // 清理函数
  const cleanup = () => {
    document.removeEventListener('copy', handleCopy)
    document.removeEventListener('paste', handlePaste)
    document.removeEventListener('keydown', handleGlobalKeydown)
  }
  
  // 组件卸载时清理
  onUnmounted(cleanup)
})

/**
 * 组件卸载前保存状态
 */
onBeforeUnmount(() => {
  // 先保存状态（无论切换还是关闭都先保存，确保数据不丢失）
  savePageState()
  
  // 清除定时器
  if (saveStateTimer) {
    clearTimeout(saveStateTimer)
    saveStateTimer = null
  }
  
  // 检查标签页是否被关闭
  // 注意：必须使用挂载时的路由信息，因为关闭标签页时路由会跳转到其他页面
  if (!mountedRoutePath || !mountedRouteFullPath) {
    console.warn('ImportGrid: 无法检查标签页状态，挂载路由信息丢失')
    return
  }
  
  const pathToCheck = mountedRoutePath
  const fullPathToCheck = mountedRouteFullPath
  
  // 延迟检查，确保标签页状态已经更新
  const checkAndClear = () => {
    const visitedViews = tagsViewStore.getVisitedViews
    // 检查挂载时的路由是否还在 visitedViews 中（使用 path 匹配，因为 store 使用 path）
    const isStillOpen = visitedViews.some(view => view.path === pathToCheck)
    
    if (!isStillOpen) {
      // 标签页已被关闭，清空状态数据
      // 使用保存的 fullPath 来生成正确的 key
      const stateKey = `IMPORT_GRID_STATE_${fullPathToCheck}`
      clearPageState(stateKey, fullPathToCheck)
      console.log('ImportGrid: 检测到标签页关闭，已清空页面状态', { 
        mountedPath: pathToCheck, 
        mountedFullPath: fullPathToCheck,
        currentPath: router.currentRoute.value.path,
        currentFullPath: router.currentRoute.value.fullPath,
        stateKey,
        visitedViewsCount: visitedViews.length,
        visitedPaths: visitedViews.map(v => v.path)
      })
      return true
    } else {
      // 标签页仍然打开，只是切换了路由，保持状态数据
      console.log('ImportGrid: 检测到路由切换，保持页面状态', { 
        mountedPath: pathToCheck, 
        mountedFullPath: fullPathToCheck,
        currentPath: router.currentRoute.value.path,
        currentFullPath: router.currentRoute.value.fullPath,
        visitedViewsCount: visitedViews.length,
        visitedPaths: visitedViews.map(v => v.path)
      })
      return false
    }
  }
  
  // 延迟检查，确保标签页状态已经更新
  nextTick(() => {
    // 第一次检查（50ms后）
    setTimeout(() => {
      if (checkAndClear()) return
      
      // 第二次检查（200ms后，如果第一次检查标签页还在）
      setTimeout(() => {
        checkAndClear()
      }, 150)
    }, 50)
  })
})

// 暴露方法供父组件调用
defineExpose({
  getData: () => dataList.value,
  setData: (data: any[]) => {
    dataList.value = data
  },
  loadDataFromStorage
})
</script>

<template>
  <div class="import-grid-container">
    <ElTable
      ref="tableRef"
      :data="dataList"
      border
      class="excel-table"
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
      />
      
      <ElTableColumn
        v-for="column in props.columns.filter(col => col.show !== false)"
        :key="column.field"
        :prop="column.field"
        :label="column.label"
        :width="column.width"
        :min-width="column.minWidth"
      >
        <template #default="scope">
          <!-- 编辑模式：数字输入框 -->
          <ElInputNumber
            v-if="isEditing(scope.$index, column.field) && column.editable !== false && column.type === 'number'"
            :key="`input-number-${scope.$index}-${column.field}`"
            :data-cell-key="`${scope.$index}-${column.field}`"
            v-model="scope.row[column.field]"
            size="small"
            :controls="false"
            class="excel-edit-input"
            @keydown.stop="handleInputKeydown($event, scope.$index, column.field)"
            @focus="handleInputFocus(scope.$index, column.field)"
            @blur="handleInputBlur($event, scope.$index, column.field)"
            @input="handleInputInput(scope.$index, column.field)"
          />
          
          <!-- 编辑模式：下拉选择 -->
          <ElSelect
            v-else-if="isEditing(scope.$index, column.field) && column.editable !== false && column.type === 'select' && column.options"
            :key="`select-${scope.$index}-${column.field}`"
            :data-cell-key="`${scope.$index}-${column.field}`"
            v-model="scope.row[column.field]"
            size="small"
            class="excel-edit-select"
            filterable
            @keydown.stop="handleInputKeydown($event, scope.$index, column.field)"
            @focus="handleInputFocus(scope.$index, column.field)"
            @blur="handleInputBlur($event, scope.$index, column.field)"
          >
            <ElOption
              v-for="opt in column.options"
              :key="opt.value"
              :label="opt.label"
              :value="opt.value"
            />
          </ElSelect>
          
          <!-- 编辑模式：文本输入框 -->
          <ElInput
            v-else-if="isEditing(scope.$index, column.field) && column.editable !== false"
            :key="`input-${scope.$index}-${column.field}`"
            :data-cell-key="`${scope.$index}-${column.field}`"
            v-model="scope.row[column.field]"
            size="small"
            class="excel-edit-input"
            @keydown.stop="handleInputKeydown($event, scope.$index, column.field)"
            @focus="handleInputFocus(scope.$index, column.field)"
            @blur="handleInputBlur($event, scope.$index, column.field)"
            @input="handleInputInput(scope.$index, column.field)"
            @update:model-value="handleInputUpdate(scope.$index, column.field, $event)"
          />
          
          <!-- 显示模式 -->
          <span 
            v-else
            class="excel-cell"
            :class="{ 'cell-focused': isEditing(scope.$index, column.field) }"
            @keydown="column.editable !== false && handleCellKeydown($event, scope.row, { property: column.field })"
            tabindex="0"
          >{{ formatCellValue(scope.row[column.field], column) }}</span>
        </template>
      </ElTableColumn>
    </ElTable>
  </div>
</template>

<style lang="less" scoped>
.import-grid-container {
  padding: 0;
  height: 100%;
  overflow: hidden;
  margin-top: 10px;
}

:deep(.excel-table) {
  height: 100%;
  
  .el-table__body-wrapper {
    overflow-y: auto;
  }
  
  .el-table__cell {
    padding: 4px 8px !important;
    position: relative;
    
    &:hover {
      background-color: #f5f7fa;
    }
  }
  
  // 序号列样式
  .el-table__cell:first-child {
    background-color: #fafafa;
    font-weight: 500;
    text-align: center;
    user-select: none;
    padding-left: 0 !important;
    padding-right: 0 !important;
    font-size: 12px !important; // 减小2级字号
  }
  
  // 序号列表头隐藏
  .el-table__header-wrapper .el-table__header th:first-child {
    background-color: #fafafa;
    border-right: 1px solid #ebeef5;
  }
  
  .excel-cell {
    display: block;
    width: 100%;
    min-height: 20px;
    padding: 2px 4px;
    cursor: cell;
    outline: none;
    position: relative;
    box-sizing: border-box;
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
  
  // 编辑状态下的单元格样式
  .excel-edit-input,
  .excel-edit-select {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    width: 100%;
    height: 100%;
    margin: 0;
    
    :deep(.el-input__wrapper),
    :deep(.el-input__inner) {
      height: 100%;
      border: 2px solid rgb(16, 153, 104);
      box-shadow: none;
      border-radius: 0;
      padding: 0 4px;
      line-height: 1.5;
    }
    
    :deep(.el-input-number__decrease),
    :deep(.el-input-number__increase) {
      display: none;
    }
  }
  
  .excel-edit-select {
    :deep(.el-select__wrapper) {
      height: 100%;
      border: 2px solid rgb(16, 153, 104);
      box-shadow: none;
      border-radius: 0;
      padding: 0 4px;
      line-height: 1.5;
    }
    
    :deep(.el-input__wrapper) {
      height: 100%;
      border: none;
      padding: 0;
    }
    
    :deep(.el-input__inner) {
      height: 100%;
      border: none;
      padding: 0;
    }
  }
  
  // 编辑状态下的单元格，移除默认padding
  .el-table__cell.editing-cell {
    padding: 0 !important;
  }
  
  // 表头样式
  .el-table__header {
    th {
      background-color: #fafafa;
      font-weight: 600;
      border-bottom: 2px solid #e8e8e8;
    }
  }
}
</style>
